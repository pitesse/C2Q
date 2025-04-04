from __future__ import annotations
import re
import sys
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

# Updated Qiskit imports with fallbacks
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram

# Try to import Aer and execute from various locations
try:
    # First try qiskit_aer (newest)
    from qiskit_aer import Aer, QasmSimulator
    AerSimulator = Aer.get_backend('qasm_simulator')
except ImportError:
    try:
        # Fall back to older structure
        from qiskit import Aer
        AerSimulator = Aer.get_backend('qasm_simulator')
    except ImportError:
        print("Warning: Could not import Aer. Install with: pip install qiskit-aer")
        AerSimulator = None

# Try to import execute from various locations
try:
    from qiskit import execute
except ImportError:
    try:
        from qiskit.execute_function import execute
    except ImportError:
        # Fallback - define our own execute function if needed
        def execute(circuits, backend, **kwargs):
            return backend.run(circuits, **kwargs)

class QiskitTranslator:
    """
    Translates xDSL Quantum IR to Qiskit quantum circuits
    """
    def __init__(self, verbose=False):
        self.verbose = verbose
        # Maps IR result identifiers to qubit indices
        self.result_to_qubit = {}
        # Track the next available qubit/cbit
        self.next_qubit = 0
        self.next_cbit = 0
        # Maps result IDs to the operations that produced them
        self.operations = {}
        # Store function operations
        self.functions = {}
        
    def translate_ir(self, ir_text: str) -> dict[str, QuantumCircuit]:
        """
        Parse quantum IR and convert to Qiskit circuits
        Returns a dictionary of function names to circuits
        """
        # Parse the IR operations
        self.parse_ir_operations(ir_text)
        
        # Create circuits for each function
        circuits = {}
        for func_name, func_info in self.functions.items():
            circuits[func_name] = self.create_circuit(func_info['region'])
        
        return circuits
        
    def parse_ir_operations(self, ir_text: str):
        """Parse quantum IR operations from text output"""
        # Track current function being parsed
        current_function = None
        current_region = None
        region_level = 0
        
        # Regex patterns for parsing
        func_pattern = r'"quantum\.func"\(\) \(\{(.+?)\}\) \{func_name = "([^"]+)"\}'
        op_pattern = r'%(\d+) = "quantum\.([^"]+)"\(([^)]*)\)(?: \{([^}]+)\})? : \([^)]*\) -> ([a-z0-9]+)'
        
        # Split by lines and process each line
        lines = ir_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for function declarations
            if "quantum.func" in line:
                match = re.search(r'\{func_name = "([^"]+)"\}', line)
                if match:
                    func_name = match.group(1)
                    current_function = func_name
                    current_region = []
                    self.functions[func_name] = {
                        'region': current_region
                    }
                    if self.verbose:
                        print(f"Found function: {func_name}")
                    region_level += 1
                    continue
            
            # Check for region end
            if line.strip() == "}) {func_name" or line.strip() == "})":
                region_level -= 1
                if region_level == 0:
                    current_function = None
                    current_region = None
                continue
                
            # Parse quantum operations
            match = re.search(op_pattern, line)
            if match and current_region is not None:
                result_id, op_name, operands_str, attributes_str, result_type = match.groups()
                
                # Parse operands
                operands = []
                if operands_str:
                    operands = [op.strip() for op in operands_str.split(',')]
                
                # Parse attributes
                attributes = {}
                if attributes_str:
                    # Match attribute name and value pairs
                    attr_matches = re.finditer(r'([a-zA-Z0-9_]+) = ([^,]+)(?:,|$)', attributes_str)
                    for attr_match in attr_matches:
                        key, value = attr_match.groups()
                        # Handle different attribute types
                        if value == "true":
                            attributes[key] = True
                        elif value == "false":
                            attributes[key] = False
                        elif value.isdigit():
                            attributes[key] = int(value)
                        else:
                            attributes[key] = value
                
                # Store the operation
                op = {
                    'id': f"%{result_id}",
                    'name': op_name,
                    'operands': operands,
                    'attributes': attributes,
                    'result_type': result_type
                }
                
                self.operations[f"%{result_id}"] = op
                current_region.append(op)
                
                if self.verbose:
                    print(f"Parsed op: {op_name} with id {result_id}, operands {operands}")
    
    def create_circuit(self, operations: list) -> QuantumCircuit:
        """Create a Qiskit circuit from parsed operations"""
        # Reset qubit mapping for this circuit
        self.result_to_qubit = {}
        self.next_qubit = 0
        self.next_cbit = 0
        
        # First pass: count required qubits and classical bits
        for op in operations:
            if op['name'] == 'measure':
                self.next_cbit += 1
        
        # Create circuit - add extra qubits to account for ancillas
        n_qubits = max(len(operations), self.next_qubit + 5)
        circuit = QuantumCircuit(n_qubits, self.next_cbit)
        
        # Second pass: add operations to circuit
        for op in operations:
            self.add_operation_to_circuit(circuit, op)
            
        # Final cleanup - remove unused qubits and bits
        # Get the highest qubit and classical bit indices used
        max_qubit = -1
        for qubit_idx in self.result_to_qubit.values():
            if qubit_idx > max_qubit:
                max_qubit = qubit_idx
                
        # Create a new circuit with the exact number of qubits and bits needed
        if max_qubit >= 0:
            optimized_circuit = QuantumCircuit(max_qubit + 1, self.next_cbit)
            # Copy instructions from original circuit
            for instr in circuit.data:
                # Only include instructions that operate on qubits within our range
                if all(q.index <= max_qubit for q in instr.qubits):
                    optimized_circuit.append(instr.operation, [q.index for q in instr.qubits], 
                                            [c.index for c in instr.clbits])
            return optimized_circuit
            
        return circuit
    
    def get_qubit_index(self, result_id: str) -> int:
        """Get or assign a qubit index for a result ID"""
        if result_id not in self.result_to_qubit:
            self.result_to_qubit[result_id] = self.next_qubit
            self.next_qubit += 1
        return self.result_to_qubit[result_id]
    
    def add_operation_to_circuit(self, circuit: QuantumCircuit, op: dict):
        """Add a quantum operation to the circuit"""
        # Assign a qubit for the result
        result_id = op['id']
        result_qubit = self.get_qubit_index(result_id)
        
        # Map operand IDs to qubit indices
        operand_qubits = []
        for operand in op['operands']:
            operand_qubits.append(self.get_qubit_index(operand))
        
        # Apply the appropriate gate based on operation name
        if op['name'] == 'init':
            # Initialize qubit - handled by default state |0⟩
            pass
            
        elif op['name'] == 'not':
            # X gate (NOT)
            if len(operand_qubits) > 0:
                circuit.x(operand_qubits[0])
                self.result_to_qubit[result_id] = operand_qubits[0]
            else:
                # Apply to result qubit directly if no operands
                circuit.x(result_qubit)
        
        elif op['name'] == 'h':
            # Hadamard gate
            if len(operand_qubits) > 0:
                circuit.h(operand_qubits[0])
                self.result_to_qubit[result_id] = operand_qubits[0]
            else:
                circuit.h(result_qubit)
        
        elif op['name'] == 'cnot':
            # Controlled-NOT gate
            if len(operand_qubits) >= 2:
                circuit.cx(operand_qubits[0], operand_qubits[1])
                self.result_to_qubit[result_id] = operand_qubits[1]
            else:
                if self.verbose:
                    print(f"Warning: CNOT needs 2 operands, got {len(operand_qubits)}")
        
        elif op['name'] == 'ccnot':
            # Toffoli gate (CCNOT)
            if len(operand_qubits) >= 3:
                circuit.ccx(operand_qubits[0], operand_qubits[1], operand_qubits[2])
                self.result_to_qubit[result_id] = operand_qubits[2]
            else:
                if self.verbose:
                    print(f"Warning: CCNOT needs 3 operands, got {len(operand_qubits)}")
        
        elif op['name'] == 't':
            # T gate
            if len(operand_qubits) > 0:
                circuit.t(operand_qubits[0])
                self.result_to_qubit[result_id] = operand_qubits[0]
            else:
                circuit.t(result_qubit)
        
        elif op['name'] == 'tdagger':
            # T dagger gate
            if len(operand_qubits) > 0:
                circuit.tdg(operand_qubits[0])
                self.result_to_qubit[result_id] = operand_qubits[0]
            else:
                circuit.tdg(result_qubit)
                
        elif op['name'] == 'measure':
            # Measurement
            if len(operand_qubits) > 0:
                cbit_idx = self.next_cbit
                circuit.measure(operand_qubits[0], cbit_idx)
                self.next_cbit += 1
            else:
                if self.verbose:
                    print("Warning: Measure operation without qubit operand")
                
        else:
            if self.verbose:
                print(f"Unsupported operation: {op['name']}")


def run_simulation(circuit: QuantumCircuit, shots: int = 1024):
    """Run the circuit on a simulator and return results"""
    if AerSimulator is None:
        raise ImportError("No simulator available. Please install qiskit-aer with: pip install qiskit-aer")
    
    # First optimize the circuit
    transpiled_circuit = transpile(circuit, AerSimulator, optimization_level=1)
    
    try:
        # Try using execute function if available
        job = execute(transpiled_circuit, AerSimulator, shots=shots)
    except (NameError, AttributeError):
        # Fall back to direct run method
        job = AerSimulator.run(transpiled_circuit, shots=shots)
        
    result = job.result()
    return result

def visualize_circuit(circuit: QuantumCircuit, filename=None):
    """Visualize the circuit and optionally save to file"""
    circuit_fig = circuit.draw(output='mpl')
    if filename:
        circuit_fig.savefig(filename)
    return circuit_fig

def visualize_results(counts, filename=None):
    """Visualize the results histogram and optionally save to file"""
    plt.figure(figsize=(10, 6))
    plot_hist = plot_histogram(counts)
    if filename:
        plot_hist.savefig(filename)
    return plot_hist

def main():
    parser = argparse.ArgumentParser(description="Run Qiskit simulations from Quantum IR")
    parser.add_argument("ir_file", type=str, help="Path to file containing Quantum IR")
    parser.add_argument("--shots", type=int, default=1024, help="Number of shots for simulation")
    parser.add_argument("--function", type=str, default=None, help="Function name to run (defaults to all)")
    parser.add_argument("--save-circuit", type=str, default=None, help="Save circuit diagram to file")
    parser.add_argument("--save-results", type=str, default=None, help="Save results histogram to file")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    
    args = parser.parse_args()
    
    # Read IR from file
    with open(args.ir_file, 'r') as f:
        ir_text = f.read()
    
    # Translate IR to Qiskit circuits
    translator = QiskitTranslator(verbose=args.verbose)
    circuits = translator.translate_ir(ir_text)
    
    if not circuits:
        print("No quantum functions found in IR!")
        return
    
    # Run specific function or all functions
    if args.function:
        if args.function in circuits:
            circuit = circuits[args.function]
            print(f"\nRunning circuit for function '{args.function}':")
            print(circuit)
            
            # Save circuit diagram if requested
            if args.save_circuit:
                filename = f"{args.save_circuit}_{args.function}.png" if args.save_circuit.endswith('.png') else f"{args.save_circuit}_{args.function}.png"
                visualize_circuit(circuit, filename)
                print(f"Circuit diagram saved to {filename}")
            
            # Run simulation
            result = run_simulation(circuit, args.shots)
            counts = result.get_counts(circuit)
            
            print("\nSimulation Results:")
            for outcome, count in counts.items():
                print(f"  {outcome}: {count} ({count/args.shots:.2%})")
            
            # Save results if requested
            if args.save_results:
                filename = f"{args.save_results}_{args.function}.png" if args.save_results.endswith('.png') else f"{args.save_results}_{args.function}.png"
                visualize_results(counts, filename)
                print(f"Results histogram saved to {filename}")
        else:
            print(f"Function '{args.function}' not found in IR!")
            print(f"Available functions: {', '.join(circuits.keys())}")
    else:
        # Run all functions
        for func_name, circuit in circuits.items():
            print(f"\nRunning circuit for function '{func_name}':")
            print(circuit)
            
            # Save circuit diagram if requested
            if args.save_circuit:
                filename = f"{args.save_circuit}_{func_name}.png" if args.save_circuit.endswith('.png') else f"{args.save_circuit}_{func_name}.png"
                visualize_circuit(circuit, filename)
                print(f"Circuit diagram saved to {filename}")
            
            # Run simulation
            result = run_simulation(circuit, args.shots)
            counts = result.get_counts(circuit)
            
            print("\nSimulation Results:")
            for outcome, count in counts.items():
                print(f"  {outcome}: {count} ({count/args.shots:.2%})")
            
            # Save results if requested
            if args.save_results:
                filename = f"{args.save_results}_{func_name}.png" if args.save_results.endswith('.png') else f"{args.save_results}_{func_name}.png"
                visualize_results(counts, filename)
                print(f"Results histogram saved to {filename}")

if __name__ == "__main__":
    main()