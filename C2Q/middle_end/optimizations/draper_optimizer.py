"""
Specialized optimizations for Draper QFT-based arithmetic circuits.

This module contains optimizations specifically designed for the quantum arithmetic
algorithms used in the C-to-Quantum compiler, particularly Draper's QFT-based
addition and subtraction.
"""

import math
from typing import List, Dict, Set, Optional
from collections import defaultdict

from xdsl.ir import SSAValue, Operation
from xdsl.dialects.builtin import ModuleOp

from .quantum_optimizer import OptimizationStats


class DraperOptimizer:
    """
    Optimizations specific to Draper QFT arithmetic circuits.
    
    These optimizations understand the structure of QFT-based arithmetic
    and can make intelligent decisions about precision, gate elimination,
    and circuit depth reduction.
    """
    
    def __init__(self, precision_threshold: float = 1e-3):
        """
        Initialize Draper-specific optimizer.
        
        Args:
            precision_threshold: Minimum phase angle to keep (eliminates smaller rotations)
        """
        self.precision_threshold = precision_threshold
        self.stats = OptimizationStats()
    
    def optimize_draper_circuit(self, module: ModuleOp) -> ModuleOp:
        """
        Apply Draper-specific optimizations to reduce arithmetic circuit complexity.
        
        Key optimizations:
        1. Eliminate high-precision phase rotations for small operands
        2. Optimize QFT depth based on actual register usage
        3. Consolidate adjacent phase rotations in frequency domain
        4. Remove redundant SWAP operations in QFT
        """
        print("🧮 Starting Draper arithmetic optimization...")
        
        # Draper-specific passes
        self._optimize_phase_precision(module)
        self._optimize_qft_depth(module) 
        self._eliminate_redundant_swaps(module)
        self._optimize_zero_operands(module)
        
        print("✅ Draper optimization complete!")
        print(self.stats)
        
        return module
    
    def _optimize_phase_precision(self, module: ModuleOp) -> None:
        """
        Eliminate negligible phase rotations in Draper arithmetic.
        
        For small integer operands, many of the high-precision phase rotations
        (like π/256, π/512) have negligible effect and can be safely removed.
        """
        print("  📏 Optimizing phase precision...")
        
        eliminated = 0
        for op in list(module.walk()):
            if hasattr(op, 'name') and op.name == "quantum.OnQubit_controlled_phase":
                phase = abs(self._extract_phase(op))
                
                # Eliminate very small phase rotations
                if phase < self.precision_threshold:
                    if op.parent is not None:
                        op.detach()
                    op.erase()
                    eliminated += 1
                    self.stats.gates_eliminated += 1
                    
        print(f"    Eliminated {eliminated} negligible phase rotations")
    
    def _optimize_qft_depth(self, module: ModuleOp) -> None:
        """
        Reduce QFT depth by analyzing actual register bit usage.
        
        If we know that operands are small (e.g., fit in 4 bits instead of 8),
        we can eliminate the higher-order QFT operations.
        """
        print("  🔍 Analyzing QFT depth requirements...")
        
        # Analyze the actual bit patterns used in the circuit
        # This is a heuristic approach - in practice, you'd want static analysis
        
        # Look for patterns where higher-order bits are never set
        bit_usage = self._analyze_bit_usage(module)
        # Default to 7 (full 8-bit) if no bits found (e.g., dynamic inputs)
        max_significant_bit = max(bit_usage) if bit_usage else 7
        
        # If we're only using lower bits, we can eliminate higher-order QFT operations
        if max_significant_bit < 7:  # Default 8-bit assumption
            eliminated = self._eliminate_unused_qft_operations(module, max_significant_bit + 1)
            self.stats.depth_reduction += eliminated
            print(f"    Reduced QFT depth to {max_significant_bit + 1} bits")
        else:
            print(f"    All bits ({max_significant_bit + 1}) in use, no QFT depth reduction possible")
    
    def _eliminate_redundant_swaps(self, module: ModuleOp) -> None:
        """
        Remove redundant SWAP operations in QFT implementation.
        
        Sometimes SWAP-SWAP pairs can cancel out, or SWAPs can be absorbed
        into the computation rather than performed explicitly.
        """
        print("  🔄 Eliminating redundant SWAP operations...")
        
        swaps = [op for op in module.walk() if op.name == "quantum.OnQubit_swap"]
        eliminated = 0
        
        # Look for SWAP-SWAP cancellations
        i = 0
        while i < len(swaps) - 1:
            swap1 = swaps[i]
            swap2 = swaps[i + 1]
            
            if self._swaps_cancel(swap1, swap2):
                swap1.erase()
                swap2.erase() 
                eliminated += 2
                self.stats.gates_eliminated += 2
                i += 2
            else:
                i += 1
                
        print(f"    Eliminated {eliminated} redundant SWAPs")
    
    def _optimize_zero_operands(self, module: ModuleOp) -> None:
        """
        Optimize arithmetic operations involving zero operands.
        
        Special cases:
        - A + 0 = A (no operation needed)
        - A - 0 = A (no operation needed)  
        - 0 + B = B (no operation needed)
        - A * 0 = 0 (replace with register clear)
        """
        print("  0️⃣  Optimizing zero operand cases...")
        
        # This requires analyzing the data flow to identify zero constants
        # For now, implement detection of obvious zero patterns
        
        zero_optimizations = self._detect_zero_arithmetic(module)
        for optimization in zero_optimizations:
            self._apply_zero_optimization(optimization)
            
        print(f"    Applied {len(zero_optimizations)} zero-operand optimizations")
    
    def _extract_phase(self, op: Operation) -> float:
        """Extract phase angle from controlled phase operation."""
        try:
            attr = op.attributes.get("phase")
            if attr is None:
                return 0.0
            # Try different XDSL attribute access patterns
            if hasattr(attr, 'value'):
                if hasattr(attr.value, 'data'):
                    return float(attr.value.data)
                return float(attr.value)
            elif hasattr(attr, 'data'):
                return float(attr.data)
            elif hasattr(attr, 'parameters') and len(attr.parameters) > 0:
                return float(attr.parameters[0].data)
            else:
                return float(attr)
        except:
            return 0.0
    
    def _analyze_bit_usage(self, module: ModuleOp) -> Set[int]:
        """
        Analyze which bit positions are actually used in the circuit.
        
        A bit is considered "used" if it appears in ANY quantum operation's
        index, target_index, or control_index attributes. This ensures we
        don't remove QFT operations for bits that participate in Fourier-domain
        arithmetic (like controlled phase rotations in multiplication).
        """
        used_bits = set()
        
        # Iterate through ALL quantum operations
        for op in module.walk():
            if hasattr(op, 'name') and hasattr(op, 'attributes'):
                try:
                    # Check all relevant index attributes
                    for attr_name in ['index', 'target_index', 'control_index']:
                        attr = op.attributes.get(attr_name)
                        if attr is not None:
                            # Extract the integer value using multiple access patterns
                            val = None
                            if hasattr(attr, 'value'):
                                if hasattr(attr.value, 'data'):
                                    val = int(attr.value.data)
                                else:
                                    val = int(attr.value)
                            elif hasattr(attr, 'data'):
                                val = int(attr.data)
                            else:
                                val = int(attr)
                            
                            if val is not None:
                                used_bits.add(val)
                except:
                    # If we can't extract the index, skip this operation
                    pass
                    
        return used_bits
    
    def _eliminate_unused_qft_operations(self, module: ModuleOp, max_bits: int) -> int:
        """
        Remove QFT operations on unused higher-order bits.
        
        Args:
            module: MLIR module
            max_bits: Maximum number of bits actually needed
            
        Returns:
            Number of operations eliminated
        """
        eliminated = 0
        
        for op in list(module.walk()):
            # Remove operations on bits >= max_bits
            if self._operates_on_high_bits(op, max_bits):
                if op.parent is not None:
                    op.detach()
                op.erase()
                eliminated += 1
                self.stats.gates_eliminated += 1
                
        return eliminated
    
    def _operates_on_high_bits(self, op: Operation, max_bits: int) -> bool:
        """Check if operation works on bits >= max_bits."""
        try:
            if hasattr(op, 'attributes'):
                # Check index attribute
                attr = op.attributes.get("index")
                if attr is not None:
                    val = None
                    if hasattr(attr, 'value'):
                        if hasattr(attr.value, 'data'):
                            val = int(attr.value.data)
                        else:
                            val = int(attr.value)
                    elif hasattr(attr, 'data'):
                        val = int(attr.data)
                    else:
                        val = int(attr)
                    if val is not None and val >= max_bits:
                        return True
                    
                # Also check target_index for controlled operations
                target_attr = op.attributes.get("target_index")
                if target_attr is not None:
                    val = None
                    if hasattr(target_attr, 'value'):
                        if hasattr(target_attr.value, 'data'):
                            val = int(target_attr.value.data)
                        else:
                            val = int(target_attr.value)
                    elif hasattr(target_attr, 'data'):
                        val = int(target_attr.data)
                    else:
                        val = int(target_attr)
                    if val is not None and val >= max_bits:
                        return True
                    
        except:
            pass
            
        return False
    
    def _swaps_cancel(self, swap1: Operation, swap2: Operation) -> bool:
        """Check if two SWAP operations cancel each other out."""
        try:
            # Extract the qubit indices being swapped
            indices1 = self._get_swap_indices(swap1)
            indices2 = self._get_swap_indices(swap2)
            
            # SWAPs cancel if they swap the same pair of qubits
            return indices1 == indices2 or indices1 == indices2[::-1]
        except:
            return False
    
    def _get_swap_indices(self, swap_op: Operation) -> tuple:
        """Extract the pair of qubit indices being swapped."""
        try:
            idx1 = swap_op.attributes.get("qubit1", 0)
            idx2 = swap_op.attributes.get("qubit2", 0) 
            return (int(idx1), int(idx2))
        except:
            return (0, 0)
    
    def _detect_zero_arithmetic(self, module: ModuleOp) -> List[Dict]:
        """
        Detect arithmetic operations involving zero operands.
        
        Returns list of optimization opportunities.
        """
        optimizations = []
        
        # This would require more sophisticated analysis of the data flow
        # to detect which registers contain zero values
        
        # For now, return empty list (placeholder)
        return optimizations
    
    def _apply_zero_optimization(self, optimization: Dict) -> None:
        """Apply a specific zero-operand optimization."""
        # Placeholder for applying detected optimizations
        pass


def optimize_draper_arithmetic(module: ModuleOp, **kwargs) -> ModuleOp:
    """
    Convenience function to optimize Draper arithmetic circuits.
    
    Args:
        module: Input MLIR module containing Draper arithmetic
        **kwargs: Options passed to DraperOptimizer
        
    Returns:
        Optimized MLIR module
    """
    optimizer = DraperOptimizer(**kwargs)
    return optimizer.optimize_draper_circuit(module)
