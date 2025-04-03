from __future__ import annotations

from typing import TypeVar

from xdsl.dialects.builtin import IntegerType, StringAttr, VectorType, IntegerAttr, ModuleOp
from xdsl.dialects.builtin import Builtin  # Import the Builtin dialect
from xdsl.ir import Dialect, OpResult, SSAValue, Region, Attribute, Operation
from xdsl.context import Context
from xdsl.irdl import IRDLOperation, Operand, attr_def, irdl_op_definition, operand_def, result_def, region_def
from xdsl.parser import Parser
from xdsl.printer import Printer
# from xdsl.dialects.mlir_dialect import LLVM
from dialect.quantum_dialect import Quantum, CNotOp, CCNotOp, InitOp, MeasureOp, TGateOp, TDaggerGateOp, HadamardOp


def translate_mlir_to_quantum(mlir_file: str):
    """
    Translate the given MLIR file into quantum operations using the defined dialect.
    """

    # Parse the MLIR content into xDSL's IR
    ctx = Context()
    ctx.register_dialect("quantum", lambda: Quantum)  # Register the Quantum dialect

    # Read the MLIR file content
    with open(mlir_file, "r") as f:
        mlir_content = f.read()

    # Parse the content
    parser = Parser(ctx, mlir_content)
    module = parser.parse_module()

    return module


if __name__ == "__main__":
    # Example usage
    mlir_file = "add.mlir"
    transformed_module = translate_mlir_to_quantum(mlir_file)

    # Save the quantum operations to a file (if needed)
    with open("output.qasm", "w") as f:
        f.write("// Quantum operations translated from MLIR\n")
        for op in transformed_module:
            f.write(str(op) + "\n")

    print("Translation complete. Quantum operations saved to output.qasm.")