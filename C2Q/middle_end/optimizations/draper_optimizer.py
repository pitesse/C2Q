"""Specialized optimizations for Draper QFT-based arithmetic circuits.

This module contains optimizations specifically designed for the quantum arithmetic
algorithms used in the C-to-Quantum compiler, particularly Draper's QFT-based
addition and subtraction.
"""

from typing import Set, Optional
from dataclasses import dataclass

from xdsl.ir import SSAValue, Operation
from xdsl.dialects.builtin import Float64Type, FloatAttr, IntegerAttr, ModuleOp
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
)


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

    def optimize_draper_circuit(self, module: ModuleOp, verbose: bool = True) -> ModuleOp:
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
        def log(msg: str) -> None:
            if verbose:
                print(msg)

        log("[INFO] Starting iterative Draper arithmetic optimization...")

        iteration = 0
        max_iterations = 10

        while iteration < max_iterations:
            iteration += 1
            log(f"\n  [INFO] Draper Iteration {iteration}")

            prev_gates = self.stats.gates_eliminated
            prev_phases = self.stats.phases_consolidated

            changed = self._run_iteration(module, verbose=verbose)

            gates_this_iter = self.stats.gates_eliminated - prev_gates
            phases_this_iter = self.stats.phases_consolidated - prev_phases
            changes_this_iter = gates_this_iter + phases_this_iter

            log(
                f"    [INFO] Changes: {changes_this_iter} (gates: {gates_this_iter}, phases: {phases_this_iter})"
            )

            if changes_this_iter == 0 or not changed:
                log(f"\n  [OK] Draper optimization converged after {iteration} iteration(s)")
                break

        if iteration >= max_iterations:
            log(f"\n  [WARN] Reached maximum Draper iterations ({max_iterations})")
        log("\n[INFO] Draper optimization complete.")
        if verbose:
            print(self.stats)

        return module

    # ---------------------------------------------------------------------
    # xDSL rewrite patterns (applied via PatternRewriteWalker)
    # ---------------------------------------------------------------------

    @staticmethod
    def _int_attr(op: Operation, name: str) -> Optional[int]:
        attr = op.attributes.get(name)
        if isinstance(attr, IntegerAttr):
            return int(attr.value.data)
        # legacy/loose fallback
        if attr is not None and hasattr(attr, "data"):
            try:
                return int(attr.data)  # type: ignore[attr-defined]
            except Exception:
                return None
        return None

    @staticmethod
    def _float_attr(op: Operation, name: str) -> float:
        attr = op.attributes.get(name)
        if isinstance(attr, FloatAttr):
            return float(attr.value.data)
        if attr is None:
            return 0.0
        #  fallback -- try to extract float from various attribute types
        if hasattr(attr, "value"):
            try:
                v = attr.value  # type: ignore[attr-defined]
                if hasattr(v, "data"):
                    return float(v.data)  # type: ignore[attr-defined]
                return float(v)
            except Exception:
                return 0.0
        if hasattr(attr, "data"):
            try:
                return float(attr.data)  # type: ignore[attr-defined]
            except Exception:
                return 0.0
        try:
            return float(attr)  # type: ignore[arg-type]
        except Exception:
            return 0.0

    @staticmethod
    def _set_float_attr(op: Operation, name: str, value: float) -> None:
        op.attributes[name] = FloatAttr(float(value), Float64Type())

    class _EliminateNegligibleControlledPhase(RewritePattern):
        def __init__(self, optimizer: "DraperOptimizer") -> None:
            self.optimizer = optimizer

        def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter) -> None:
            if op.name != "quantum.OnQubit_controlled_phase":
                return
            phase = abs(self.optimizer._float_attr(op, "phase"))
            if phase >= self.optimizer.precision_threshold:
                return
            if not op.results or len(op.operands) < 2:
                return
            replacement = op.operands[1]
            result = op.results[0]
            for use in list(result.uses):
                use.operation.operands[use.index] = replacement
            rewriter.erase_op(op)
            self.optimizer.stats.gates_eliminated += 1

    class _ConsolidateAdjacentControlledPhases(RewritePattern):
        def __init__(self, optimizer: "DraperOptimizer") -> None:
            self.optimizer = optimizer

        def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter) -> None:
            if op.name != "quantum.OnQubit_controlled_phase":
                return
            nxt = op._next_op
            if nxt is None or nxt.name != "quantum.OnQubit_controlled_phase":
                return
            if not op.results or not nxt.results or len(op.operands) < 2 or len(nxt.operands) < 2:
                return

            cidx1 = self.optimizer._int_attr(op, "control_index")
            tidx1 = self.optimizer._int_attr(op, "target_index")
            cidx2 = self.optimizer._int_attr(nxt, "control_index")
            tidx2 = self.optimizer._int_attr(nxt, "target_index")
            if cidx1 is None or tidx1 is None or cidx2 is None or tidx2 is None:
                return
            if cidx1 != cidx2 or tidx1 != tidx2:
                return

            # SSA chaining: second must consume first's updated target register.
            if nxt.operands[1] != op.results[0]:
                return

            # control register may be unchanged (different register) or equal to the
            # updated target (same-register controlled phase).
            if op.operands[0] == op.operands[1]:
                if nxt.operands[0] != op.results[0] or nxt.operands[1] != op.results[0]:
                    return
            else:
                if nxt.operands[0] != op.operands[0]:
                    return

            combined = self.optimizer._float_attr(op, "phase") + self.optimizer._float_attr(nxt, "phase")
            self.optimizer._set_float_attr(op, "phase", combined)

            for use in list(nxt.results[0].uses):
                use.operation.operands[use.index] = op.results[0]

            rewriter.erase_op(nxt)
            self.optimizer.stats.phases_consolidated += 1

    class _CancelAdjacentHadamards(RewritePattern):
        def __init__(self, optimizer: "DraperOptimizer") -> None:
            self.optimizer = optimizer

        def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter) -> None:
            if op.name != "quantum.OnQubit_hadamard":
                return
            nxt = op._next_op
            if nxt is None or nxt.name != "quantum.OnQubit_hadamard":
                return
            if not op.results or not nxt.results or len(op.operands) < 1 or len(nxt.operands) < 1:
                return

            idx1 = self.optimizer._int_attr(op, "index")
            idx2 = self.optimizer._int_attr(nxt, "index")
            if idx1 is None or idx2 is None or idx1 != idx2:
                return
            if nxt.operands[0] != op.results[0]:
                return

            original = op.operands[0]
            final_res = nxt.results[0]
            for use in list(final_res.uses):
                use.operation.operands[use.index] = original

            rewriter.erase_op(nxt)
            rewriter.erase_op(op)
            self.optimizer.stats.gates_eliminated += 2

    class _CancelAdjacentSwaps(RewritePattern):
        def __init__(self, optimizer: "DraperOptimizer") -> None:
            self.optimizer = optimizer

        def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter) -> None:
            if op.name != "quantum.OnQubit_swap":
                return
            nxt = op._next_op
            if nxt is None or nxt.name != "quantum.OnQubit_swap":
                return
            if not op.results or not nxt.results or len(op.operands) < 1 or len(nxt.operands) < 1:
                return
            if nxt.operands[0] != op.results[0]:
                return

            a1 = self.optimizer._int_attr(op, "qubit1_index")
            b1 = self.optimizer._int_attr(op, "qubit2_index")
            a2 = self.optimizer._int_attr(nxt, "qubit1_index")
            b2 = self.optimizer._int_attr(nxt, "qubit2_index")
            if None in (a1, b1, a2, b2):
                return
            if not ((a1 == a2 and b1 == b2) or (a1 == b2 and b1 == a2)):
                return

            original = op.operands[0]
            final_res = nxt.results[0]
            for use in list(final_res.uses):
                use.operation.operands[use.index] = original

            rewriter.erase_op(nxt)
            rewriter.erase_op(op)
            self.optimizer.stats.gates_eliminated += 2

    class _EliminateHighBitOps(RewritePattern):
        def __init__(self, optimizer: "DraperOptimizer", max_bits: int) -> None:
            self.optimizer = optimizer
            self.max_bits = max_bits

        def _op_uses_high_bit(self, op: Operation) -> bool:
            # look for any known bit-index attrs.
            for key in (
                "index",
                "target_index",
                "control_index",
                "control1_index",
                "control2_index",
                "qubit1_index",
                "qubit2_index",
            ):
                v = self.optimizer._int_attr(op, key)
                if v is not None and v >= self.max_bits:
                    return True
            return False

        def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter) -> None:
            if not op.name.startswith("quantum."):
                return
            if op.name in ("quantum.func",):
                return
            if not self._op_uses_high_bit(op):
                return
            if not op.results or not op.operands:
                return

            replacement = op.operands[-1]
            result = op.results[0]
            for use in list(result.uses):
                use.operation.operands[use.index] = replacement
            rewriter.erase_op(op)
            self.optimizer.stats.gates_eliminated += 1
            self.optimizer.stats.depth_reduction += 1

    def _run_patterns(self, module: ModuleOp, patterns: list[RewritePattern]) -> bool:
        applier = GreedyRewritePatternApplier(patterns)
        walker = PatternRewriteWalker(applier)
        return bool(walker.rewrite_module(module))

    def _analyze_bit_usage(self, module: ModuleOp) -> Set[int]:
        used_bits: Set[int] = set()
        for op in module.walk():
            if not hasattr(op, "attributes"):
                continue
            for key in (
                "index",
                "target_index",
                "control_index",
                "control1_index",
                "control2_index",
                "qubit1_index",
                "qubit2_index",
            ):
                v = self._int_attr(op, key)
                if v is not None:
                    used_bits.add(v)
        return used_bits

    def _run_iteration(self, module: ModuleOp, verbose: bool) -> bool:
        def log(msg: str) -> None:
            if verbose:
                print(msg)

        log("  [INFO] Optimizing phase precision...")
        eliminated_phase = self._run_patterns(
            module, [self._EliminateNegligibleControlledPhase(self)]
        )

        log("  [INFO] Consolidating adjacent phase rotations...")
        consolidated = self._run_patterns(
            module, [self._ConsolidateAdjacentControlledPhases(self)]
        )

        log("  [INFO] Cancelling Hadamard pairs (H·H = I)...")
        cancelled_h = self._run_patterns(module, [self._CancelAdjacentHadamards(self)])

        log("  [INFO] Analyzing QFT depth requirements...")
        used_bits = self._analyze_bit_usage(module)
        max_significant_bit = max(used_bits) if used_bits else 7
        log(
            f"    [INFO] Max significant bit: {max_significant_bit} (cutoff={max_significant_bit + 1})"
        )
        eliminated_high_bits = self._run_patterns(
            module, [self._EliminateHighBitOps(self, max_significant_bit + 1)]
        )

        log("  [INFO] Eliminating redundant SWAP operations...")
        cancelled_swaps = self._run_patterns(module, [self._CancelAdjacentSwaps(self)])

        return bool(
            eliminated_phase
            or consolidated
            or cancelled_h
            or eliminated_high_bits
            or cancelled_swaps
        )

def optimize_draper_arithmetic(module: ModuleOp, verbose: bool = True, **kwargs) -> ModuleOp:
    """Convenience function to optimize Draper arithmetic circuits.

    Args:
        module: Input MLIR module containing Draper arithmetic.
        **kwargs: Options passed to DraperOptimizer.

    Returns:
        Optimized MLIR module.
    """
    optimizer = DraperOptimizer(**kwargs)
    return optimizer.optimize_draper_circuit(module, verbose=verbose)
