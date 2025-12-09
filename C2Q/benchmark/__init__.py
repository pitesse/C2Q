"""
Benchmarking module for C2Q compiler optimization analysis.

This module provides tools for collecting quantitative metrics on compiler
optimizations, generating data for scientific evaluation and publication.
"""

from .run_benchmarks import run_all_benchmarks, BenchmarkResult

__all__ = ['run_all_benchmarks', 'BenchmarkResult']
