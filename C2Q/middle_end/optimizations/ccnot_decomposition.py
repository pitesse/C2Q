"""
CCNOT Decomposition Optimization Pass

Decomposes CCNOT (Toffoli) gates into elementary quantum gates for circuit evaluation
using the Barenco et al. construction (6 CNOTs, 2 Hadamards, 4 T gates, 3 T† gates).

NOTE: This optimization is currently unused in the benchmark suite. The compiler's
QFT-based arithmetic (Draper's algorithm) uses doubly-controlled phase gates instead
of Toffoli gates. This pass remains available for future algorithms that may require
classical logic gates or alternative arithmetic implementations.

Technical Implementation:
- Uses xDSL's pattern rewriting framework for automatic SSA value management
- Operates on full quantum register SSAValues (not individual qubits)
- Employs rewriter.insert_op_before_matched_op() for clean gate insertion
"""

from xdsl.ir import SSAValue
from xdsl.rewriter import InsertPoint
from xdsl.pattern_rewriter import (
    PatternRewriter,
    RewritePattern,
    op_type_rewrite_pattern,
)

from ...dialects.quantum_dialect import (
    OnQubitCCnotOp,
    CNotOp,
    HadamardOp,
    TGateOp,
    TDaggerGateOp,
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
        if op.name != "quantum.OnQubit_ccnot":
            return

        control1 = op.control1  # type: ignore
        control2 = op.control2  # type: ignore
        target = op.target  # type: ignore

        h1 = rewriter.insert_op(HadamardOp.from_value(target), InsertPoint.before(rewriter.current_operation))
        self._propagate_name(target, h1.res)
        
        cnot1 = rewriter.insert_op(
            CNotOp.from_value(control2, h1.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(h1.res, cnot1.res)

        tdg1 = rewriter.insert_op(
            TDaggerGateOp.from_value(cnot1.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(cnot1.res, tdg1.res)

        cnot2 = rewriter.insert_op(
            CNotOp.from_value(control1, tdg1.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(tdg1.res, cnot2.res)

        t1 = rewriter.insert_op(
            TGateOp.from_value(cnot2.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(cnot2.res, t1.res)

        cnot3 = rewriter.insert_op(
            CNotOp.from_value(control2, t1.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(t1.res, cnot3.res)

        tdg2 = rewriter.insert_op(
            TDaggerGateOp.from_value(cnot3.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(cnot3.res, tdg2.res)

        cnot4 = rewriter.insert_op(
            CNotOp.from_value(control1, tdg2.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(tdg2.res, cnot4.res)

        cnot5 = rewriter.insert_op(
            CNotOp.from_value(control1, control2), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(control2, cnot5.res)

        tdg3 = rewriter.insert_op(
            TDaggerGateOp.from_value(cnot5.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(cnot5.res, tdg3.res)

        cnot6 = rewriter.insert_op(
            CNotOp.from_value(control1, tdg3.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(tdg3.res, cnot6.res)

        t2 = rewriter.insert_op(
            TGateOp.from_value(control1), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(control1, t2.res)

        t3 = rewriter.insert_op(
            TGateOp.from_value(cnot6.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(cnot6.res, t3.res)

        t4 = rewriter.insert_op(
            TGateOp.from_value(cnot4.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(cnot4.res, t4.res)

        h2 = rewriter.insert_op(
            HadamardOp.from_value(t4.res), InsertPoint.before(rewriter.current_operation)
        )
        self._propagate_name(t4.res, h2.res)

        rewriter.replace_matched_op([], [h2.res])
