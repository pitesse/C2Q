# C2Q: C-to-Quantum Compilation Infrastructure

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-9%2F9%20passing-brightgreen)

A research compiler framework that translates a subset of **Standard C** into executable **Quantum Circuits** (QASM/Qiskit) using Draper's QFT-based arithmetic algorithms.

---

## Project Overview

C2Q is a complete compilation infrastructure designed to bridge classical programming and quantum computation. The compiler transforms C source code through a multi-stage pipeline, ultimately producing optimized quantum circuits that can be simulated or executed on quantum hardware.

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
│  Executable   ┌───────────────────┐    ┌────────────────────────────────┐   │
│  Circuit  ◄───│  Qiskit Backend   │◄───│  SSA-Aware Circuit Generation  │   │
│  (.qasm)      │  (Simulation/     │    │  (Handles Aggressive Renaming) │   │
│               │  Visualization)   │    │                                │   │
│               └───────────────────┘    └────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

The compiler leverages the **xDSL** framework for MLIR-based intermediate representation, enabling powerful pattern-based optimizations and a clean separation of concerns between frontend parsing, IR generation, optimization passes, and backend circuit synthesis.

---

## Features

### Draper QFT Arithmetic
Implements quantum addition, subtraction, and multiplication using the **Quantum Fourier Transform** basis. Arithmetic operations are performed in the frequency domain via controlled phase rotations, achieving O(n²) gate complexity for n-bit operations.

```c
// Automatically compiled to QFT-based quantum arithmetic
int a = 3;
int b = 5;
int c = a + b;  // Draper addition in Fourier basis
```

### Dynamic Width Handling
Supports **mixed-precision arithmetic** with automatic width detection and promotion. The compiler correctly handles operations between operands of different bit widths (e.g., 8-bit + 16-bit) and determines appropriate result register sizes.

### Advanced Optimization Pipeline
Multi-pass optimization framework with **iterative convergence**, achieving 15-36% gate count reduction across test cases.

#### Primary Optimization: Phase Precision Filtering
The dominant optimization pass that drives circuit improvements:

- **Eliminates negligible phase rotations** below a configurable threshold (default: 0.1 radians in benchmarks)
- **Iterative refinement**: Typically converges in 2 iterations
- **Impact**: Reduces phase gates by 19-56% depending on circuit complexity
  - Simple arithmetic (8-bit add/sub): ~20% reduction
  - Multiplication circuits: ~55% reduction
  - Mixed-width operations: ~55% reduction

The Draper QFT arithmetic inherently generates many fine-grained phase rotations. For practical integer operands, high-precision rotations (< 0.1 rad ≈ 5.7°) have negligible effect on measurement outcomes and can be safely eliminated without affecting computational correctness.

#### Supporting Optimization Passes
Additional passes available in the pipeline (impact varies by circuit structure):

| Optimization Pass | Implementation | Description |
|:---|:---|:---|
| **Phase Precision Filtering** | [draper_optimizer.py](C2Q/middle_end/optimizations/draper_optimizer.py#L108-L140) · `_optimize_phase_precision()` | Eliminates negligible phase rotations below threshold (primary optimization) |
| **Dead Code Elimination** | [remove_unused_op.py](C2Q/middle_end/optimizations/remove_unused_op.py) · `RemoveUnusedOperations` | Quantum-safe removal of unused operations preserving measurement dependencies |
| **CCNOT Decomposition** | [ccnot_decomposition.py](C2Q/middle_end/optimizations/ccnot_decomposition.py) · `CCnot_decomposition` | Barenco construction decomposing Toffoli gates into 1- and 2-qubit gates |
| **Adjacent Phase Consolidation** | [draper_optimizer.py](C2Q/middle_end/optimizations/draper_optimizer.py#L187-L240) · `_consolidate_adjacent_phases()` | Merges consecutive phase gates acting on the same qubit |
| **QFT Depth Analysis** | [draper_optimizer.py](C2Q/middle_end/optimizations/draper_optimizer.py#L142-L155) · `_optimize_qft_depth()` | Reduces QFT depth when operands use fewer bits than register width |
| **Hadamard Cancellation** | [draper_optimizer.py](C2Q/middle_end/optimizations/draper_optimizer.py#L246-L283) · `_cancel_hadamard_pairs()` | Cancels adjacent Hadamard gates at QFT/IQFT boundaries |
| **Redundant SWAP Elimination** | [draper_optimizer.py](C2Q/middle_end/optimizations/draper_optimizer.py#L157-L185) · `_eliminate_redundant_swaps()` | Removes unnecessary SWAP operations in QFT circuits |

**Orchestration**: All passes are coordinated by [integrated_optimizer.py](C2Q/middle_end/optimizations/integrated_optimizer.py) · `IntegratedQuantumOptimizer.optimize_circuit()`, which applies the Draper optimizer iteratively until convergence.

> **Note**: The supporting passes show circuit-dependent effectiveness. In the benchmark suite, phase precision filtering is the primary contributor to gate count and depth reductions.

### Robust Backend
**SSA-aware circuit generation** that correctly handles aggressive optimization and register renaming. The backend traces SSA value chains to maintain correct qubit mappings even after extensive IR transformations.

### Validation Framework
Built-in simulation using Qiskit Aer's **Matrix Product State (MPS)** method for efficient validation of circuits with 24+ qubits without exponential memory overhead.

---

## Performance Results

Benchmark results from the integrated optimization pipeline across 9 test cases:

| Metric | Average Improvement | Best Case |
|:---|:---:|:---:|
| **Gate Count** | -22.5% | -36.4% |
| **Circuit Depth** | -27.7% | -51.4% |
| **Phase Gates** | -22.0% | -56.1% |
| **MLIR Operations** | -22.2% | -36.4% |

### Detailed Benchmark Results

| Test Case | Base Gates | Opt Gates | Reduction | Base Depth | Opt Depth | Depth Δ |
|:---|---:|---:|---:|---:|---:|---:|
| Add (8-bit) | 120 | 102 | -15.0% | 39 | 36 | -7.7% |
| Sub (8-bit) | 119 | 101 | -15.1% | 39 | 36 | -7.7% |
| Mult (2×3) | 3,155 | 2,051 | -35.0% | 2,051 | 1,002 | -51.1% |
| Complex Math | 3,573 | 2,271 | -36.4% | 2,083 | 1,012 | -51.4% |

> **Note**: All 9/9 test cases pass validation, confirming functional correctness after optimization.

---

## Quick Start

### Installation

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

### Basic Usage

The compiler is invoked as a Python module with various options:

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
# Run full benchmark suite with all 9 test cases
python -m C2Q.benchmark.run_benchmarks

# Results are saved to benchmarks_data/results.csv
# Individual MLIR files saved to benchmarks_data/*.mlir
```

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
│   │       └── in_placing.py             # CNOT chain optimization
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

## Technical Details

### Draper QFT Arithmetic

The compiler implements Thomas Draper's quantum arithmetic algorithms:

1. **Quantum Fourier Transform (QFT)**: Transforms the target register to the frequency domain
2. **Controlled Phase Rotations**: Applies phase gates proportional to the addend values
3. **Inverse QFT**: Transforms back to the computational basis

```
Addition: |a⟩|b⟩ → |a⟩|a+b⟩

     ┌─────┐                    ┌──────┐
|a⟩──┤     ├─── controlled ────┤      ├── |a⟩
     │     │    phase gates    │      │
|b⟩──┤ QFT ├──────────────────┤ IQFT ├── |a+b⟩
     └─────┘                    └──────┘
```

### Register Naming Convention

Quantum registers follow the `qX_Y` naming scheme:
- `X`: Register number (unique per variable)
- `Y`: Version number (incremented on each operation)

This SSA-style naming enables precise tracking through optimization passes.

### Optimization Convergence

The Draper optimizer uses iterative refinement, typically converging in 2 iterations:

```
Iteration 1: Eliminate negligible phase rotations (primary reduction)
            • Simple arithmetic: ~18 phase gates eliminated
            • Multiplication: ~1100+ phase gates eliminated
            
Iteration 2: Verify no additional optimizations possible
            • Apply supporting passes
            • Check for convergence (typically 0 changes)
```

**Example from benchmark output (Mult 2×3 circuit):**
```
Draper Iteration 1: Eliminated 1104/1968 phase rotations (56% reduction)
Draper Iteration 2: Eliminated 0/864 phase rotations → Converged
```

The iterative approach ensures all optimization opportunities are explored while avoiding unnecessary passes once convergence is reached.

---

## Citation

If you use C2Q in academic research, please cite:

```bibtex
@article{pizzoccheri2025c2q,
  title     = {C2Q: A Compiler Framework for Translating C Programs to Quantum Circuits},
  author    = {Pizzoccheri, Pietro},
  journal   = {Politecnico di Milano},
  year      = {2025}
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
