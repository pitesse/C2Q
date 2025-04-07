TODO review this readme

# C to Quantum Compiler

A tool for converting C code to quantum representations using the XDSL compiler infrastructure.

## Overview

C_to_Quantum is a compiler that transforms classical C programs into quantum intermediate representations, allowing for translation between classical algorithms and their quantum counterparts. The compiler uses a custom lexer and parser built on top of XDSL utilities to analyze C code and generate appropriate quantum representations.

## Installation

First, ensure you have Python 3.10+ installed on your system.

### Dependencies

This tool requires the following Python packages:
- xdsl (MLIR-based compiler infrastructure)
- libclang
- qiskit
- matpoltlib

```bash
# Clone the repository
git clone https://github.com/yourusername/C_to_Quantum.git
cd C_to_Quantum

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install xdsl

pip install libclang

pip install qiskit

pip install qiskit-aer

pip install matplotlib
```

## Usage

Convert a C file to quantum representation:

```bash
# Ensure your virtual environment is activated
source .venv/bin/activate

# Run using the module syntax
python -m C2Q <file_name>.c
```

### Examples

Basic usage:
```bash
python -m C2Q examples/simple.c
```

Generate AST without conversion:
```bash
python -m C2Q examples/simple.c --emit ast
```

## Documentation

### Viewing Documentation

This project includes comprehensive documentation generated with Doxygen.

#### HTML Documentation
```bash
xdg-open docs/html/index.html
```


## Project Structure

- C2Q - Main package directory
  - `frontend/` - C lexing, parsing and initial IR generation
    - `lexer.py` - Custom C lexer implementation
    - `parser.py` - C parser using the lexer to generate AST
    - `ir_gen.py` - Converts AST to quantum IR
  - `midend/` - IR transformations and optimizations
  - `backend/` - Target-specific code generation
  - `examples/` - Example C programs

## Implementation Details

The compiler uses a custom implementation of a C lexer and parser rather than relying on external libraries like libClang. This gives precise control over the parsing process and allows for specialized handling of C constructs that are relevant to quantum transformation.

## Troubleshooting

- **Import Errors**: Ensure you're running the tool as a module with `python -m C2Q` rather than directly executing a script.
- **Missing Dependencies**: Make sure your virtual environment is activated before running the tool.
- **Documentation Issues**: If documentation doesn't generate correctly, ensure Doxygen is properly installed.

## Contributing



## License

