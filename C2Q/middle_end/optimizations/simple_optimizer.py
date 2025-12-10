"""
Simple and safe quantum circuit optimizations.

This module provides basic optimizations that are safe to apply without
complex dependency analysis, focusing on pattern recognition and 
simple transformations.
"""

import math
from typing import List, Dict, Set, Optional
from collections import defaultdict

from xdsl.ir import SSAValue, Operation
from xdsl.dialects.builtin import ModuleOp


class SimpleQuantumOptimizer:
    """
    Simple optimization passes that don't require complex SSA analysis.
    
    Focuses on safe optimizations that can be applied based on pattern
    recognition without breaking SSA dependencies.
    """
    
    def __init__(self, precision_threshold: float = 1e-6):
        """
        Initialize simple optimizer.
        
        Args:
            precision_threshold: Minimum phase angle to consider significant
        """
        self.precision_threshold = precision_threshold
        self.stats = {
            'small_phases_found': 0,
            'patterns_analyzed': 0,
            'qft_operations': 0,
            'register_usage': {}
        }
    
    def analyze_and_optimize(self, module: ModuleOp) -> ModuleOp:
        """
        Analyze quantum circuit and provide optimization insights.
        
        Instead of aggressively modifying the circuit, this function
        analyzes patterns and provides insights about potential optimizations.
        """
        print("🔍 Analyzing quantum circuit for optimization opportunities...")
        
        # Count operation types
        self._analyze_operation_distribution(module)
        
        # Analyze phase precision
        self._analyze_phase_precision(module)
        
        # Analyze register usage patterns
        self._analyze_register_usage(module)
        
        # Analyze QFT structure
        self._analyze_qft_structure(module)
        
        # Print optimization insights
        self._print_optimization_insights()
        
        return module
    
    def _analyze_operation_distribution(self, module: ModuleOp) -> None:
        """Analyze distribution of quantum operations."""
        op_counts = defaultdict(int)
        
        for op in module.walk():
            if hasattr(op, 'name'):
                op_counts[op.name] += 1
                
        self.stats['operation_counts'] = dict(op_counts)
        self.stats['patterns_analyzed'] = sum(op_counts.values())
    
    def _analyze_phase_precision(self, module: ModuleOp) -> None:
        """Analyze phase rotation precision."""
        phase_angles = []
        small_phases = 0
        
        for op in module.walk():
            if hasattr(op, 'name') and op.name == "quantum.OnQubit_controlled_phase":
                try:
                    # Try to extract phase from attributes
                    if hasattr(op, 'attributes') and 'phase' in op.attributes:
                        phase = float(op.attributes['phase'].data)  # type: ignore[attr-defined]
                        phase_angles.append(abs(phase))
                        
                        if abs(phase) < self.precision_threshold:
                            small_phases += 1
                except:
                    pass
        
        self.stats['phase_angles'] = phase_angles
        self.stats['small_phases_found'] = small_phases
        self.stats['total_phase_ops'] = len(phase_angles)
    
    def _analyze_register_usage(self, module: ModuleOp) -> None:
        """Analyze quantum register usage patterns."""
        register_ops = defaultdict(int)
        
        for op in module.walk():
            if hasattr(op, 'name') and op.name == "quantum.init":
                # Track register initialization
                if hasattr(op, 'results') and op.results:
                    result = op.results[0]
                    if hasattr(result, '_name') and result._name:
                        register_ops[result._name] += 1
        
        self.stats['register_usage'] = dict(register_ops)
    
    def _analyze_qft_structure(self, module: ModuleOp) -> None:
        """Analyze QFT operation structure."""
        hadamard_count = 0
        swap_count = 0
        phase_count = 0
        
        for op in module.walk():
            if hasattr(op, 'name'):
                if op.name == "quantum.OnQubit_hadamard":
                    hadamard_count += 1
                elif op.name == "quantum.OnQubit_swap":
                    swap_count += 1
                elif op.name == "quantum.OnQubit_controlled_phase":
                    phase_count += 1
        
        self.stats['qft_operations'] = {
            'hadamard_gates': hadamard_count,
            'swap_gates': swap_count,
            'phase_rotations': phase_count
        }
    
    def _print_optimization_insights(self) -> None:
        """Print insights about optimization opportunities."""
        print("\n📊 Quantum Circuit Analysis Results:")
        print("=" * 50)
        
        # Operation distribution
        if 'operation_counts' in self.stats:
            print("\n🔢 Operation Distribution:")
            for op_name, count in self.stats['operation_counts'].items():
                if 'quantum.' in op_name:
                    clean_name = op_name.replace('quantum.OnQubit_', '').replace('quantum.', '')
                    print(f"  {clean_name}: {count}")
        
        # Phase precision analysis
        if self.stats['small_phases_found'] > 0:
            total_phases = self.stats.get('total_phase_ops', 0)
            percentage = (self.stats['small_phases_found'] / total_phases * 100) if total_phases > 0 else 0
            print(f"\n⚡ Phase Optimization Opportunity:")
            print(f"  Found {self.stats['small_phases_found']} phase rotations < {self.precision_threshold}")
            print(f"  This represents {percentage:.1f}% of all phase operations")
            print(f"  💡 These could potentially be eliminated for reduced circuit depth")
        
        # QFT structure analysis
        qft_ops = self.stats.get('qft_operations', {})
        if qft_ops:
            print(f"\n🌊 QFT Structure Analysis:")
            print(f"  Hadamard gates: {qft_ops.get('hadamard_gates', 0)}")
            print(f"  SWAP gates: {qft_ops.get('swap_gates', 0)}")
            print(f"  Phase rotations: {qft_ops.get('phase_rotations', 0)}")
            
            # Calculate QFT efficiency
            total_qft_ops = sum(qft_ops.values())
            if total_qft_ops > 0:
                phase_ratio = qft_ops.get('phase_rotations', 0) / total_qft_ops
                print(f"  Phase rotation ratio: {phase_ratio:.2f}")
                if phase_ratio > 0.7:
                    print("  💡 High phase rotation density - good candidate for precision optimization")
        
        # Register usage insights
        register_count = len(self.stats.get('register_usage', {}))
        if register_count > 0:
            print(f"\n📝 Register Usage: {register_count} quantum registers allocated")
            
        # Overall optimization recommendations
        print(f"\n🎯 Optimization Recommendations:")
        
        small_phases = self.stats.get('small_phases_found', 0)
        if small_phases > 5:
            print(f"  ✅ Phase precision optimization could eliminate ~{small_phases} gates")
        else:
            print(f"  ⚪ Phase precision: minimal impact ({small_phases} small phases)")
            
        swap_gates = qft_ops.get('swap_gates', 0)
        if swap_gates > 8:
            print(f"  ✅ SWAP optimization could reduce {swap_gates} gates")
        else:
            print(f"  ⚪ SWAP optimization: minimal impact ({swap_gates} swaps)")
            
        if register_count >= 4:
            print(f"  ✅ Register coalescing could reduce qubit count from {register_count}")
        else:
            print(f"  ⚪ Register usage: already efficient ({register_count} registers)")
        
        print("\n🏆 Overall Assessment:")
        total_ops = self.stats.get('patterns_analyzed', 0)
        potential_savings = small_phases + max(0, swap_gates - 4)
        if potential_savings > 0 and total_ops > 0:
            savings_percentage = (potential_savings / total_ops) * 100
            print(f"  Potential gate reduction: ~{potential_savings} gates ({savings_percentage:.1f}%)")
        else:
            print(f"  Circuit is already well-optimized with {total_ops} operations")


def analyze_quantum_circuit(module: ModuleOp, **kwargs) -> ModuleOp:
    """
    Convenience function to analyze quantum circuit for optimization opportunities.
    
    Args:
        module: Input MLIR module
        **kwargs: Options passed to SimpleQuantumOptimizer
        
    Returns:
        Analyzed MLIR module (unchanged)
    """
    analyzer = SimpleQuantumOptimizer(**kwargs)
    return analyzer.analyze_and_optimize(module)
