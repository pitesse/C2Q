"""Quantum-Safe Dead Code Elimination Pass

Removes unused quantum operations while preserving multi-qubit gates that may
have side effects through phase kickback or entanglement. This optimization is
safe for quantum circuits as it only eliminates single-qubit gates with no uses.

Key safety features:
- Never removes multi-qubit gates (CNOT, controlled-phase, SWAP)
- Preserves measurement operations and function returns
- Only eliminates unused single-qubit gates (NOT, Hadamard, Pauli)
"""

from xdsl.ir import Operation
from xdsl.pattern_rewriter import PatternRewriter, RewritePattern
from xdsl.dialects.builtin import ModuleOp

from ...dialects.quantum_dialect import FuncOp, MeasureOp


def is_trivially_dead(op: Operation) -> bool:
    """Check if an operation can be safely removed as dead code.
    
    Implements quantum-safe dead code detection by preserving operations that:
    1. Are control structures (ModuleOp, FuncOp)
    2. Have observable effects (MeasureOp)
    3. Serve as function return values (last operation in FuncOp)
    4. Are multi-qubit gates (may cause phase kickback or entanglement)
    
    Args:
        op: Operation to check for liveness.
        
    Returns:
        True if the operation can be safely removed, False otherwise.
    """
    # these types of operations are never dead
    if isinstance(op, ModuleOp) or isinstance(op, FuncOp) or isinstance(op, MeasureOp):
        return False
    
    # check if this is the last operation in a function (implicit return value)
    if op.parent is not None:
        region = op.parent.parent
        if region and hasattr(region, 'parent'):
            func_op = region.parent
            if isinstance(func_op, FuncOp):
                block = op.parent
                ops_list = list(block.ops)
                if ops_list and ops_list[-1] is op:
                    return False
    
    # quantum-safe: multi-qubit gates can have side effects via phase kickback
    # or entanglement, even if their target result appears unused
    if len(op.operands) > 1:
        return False
    
    # additional safety: check operation name patterns for multi-qubit gates
    if hasattr(op, 'name'):
        op_name = str(op.name).lower()
        unsafe_patterns = ['cnot', 'controlled', 'ccnot', 'swap', 'phase']
        if any(pattern in op_name for pattern in unsafe_patterns):
            return False
    
    # safe to remove: single-qubit gates with unused results
    return not op.res.uses  # type: ignore[attr-defined]

class RemoveUnusedOperations(RewritePattern):
    """Pattern rewriter for quantum-safe dead code elimination.
    
    Removes unused operations from quantum circuits while preserving correctness.
    Only eliminates single-qubit gates with no uses, ensuring multi-qubit gates
    are never removed as they may affect control qubits through phase kickback.
    
    Methods:
        match_and_rewrite: Identifies and removes dead operations.
    """

    def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter) -> None:
        """Match and remove dead operations from the circuit.
        
        Args:
            op: Operation to check for dead code elimination.
            rewriter: Pattern rewriter for applying transformations.
        """
        if is_trivially_dead(op) and op.parent is not None:
            rewriter.erase_op(op)