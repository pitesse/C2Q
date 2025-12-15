"""Quantum Operation Dialect Implementation

Defines quantum operations for the C-to-Quantum compiler's intermediate
representation using xDSL's IRDL framework. Provides a comprehensive set
of quantum gates and operations for building quantum circuits.

Operation Categories:
- Single-qubit gates: NOT, Hadamard, T, T-dagger, Phase
- Multi-qubit gates: CNOT, CCNOT, Controlled-phase, SWAP
- Register operations: Initialization, Measurement, Bit extraction/insertion
- On-qubit operations: Direct bit manipulation within vector registers
- Control structures: Function definitions, Comments

All operations are registered as part of the "quantum" dialect.
"""

from __future__ import annotations

from typing import TypeVar

from xdsl.dialects.builtin import (
    IntegerType,
    StringAttr,
    VectorType,
    IntegerAttr,
    FloatAttr,
    Float64Type,
)
from xdsl.ir import Dialect, OpResult, SSAValue, Region, Attribute
from xdsl.irdl import (
    IRDLOperation,
    Operand,
    attr_def,
    irdl_op_definition,
    operand_def,
    result_def,
    region_def,
)


# ============================================================================
# BASIC QUANTUM OPERATIONS
# ============================================================================


@irdl_op_definition
class InitOp(IRDLOperation):
    """Initialize a qubit or vector of qubits to the |0⟩ state.

    Creates new quantum register(s) initialized to the computational zero state,
    which is the standard initial state for quantum computation.
    """

    name = "quantum.init"
    value: IntegerType = attr_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    res: OpResult = result_def()

    def __init__(self, values):
        """
        Initialize a qubit or vector of qubits to zero.

        Args:
            values: An IntegerType for a single qubit or a VectorType for multiple qubits

        Raises:
            TypeError: If values is not an IntegerType or VectorType of IntegerType
        """
        # Determine if values is a single IntegerType or a VectorType of IntegerType
        result_types = []
        attributes = []
        if isinstance(values, IntegerType):
            # Single IntegerType case
            result_types = [IntegerType(1)]
            attributes = {"type": values, "value": IntegerAttr(0, IntegerType(1))}
        elif isinstance(values, VectorType):
            # Vector of IntegerType case
            result_types = [
                VectorType(
                    values.get_element_type(),
                    [
                        values.shape.data[0],  # type: ignore
                    ],
                )
            ]
            attributes = {
                "type": values,
                "value": IntegerAttr(0, IntegerType(values.shape.data[0])),  # type: ignore
            }
        else:
            raise TypeError(
                "Expected IntegerType or VectorType(IntegerType) for values"
            )

        super().__init__(result_types=result_types, attributes=attributes)

    @staticmethod
    def from_value(value) -> InitOp:
        """
        Factory method to create an InitOp from a value.

        Args:
            value: The value to initialize qubits from

        Returns:
            A new InitOp instance
        """
        return InitOp(value)


@irdl_op_definition
class NotOp(IRDLOperation):
    """Apply the NOT gate (X gate) to flip qubit states.

    The NOT gate flips qubit states: |0⟩ ↔ |1⟩. It is a fundamental
    single-qubit gate equivalent to the Pauli-X operator.
    """

    name = "quantum.not"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """Apply a NOT gate to target qubit(s).

        Args:
            target: The qubit or vector of qubits to flip.
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else:  # VectorType
            size = target.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[
                    VectorType(
                        IntegerType(1),
                        [
                            size,
                        ],
                    )
                ],
                operands=[target],
            )

    @staticmethod
    def from_value(value: SSAValue) -> NotOp:
        """Create a NotOp from a value.

        Args:
            value: The target qubit or vector of qubits.

        Returns:
            A new NotOp instance.
        """
        return NotOp(value)


# ============================================================================
# MULTI-QUBIT OPERATIONS
# ============================================================================


@irdl_op_definition
class CNotOp(IRDLOperation):
    """Apply the CNOT gate (Controlled-NOT) for entanglement.

    Two-qubit gate that flips the target qubit if the control qubit is |1⟩.
    Fundamental for creating entanglement between qubits.
    """

    name = "quantum.cnot"
    control: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    res: OpResult = result_def()

    def __init__(self, control: SSAValue, target: SSAValue):
        """Apply a CNOT gate between control and target qubits.

        Args:
            control: The control qubit or vector.
            target: The target qubit or vector.
        """
        if isinstance(control.type, IntegerType) and isinstance(
            target.type, IntegerType
        ):
            super().__init__(result_types=[IntegerType(1)], operands=[control, target])
        else:  # VectorType
            size = control.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[
                    VectorType(
                        IntegerType(1),
                        [
                            size,
                        ],
                    )
                ],
                operands=[control, target],
            )

    @staticmethod
    def from_value(control: SSAValue, target: SSAValue) -> CNotOp:
        """Create a CNotOp from control and target values.

        Args:
            control: The control qubit or vector.
            target: The target qubit or vector.

        Returns:
            A new CNotOp instance.
        """
        return CNotOp(control, target)


@irdl_op_definition
class CCNotOp(IRDLOperation):
    """Apply the CCNOT gate (Toffoli gate) for reversible computation.

    Three-qubit gate that flips the target qubit if both control qubits are |1⟩.
    Universal gate for classical reversible computation within quantum systems.
    """

    name = "quantum.ccnot"
    control1: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    control2: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    res: OpResult = result_def()

    def __init__(self, control1: SSAValue, control2: SSAValue, target: SSAValue):
        """Apply a CCNOT gate with two controls and one target.

        Args:
            control1: The first control qubit or vector.
            control2: The second control qubit or vector.
            target: The target qubit or vector.
        """
        if (
            isinstance(control1.type, IntegerType)
            and isinstance(control2.type, IntegerType)
            and isinstance(target.type, IntegerType)
        ):
            super().__init__(
                result_types=[IntegerType(1)], operands=[control1, control2, target]
            )
        else:  # VectorType
            size = control1.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[
                    VectorType(
                        IntegerType(1),
                        [
                            size,
                        ],
                    )
                ],
                operands=[control1, control2, target],
            )

    @staticmethod
    def from_value(control1: SSAValue, control2: SSAValue, target: SSAValue) -> CCNotOp:
        """Create a CCNotOp from control and target values.

        Args:
            control1: The first control qubit or vector.
            control2: The second control qubit or vector.
            target: The target qubit or vector.

        Returns:
            A new CCNotOp instance.
        """
        return CCNotOp(control1, control2, target)


@irdl_op_definition
class MeasureOp(IRDLOperation):
    """Measure qubit(s) to extract classical information.

    Collapses the quantum state and returns a classical bit result.
    Typically used at circuit end to extract computation results.
    """

    name = "quantum.measure"
    target: Operand = operand_def(IntegerType(1))
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """Measure target qubit(s).

        Args:
            target: The qubit or vector of qubits to measure.
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else:  # VectorType
            size = target.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[
                    VectorType(
                        IntegerType(1),
                        [
                            size,
                        ],
                    )
                ],
                operands=[target],
            )

    @staticmethod
    def from_value(target: SSAValue) -> MeasureOp:
        """Create a MeasureOp from a target value.

        Args:
            target: The qubit or vector of qubits to measure.

        Returns:
            A new MeasureOp instance.
        """
        return MeasureOp(target)


@irdl_op_definition
class FuncOp(IRDLOperation):
    """Define a quantum function for code organization.

    Encapsulates a sequence of quantum operations as a named function,
    providing structure for quantum circuit organization.
    """

    name = "quantum.func"
    body: Region = region_def()
    func_name: StringAttr = attr_def(StringAttr)

    def __init__(
        self, name: str, region: Region | type[Region.DEFAULT] = Region.DEFAULT
    ):
        """Define a quantum function.

        Args:
            name: The function name.
            region: The region containing the function body operations.
        """
        attributes: dict[str, Attribute] = {"func_name": StringAttr(name)}
        regions_list = [region] if region is not Region.DEFAULT else []
        return super().__init__(attributes=attributes, regions=regions_list)  # type: ignore


@irdl_op_definition
class TGateOp(IRDLOperation):
    """Apply the T gate for π/4 phase rotation.

    Single-qubit gate that rotates the state vector by π/4 radians around
    the Z-axis of the Bloch sphere. Essential for universal quantum computation.
    """

    name = "quantum.not"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """Apply a T gate to target qubit(s).

        Args:
            target: The qubit or vector to apply the gate to.
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else:  # VectorType
            size = target.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[
                    VectorType(
                        IntegerType(1),
                        [
                            size,
                        ],
                    )
                ],
                operands=[target],
            )

    @staticmethod
    def from_value(target: SSAValue) -> TGateOp:
        """Create a TGateOp from a target value.

        Args:
            target: The qubit or vector to apply the T gate to.

        Returns:
            A new TGateOp instance.
        """
        return TGateOp(target)


@irdl_op_definition
class TDaggerGateOp(IRDLOperation):
    """Apply the T-dagger gate for -π/4 phase rotation.

    Adjoint (inverse) of the T gate. Rotates the state vector by -π/4 radians
    around the Z-axis. Used with T gate for quantum circuit construction.
    """

    name = "quantum.tdagger"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """Apply a T-dagger gate to target qubit(s).

        Args:
            target: The qubit or vector to apply the gate to.
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else:  # VectorType
            size = target.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[
                    VectorType(
                        IntegerType(1),
                        [
                            size,
                        ],
                    )
                ],
                operands=[target],
            )

    @staticmethod
    def from_value(target: SSAValue) -> TDaggerGateOp:
        """Create a TDaggerGateOp from a target value.

        Args:
            target: The qubit or vector to apply the T-dagger gate to.

        Returns:
            A new TDaggerGateOp instance.
        """
        return TDaggerGateOp(target)


@irdl_op_definition
class HadamardOp(IRDLOperation):
    """Apply the Hadamard gate to create superposition.

    Creates superposition by transforming |0⟩ → |+⟩ and |1⟩ → |-⟩.
    Fundamental for quantum algorithms, often used as initialization step.
    """

    name = "quantum.h"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """Apply a Hadamard gate to target qubit(s).

        Args:
            target: The qubit or vector to apply the gate to.
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else:  # VectorType
            size = target.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[
                    VectorType(
                        IntegerType(1),
                        [
                            size,
                        ],
                    )
                ],
                operands=[target],
            )

    @staticmethod
    def from_value(target: SSAValue) -> HadamardOp:
        """Create a HadamardOp from a target value.

        Args:
            target: The qubit or vector to apply the Hadamard gate to.

        Returns:
            A new HadamardOp instance.
        """
        return HadamardOp(target)


@irdl_op_definition
class CommentOp(IRDLOperation):
    """Add a comment to the IR for documentation.

    Non-computational operation for documentation and debugging.
    Makes IR more readable without affecting quantum execution.
    """

    name = "quantum.comment"
    comment_text: StringAttr = attr_def(StringAttr)

    def __init__(self, text: str):
        """Create a comment operation.

        Args:
            text: The comment text.
        """
        super().__init__(attributes={"comment_text": StringAttr(text)})

    @staticmethod
    def from_string(text: str) -> "CommentOp":
        """Create a CommentOp from a string.

        Args:
            text: The comment text.

        Returns:
            A new CommentOp instance.
        """
        return CommentOp(text)


@irdl_op_definition
class ExtractBitOp(IRDLOperation):
    """Extract a single qubit from a multi-qubit register.

    Extracts one qubit from a vector at the specified index.
    """

    name = "quantum.extract_bit"
    vector: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def()

    def __init__(self, vector: SSAValue, index: int):
        """Extract a single qubit from a vector.

        Args:
            vector: The vector of qubits.
            index: The index to extract.
        """
        super().__init__(
            result_types=[IntegerType(1)],
            operands=[vector],
            attributes={"index": IntegerAttr(index, IntegerType(32))},
        )

    @staticmethod
    def from_value(vector: SSAValue, index: int) -> "ExtractBitOp":
        """Create an ExtractBitOp.

        Args:
            vector: The vector to extract from.
            index: The bit index to extract.

        Returns:
            A new ExtractBitOp instance.
        """
        return ExtractBitOp(vector, index)


@irdl_op_definition
class InsertBitOp(IRDLOperation):
    """
    @brief Operation to insert a single qubit into a multi-qubit register.

    This operation inserts one qubit into a vector of qubits at a specified index.
    """

    name = "quantum.insert_bit"
    vector: Operand = operand_def(VectorType)
    value: Operand = operand_def(IntegerType(1))
    index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def()

    def __init__(self, vector: SSAValue, value: SSAValue, index: int):
        """
        @brief Insert a single qubit into a vector.

        @param vector: The vector of qubits to update
        @param value: The qubit value to insert
        @param index: The bit position to insert at
        """
        if isinstance(vector.type, VectorType):
            size = vector.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[vector, value],
                attributes={"index": IntegerAttr(index, IntegerType(32))},
            )
        else:
            raise TypeError("Expected VectorType for vector parameter")

    @staticmethod
    def from_values(vector: SSAValue, value: SSAValue, index: int) -> "InsertBitOp":
        """Create an InsertBitOp.

        Args:
            vector: The vector to insert into.
            value: The qubit value to insert.
            index: The bit position.

        Returns:
            A new InsertBitOp instance.
        """
        return InsertBitOp(vector, value, index)


# ============================================================================
# ON-QUBIT OPERATIONS (direct bit manipulation for qubits vectors/registers)
# ============================================================================


@irdl_op_definition
class OnQubitNotOp(IRDLOperation):
    """Apply NOT gate directly to an indexed bit in a register.

    Applies NOT to a specific bit within a vector register, avoiding
    separate extract and insert operations.
    """

    name = "quantum.OnQubit_not"
    vector: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)

    def __init__(self, vector: SSAValue, bit_index: int):
        """Apply NOT gate to a specific bit in a vector.

        Args:
            vector: The vector of qubits.
            bit_index: The index of the bit to flip.
        """
        if isinstance(vector.type, VectorType):
            size = vector.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[vector],
                attributes={"index": IntegerAttr(bit_index, IntegerType(32))},
            )
        else:
            raise TypeError("Expected VectorType for vector parameter")

    @staticmethod
    def from_value(vector: SSAValue, bit_index: int) -> "OnQubitNotOp":
        """Create a OnQubitNotOp from a vector and bit index.

        Args:
            vector: The vector of qubits.
            bit_index: The index of the bit to flip.

        Returns:
            A new OnQubitNotOp instance.
        """
        return OnQubitNotOp(vector, bit_index)


@irdl_op_definition
class OnQubitCNotOp(IRDLOperation):
    """Apply CNOT gate directly to indexed bits in registers.

    Applies CNOT between specific bits within vector registers, avoiding
    separate extract and insert operations.
    """

    name = "quantum.OnQubit_cnot"
    control_vector: Operand = operand_def(VectorType)
    target_vector: Operand = operand_def(VectorType)
    control_index: IntegerAttr = attr_def(IntegerAttr)
    target_index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)

    def __init__(
        self,
        control_vector: SSAValue,
        control_index: int,
        target_vector: SSAValue,
        target_index: int,
    ):
        """Apply CNOT gate between specific bits in vectors.

        Args:
            control_vector: The vector containing the control qubit.
            control_index: The index of the control bit.
            target_vector: The vector containing the target qubit.
            target_index: The index of the target bit.
        """
        if isinstance(control_vector.type, VectorType) and isinstance(
            target_vector.type, VectorType
        ):
            size = target_vector.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[control_vector, target_vector],
                attributes={
                    "control_index": IntegerAttr(control_index, IntegerType(32)),
                    "target_index": IntegerAttr(target_index, IntegerType(32)),
                },
            )
        else:
            raise TypeError("Expected VectorType for both vector parameters")

    @staticmethod
    def from_values(
        control_vector: SSAValue,
        control_index: int,
        target_vector: SSAValue,
        target_index: int,
    ) -> "OnQubitCNotOp":
        """Create a OnQubitCNotOp.

        Args:
            control_vector: Vector containing the control qubit.
            control_index: Index of the control bit.
            target_vector: Vector containing the target qubit.
            target_index: Index of the target bit.

        Returns:
            A new OnQubitCNotOp instance.
        """
        return OnQubitCNotOp(control_vector, control_index, target_vector, target_index)


@irdl_op_definition
class OnQubitCCnotOp(IRDLOperation):
    """Apply CCNOT gate directly to indexed bits in registers.

    Applies CCNOT between two control bits and a target bit within vector
    registers, avoiding separate extract and insert operations.
    """

    name = "quantum.OnQubit_ccnot"
    control1_vector: Operand = operand_def(VectorType)
    control2_vector: Operand = operand_def(VectorType)
    target_vector: Operand = operand_def(VectorType)
    control1_index: IntegerAttr = attr_def(IntegerAttr)
    control2_index: IntegerAttr = attr_def(IntegerAttr)
    target_index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)

    def __init__(
        self,
        control1_vector: SSAValue,
        control1_index: int,
        control2_vector: SSAValue,
        control2_index: int,
        target_vector: SSAValue,
        target_index: int,
    ):
        """Apply CCNOT gate between specific bits in vectors.

        Args:
            control1_vector: Vector containing the first control qubit.
            control1_index: Index of the first control bit.
            control2_vector: Vector containing the second control qubit.
            control2_index: Index of the second control bit.
            target_vector: Vector containing the target qubit.
            target_index: Index of the target bit.
        """
        if (
            isinstance(control1_vector.type, VectorType)
            and isinstance(control2_vector.type, VectorType)
            and isinstance(target_vector.type, VectorType)
        ):
            size = target_vector.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[control1_vector, control2_vector, target_vector],
                attributes={
                    "control1_index": IntegerAttr(control1_index, IntegerType(32)),
                    "control2_index": IntegerAttr(control2_index, IntegerType(32)),
                    "target_index": IntegerAttr(target_index, IntegerType(32)),
                },
            )
        else:
            raise TypeError("Expected VectorType for all vector parameters")

    @staticmethod
    def from_values(
        control1_vector: SSAValue,
        control1_index: int,
        control2_vector: SSAValue,
        control2_index: int,
        target_vector: SSAValue,
        target_index: int,
    ) -> "OnQubitCCnotOp":
        """Create a OnQubitCCnotOp.

        Args:
            control1_vector: Vector containing the first control qubit.
            control1_index: Index of the first control bit.
            control2_vector: Vector containing the second control qubit.
            control2_index: Index of the second control bit.
            target_vector: Vector containing the target qubit.
            target_index: Index of the target bit.

        Returns:
            A new OnQubitCCnotOp instance.
        """
        return OnQubitCCnotOp(
            control1_vector,
            control1_index,
            control2_vector,
            control2_index,
            target_vector,
            target_index,
        )


@irdl_op_definition
class OnQubitHadamardOp(IRDLOperation):
    """Apply Hadamard gate to a specific qubit in a register.

    Applies Hadamard to a specific qubit within a vector register,
    creating superposition: H|0⟩ = (|0⟩ + |1⟩)/√2, H|1⟩ = (|0⟩ - |1⟩)/√2.
    """

    name = "quantum.OnQubit_hadamard"
    register: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)

    def __init__(self, register: SSAValue, index: int):
        """Apply Hadamard gate to a specific qubit.

        Args:
            register: The vector containing the qubit.
            index: The index of the qubit.
        """
        if isinstance(register.type, VectorType):
            size = register.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[register],
                attributes={
                    "index": IntegerAttr(index, IntegerType(32)),
                },
            )
        else:
            raise TypeError("Expected VectorType for register parameter")

    @staticmethod
    def from_value(register: SSAValue, index: int) -> "OnQubitHadamardOp":
        """Create a OnQubitHadamardOp.

        Args:
            register: Vector containing the qubit.
            index: Index of the qubit.

        Returns:
            A new OnQubitHadamardOp instance.
        """
        return OnQubitHadamardOp(register, index)


@irdl_op_definition
class OnQubitPhaseOp(IRDLOperation):
    """Apply phase gate to a specific qubit in a register.

    Applies phase rotation to a specific qubit: |0⟩ → |0⟩, |1⟩ → e^(iθ)|1⟩.
    """

    name = "quantum.OnQubit_phase"
    register: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    phase: FloatAttr = attr_def(FloatAttr)
    res: OpResult = result_def(VectorType)

    def __init__(self, register: SSAValue, index: int, phase: float):
        """Apply phase gate to a specific qubit.

        Args:
            register: The vector containing the qubit.
            index: The index of the qubit.
            phase: The phase angle in radians.
        """
        if isinstance(register.type, VectorType):
            size = register.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[register],
                attributes={
                    "index": IntegerAttr(index, IntegerType(32)),
                    "phase": FloatAttr(phase, Float64Type()),
                },
            )
        else:
            raise TypeError("Expected VectorType for register parameter")

    @staticmethod
    def from_value(register: SSAValue, index: int, phase: float) -> "OnQubitPhaseOp":
        """Create a OnQubitPhaseOp.

        Args:
            register: Vector containing the qubit.
            index: Index of the qubit.
            phase: The phase angle in radians.

        Returns:
            A new OnQubitPhaseOp instance.
        """
        return OnQubitPhaseOp(register, index, phase)


@irdl_op_definition
class OnQubitControlledPhaseOp(IRDLOperation):
    """Apply controlled phase rotation to qubits in registers.

    Applies phase to target qubit only if control qubit is |1⟩.
    """

    name = "quantum.OnQubit_controlled_phase"
    control_register: Operand = operand_def(VectorType)
    target_register: Operand = operand_def(VectorType)
    control_index: IntegerAttr = attr_def(IntegerAttr)
    target_index: IntegerAttr = attr_def(IntegerAttr)
    phase: FloatAttr = attr_def(FloatAttr)
    res: OpResult = result_def(VectorType)

    def __init__(
        self,
        control_register: SSAValue,
        control_index: int,
        target_register: SSAValue,
        target_index: int,
        phase: float,
    ):
        """Apply controlled phase rotation between specific qubits.

        Args:
            control_register: Vector containing the control qubit.
            control_index: Index of the control qubit.
            target_register: Vector containing the target qubit.
            target_index: Index of the target qubit.
            phase: The phase angle in radians.
        """
        if isinstance(control_register.type, VectorType) and isinstance(
            target_register.type, VectorType
        ):
            size = target_register.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[control_register, target_register],
                attributes={
                    "control_index": IntegerAttr(control_index, IntegerType(32)),
                    "target_index": IntegerAttr(target_index, IntegerType(32)),
                    "phase": FloatAttr(phase, Float64Type()),
                },
            )
        else:
            raise TypeError("Expected VectorType for both register parameters")

    @staticmethod
    def from_values(
        control_register: SSAValue,
        control_index: int,
        target_register: SSAValue,
        target_index: int,
        phase: float,
    ) -> "OnQubitControlledPhaseOp":
        """Create a OnQubitControlledPhaseOp.

        Args:
            control_register: Vector containing the control qubit.
            control_index: Index of the control qubit.
            target_register: Vector containing the target qubit.
            target_index: Index of the target qubit.
            phase: The phase angle in radians.

        Returns:
            A new OnQubitControlledPhaseOp instance.
        """
        return OnQubitControlledPhaseOp(
            control_register, control_index, target_register, target_index, phase
        )


@irdl_op_definition
class OnQubitSwapOp(IRDLOperation):
    """Swap two qubits within a register.

    Exchanges the quantum states of two qubits within the same vector register.
    """

    name = "quantum.OnQubit_swap"
    register: Operand = operand_def(VectorType)
    qubit1_index: IntegerAttr = attr_def(IntegerAttr)
    qubit2_index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)

    def __init__(self, register: SSAValue, qubit1_index: int, qubit2_index: int):
        """Swap two qubits within a vector register.

        Args:
            register: The vector containing both qubits.
            qubit1_index: Index of the first qubit.
            qubit2_index: Index of the second qubit.
        """
        if isinstance(register.type, VectorType):
            size = register.type.shape.data[0]  # type: ignore
            super().__init__(
                result_types=[VectorType(IntegerType(1), [size])],
                operands=[register],
                attributes={
                    "qubit1_index": IntegerAttr(qubit1_index, IntegerType(32)),
                    "qubit2_index": IntegerAttr(qubit2_index, IntegerType(32)),
                },
            )
        else:
            raise TypeError("Expected VectorType for register parameter")

    @staticmethod
    def from_values(
        register: SSAValue, qubit1_index: int, qubit2_index: int
    ) -> "OnQubitSwapOp":
        """Create a OnQubitSwapOp.

        Args:
            register: Vector containing both qubits.
            qubit1_index: Index of the first qubit.
            qubit2_index: Index of the second qubit.

        Returns:
            A new OnQubitSwapOp instance.
        """
        return OnQubitSwapOp(register, qubit1_index, qubit2_index)


Quantum = Dialect(
    "quantum",
    [
        InitOp,
        NotOp,
        CNotOp,
        CCNotOp,
        MeasureOp,
        FuncOp,
        TGateOp,
        TDaggerGateOp,
        HadamardOp,
        CommentOp,
        ExtractBitOp,
        InsertBitOp,
        OnQubitNotOp,
        OnQubitCNotOp,
        OnQubitCCnotOp,
        OnQubitHadamardOp,
        OnQubitControlledPhaseOp,
        OnQubitSwapOp,
    ],
    [],
)


# ============================================================================
# DIALECT REGISTRATION
# ============================================================================

# the quantum dialect is automatically registered when this module is imported
# and provides all quantum operations for the c-to-quantum compiler's ir generation
