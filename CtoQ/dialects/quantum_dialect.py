"""
@file quantum_dialect.py
@brief Quantum operation dialect implementation for the C to Quantum compiler.

This module defines a set of quantum operations for use in the C to Quantum
compiler's intermediate representation (IR). It provides a collection of
quantum gates and operations that can be used to build quantum circuits,
including initialization, measurement, and various quantum gates like NOT,
CNOT, CCNOT, Hadamard, and T gates.

The operations are defined using xDSL's IR definition language (IRDL) and
are registered as part of the "quantum" dialect.
"""

from __future__ import annotations

from typing import TypeVar

from xdsl.dialects.builtin import IntegerType, StringAttr, VectorType,IntegerAttr
from xdsl.ir import Dialect, OpResult, SSAValue, Region, Attribute
from xdsl.irdl import IRDLOperation, Operand, attr_def, irdl_op_definition, operand_def, result_def, region_def


@irdl_op_definition
class InitOp(IRDLOperation):
    """
    @brief Operation to initialize a qubit or a vector of qubits to zero.
    
    This operation creates a new qubit or vector of qubits, initializing
    them to the |0⟩ state, which is the standard initial state for 
    quantum computation.
    
    @see MeasureOp
    """

    name = "quantum.init"
    value: IntegerType = attr_def(TypeVar("AttributeInvT", bound=Attribute))
    res: OpResult = result_def()

    def __init__(self, values):
        """
        @brief Initialize a qubit or vector of qubits to zero.
        
        @param values: An IntegerType for a single qubit or a VectorType for multiple qubits
        @throws TypeError if values is not an IntegerType or VectorType of IntegerType
        """
        # Determine if values is a single IntegerType or a VectorType of IntegerType
        result_types=[]
        attributes=[]
        if isinstance(values, IntegerType):
            # Single IntegerType case
            result_types = [IntegerType(1)]
            attributes = {"type": values,"value": IntegerAttr(0,IntegerType(1))}   
        elif isinstance(values, VectorType):
            # Vector of IntegerType case
            result_types= [VectorType(values.get_element_type(), [values.get_shape()[0],])]     
            attributes = {"type": values,"value": IntegerAttr(0,IntegerType(values.get_shape()[0]))}
        else: 
            raise TypeError("Expected IntegerType or VectorType(IntegerType) for values")

        super().__init__(result_types=result_types, attributes=attributes)
           
    @staticmethod
    def from_value(value) -> InitOp:
        """
        @brief Factory method to create an InitOp from a value.
        
        @param value: The value to initialize qubits from
        @return A new InitOp instance
        """
        return InitOp(value)


@irdl_op_definition
class NotOp(IRDLOperation):
    """
    @brief Operation to apply the NOT gate (X gate) to a qubit or vector of qubits.
    
    The NOT gate flips the state of a qubit, changing |0⟩ to |1⟩ and vice versa.
    It is one of the fundamental single-qubit gates in quantum computing.
    
    @see CNotOp
    @see CCNotOp
    """

    name = "quantum.not"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a NOT gate to a target qubit or vector of qubits.
        
        @param target: The qubit or vector of qubits to apply the NOT gate to
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else: # VectorType
            size=target.type.get_shape()[0]
            super().__init__(result_types=[VectorType(IntegerType(1),[size,])], operands=[target])
    
    @staticmethod
    def from_value(value: SSAValue) -> NotOp:
        """
        @brief Factory method to create a NotOp from a value.
        
        @param value: The target qubit or vector of qubits
        @return A new NotOp instance
        """
        return NotOp(value)
    

@irdl_op_definition
class CNotOp(IRDLOperation):
    """
    @brief Operation to apply the CNOT gate (Controlled-NOT) to qubits.
    
    The CNOT gate is a two-qubit operation where the state of the target qubit
    is flipped if the control qubit is in the |1⟩ state. It is fundamental for
    creating entanglement between qubits.
    
    @see NotOp
    @see CCNotOp
    """

    name = "quantum.cnot"
    control: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    res: OpResult = result_def()

    def __init__(self, control: SSAValue, target: SSAValue):
        """
        @brief Apply a CNOT gate with the specified control and target qubits.
        
        @param control: The control qubit (or vector of control qubits)
        @param target: The target qubit (or vector of target qubits)
        """
        if isinstance(control.type, IntegerType) and isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[control, target])
        else: # VectorType
            size = control.type.get_shape()[0]
            super().__init__(result_types=[VectorType(IntegerType(1),[size,])], operands=[control, target])

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
    control1: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    control2: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    res: OpResult = result_def()

    def __init__(self, control1: SSAValue, control2: SSAValue, target: SSAValue):
        """
        @brief Apply a CCNOT gate with the specified control and target qubits.
        
        @param control1: The first control qubit (or vector of control qubits)
        @param control2: The second control qubit (or vector of control qubits)
        @param target: The target qubit (or vector of target qubits)
        """
        if isinstance(control1.type, IntegerType) and isinstance(control2.type, IntegerType) and isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[control1, control2, target])
        else: # VectorType
            size = control1.type.get_shape()[0]
            super().__init__(result_types=[VectorType(IntegerType(1),[size,])], operands=[control1, control2, target])
 
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
        else: # VectorType
            size=target.type.get_shape()[0]
            super().__init__(result_types=[VectorType(IntegerType(1),[size,])], operands=[target])

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

    def __init__(self, name: str, region: Region | type[Region.DEFAULT] = Region.DEFAULT):
        """
        @brief Define a quantum function with the specified name and region.
        
        @param name: The function name
        @param region: The region containing the function body operations
        """
        attributes: dict[str, Attribute] = { "func_name": StringAttr(name) }
        return super().__init__(attributes=attributes, regions=[region])


@irdl_op_definition
class TGateOp(IRDLOperation):
    """
    @brief T-Gate operation for phase rotation.
    
    The T gate is a single-qubit operation that rotates the state vector around
    the Z-axis of the Bloch sphere by π/4 radians (45 degrees). It is particularly
    important for universal quantum computation.
    
    @see TDaggerGateOp
    """

    name = "quantum.t"
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a T gate to a target qubit or vector of qubits.
        
        @param target: The qubit or vector of qubits to apply the T gate to
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else: # VectorType
            size=target.type.get_shape()[0]
            super().__init__(result_types=[VectorType(IntegerType(1),[size,])], operands=[target])
    
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
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a T-Dagger gate to a target qubit or vector of qubits.
        
        @param target: The qubit or vector of qubits to apply the T-Dagger gate to
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else: # VectorType
            size=target.type.get_shape()[0]
            super().__init__(result_types=[VectorType(IntegerType(1),[size,])], operands=[target])

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
    target: Operand = operand_def(TypeVar("AttributeInvT", bound=Attribute))
    res: OpResult = result_def()

    def __init__(self, target: SSAValue):
        """
        @brief Apply a Hadamard gate to a target qubit or vector of qubits.
        
        @param target: The qubit or vector of qubits to apply the Hadamard gate to
        """
        if isinstance(target.type, IntegerType):
            super().__init__(result_types=[IntegerType(1)], operands=[target])
        else: # VectorType
            size=target.type.get_shape()[0]
            super().__init__(result_types=[VectorType(IntegerType(1),[size,])], operands=[target])

    @staticmethod
    def from_value(target: SSAValue) -> HadamardOp:
        """
        @brief Factory method to create a HadamardOp from a target value.
        
        @param target: The qubit or vector of qubits to apply the Hadamard gate to
        @return A new HadamardOp instance
        """
        return HadamardOp(target)


# Register the quantum dialect with all defined operations
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
        HadamardOp
    ],
    [],
)