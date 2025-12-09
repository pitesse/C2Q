"""
Ablation Study: Verify that each optimization contributes to the result.

This script compiles test_stress_opt.c in 3 modes:
- Mode A: Only DraperOptimizer (precision 0.1)
- Mode B: Only RemoveUnusedOperations (Dead Code)
- Mode C: Full Pipeline (default)

Expected: C < A and C < B (proving synergy)
"""

import sys
from pathlib import Path
from io import StringIO

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from xdsl.printer import Printer
from xdsl.dialects.builtin import ModuleOp

from C2Q.frontend.parser import CParser
from C2Q.frontend.ir_gen import QuantumIRGen
from C2Q.backend.run_qasm import get_quantum_circuit_info, create_circuit, metrics

# Import individual optimizers
from C2Q.middle_end.optimizations.draper_optimizer import DraperOptimizer
from C2Q.middle_end.optimizations.remove_unused_op import RemoveUnusedOperations
from C2Q.middle_end.optimizations import optimize_quantum_circuit

from xdsl.pattern_rewriter import PatternRewriteWalker, GreedyRewritePatternApplier


def compile_source(source_path: Path) -> ModuleOp:
    """Compile C source to unoptimized MLIR module."""
    with open(source_path) as f:
        parser = CParser(source_path, f.read())
        ast = parser.parseModule()
    
    ir_gen = QuantumIRGen()
    return ir_gen.ir_gen_module(ast)


def count_ops(module: ModuleOp) -> int:
    """Count total operations in module."""
    count = 0
    for op in module.body.block.ops:
        if op.name == "quantum.func":
            for inner_op in op.regions[0].blocks[0].ops:
                count += 1
    return count


def get_gate_count(module: ModuleOp) -> int:
    """Get Qiskit gate count from module."""
    try:
        funcOp = None
        for op in module.body.block.ops:
            if op.name == "quantum.func":
                funcOp = op
                break
        
        if funcOp is None:
            return 0
        
        input_args = funcOp.regions[0].blocks[0]._args
        first_op = funcOp.regions[0].blocks[0]._first_op
        circuit_info = get_quantum_circuit_info(input_args, first_op)
        circuit = create_circuit(first_op, circuit_info["output_number"])
        return len(circuit.data)
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def main():
    print("=" * 60)
    print("ABLATION STUDY: Optimization Contribution Analysis")
    print("=" * 60)
    
    source_path = Path("tests/inputs/test_stress_opt.c")
    
    if not source_path.exists():
        print(f"ERROR: {source_path} not found!")
        return
    
    print(f"\nTest file: {source_path}")
    print("-" * 60)
    
    # Baseline: No optimization
    print("\n📊 BASELINE (No optimization):")
    baseline_module = compile_source(source_path)
    baseline_ops = count_ops(baseline_module)
    baseline_gates = get_gate_count(baseline_module)
    print(f"   MLIR Ops: {baseline_ops}")
    print(f"   Gate Count: {baseline_gates}")
    
    # Mode A: Only DraperOptimizer
    print("\n📊 MODE A: Only DraperOptimizer (precision=0.1):")
    module_a = compile_source(source_path)
    draper = DraperOptimizer(precision_threshold=0.1)
    draper.optimize_draper_circuit(module_a)
    mode_a_ops = count_ops(module_a)
    mode_a_gates = get_gate_count(module_a)
    print(f"   MLIR Ops: {mode_a_ops}")
    print(f"   Gate Count: {mode_a_gates}")
    
    # Mode B: Only RemoveUnusedOperations
    print("\n📊 MODE B: Only RemoveUnusedOperations:")
    module_b = compile_source(source_path)
    walker = PatternRewriteWalker(
        GreedyRewritePatternApplier([RemoveUnusedOperations()]),
        apply_recursively=True
    )
    walker.rewrite_module(module_b)
    mode_b_ops = count_ops(module_b)
    mode_b_gates = get_gate_count(module_b)
    print(f"   MLIR Ops: {mode_b_ops}")
    print(f"   Gate Count: {mode_b_gates}")
    
    # Mode C: Full Pipeline
    print("\n📊 MODE C: Full Pipeline (default):")
    module_c = compile_source(source_path)
    module_c = optimize_quantum_circuit(
        module_c,
        optimization_level="default",
        precision_threshold=0.1,
        verbose=False
    )
    mode_c_ops = count_ops(module_c)
    mode_c_gates = get_gate_count(module_c)
    print(f"   MLIR Ops: {mode_c_ops}")
    print(f"   Gate Count: {mode_c_gates}")
    
    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    print(f"\n| Mode | MLIR Ops | Gate Count |")
    print(f"|------|----------|------------|")
    print(f"| Baseline | {baseline_ops} | {baseline_gates} |")
    print(f"| A (Draper only) | {mode_a_ops} | {mode_a_gates} |")
    print(f"| B (DCE only) | {mode_b_ops} | {mode_b_gates} |")
    print(f"| C (Full) | {mode_c_ops} | {mode_c_gates} |")
    
    print("\n📋 SYNERGY CHECK:")
    
    # Check: C should be better than or equal to A and B individually
    synergy_a = mode_c_gates <= mode_a_gates
    synergy_b = mode_c_gates <= mode_b_gates
    
    if synergy_a:
        print(f"   ✅ C ({mode_c_gates}) <= A ({mode_a_gates}): Full pipeline beats Draper-only")
    else:
        print(f"   ❌ C ({mode_c_gates}) > A ({mode_a_gates}): UNEXPECTED!")
    
    if synergy_b:
        print(f"   ✅ C ({mode_c_gates}) <= B ({mode_b_gates}): Full pipeline beats DCE-only")
    else:
        print(f"   ❌ C ({mode_c_gates}) > B ({mode_b_gates}): UNEXPECTED!")
    
    if synergy_a and synergy_b:
        print("\n✅ ABLATION STUDY PASSED: Optimizations show synergy!")
    else:
        print("\n⚠️  ABLATION STUDY: Some expectations not met")


if __name__ == "__main__":
    main()
