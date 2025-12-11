"""
Comprehensive Quantum Circuit Optimization Demo.

Demonstrates the integrated optimization framework that combines existing
optimization passes with new analysis capabilities.
"""

import subprocess
import sys
from pathlib import Path

def run_comparison(test_file: str, description: str):
    """Compare results with and without optimization."""
    print(f"\n{'='*70}")
    print(f"[INFO] {description}")
    print(f"[INFO] file: {test_file}")
    print('='*70)
    
    if not Path(test_file).exists():
        print(f"[ERROR] test file {test_file} not found")
        return
    
    metrics = {}
    
    # run without optimization
    print("[INFO] without optimization:")
    try:
        result = subprocess.run([
            sys.executable, "-m", "C2Q", test_file, "--no-optimize"
        ], capture_output=True, text=True, cwd="/home/linuxesse/C_to_Quantum")
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if "Gate Count:" in line:
                    metrics['gates_before'] = int(line.split(':')[1].strip())
                elif "Depth:" in line:
                    metrics['depth_before'] = int(line.split(':')[1].strip())
                elif "Width:" in line:
                    metrics['width_before'] = int(line.split(':')[1].strip())
            
            print(f"   gates: {metrics.get('gates_before', 'N/A')}")
            print(f"   depth: {metrics.get('depth_before', 'N/A')}")
            print(f"   width: {metrics.get('width_before', 'N/A')}")
        else:
            print(f"   [ERROR] error: {result.stderr}")
            
    except Exception as e:
        print(f"   [ERROR] exception: {e}")
    
    # run with optimization
    print("\n[INFO] with integrated optimization:")
    try:
        result = subprocess.run([
            sys.executable, "-m", "C2Q", test_file
        ], capture_output=True, text=True, cwd="/home/linuxesse/C_to_Quantum")
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            
            # extract optimization summary
            in_summary = False
            for line in lines:
                if "OPTIMIZATION SUMMARY" in line:
                    in_summary = True
                elif in_summary and "Operations:" in line and "→" in line:
                    print(f"   {line.strip()}")
                elif "Gate Count:" in line:
                    metrics['gates_after'] = int(line.split(':')[1].strip())
                elif "Depth:" in line:
                    metrics['depth_after'] = int(line.split(':')[1].strip())
                elif "Width:" in line:
                    metrics['width_after'] = int(line.split(':')[1].strip())
                elif "Passes applied:" in line:
                    print(f"   {line.strip()}")
            
            print(f"   gates: {metrics.get('gates_after', 'N/A')}")
            print(f"   depth: {metrics.get('depth_after', 'N/A')}")
            print(f"   width: {metrics.get('width_after', 'N/A')}")
            
            # calculate improvements
            if 'gates_before' in metrics and 'gates_after' in metrics:
                gate_improvement = metrics['gates_before'] - metrics['gates_after']
                gate_percent = (gate_improvement / metrics['gates_before']) * 100
                print(f"   [INFO] gate reduction: {gate_improvement} ({gate_percent:.1f}%)")
            
            if 'depth_before' in metrics and 'depth_after' in metrics:
                depth_improvement = metrics['depth_before'] - metrics['depth_after']
                depth_percent = (depth_improvement / metrics['depth_before']) * 100
                print(f"   [INFO] depth reduction: {depth_improvement} ({depth_percent:.1f}%)")
                
            if 'width_before' in metrics and 'width_after' in metrics:
                width_improvement = metrics['width_before'] - metrics['width_after']
                width_percent = (width_improvement / metrics['width_before']) * 100
                print(f"   [INFO] width reduction: {width_improvement} ({width_percent:.1f}%)")
        else:
            print(f"   [ERROR] error: {result.stderr}")
            
    except Exception as e:
        print(f"   [ERROR] exception: {e}")

def show_optimization_details():
    """Show details about the integrated optimization framework."""
    print("\n[INFO] INTEGRATED OPTIMIZATION FRAMEWORK")
    print("="*50)
    

def main():
    """Run comprehensive optimization demonstration."""
    
    print("[INFO] quantum circuit optimization demo")
    print("Showcasing Your Existing Optimizations + New Analysis")
    print("="*70)
    
    show_optimization_details()
    
    print("\n[INFO] TESTING OPTIMIZATION EFFECTIVENESS")
    print("="*50)
    
    test_cases = [
        ("test_add_new.c", "simple addition: 3 + 5 = 8"),
        ("test_sub_new.c", "simple subtraction: 8 - 3 = 5"), 
        ("test_debug_add.c", "zero operand case: 3 + 0 = 3"),
        ("test_draper.c", "complex Draper operations")
    ]
    
    for test_file, description in test_cases:
        run_comparison(test_file, description)
    
    print(f"\n{'='*70}")
    print("[INFO] OPTIMIZATION FRAMEWORK SUMMARY")  
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
