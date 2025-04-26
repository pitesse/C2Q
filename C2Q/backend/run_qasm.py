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


def create_circuit(first_op, qubit_number, output_number):
    """
    Create a Qiskit quantum circuit from IR operations with preserved register names
    """
    # Track all register versions (q0_0, q0_1, q0_3, etc.)
    register_versions = {}
    quantum_regs = {}
    
    # Track operations to apply later
    deferred_gates = []
    
    # First pass - identify all registers and their extracted bits
    current = first_op
    while current is not None:
        if current.name == "quantum.init" and hasattr(current, "results") and current.results:
            result = current.results[0]
            if hasattr(result, "_name") and result._name:
                reg_name = result._name
                # Extract the base register name (e.g., q0 from q0_1)
                base_name = reg_name.split('_')[0]
                
                # Get vector size if applicable
                vec_size = 1
                if hasattr(current, "result_types") and hasattr(current.result_types[0], "get_shape"):
                    vec_size = current.result_types[0].get_shape()[0]
                
                # Create or get the register
                if base_name not in quantum_regs:
                    q_reg = QuantumRegister(vec_size, name=base_name)
                    quantum_regs[base_name] = q_reg
                
                # Track this version of the register
                register_versions[reg_name] = base_name
        
        # Track bit extraction operations
        elif current.name == "quantum.extract_bit" and len(current.operands) > 0:
            # This extracts a bit from a vector
            if hasattr(current, "results") and current.results:
                result_name = current.results[0]._name if hasattr(current.results[0], "_name") else None
                if result_name and "[" in result_name and "]" in result_name:
                    # This names a bit like q0_1[2]
                    vector_name = current.operands[0]._name if hasattr(current.operands[0], "_name") else None
                    if vector_name and vector_name in register_versions:
                        bit_idx = current.attributes["index"].value.data
                        # Track that this named bit refers to this register/index
                        register_versions[result_name] = (register_versions[vector_name], bit_idx)
        
        # Track operations on bits
        elif (current.name.startswith("quantum.") and 
              current.name not in ["quantum.comment", "quantum.extract_bit", "quantum.insert_bit", "quantum.init"]):
            # This is a quantum gate operation - track it for later application
            deferred_gates.append(current)
            
        current = current.next_op
    
    # Create classical register for outputs
    c_reg = ClassicalRegister(output_number, "c")
    
    # Create circuit with all registers
    circuit = QuantumCircuit(*quantum_regs.values(), c_reg)
    
    # Apply the deferred gates
    cbit_index = 0
    for gate_op in deferred_gates:
        try:
            # Process operands - translate them to actual qubits
            operands = []
            for op in gate_op.operands:
                if hasattr(op, "_name") and op._name:
                    name = op._name
                    # Handle bit reference
                    if name in register_versions:
                        # Is this a direct bit reference from extraction?
                        if isinstance(register_versions[name], tuple):
                            base_name, bit_idx = register_versions[name]
                            operands.append(quantum_regs[base_name][bit_idx])
                        else:
                            # It's a register reference
                            base_name = register_versions[name]
                            operands.append(quantum_regs[base_name])
            
            # Apply appropriate gate based on operation type
            if gate_op.name == "quantum.not" and operands:
                circuit.x(operands[0])
            elif gate_op.name == "quantum.cnot" and len(operands) >= 2:
                circuit.cx(operands[0], operands[1])
            elif gate_op.name == "quantum.ccnot" and len(operands) >= 3:
                circuit.ccx(operands[0], operands[1], operands[2])
            elif gate_op.name == "quantum.h" and operands:
                circuit.h(operands[0])
            elif gate_op.name == "quantum.t" and operands:
                circuit.t(operands[0])
            elif gate_op.name == "quantum.tdagger" and operands:
                circuit.tdg(operands[0])
            elif gate_op.name == "quantum.measure" and operands:
                circuit.measure(operands[0], c_reg[cbit_index])
                cbit_index += 1
                
        except Exception as e:
            print(f"Warning: Skipping operation {gate_op.name} due to: {e}")
    
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
    circuit = create_circuit(
        first_op, circuit_info["qubit_number"], circuit_info["output_number"]
    )

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

    #TODO doesnt work
    figure = circuit.draw("mpl")
    plt.savefig("quantum_circuit.png")
    print("Circuit saved to 'quantum_circuit.png'")
    plt.show()  


if __name__ == "__main__":
    main()
