# Test Outputs

This directory contains generated files from the C2Q compiler.

## File Types

### AST Files (`.ast`)
Abstract Syntax Tree representations of the parsed C code.

### MLIR Files (`.mlir`)
Quantum IR files in MLIR format, containing the quantum circuit representation.

## Auto-Generated

These files are automatically generated when running the compiler. You can safely delete them and regenerate as needed.

## Regenerating Outputs

```bash
# Generate outputs for a specific test
python -m C2Q tests/inputs/test_add_new.c

# This will create:
# - tests/outputs/test_add_new.ast (if --emit ast is used)
# - tests/outputs/test_add_new.mlir
```

## .gitignore

Consider adding this directory to `.gitignore` if you don't want to track generated files:

```
tests/outputs/*.ast
tests/outputs/*.mlir
```
