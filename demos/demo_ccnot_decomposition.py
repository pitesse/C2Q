"""Demo: CCNOT decomposition

Builds a tiny MLIR module containing a single `quantum.OnQubit_ccnot` and runs the
optimizer to show that the CCNOT is replaced by an equivalent sequence of
`quantum.OnQubit_*` primitives.

Run:
  python demos/demo_ccnot_decomposition.py
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

from xdsl.context import Context
from xdsl.dialects.builtin import IntegerType, ModuleOp, VectorType
from xdsl.ir import Block, Region
from xdsl.printer import Printer

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from C2Q.dialects import quantum_dialect
from C2Q.dialects.quantum_dialect import FuncOp, InitOp, OnQubitCCnotOp
from C2Q.middle_end.optimizations import optimize_quantum_circuit


def build_ccnot_module() -> ModuleOp:
    ctx = Context()
    # quantum dialect for printing/parsing consistency.
    try:
        ctx.load_dialect(quantum_dialect.Quantum)
    except Exception:
        pass

    module = ModuleOp([])

    entry_block = Block()
    region = Region(entry_block)
    func = FuncOp("main", region)
    module.body.blocks[0].add_op(func)

    qtype = VectorType(IntegerType(1), [8])

    init1 = InitOp.from_value(qtype)
    entry_block.add_op(init1)
    c1 = init1.res

    init2 = InitOp.from_value(qtype)
    entry_block.add_op(init2)
    c2 = init2.res

    init3 = InitOp.from_value(qtype)
    entry_block.add_op(init3)
    tgt = init3.res

    ccnot = OnQubitCCnotOp.from_values(c1, 0, c2, 1, tgt, 2)
    entry_block.add_op(ccnot)

    _ = ccnot.res

    return module


def print_module(module: ModuleOp) -> str:
    buf = StringIO()
    Printer(stream=buf).print(module)
    return buf.getvalue()


def main() -> None:
    module = build_ccnot_module()

    before = print_module(module)
    optimized = optimize_quantum_circuit(
        module,
        optimization_level="aggressive",
        verbose=False,
    )
    after = print_module(optimized)

    print("=== BEFORE (contains OnQubit_ccnot) ===")
    print(before)

    print("=== AFTER (CCNOT decomposed) ===")
    print(after)

    before_has = "quantum.OnQubit_ccnot" in before
    after_has = "quantum.OnQubit_ccnot" in after

    print("=== CHECKS ===")
    print("OnQubit_ccnot present before?", before_has)
    print("OnQubit_ccnot present after? ", after_has)

    if not before_has:
        raise SystemExit("Expected demo IR to contain quantum.OnQubit_ccnot")
    if after_has:
        raise SystemExit("CCNOT decomposition did not eliminate quantum.OnQubit_ccnot")


if __name__ == "__main__":
    main()
