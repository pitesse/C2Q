"""
@file __main__.py
@brief Main entry point for the C to Quantum compiler.

This module serves as the entry point for the C to Quantum (CtoQ) tool,
which parses C source code and generates corresponding Quantum IR.
It handles command-line arguments and orchestrates the compilation process.
"""

import argparse
from pathlib import Path

from xdsl.dialects.riscv import riscv_code
from xdsl.interpreters.affine import AffineFunctions
from xdsl.interpreters.arith import ArithFunctions
from xdsl.interpreters.builtin import BuiltinFunctions
from xdsl.interpreters.func import FuncFunctions
from xdsl.interpreters.memref import MemRefFunctions
from xdsl.interpreters.printf import PrintfFunctions
from xdsl.interpreters.riscv_cf import RiscvCfFunctions
from xdsl.interpreters.riscv_debug import RiscvDebugFunctions
from xdsl.interpreters.riscv_func import RiscvFuncFunctions
from xdsl.interpreters.riscv_libc import RiscvLibcFunctions
from xdsl.interpreters.riscv_scf import RiscvScfFunctions
from xdsl.interpreters.scf import ScfFunctions
from xdsl.parser import Parser as IRParser
from xdsl.printer import Printer

# from .compiler import context
# from .emulator.toy_accelerator_instruction_functions import (
#     ToyAcceleratorInstructionFunctions,
# )
from .frontend.ir_gen import QuantumIRGen
from .frontend.parser import CParser as CParser

# from .interpreter import Interpreter, ToyFunctions

# Set up command-line argument parser
parser = argparse.ArgumentParser(description="Process Toy file")
parser.add_argument("source", type=Path, help="toy source file")
parser.add_argument(
    "--emit",
    dest="emit",
    choices=[
        "ast",
        "toy",
        "toy-opt",
        "toy-inline",
        "toy-infer-shapes",
        "affine",
        "scf",
        "riscv",
        "riscv-opt",
        "riscv-regalloc",
        "riscv-regalloc-opt",
        "riscv-lowered",
        "riscv-asm",
    ],
    default="riscv-asm",
    help="Compilation target (default: riscv-asm)",
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
                # Parse the C code
                parser = CParser(path, f.read())
                ast = parser.parseModule()
                
                if emit == "ast":
                    print(ast.dump())
                    return

                # Generate Quantum IR
                ir_gen = QuantumIRGen()
                module_op = ir_gen.ir_gen_module(ast)
                
                # Print the generated IR
                printer = Printer(print_generic_format=print_generic)
                printer.print(module_op)

            #     ir_gen = IRGen()
            #     module_op = ir_gen.ir_gen_module(ast)
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