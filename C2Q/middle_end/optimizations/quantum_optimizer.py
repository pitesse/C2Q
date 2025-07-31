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
        Apply all optimization passes to a quantum MLIR module.
        
        Args:
            module: Input MLIR module containing quantum operations
            
        Returns:
            Optimized MLIR module with reduced resource requirements
        """
        print("🔧 Starting quantum circuit optimization...")
        
        # Pass 1: Gate cancellation (X-X = I, etc.)
        self._eliminate_gate_cancellations(module)
        
        # Pass 2: Phase consolidation (combine rotations)
        self._consolidate_phase_rotations(module)
        
        # Pass 3: Dead code elimination
        self._eliminate_dead_qubits(module)
        
        # Pass 4: QFT optimization (reduce precision for small values)
        self._optimize_qft_precision(module)
        
        # Pass 5: Register coalescing (reuse registers when possible)
        self._coalesce_registers(module)
        
        print(f"✅ Optimization complete!")
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
        Combine consecutive phase rotations on the same qubit pair.
        
        Multiple controlled phase rotations between the same control and target
        qubits can be combined: R(θ₁)·R(θ₂) = R(θ₁ + θ₂)
        """
        print("  🔄 Pass 2: Phase consolidation...")
        
        # Group phase rotations by (control_qubit, target_qubit)
        phase_groups: Dict[Tuple[str, int, str, int], List[Operation]] = defaultdict(list)
        
        for op in module.walk():
            if hasattr(op, 'name') and op.name == "quantum.OnQubit_controlled_phase":
                key = self._get_phase_rotation_key(op)
                if key:
                    phase_groups[key].append(op)
        
        consolidated = 0
        for key, ops in phase_groups.items():
            if len(ops) > 1:
                # Consolidate phases
                total_phase = sum(self._get_phase_angle(op) for op in ops)
                
                # Keep first operation, update its phase
                first_op = ops[0]
                self._set_phase_angle(first_op, total_phase)
                
                # Remove subsequent operations
                for op in ops[1:]:
                    if op.parent is not None:
                        op.detach()
                    op.erase()
                    
                consolidated += len(ops) - 1
                self.stats.phases_consolidated += len(ops) - 1
        
        print(f"    Consolidated {consolidated} phase rotations")
    
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
            control_idx = op.attributes.get("control_index", 0)
            target_reg = str(op.operands[1])
            target_idx = op.attributes.get("target_index", 0)
            
            return (control_reg, control_idx, target_reg, target_idx)
        except:
            return None
    
    def _get_phase_angle(self, op: Operation) -> float:
        """Extract phase angle from controlled phase operation."""
        try:
            return float(op.attributes.get("phase", 0.0))
        except:
            return 0.0
    
    def _set_phase_angle(self, op: Operation, phase: float) -> None:
        """Set phase angle for controlled phase operation.""" 
        try:
            op.attributes["phase"] = phase
        except:
            pass
    
    def _is_dead_register(self, init_op: Operation) -> bool:
        """Check if a register is never used after initialization."""
        # This requires data flow analysis to determine if the register
        # is referenced by any subsequent operations
        
        # Simple heuristic: if the register result is never used
        try:
            result = init_op.results[0] if init_op.results else None
            return result is not None and len(result.uses) == 0
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
