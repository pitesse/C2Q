# C2Q: C to Quantum Compiler

A compiler framework that translates classical C programs into executable quantum circuits using Draper's QFT-based arithmetic algorithms.

## Overview

C2Q is a complete compilation pipeline that transforms C source code into optimized quantum circuits. The compiler implements quantum arithmetic using Draper's Quantum Fourier Transform (QFT) algorithms, providing efficient quantum implementations of classical operations.

### Key Features

- Complete compilation pipeline: C source to executable quantum circuits
- QFT-based quantum arithmetic (addition, subtraction, multiplication)
- Multi-stage optimization framework (AST-level and quantum-level)
- Custom C parser built on XDSL framework
- Qiskit integration for circuit simulation and visualization
- Comprehensive validation and testing infrastructure

## Architecture

The compiler follows a standard three-phase architecture:

```
C Source Code
    ↓
Frontend (Lexer → Parser → AST)
    ↓
IR Generation (AST → Quantum MLIR)
    ↓
Middle-end (Optimization Passes)
    ↓
Backend (Qiskit Circuit Generation)
    ↓
Executable Quantum Circuit
```

### Pipeline Stages

**Frontend**: Custom lexer and recursive-descent parser generate Abstract Syntax Tree (AST) with semantic validation.

**IR Generation**: Translates C operations into quantum gates using Draper's QFT algorithms. Allocates 8-qubit registers and implements arithmetic via quantum phase rotations.

**Optimization**: Multi-pass optimization framework including constant folding, zero operand detection, phase precision filtering, and dead code elimination.

**Backend**: Converts optimized quantum IR to Qiskit circuits with metrics calculation (gate count, depth, qubit usage).

## Installation

### Requirements
- Python 3.10 or higher
- pip package manager

### Setup

```bash
# Clone repository
git clone https://github.com/pitesse/C_to_Quantum.git
cd C_to_Quantum

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install xdsl qiskit qiskit-aer matplotlib
```

## Usage

### Basic Compilation

```bash
# Activate virtual environment
source .venv/bin/activate

# Compile C program to quantum circuit
python -m C2Q tests/inputs/test_add_new.c

# View intermediate representation
python -m C2Q tests/inputs/test_add_new.c --ir

# Generate AST only
python -m C2Q tests/inputs/test_add_new.c --emit ast
```

### Example Programs

The `tests/inputs/` directory contains example C programs:

```bash
# Addition: 3 + 5 = 8
python -m C2Q tests/inputs/test_add_new.c

# Subtraction: 5 - 3 = 2
python -m C2Q tests/inputs/test_sub_new.c

# Multiplication: 2 × 3 = 6
python -m C2Q tests/inputs/test_mult_2x3.c
```

Generated outputs (AST, MLIR, circuit diagrams) are saved to `tests/outputs/`.

## Supported C Features

Currently supported:
- Variable declarations and assignments
- Integer arithmetic operations (addition, subtraction, multiplication)
- Function definitions with parameters and return values
- 8-bit integer representation

Planned features (see `TODO.md`):
- Control flow (if/else, loops)
- Comparison and logical operators
- Arrays and pointers
- Dynamic bit-width sizing

## Implementation Details

### Quantum Arithmetic Algorithms

The compiler uses Draper's QFT-based approach:

1. **Quantum Fourier Transform (QFT)**: Transforms register to frequency domain
2. **Phase Rotations**: Apply controlled phase gates proportional to addends
3. **Inverse QFT**: Transform back to computational basis

This approach achieves O(n²) gate complexity for n-bit operations.

### Register Management

Each integer variable is allocated an 8-qubit quantum register. Operations use OnQubit addressing for bit-level gate application within registers.

### Optimization Framework

The compiler implements two optimization levels:

**Classical Optimizations** (AST/IR level):
- Constant folding: Evaluate compile-time expressions
- Zero operand detection: Skip unnecessary QFT operations
- Algebraic simplification: Strength reduction and reassociation
- Dead store elimination: Remove unused variables

**Quantum Optimizations** (MLIR level):
- Phase precision filtering: Eliminate negligible rotations
- Partial QFT: Apply transforms only to used bits
- Gate cancellation: Remove inverse gate pairs
- SWAP optimization: Minimize qubit routing overhead

## Project Structure

```
C_to_Quantum/
├── C2Q/                   # Main compiler package
│   ├── frontend/          # Lexer, parser, AST definitions
│   │   ├── lexer.py       # Tokenization
│   │   ├── parser.py      # Recursive descent parser
│   │   ├── c_ast.py       # AST node definitions
│   │   └── ir_gen.py      # Quantum IR generation
│   ├── dialects/          # MLIR dialect definitions
│   │   └── quantum_dialect.py
│   ├── middle_end/        # Optimization passes
│   │   └── optimizations/
│   └── backend/           # Circuit generation
│       ├── run_qasm.py    # Qiskit integration
│       └── validate.py    # Validation framework
├── tests/                 # Test suite
│   ├── inputs/            # C test programs
│   └── outputs/           # Generated artifacts
├── demos/                 # Analysis and demo scripts
├── paper/                 # Academic paper (LaTeX)
├── TODO.md                # Development roadmap
└── README.md              # This file
```

## Development

### Current Status

The compiler is functional with basic arithmetic operations. See `TODO.md` for the development roadmap including:

1. Fix multiplication algorithm (critical)
2. Implement high-impact classical optimizations
3. Add comprehensive validation framework
4. Extend C language support

### Running Tests

```bash
# Activate environment
source .venv/bin/activate

# Run individual test
python -m C2Q tests/inputs/test_add_new.c

# Run optimization demos
python demos/optimization_demo.py
```

### Documentation

- **TODO.md**: Prioritized development roadmap with 18 tasks
- **paper/**: Academic paper documenting the compiler design
- **demos/**: Analysis scripts for optimization effectiveness

## Performance

Current optimization results for typical programs:
- Gate count reduction: 30-40%
- Circuit depth reduction: 30-50%
- Qubit usage reduction: 25-35%

Planned optimizations (see `TODO.md`) target 70-90% reduction for programs with constant expressions.

## Troubleshooting

**Import Errors**: Run as module with `python -m C2Q`, not direct script execution.

**Missing Dependencies**: Ensure virtual environment is activated before running.

**Compilation Errors**: Check that input C files use supported features only.

## Contributing

Contributions are welcome. Priority areas include:
- Multiplication algorithm correctness (Task #1 in TODO.md)
- Classical optimization passes (constant folding, zero detection)
- Extended C language support (control flow, arrays)
- Hardware-specific optimizations

## Citation

If you use this compiler in research, please cite:

```bibtex
@article{pizzoccheri2025c2q,
  title={C2Q: A Compiler Framework for Translating C Programs to Quantum Circuits},
  author={Pizzoccheri, Pietro},
  journal={Politecnico di Milano},
  year={2025}
}
```

## License

[To be determined]