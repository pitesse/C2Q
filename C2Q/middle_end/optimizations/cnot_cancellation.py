"""Adjacent CNOT Cancellation Pass (Quantum-Safe)

This pass performs only unitary-preserving rewrites.

Optimization implemented:
- Cancel adjacent identical `quantum.OnQubit_cnot` pairs.

  If we have (SSA style):
    t1 = CNOT(c -> t0)
    t2 = CNOT(c -> t1)
  with the same `(control_index, target_index)`, then `t2 == t0` and both CNOT
  operations cancel. We replace all uses of `t2` with `t0` and erase the two ops.

"""

import os
from typing import Optional, cast

from xdsl.dialects.builtin import IntegerAttr, ModuleOp
from xdsl.ir import Operation, SSAValue
from xdsl.pattern_rewriter import PatternRewriter, RewritePattern

from ...dialects.quantum_dialect import FuncOp, InitOp


class CNotPairCancellation(RewritePattern):
    """Cancels adjacent identical `quantum.OnQubit_cnot` pairs."""

    def __init__(self) -> None:
        self._debug = False # set True for verbose debugging

    def _dbg(self, *args: object) -> None:
        if self._debug:
            print("[DEBUG][CNotPairCancellation]", *args)

    @staticmethod
    def _get_name(val: SSAValue) -> Optional[str]:
        name = getattr(val, "_name", None)
        if isinstance(name, str) and name:
            return name
        return None

    @staticmethod
    def _get_int_attr(op: Operation, attr_name: str) -> Optional[int]:
        attr = op.attributes.get(attr_name)
        if attr is None:
            return None
        if isinstance(attr, IntegerAttr):
            int_attr = cast(IntegerAttr, attr)
            return int(int_attr.value.data)
        return None

    @classmethod
    def _same_cnot(cls, first: Operation, second: Operation) -> bool:
        if first.name != "quantum.OnQubit_cnot" or second.name != "quantum.OnQubit_cnot":
            return False
        if len(first.operands) < 2 or len(second.operands) < 2:
            return False
        if not first.results or not second.results:
            return False
        return (
            first.operands[0] == second.operands[0]
            and cls._get_int_attr(first, "control_index")
            == cls._get_int_attr(second, "control_index")
            and cls._get_int_attr(first, "target_index")
            == cls._get_int_attr(second, "target_index")
            and second.operands[1] == first.results[0]
        )

    def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter):
        if op.name != "quantum.OnQubit_cnot":
            return
        if isinstance(op, (ModuleOp, FuncOp, InitOp)):
            return

        prev = op._prev_op
        if prev is None:
            return
        if not self._same_cnot(prev, op):
            return

        original_target = prev.operands[1]
        final_res = op.results[0]

        self._dbg(
            "Cancelling adjacent CNOT pair",
            "control=",
            self._get_name(op.operands[0]),
            "ctrl_idx=",
            self._get_int_attr(op, "control_index"),
            "tgt_idx=",
            self._get_int_attr(op, "target_index"),
        )

        for use in list(final_res.uses):
            user = use.operation
            for i, operand in enumerate(user.operands):
                if operand == final_res:
                    user.operands[i] = original_target

        rewriter.erase_op(op)
        rewriter.erase_op(prev)
