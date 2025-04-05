# Running C to Quantum

## Installation

First, ensure you have Python 3 installed on your system.

### Dependencies

This tool requires the following Python packages:
- xdsl


```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install xdsl
```

## Usage

Convert a C file to quantum representation:

```bash
# Ensure your virtual environment is activated
source .venv/bin/activate

# Run using the module syntax
python -m CtoQ <file_name>.c
```

### Example

```bash
python -m CtoQ examples/simple.c
```

## Options

Add any additional command-line options here:

- 

## Troubleshooting

If you encounter import errors, ensure you're running the tool as a module with `python -m CtoQ` rather than directly executing a script.

Make sure your virtual environment is activated before running the tool.

