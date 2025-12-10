"""
Quantum-specific MLIR optimization passes.

This module implements optimization passes that understand quantum semantics
and can reduce resource requirements while preserving quantum correctness.

Key optimizations:
- Gate fusion and cancellation
- Phase rotation consolidation  
- Dead qubit elimination
- QFT depth reduction
- Register coalescing
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import math
from collections import defaultdict

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
        return (f"Optimization Results:\n"
                f"  Gates eliminated: {self.gates_eliminated}\n"
                f"  Phases consolidated: {self.phases_consolidated}\n" 
                f"  Qubits eliminated: {self.qubits_eliminated}\n"
                f"  Depth reduction: {self.depth_reduction}")


class QuantumOptimizer:
    """
    Main optimization engine for quantum MLIR.
    
    Applies a sequence of optimization passes that understand quantum
    gate semantics and can safely transform circuits while preserving
    computational results.
    """
    
    def __init__(self, epsilon: float = 1e-6):
        """
        Initialize optimizer.
        
        Args:
            epsilon: Threshold for eliminating negligible phase rotations
        """
        self.epsilon = epsilon
        self.stats = OptimizationStats()
        
    def optimize_module(self, module: ModuleOp) -> ModuleOp:
        """
        Apply all optimization passes to a quantum MLIR module iteratively.
        
        Runs optimization passes in a loop until no more changes occur.
        This allows "peeling away" layers - e.g., once outer Hadamards cancel,
        inner Phase gates become adjacent and can merge in the next iteration.
        
        Args:
            module: Input MLIR module containing quantum operations
            
        Returns:
            Optimized MLIR module with reduced resource requirements
        """
        print("🔧 Starting iterative quantum circuit optimization...")
        
        iteration = 0
        max_iterations = 10  # Safety limit to prevent infinite loops
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n  🔄 Iteration {iteration}")
            
            # Reset per-iteration stats
            prev_gates = self.stats.gates_eliminated
            prev_phases = self.stats.phases_consolidated
            
            # Pass 1: Gate cancellation (X-X = I, H-H = I, etc.)
            self._eliminate_gate_cancellations(module)
            
            # Pass 2: Phase consolidation (combine rotations)
            self._consolidate_phase_rotations(module)
            
            # Pass 3: Dead code elimination
            self._eliminate_dead_qubits(module)
            
            # Pass 4: QFT optimization (reduce precision for small values)
            self._optimize_qft_precision(module)
            
            # Pass 5: Register coalescing (reuse registers when possible)
            self._coalesce_registers(module)
            
            # Check if any changes were made in this iteration
            gates_this_iter = self.stats.gates_eliminated - prev_gates
            phases_this_iter = self.stats.phases_consolidated - prev_phases
            changes_this_iter = gates_this_iter + phases_this_iter
            
            print(f"    Changes this iteration: {changes_this_iter} (gates: {gates_this_iter}, phases: {phases_this_iter})")
            
            if changes_this_iter == 0:
                print(f"\n  ✅ Converged after {iteration} iteration(s)")
                break
        
        if iteration >= max_iterations:
            print(f"\n  ⚠️  Reached maximum iterations ({max_iterations})")
        
        print(f"\n🏆 Optimization complete!")
        print(self.stats)
        
        return module
    
    def _eliminate_gate_cancellations(self, module: ModuleOp) -> None:
        """
        Remove pairs of gates that cancel out (X-X, H-H, etc.).
        
        This pass identifies consecutive inverse operations and eliminates them:
        - NOT followed by NOT on same qubit
        - Hadamard followed by Hadamard on same qubit  
        - Phase rotation followed by negative phase rotation
        """
        print("  🗑️  Pass 1: Gate cancellation...")
        
        operations = list(module.walk())
        to_remove = set()
        
        for i, op in enumerate(operations[:-1]):
            if op in to_remove:
                continue
                
            next_op = operations[i + 1]
            if next_op in to_remove:
                continue
                
            # Check for NOT gate cancellation (X·X = I)
            if (hasattr(op, 'name') and hasattr(next_op, 'name') and
                op.name == "quantum.OnQubit_not" and 
                next_op.name == "quantum.OnQubit_not"):
                
                if self._same_qubit_target(op, next_op):
                    to_remove.add(op)
                    to_remove.add(next_op)
                    self.stats.gates_eliminated += 2
                    
            # Check for Hadamard cancellation (H·H = I)  
            elif (hasattr(op, 'name') and hasattr(next_op, 'name') and
                  op.name == "quantum.OnQubit_hadamard" and
                  next_op.name == "quantum.OnQubit_hadamard"):
                  
                if self._same_qubit_target(op, next_op):
                    to_remove.add(op)
                    to_remove.add(next_op)
                    self.stats.gates_eliminated += 2
                    
            # Check for phase rotation cancellation
            elif (hasattr(op, 'name') and hasattr(next_op, 'name') and
                  op.name == "quantum.OnQubit_controlled_phase" and
                  next_op.name == "quantum.OnQubit_controlled_phase"):
                  
                if self._opposite_phase_rotations(op, next_op):
                    to_remove.add(op)
                    to_remove.add(next_op)
                    self.stats.gates_eliminated += 2
        
        # Remove identified operations (need to detach first)
        for op in to_remove:
            if op.parent is not None:
                op.detach()
            op.erase()
            
        print(f"    Eliminated {len(to_remove)} redundant gates")
    
    def _consolidate_phase_rotations(self, module: ModuleOp) -> None:
        """
        Combine consecutive phase rotations on the same qubit pair (SAFE VERSION).
        
        Only merges adjacent controlled-phase operations that:
        - Are both OnQubit_controlled_phase
        - Share the exact same operands (control and target SSAValues)
        - Are strictly adjacent in the operation sequence
        
        This ensures we never incorrectly merge phases that have intervening
        operations that would change the semantics.
        """
        print("  🔄 Pass 2: Phase consolidation (safe adjacency)...")
        
        # Get operations in linear order
        operations = list(module.walk())
        to_remove = set()
        consolidated = 0
        
        i = 0
        while i < len(operations) - 1:
            op = operations[i]
            
            # Skip if already marked for removal
            if op in to_remove:
                i += 1
                continue
            
            # Check if this is a controlled-phase operation
            if not (hasattr(op, 'name') and op.name == "quantum.OnQubit_controlled_phase"):
                i += 1
                continue
            
            # Look for consecutive controlled-phase operations on same qubits
            next_op = operations[i + 1]
            
            if (hasattr(next_op, 'name') and 
                next_op.name == "quantum.OnQubit_controlled_phase" and
                next_op not in to_remove):
                
                # Check if they operate on the same qubit pair
                if self._same_phase_target(op, next_op):
                    # Merge phases: add next_op's phase to op's phase
                    phase1 = self._get_phase_angle(op)
                    phase2 = self._get_phase_angle(next_op)
                    combined_phase = phase1 + phase2
                    
                    # Update first operation with combined phase
                    self._set_phase_angle(op, combined_phase)
                    
                    # Mark second operation for removal
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
    
    def _eliminate_dead_qubits(self, module: ModuleOp) -> None:
        """
        Remove quantum registers that are never used after initialization.
        
        This is particularly useful after variable scoping where some
        intermediate registers may become unreferenced.
        """
        print("  🧹 Pass 3: Dead qubit elimination...")
        
        # Find all quantum.init operations
        init_ops = [op for op in module.walk() if hasattr(op, 'name') and op.name == "quantum.init"]
        
        eliminated = 0
        for init_op in init_ops:
            if self._is_dead_register(init_op):
                # Remove the entire chain of operations on this dead register
                self._remove_register_chain(init_op)
                eliminated += 1
                self.stats.qubits_eliminated += 1
                
        print(f"    Eliminated {eliminated} dead registers")
    
    def _optimize_qft_precision(self, module: ModuleOp) -> None:
        """
        Reduce QFT precision by eliminating negligible phase rotations.
        
        For small phase angles (< epsilon), the quantum effect is negligible
        and the gates can be safely removed to reduce circuit depth.
        """
        print("  📐 Pass 4: QFT precision optimization...")
        
        eliminated = 0
        for op in list(module.walk()):
            if hasattr(op, 'name') and op.name == "quantum.OnQubit_controlled_phase":
                phase = self._get_phase_angle(op)
                if abs(phase) < self.epsilon:
                    if op.parent is not None:
                        op.detach()
                    op.erase()
                    eliminated += 1
                    self.stats.gates_eliminated += 1
                    
        print(f"    Eliminated {eliminated} negligible phase rotations")
    
    def _coalesce_registers(self, module: ModuleOp) -> None:
        """
        Reuse quantum registers when their lifetimes don't overlap.
        
        This optimization identifies registers that are never used simultaneously
        and merges them to reduce the total qubit count.
        """
        print("  🔗 Pass 5: Register coalescing...")
        
        # This is a complex optimization that requires lifetime analysis
        # For now, implement a simple version that identifies obvious cases
        
        # TODO: Implement full register lifetime analysis
        print("    Register coalescing analysis (placeholder)")
    
    # === Helper Methods ===
    
    def _same_qubit_target(self, op1: Operation, op2: Operation) -> bool:
        """Check if two operations target the same qubit."""
        # Extract qubit indices from operations
        try:
            idx1 = op1.attributes.get("index")
            idx2 = op2.attributes.get("index") 
            reg1 = op1.operands[0] if op1.operands else None
            reg2 = op2.operands[0] if op2.operands else None
            
            return (idx1 == idx2 and reg1 == reg2)
        except:
            return False
    
    def _same_phase_target(self, op1: Operation, op2: Operation) -> bool:
        """Check if two controlled-phase operations target the same qubit pair."""
        try:
            # For controlled-phase, we need to check both control and target
            # Operands are typically: [control_register, target_register]
            if len(op1.operands) < 2 or len(op2.operands) < 2:
                return False
            
            control1 = op1.operands[0]
            target1 = op1.operands[1]
            control2 = op2.operands[0]
            target2 = op2.operands[1]
            
            # Get indices from attributes
            control_idx1 = op1.attributes.get("control_index", 0)
            target_idx1 = op1.attributes.get("target_index", 0)
            control_idx2 = op2.attributes.get("control_index", 0)
            target_idx2 = op2.attributes.get("target_index", 0)
            
            # Check if same control and target
            same_control = (control1 == control2 and control_idx1 == control_idx2)
            same_target = (target1 == target2 and target_idx1 == target_idx2)
            
            return same_control and same_target
        except:
            return False
    
    def _opposite_phase_rotations(self, op1: Operation, op2: Operation) -> bool:
        """Check if two phase rotations are opposite and cancel out."""
        try:
            phase1 = self._get_phase_angle(op1)
            phase2 = self._get_phase_angle(op2) 
            
            # Check if they target same qubits and have opposite phases
            same_target = self._same_qubit_target(op1, op2)
            opposite_phase = abs(phase1 + phase2) < self.epsilon
            
            return same_target and opposite_phase
        except:
            return False
    
    def _get_phase_rotation_key(self, op: Operation) -> Optional[Tuple[str, int, str, int]]:
        """Extract (control_reg, control_idx, target_reg, target_idx) key."""
        try:
            # This would need to be adapted based on your exact MLIR structure
            control_reg = str(op.operands[0])
            target_reg = str(op.operands[1])
            
            # Get index attributes properly
            control_attr = op.attributes.get("control_index")
            target_attr = op.attributes.get("target_index")
            
            control_idx = int(control_attr.data) if control_attr and hasattr(control_attr, 'data') else 0  # type: ignore[attr-defined]
            target_idx = int(target_attr.data) if target_attr and hasattr(target_attr, 'data') else 0  # type: ignore[attr-defined]
            
            return (control_reg, control_idx, target_reg, target_idx)
        except:
            return None
    
    def _get_phase_angle(self, op: Operation) -> float:
        """Extract phase angle from controlled phase operation."""
        try:
            attr = op.attributes.get("phase")
            if attr is None:
                return 0.0
            # FloatAttr has .data property containing the float value
            if hasattr(attr, 'data'):
                return float(attr.data)  # type: ignore[attr-defined]
            return 0.0
        except:
            return 0.0
    
    def _set_phase_angle(self, op: Operation, phase: float) -> None:
        """Set phase angle for controlled phase operation."""
        try:
            from xdsl.dialects.builtin import FloatAttr, Float64Type
            op.attributes["phase"] = FloatAttr(phase, Float64Type())
        except:
            pass
    
    def _is_dead_register(self, init_op: Operation) -> bool:
        """Check if a register is never used after initialization."""
        # This requires data flow analysis to determine if the register
        # is referenced by any subsequent operations
        
        # Simple heuristic: if the register result is never used
        try:
            result = init_op.results[0] if init_op.results else None
            # IRUses is iterable, check if it has any uses
            return result is not None and not any(True for _ in result.uses)
        except:
            return False
    
    def _remove_register_chain(self, init_op: Operation) -> None:
        """Remove a register and all operations that depend on it."""
        if init_op.parent is not None:
            init_op.detach()
        init_op.erase()


def optimize_quantum_module(module: ModuleOp, **kwargs) -> ModuleOp:
    """
    Convenience function to optimize a quantum MLIR module.
    
    Args:
        module: Input MLIR module
        **kwargs: Options passed to QuantumOptimizer
        
    Returns:
        Optimized MLIR module
    """
    optimizer = QuantumOptimizer(**kwargs)
    return optimizer.optimize_module(module)
