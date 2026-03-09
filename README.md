# C2Q: C-to-Quantum Compilation Infrastructure

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Benchmarks](https://img.shields.io/badge/benchmarks-8%2F8%20passing-brightgreen)

A research compiler framework that translates a subset of **Standard C** into executable **Quantum Circuits** (QASM/Qiskit) using Draper's QFT-based arithmetic algorithms.

---

## Project Overview

C2Q is a complete compilation infrastructure designed to bridge classical programming and quantum computation. The compiler transforms C source code through a multi-stage pipeline, ultimately producing optimized quantum circuits that can be simulated or executed on quantum hardware.

For a comprehensive understanding of the project's scope, results, and the academic contributions it enabled, please refer to the detailed project paper,  see [paper.pdf](paper/main.pdf).

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          C2Q COMPILATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  C Source     ┌───────────┐    ┌───────────┐    ┌───────────────────────┐   │
│  Code    ───► │  Frontend │───►│  IR Gen   │───►│  Quantum MLIR Dialect │   │
│  (.c)         │  (Lexer/  │    │  (Draper  │    │  (xDSL Framework)     │   │
│               │  Parser)  │    │  QFT).    │    │                       │   │
│               └───────────┘    └───────────┘    └───────────┬───────────┘   │
│                                                             │               │
│                                                             ▼               │
│               ┌───────────────────────────────────────────────────────────┐ │
│               │              OPTIMIZATION PIPELINE                        │ │
│               │                                                           │ │
│               │  ┌──────────────────────────────────────────────────────┐ │ │
│               │  │  Phase Precision Filtering (Primary)                 │ │ │
│               │  │  • Eliminates negligible phase rotations < threshold │ │ │
│               │  │  • Iterative convergence (typically 2 iterations)    │ │ │
│               │  │  • Average: 20-56% phase gate reduction              │ │ │
│               │  └──────────────────────────────────────────────────────┘ │ │
│               │                                                           │ │
│               │  Supporting Passes (Circuit-Dependent):                   │ │
│               │  • Dead Code Elimination • CCNOT Decomposition            │ │
│               │  • Adjacent Phase Consolidation • QFT Depth Analysis      │ │
│               │  • Hadamard Cancellation • Redundant SWAP Elimination     │ │
│               │                                                           │ │
│               └───────────────────────────────────────────────────────────┘ │
│                                                             │               │
│                                                             ▼               │
│               ┌───────────────────┐    ┌────────────────────────────────┐   │
│  Circuit  ◄───│  Qiskit Backend   │◄───│  SSA-Aware Circuit Generation  │   │
│               │  (Simulation/     │    │  (Handles Aggressive Renaming) │   │
│               │  Visualization)   │    │                                │   │
│               └───────────────────┘    └────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

The compiler leverages the **xDSL** framework for MLIR-based intermediate representation, enabling powerful pattern-based optimizations and a clean separation of concerns between frontend parsing, IR generation, optimization passes, and backend circuit synthesis.

---

## Quick Start

> **New here?** If you want a zero-configuration setup, start with **Docker** in the next section and skip native dependency installation.

## Docker Setup and Usage

This repository includes a zero-configuration Docker environment based on `python:3.12`.
The container image installs all runtime dependencies used by the compiler and benchmark pipeline:
`xdsl`, `qiskit`, `qiskit-aer`, `matplotlib`, and `typing_extensions`.

### 1) Build the Docker image

```bash
# Clone repository
git clone https://github.com/pitesse/C2Q.git
cd C2Q
```

```bash
docker compose build
```

### 2) Run the compiler in Docker

Compile a test input with the default command (`--rm` ensures the container is removed after computation):

```bash
docker compose run --rm c2q
```

Run custom compiler commands (copy-pasteable examples):

```bash
# Emit IR and print it
docker compose run --rm c2q python -m C2Q tests/inputs/test_add.c --emit ir --ir

# Compile with optimization disabled
docker compose run --rm c2q python -m C2Q tests/inputs/test_add.c --no-optimize

# Validate expected output
docker compose run --rm c2q python -m C2Q tests/inputs/test_add.c --force-optimize --validate 8
```

### 3) Run benchmarks in Docker

```bash
docker compose run --rm benchmark
```

Benchmark artifacts are written to `benchmarks_data/` on the host (for example `benchmarks_data/results.csv` and the generated `*_base.mlir` / `*_opt.mlir` files).

### Notes

- LaTeX sources under `paper/` are excluded from the Docker build context.
- The compose setup mounts only `C2Q/`, `tests/`, and `benchmarks_data/` into containers for a clean runtime environment.

---

## Native Installation (without Docker)

**Python Version Requirement:** Python 3.11 or 3.12 is required. Python 3.13+ is not yet supported by qiskit-aer.

```bash
# Clone repository
git clone https://github.com/pitesse/C2Q.git
cd C2Q
```

Use this path only if you want to run the project directly on your machine.

```bash
# Create virtual environment with Python 3.12 
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install xdsl qiskit qiskit-aer matplotlib
```

### Basic Usage (Without Docker)

The compiler is invoked as a Python module with various options:

> **Note:** All commands below assume the virtual environment is activated. Use `python` (not `python3.12`) when running inside the venv.

```bash
# Basic compilation: generates AST, MLIR, and circuit visualization
python -m C2Q tests/inputs/test_add.c

# Compile with optimizations and validate result
python -m C2Q tests/inputs/test_add.c --force-optimize --validate 8

# Print intermediate representation to console
python -m C2Q tests/inputs/test_add.c --ir

# Generate AST only (no circuit generation)
python -m C2Q tests/inputs/test_add.c --emit ast

# Disable optimizations for debugging
python -m C2Q tests/inputs/test_add.c --no-optimize
```

### Command-Line Options

| Option | Description |
|:---|:---|
| `--emit {ast,ir}` | Output format (default: ir) |
| `--ir` | Print generated MLIR to console |
| `--force-optimize` | Apply optimizations during validation |
| `--no-optimize` | Disable optimization passes |
| `--validate N` | Validate circuit output equals N |
| `--signed` | Interpret result as signed two's complement |
| `--result-width N` | Result register width in bits (default: 8, use 16 for multiplication) |
| `--precision F` | Phase precision threshold (default: 1e-4) |

### Running Benchmarks

```bash
# Run full benchmark suite (8 test cases)
python -m C2Q.benchmark.run_benchmarks

# Results are saved to benchmarks_data/results.csv
# Individual MLIR files saved to benchmarks_data/*.mlir

```

### Debugging Passes

- Adjacent CNOT cancellation debug: `C2Q_DEBUG_CNOT_CANCEL=1` (legacy: `C2Q_DEBUG_INPLACING=1`)

### Example: Complete Workflow

```bash
# 1. Compile and view the circuit
python -m C2Q tests/inputs/test_mult_2x3.c --ir

# 2. Validate correctness (2 × 3 = 6)
python -m C2Q tests/inputs/test_mult_2x3.c --force-optimize --validate 6 --result-width 16

# 3. Compare optimized vs unoptimized
python -m C2Q tests/inputs/test_mult_2x3.c --no-optimize  # Baseline
python -m C2Q tests/inputs/test_mult_2x3.c               # Optimized
```

---

## Project Structure

```
C_to_Quantum/
├── C2Q/                              # Main compiler package
│   ├── __main__.py                   # Entry point and CLI
│   │
│   ├── frontend/                     # Parsing and IR generation
│   │   ├── lexer.py                  # Tokenization of C source
│   │   ├── parser.py                 # Recursive-descent parser
│   │   ├── c_ast.py                  # AST node definitions
│   │   ├── ir_gen.py                 # C AST → Quantum MLIR
│   │   ├── quantum_arithmetic.py     # Draper QFT algorithms
│   │   └── location.py               # Source location tracking
│   │
│   ├── dialects/                     # MLIR dialect definitions
│   │   └── quantum_dialect.py        # Quantum operations (xDSL/IRDL)
│   │
│   ├── middle_end/                   # Optimization passes
│   │   └── optimizations/
│   │       ├── integrated_optimizer.py   # Main optimization pipeline
│   │       ├── draper_optimizer.py       # QFT-specific optimizations
│   │       ├── remove_unused_op.py       # Dead code elimination
│   │       ├── ccnot_decomposition.py    # Toffoli decomposition
│   │       └── cnot_cancellation.py      # Adjacent CNOT cancellation (quantum-safe)
│   │
│   ├── backend/                      # Circuit generation
│   │   ├── run_qasm.py               # MLIR → Qiskit conversion
│   │   └── validate.py               # MPS simulation framework
│   │
│   └── benchmark/                    # Benchmarking infrastructure
│       └── run_benchmarks.py         # Automated test suite
│
├── tests/                            # Test suite
│   ├── inputs/                       # C test programs
│   │   ├── test_add.c                # Addition: 3 + 5 = 8
│   │   ├── test_sub.c                # Subtraction: 8 - 3 = 5
│   │   ├── test_mult_2x3.c           # Multiplication: 2 × 3 = 6
│   │   └── ...                       # Additional test cases
│   └── outputs/                      # Generated AST/MLIR/circuits
│
├── benchmarks_data/                  # Benchmark results and artifacts
│   ├── results.csv                   # Metrics comparison table
│   └── *.mlir                        # Base and optimized IR files
│
├── demos/                            # Analysis and demo scripts
├── paper/                            # Academic paper (LaTeX)
└── README.md                         # This file
```

### Module Descriptions

| Module | Purpose |
|:---|:---|
| `frontend/` | Lexical analysis, parsing, and AST construction. Transforms C source into an abstract syntax tree with semantic validation. |
| `frontend/ir_gen.py` | Core IR generation. Maps C operations to quantum gate sequences using Draper QFT arithmetic. Manages quantum register allocation. |
| `dialects/` | Defines the `quantum` MLIR dialect using xDSL's IRDL framework. Includes all quantum operations (gates, measurements, control flow). |
| `middle_end/` | Optimization passes operating on quantum MLIR. Pattern-based rewrites using xDSL's `RewritePattern` infrastructure. |
| `backend/` | Converts optimized MLIR to Qiskit circuits. Handles SSA value tracking, gate mapping, and circuit metrics calculation. |

---

## Supported C Features

### Currently Implemented

- **Variable declarations**: `int a = 5;`
- **Assignment statements**: `a = b + c;`
- **Arithmetic operations**: `+`, `-`, `*` (addition, subtraction, multiplication)
- **Function definitions**: `int main() { ... }`
- **Return statements**: `return expression;`
- **8-bit integer representation** (configurable width)

### Example Input

```c
// tests/inputs/test_add.c
int main() {
    int a = 3;
    int b = 5;
    int c = a + b;
    return c;
}
```

### Generated Output

The compiler produces:
1. **AST**: Abstract syntax tree representation
2. **Quantum MLIR**: Intermediate representation with quantum operations
3. **Qiskit Circuit**: Executable quantum circuit with visualization
4. **Metrics**: Gate count, depth, qubit usage statistics

---

## Citation

If you use C2Q in academic research, please cite:

```bibtex
@article{pizzoccheri2025c2q,
  title     = {C2Q: A Compiler Framework for Translating C Programs to Quantum Circuits},
  author    = {Pizzoccheri, Pietro},
  journal   = {Politecnico di Milano},
  year      = {2026}
}
```

---

## License

MIT License

Copyright (c) 2025 Pietro Pizzoccheri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.