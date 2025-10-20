#!/usr/bin/env python3
"""
Generate figures for the C2Q paper from test cases.

This script runs the C2Q compiler on various test cases and exports
the resulting quantum circuits as PDF figures for use in the paper.
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qiskit.visualization import circuit_drawer
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

def generate_circuit_figure(c_file: Path, output_name: str):
    """
    Generate a circuit diagram from a C test file.
    
    Args:
        c_file: Path to the C source file
        output_name: Name for the output PDF (without extension)
    """
    print(f"Processing {c_file.name}...")
    
    try:
        # Import after ensuring path is set
        from C2Q.frontend.parser import CParser
        from C2Q.frontend.ir_gen import QuantumIRGen
        from C2Q.backend.run_qasm import get_quantum_circuit_info, create_circuit
        
        # Parse C file
        with open(c_file, 'r') as f:
            c_code = f.read()
        
        parser = CParser()
        ast = parser.parse_program(c_code)
        
        # Generate IR
        ir_gen = QuantumIRGen()
        module = ir_gen.gen_module(ast)
        
        # Get function operation
        funcOp = module.body.block._first_op
        input_args = funcOp.body.block._args
        first_op = funcOp.body.block._first_op
        
        # Get circuit info and create circuit
        info = get_quantum_circuit_info(input_args, first_op)
        circuit = create_circuit(first_op, info["output_number"])
        
        # Create figure
        fig = circuit_drawer(circuit, output='mpl', style='iqp', fold=-1)
        
        # Save figure
        output_path = Path(__file__).parent / 'figures' / f'{output_name}.pdf'
        plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=300)
        plt.close()
        
        print(f"  ✓ Saved to {output_path}")
        
        return circuit, info
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, None

def generate_metrics_chart(test_results: dict):
    """
    Generate a bar chart comparing metrics across test cases.
    
    Args:
        test_results: Dictionary mapping test names to metrics
    """
    print("Generating metrics comparison chart...")
    
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    
    test_names = list(test_results.keys())
    gate_counts = [r['gates'] for r in test_results.values()]
    depths = [r['depth'] for r in test_results.values()]
    qubits = [r['qubits'] for r in test_results.values()]
    
    # Gate count
    axes[0].bar(test_names, gate_counts, color='steelblue')
    axes[0].set_ylabel('Gate Count')
    axes[0].set_title('Total Gates')
    axes[0].tick_params(axis='x', rotation=45)
    
    # Circuit depth
    axes[1].bar(test_names, depths, color='coral')
    axes[1].set_ylabel('Circuit Depth')
    axes[1].set_title('Circuit Depth')
    axes[1].tick_params(axis='x', rotation=45)
    
    # Qubit usage
    axes[2].bar(test_names, qubits, color='mediumseagreen')
    axes[2].set_ylabel('Number of Qubits')
    axes[2].set_title('Qubit Usage')
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    output_path = Path(__file__).parent / 'figures' / 'metrics_comparison.pdf'
    plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"  ✓ Saved to {output_path}")

def main():
    """Main function to generate all figures."""
    print("C2Q Paper Figure Generator")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Test files to process
    test_files = [
        ('test_add_new.c', 'circuit_addition'),
        ('test_sub_new.c', 'circuit_subtraction'),
        ('test_mul_new.c', 'circuit_multiplication'),
    ]
    
    test_results = {}
    
    for c_file_name, output_name in test_files:
        c_file = project_root / c_file_name
        
        if not c_file.exists():
            print(f"Warning: {c_file_name} not found, skipping...")
            continue
        
        circuit, info = generate_circuit_figure(c_file, output_name)
        
        if circuit and info:
            from qiskit.converters import circuit_to_dag
            dag = circuit_to_dag(circuit)
            
            test_results[output_name] = {
                'gates': len(circuit),
                'depth': circuit.depth(),
                'qubits': circuit.num_qubits
            }
    
    # Generate metrics chart if we have results
    if test_results:
        generate_metrics_chart(test_results)
    
    print("\n" + "=" * 50)
    print("Figure generation complete!")
    print(f"Figures saved to: {Path(__file__).parent / 'figures'}")

if __name__ == '__main__':
    main()
