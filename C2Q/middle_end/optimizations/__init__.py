"""
Quantum circuit optimization passes.

This module provides optimization passes specifically designed for quantum circuits,
focusing on reducing gate count, circuit depth, and qubit usage while preserving
quantum computational correctness.
"""

from .draper_optimizer import DraperOptimizer, optimize_draper_arithmetic, OptimizationStats
from .integrated_optimizer import IntegratedQuantumOptimizer, optimize_quantum_circuit, create_optimizer_pipeline

# Legacy optimizations (pattern-based)
from .remove_unused_op import RemoveUnusedOperations
from .ccnot_decomposition import CCnot_decomposition
from .qubit_renumber import QubitRenumber
from .in_placing import InPlacing

__all__ = [
    # Main optimization interfaces
    'IntegratedQuantumOptimizer',
    'optimize_quantum_circuit',
    'create_optimizer_pipeline',
    
    # Specialized optimizers
    'DraperOptimizer',
    'optimize_draper_arithmetic', 
    'OptimizationStats',
    
    # Individual pattern-based passes
    'RemoveUnusedOperations',
    'CCnot_decomposition', 
    'QubitRenumber',
    'InPlacing'
]
