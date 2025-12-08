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
    
    # if the result of the operation is never used then it is dead
    return not op.res.uses

# Class to drive the removal of unused operations in the main program.
class RemoveUnusedOperations(RewritePattern):

    def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter):
        if is_trivially_dead(op) and op.parent is not None:
            rewriter.erase_op(op)