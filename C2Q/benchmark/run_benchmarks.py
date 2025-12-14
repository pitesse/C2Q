"""
Benchmarking suite for C2Q compiler optimization evaluation.

This module provides comprehensive benchmarking capabilities for measuring
the impact of optimization passes on quantum circuit generation.

Usage:
    python -m C2Q.benchmark.run_benchmarks
"""

import os
import csv
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
from io import StringIO

from xdsl.printer import Printer
from xdsl.dialects.builtin import ModuleOp

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from C2Q.frontend.parser import CParser
from C2Q.frontend.ir_gen import QuantumIRGen
from C2Q.middle_end.optimizations import optimize_quantum_circuit
from C2Q.backend.run_qasm import get_quantum_circuit_info, create_circuit
from C2Q.backend.validate import validate_circuit


@dataclass
class BenchmarkResult:
    """Container for benchmark metrics from a single compilation run.

    Attributes:
        test_name: Name of the test case.
        optimization_level: Optimization level used ("none" or "default").
        mlir_op_count: Number of MLIR operations.
        total_gates: Total number of quantum gates.
        circuit_depth: Circuit depth.
        qubit_count: Number of qubits used.
        cnot_count: Number of CNOT gates.
        hadamard_count: Number of Hadamard gates.
        swap_count: Number of SWAP gates.
        phase_gates: Number of phase gates.
        validation_passed: Whether validation passed.
    """

    test_name: str
    optimization_level: str
    mlir_op_count: int
    total_gates: int
    circuit_depth: int
    qubit_count: int
    cnot_count: int
    hadamard_count: int
    swap_count: int
    phase_gates: int
    validation_passed: bool = True

    def improvement_percentage(self, baseline: "BenchmarkResult", metric: str) -> float:
        """Calculate percentage improvement over baseline for a given metric.

        Args:
            baseline: Baseline result to compare against.
            metric: Name of the metric attribute to compare.

        Returns:
            Percentage improvement (positive for reduction, negative for increase).
        """
        baseline_value = getattr(baseline, metric)
        optimized_value = getattr(self, metric)

        if baseline_value == 0:
            return 0.0

        return ((baseline_value - optimized_value) / baseline_value) * 100


# tdest suite configuration
TEST_SUITE = [
    {
        "name": "Add (8-bit)",
        "path": "tests/inputs/test_add.c",
        "description": "Addition: a=3, b=5, c=a+b",
        "expected_result": 8,
        "result_width": 8,
    },
    {
        "name": "Sub (8-bit)",
        "path": "tests/inputs/test_sub.c",
        "description": "Subtraction using Draper QFT",
        "expected_result": 5,
        "result_width": 8,
    },
    {
        "name": "Mult (Small 2×3)",
        "path": "tests/inputs/test_mult_2x3.c",
        "description": "Multiplication: 2×3 using repeated addition",
        "expected_result": 6,
        "result_width": 16,
    },
    # {
    #     "name": "Assignment",
    #     "path": "tests/inputs/test_assignment.c",
    #     "description": "Multiple assignment operations",
    #     "expected_result": 5,
    #     "result_width": 8,
    # },
    {
        "name": "Optimization Showcase",
        "path": "tests/inputs/test_optimization_showcase.c",
        "description": "Multiplication 5×3 with dead code, redundant ops, aggressive phase optimization",
        "expected_result": 15,
        "result_width": 16,
    },
    {
        "name": "Stress Test (Loop)",
        "path": "tests/inputs/test_stress_opt.c",
        "description": "Unrolled loop + cancelling ops - iterative optimization showcase",
        "expected_result": 4,
        "result_width": 8,
    },
    {
        "name": "Complex Math (Mixed Width)",
        "path": "tests/inputs/test_complex_math.c",
        "description": "Chained arithmetic: (3*2)+5 = 11, tests 16-bit mult → 16+8-bit addition",
        "expected_result": 11,
        "result_width": 16,
    },
    {
        "name": "Overflow (8-bit Wrap)",
        "path": "tests/inputs/test_overflow.c",
        "description": "Modular arithmetic: 255+1 = 0 (mod 256), tests 8-bit overflow behavior",
        "expected_result": 0,
        "result_width": 8,
    },
    {
        "name": "Mixed add/mult",
        "path": "tests/inputs/test_mixed_add.c",
        "description": "Mixed addition and multiplication: (2 * 3) + 5 = 11",
        "expected_result": 11,
        "result_width": 16,
    },
]


def compile_to_mlir(
    source_path: Path,
    optimization_level: str = "none",
    precision_threshold: float = 1e-6,
) -> ModuleOp:
    """
    Compile C source to MLIR with specified optimization level.

    Args:
        source_path: Path to C source file
        optimization_level: "none" (no optimization) or "default" (full optimization)
        precision_threshold: Phase precision threshold for approximate QFT (default: 1e-6, aggressive: 0.1)

    Returns:
        MLIR ModuleOp
    """
    with open(source_path) as f:
        parser = CParser(source_path, f.read())
        ast = parser.parseModule()

    ir_gen = QuantumIRGen()
    module_op = ir_gen.ir_gen_module(ast)

    if optimization_level == "default":
        module_op = optimize_quantum_circuit(
            module_op,
            optimization_level=optimization_level,
            analysis_only=False,
            verbose=False,
            precision_threshold=precision_threshold,
        )

    return module_op


def extract_mlir_metrics(module: ModuleOp) -> Dict[str, int]:
    """
    Extract metrics from MLIR module.

    Args:
        module: MLIR ModuleOp

    Returns:
        Dictionary with metric counts
    """
    op_count = len(list(module.walk()))
    return {"mlir_op_count": op_count}


def extract_qiskit_metrics(module: ModuleOp) -> Dict[str, int]:
    """
    Extract quantum circuit metrics using Qiskit.

    Args:
        module: MLIR ModuleOp

    Returns:
        Dictionary with circuit metrics
    """
    funcOp = None
    for op in module.body.block.ops:
        if op.name == "quantum.func":
            funcOp = op
            break

    if funcOp is None:
        raise ValueError("No quantum.func operation found in module")

    input_args = funcOp.regions[0].blocks[0]._args
    first_op = funcOp.regions[0].blocks[0]._first_op

    circuit_info = get_quantum_circuit_info(input_args, first_op)
    circuit = create_circuit(first_op, circuit_info["output_number"])

    # convert to dict with string keys for type safety
    raw_counts = circuit.count_ops()
    gate_counts: dict[str, int] = {str(k): v for k, v in raw_counts.items()}

    return {
        "total_gates": len(circuit),
        "circuit_depth": circuit.depth(),
        "qubit_count": circuit.num_qubits,
        "cnot_count": gate_counts.get("cx", 0),
        "hadamard_count": gate_counts.get("h", 0),
        "swap_count": gate_counts.get("swap", 0),
        "phase_gates": gate_counts.get("cp", 0) + gate_counts.get("p", 0),
    }


def save_mlir_artifact(module: ModuleOp, output_path: Path) -> None:
    """Save MLIR module to file.

    Args:
        module: MLIR ModuleOp to save.
        output_path: Path to output file.
    """
    buffer = StringIO()
    printer = Printer(stream=buffer)
    printer.print(module)

    with open(output_path, "w") as f:
        f.write(buffer.getvalue())


def run_benchmark(test_case: Dict) -> Tuple[BenchmarkResult, BenchmarkResult]:
    """
    Run benchmark for a single test case.

    Args:
        test_case: Test configuration dictionary

    Returns:
        Tuple of (baseline_result, optimized_result)
    """
    test_name = test_case["name"]
    source_path = Path(test_case["path"])

    print(f"  Benchmarking: {test_name}")
    print(f"    Source: {source_path}")

    print("    Running baseline (no optimization)...")
    baseline_module = compile_to_mlir(source_path, optimization_level="none")
    baseline_mlir_metrics = extract_mlir_metrics(baseline_module)
    baseline_qiskit_metrics = extract_qiskit_metrics(baseline_module)

    baseline_result = BenchmarkResult(
        test_name=test_name,
        optimization_level="none",
        mlir_op_count=baseline_mlir_metrics["mlir_op_count"],
        total_gates=baseline_qiskit_metrics["total_gates"],
        circuit_depth=baseline_qiskit_metrics["circuit_depth"],
        qubit_count=baseline_qiskit_metrics["qubit_count"],
        cnot_count=baseline_qiskit_metrics["cnot_count"],
        hadamard_count=baseline_qiskit_metrics["hadamard_count"],
        swap_count=baseline_qiskit_metrics["swap_count"],
        phase_gates=baseline_qiskit_metrics["phase_gates"],
    )

    print("    Running optimized (aggressive threshold=0.1)...")
    # π/32 ≈ 0.098, so threshold=0.1 eliminates rotations smaller than π/16
    # this creates an approximate QFT, a standard quantum optimization technique
    optimized_module = compile_to_mlir(
        source_path, optimization_level="default", precision_threshold=0.1
    )
    optimized_mlir_metrics = extract_mlir_metrics(optimized_module)
    optimized_qiskit_metrics = extract_qiskit_metrics(optimized_module)

    validation_passed: bool = True

    if "expected_result" in test_case:
        import time

        val_start = time.time()

        print("    Validating optimized circuit...")
        try:
            funcOp = None
            for op in optimized_module.body.block.ops:
                if op.name == "quantum.func":
                    funcOp = op
                    break

            if funcOp:
                input_args = funcOp.regions[0].blocks[0]._args
                first_op = funcOp.regions[0].blocks[0]._first_op
                circuit_info = get_quantum_circuit_info(input_args, first_op)
                circuit = create_circuit(first_op, circuit_info["output_number"])

                if circuit.num_qubits == 0 or len(circuit.data) == 0:
                    print(
                        f"    [ERROR] Generated circuit for {test_name} is empty/invalid"
                    )
                    validation_passed = False
                else:
                    print(
                        f"    [INFO] Checking circuit: {len(circuit.data)} ops, {circuit.num_qubits} qubits"
                    )

                    print(f"    [INFO] Circuit fingerprint for {test_name}:")
                    print(f"       - Qubits: {circuit.num_qubits}")
                    print(f"       - Depth: {circuit.depth()}")
                    print(f"       - Total Ops: {len(circuit.data)}")
                    print(f"       - Ops Breakdown: {circuit.count_ops()}")

                    print(
                        f"    [INFO] Validating circuit with depth {circuit.depth()} (Baseline was {baseline_result.circuit_depth})"
                    )
                    if circuit.depth() > baseline_result.circuit_depth:
                        print(f"    [WARN] Optimized circuit is deeper than baseline")
                    if len(circuit.data) > baseline_result.total_gates:
                        print(
                            f"    [WARN] Optimized circuit has more gates than baseline"
                        )

                    # use standardized validation function (same logic as CLI)
                    result_width = test_case.get("result_width", 8)
                    is_signed = "Sub" in test_name
                    expected_result = test_case["expected_result"]

                    validation_passed = validate_circuit(
                        circuit=circuit,
                        expected_result=expected_result,
                        verbose=False,
                        signed=is_signed,
                        result_width=result_width,
                    )

                    val_time = time.time() - val_start
                    print(f"    [INFO] Validation took {val_time:.2f}s")
            else:
                print("    [WARN] No quantum.func found for validation")
                validation_passed = False
        except Exception as e:
            print(f"    [WARN] Validation error: {e}")
            import traceback

            traceback.print_exc()
            validation_passed = False

    optimized_result = BenchmarkResult(
        test_name=test_name,
        optimization_level="default",
        mlir_op_count=optimized_mlir_metrics["mlir_op_count"],
        total_gates=optimized_qiskit_metrics["total_gates"],
        circuit_depth=optimized_qiskit_metrics["circuit_depth"],
        qubit_count=optimized_qiskit_metrics["qubit_count"],
        cnot_count=optimized_qiskit_metrics["cnot_count"],
        hadamard_count=optimized_qiskit_metrics["hadamard_count"],
        swap_count=optimized_qiskit_metrics["swap_count"],
        phase_gates=optimized_qiskit_metrics["phase_gates"],
        validation_passed=validation_passed,
    )

    artifacts_dir = Path("benchmarks_data")
    artifacts_dir.mkdir(exist_ok=True)

    safe_name = (
        test_name.replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("×", "x")
        .replace("/", "-")
    )
    save_mlir_artifact(baseline_module, artifacts_dir / f"{safe_name}_base.mlir")
    save_mlir_artifact(optimized_module, artifacts_dir / f"{safe_name}_opt.mlir")

    print(
        f"    [PASS] Baseline:  {baseline_result.total_gates} gates, depth {baseline_result.circuit_depth}"
    )
    print(
        f"    [PASS] Optimized: {optimized_result.total_gates} gates, depth {optimized_result.circuit_depth}"
    )
    print()

    return baseline_result, optimized_result


def save_results_csv(
    results: List[Tuple[BenchmarkResult, BenchmarkResult]], output_path: Path
) -> None:
    """
    Save benchmark results to CSV file.

    Args:
        results: List of (baseline, optimized) result pairs
        output_path: Path to output CSV file
    """
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "Test Name",
                "Base MLIR Ops",
                "Opt MLIR Ops",
                "MLIR Reduction %",
                "Base Gates",
                "Opt Gates",
                "Gate Reduction %",
                "Base Depth",
                "Opt Depth",
                "Depth Reduction %",
                "Base Qubits",
                "Opt Qubits",
                "Base CNOTs",
                "Opt CNOTs",
                "CNOT Reduction %",
                "Base Hadamards",
                "Opt Hadamards",
                "Base SWAPs",
                "Opt SWAPs",
                "Base Phase Gates",
                "Opt Phase Gates",
            ]
        )

        # data rows
        for baseline, optimized in results:
            writer.writerow(
                [
                    baseline.test_name,
                    baseline.mlir_op_count,
                    optimized.mlir_op_count,
                    f"{optimized.improvement_percentage(baseline, 'mlir_op_count'):.1f}",
                    baseline.total_gates,
                    optimized.total_gates,
                    f"{optimized.improvement_percentage(baseline, 'total_gates'):.1f}",
                    baseline.circuit_depth,
                    optimized.circuit_depth,
                    f"{optimized.improvement_percentage(baseline, 'circuit_depth'):.1f}",
                    baseline.qubit_count,
                    optimized.qubit_count,
                    baseline.cnot_count,
                    optimized.cnot_count,
                    f"{optimized.improvement_percentage(baseline, 'cnot_count'):.1f}",
                    baseline.hadamard_count,
                    optimized.hadamard_count,
                    baseline.swap_count,
                    optimized.swap_count,
                    baseline.phase_gates,
                    optimized.phase_gates,
                ]
            )


def print_comparison_table(
    results: List[Tuple[BenchmarkResult, BenchmarkResult]],
) -> None:
    """
    Print formatted comparison table to console.

    Args:
        results: List of (baseline, optimized) result pairs
    """
    print("=" * 100)
    print("BENCHMARK RESULTS: Optimization Impact Analysis")
    print("=" * 100)
    print()

    for baseline, optimized in results:
        validation_indicator = ""
        if hasattr(optimized, "validation_passed"):
            if optimized.validation_passed:
                validation_indicator = " [PASS]"
            else:
                validation_indicator = " [FAIL]"

        print(f"Test: {baseline.test_name}{validation_indicator}")
        print("-" * 100)

        metrics = [
            ("MLIR Operations", "mlir_op_count"),
            ("Total Gates", "total_gates"),
            ("Circuit Depth", "circuit_depth"),
            # ("Qubit Count", "qubit_count"),
            # ("CNOT Gates", "cnot_count"),
            ("Hadamard Gates", "hadamard_count"),
            # ("SWAP Gates", "swap_count"),
            ("Phase Gates", "phase_gates"),
        ]

        print(f"{'Metric':<25} {'Baseline':<15} {'Optimized':<15} {'Improvement':<15}")
        print("-" * 100)

        for metric_name, metric_key in metrics:
            baseline_val = getattr(baseline, metric_key)
            optimized_val = getattr(optimized, metric_key)
            improvement = optimized.improvement_percentage(baseline, metric_key)

            if improvement > 0:
                improvement_str = f"↓ {improvement:.1f}%"
            elif improvement < 0:
                improvement_str = f"↑ {abs(improvement):.1f}%"
            else:
                improvement_str = "="

            print(
                f"{metric_name:<25} {baseline_val:<15} {optimized_val:<15} {improvement_str:<15}"
            )

        print()

    print("=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)

    avg_gate_reduction = sum(
        opt.improvement_percentage(base, "total_gates") for base, opt in results
    ) / len(results)

    avg_depth_reduction = sum(
        opt.improvement_percentage(base, "circuit_depth") for base, opt in results
    ) / len(results)

    avg_mlir_reduction = sum(
        opt.improvement_percentage(base, "mlir_op_count") for base, opt in results
    ) / len(results)

    print(f"Average Gate Count Reduction:    {avg_gate_reduction:.1f}%")
    print(f"Average Circuit Depth Reduction: {avg_depth_reduction:.1f}%")
    print(f"Average MLIR Op Reduction:       {avg_mlir_reduction:.1f}%")
    print()


def run_all_benchmarks() -> List[Tuple[BenchmarkResult, BenchmarkResult]]:
    """
    Run complete benchmark suite.

    Returns:
        List of (baseline, optimized) result pairs
    """
    print("=" * 100)
    print("C2Q COMPILER OPTIMIZATION BENCHMARK SUITE")
    print("=" * 100)
    print()

    results = []

    artifacts_dir = Path("benchmarks_data")
    artifacts_dir.mkdir(exist_ok=True)
    print(f"[INFO] Artifacts directory: {artifacts_dir.absolute()}")
    print()

    # run each test case
    for test_case in TEST_SUITE:
        try:
            baseline, optimized = run_benchmark(test_case)
            results.append((baseline, optimized))
        except FileNotFoundError as e:
            print(
                f"  [WARN] Skipping {test_case['name']}: File not found - {test_case['path']}"
            )
            print()
            continue
        except Exception as e:
            print(f"  [ERROR] Error running {test_case['name']}: {e}")
            print()
            continue

    if not results:
        print("[ERROR] No benchmarks completed successfully")
        return []

    csv_path = artifacts_dir / "results.csv"
    save_results_csv(results, csv_path)
    print(f"[PASS] Results saved to: {csv_path.absolute()}")
    print()

    print_comparison_table(results)

    total_tests = len(results)
    validated_tests = sum(
        1
        for _, opt in results
        if hasattr(opt, "validation_passed") and opt.validation_passed
    )
    failed_validations = sum(
        1
        for _, opt in results
        if hasattr(opt, "validation_passed") and not opt.validation_passed
    )

    print("=" * 100)
    if failed_validations > 0:
        print(
            f"[WARN] Benchmark suite completed: {len(results)}/{len(TEST_SUITE)} tests, {validated_tests} validated, {failed_validations} failed validation"
        )
    else:
        print(
            f"[PASS] Benchmark suite completed: {len(results)}/{len(TEST_SUITE)} tests successful, all validations passed"
        )
    print("=" * 100)

    return results


if __name__ == "__main__":
    run_all_benchmarks()
