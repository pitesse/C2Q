"""
Middle-end passes for the C2Q compiler.

This module contains various transformation and analysis passes
that operate on the quantum IR after initial generation.
"""

from .naming import QuantumRegisterNamer

__all__ = ["QuantumRegisterNamer"]
