"""
@file __main__.py
@brief Main entry point for the C to Quantum compiler.

This module serves as the entry point for the C to Quantum (CtoQ) tool,
which parses C source code and generates corresponding Quantum IR.
It handles command-line arguments and orchestrates the compilation process.
"""

import argparse
from pathlib import Path
from xdsl.printer import Printer

# from .compiler import context
# from .emulator.toy_accelerator_instruction_functions import (
#     ToyAcceleratorInstructionFunctions,
# )
from .frontend.ir_gen import QuantumIRGen
from .frontend.parser import CParser as CParser

from .backend.run_qasm import get_quantum_circuit_info, create_circuit, metrics

# from .interpreter import Interpreter, ToyFunctions


# set up command-line argument parser
parser = argparse.ArgumentParser(description="Process Toy file")
parser.add_argument("source", type=Path, help="toy source file")
parser.add_argument(
    "--emit",
    dest="emit",
    choices=["ast", "ir"],
    default="ir",
    help="Output format (default: ir)",
)
parser.add_argument("--ir", dest="ir", action="store_true")
parser.add_argument("--print-op-generic", dest="print_generic", action="store_true")


def main(path: Path, emit: str, ir: bool, print_generic: bool):
    """
    @brief Main compilation function that processes input files and generates quantum IR.
    
    This function drives the compilation pipeline by reading the input file,
    parsing it based on its extension, and generating the appropriate IR.
    Currently, it supports C files for conversion to Quantum IR.
    
    @param path: Path object pointing to the source file
    @param emit: Target compilation format (e.g., "ast", "toy", "riscv-asm")
    @param ir: Flag to indicate whether to print the IR
    @param print_generic: Flag to indicate whether to print in generic format
    @return: None
    """
    path = args.source

    with open(path) as f:
            match path.suffix:
                case ".c":
                    # parse the C code
                    parser = CParser(path, f.read())
                    ast = parser.parseModule()
                    
                    if emit == "ast":
                        print(ast.dump())
                        return
    
                    # generate Quantum IR
                    ir_gen = QuantumIRGen()
                    module_op = ir_gen.ir_gen_module(ast)
                    
                    # print the generated IR
                    printer = Printer(print_generic_format=print_generic)
                    printer.print(module_op)
    
                    # find the quantum.func operation in the module
                    funcOp = None
                    for op in module_op.body.block.ops:
                        if op.name == "quantum.func":
                            funcOp = op
                            break
                    
                    if funcOp is None:
                        print("Error: No quantum.func operation found in the module")
                        return
                    
                    # get input arguments and first operation
                    input_args = funcOp.regions[0].blocks[0]._args
                    first_op = funcOp.regions[0].blocks[0]._first_op

                    # print the input arguments
                    print("\nInput Arguments:")
                    for arg in input_args:
                        print(arg)
                    print("\nFirst Operation:")
                    print(first_op)
                    
                    # import and use functions from run_qasm.py directly
                    from .backend.run_qasm import get_quantum_circuit_info, create_circuit, metrics
    
                    # get circuit information
                    circuit_info = get_quantum_circuit_info(input_args, first_op)
                    
                    # create Qiskit circuit
                    try:
                        circuit = create_circuit(first_op, circuit_info["qubit_number"], circuit_info["output_number"])
                        
                        # calculate metrics
                        circuit_metrics = metrics(circuit)
                        
                        # output results
                        print("\nQuantum Circuit Metrics:")
                        for key, value in circuit_metrics.items():
                            if key != "Gate Distribution":
                                print(f"{key}: {value}")
                        
                        print("\nCircuit Information:")
                        print(f"Input qubits: {circuit_info['input_number']}")
                        print(f"Support qubits: {circuit_info['init_number']}")
                        print(f"Total qubits used: {circuit_info['qubit_number']}")
                        print(f"Output bits: {circuit_info['output_number']}")
                        
                        # draw the circuit
                        print("\nCircuit Visualization:")
                        print(circuit.draw(output='text'))
                    except Exception as e:
                        print(f"Error creating or analyzing circuit: {e}")
                        print("This may be due to the structure of the quantum operations in the IR.")

                # case ".mlir":
                #     parser = IRParser(ctx, f.read(), name=f"{path}")
                #     module_op = parser.parse_module()
                case _:
                    print(f"Unknown file format {path}")
                    return

    # asm = emit == "riscv-asm"

    # if asm:
    #     emit = "riscv-lowered"

    # transform(ctx, module_op, target=emit)

    # if asm:
    #     code = riscv_code(module_op)

    #     if ir:
    #         print(code)
    #         return

    #     emulate_riscv(code)
    #     return

    # if ir:
    #     printer = Printer(print_generic_format=print_generic)
    #     printer.print(module_op)
    #     return

    # interpreter = Interpreter(module_op)
    # if emit in ("toy", "toy-opt", "toy-inline", "toy-infer-shapes"):
    #     interpreter.register_implementations(ToyFunctions())
    # if emit in ("affine"):
    #     interpreter.register_implementations(AffineFunctions())
    # if emit in ("affine", "scf"):
    #     interpreter.register_implementations(ArithFunctions())
    #     interpreter.register_implementations(MemRefFunctions())
    #     interpreter.register_implementations(PrintfFunctions())
    #     interpreter.register_implementations(FuncFunctions())
    # if emit == "scf":
    #     interpreter.register_implementations(ScfFunctions())
    #     interpreter.register_implementations(BuiltinFunctions())
    # if emit in (
    #     "riscv",
    #     "riscv-opt",
    #     "riscv-regalloc",
    #     "riscv-regalloc-opt",
    #     "riscv-lowered",
    # ):
    #     interpreter.register_implementations(ToyAcceleratorInstructionFunctions())
    #     interpreter.register_implementations(RiscvFuncFunctions())
    #     interpreter.register_implementations(RiscvDebugFunctions())
    #     interpreter.register_implementations(RiscvLibcFunctions())
    # if emit in ("riscv", "riscv-opt", "riscv-regalloc", "riscv-regalloc-opt"):
    #     interpreter.register_implementations(RiscvScfFunctions())
    # if emit in ("riscv-lowered",):
    #     interpreter.register_implementations(RiscvCfFunctions())

    # interpreter.call_op("main", ())


if __name__ == "__main__":
    """
    @brief Entry point when script is executed directly.
    
    Parses command-line arguments and calls the main function with the provided options.
    """
    args = parser.parse_args()
    main(args.source, args.emit, args.ir, args.print_generic)