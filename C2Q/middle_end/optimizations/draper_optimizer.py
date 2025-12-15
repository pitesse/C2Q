"""Specialized optimizations for Draper QFT-based arithmetic circuits.

This module contains optimizations specifically designed for the quantum arithmetic
algorithms used in the C-to-Quantum compiler, particularly Draper's QFT-based
addition and subtraction.
"""

import math
from typing import List, Dict, Set, Optional
from collections import defaultdict
from dataclasses import dataclass

from xdsl.ir import SSAValue, Operation
from xdsl.dialects.builtin import ModuleOp


@dataclass
class OptimizationStats:
    """Statistics tracking optimization effectiveness."""

    gates_eliminated: int = 0
    phases_consolidated: int = 0
    qubits_eliminated: int = 0
    depth_reduction: int = 0

    def __str__(self) -> str:
        return (
            f"Optimization Results:\n"
            f"  Gates eliminated: {self.gates_eliminated}\n"
            f"  Phases consolidated: {self.phases_consolidated}\n"
            f"  Qubits eliminated: {self.qubits_eliminated}\n"
            f"  Depth reduction: {self.depth_reduction}"
        )


class DraperOptimizer:
    """Optimizations specific to Draper QFT arithmetic circuits.

    These optimizations understand the structure of QFT-based arithmetic
    and can make intelligent decisions about precision, gate elimination,
    and circuit depth reduction.
    """

    def __init__(self, precision_threshold: float = 1e-3) -> None:
        """Initialize Draper-specific optimizer.

        Args:
            precision_threshold: Minimum phase angle to keep (eliminates smaller rotations).
        """
        self.precision_threshold = precision_threshold
        self.stats = OptimizationStats()

    def optimize_draper_circuit(self, module: ModuleOp) -> ModuleOp:
        """Apply Draper-specific optimizations iteratively to reduce arithmetic circuit complexity.

        Runs optimization passes in a loop until convergence. This allows peeling away layers:
        iteration 1 cancels outer Hadamards at QFT/IQFT boundaries, iteration 2 merges
        now-adjacent phase gates from inner QFT layers, and subsequent iterations continue
        until no more improvements are found.

        Key optimizations:
        1. Eliminate high-precision phase rotations for small operands
        2. Optimize QFT depth based on actual register usage
        3. Consolidate adjacent phase rotations in frequency domain
        4. Remove redundant SWAP operations in QFT
        5. Hadamard cancellation at QFT/IQFT boundaries

        Args:
            module: Input MLIR module containing quantum operations.

        Returns:
            Optimized MLIR module.
        """
        print("[INFO] Starting iterative Draper arithmetic optimization...")

        iteration = 0
        max_iterations = 10

        while iteration < max_iterations:
            iteration += 1
            print(f"\n  [INFO] Draper Iteration {iteration}")

            prev_gates = self.stats.gates_eliminated
            prev_phases = self.stats.phases_consolidated

            self._optimize_phase_precision(module)
            self._consolidate_adjacent_phases(module)
            self._cancel_hadamard_pairs(module)
            self._optimize_qft_depth(module)
            self._eliminate_redundant_swaps(module)

            gates_this_iter = self.stats.gates_eliminated - prev_gates
            phases_this_iter = self.stats.phases_consolidated - prev_phases
            changes_this_iter = gates_this_iter + phases_this_iter

            print(
                f"    [INFO] Changes: {changes_this_iter} (gates: {gates_this_iter}, phases: {phases_this_iter})"
            )

            if changes_this_iter == 0:
                print(
                    f"\n  [OK] Draper optimization converged after {iteration} iteration(s)"
                )
                break

        if iteration >= max_iterations:
            print(f"\n  [WARN] Reached maximum Draper iterations ({max_iterations})")
        print("\n[INFO] Draper optimization complete.")
        print(self.stats)

        return module

    def _optimize_phase_precision(self, module: ModuleOp) -> None:
        """Eliminate negligible phase rotations in Draper arithmetic.

        For small integer operands, many of the high-precision phase rotations
        have negligible effect and can be safely removed.

        Args:
            module: MLIR module to optimize.
        """
        print("  [INFO] Optimizing phase precision...")

        eliminated = 0
        total_phases = 0
        for op in list(module.walk()):
            if hasattr(op, "name") and op.name == "quantum.OnQubit_controlled_phase":
                total_phases += 1
                phase = abs(self._extract_phase(op))

                if phase < self.precision_threshold:
                    if len(op.results) > 0 and len(op.operands) > 1:
                        op.results[0].replace_by(op.operands[1])

                    if op.parent is not None:
                        op.detach()
                    op.erase()
                    eliminated += 1
                    self.stats.gates_eliminated += 1

        print(
            f"    [INFO] Eliminated {eliminated}/{total_phases} negligible phase rotations (< {self.precision_threshold:.4f} rad)"
        )

    def _optimize_qft_depth(self, module: ModuleOp) -> None:
        """Reduce QFT depth by analyzing actual register bit usage.

        If we know that operands are small (e.g., fit in 4 bits instead of 8),
        we can eliminate the higher-order QFT operations.

        Args:
            module: MLIR module to optimize.
        """
        print("  [INFO] Analyzing QFT depth requirements...")

        bit_usage = self._analyze_bit_usage(module)
        max_significant_bit = max(bit_usage) if bit_usage else 7

        if max_significant_bit < 7:
            eliminated = self._eliminate_unused_qft_operations(
                module, max_significant_bit + 1
            )
            self.stats.depth_reduction += eliminated
            print(f"    [INFO] Reduced QFT depth to {max_significant_bit + 1} bits")
        else:
            print(
                f"    [INFO] All bits ({max_significant_bit + 1}) in use, no QFT depth reduction possible"
            )

    def _eliminate_redundant_swaps(self, module: ModuleOp) -> None:
        """Remove redundant SWAP operations in QFT implementation.

        SWAP-SWAP pairs can cancel out, or SWAPs can be absorbed
        into the computation rather than performed explicitly.

        Args:
            module: MLIR module to optimize.
        """
        print("  [INFO] Eliminating redundant SWAP operations...")

        swaps = [op for op in module.walk() if op.name == "quantum.OnQubit_swap"]
        eliminated = 0

        i = 0
        while i < len(swaps) - 1:
            swap1 = swaps[i]
            swap2 = swaps[i + 1]

            if self._swaps_cancel(swap1, swap2):
                swap1.erase()
                swap2.erase()
                eliminated += 2
                self.stats.gates_eliminated += 2
                i += 2
            else:
                i += 1

        print(f"    [INFO] Eliminated {eliminated} redundant SWAPs")

    def _consolidate_adjacent_phases(self, module: ModuleOp) -> None:
        """Consolidate adjacent controlled-phase operations on the same qubit pair.

        Multiple controlled phase rotations between the same control and target
        qubits can be combined using R(θ₁)·R(θ₂) = R(θ₁ + θ₂). This is especially
        important after Hadamard cancellation exposes adjacent phases.

        Args:
            module: MLIR module to optimize.
        """
        print("  [INFO] Consolidating adjacent phase rotations...")

        operations = list(module.walk())
        to_remove: Set[Operation] = set()
        consolidated = 0

        i = 0
        while i < len(operations) - 1:
            op = operations[i]
            # print(type(op))

            if op in to_remove:
                i += 1
                continue

            if not (
                hasattr(op, "name") and op.name == "quantum.OnQubit_controlled_phase"
            ):
                i += 1
                continue

            next_op = operations[i + 1]

            if (
                hasattr(next_op, "name")
                and next_op.name == "quantum.OnQubit_controlled_phase"
                and next_op not in to_remove
            ):

                if self._same_phase_qubits(op, next_op):
                    phase1 = self._extract_phase(op)
                    phase2 = self._extract_phase(next_op)
                    combined_phase = phase1 + phase2

                    self._set_phase(op, combined_phase)

                    if len(next_op.results) > 0 and len(op.results) > 0:
                        next_op.results[0].replace_by(op.results[0])

                    to_remove.add(next_op)
                    consolidated += 1
                    self.stats.phases_consolidated += 1

                    continue

            i += 1

        for op in to_remove:
            if op.parent is not None:
                op.detach()
            op.erase()

        print(f"    [INFO] Consolidated {consolidated} adjacent phase rotations")

    def _cancel_hadamard_pairs(self, module: ModuleOp) -> None:
        """Cancel pairs of Hadamard gates on the same qubit.

        Applies the identity H·H = I, which is especially important at QFT/IQFT boundaries
        where the trailing Hadamard of a QFT immediately precedes the leading Hadamard
        of an IQFT. Cancelling these exposes the inner phase gates for consolidation.

        Args:
            module: MLIR module to optimize.
        """
        print("  [INFO] Cancelling Hadamard pairs (H·H = I)...")

        operations = list(module.walk())
        to_remove: Set[Operation] = set()
        cancelled = 0

        for i in range(len(operations) - 1):
            op = operations[i]

            if op in to_remove:
                continue

            next_op = operations[i + 1]
            if next_op in to_remove:
                continue

            if (
                hasattr(op, "name")
                and hasattr(next_op, "name")
                and op.name == "quantum.OnQubit_hadamard"
                and next_op.name == "quantum.OnQubit_hadamard"
            ):

                if self._same_qubit(op, next_op):
                    to_remove.add(op)
                    to_remove.add(next_op)
                    cancelled += 2
                    self.stats.gates_eliminated += 2

        for op in to_remove:
            if op.parent is not None:
                op.detach()
            op.erase()

        print(f"    [INFO] Cancelled {cancelled} Hadamard gates ({cancelled//2} pairs)")

    def _same_qubit(self, op1: Operation, op2: Operation) -> bool:
        """Check if two operations target the same qubit.

        Args:
            op1: First operation.
            op2: Second operation.

        Returns:
            True if both operations target the same qubit, False otherwise.
        """
        try:
            if len(op1.operands) == 0 or len(op2.operands) == 0:
                return False

            reg1 = op1.operands[0]
            reg2 = op2.operands[0]

            idx1 = op1.attributes.get("index", 0)
            idx2 = op2.attributes.get("index", 0)

            return reg1 == reg2 and idx1 == idx2
        except:
            return False

    def _same_phase_qubits(self, op1: Operation, op2: Operation) -> bool:
        """Check if two controlled-phase operations target the same qubit pair.

        Args:
            op1: First controlled-phase operation.
            op2: Second controlled-phase operation.

        Returns:
            True if both operations have the same control and target qubits, False otherwise.
        """
        try:
            if len(op1.operands) < 2 or len(op2.operands) < 2:
                return False

            control1 = op1.operands[0]
            target1 = op1.operands[1]
            control2 = op2.operands[0]
            target2 = op2.operands[1]

            control_idx1 = op1.attributes.get("control_index", 0)
            target_idx1 = op1.attributes.get("target_index", 0)
            control_idx2 = op2.attributes.get("control_index", 0)
            target_idx2 = op2.attributes.get("target_index", 0)

            same_control = control1 == control2 and control_idx1 == control_idx2
            same_target = target1 == target2 and target_idx1 == target_idx2

            return same_control and same_target
        except:
            return False

    def _set_phase(self, op: Operation, phase: float) -> None:
        """Set phase angle for controlled-phase operation.

        Args:
            op: Controlled-phase operation to modify.
            phase: New phase angle in radians.
        """
        try:
            from xdsl.dialects.builtin import FloatAttr, Float64Type

            op.attributes["phase"] = FloatAttr(phase, Float64Type())
        except:
            pass

    def _extract_phase(self, op: Operation) -> float:
        """Extract phase angle from controlled phase operation.

        Args:
            op: Controlled-phase operation.

        Returns:
            Phase angle in radians, or 0.0 if extraction fails.
        """
        try:
            attr = op.attributes.get("phase")
            if attr is None:
                return 0.0

            if hasattr(attr, "value"):
                if hasattr(attr.value, "data"):  # type: ignore[attr-defined]
                    return float(attr.value.data)  # type: ignore[attr-defined]
                return float(attr.value)  # type: ignore[attr-defined]

            if hasattr(attr, "data"):
                return float(attr.data)  # type: ignore[attr-defined]

            try:
                return float(attr)  # type: ignore[arg-type]
            except:
                return 0.0
        except:
            return 0.0

    def _analyze_bit_usage(self, module: ModuleOp) -> Set[int]:
        """Analyze which bit positions are actually used in the circuit.

        A bit is considered used if it appears in any quantum operation's
        index, target_index, or control_index attributes. This ensures proper
        handling of all bits that participate in Fourier-domain arithmetic.

        Args:
            module: MLIR module to analyze.

        Returns:
            Set of bit indices that are used in the circuit.
        """
        used_bits = set()

        for op in module.walk():
            if hasattr(op, "name") and hasattr(op, "attributes"):
                try:
                    for attr_name in ["index", "target_index", "control_index"]:
                        attr = op.attributes.get(attr_name)
                        if attr is not None:
                            if hasattr(attr, "data"):
                                val = int(attr.data)  # type: ignore[attr-defined]
                                used_bits.add(val)
                except:
                    print(f"    [WARN] Failed to analyze bit usage for operation: {op}")
                    pass

        return used_bits

    def _eliminate_unused_qft_operations(self, module: ModuleOp, max_bits: int) -> int:
        """Remove QFT operations on unused higher-order bits.

        Args:
            module: MLIR module to optimize.
            max_bits: Maximum number of bits actually needed.

        Returns:
            Number of operations eliminated.
        """
        eliminated = 0

        for op in list(module.walk()):
            if self._operates_on_high_bits(op, max_bits):
                if op.parent is not None:
                    op.detach()
                op.erase()
                eliminated += 1
                self.stats.gates_eliminated += 1

        return eliminated

    def _operates_on_high_bits(self, op: Operation, max_bits: int) -> bool:
        """Check if operation works on bits >= max_bits.

        Args:
            op: Operation to check.
            max_bits: Threshold bit index.

        Returns:
            True if operation targets high bits, False otherwise.
        """
        try:
            if hasattr(op, "attributes"):
                attr = op.attributes.get("index")
                if attr is not None and hasattr(attr, "data"):
                    val = int(attr.data)  # type: ignore[attr-defined]
                    if val >= max_bits:
                        return True

                target_attr = op.attributes.get("target_index")
                if target_attr is not None and hasattr(target_attr, "data"):
                    val = int(target_attr.data)  # type: ignore[attr-defined]
                    if val >= max_bits:
                        return True

        except:
            pass

        return False

    def _swaps_cancel(self, swap1: Operation, swap2: Operation) -> bool:
        """Check if two SWAP operations cancel each other out.

        Args:
            swap1: First SWAP operation.
            swap2: Second SWAP operation.

        Returns:
            True if the swaps cancel (swap the same pair of qubits), False otherwise.
        """
        try:
            indices1 = self._get_swap_indices(swap1)
            indices2 = self._get_swap_indices(swap2)

            return indices1 == indices2 or indices1 == indices2[::-1]
        except:
            return False

    def _get_swap_indices(self, swap_op: Operation) -> tuple[int, int]:
        """Extract the pair of qubit indices being swapped.

        Args:
            swap_op: SWAP operation.

        Returns:
            Tuple of two qubit indices.
        """
        try:
            attr1 = swap_op.attributes.get("qubit1")
            attr2 = swap_op.attributes.get("qubit2")
            idx1 = int(attr1.data) if attr1 and hasattr(attr1, "data") else 0  # type: ignore[attr-defined]
            idx2 = int(attr2.data) if attr2 and hasattr(attr2, "data") else 0  # type: ignore[attr-defined]
            return (idx1, idx2)
        except:
            return (0, 0)


def optimize_draper_arithmetic(module: ModuleOp, **kwargs) -> ModuleOp:
    """Convenience function to optimize Draper arithmetic circuits.

    Args:
        module: Input MLIR module containing Draper arithmetic.
        **kwargs: Options passed to DraperOptimizer.

    Returns:
        Optimized MLIR module.
    """
    optimizer = DraperOptimizer(**kwargs)
    return optimizer.optimize_draper_circuit(module)
