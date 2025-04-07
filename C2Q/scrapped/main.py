from __future__ import annotations
import subprocess
import sys
from pathlib import Path
import shutil
import argparse
from middle_end.transformations.mlir_to_quantum import Transformator

def find_mlir_translate():
    # Check possible names in order of preference
    possible_names = ["mlir-translate", "mlir-translate-15"]
    for name in possible_names:
        if shutil.which(name):
            return name
    raise RuntimeError("mlir-translate not found! Install MLIR first (read README.md)")

def generate_llvm_ir(input_c: str):
    subprocess.run([
        "clang", "-S", "-emit-llvm",
        input_c, "temp.ll"
    ], check=True)
    
    temp_ll = Path("temp.ll")
    if not temp_ll.exists():
        raise RuntimeError("Failed to generate temp.ll")
    print(f"LLVM IR saved to: {temp_ll.resolve()}")
    
def generate_mlir(temp_ll: Path):
    mlir_translate = find_mlir_translate()
    subprocess.run([
        mlir_translate, "--import-llvm", "temp.ll",
        "-o", "temp.mlir"
    ], check=True)

    # Ensure temp.mlir is saved in the current directory
    temp_mlir = Path("temp.mlir")
    if not temp_mlir.exists():
        raise RuntimeError("Failed to generate temp.mlir")
    print(f"MLIR saved to: {temp_mlir.resolve()}")

def c_to_qasm(input_c: str):
    
    generate_llvm_ir(input_c)

    generate_mlir(Path("temp.ll"))
    

    # 3. Translate MLIR to quantum operations
    transformed_module=Transformator.translate_mlir_to_quantum("temp.mlir")
    print(transformed_module)


    # 
    # with open("temp.mlir") as f:
    #     mlir_content = f.read()
    
    # # Parse MLIR into xDSL's IR
    # ctx = MLContext()
    # ctx.register_dialect(LLVMDialect)  # Register required dialects
    # ir_module = mlir_parser.parse_mlir_module(ctx, mlir_content)

    # temp_ll.unlink(missing_ok=True)
    # temp_mlir.unlink(missing_ok=True)
    
    # Your custom lowering passes here
    # ...
    
    # Generate QASM
    # with open(output_qasm, "w") as f:
    #     f.write(generate_qasm(ir_module))

def main():
    parser = argparse.ArgumentParser(description="Convert C code to QASM.")
    parser.add_argument("input_c", help="Path to the input C file")
    # parser.add_argument("output_qasm", help="Path to the output QASM file")
    args = parser.parse_args()

    input_c = args.input_c
    # output_qasm = args.output_qasm

    if not Path(input_c).exists():
        print(f"Error: Input file '{input_c}' does not exist.")
        sys.exit(1)

    c_to_qasm(input_c)

if __name__ == "__main__":
    main()

