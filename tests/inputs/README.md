# Test Inputs

This directory contains C source files used for testing the C2Q compiler.

## Test Categories

### Basic Arithmetic Tests
- `test_add_new.c` - Addition with new variable (a + b → c)
- `test_add_overwrite.c` - Addition overwriting existing variable
- `test_sub_new.c` - Subtraction with new variable
- `test_sub_overwrite.c` - Subtraction overwriting existing variable
- `test_mul_new.c` - Multiplication with new variable
- `test_mul_overwrite.c` - Multiplication overwriting existing variable

### Specific Algorithm Tests
- `test_draper.c` - Draper QFT arithmetic algorithm test

### Edge Cases
- `test_debug_add.c` - Addition with zero operand (3 + 0) for testing optimization

### Assignment Tests
- `test_assignment.c` - Variable assignment and overwrite patterns

### Multiplication Tests
- `test_mult_2x3.c` - Simple multiplication: 2 × 3
- `test_mult_3x3.c` - Simple multiplication: 3 × 3

### Register Management
- `test_register_management.c` - Register allocation and management

## Running Tests

```bash
# Compile a test file
python -m C2Q tests/inputs/test_add_new.c

# Generate AST only
python -m C2Q tests/inputs/test_add_new.c --emit ast

# Run optimization analysis
python demos/optimization_demo.py tests/inputs/test_add_new.c
```

## Generated Files

When you run the compiler, generated `.ast` and `.mlir` files will be placed in `tests/outputs/`.
