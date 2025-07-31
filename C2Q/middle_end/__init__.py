"""
Middle-end optimization passes for quantum circuits.

This module provides optimization and transformation passes that operate on
quantum MLIR to reduce resource requirements and improve circuit efficiency.
"""

from .optimizations import optimize_quantum_module, optimize_draper_arithmetic

__all__ = [
    'optimize_quantum_module',
    'optimize_draper_arithmetic'
]