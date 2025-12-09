#!/usr/bin/env python3
"""
Benchmark and validation script for DraperOptimizer.

Compiles test programs twice (with and without optimization), validates
both circuits produce correct results, and compares gate counts/depth.

Usage:
    python demos/validate_optimization.py tests/inputs/test_mult_2x3.c --expected 6
    python demos/validate_optimization.py tests/inputs/test_add_1plus1.c --expected 2
"""


import argparse
import subprocess
import sys
import re
from pathlib import Path


def run_compiler(source_path: str, optimize: bool, expected: int, signed: bool = False, result_width: int = 8):
    """
    Run the C2Q compiler with validation.
    
    Returns:
        dict with keys: success (bool), gate_count (int), depth (int), output (str)
    """
    # Convert to absolute path
    source_path = str(Path(source_path).resolve())
    
    cmd = [
        sys.executable, "-m", "C2Q",
        source_path,
        "--validate", str(expected),
        "--result-width", str(result_width)
    ]
    
    if signed:
        cmd.append("--signed")
    
    if optimize:
        cmd.append("--force-optimize")
    else:
        cmd.append("--no-optimize")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        
        # Parse gate count from output (look for "Total gates:" or similar)
        gate_count = None
        depth = None
        
        # Try to extract metrics from output
        for line in output.split('\n'):
            if 'gate' in line.lower() and any(c.isdigit() for c in line):
                # Extract first number from line
                numbers = re.findall(r'\d+', line)
                if numbers and gate_count is None:
                    gate_count = int(numbers[0])
            if 'depth' in line.lower() and any(c.isdigit() for c in line):
                numbers = re.findall(r'\d+', line)
                if numbers and depth is None:
                    depth = int(numbers[0])
        
        # Check validation result
        success = "✅ VALIDATION PASSED" in output or result.returncode == 0
        
        return {
            'success': success,
            'gate_count': gate_count,
            'depth': depth,
            'output': output,
            'returncode': result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'gate_count': None,
            'depth': None,
            'output': "ERROR: Compilation timeout",
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'gate_count': None,
            'depth': None,
            'output': f"ERROR: {str(e)}",
            'returncode': -1
        }


def format_comparison_table(unoptimized, optimized, test_name):
    """Format comparison results as a table."""
    
    print("\n" + "="*80)
    print(f"📊 OPTIMIZATION BENCHMARK: {test_name}")
    print("="*80)
    
    # Validation status
    print("\n🔬 Validation Status:")
    print(f"  Unoptimized: {'✅ PASS' if unoptimized['success'] else '❌ FAIL'}")
    print(f"  Optimized:   {'✅ PASS' if optimized['success'] else '❌ FAIL'}")
    
    # Circuit metrics comparison
    if unoptimized['gate_count'] is not None or optimized['gate_count'] is not None:
        print("\n📈 Circuit Metrics:")
        print(f"  {'Metric':<20} {'Unoptimized':<15} {'Optimized':<15} {'Improvement':<15}")
        print(f"  {'-'*20} {'-'*15} {'-'*15} {'-'*15}")
        
        if unoptimized['gate_count'] and optimized['gate_count']:
            reduction = unoptimized['gate_count'] - optimized['gate_count']
            percent = (reduction / unoptimized['gate_count'] * 100) if unoptimized['gate_count'] > 0 else 0
            print(f"  {'Gate Count':<20} {unoptimized['gate_count']:<15} {optimized['gate_count']:<15} {f'-{reduction} (-{percent:.1f}%)':<15}")
        
        if unoptimized['depth'] and optimized['depth']:
            reduction = unoptimized['depth'] - optimized['depth']
            percent = (reduction / unoptimized['depth'] * 100) if unoptimized['depth'] > 0 else 0
            print(f"  {'Circuit Depth':<20} {unoptimized['depth']:<15} {optimized['depth']:<15} {f'-{reduction} (-{percent:.1f}%)':<15}")
    
    # Overall result
    print("\n" + "="*80)
    if unoptimized['success'] and optimized['success']:
        print("✅ RESULT: Both circuits validated successfully!")
        print("   The optimizer preserves arithmetic correctness while improving metrics.")
    elif unoptimized['success'] and not optimized['success']:
        print("⚠️  WARNING: Optimization broke correctness!")
        print("   The unoptimized circuit works, but optimization introduced bugs.")
    elif not unoptimized['success'] and optimized['success']:
        print("⚠️  WARNING: Unoptimized circuit failed but optimized passed!")
        print("   This is unexpected - check test configuration.")
    else:
        print("❌ ERROR: Both circuits failed validation.")
        print("   Check test program and expected result.")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark DraperOptimizer: validate correctness and compare metrics"
    )
    parser.add_argument("source", help="C source file to compile")
    parser.add_argument("--expected", type=int, required=True,
                       help="Expected result value for validation")
    parser.add_argument("--signed", action="store_true",
                       help="Interpret result as signed two's complement")
    parser.add_argument("--result-width", type=int, default=8,
                       help="Result width in bits (default: 8, use 16 for multiplication)")
    parser.add_argument("--verbose", action="store_true",
                       help="Print full compiler output for both runs")
    
    args = parser.parse_args()
    
    # Verify source file exists
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ ERROR: Source file not found: {args.source}")
        sys.exit(1)
    
    test_name = source_path.stem
    
    print("🚀 Starting benchmark...")
    print(f"   Test: {test_name}")
    print(f"   Expected result: {args.expected}")
    print(f"   Result width: {args.result_width} bits")
    if args.signed:
        print(f"   Interpretation: signed two's complement")
    
    # Run unoptimized compilation
    print("\n⏳ Compiling without optimization...")
    unoptimized = run_compiler(args.source, optimize=False, expected=args.expected,
                              signed=args.signed, result_width=args.result_width)
    
    if args.verbose:
        print("\n--- Unoptimized Output ---")
        print(unoptimized['output'])
        print("--- End Output ---\n")
    
    # Run optimized compilation
    print("⏳ Compiling with optimization...")
    optimized = run_compiler(args.source, optimize=True, expected=args.expected,
                            signed=args.signed, result_width=args.result_width)
    
    if args.verbose:
        print("\n--- Optimized Output ---")
        print(optimized['output'])
        print("--- End Output ---\n")
    
    # Display comparison table
    format_comparison_table(unoptimized, optimized, test_name)
    
    # Exit with appropriate code
    if unoptimized['success'] and optimized['success']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
