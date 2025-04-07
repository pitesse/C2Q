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
from qiskit_aer import AerSimulator
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGOpNode

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
    with open(file_path, 'r') as f:
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
    """!
    @brief Create a Qiskit quantum circuit from IR operations
    @param first_op First operation in the IR sequence
    @param qubit_number Total number of qubits in the circuit
    @param output_number Number of classical output bits
    @return QuantumCircuit object representing the quantum program
    """
    circuit = QuantumCircuit(qubit_number, output_number)
    current = first_op
    cbit_index = 0

    # initialize counter for unnamed operands
    op_index = 0

    circuit.initialize(1)

    while(current is not None):
        # handle operations without operands safely
        if not hasattr(current, 'operands') or len(current.operands) == 0:
            current = current.next_op
            continue
            
        # get operand indices safely
        try:
            operands_names = []
            for op in current.operands:
                if hasattr(op, '_name') and op._name is not None:
                    operands_names.append(op._name)
                else:
                    # use a generated name for operands without names
                    operands_names.append(f"q_{op_index}")
                    op_index += 1
                    
            # extract indices safely with fallback to positional indices
            indexes = []
            for i, name in enumerate(operands_names):
                try:
                    if name and '_' in name:
                        indexes.append(int(name.split("_")[0][1:]))
                    else:
                        indexes.append(i)  # fallback to position-based index
                except (ValueError, IndexError):
                    indexes.append(i)  # fallback to position-based index
            
            # process gates based on available indices
            if current.name == "quantum.not" and len(indexes) > 0:
                circuit.x(indexes[0])
            elif current.name == "quantum.cnot" and len(indexes) > 1:
                circuit.cx(indexes[0], indexes[1])
            elif current.name == "quantum.ccnot" and len(indexes) > 2:
                circuit.ccx(indexes[0], indexes[1], indexes[2])
            elif current.name == "quantum.h" and len(indexes) > 0:
                circuit.h(indexes[0])
            elif current.name == "quantum.t" and len(indexes) > 0:
                circuit.t(indexes[0])
            elif current.name == "quantum.tdagger" and len(indexes) > 0:
                circuit.tdg(indexes[0])
            elif current.name == "quantum.measure" and len(indexes) > 0:
                circuit.measure(indexes[0], cbit_index)
                cbit_index += 1
        except Exception as e:
            print(f"Warning: Skipping operation {current.name} due to: {e}")
        
        current = current.next_op
    
    return circuit

def get_quantum_circuit_info(input_args, first_op):
    """!
    @brief Extract basic information about the quantum circuit
    @param input_args List of input arguments from the function operation
    @param first_op First operation in the IR sequence
    @return Dictionary containing qubit counts and circuit structure information
    @details Returns a dictionary with keys:
             - input_number: Number of input qubits
             - output_number: Number of measured output bits
             - init_number: Number of initialized qubits
             - qubit_number: Total qubit count
    """
    # scroll through the IR tree to count the number of (qu)bits numbers
    input_number = len(input_args)
    output_number = 0
    init_number = 0

    current = first_op
    while(current is not None):
        if current.name == "quantum.init":
            init_number += 1
        if current.name == "quantum.measure":
            output_number += 1
        current = current.next_op

    qubit_number = input_number + init_number
    
    return {
        "input_number": input_number,
        "output_number": output_number,
        "init_number": init_number,
        "qubit_number": qubit_number
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
    t_gate_count = gate_counts.get('t', 0) + gate_counts.get('tdg', 0)

    # t gate depth 
    t_gate_depth = circuit.depth(lambda instr: instr.operation.name in ['t', 'tdg'])

    return {
        "Depth": depth,
        "Width": width,
        "Gate Count": gate_count,
        "T Gate Count": t_gate_count,
        "T Gate Depth": t_gate_depth,
        "Gate Distribution": gate_counts
    }

def main():
    """!
    @brief Main function to process MLIR files and analyze quantum circuits
    @details Parses command line arguments, processes the MLIR file,
             extracts circuit information, and displays metrics and circuit visualization
    """
    # parse command line arguments
    parser = argparse.ArgumentParser(description='Calculate metrics for a quantum MLIR file')
    parser.add_argument('mlir_file', type=str, help='Path to the quantum MLIR file')
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
    circuit = create_circuit(first_op, circuit_info["qubit_number"], circuit_info["output_number"])
    
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
    print(circuit.draw(output='text'))

if __name__ == "__main__":
    main()