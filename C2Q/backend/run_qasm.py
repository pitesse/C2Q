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


def create_circuit(first_op, output_number):
    """
    Create a Qiskit quantum circuit from IR operations with preserved register names
    """
    quantum_registers = {}
    reg_counter = 0
    current_op = first_op

    circuit = QuantumCircuit()

    while(current_op is not None):
        if current_op.name == "quantum.init":
            new_reg = create_quantum_register(current_op)
            quantum_registers[reg_counter] = new_reg
            reg_counter += 1
            circuit.add_register(new_reg)
        elif current_op.name == "quantum.not" and current_op.operands:
            circuit.x(current_op.operands[0])
        elif current_op.name == "quantum.cnot" and len(current_op.operands) >= 2:
            circuit.cx(current_op.operands[0], current_op.operands[1])
        elif current_op.name == "quantum.ccnot" and len(current_op.operands) >= 3:
            circuit.ccx(current_op.operands[0], current_op.operands[1], current_op.operands[2])
        elif current_op.name == "quantum.h" and current_op.operands:
            circuit.h(current_op.operands[0])
        elif current_op.name == "quantum.t" and current_op.operands:
            circuit.t(current_op.operands[0])
        elif current_op.name == "quantum.tdagger" and current_op.operands:
            circuit.tdg(current_op.operands[0])
        elif current_op.name == "quantum.measure" and current_op.operands:
            circuit.measure(current_op.operands[0], c_reg[cbit_index])
            cbit_index += 1
        elif current_op.name == "quantum.measure":
            # Create a classical register for the measurement results
            creg = ClassicalRegister(output_number, name=current_op.result_names[0])
            quantum_registers[current_op.result_names[0]] = creg

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


def main():
    """!
    @brief Main function to process MLIR files and analyze quantum circuits
    @details Parses command line arguments, processes the MLIR file,
             extracts circuit information, and displays metrics and circuit visualization
    """
    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="Calculate metrics for a quantum MLIR file"
    )
    parser.add_argument("mlir_file", type=str, help="Path to the quantum MLIR file")
    args = parser.parse_args()

    mlir_path = Path(args.mlir_file)
    if not mlir_path.exists():
        print(f"Error: File {mlir_path} does not exist.")
        sys.exit(1)

    print(f"Analyzing quantum circuit in: {mlir_path}")

    # parse the MLIR file
    module = parse_mlir_file(mlir_path)

    # extract function operation from module
    funcOp = module.body.block._first_op

    # get input arguments and first operation
    input_args = funcOp.body.block._args
    first_op = funcOp.body.block._first_op

    # get circuit information
    circuit_info = get_quantum_circuit_info(input_args, first_op)

    # create Qiskit circuit
    circuit = create_circuit(first_op, circuit_info["output_number"])

    # calculate metrics
    circuit_metrics = metrics(circuit)

    # output results
    print("\nQuantum Circuit Metrics:")
    for key, value in circuit_metrics.items():
        if key != "Gate Distribution":
            print(f"{key}: {value}")

    print("\nGate Distribution:")
    for gate, count in circuit_metrics["Gate Distribution"].items():
        print(f"  {gate}: {count}")

    print("\nCircuit Information:")
    print(f"Input qubits: {circuit_info['input_number']}")
    print(f"Support qubits: {circuit_info['init_number']}")
    print(f"Total qubits used: {circuit_info['qubit_number']}")
    print(f"Output bits: {circuit_info['output_number']}")

    # optionally draw the circuit
    print("\nCircuit Visualization:")
    print(circuit.draw(output="text"))

    # TODO doesnt work
    figure = circuit.draw("mpl")
    plt.savefig("quantum_circuit.png")
    print("Circuit saved to 'quantum_circuit.png'")
    plt.show()


if __name__ == "__main__":
    main()
