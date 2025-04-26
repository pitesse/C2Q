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
        base_name = reg_name.split('_')[0]
    else:
        print("Warning: Register name not found")

    # Get vector size 
    vec_size = 1
    if hasattr(op, "result_types") and hasattr(
        op.result_types[0], "get_shape"
    ):
        vec_size = op.result_types[0].get_shape()[0]

    q_reg = QuantumRegister(vec_size, name=base_name)

    return q_reg


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
        if current_op.name == "quantum.init" and hasattr(current_op, "results") and current_op.results:
            new_reg = create_quantum_register(current_op)
            if(new_reg.name not in quantum_registers):
                quantum_registers[reg_counter] = new_reg
                reg_counter += 1
                circuit.add_register(new_reg)

           
        # elif current_op.name == "quantum.not" and current_op.operands:
        #     circuit.x(current_op.operands[0])
        # elif current_op.name == "quantum.cnot" and len(current_op.operands) >= 2:
        #     circuit.cx(current_op.operands[0], current_op.operands[1])
        # elif current_op.name == "quantum.ccnot" and len(current_op.operands) >= 3:
        #     circuit.ccx(current_op.operands[0], current_op.operands[1], current_op.operands[2])
        # elif current_op.name == "quantum.h" and current_op.operands:
        #     circuit.h(current_op.operands[0])
        # elif current_op.name == "quantum.t" and current_op.operands:
        #     circuit.t(current_op.operands[0])
        # elif current_op.name == "quantum.tdagger" and current_op.operands:
        #     circuit.tdg(current_op.operands[0])
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
