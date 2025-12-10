from xdsl.ir import Operation
from xdsl.pattern_rewriter import PatternRewriter, RewritePattern
from xdsl.dialects.builtin import ModuleOp

from ...dialects.quantum_dialect import FuncOp, MeasureOp

# Check if the operation is not used in the following part of the program.
def is_trivially_dead(op: Operation) -> bool:

    # these types of operations are never dead
    if isinstance(op, ModuleOp) or isinstance(op, FuncOp) or isinstance(op, MeasureOp):
        return False
    
    # Check if this is the last operation in a FuncOp (implicit return value)
    if op.parent is not None:
        # op.parent is the Block
        # op.parent.parent is the Region  
        # op.parent.parent.parent is the FuncOp
        region = op.parent.parent
        if region and hasattr(region, 'parent'):
            func_op = region.parent
            if isinstance(func_op, FuncOp):
                # Get the block containing this operation
                block = op.parent
                ops_list = list(block.ops)
                if ops_list and ops_list[-1] is op:
                    # This is the last operation in the function - it's the return value
                    return False
    
    # QUANTUM-SAFE CHECK: Multi-qubit gates can have side effects via phase kickback
    # or entanglement, even if their target result appears unused.
    # Do NOT remove operations with multiple operands (e.g., CNOT, controlled-phase, SWAP)
    if len(op.operands) > 1:
        return False
    
    # Additional safety check: operation name patterns that indicate multi-qubit gates
    if hasattr(op, 'name'):
        op_name = str(op.name).lower()
        unsafe_patterns = ['cnot', 'controlled', 'ccnot', 'swap', 'phase']
        if any(pattern in op_name for pattern in unsafe_patterns):
            return False
    
    # Safe to remove: single-qubit gates (Not, Hadamard, Pauli) with unused results
    # if the result of the operation is never used then it is dead
    return not op.res.uses  # type: ignore[attr-defined]

# Class to drive the removal of unused operations in the main program.
class RemoveUnusedOperations(RewritePattern):

    def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter):
        if is_trivially_dead(op) and op.parent is not None:
            rewriter.erase_op(op)