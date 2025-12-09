"""!
@file __main__.py
@brief Main entry point for the C to Quantum compiler.
@details This module serves as the entry point for the C to Quantum (C2Q) tool,
which parses C source code and generates corresponding Quantum IR.
It handles command-line arguments, orchestrates the compilation process,
and provides visualization and metrics of the generated quantum circuits.
"""

#------------------------------------------------------------------------------
# IMPORTS
#------------------------------------------------------------------------------
# Standard library imports
import argparse
from io import StringIO
from pathlib import Path

# Third-party imports
from xdsl.printer import Printer

# Local imports - frontend
from .frontend.parser import CParser
from .frontend.ir_gen import QuantumIRGen

# Local imports - middle-end optimizations  
from .middle_end.optimizations import optimize_quantum_circuit

# Local imports - backend
from C2Q.backend.run_qasm import get_quantum_circuit_info, create_circuit, metrics

#------------------------------------------------------------------------------
# HELPER FUNCTIONS
#------------------------------------------------------------------------------
def parse_c_to_ast(path: Path):
    """Parse C file to AST and save to disk"""
    with open(path) as f:
        parser = CParser(path, f.read())
        ast = parser.parseModule()
    
    # Determine output path
    output_path = get_output_path(path, ".ast")
    
    # Save the AST to disk
    with open(output_path, "w") as ast_file:
        ast_file.write(ast.dump())
    
    return ast

def generate_quantum_ir(ast, print_generic: bool, optimize: bool = True):
    """Generate Quantum IR from AST with optional optimizations"""
    ir_gen = QuantumIRGen()
    module_op = ir_gen.ir_gen_module(ast)
    
    # Apply optimization passes if requested
    if optimize:
        print("🔧 Starting Integrated Quantum Circuit Optimization...")
        
        # Apply comprehensive optimization pipeline
        module_op = optimize_quantum_circuit(
            module_op, 
            optimization_level="default",
            analysis_only=False,
            verbose=True
        )
        
        print("✅ Optimization pipeline completed")
    
    # create a StringIO buffer to capture output
    ir_buffer = StringIO()
    printer = Printer(stream=ir_buffer, print_generic_format=print_generic)
    printer.print(module_op)
    
    return module_op, ir_buffer.getvalue()

def get_output_path(input_path: Path, suffix: str) -> Path:
    """
    Determine output path for generated files.
    If input is in tests/inputs/, output to tests/outputs/.
    Otherwise, output to same directory as input.
    """
    input_path_str = str(input_path.resolve())
    
    # Check if input is in tests/inputs/
    if "tests/inputs" in input_path_str or "tests\\inputs" in input_path_str:
        # Replace tests/inputs with tests/outputs
        output_dir = Path(input_path_str.replace("tests/inputs", "tests/outputs").replace("tests\\inputs", "tests\\outputs")).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / (input_path.stem + suffix)
    else:
        # Output to same directory as input
        return input_path.with_suffix(suffix)

def save_ir_to_file(path: Path, mlir: str):
    """Save IR to file"""
    output_path = get_output_path(path, ".mlir")
    with open(output_path, "w") as ir_file:
        ir_file.write(mlir)

def print_banner():
    """Print the C2Q banner"""
    print("\n=========================================\n")
    print(
        "    mmmm    mmmmm      mmmm\n"
    + '  ##""""#  #""""##m   ##""##\n'
    + ' ##"             ##  ##    ##\n'
    + ' ##            m#"   ##    ##\n'
    + ' ##m         m#"     ##    ##\n'
    + '  ##mmmm#  m##mmmmm   ##mm##"\n'
    + '    """"   """"""""    """##\n'
    + '                           ""'
    )
    print("=========================================")

def display_circuit_metrics(circuit_metrics, circuit_info, circuit):
    """Display circuit metrics and visualization"""
    # Output results
    print("\nQuantum Circuit Metrics:")
    for key, value in circuit_metrics.items():
        if key != "Gate Distribution":
            print(f"{key}: {value}")

    print("\nCircuit Information:")
    print(f"Input qubits: {circuit_info['input_number']}")
    print(f"Support qubits: {circuit_info['init_number']}")
    print(f"Total qubits used: {circuit_info['qubit_number']}")
    print(f"Output bits: {circuit_info['output_number']}")

    # Draw the circuit
    print("\nCircuit Visualization:")
    print(circuit.draw(output="text"))
    circuit.draw(filename="circuit.png", output="mpl")

#------------------------------------------------------------------------------
# MAIN FUNCTION
#------------------------------------------------------------------------------
def main(path: Path, emit: str, ir: bool, print_generic: bool, optimize: bool = True):
    """!
    @brief Main compilation function that processes input files and generates quantum IR.
    
    @details This function drives the compilation pipeline by reading the input file,
    parsing it based on its extension, and generating the appropriate IR.
    The pipeline includes:
    1. Parsing C source code into an AST
    2. Generating Quantum IR from the AST
    3. Extracting quantum circuit information
    4. Creating a Qiskit circuit for simulation
    5. Calculating and displaying circuit metrics
    
    Currently, it supports C files for conversion to Quantum IR.

    @param path Path object pointing to the source file
    @param emit Target compilation format (e.g., "ast", "ir")
    @param ir Flag to indicate whether to print the IR
    @param print_generic Flag to indicate whether to print in generic format
    @return The created QuantumCircuit object, or None if not created
    
    @exception FileNotFoundError If the specified input file doesn't exist
    @exception Exception Various exceptions may be raised during circuit creation/analysis
    """
    print_banner()

    # process file based on extension
    match path.suffix:
        case ".c":
            # parse C to AST
            ast = parse_c_to_ast(path)
            
            # if only AST output is requested, print and return
            if emit == "ast":
                print(ast.dump())
                return None

            # generate Quantum IR
            module_op, mlir = generate_quantum_ir(ast, print_generic, optimize)
            
            # save IR to file
            save_ir_to_file(path, mlir)
            
            # print IR if requested
            if ir:
                print("\nGenerated Quantum IR:")
                print(mlir)

            # find the quantum.func operation in the module
            funcOp = None
            for op in module_op.body.block.ops:
                if op.name == "quantum.func":
                    funcOp = op
                    break

            if funcOp is None:
                print("Error: No quantum.func operation found in the module")
                return None

            # extract circuit information
            input_args = funcOp.regions[0].blocks[0]._args
            first_op = funcOp.regions[0].blocks[0]._first_op
            print(f"First operation: {first_op}")
            circuit_info = get_quantum_circuit_info(input_args, first_op)

            # create and analyze quantum circuit
            try:
                circuit = create_circuit(
                    first_op,
                    # circuit_info["qubit_number"],
                    circuit_info["output_number"],
                )
                
                # calculate metrics
                circuit_metrics = metrics(circuit)
                
                # display results
                display_circuit_metrics(circuit_metrics, circuit_info, circuit)
                
                return circuit
                
            except Exception as e:
                print(f"Error creating or analyzing circuit: {e}")
                print("This may be due to the structure of the quantum operations in the IR.")
                return None

        case _:
            print(f"Unknown file format {path}")
            return None

#------------------------------------------------------------------------------
# ENTRY POINT
#------------------------------------------------------------------------------
if __name__ == "__main__":
    """!
    @brief Entry point when script is executed directly.
    @details Parses command-line arguments and calls the main function with the provided options.
    The workflow is:
    1. Parse command-line arguments
    2. Call main() with the parsed arguments
    """
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="C to Quantum Compiler")
    parser.add_argument("source", type=Path, help="C source file to compile")
    parser.add_argument(
        "--emit",
        dest="emit",
        choices=["ast", "ir"],
        default="ir",
        help="Output format (default: ir)",
    )
    parser.add_argument("--ir", dest="ir", action="store_true", 
                       help="Print the generated IR to console")
    parser.add_argument("--print-op-generic", dest="print_generic", action="store_true",
                       help="Print operations in generic format")
    parser.add_argument("--no-optimize", dest="no_optimize", action="store_true",
                       help="Disable quantum circuit optimizations")
    parser.add_argument("--validate", dest="validate", type=int, metavar="EXPECTED",
                       help="Validate circuit output against expected integer result")
    parser.add_argument("--signed", dest="signed", action="store_true",
                       help="Interpret validation result as signed two's complement (for subtraction)")
    parser.add_argument("--result-width", dest="result_width", type=int, default=8, metavar="BITS",
                       help="Number of bits in result register (default: 8, use 16 for multiplication)")
    
    # Parse arguments and run main function
    args = parser.parse_args()
    
    # Force optimizations off when validating (optimizations currently have bugs)
    optimize = not args.no_optimize
    if args.validate is not None:
        optimize = False
        if not args.no_optimize:
            print("⚠️  Optimizations disabled for validation (optimization passes have known bugs)")
    
    # Run compilation to get the circuit
    circuit = main(args.source, args.emit, args.ir, args.print_generic, optimize)
    
    # If validation requested, validate the circuit we just created
    if args.validate is not None and circuit is not None:
        from C2Q.backend.validate import validate_circuit
        
        print("\n" + "="*60)
        print("🔬 VALIDATION")
        print("="*60)
        
        passed = validate_circuit(
            circuit, 
            args.validate, 
            verbose=True,
            signed=args.signed,
            result_width=args.result_width
        )
        
        import sys
        sys.exit(0 if passed else 1)