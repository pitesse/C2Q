"""Quantum-Safe Dead Code Elimination Pass.

Removes operations whose *results* are unused, while staying conservative about
quantum semantics:

- Never removes multi-qubit gates (anything with >1 operand), to avoid
    accidentally deleting entangling operations.
- Preserves control-structure ops (module/function) and measurements.
- Preserves the last op in a function as an implicit "return" anchor for the
    SSA chain (many benchmarks end without an explicit return value).

Note: This pass is intentionally conservative; it focuses on pruning obviously
dead SSA-producing ops (including unused initializations).
"""

from xdsl.ir import OpResult, Operation
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
        if region and hasattr(region, "parent"):
            func_op = region.parent
            if isinstance(func_op, FuncOp):
                block = op.parent
                ops_list = list(block.ops)
                if ops_list and ops_list[-1] is op:
                    return False

    # quantum-safe: multi-qubit gates can have side effects via phase kickback
    # or entanglement, even if their target result appears unused.
    # keeping this conservative rule instead of trying to infer purity.
    if len(op.operands) > 1:
        return False

    # if the op has no SSA results (e.g., quantum.comment), don't touch it.
    # this avoids attribute errors and avoids making assumptions about effects.
    if len(op.results) == 0:
        return False

    # safe to remove: SSA-producing ops whose results are all unused.
    # (most quantum ops here have exactly one result.)
    def result_is_used(result: OpResult) -> bool:
        return any(True for _ in result.uses)

    return not any(result_is_used(result) for result in op.results)


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
