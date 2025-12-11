"""Main entry point for the C to Quantum compiler.

This module serves as the entry point for the C to Quantum (C2Q) tool,
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
    """Parse C file to AST and save to disk.
    
    Args:
        path: Path to the C source file.
        
    Returns:
        The parsed AST module.
    """
    with open(path) as f:
        parser = CParser(path, f.read())
        ast = parser.parseModule()
    
    output_path = get_output_path(path, ".ast")
    
    # save the AST to disk
    with open(output_path, "w") as ast_file:
        ast_file.write(ast.dump())
    
    return ast

def generate_quantum_ir(ast, print_generic: bool, optimize: bool = True, precision: float = 1e-4):
    """Generate Quantum IR from AST with optional optimizations.
    
    Args:
        ast: The parsed AST module.
        print_generic: Whether to print operations in generic format.
        optimize: Whether to apply optimization passes.
        precision: Phase precision threshold for optimizations.
        
    Returns:
        Tuple of (module_op, mlir_string) containing the IR module and its string representation.
    """
    ir_gen = QuantumIRGen()
    module_op = ir_gen.ir_gen_module(ast)
    
    if optimize:
        print("[OPTIMIZE] Starting Integrated Quantum Circuit Optimization...")
        
        module_op = optimize_quantum_circuit(
            module_op, 
            optimization_level="default",
            analysis_only=False,
            verbose=True,
            precision_threshold=precision
        )
        
        print("[PASS] Optimization pipeline completed")
    
    # create a StringIO buffer to capture output
    ir_buffer = StringIO()
    printer = Printer(stream=ir_buffer, print_generic_format=print_generic)
    printer.print(module_op)
    
    return module_op, ir_buffer.getvalue()

def get_output_path(input_path: Path, suffix: str) -> Path:
    """Determine output path for generated files.
    
    If input is in tests/inputs/, output to tests/outputs/.
    Otherwise, output to same directory as input.
    
    Args:
        input_path: Path to the input file.
        suffix: File suffix for the output file.
        
    Returns:
        Path object for the output file.
    """
    input_path_str = str(input_path.resolve())
    
    if "tests/inputs" in input_path_str or "tests\\inputs" in input_path_str:
        output_dir = Path(input_path_str.replace("tests/inputs", "tests/outputs").replace("tests\\inputs", "tests\\outputs")).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / (input_path.stem + suffix)
    else:
        return input_path.with_suffix(suffix)

def save_ir_to_file(path: Path, mlir: str):
    """Save IR to file.
    
    Args:
        path: Path to the input file (used to determine output path).
        mlir: MLIR string to save.
    """
    output_path = get_output_path(path, ".mlir")
    with open(output_path, "w") as ir_file:
        ir_file.write(mlir)

def print_banner():
    """Print the C2Q banner."""
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
    """Display circuit metrics and visualization.
    
    Args:
        circuit_metrics: Dictionary of circuit metrics.
        circuit_info: Dictionary of circuit information.
        circuit: Qiskit QuantumCircuit object.
    """
    print("\nQuantum Circuit Metrics:")
    for key, value in circuit_metrics.items():
        if key != "Gate Distribution":
            print(f"{key}: {value}")

    print("\nCircuit Information:")
    print(f"Input qubits: {circuit_info['input_number']}")
    print(f"Support qubits: {circuit_info['init_number']}")
    print(f"Total qubits used: {circuit_info['qubit_number']}")
    print(f"Output bits: {circuit_info['output_number']}")

    print("\nCircuit Visualization:")
    print(circuit.draw(output="text"))

#------------------------------------------------------------------------------
# MAIN FUNCTION
#------------------------------------------------------------------------------
def main(path: Path, emit: str, ir: bool, print_generic: bool, optimize: bool = True, precision: float = 1e-4):
    """Main compilation function that processes input files and generates quantum IR.
    
    This function drives the compilation pipeline by reading the input file,
    parsing it based on its extension, and generating the appropriate IR.
    The pipeline includes:
    1. Parsing C source code into an AST
    2. Generating Quantum IR from the AST
    3. Extracting quantum circuit information
    4. Creating a Qiskit circuit for simulation
    5. Calculating and displaying circuit metrics
    
    Currently, it supports C files for conversion to Quantum IR.

    Args:
        path: Path object pointing to the source file.
        emit: Target compilation format (e.g., "ast", "ir").
        ir: Flag to indicate whether to print the IR.
        print_generic: Flag to indicate whether to print in generic format.
        optimize: Whether to apply optimization passes.
        precision: Phase precision threshold for optimizations.
    
    Returns:
        The created QuantumCircuit object, or None if not created.
    
    Raises:
        FileNotFoundError: If the specified input file doesn't exist.
        Exception: Various exceptions may be raised during circuit creation/analysis.
    """
    print_banner()

    match path.suffix:
        case ".c":
            ast = parse_c_to_ast(path)
            
            if emit == "ast":
                print(ast.dump())
                return None

            module_op, mlir = generate_quantum_ir(ast, print_generic, optimize, precision)
            
            save_ir_to_file(path, mlir)
            
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

            input_args = funcOp.regions[0].blocks[0]._args
            first_op = funcOp.regions[0].blocks[0]._first_op
            print(f"First operation: {first_op}")
            circuit_info = get_quantum_circuit_info(input_args, first_op)

            try:
                circuit = create_circuit(
                    first_op,
                    circuit_info["output_number"],
                )
                
                circuit_metrics = metrics(circuit)
                
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
    # set up command-line argument parser
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
    parser.add_argument("--force-optimize", dest="force_optimize", action="store_true",
                       help="Force optimizations even during validation (use to test optimized circuits)")
    parser.add_argument("--validate", dest="validate", type=int, metavar="EXPECTED",
                       help="Validate circuit output against expected integer result")
    parser.add_argument("--signed", dest="signed", action="store_true",
                       help="Interpret validation result as signed two's complement (for subtraction)")
    parser.add_argument("--result-width", dest="result_width", type=int, default=8, metavar="BITS",
                       help="Number of bits in result register (default: 8, use 16 for multiplication)")
    parser.add_argument("--precision", dest="precision", type=float, default=1e-4,
                       help="Phase precision threshold for optimization (default: 1e-4)")
    
    args = parser.parse_args()
    
    # determine optimization setting
    optimize = not args.no_optimize
    if args.validate is not None and not args.force_optimize:
        optimize = False
        if not args.no_optimize:
            print("[WARN] Optimizations disabled for validation (use --force-optimize to test optimized circuits)")
    elif args.validate is not None and args.force_optimize:
        optimize = True
        print("[INFO] Validating OPTIMIZED circuit (--force-optimize enabled)")
    
    circuit = main(args.source, args.emit, args.ir, args.print_generic, optimize, args.precision)
    
    # validate the circuit if requested
    if args.validate is not None and circuit is not None:
        from C2Q.backend.validate import validate_circuit
        
        print("\n" + "="*60)
        print("VALIDATION")
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