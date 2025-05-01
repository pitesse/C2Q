"""!
@file run_qasm.py
@brief MLIR Quantum Circuit Metrics Calculator
@details This script analyzes a quantum MLIR file and calculates various metrics
         about the quantum circuit it represents, such as depth, width, gate count,
         and T-gate specific metrics.
@example
python quantum_metrics.py path/to/quantum_ir.mlir
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
from xdsl.dialects.builtin import Builtin

from C2Q.dialects.quantum_dialect import Quantum

######### functions #########


def parse_mlir_file(file_path):
    """!
    @brief Parse an MLIR file into IR objects
    @param file_path Path to the MLIR file
    @return Module object containing the parsed IR
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


######## functions for creating Qiskit circuit from IR operations #####


def create_quantum_register(op):
    """!
    @brief Create a Qiskit QuantumRegister from an IR operation
    @param op IR operation representing a quantum register
    @return Qiskit QuantumRegister object
    """
    result = op.results[0]
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

    print(f"Creating QuantumRegister: {q_reg.name} with size {vec_size}")

    return q_reg


def apply_not(circuit, op):
    """!
    @brief Apply a NOT gate to the circuit
    @param circuit Qiskit QuantumCircuit object
    @param op IR operation representing the NOT gate
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
    """!
    @brief Apply a direct NOT gate to a specific bit in a register
    @param circuit Qiskit QuantumCircuit object
    @param op OnQubitNotOp operation
    """
    if len(op.operands) == 1:
        # Get the vector register
        vector = op.operands[0]

        # Get the index from the operation attributes
        if hasattr(op, "attributes") and "index" in op.attributes:
            bit_index = op.attributes["index"].value.data

            # Get the register name
            if hasattr(vector, "_name") and vector._name:
                reg_name = vector._name
                base_name = reg_name.split("_")[0]

                # Find the register in the circuit
                for qreg in circuit.qregs:
                    if qreg.name == base_name:
                        # Apply the NOT gate directly to the bit
                        circuit.x(qreg[bit_index])
                        return

                print(f"Warning: Register {base_name} not found in circuit")
            else:
                print("Warning: Vector name not found")
        else:
            print("Warning: Bit index attribute not found")
    else:
        print("Warning: Invalid number of operands for OnQubit NOT operation")


def apply_onqubit_cnot(circuit, op):
    """!
    @brief Apply a direct CNOT gate between bits in two registers
    @param circuit Qiskit QuantumCircuit object
    @param op OnQubitCNotOp operation
    """
    if len(op.operands) == 2:
        # Get the control and target vectors
        control_vector = op.operands[0]
        target_vector = op.operands[1]

        # Get the indices from attributes
        if (
            hasattr(op, "attributes")
            and "control_index" in op.attributes
            and "target_index" in op.attributes
        ):

            control_index = op.attributes["control_index"].value.data
            target_index = op.attributes["target_index"].value.data

            # Get register names
            if (
                hasattr(control_vector, "_name")
                and control_vector._name
                and hasattr(target_vector, "_name")
                and target_vector._name
            ):

                control_name = control_vector._name
                control_base = control_name.split("_")[0]

                target_name = target_vector._name
                target_base = target_name.split("_")[0]

                # Find the registers in the circuit
                control_qreg = None
                target_qreg = None

                for qreg in circuit.qregs:
                    if qreg.name == control_base:
                        control_qreg = qreg
                    if qreg.name == target_base:
                        target_qreg = qreg

                if control_qreg and target_qreg:
                    # Apply CNOT directly between the bits
                    circuit.cx(control_qreg[control_index], target_qreg[target_index])
                    return
                else:
                    if not control_qreg:
                        print(f"Warning: Control register {control_base} not found")
                    if not target_qreg:
                        print(f"Warning: Target register {target_base} not found")
            else:
                print("Warning: Register names not found")
        else:
            print("Warning: Index attributes not found")
    else:
        print("Warning: Invalid number of operands for OnQubit CNOT operation")


def apply_cnot(circuit, op):
    """!
    @brief Apply a CNOT gate to the circuit
    @param circuit Qiskit QuantumCircuit object
    @param op IR operation representing the CNOT gate
    """
    if len(op.operands) == 2:
        control_qubit = op.operands[0]
        target_qubit = op.operands[1]

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

        circuit.cx(control_qreg, target_qreg)
    else:
        print("Warning: Invalid number of operands for CNOT operation")


def apply_ccnot(circuit, op):
    """!
    @brief Apply a CCNOT gate to the circuit
    @param circuit Qiskit QuantumCircuit object
    @param op IR operation representing the CCNOT gate
    """
    if len(op.operands) == 3:
        control_qubit1 = op.operands[0]
        control_qubit2 = op.operands[1]
        target_qubit = op.operands[2]

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
        circuit.ccx(c1_qreg, c2_qreg, t_qreg)
    else:
        print("Warning: Invalid number of operands for CCNOT operation")


def apply_onqubit_ccnot(circuit, op):
    """!
    @brief Apply a direct CCNOT gate between bits in three registers
    @param circuit Qiskit QuantumCircuit object
    @param op OnQubitCCnotOp operation
    """
    if len(op.operands) == 3:
        # Get the vectors
        control1_vector = op.operands[0]
        control2_vector = op.operands[1]
        target_vector = op.operands[2]

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

            # Get register names
            if (
                hasattr(control1_vector, "_name")
                and control1_vector._name
                and hasattr(control2_vector, "_name")
                and control2_vector._name
                and hasattr(target_vector, "_name")
                and target_vector._name
            ):

                control1_name = control1_vector._name
                control1_base = control1_name.split("_")[0]

                control2_name = control2_vector._name
                control2_base = control2_name.split("_")[0]

                target_name = target_vector._name
                target_base = target_name.split("_")[0]

                # Find registers in circuit
                control1_qreg = None
                control2_qreg = None
                target_qreg = None

                for qreg in circuit.qregs:
                    if qreg.name == control1_base:
                        control1_qreg = qreg
                    if qreg.name == control2_base:
                        control2_qreg = qreg
                    if qreg.name == target_base:
                        target_qreg = qreg

                if control1_qreg and control2_qreg and target_qreg:
                    # Apply CCNOT directly between bits
                    circuit.ccx(
                        control1_qreg[control1_index],
                        control2_qreg[control2_index],
                        target_qreg[target_index],
                    )
                    return
                else:
                    if not control1_qreg:
                        print(f"Warning: Control1 register {control1_base} not found")
                    if not control2_qreg:
                        print(f"Warning: Control2 register {control2_base} not found")
                    if not target_qreg:
                        print(f"Warning: Target register {target_base} not found")
            else:
                print("Warning: Register names not found")
        else:
            print("Warning: Index attributes not found")
    else:
        print("Warning: Invalid number of operands for OnQubit CCNOT operation")


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


def create_circuit(first_op, output_number):
    """
    Create a Qiskit quantum circuit from IR operations with preserved register names
    """
    quantum_registers = {}
    reg_counter = 0
    current_op = first_op

    circuit = QuantumCircuit()

    while current_op is not None:
        print(f"Processing operation: {current_op.name}")

        if (
            current_op.name == "quantum.init"
            and hasattr(current_op, "results")
            and current_op.results
        ):
            new_reg = create_quantum_register(current_op)
            if new_reg.name not in quantum_registers:
                quantum_registers[reg_counter] = new_reg
                reg_counter += 1
                circuit.add_register(new_reg)
        elif current_op.name == "quantum.not":
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


def get_quantum_circuit_info(input_args, first_op):
    """!
    @brief Extract basic information about the quantum circuit
    @param input_args List of input arguments from the function operation
    @param first_op First operation in the IR sequence
    @return Dictionary containing qubit counts and circuit structure information
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
    """!
    @brief Calculate various metrics for a quantum circuit
    @param circuit QuantumCircuit object to analyze
    @return Dictionary of circuit metrics
    @details The returned metrics include:
             - Depth: Overall circuit depth
             - Width: Number of qubits
             - Gate Count: Total number of gates
             - T Gate Count: Number of T and T-dagger gates
             - T Gate Depth: Depth considering only T and T-dagger gates
             - Gate Distribution: Count of gates by type
    """
    # circuit depth
    depth = circuit.depth()

    # circuit width (number of qubits)
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
