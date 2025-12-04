#!/usr/bin/env python3
"""
Test script to demonstrate quantum circuit optimizations.

This script compiles several test cases both with and without optimizations
to show the effectiveness of the optimization passes.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import C2Q
sys.path.append(str(Path(__file__).parent))

from C2Q.__main__ import main


def test_optimization_effectiveness():
    """
    Test the optimization passes on various arithmetic test cases.
    """
    print("🧪 Testing Quantum Circuit Optimization Effectiveness")
    print("=" * 60)
    
    test_files = [
        "test_add_new.c",
        "test_sub_new.c", 
        "test_debug_add.c",
        "test_draper.c"
    ]
    
    for test_file in test_files:
        file_path = Path(test_file)
        
        if not file_path.exists():
            print(f"❌ Test file {test_file} not found, skipping...")
            continue
            
        print(f"\n📁 Testing: {test_file}")
        print("-" * 40)
        
        # Test without optimization
        print("🚫 Without optimization:")
        try:
            main(file_path, "ir", False, False, optimize=False)
        except Exception as e:
            print(f"❌ Error without optimization: {e}")
        
        print("\n✨ With optimization:")
        try:
            main(file_path, "ir", False, False, optimize=True)
        except Exception as e:
            print(f"❌ Error with optimization: {e}")
        
        print("\n" + "="*60)


def demonstrate_specific_optimizations():
    """
    Show examples of specific optimizations that can be applied.
    """
    print("\n🔍 Quantum Circuit Optimization Examples")
    print("=" * 50)
    
    print("""
📋 **Gate Fusion & Cancellation**
   Before: X-X gates on same qubit → After: Both eliminated
   Before: H-H gates on same qubit → After: Both eliminated
   Savings: 2 gates eliminated per pair

📐 **Phase Consolidation** 
   Before: R(π/2), R(π/4) on same qubit → After: R(3π/4) 
   Savings: 1 gate eliminated per consolidation

🗑️  **Dead Qubit Elimination**
   Before: Unused registers from variable scoping
   After: Registers and dependent operations removed
   Savings: Entire register chains eliminated

⚡ **QFT Precision Optimization**
   Before: Full 8-bit precision for small values
   After: Reduced precision based on actual usage
   Savings: High-order operations eliminated

🎯 **Draper-Specific Optimizations**
   - Negligible phase rotations (< 1e-3) eliminated
   - Zero operand cases optimized (A + 0 = A)
   - Redundant SWAP operations removed
   - QFT depth reduced for small operands
""")


if __name__ == "__main__":
    """Run optimization tests and demonstrations."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demonstrate_specific_optimizations()
    else:
        test_optimization_effectiveness()
        demonstrate_specific_optimizations()
