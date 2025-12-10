"""CCNOT decomposition optimization pass.

This module implements a pattern rewriting pass to transform CCNOT operations
into a sequence of CNOT, Hadamard, and T-gate operations for evaluation of
circuit performance using existing metrics.
"""

from xdsl.ir import Operation, SSAValue
from xdsl.pattern_rewriter import PatternRewriter, RewritePattern
from xdsl.builder import Builder
from xdsl.rewriter import InsertPoint
from xdsl.dialects.builtin import ModuleOp

from ...dialects.quantum_dialect import (
    HadamardOp,
    TGateOp,
    TDaggerGateOp,
    CNotOp,
    FuncOp,
)


class CCnot_decomposition(RewritePattern):
    """Pattern rewriter for decomposing CCNOT gates.

    Transforms CCNOT operations into a sequence of CNOT, Hadamard, and T-gate
    operations to enable evaluation using existing circuit performance metrics.

    Attributes:
        Builder: Builder instance for inserting new operations.
        passedOperation: Set of operations that have been processed.
    """

    Builder: Builder
    passedOperation: set

    def __init__(self) -> None:
        """Initialize the CCNOT decomposition pattern."""
        self.passedOperation = set()
    
    def fixnames(self, changed: SSAValue) -> None:
        """Recursively fix the names of SSAValues after a replacement.

        Args:
            changed: The SSAValue whose dependent operations need name updates.
        """
        uses = list(changed.uses)

        for use in uses:
            using_operation = use.operation
            target_idx = len(using_operation.operands) - 1
            if using_operation.operands[target_idx] == changed:
                if hasattr(using_operation, 'res'):
                    using_operation.res._name = changed._name.split("_")[0] + "_" + str(int(changed._name.split("_")[1])+1)  # type: ignore[attr-defined, union-attr]
                    self.fixnames(using_operation.res)  # type: ignore[attr-defined]

    def replace(self, old: SSAValue, new: SSAValue) -> None:
        """Replace old SSAValue with new one and fix dependent operation names.

        Args:
            old: The SSAValue to be replaced.
            new: The SSAValue to replace with.
        """
        uses = list(old.uses)

        for use in uses:
            using_operation = use.operation

            if using_operation in self.passedOperation:
                continue
            target_idx = len(using_operation.operands) - 1
            if using_operation.operands[target_idx] == old:
                using_operation.operands[target_idx] = new
                if hasattr(using_operation, 'res'):
                    using_operation.res._name = new._name.split("_")[0] + "_" + str(int(new._name.split("_")[1])+1)  # type: ignore[attr-defined, union-attr]
                    self.fixnames(using_operation.res)  # type: ignore[attr-defined]
            else:  # used as a control
                using_operation.operands[using_operation.operands.index(old)] = new

    def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter) -> None:
        """Match CCNOT operations and rewrite them into decomposed gates.

        Transforms each CCNOT operation into a sequence of CNOT, Hadamard, and
        T-gate operations according to standard decomposition.

        Args:
            op: The operation to match and potentially rewrite.
            rewriter: Pattern rewriter for performing transformations.
        """

        if isinstance(op,ModuleOp) or isinstance(op,FuncOp):
            return

        self.passedOperation.add(op)

        if op.name == "quantum.OnQubit_ccnot":
            self.builder = Builder(InsertPoint.before(op))

            if not (hasattr(op, 'control1') and hasattr(op, 'control2') and hasattr(op, 'target') and hasattr(op, 'res')):
                return

            control1 = op.control1  # type: ignore[attr-defined]

            control2 = op.control2  # type: ignore[attr-defined]

            target = op.target  # type: ignore[attr-defined]

            res = op.res  # type: ignore[attr-defined]

            h1_res = self.builder.insert(HadamardOp.from_value(target)).res
            h1_res._name = target._name.split('_')[0] +"_" + str(int(target._name.split('_')[1])+1)  # type: ignore[union-attr]
            self.passedOperation.add(h1_res.op)
            
            cnot1_res = self.builder.insert(CNotOp.from_value(control2, h1_res)).res
            cnot1_res._name = h1_res._name.split('_')[0] +"_" + str(int(h1_res._name.split('_')[1])+1)  # type: ignore[union-attr]
            self.passedOperation.add(cnot1_res.op)
        
            tcross1_res = self.builder.insert(TDaggerGateOp.from_value(cnot1_res)).res
            tcross1_res._name = cnot1_res._name.split('_')[0] +"_" + str(int(cnot1_res._name.split('_')[1])+1)
            self.passedOperation.add(tcross1_res.op)

            cnot2_res = self.builder.insert(CNotOp.from_value(control1, tcross1_res)).res
            cnot2_res._name = tcross1_res._name.split('_')[0] +"_" + str(int(tcross1_res._name.split('_')[1])+1)
            self.passedOperation.add(cnot2_res.op)

            t1_res = self.builder.insert(TGateOp.from_value(cnot2_res)).res
            t1_res._name = cnot2_res._name.split('_')[0] +"_" + str(int(cnot2_res._name.split('_')[1])+1)
            self.passedOperation.add(t1_res.op)

            cnot3_res = self.builder.insert(CNotOp.from_value(control2, t1_res)).res
            cnot3_res._name = t1_res._name.split('_')[0] +"_" + str(int(t1_res._name.split('_')[1])+1)
            self.passedOperation.add(cnot3_res.op)

            tcross2_res = self.builder.insert(TDaggerGateOp.from_value(cnot3_res)).res
            tcross2_res._name = cnot3_res._name.split('_')[0] +"_" + str(int(cnot3_res._name.split('_')[1])+1)
            self.passedOperation.add(tcross2_res.op)

            cnot4_res = self.builder.insert(CNotOp.from_value(control1, tcross2_res)).res
            cnot4_res._name = tcross2_res._name.split('_')[0] +"_" + str(int(tcross2_res._name.split('_')[1])+1)
            self.passedOperation.add(cnot4_res.op)
            cnot5_res = self.builder.insert(CNotOp.from_value(control1, control2)).res
            cnot5_res._name = control2._name.split('_')[0] +"_" + str(int(control2._name.split('_')[1])+1)
            self.passedOperation.add(cnot5_res.op)

            tcross3_res = self.builder.insert(TDaggerGateOp.from_value(cnot5_res)).res
            tcross3_res._name = cnot5_res._name.split('_')[0] +"_" + str(int(cnot5_res._name.split('_')[1])+1)  # type: ignore[union-attr]
            self.passedOperation.add(tcross3_res.op)
            cnot6_res = self.builder.insert(CNotOp.from_value(control1, tcross3_res)).res
            cnot6_res._name = tcross3_res._name.split('_')[0] +"_" + str(int(tcross3_res._name.split('_')[1])+1)
            self.passedOperation.add(cnot6_res.op)

            # new control1
            t2_res = self.builder.insert(TGateOp.from_value(control1)).res
            t2_res._name = control1._name.split('_')[0] +"_" + str(int(control1._name.split('_')[1])+1)
            self.passedOperation.add(t2_res.op)

            # new control2
            t3_res = self.builder.insert(TGateOp.from_value(cnot6_res)).res
            t3_res._name = cnot6_res._name.split('_')[0] +"_" + str(int(cnot6_res._name.split('_')[1])+1)
            self.passedOperation.add(t3_res.op)


            # new target
            t4_res = self.builder.insert(TGateOp.from_value(cnot4_res)).res
            t4_res._name = cnot4_res._name.split('_')[0] +"_" + str(int(cnot4_res._name.split('_')[1])+1)
            self.passedOperation.add(t4_res.op)
            h2_res = self.builder.insert(HadamardOp.from_value(t4_res)).res
            h2_res._name = t4_res._name.split('_')[0] +"_" + str(int(t4_res._name.split('_')[1])+1)
            self.passedOperation.add(h2_res.op)



            # replace old ccnot operands with the new ones
            self.replace(res, h2_res)
            self.replace(control1, t2_res)
            self.replace(control2, t3_res)

            # erase the ccnot
            rewriter.erase_op(op)
            return

            

