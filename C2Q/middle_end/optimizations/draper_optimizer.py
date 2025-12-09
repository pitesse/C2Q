"""
Specialized optimizations for Draper QFT-based arithmetic circuits.

This module contains optimizations specifically designed for the quantum arithmetic
algorithms used in the C-to-Quantum compiler, particularly Draper's QFT-based
addition and subtraction.
"""

import math
from typing import List, Dict, Set, Optional
from collections import defaultdict

from xdsl.ir import SSAValue, Operation
from xdsl.dialects.builtin import ModuleOp

from .quantum_optimizer import OptimizationStats


class DraperOptimizer:
    """
    Optimizations specific to Draper QFT arithmetic circuits.
    
    These optimizations understand the structure of QFT-based arithmetic
    and can make intelligent decisions about precision, gate elimination,
    and circuit depth reduction.
    """
    
    def __init__(self, precision_threshold: float = 1e-3):
        """
        Initialize Draper-specific optimizer.
        
        Args:
            precision_threshold: Minimum phase angle to keep (eliminates smaller rotations)
        """
        self.precision_threshold = precision_threshold
        self.stats = OptimizationStats()
    
    def optimize_draper_circuit(self, module: ModuleOp) -> ModuleOp:
        """
        Apply Draper-specific optimizations iteratively to reduce arithmetic circuit complexity.
        
        Runs optimization passes in a loop until convergence. This allows "peeling away" layers:
        - Iteration 1: Cancel outer Hadamards (H-H = I at QFT/IQFT boundaries)
        - Iteration 2: Merge now-adjacent phase gates from inner QFT layers
        - Iteration 3+: Continue until no more improvements
        
        Key optimizations:
        1. Eliminate high-precision phase rotations for small operands
        2. Optimize QFT depth based on actual register usage
        3. Consolidate adjacent phase rotations in frequency domain
        4. Remove redundant SWAP operations in QFT
        5. Hadamard cancellation at QFT/IQFT boundaries
        """
        print("🧮 Starting iterative Draper arithmetic optimization...")
        
        iteration = 0
        max_iterations = 10  # Safety limit
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n  🔄 Draper Iteration {iteration}")
            
            # Track changes in this iteration
            prev_gates = self.stats.gates_eliminated
            prev_phases = self.stats.phases_consolidated
            
            # Draper-specific passes
            self._optimize_phase_precision(module)
            self._consolidate_adjacent_phases(module)  # New: merge adjacent phases
            self._cancel_hadamard_pairs(module)  # New: H-H cancellation
            self._optimize_qft_depth(module) 
            self._eliminate_redundant_swaps(module)
            self._optimize_zero_operands(module)
            
            # Check for convergence
            gates_this_iter = self.stats.gates_eliminated - prev_gates
            phases_this_iter = self.stats.phases_consolidated - prev_phases
            changes_this_iter = gates_this_iter + phases_this_iter
            
            print(f"    Changes: {changes_this_iter} (gates: {gates_this_iter}, phases: {phases_this_iter})")
            
            if changes_this_iter == 0:
                print(f"\n  ✅ Draper optimization converged after {iteration} iteration(s)")
                break
        
        if iteration >= max_iterations:
            print(f"\n  ⚠️  Reached maximum Draper iterations ({max_iterations})")
        
        print("\n🏆 Draper optimization complete!")
        print(self.stats)
        
        return module
    
    def _optimize_phase_precision(self, module: ModuleOp) -> None:
        """
        Eliminate negligible phase rotations in Draper arithmetic.
        
        For small integer operands, many of the high-precision phase rotations
        (like π/256, π/512) have negligible effect and can be safely removed.
        """
        print("  📏 Optimizing phase precision...")
        
        eliminated = 0
        for op in list(module.walk()):
            if hasattr(op, 'name') and op.name == "quantum.OnQubit_controlled_phase":
                phase = abs(self._extract_phase(op))
                
                # Eliminate very small phase rotations
                if phase < self.precision_threshold:
                    # Replace the result with the input (effectively no-op)
                    if len(op.results) > 0 and len(op.operands) > 1:
                        # The result should be the target register (operand 1)
                        op.results[0].replace_by(op.operands[1])
                    
                    if op.parent is not None:
                        op.detach()
                    op.erase()
                    eliminated += 1
                    self.stats.gates_eliminated += 1
                    
        print(f"    Eliminated {eliminated} negligible phase rotations")
    
    def _optimize_qft_depth(self, module: ModuleOp) -> None:
        """
        Reduce QFT depth by analyzing actual register bit usage.
        
        If we know that operands are small (e.g., fit in 4 bits instead of 8),
        we can eliminate the higher-order QFT operations.
        """
        print("  🔍 Analyzing QFT depth requirements...")
        
        # Analyze the actual bit patterns used in the circuit
        # This is a heuristic approach - in practice, you'd want static analysis
        
        # Look for patterns where higher-order bits are never set
        bit_usage = self._analyze_bit_usage(module)
        # Default to 7 (full 8-bit) if no bits found (e.g., dynamic inputs)
        max_significant_bit = max(bit_usage) if bit_usage else 7
        
        # If we're only using lower bits, we can eliminate higher-order QFT operations
        if max_significant_bit < 7:  # Default 8-bit assumption
            eliminated = self._eliminate_unused_qft_operations(module, max_significant_bit + 1)
            self.stats.depth_reduction += eliminated
            print(f"    Reduced QFT depth to {max_significant_bit + 1} bits")
        else:
            print(f"    All bits ({max_significant_bit + 1}) in use, no QFT depth reduction possible")
    
    def _eliminate_redundant_swaps(self, module: ModuleOp) -> None:
        """
        Remove redundant SWAP operations in QFT implementation.
        
        Sometimes SWAP-SWAP pairs can cancel out, or SWAPs can be absorbed
        into the computation rather than performed explicitly.
        """
        print("  🔄 Eliminating redundant SWAP operations...")
        
        swaps = [op for op in module.walk() if op.name == "quantum.OnQubit_swap"]
        eliminated = 0
        
        # Look for SWAP-SWAP cancellations
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
                
        print(f"    Eliminated {eliminated} redundant SWAPs")
    
    def _optimize_zero_operands(self, module: ModuleOp) -> None:
        """
        Optimize arithmetic operations involving zero operands.
        
        Special cases:
        - A + 0 = A (no operation needed)
        - A - 0 = A (no operation needed)  
        - 0 + B = B (no operation needed)
        - A * 0 = 0 (replace with register clear)
        """
        print("  0️⃣  Optimizing zero operand cases...")
        
        # This requires analyzing the data flow to identify zero constants
        # For now, implement detection of obvious zero patterns
        
        zero_optimizations = self._detect_zero_arithmetic(module)
        for optimization in zero_optimizations:
            self._apply_zero_optimization(optimization)
            
        print(f"    Applied {len(zero_optimizations)} zero-operand optimizations")
    
    def _consolidate_adjacent_phases(self, module: ModuleOp) -> None:
        """
        Consolidate adjacent controlled-phase operations on the same qubit pair.
        
        Multiple controlled phase rotations between the same control and target
        qubits can be combined: R(θ₁)·R(θ₂) = R(θ₁ + θ₂)
        
        This is crucial after Hadamard cancellation exposes adjacent phases.
        """
        print("  🔄 Consolidating adjacent phase rotations...")
        
        operations = list(module.walk())
        to_remove = set()
        consolidated = 0
        
        i = 0
        while i < len(operations) - 1:
            op = operations[i]
            
            if op in to_remove:
                i += 1
                continue
            
            # Check if this is a controlled-phase operation
            if not (hasattr(op, 'name') and op.name == "quantum.OnQubit_controlled_phase"):
                i += 1
                continue
            
            # Look for consecutive controlled-phase on same qubits
            next_op = operations[i + 1]
            
            if (hasattr(next_op, 'name') and 
                next_op.name == "quantum.OnQubit_controlled_phase" and
                next_op not in to_remove):
                
                # Check if they operate on the same qubit pair
                if self._same_phase_qubits(op, next_op):
                    # Merge phases
                    phase1 = self._extract_phase(op)
                    phase2 = self._extract_phase(next_op)
                    combined_phase = phase1 + phase2
                    
                    # Update first operation
                    self._set_phase(op, combined_phase)
                    
                    # Replace uses of next_op's result with op's result
                    if len(next_op.results) > 0 and len(op.results) > 0:
                        next_op.results[0].replace_by(op.results[0])
                    
                    # Mark second for removal
                    to_remove.add(next_op)
                    consolidated += 1
                    self.stats.phases_consolidated += 1
                    
                    # Don't increment i - check if we can merge more
                    continue
            
            i += 1
        
        # Remove marked operations
        for op in to_remove:
            if op.parent is not None:
                op.detach()
            op.erase()
        
        print(f"    Consolidated {consolidated} adjacent phase rotations")
    
    def _cancel_hadamard_pairs(self, module: ModuleOp) -> None:
        """
        Cancel pairs of Hadamard gates on the same qubit (H·H = I).
        
        This is especially important at QFT/IQFT boundaries where the trailing
        Hadamard of a QFT immediately precedes the leading Hadamard of an IQFT.
        
        Cancelling these exposes the inner phase gates for consolidation.
        """
        print("  ✂️  Cancelling Hadamard pairs (H·H = I)...")
        
        operations = list(module.walk())
        to_remove = set()
        cancelled = 0
        
        for i in range(len(operations) - 1):
            op = operations[i]
            
            if op in to_remove:
                continue
            
            next_op = operations[i + 1]
            if next_op in to_remove:
                continue
            
            # Check for Hadamard-Hadamard pair
            if (hasattr(op, 'name') and hasattr(next_op, 'name') and
                op.name == "quantum.OnQubit_hadamard" and
                next_op.name == "quantum.OnQubit_hadamard"):
                
                # Check if same qubit
                if self._same_qubit(op, next_op):
                    to_remove.add(op)
                    to_remove.add(next_op)
                    cancelled += 2
                    self.stats.gates_eliminated += 2
        
        # Remove identified pairs
        for op in to_remove:
            if op.parent is not None:
                op.detach()
            op.erase()
        
        print(f"    Cancelled {cancelled} Hadamard gates ({cancelled//2} pairs)")
    
    # === Helper Methods ===
    
    def _same_qubit(self, op1: Operation, op2: Operation) -> bool:
        """Check if two operations target the same qubit."""
        try:
            # Get operands and indices
            if len(op1.operands) == 0 or len(op2.operands) == 0:
                return False
            
            reg1 = op1.operands[0]
            reg2 = op2.operands[0]
            
            idx1 = op1.attributes.get("index", 0)
            idx2 = op2.attributes.get("index", 0)
            
            return (reg1 == reg2 and idx1 == idx2)
        except:
            return False
    
    def _same_phase_qubits(self, op1: Operation, op2: Operation) -> bool:
        """Check if two controlled-phase operations target the same qubit pair."""
        try:
            # For controlled-phase, check both control and target
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
            
            same_control = (control1 == control2 and control_idx1 == control_idx2)
            same_target = (target1 == target2 and target_idx1 == target_idx2)
            
            return same_control and same_target
        except:
            return False
    
    def _set_phase(self, op: Operation, phase: float) -> None:
        """Set phase angle for controlled-phase operation."""
        try:
            op.attributes["phase"] = phase
        except:
            pass
    
    def _extract_phase(self, op: Operation) -> float:
        """Extract phase angle from controlled phase operation."""
        try:
            attr = op.attributes.get("phase")
            if attr is None:
                return 0.0
            # Try different XDSL attribute access patterns
            if hasattr(attr, 'value'):
                if hasattr(attr.value, 'data'):
                    return float(attr.value.data)
                return float(attr.value)
            elif hasattr(attr, 'data'):
                return float(attr.data)
            elif hasattr(attr, 'parameters') and len(attr.parameters) > 0:
                return float(attr.parameters[0].data)
            else:
                return float(attr)
        except:
            return 0.0
    
    def _analyze_bit_usage(self, module: ModuleOp) -> Set[int]:
        """
        Analyze which bit positions are actually used in the circuit.
        
        A bit is considered "used" if it appears in ANY quantum operation's
        index, target_index, or control_index attributes. This ensures we
        don't remove QFT operations for bits that participate in Fourier-domain
        arithmetic (like controlled phase rotations in multiplication).
        """
        used_bits = set()
        
        # Iterate through ALL quantum operations
        for op in module.walk():
            if hasattr(op, 'name') and hasattr(op, 'attributes'):
                try:
                    # Check all relevant index attributes
                    for attr_name in ['index', 'target_index', 'control_index']:
                        attr = op.attributes.get(attr_name)
                        if attr is not None:
                            # Extract the integer value using multiple access patterns
                            val = None
                            if hasattr(attr, 'value'):
                                if hasattr(attr.value, 'data'):
                                    val = int(attr.value.data)
                                else:
                                    val = int(attr.value)
                            elif hasattr(attr, 'data'):
                                val = int(attr.data)
                            else:
                                val = int(attr)
                            
                            if val is not None:
                                used_bits.add(val)
                except:
                    # If we can't extract the index, skip this operation
                    pass
                    
        return used_bits
    
    def _eliminate_unused_qft_operations(self, module: ModuleOp, max_bits: int) -> int:
        """
        Remove QFT operations on unused higher-order bits.
        
        Args:
            module: MLIR module
            max_bits: Maximum number of bits actually needed
            
        Returns:
            Number of operations eliminated
        """
        eliminated = 0
        
        for op in list(module.walk()):
            # Remove operations on bits >= max_bits
            if self._operates_on_high_bits(op, max_bits):
                if op.parent is not None:
                    op.detach()
                op.erase()
                eliminated += 1
                self.stats.gates_eliminated += 1
                
        return eliminated
    
    def _operates_on_high_bits(self, op: Operation, max_bits: int) -> bool:
        """Check if operation works on bits >= max_bits."""
        try:
            if hasattr(op, 'attributes'):
                # Check index attribute
                attr = op.attributes.get("index")
                if attr is not None:
                    val = None
                    if hasattr(attr, 'value'):
                        if hasattr(attr.value, 'data'):
                            val = int(attr.value.data)
                        else:
                            val = int(attr.value)
                    elif hasattr(attr, 'data'):
                        val = int(attr.data)
                    else:
                        val = int(attr)
                    if val is not None and val >= max_bits:
                        return True
                    
                # Also check target_index for controlled operations
                target_attr = op.attributes.get("target_index")
                if target_attr is not None:
                    val = None
                    if hasattr(target_attr, 'value'):
                        if hasattr(target_attr.value, 'data'):
                            val = int(target_attr.value.data)
                        else:
                            val = int(target_attr.value)
                    elif hasattr(target_attr, 'data'):
                        val = int(target_attr.data)
                    else:
                        val = int(target_attr)
                    if val is not None and val >= max_bits:
                        return True
                    
        except:
            pass
            
        return False
    
    def _swaps_cancel(self, swap1: Operation, swap2: Operation) -> bool:
        """Check if two SWAP operations cancel each other out."""
        try:
            # Extract the qubit indices being swapped
            indices1 = self._get_swap_indices(swap1)
            indices2 = self._get_swap_indices(swap2)
            
            # SWAPs cancel if they swap the same pair of qubits
            return indices1 == indices2 or indices1 == indices2[::-1]
        except:
            return False
    
    def _get_swap_indices(self, swap_op: Operation) -> tuple:
        """Extract the pair of qubit indices being swapped."""
        try:
            idx1 = swap_op.attributes.get("qubit1", 0)
            idx2 = swap_op.attributes.get("qubit2", 0) 
            return (int(idx1), int(idx2))
        except:
            return (0, 0)
    
    def _detect_zero_arithmetic(self, module: ModuleOp) -> List[Dict]:
        """
        Detect arithmetic operations involving zero operands.
        
        Returns list of optimization opportunities.
        """
        optimizations = []
        
        # This would require more sophisticated analysis of the data flow
        # to detect which registers contain zero values
        
        # For now, return empty list (placeholder)
        return optimizations
    
    def _apply_zero_optimization(self, optimization: Dict) -> None:
        """Apply a specific zero-operand optimization."""
        # Placeholder for applying detected optimizations
        pass


def optimize_draper_arithmetic(module: ModuleOp, **kwargs) -> ModuleOp:
    """
    Convenience function to optimize Draper arithmetic circuits.
    
    Args:
        module: Input MLIR module containing Draper arithmetic
        **kwargs: Options passed to DraperOptimizer
        
    Returns:
        Optimized MLIR module
    """
    optimizer = DraperOptimizer(**kwargs)
    return optimizer.optimize_draper_circuit(module)
