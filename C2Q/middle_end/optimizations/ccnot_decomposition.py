"""
CCNOT Decomposition Optimization Pass

Decomposes bit-indexed CCNOT (Toffoli) gates into elementary on-qubit operations for
circuit evaluation using the Barenco et al. construction.

Gate cost (standard no-ancilla decomposition):
- 6 CNOT gates
- 2 Hadamard gates
- 4 T gates
- 3 T† (T-dagger) gates

In this IR, we implement T/T† via phase rotations of ±π/4.

NOTE: This optimization is currently unused in the benchmark suite. The compiler's
QFT-based arithmetic (Draper's algorithm) uses doubly-controlled phase gates instead
of Toffoli gates. This pass remains available for future algorithms that may require
classical logic gates or alternative arithmetic implementations.

Technical Implementation:
- Uses xDSL's pattern rewriting framework for automatic SSA value management
- Operates on indexed bits within vector registers (quantum.OnQubit_* ops)
- Inserts the decomposition before the matched CCNOT, then rewires SSA uses
  of the control registers after the CCNOT so control-side gates are preserved.
"""

import math

from xdsl.ir import SSAValue
from xdsl.dialects.builtin import IntegerAttr
from xdsl.rewriter import InsertPoint
from xdsl.pattern_rewriter import (
    PatternRewriter,
    RewritePattern,
    op_type_rewrite_pattern,
)

from ...dialects.quantum_dialect import (
    OnQubitCCnotOp,
    OnQubitCNotOp,
    OnQubitHadamardOp,
    OnQubitPhaseOp,
)


class CCnot_decomposition(RewritePattern):
    """
    Pattern rewriter that decomposes CCNOT (Toffoli) gates into elementary gates.

    Implements the Barenco et al. construction which uses 15 gates total:
    - 6 CNOT gates
    - 2 Hadamard gates
    - 4 T gates
    - 3 T† (T-dagger) gates

    The decomposition preserves the semantics of the Toffoli gate while using only
    single and two-qubit gates that are typically easier to implement on physical
    quantum hardware.

    Attributes:
        None - uses decorator-based pattern matching

    Methods:
        match_and_rewrite: Performs the actual decomposition when a CCNOT is found
    """

    @staticmethod
    def _propagate_name(source: SSAValue, target: SSAValue) -> None:
        """
        Propagate SSA naming convention for debugging purposes.

        Maintains the qX_Y naming pattern where X is the register number and Y is
        the version number. This is optional as xDSL automatically manages SSA values.

        Args:
            source: Source SSAValue with existing _name attribute
            target: Target SSAValue to receive incremented name
        """
        if hasattr(source, "_name") and source._name:
            parts = source._name.split("_")
            if len(parts) == 2 and parts[1].isdigit():
                target._name = f"{parts[0]}_{int(parts[1]) + 1}"

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: OnQubitCCnotOp, rewriter: PatternRewriter):
        """
        Match and decompose CCNOT operations into elementary gates.

        Implements the standard Barenco decomposition which converts one CCNOT gate
        into a sequence of 15 elementary gates. The decomposition is universal and
        works for any CCNOT gate regardless of the qubit indices.

        Gate sequence: H→CNOT→T†→CNOT→T→CNOT→T†→CNOT→CNOT→T†→CNOT→T→T→T→H

        Args:
            op: The OnQubitCCnotOp to decompose
            rewriter: Pattern rewriter for applying transformations

        Returns:
            None - modifies IR in place via rewriter
        """
        def _as_index(attr: IntegerAttr) -> int:
            return int(attr.value.data)

        control1_vec = op.control1_vector
        control2_vec = op.control2_vector
        target_vec = op.target_vector
        control1_idx = _as_index(op.control1_index)
        control2_idx = _as_index(op.control2_index)
        target_idx = _as_index(op.target_index)

        insert_point = InsertPoint.before(op)

        control1_curr = control1_vec
        control2_curr = control2_vec
        target_curr = target_vec

        def apply_h(register: SSAValue, index: int) -> SSAValue:
            h = rewriter.insert_op(
                OnQubitHadamardOp.from_value(register, index), insert_point
            )
            self._propagate_name(register, h.res)
            return h.res

        def apply_t(register: SSAValue, index: int) -> SSAValue:
            p = rewriter.insert_op(
                OnQubitPhaseOp.from_value(register, index, math.pi / 4.0),
                insert_point,
            )
            self._propagate_name(register, p.res)
            return p.res

        def apply_tdg(register: SSAValue, index: int) -> SSAValue:
            p = rewriter.insert_op(
                OnQubitPhaseOp.from_value(register, index, -math.pi / 4.0),
                insert_point,
            )
            self._propagate_name(register, p.res)
            return p.res

        def apply_cnot(
            control_register: SSAValue,
            control_index: int,
            target_register: SSAValue,
            target_index: int,
        ) -> SSAValue:
            c = rewriter.insert_op(
                OnQubitCNotOp.from_values(
                    control_register, control_index, target_register, target_index
                ),
                insert_point,
            )
            self._propagate_name(target_register, c.res)
            return c.res

        # standard 15-gate Barenco decomposition (no ancilla).
        target_curr = apply_h(target_curr, target_idx)
        target_curr = apply_cnot(control2_curr, control2_idx, target_curr, target_idx)
        target_curr = apply_tdg(target_curr, target_idx)
        target_curr = apply_cnot(control1_curr, control1_idx, target_curr, target_idx)
        target_curr = apply_t(target_curr, target_idx)
        target_curr = apply_cnot(control2_curr, control2_idx, target_curr, target_idx)
        target_curr = apply_tdg(target_curr, target_idx)
        target_curr = apply_cnot(control1_curr, control1_idx, target_curr, target_idx)
        control2_curr = apply_t(control2_curr, control2_idx)
        target_curr = apply_t(target_curr, target_idx)
        control2_curr = apply_cnot(control1_curr, control1_idx, control2_curr, control2_idx)
        target_curr = apply_h(target_curr, target_idx)
        control1_curr = apply_t(control1_curr, control1_idx)
        control2_curr = apply_tdg(control2_curr, control2_idx)
        control2_curr = apply_cnot(control1_curr, control1_idx, control2_curr, control2_idx)

        # update SSA wiring for control registers after the original CCNOT.
        after_ops = set()
        cursor = op._next_op
        while cursor is not None:
            after_ops.add(cursor)
            cursor = cursor._next_op

        if control1_curr is not control1_vec:
            for use in list(control1_vec.uses):
                if use.operation in after_ops:
                    use.operation.operands[use.index] = control1_curr

        if control2_curr is not control2_vec:
            for use in list(control2_vec.uses):
                if use.operation in after_ops:
                    use.operation.operands[use.index] = control2_curr

        # replace the CCNOT's target result.
        rewriter.replace_matched_op([], [target_curr])
