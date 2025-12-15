"""
Quantum Register Naming Pass

This pass restores human-readable qN_M naming convention for debugging purposes.
It operates as a post-processing step after all IR generation is complete.

The naming convention:
- qN: Register number N (based on initialization order)
- _M: Version number M (incremented for each operation that modifies the register) - SSA

This ensures the final .mlir output is readable while keeping the core IR generation
logic clean and free from manual string manipulation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xdsl.ir import SSAValue, Operation
    from xdsl.dialects.builtin import ModuleOp

from ...dialects.quantum_dialect import InitOp


class QuantumRegisterNamer:
    """
    Post-processing pass that assigns qN_M names to quantum registers.

    This pass walks the ModuleOp and assigns human-readable names to quantum
    registers based on their SSA use-def chains:

    1. Identifies quantum.init operations as the start of register chains
    2. Assigns qX_0 to init results (X = register counter)
    3. Traverses use-def chains to propagate names with incremented versions
    4. Ensures output MLIR has readable register names for debugging

    Usage:
        namer = QuantumRegisterNamer()
        namer.apply(module)
    """

    def __init__(self):
        """Initialize the register namer with fresh counters."""
        self.register_counter = 0
        self.value_to_name: dict[SSAValue, str] = {}

    def apply(self, module: "ModuleOp") -> None:
        """
        Apply naming pass to the entire module.

        Args:
            module: The MLIR ModuleOp to process
        """
        self.register_counter = 0
        self.value_to_name = {}

        # walk all operations in the module
        self._walk_op(module)

    def _walk_op(self, op: "Operation") -> None:
        """
        Recursively walk an operation and its nested regions.

        Args:
            op: The operation to process
        """
        if isinstance(op, InitOp):
            # this is an init operation, start a new register chain
            self._name_init_result(op)
        else:
            # for other operations, propagate names from operands to results
            self._propagate_names(op)

        # recursively process nested regions (for func ops, ...)
        for region in op.regions:
            for block in region.blocks:
                for nested_op in block.ops:
                    self._walk_op(nested_op)

    def _name_init_result(self, op: InitOp) -> None:
        """
        Assign initial name to an init operation's result.

        Args:
            op: The InitOp to name
        """
        if hasattr(op, "res") and op.res is not None:
            name = f"q{self.register_counter}_0"
            op.res._name = name
            self.value_to_name[op.res] = name
            self.register_counter += 1

    def _propagate_names(self, op: "Operation") -> None:
        """
        Propagate names from operands to results, incrementing version numbers.

        For operations that take a quantum register as input and produce a new
        register as output (gates, etc.), this propagates the register name
        with an incremented version number.

        Args:
            op: The operation to process
        """
        # skip operations without results
        if not hasattr(op, "results") or not op.results:
            return

        # find quantum register operands (those with names)
        named_operands = []
        if hasattr(op, "operands"):
            for operand in op.operands:
                if operand in self.value_to_name:
                    named_operands.append(operand)

        # if we have named operands, propagate to results
        if named_operands:
            # use the first named operand as the source
            source = named_operands[0]
            source_name = self.value_to_name[source]

            # parse the source name to extract register number and version
            try:
                parts = source_name.split("_")
                if len(parts) == 2 and parts[0].startswith("q"):
                    register_num = parts[0][1:]  # remove 'q' prefix
                    version_num = int(parts[1])

                    # assign incremented names to all results
                    for i, result in enumerate(op.results):
                        new_version = version_num + 1 + i
                        new_name = f"q{register_num}_{new_version}"
                        result._name = new_name
                        self.value_to_name[result] = new_name
            except (ValueError, IndexError):
                # if parsing fails, skip naming for this op
                print(f"Warning: Could not parse register name '{source_name}'")
                pass
