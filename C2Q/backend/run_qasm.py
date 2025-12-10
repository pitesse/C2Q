"""
MLIR Quantum Circuit Metrics Calculator

This module analyzes quantum MLIR files and calculates various metrics
about the quantum circuits they represent, including:
- Circuit depth, width, and gate count
- T-gate specific metrics
- Quantum circuit visualization
- Circuit conversion to Qiskit format

Example:
    python run_qasm.py path/to/quantum_ir.mlir
"""

import sys
from pathlib import Path
import argparse

from qiskit import QuantumCircuit

# Resolve import paths explicitly
from qiskit.circuit import QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGOpNode
import matplotlib.pyplot as plt
from qiskit.visualization import circuit_drawer

from xdsl.parser import Parser
from xdsl.context import Context
from xdsl.dialects.builtin import Builtin, IntegerAttr, IntegerType, FloatAttr, Float64Type

from C2Q.dialects.quantum_dialect import Quantum

# ============================================================================
# MLIR PARSING FUNCTIONS
# ============================================================================


def parse_mlir_file(file_path):
    """
    Parse an MLIR file into IR objects.
    
    Args:
        file_path: Path to the MLIR file
        
    Returns:
        Module object containing the parsed IR
    """
    with open(file_path, "r") as f:
        mlir_content = f.read()

    # create context and register dialects
    context = Context()
    context.load_dialect(Builtin)
    context.load_dialect(Quantum)

    # parse the MLIR file
    parser = Parser(context, mlir_content)
    module = parser.parse_module()

    return module


# ============================================================================
# QISKIT CIRCUIT CREATION FUNCTIONS
# ============================================================================

# Global SSA value to Qiskit register mapping
# Maps xDSL SSA values to (QuantumRegister, base_name) tuples
_ssa_to_qreg = {}


def get_register_for_ssa(ssa_value):
    """
    Look up the Qiskit register for an SSA value.
    
    This function traces through the SSA chain to find the original register.
    Each SSA value in a quantum wire (from init through gates) maps to the same register.
    
    Args:
        ssa_value: xDSL SSA value (operand or result)
        
    Returns:
        Tuple of (QuantumRegister, base_name) or (None, None) if not found
    """
    if ssa_value in _ssa_to_qreg:
        return _ssa_to_qreg[ssa_value]
    return None, None


def register_ssa_mapping(ssa_value, qreg, base_name):
    """
    Register an SSA value to Qiskit register mapping.
    
    Args:
        ssa_value: xDSL SSA value
        qreg: Qiskit QuantumRegister
        base_name: Base name of the register (e.g., 'q0')
    """
    _ssa_to_qreg[ssa_value] = (qreg, base_name)


def propagate_ssa_mapping(from_ssa, to_ssa):
    """
    Propagate SSA mapping from one value to another.
    
    Used when a gate produces a new SSA result that represents the same qubit wire.
    
    Args:
        from_ssa: Source SSA value (operand)
        to_ssa: Target SSA value (result)
    """
    if from_ssa in _ssa_to_qreg:
        _ssa_to_qreg[to_ssa] = _ssa_to_qreg[from_ssa]


def clear_ssa_mappings():
    """Clear all SSA mappings. Call before creating a new circuit."""
    _ssa_to_qreg.clear()


def create_quantum_register(op):
    """
    Create a Qiskit QuantumRegister from an IR operation.
    
    Args:
        op: IR operation representing a quantum register
        
    Returns:
        Qiskit QuantumRegister object
    """
    result = op.results[0]
    base_name = "q0"  # Default name
    if hasattr(result, "_name") and result._name:
        reg_name = result._name
        # Extract the base register name (e.g., q0 from q0_1)
        base_name = reg_name.split("_")[0]
    else:
        print("Warning: Register name not found")

    # Get vector size
    vec_size = 1
    if hasattr(op, "result_types") and hasattr(op.result_types[0], "get_shape"):
        vec_size = op.result_types[0].get_shape()[0]

    q_reg = QuantumRegister(vec_size, name=base_name)

    return q_reg


def apply_not(circuit, op):
    """
    Apply a NOT gate to the circuit.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: IR operation representing the NOT gate
    """
    if len(op.operands) == 1:
        qubit = op.operands[0]
        if hasattr(qubit, "_name") and qubit._name:
            qubit_name = qubit._name
            # (e.g., q0 from q0_0)
            base_name = qubit_name.split("_")[0]
            # (e.g., "0" from "[0]")
            qubit_index = int(qubit_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == base_name:
                    circuit.x(qreg[qubit_index])
                    return

            print(f"Warning: Register {base_name} not found in circuit")
        else:
            print("Warning: Operand name not found")
    else:
        print("Warning: Invalid number of operands for NOT operation")


def apply_onqubit_not(circuit, op):
    """
    Apply a direct NOT gate to a specific bit in a register.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: OnQubitNotOp operation
    """
    if len(op.operands) == 1:
        # Get the vector register via SSA mapping
        vector = op.operands[0]
        qreg, base_name = get_register_for_ssa(vector)

        # Get the index from the operation attributes
        if hasattr(op, "attributes") and "index" in op.attributes:
            bit_index = op.attributes["index"].value.data

            if qreg is not None:
                # Apply the NOT gate directly to the bit
                circuit.x(qreg[bit_index])
                
                # Propagate SSA mapping if this op produces a result
                if hasattr(op, "results") and op.results:
                    propagate_ssa_mapping(vector, op.results[0])
                return
            else:
                # STRICT MODE: No fallback - SSA mapping must exist
                ssa_name = vector._name if hasattr(vector, '_name') else str(vector)
                raise ValueError(f"SSA Mapping failed for operand in OnQubit NOT: {ssa_name}")
        else:
            raise ValueError("Bit index attribute not found for OnQubit NOT operation")
    else:
        raise ValueError(f"Invalid number of operands for OnQubit NOT operation: expected 1, got {len(op.operands)}")


def apply_onqubit_cnot(circuit, op):
    """
    Apply a direct CNOT gate between bits in two registers.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: OnQubitCNotOp operation
    """
    if len(op.operands) == 2:
        # Get the control and target vectors via SSA mapping
        control_vector = op.operands[0]
        target_vector = op.operands[1]
        
        control_qreg, _ = get_register_for_ssa(control_vector)
        target_qreg, _ = get_register_for_ssa(target_vector)

        # Get the indices from attributes
        if (
            hasattr(op, "attributes")
            and "control_index" in op.attributes
            and "target_index" in op.attributes
        ):
            control_index = op.attributes["control_index"].value.data
            target_index = op.attributes["target_index"].value.data

            if control_qreg is not None and target_qreg is not None:
                # Apply CNOT directly between the bits
                circuit.cx(control_qreg[control_index], target_qreg[target_index])
                
                # Propagate SSA mapping for both results if they exist
                if hasattr(op, "results") and len(op.results) >= 2:
                    propagate_ssa_mapping(control_vector, op.results[0])
                    propagate_ssa_mapping(target_vector, op.results[1])
                return
            else:
                # STRICT MODE: No fallback - SSA mapping must exist
                ctrl_name = control_vector._name if hasattr(control_vector, '_name') else str(control_vector)
                tgt_name = target_vector._name if hasattr(target_vector, '_name') else str(target_vector)
                if control_qreg is None:
                    raise ValueError(f"SSA Mapping failed for control operand in OnQubit CNOT: {ctrl_name}")
                if target_qreg is None:
                    raise ValueError(f"SSA Mapping failed for target operand in OnQubit CNOT: {tgt_name}")
        else:
            raise ValueError("Index attributes not found for OnQubit CNOT operation")
    else:
        raise ValueError(f"Invalid number of operands for OnQubit CNOT operation: expected 2, got {len(op.operands)}")


def apply_cnot(circuit, op):
    """
    Apply a CNOT gate to the circuit.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: IR operation representing the CNOT gate
    """
    if len(op.operands) == 2:
        control_qubit = op.operands[0]
        target_qubit = op.operands[1]
        control_qreg = None
        target_qreg = None

        if hasattr(control_qubit, "_name") and control_qubit._name:
            control_name = control_qubit._name
            base_name = control_name.split("_")[0]
            control_index = int(control_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == base_name:
                    control_qreg = qreg[control_index]
                    break
            else:
                print(f"Warning: Control register {base_name} not found in circuit")
                return

        if hasattr(target_qubit, "_name") and target_qubit._name:
            target_name = target_qubit._name
            base_name = target_name.split("_")[0]
            target_index = int(target_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == base_name:
                    target_qreg = qreg[target_index]
                    break
            else:
                print(f"Warning: Target register {base_name} not found in circuit")
                return

        if control_qreg is not None and target_qreg is not None:
            circuit.cx(control_qreg, target_qreg)
    else:
        print("Warning: Invalid number of operands for CNOT operation")


def apply_ccnot(circuit, op):
    """
    Apply a CCNOT gate to the circuit.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: IR operation representing the CCNOT gate
    """
    if len(op.operands) == 3:
        control_qubit1 = op.operands[0]
        control_qubit2 = op.operands[1]
        target_qubit = op.operands[2]
        c1_qreg = None
        c2_qreg = None
        t_qreg = None

        # Extract control and target qubits properly
        if hasattr(control_qubit1, "_name") and control_qubit1._name:
            c1_name = control_qubit1._name
            c1_base = c1_name.split("_")[0]
            c1_index = int(c1_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == c1_base:
                    c1_qreg = qreg[c1_index]
                    break
            else:
                print(f"Warning: Control register {c1_base} not found in circuit")
                return

        if hasattr(control_qubit2, "_name") and control_qubit2._name:
            c2_name = control_qubit2._name
            c2_base = c2_name.split("_")[0]
            c2_index = int(c2_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == c2_base:
                    c2_qreg = qreg[c2_index]
                    break
            else:
                print(f"Warning: Control register {c2_base} not found in circuit")
                return

        if hasattr(target_qubit, "_name") and target_qubit._name:
            t_name = target_qubit._name
            t_base = t_name.split("_")[0]

            # Check if the name contains brackets
            if "[" in t_name:
                # Handle standard format with brackets: q0_65[31]
                t_index = int(t_name.split("[")[1].split("]")[0])
                for qreg in circuit.qregs:
                    if qreg.name == t_base:
                        t_qreg = qreg[t_index]
                        break
                else:
                    print(f"Warning: Target register {t_base} not found in circuit")
                    return
            else:
                # Handle ancilla qubit format: z_0
                # Check if we already have a register for this qubit
                for qreg in circuit.qregs:
                    if qreg.name == t_base:
                        # If found, assume index 0 for single-qubit register
                        t_qreg = qreg[0]
                        break
                else:
                    # If not found, create a new single-qubit register
                    print(f"Creating new register for ancilla qubit {t_name}")
                    new_qreg = QuantumRegister(1, name=t_base)
                    circuit.add_register(new_qreg)
                    t_qreg = new_qreg[0]

        # Use the built-in ccx gate (Toffoli)
        if c1_qreg is not None and c2_qreg is not None and t_qreg is not None:
            circuit.ccx(c1_qreg, c2_qreg, t_qreg)
    else:
        print("Warning: Invalid number of operands for CCNOT operation")


# ============================================================================
# ADVANCED QUANTUM GATE OPERATIONS
# ============================================================================


def apply_onqubit_ccnot(circuit, op):
    """
    Apply a direct CCNOT gate between bits in three registers.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: OnQubitCCnotOp operation
    """
    if len(op.operands) == 3:
        # Get the vectors via SSA mapping
        control1_vector = op.operands[0]
        control2_vector = op.operands[1]
        target_vector = op.operands[2]
        
        control1_qreg, _ = get_register_for_ssa(control1_vector)
        control2_qreg, _ = get_register_for_ssa(control2_vector)
        target_qreg, _ = get_register_for_ssa(target_vector)

        # Get indices from attributes
        if (
            hasattr(op, "attributes")
            and "control1_index" in op.attributes
            and "control2_index" in op.attributes
            and "target_index" in op.attributes
        ):
            control1_index = op.attributes["control1_index"].value.data
            control2_index = op.attributes["control2_index"].value.data
            target_index = op.attributes["target_index"].value.data

            if control1_qreg and control2_qreg and target_qreg:
                # Apply CCNOT directly between bits
                circuit.ccx(
                    control1_qreg[control1_index],
                    control2_qreg[control2_index],
                    target_qreg[target_index],
                )
                
                # Propagate SSA mappings
                if hasattr(op, "results") and len(op.results) >= 3:
                    propagate_ssa_mapping(control1_vector, op.results[0])
                    propagate_ssa_mapping(control2_vector, op.results[1])
                    propagate_ssa_mapping(target_vector, op.results[2])
                return
            
            # STRICT MODE: No fallback - SSA mapping must exist
            if control1_qreg is None:
                c1_name = control1_vector._name if hasattr(control1_vector, '_name') else str(control1_vector)
                raise ValueError(f"SSA Mapping failed for control1 operand in OnQubit CCNOT: {c1_name}")
            if control2_qreg is None:
                c2_name = control2_vector._name if hasattr(control2_vector, '_name') else str(control2_vector)
                raise ValueError(f"SSA Mapping failed for control2 operand in OnQubit CCNOT: {c2_name}")
            if target_qreg is None:
                tgt_name = target_vector._name if hasattr(target_vector, '_name') else str(target_vector)
                raise ValueError(f"SSA Mapping failed for target operand in OnQubit CCNOT: {tgt_name}")
        else:
            raise ValueError("Index attributes not found for OnQubit CCNOT operation")
    else:
        raise ValueError(f"Invalid number of operands for OnQubit CCNOT operation: expected 3, got {len(op.operands)}")


def apply_onqubit_hadamard(circuit, op):
    """
    Apply a Hadamard gate to a specific bit in a register.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: OnQubitHadamardOp operation
    """
    if len(op.operands) == 1:
        # Get the register via SSA mapping
        operand = op.operands[0]
        qreg, _ = get_register_for_ssa(operand)
        bit_index = op.attributes.get("index", IntegerAttr(0, IntegerType(32))).value.data
        
        if qreg is not None:
            circuit.h(qreg[bit_index])
            
            # Propagate SSA mapping if this op produces a result
            if hasattr(op, "results") and op.results:
                propagate_ssa_mapping(operand, op.results[0])
            return
        
        # STRICT MODE: No fallback - SSA mapping must exist
        ssa_name = operand._name if hasattr(operand, '_name') else str(operand)
        raise ValueError(f"SSA Mapping failed for operand in OnQubit Hadamard: {ssa_name}")
    else:
        raise ValueError(f"OnQubitHadamardOp expects 1 operand, got {len(op.operands)}")

def apply_onqubit_phase(circuit, op):
    """
    Apply a phase gate to a specific bit in a register.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: OnQubitPhaseOp operation
    """
    if len(op.operands) == 1:
        # Get the register via SSA mapping
        operand = op.operands[0]
        qreg, _ = get_register_for_ssa(operand)
        bit_index = op.attributes.get("index", IntegerAttr(0, IntegerType(32))).value.data
        phase = op.attributes.get("phase", FloatAttr(0.0, Float64Type())).value.data
        
        if qreg is not None:
            circuit.p(phase, qreg[bit_index])
            
            # Propagate SSA mapping if this op produces a result
            if hasattr(op, "results") and op.results:
                propagate_ssa_mapping(operand, op.results[0])
            return
        
        # SSA mapping is required - no fallback
        raise ValueError("SSA Mapping failed for Phase operand")
    else:
        print(f"Warning: OnQubitPhaseOp expects 1 operand, got {len(op.operands)}")

def apply_onqubit_controlled_phase(circuit, op):
    """
    Apply a controlled phase gate between specific bits.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: OnQubitControlledPhaseOp operation
    """
    if len(op.operands) == 2:
        # Get the control and target operands via SSA mapping
        control_operand = op.operands[0]
        target_operand = op.operands[1]
        
        control_reg, _ = get_register_for_ssa(control_operand)
        target_reg, _ = get_register_for_ssa(target_operand)
        
        # Get indices and phase
        control_index = op.attributes.get("control_index", IntegerAttr(0, IntegerType(32))).value.data
        target_index = op.attributes.get("target_index", IntegerAttr(0, IntegerType(32))).value.data
        phase = op.attributes.get("phase", FloatAttr(0.0, Float64Type())).value.data
        
        if control_reg is not None and target_reg is not None:
            # Apply controlled phase rotation
            circuit.cp(phase, control_reg[control_index], target_reg[target_index])
            
            # Propagate SSA mapping for results
            if hasattr(op, "results") and len(op.results) >= 2:
                propagate_ssa_mapping(control_operand, op.results[0])
                propagate_ssa_mapping(target_operand, op.results[1])
            return
        
        # SSA mapping is required - no fallback
        if control_reg is None:
            raise ValueError("SSA Mapping failed for Controlled Phase control operand")
        raise ValueError("SSA Mapping failed for Controlled Phase target operand")
    else:
        print(f"Warning: OnQubitControlledPhaseOp expects 2 operands, got {len(op.operands)}")

def apply_onqubit_swap(circuit, op):
    """
    Apply a SWAP gate between specific bits in a register.
    
    Args:
        circuit: Qiskit QuantumCircuit object
        op: OnQubitSwapOp operation
    """
    if len(op.operands) == 1:
        # Get the register via SSA mapping
        operand = op.operands[0]
        qreg, _ = get_register_for_ssa(operand)
        qubit1_index = op.attributes.get("qubit1_index", IntegerAttr(0, IntegerType(32))).value.data
        qubit2_index = op.attributes.get("qubit2_index", IntegerAttr(0, IntegerType(32))).value.data
        
        if qreg is not None:
            circuit.swap(qreg[qubit1_index], qreg[qubit2_index])
            
            # Propagate SSA mapping if this op produces a result
            if hasattr(op, "results") and op.results:
                propagate_ssa_mapping(operand, op.results[0])
            return
        
        # SSA mapping is required - no fallback
        raise ValueError("SSA Mapping failed for SWAP operand")
    else:
        print(f"Warning: OnQubitSwapOp expects 1 operand, got {len(op.operands)}")

def apply_hadamard(circuit, op):
    """!
    @brief Apply a Hadamard gate to the circuit
    @param circuit Qiskit QuantumCircuit object
    @param op IR operation representing the Hadamard gate
    """
    if len(op.operands) == 1:
        qubit = op.operands[0]
        if hasattr(qubit, "_name") and qubit._name:
            qubit_name = qubit._name
            base_name = qubit_name.split("_")[0]
            qubit_index = int(qubit_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == base_name:
                    circuit.h(qreg[qubit_index])
                    return

            print(f"Warning: Register {base_name} not found in circuit")
        else:
            print("Warning: Operand name not found")
    else:
        print("Warning: Invalid number of operands for Hadamard operation")


def apply_t(circuit, op):
    """!
    @brief Apply a T gate to the circuit
    @param circuit Qiskit QuantumCircuit object
    @param op IR operation representing the T gate
    """
    if len(op.operands) == 1:
        qubit = op.operands[0]
        if hasattr(qubit, "_name") and qubit._name:
            qubit_name = qubit._name
            base_name = qubit_name.split("_")[0]
            qubit_index = int(qubit_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == base_name:
                    circuit.t(qreg[qubit_index])
                    return

            print(f"Warning: Register {base_name} not found in circuit")
        else:
            print("Warning: Operand name not found")
    else:
        print("Warning: Invalid number of operands for T operation")


def apply_tdagger(circuit, op):
    """!
    @brief Apply a T-dagger gate to the circuit
    @param circuit Qiskit QuantumCircuit object
    @param op IR operation representing the T-dagger gate
    """
    if len(op.operands) == 1:
        qubit = op.operands[0]
        if hasattr(qubit, "_name") and qubit._name:
            qubit_name = qubit._name
            base_name = qubit_name.split("_")[0]
            qubit_index = int(qubit_name.split("[")[1].split("]")[0])
            for qreg in circuit.qregs:
                if qreg.name == base_name:
                    circuit.tdg(qreg[qubit_index])
                    return

            print(f"Warning: Register {base_name} not found in circuit")
        else:
            print("Warning: Operand name not found")
    else:
        print("Warning: Invalid number of operands for T-dagger operation")


def build_ssa_mapping(first_op, quantum_registers):
    """
    Build SSA value to register mapping by walking through all operations.
    
    This first pass establishes the mapping from SSA values to their corresponding
    Qiskit registers. Gate operations that produce results propagate the mapping
    from their operands to their results (same qubit wire, new SSA value).
    
    Args:
        first_op: First operation in the IR
        quantum_registers: Dict mapping register names to Qiskit QuantumRegister objects
    """
    current_op = first_op
    
    while current_op is not None:
        op_name = current_op.name
        
        # For init operations, the result is the initial register SSA value
        if op_name == "quantum.init" and hasattr(current_op, "results") and current_op.results:
            result = current_op.results[0]
            if hasattr(result, "_name") and result._name:
                base_name = result._name.split("_")[0]
                if base_name in quantum_registers:
                    register_ssa_mapping(result, quantum_registers[base_name], base_name)
        
        # For gate operations that produce results, propagate from operand to result
        # Single-operand gates (NOT, Hadamard, Phase, etc.)
        elif op_name in ["quantum.OnQubit_not", "quantum.OnQubit_hadamard", 
                         "quantum.OnQubit_phase", "quantum.OnQubit_swap"]:
            if len(current_op.operands) >= 1 and hasattr(current_op, "results") and current_op.results:
                propagate_ssa_mapping(current_op.operands[0], current_op.results[0])
        
        # Two-operand gates with single result (CNOT, Controlled Phase)
        # The result represents the TARGET qubit (operand[1]), not the control
        elif op_name in ["quantum.OnQubit_cnot", "quantum.OnQubit_controlled_phase"]:
            if len(current_op.operands) >= 2 and hasattr(current_op, "results") and current_op.results:
                # The single result is the new value of the target qubit (operand[1])
                propagate_ssa_mapping(current_op.operands[1], current_op.results[0])
        
        # Three-operand gates with single result (CCNOT)
        # The result represents the TARGET qubit (operand[2])
        elif op_name == "quantum.OnQubit_ccnot":
            if len(current_op.operands) >= 3 and hasattr(current_op, "results") and current_op.results:
                # The single result is the new value of the target qubit (operand[2])
                propagate_ssa_mapping(current_op.operands[2], current_op.results[0])
        
        current_op = current_op.next_op


def create_circuit(first_op, output_number):
    """
    Create a Qiskit quantum circuit from IR operations with preserved register names.
    
    Uses SSA value mapping to correctly track qubit registers through optimization passes.
    This is a two-pass approach:
    1. First pass: Create registers and build SSA mapping
    2. Second pass: Apply gates using SSA mapping
    """
    # Clear any previous SSA mappings
    clear_ssa_mappings()
    
    quantum_registers = {}
    reg_counter = 0
    current_op = first_op

    circuit = QuantumCircuit()
    
    # PASS 1: Create all quantum registers first
    while current_op is not None:
        if (
            current_op.name == "quantum.init"
            and hasattr(current_op, "results")
            and current_op.results
        ):
            new_reg = create_quantum_register(current_op)
            if new_reg.name not in quantum_registers:
                quantum_registers[new_reg.name] = new_reg
                reg_counter += 1
                circuit.add_register(new_reg)
        current_op = current_op.next_op
    
    # Build full SSA mapping by walking through all operations
    build_ssa_mapping(first_op, quantum_registers)
    
    # PASS 2: Apply all gates
    current_op = first_op
    while current_op is not None:
        if current_op.name == "quantum.not":
            apply_not(circuit, current_op)
        elif current_op.name == "quantum.OnQubit_not":
            apply_onqubit_not(circuit, current_op)
        elif current_op.name == "quantum.cnot":
            apply_cnot(circuit, current_op)
        elif current_op.name == "quantum.OnQubit_cnot":
            apply_onqubit_cnot(circuit, current_op)
        elif current_op.name == "quantum.ccnot":
            apply_ccnot(circuit, current_op)
        elif current_op.name == "quantum.OnQubit_ccnot":
            apply_onqubit_ccnot(circuit, current_op)
        elif current_op.name == "quantum.OnQubit_hadamard":
            apply_onqubit_hadamard(circuit, current_op)
        elif current_op.name == "quantum.OnQubit_phase":
            apply_onqubit_phase(circuit, current_op)
        elif current_op.name == "quantum.OnQubit_controlled_phase":
            apply_onqubit_controlled_phase(circuit, current_op)
        elif current_op.name == "quantum.OnQubit_swap":
            apply_onqubit_swap(circuit, current_op)
        elif current_op.name == "quantum.h" and current_op.operands:
            apply_hadamard(circuit, current_op)
        elif current_op.name == "quantum.t" and current_op.operands:
            apply_t(circuit, current_op)
        elif current_op.name == "quantum.tdagger" and current_op.operands:
            apply_tdagger(circuit, current_op)
            # TODO
        # elif current_op.name == "quantum.measure" and current_op.operands:
        #     circuit.measure(current_op.operands[0], c_reg[cbit_index])
        #     cbit_index += 1
        # elif current_op.name == "quantum.measure":
        #     # Create a classical register for the measurement results
        #     creg = ClassicalRegister(output_number, name=current_op.result_names[0])
        #     quantum_registers[current_op.result_names[0]] = creg

        current_op = current_op.next_op

    return circuit


# ============================================================================
# CIRCUIT ANALYSIS AND METRICS
# ============================================================================


def get_quantum_circuit_info(input_args, first_op):
    """
    Extract basic information about the quantum circuit.
    
    Args:
        input_args: List of input arguments from the function operation
        first_op: First operation in the IR sequence
        
    Returns:
        Dictionary containing qubit counts and circuit structure information
    """
    # scroll through the IR tree to count the number of (qu)bits numbers
    input_number = len(input_args)
    output_number = 0
    init_number = 0

    current = first_op
    while current is not None:
        if current.name == "quantum.init":
            # Check if this is initializing a vector (multi-qubit register)
            if hasattr(current, "result_types") and current.result_types:
                result_type = current.result_types[0]
                if hasattr(result_type, "get_shape"):  # Is it a vector?
                    vector_size = result_type.get_shape()[0]
                    init_number += vector_size  # Count all bits in the vector
                    print(f"Found vector register with {vector_size} bits")
                else:
                    init_number += 1  # Regular single qubit
            else:
                init_number += 1  # Default to 1 if we can't determine

        if current.name == "quantum.measure":
            output_number += 1

        current = current.next_op

    qubit_number = input_number + init_number

    return {
        "input_number": input_number,
        "output_number": output_number,
        "init_number": init_number,
        "qubit_number": qubit_number,
    }


def metrics(circuit):
    """
    Calculate various metrics for a quantum circuit.
    
    The returned metrics include:
    - Depth: Overall circuit depth
    - Width: Number of qubits
    - Gate count: Total number of gates
    - T-gate specific metrics
    
    Args:
        circuit: QuantumCircuit object to analyze
        
    Returns:
        Dictionary of circuit metrics
    """
    # Circuit depth
    depth = circuit.depth()

    # Circuit width (number of qubits)
    width = circuit.num_qubits

    # gate count (total number of gates)
    gate_count = circuit.size()

    # get gate counts by type
    gate_counts = circuit.count_ops()

    # count T gates (safely, in case there are none)
    t_gate_count = gate_counts.get("t", 0) + gate_counts.get("tdg", 0)

    # t gate depth
    t_gate_depth = circuit.depth(lambda instr: instr.operation.name in ["t", "tdg"])

    return {
        "Depth": depth,
        "Width": width,
        "Gate Count": gate_count,
        "T Gate Count": t_gate_count,
        "T Gate Depth": t_gate_depth,
        "Gate Distribution": gate_counts,
    }
