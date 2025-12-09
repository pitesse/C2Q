"""
Quantum Operation Dialect Implementation

This module defines a set of quantum operations for use in the C to Quantum
compiler's intermediate representation (IR). It provides a collection of
quantum gates and operations that can be used to build quantum circuits,
including initialization, measurement, and various quantum gates like NOT,
CNOT, CCNOT, Hadamard, and T gates.

The operations are defined using xDSL's IR definition language (IRDL) and
are registered as part of the "quantum" dialect.

Key Features:
- Single-qubit operations (NOT, Hadamard, T, T-dagger)
- Multi-qubit operations (CNOT, CCNOT)
- On-qubit operations for direct bit manipulation
- Controlled phase operations
- Register initialization and measurement
"""

from __future__ import annotations

from typing import TypeVar

from xdsl.dialects.builtin import IntegerType, StringAttr, VectorType, IntegerAttr, FloatAttr, Float64Type
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
    """
    Operation to initialize a qubit or a vector of qubits to zero.

    This operation creates a new qubit or vector of qubits, initializing
    them to the |0⟩ state, which is the standard initial state for
    quantum computation.
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
    """
    Operation to apply the NOT gate (X gate) to a qubit or vector of qubits.

    The NOT gate flips the state of a qubit, changing |0⟩ to |1⟩ and vice versa.
    It is one of the fundamental single-qubit gates in quantum computing.
    """

    name = "quantum.not"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a NOT gate to a target qubit or vector of qubits.

        @param target: The qubit or vector of qubits to apply the NOT gate to
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
        """
        Factory method to create a NotOp from a value.

        Args:
            value: The target qubit or vector of qubits
            
        Returns:
            A new NotOp instance
        """
        return NotOp(value)


# ============================================================================
# MULTI-QUBIT OPERATIONS
# ============================================================================


@irdl_op_definition
class CNotOp(IRDLOperation):
    """
    Operation to apply the CNOT gate (Controlled-NOT) to qubits.

    The CNOT gate is a two-qubit operation where the state of the target qubit
    is flipped if the control qubit is in the |1⟩ state. It is fundamental for
    creating entanglement between qubits.
    """

    name = "quantum.cnot"
    control: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    res: OpResult = result_def()

    def __init__(self, control: SSAValue, target: SSAValue):
        """
        @brief Apply a CNOT gate with the specified control and target qubits.

        @param control: The control qubit (or vector of control qubits)
        @param target: The target qubit (or vector of target qubits)
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
        """
        @brief Factory method to create a CNotOp from control and target values.

        @param control: The control qubit (or vector of control qubits)
        @param target: The target qubit (or vector of target qubits)
        @return A new CNotOp instance
        """
        return CNotOp(control, target)


@irdl_op_definition
class CCNotOp(IRDLOperation):
    """
    @brief Operation to apply the CCNOT gate (Toffoli gate) to qubits.

    The CCNOT gate is a three-qubit operation where the state of the target qubit
    is flipped if both control qubits are in the |1⟩ state. It is a universal gate
    for classical reversible computation within quantum computing.

    @see NotOp
    @see CNotOp
    """

    name = "quantum.ccnot"
    control1: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    control2: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    res: OpResult = result_def()

    def __init__(self, control1: SSAValue, control2: SSAValue, target: SSAValue):
        """
        @brief Apply a CCNOT gate with the specified control and target qubits.

        @param control1: The first control qubit (or vector of control qubits)
        @param control2: The second control qubit (or vector of control qubits)
        @param target: The target qubit (or vector of target qubits)
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
        """
        @brief Factory method to create a CCNotOp from control and target values.

        @param control1: The first control qubit (or vector of control qubits)
        @param control2: The second control qubit (or vector of control qubits)
        @param target: The target qubit (or vector of target qubits)
        @return A new CCNotOp instance
        """
        return CCNotOp(control1, control2, target)


@irdl_op_definition
class MeasureOp(IRDLOperation):
    """
    @brief Operation to measure a qubit or vector of qubits.

    This operation collapses the quantum state and returns a classical bit result.
    It is typically used at the end of quantum circuits to extract classical
    information from the quantum computation.

    @see InitOp
    """

    name = "quantum.measure"
    target: Operand = operand_def(IntegerType(1))
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Measure a target qubit or vector of qubits.

        @param target: The qubit or vector of qubits to measure
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
        """
        @brief Factory method to create a MeasureOp from a target value.

        @param target: The qubit or vector of qubits to measure
        @return A new MeasureOp instance
        """
        return MeasureOp(target)


@irdl_op_definition
class FuncOp(IRDLOperation):
    """
    @brief Operation to define a quantum function.

    This operation encapsulates a sequence of quantum operations as a function
    with a specified name. It provides a container for quantum code organization.
    """

    name = "quantum.func"
    body: Region = region_def()
    func_name: StringAttr = attr_def(StringAttr)

    def __init__(
        self, name: str, region: Region | type[Region.DEFAULT] = Region.DEFAULT
    ):
        """
        @brief Define a quantum function with the specified name and region.

        @param name: The function name
        @param region: The region containing the function body operations
        """
        attributes: dict[str, Attribute] = {"func_name": StringAttr(name)}
        regions_list = [region] if region is not Region.DEFAULT else []
        return super().__init__(attributes=attributes, regions=regions_list)  # type: ignore


@irdl_op_definition
class TGateOp(IRDLOperation):
    """
    @brief T-Gate operation for phase rotation.

    The T gate is a single-qubit operation that rotates the state vector around
    the Z-axis of the Bloch sphere by π/4 radians (45 degrees). It is particularly
    important for universal quantum computation.

    @see TDaggerGateOp
    """

    name = "quantum.not"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a NOT gate to a target qubit or vector of qubits.

        @param target: The qubit or vector of qubits to apply the NOT gate to
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
        """
        @brief Factory method to create a TGateOp from a target value.

        @param target: The qubit or vector of qubits to apply the T gate to
        @return A new TGateOp instance
        """
        return TGateOp(target)


@irdl_op_definition
class TDaggerGateOp(IRDLOperation):
    """
    @brief T-Dagger Gate operation for inverse phase rotation.

    The T-Dagger gate is the adjoint (inverse) of the T gate. It rotates the state
    vector around the Z-axis of the Bloch sphere by -π/4 radians (-45 degrees).
    It is used in conjunction with the T gate for quantum circuit construction.

    @see TGateOp
    """

    name = "quantum.tdagger"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a T-Dagger gate to a target qubit or vector of qubits.

        @param target: The qubit or vector of qubits to apply the T-Dagger gate to
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
        """
        @brief Factory method to create a TDaggerGateOp from a target value.

        @param target: The qubit or vector of qubits to apply the T-Dagger gate to
        @return A new TDaggerGateOp instance
        """
        return TDaggerGateOp(target)


@irdl_op_definition
class HadamardOp(IRDLOperation):
    """
    @brief Hadamard gate operation for creating superposition.

    The Hadamard gate creates a superposition by transforming states |0⟩ to |+⟩ and
    |1⟩ to |-⟩. It is fundamental for creating superposition states in quantum
    algorithms and is often used as the first step in many quantum circuits.
    """

    name = "quantum.h"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))  # type: ignore
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a Hadamard gate to a target qubit or vector of qubits.

        @param target: The qubit or vector of qubits to apply the Hadamard gate to
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
        """
        @brief Factory method to create a HadamardOp from a target value.

        @param target: The qubit or vector of qubits to apply the Hadamard gate to
        @return A new HadamardOp instance
        """
        return HadamardOp(target)


@irdl_op_definition
class CommentOp(IRDLOperation):
    """
    @brief Operation to add a comment to the IR.

    This operation exists purely for documentation and debugging purposes.
    It doesn't perform any quantum computation but helps make the IR more readable.
    """

    name = "quantum.comment"
    comment_text: StringAttr = attr_def(StringAttr)

    def __init__(self, text: str):
        """
        @brief Create a comment operation.

        @param text: The comment text
        """
        super().__init__(attributes={"comment_text": StringAttr(text)})

    @staticmethod
    def from_string(text: str) -> "CommentOp":
        """
        @brief Factory method to create a CommentOp from a string.

        @param text: The comment text
        @return A new CommentOp instance
        """
        return CommentOp(text)


@irdl_op_definition
class ExtractBitOp(IRDLOperation):
    """
    @brief Operation to extract a single qubit from a multi-qubit register.

    This operation extracts one qubit from a vector of qubits at a specified index.
    """

    name = "quantum.extract_bit"
    vector: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def()

    def __init__(self, vector: SSAValue, index: int):
        """
        @brief Extract a single qubit from a vector.

        @param vector: The vector of qubits
        @param index: The index to extract
        """
        super().__init__(
            result_types=[IntegerType(1)],
            operands=[vector],
            attributes={"index": IntegerAttr(index, IntegerType(32))},
        )

    @staticmethod
    def from_value(vector: SSAValue, index: int) -> "ExtractBitOp":
        """
        @brief Factory method to create an ExtractBitOp.

        @param vector: The vector to extract from
        @param index: The bit index to extract
        @return A new ExtractBitOp instance
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
        """
        @brief Factory method to create an InsertBitOp.

        @param vector: The vector to insert into
        @param value: The qubit value to insert
        @param index: The bit position
        @return A new InsertBitOp instance
        """
        return InsertBitOp(vector, value, index)


# ============================================================================
# ON-QUBIT OPERATIONS (Direct Bit Manipulation)
# ============================================================================


@irdl_op_definition
class OnQubitNotOp(IRDLOperation):
    """
    Operation to apply the NOT gate directly to an indexed bit in a register.

    This operation applies a NOT gate to a specific bit within a vector register,
    avoiding the need for separate extract and insert operations.
    """

    name = "quantum.OnQubit_not"
    vector: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)

    def __init__(self, vector: SSAValue, bit_index: int):
        """
        @brief Apply a NOT gate OnQubitly to a specific bit in a vector.

        @param vector: The vector of qubits
        @param bit_index: The index of the bit to apply the NOT gate to
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
        """
        @brief Factory method to create a OnQubitNotOp from a vector and bit index.

        @param vector: The vector of qubits
        @param bit_index: The index of the bit to apply the NOT gate to
        @return A new OnQubitNotOp instance
        """
        return OnQubitNotOp(vector, bit_index)


@irdl_op_definition
class OnQubitCNotOp(IRDLOperation):
    """
    @brief Operation to apply the CNOT gate OnQubitly to indexed bits in registers.

    This operation applies a CNOT gate between two specific bits within vector registers,
    avoiding the need for separate extract and insert operations.
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
        """
        @brief Apply a CNOT gate OnQubitly between specific bits in vectors.

        @param control_vector: The vector containing the control qubit
        @param control_index: The index of the control bit
        @param target_vector: The vector containing the target qubit
        @param target_index: The index of the target bit
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
        """
        @brief Factory method to create a OnQubitCNotOp.

        @param control_vector: The vector containing the control qubit
        @param control_index: The index of the control bit
        @param target_vector: The vector containing the target qubit
        @param target_index: The index of the target bit
        @return A new OnQubitCNotOp instance
        """
        return OnQubitCNotOp(control_vector, control_index, target_vector, target_index)


@irdl_op_definition
class OnQubitCCnotOp(IRDLOperation):
    """
    @brief Operation to apply the CCNOT gate OnQubitly to indexed bits in registers.

    This operation applies a CCNOT gate between two control bits and a target bit
    within vector registers, avoiding the need for separate extract and insert operations.
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
        """
        @brief Apply a CCNOT gate OnQubitly between specific bits in vectors.

        @param control1_vector: The vector containing the first control qubit
        @param control1_index: The index of the first control bit
        @param control2_vector: The vector containing the second control qubit
        @param control2_index: The index of the second control bit
        @param target_vector: The vector containing the target qubit
        @param target_index: The index of the target bit
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
        """
        @brief Factory method to create a OnQubitCCnotOp.
        @param control1_vector: The vector containing the first control qubit
        @param control1_index: The index of the first control bit
        @param control2_vector: The vector containing the second control qubit
        @param control2_index: The index of the second control bit
        @param target_vector: The vector containing the target qubit
        @param target_index: The index of the target bit
        @return A new OnQubitCCnotOp instance
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
    """
    @brief Operation to apply the Hadamard gate to a specific qubit in a register.
    
    This operation applies a Hadamard gate to a specific qubit within a vector register,
    creating superposition: H|0⟩ = (|0⟩ + |1⟩)/√2, H|1⟩ = (|0⟩ - |1⟩)/√2
    """
    
    name = "quantum.OnQubit_hadamard"
    register: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)
    
    def __init__(self, register: SSAValue, index: int):
        """
        @brief Apply a Hadamard gate to a specific qubit in a vector.
        
        @param register: The vector containing the qubit
        @param index: The index of the qubit to apply Hadamard to
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
        """
        @brief Factory method to create a OnQubitHadamardOp.
        
        @param register: The vector containing the qubit
        @param index: The index of the qubit
        @return A new OnQubitHadamardOp instance
        """
        return OnQubitHadamardOp(register, index)


@irdl_op_definition
class OnQubitPhaseOp(IRDLOperation):
    """
    @brief Operation to apply a phase gate to a specific qubit in a register.
    
    This operation applies a phase rotation to a specific qubit within a vector register.
    Phase gate: |0⟩ → |0⟩, |1⟩ → e^(iθ)|1⟩
    """
    
    name = "quantum.OnQubit_phase"
    register: Operand = operand_def(VectorType)
    index: IntegerAttr = attr_def(IntegerAttr)
    phase: FloatAttr = attr_def(FloatAttr)
    res: OpResult = result_def(VectorType)
    
    def __init__(self, register: SSAValue, index: int, phase: float):
        """
        @brief Apply a phase gate to a specific qubit in a vector.
        
        @param register: The vector containing the qubit
        @param index: The index of the qubit to apply phase to
        @param phase: The phase angle in radians
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
        """
        @brief Factory method to create a OnQubitPhaseOp.
        
        @param register: The vector containing the qubit
        @param index: The index of the qubit
        @param phase: The phase angle in radians
        @return A new OnQubitPhaseOp instance
        """
        return OnQubitPhaseOp(register, index, phase)


@irdl_op_definition
class OnQubitControlledPhaseOp(IRDLOperation):
    """
    @brief Operation to apply a controlled phase rotation to qubits in registers.
    
    This operation applies a controlled phase rotation where the phase is applied
    to the target qubit only if the control qubit is in state |1⟩.
    """
    
    name = "quantum.OnQubit_controlled_phase"
    control_register: Operand = operand_def(VectorType)
    target_register: Operand = operand_def(VectorType)
    control_index: IntegerAttr = attr_def(IntegerAttr)
    target_index: IntegerAttr = attr_def(IntegerAttr)
    phase: FloatAttr = attr_def(FloatAttr)
    res: OpResult = result_def(VectorType)
    
    def __init__(self, control_register: SSAValue, control_index: int,
                 target_register: SSAValue, target_index: int, phase: float):
        """
        @brief Apply a controlled phase rotation between specific qubits.
        
        @param control_register: The vector containing the control qubit
        @param control_index: The index of the control qubit
        @param target_register: The vector containing the target qubit
        @param target_index: The index of the target qubit
        @param phase: The phase angle in radians
        """
        if isinstance(control_register.type, VectorType) and isinstance(target_register.type, VectorType):
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
    def from_values(control_register: SSAValue, control_index: int,
                   target_register: SSAValue, target_index: int, 
                   phase: float) -> "OnQubitControlledPhaseOp":
        """
        @brief Factory method to create a OnQubitControlledPhaseOp.
        
        @param control_register: The vector containing the control qubit
        @param control_index: The index of the control qubit
        @param target_register: The vector containing the target qubit
        @param target_index: The index of the target qubit
        @param phase: The phase angle in radians
        @return A new OnQubitControlledPhaseOp instance
        """
        return OnQubitControlledPhaseOp(control_register, control_index, 
                                       target_register, target_index, phase)


@irdl_op_definition
class OnQubitSwapOp(IRDLOperation):
    """
    @brief Operation to swap two qubits within a register.
    
    This operation swaps the states of two qubits within the same vector register.
    """
    
    name = "quantum.OnQubit_swap"
    register: Operand = operand_def(VectorType)
    qubit1_index: IntegerAttr = attr_def(IntegerAttr)
    qubit2_index: IntegerAttr = attr_def(IntegerAttr)
    res: OpResult = result_def(VectorType)
    
    def __init__(self, register: SSAValue, qubit1_index: int, qubit2_index: int):
        """
        @brief Swap two qubits within a vector register.
        
        @param register: The vector containing both qubits
        @param qubit1_index: The index of the first qubit
        @param qubit2_index: The index of the second qubit
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
    def from_values(register: SSAValue, qubit1_index: int, qubit2_index: int) -> "OnQubitSwapOp":
        """
        @brief Factory method to create a OnQubitSwapOp.
        
        @param register: The vector containing both qubits
        @param qubit1_index: The index of the first qubit
        @param qubit2_index: The index of the second qubit
        @return A new OnQubitSwapOp instance
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

# The Quantum dialect is automatically registered when this module is imported
# and provides all quantum operations for the C-to-Quantum compiler's IR generation.
