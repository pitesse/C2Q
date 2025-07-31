#!/usr/bin/env python3
"""
Quick demonstration of quantum circuit analysis features.
"""

import subprocess
import sys

def show_circuit_analysis(test_file: str):
    """Show detailed circuit analysis for a test file."""
    print(f"\n🔍 Analyzing {test_file}")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "C2Q", test_file
        ], capture_output=True, text=True, cwd="/home/linuxesse/C_to_Quantum")
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            
            # Extract analysis sections
            for line in lines:
                if any(marker in line for marker in [
                    "Operation Distribution:",
                    "Phase rotation ratio:",
                    "Circuit complexity:",
                    "Optimization Summary",
                    "Operations:",
                    "Depth:",
                    "Width:",
                    "High phase rotation density",
                    "Added:"
                ]):
                    print(f"   {line}")
        else:
            print(f"❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    print("⚡ Quick Circuit Analysis Demo")
    print("=" * 40)
    
    test_files = ["test_add_new.c", "test_draper.c"]
    
    for test_file in test_files:
        show_circuit_analysis(test_file)
    
    print(f"\n{'=' * 40}")
    print("✅ Your optimization framework provides:")
    print("   • Detailed circuit analysis")
    print("   • Resource usage optimization")
    print("   • Pattern-based improvements")
    print("   • Hardware compatibility enhancements")

if __name__ == "__main__":
    main()
