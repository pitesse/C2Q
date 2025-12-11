"""
Quantum Arithmetic Module for C2Q Compiler

This module implements Draper QFT-based quantum arithmetic operations including
addition, subtraction, and multiplication. The algorithms use the Quantum Fourier
Transform to perform arithmetic in the frequency domain.

Reference:
    Draper, T. G. (2000). Addition on a Quantum Computer. arXiv:quant-ph/0008033

CRITICAL DESIGN NOTE:
    Every method accepts `builder` as its FIRST argument to ensure operations
    are inserted at the correct insertion point (inside the current function block).
    DO NOT store builder in __init__ - this causes the "stale builder" bug where
    operations get inserted at module scope instead of inside the function.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from xdsl.ir import SSAValue
    from xdsl.builder import Builder
    from xdsl.dialects.builtin import VectorType

from ..dialects.quantum_dialect import (
    OnQubitHadamardOp,
    OnQubitControlledPhaseOp,
    OnQubitSwapOp,
    OnQubitPhaseOp,
    OnQubitCNotOp,
    OnQubitCCnotOp,
)


class QuantumArithmetic:
    """
    Implements Draper QFT-based quantum arithmetic operations.

    This class encapsulates all quantum gate operations and arithmetic algorithms
    used by the C2Q compiler. Each method accepts a `builder` parameter to ensure
    operations are inserted at the correct point in the IR.

    CRITICAL: Do NOT store builder in __init__. Pass it to every method.
    """

    def __init__(self):
        """
        Initialize the quantum arithmetic module.

        NOTE: We intentionally do NOT store the builder here.
        The builder must be passed to each method to ensure operations
        are inserted at the current insertion point.
        """
        pass

    # =========================================================================
    # naming helper
    # =========================================================================

    @staticmethod
    def _propagate_name(source: "SSAValue", target: "SSAValue") -> None:
        """
        Propagate and increment SSA naming from source to target register.

        Maintains the qX_Y naming convention where X is the register number
        and Y is the version number (incremented on each operation).
        """
        if hasattr(source, "_name") and source._name:
            parts = source._name.split("_")
            if len(parts) == 2:
                register_num = parts[0].lstrip("q")
                version_num = int(parts[1]) + 1
                target._name = f"q{register_num}_{version_num}"

    # =========================================================================
    # basic quantum gates
    # =========================================================================

    def apply_hadamard_gate(
        self, builder: "Builder", register: "SSAValue", qubit_index: int
    ) -> "SSAValue":
        """
        Apply Hadamard gate to a specific qubit in the register.
        H|0⟩ = (|0⟩ + |1⟩)/√2, H|1⟩ = (|0⟩ - |1⟩)/√2

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            register: The multi-qubit register
            qubit_index: Index of the qubit to apply Hadamard to

        Returns:
            The updated register after applying the Hadamard gate
        """
        result = builder.insert(OnQubitHadamardOp.from_value(register, qubit_index)).res
        self._propagate_name(register, result)
        return result

    def apply_controlled_phase_rotation(
        self,
        builder: "Builder",
        control_register: "SSAValue",
        control_index: int,
        target_register: "SSAValue",
        target_index: int,
        phase_angle: float,
    ) -> "SSAValue":
        """
        Apply controlled phase rotation.
        |control⟩|target⟩ → |control⟩|target⟩ if control=0
                          → |control⟩e^(iθ)|target⟩ if control=1

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            control_register: Register containing the control qubit
            control_index: Index of the control qubit
            target_register: Register containing the target qubit
            target_index: Index of the target qubit
            phase_angle: Phase rotation angle in radians

        Returns:
            The updated target register
        """
        result = builder.insert(
            OnQubitControlledPhaseOp.from_values(
                control_register,
                control_index,
                target_register,
                target_index,
                phase_angle,
            )
        ).res
        self._propagate_name(target_register, result)
        return result

    def apply_swap_gate(
        self, builder: "Builder", register: "SSAValue", qubit1: int, qubit2: int
    ) -> "SSAValue":
        """
        Swap two qubits using the dedicated swap operation.
        SWAP|ab⟩ = |ba⟩

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            register: The multi-qubit register
            qubit1: Index of the first qubit
            qubit2: Index of the second qubit

        Returns:
            The updated register after swapping
        """
        result = builder.insert(OnQubitSwapOp.from_values(register, qubit1, qubit2)).res
        self._propagate_name(register, result)
        return result

    def apply_phase_gate(
        self, builder: "Builder", register: "SSAValue", qubit_index: int, phase: float
    ) -> "SSAValue":
        """
        Apply a single-qubit phase rotation gate.
        P(θ)|0⟩ = |0⟩, P(θ)|1⟩ = e^(iθ)|1⟩

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            register: The multi-qubit register
            qubit_index: Index of the qubit
            phase: Phase rotation angle in radians

        Returns:
            The updated register
        """
        result = builder.insert(
            OnQubitPhaseOp.from_value(register, qubit_index, phase)
        ).res
        self._propagate_name(register, result)
        return result

    def apply_cnot_on_bits(
        self,
        builder: "Builder",
        control_register: "SSAValue",
        control_index: int,
        target_register: "SSAValue",
        target_index: int,
    ) -> "SSAValue":
        """
        Apply a CNOT gate directly between bits in two registers.

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            control_register: The register containing the control qubit
            control_index: The index of the control bit
            target_register: The register containing the target qubit
            target_index: The index of the target bit

        Returns:
            The updated target register after applying CNOT
        """
        result = builder.insert(
            OnQubitCNotOp.from_values(
                control_register, control_index, target_register, target_index
            )
        ).res
        self._propagate_name(target_register, result)
        return result

    def apply_ccnot_on_bits(
        self,
        builder: "Builder",
        control1_register: "SSAValue",
        control1_index: int,
        control2_register: "SSAValue",
        control2_index: int,
        target_register: "SSAValue",
        target_index: int,
    ) -> "SSAValue":
        """
        Apply a CCNOT (Toffoli) gate directly between bits in three registers.

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            control1_register: The register containing the first control qubit
            control1_index: The index of the first control bit
            control2_register: The register containing the second control qubit
            control2_index: The index of the second control bit
            target_register: The register containing the target qubit
            target_index: The index of the target bit

        Returns:
            The updated target register after applying CCNOT
        """
        result = builder.insert(
            OnQubitCCnotOp.from_values(
                control1_register,
                control1_index,
                control2_register,
                control2_index,
                target_register,
                target_index,
            )
        ).res
        self._propagate_name(target_register, result)
        return result

    # =========================================================================
    # composite gates
    # =========================================================================

    def reverse_qubit_order(
        self, builder: "Builder", register: "SSAValue", n_qubits: int
    ) -> "SSAValue":
        """
        Reverse the order of qubits in a register using SWAP gates.

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            register: The multi-qubit register
            n_qubits: Number of qubits in the register

        Returns:
            The register with reversed qubit order
        """
        result = register
        for i in range(n_qubits // 2):
            j = n_qubits - 1 - i
            result = self.apply_swap_gate(builder, result, i, j)
        return result

    def apply_ccphase(
        self,
        builder: "Builder",
        control1_reg: "SSAValue",
        control1_bit: int,
        control2_reg: "SSAValue",
        control2_bit: int,
        target_reg: "SSAValue",
        target_bit: int,
        phase_angle: float,
    ) -> "SSAValue":
        """
        Apply doubly-controlled phase gate: CCPhase(theta).
        Only applies phase if BOTH control qubits are |1⟩.

        Decomposition:
        1. CP(theta/2, control2, target)
        2. CNOT(control1, control2)
        3. CP(-theta/2, control2, target)
        4. CNOT(control1, control2)
        5. CP(theta/2, control1, target)

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            control1_reg: First control register
            control1_bit: First control bit index
            control2_reg: Second control register
            control2_bit: Second control bit index
            target_reg: Target register
            target_bit: Target bit index
            phase_angle: Phase angle theta

        Returns:
            Updated target register
        """
        result = target_reg

        result = self.apply_controlled_phase_rotation(
            builder, control2_reg, control2_bit, result, target_bit, phase_angle / 2
        )

        control2_reg = self.apply_cnot_on_bits(
            builder, control1_reg, control1_bit, control2_reg, control2_bit
        )

        result = self.apply_controlled_phase_rotation(
            builder, control2_reg, control2_bit, result, target_bit, -phase_angle / 2
        )

        control2_reg = self.apply_cnot_on_bits(
            builder, control1_reg, control1_bit, control2_reg, control2_bit
        )

        result = self.apply_controlled_phase_rotation(
            builder, control1_reg, control1_bit, result, target_bit, phase_angle / 2
        )

        return result

    # =========================================================================
    # quantum fourier transform
    # =========================================================================

    def apply_qft(
        self, builder: "Builder", register: "SSAValue", n_qubits: int
    ) -> "SSAValue":
        """
        Apply Quantum Fourier Transform to a register.
        Matches Qiskit's standard implementation (MSB -> LSB).

        QFT transforms |x⟩ → (1/√2ⁿ) Σ e^(2πixk/2ⁿ) |k⟩

        NOTE: This implements QFT with do_swaps=False (matching Qiskit's Draper adder).

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            register: The input quantum register
            n_qubits: Number of qubits in the register

        Returns:
            The register in the Fourier basis
        """
        result = register

        for i in reversed(range(n_qubits)):
            result = self.apply_hadamard_gate(builder, result, i)

            for j in reversed(range(i)):
                k = i - j + 1
                phase_angle = 2 * math.pi / (2**k)
                result = self.apply_controlled_phase_rotation(
                    builder, result, j, result, i, phase_angle
                )

        return result

    def apply_inverse_qft(
        self, builder: "Builder", register: "SSAValue", n_qubits: int
    ) -> "SSAValue":
        """
        Apply Inverse Quantum Fourier Transform.
        Un-does the operations of QFT in exact reverse order.

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            register: The register in Fourier basis
            n_qubits: Number of qubits in the register

        Returns:
            The register in computational basis
        """
        result = register

        for i in range(n_qubits):
            for j in range(i):
                k = i - j + 1
                phase_angle = -2 * math.pi / (2**k)
                result = self.apply_controlled_phase_rotation(
                    builder, result, j, result, i, phase_angle
                )

            result = self.apply_hadamard_gate(builder, result, i)

        return result

    # =========================================================================
    # draper arithmetic (qft-based)
    # =========================================================================

    def draper_addition(
        self,
        builder: "Builder",
        a_reg: "SSAValue",
        target_reg: "SSAValue",
        width_a: int,
        op_width: int,
    ) -> "SSAValue":
        """
        Draper quantum addition using QFT approach.

        Adds the value in a_reg to target_reg (which should already be in QFT basis
        or will have QFT applied). The caller is responsible for:
        - Copying operand B into target_reg before calling
        - Applying QFT to target_reg before calling
        - Applying inverse QFT after calling

        Algorithm:
        For each bit i in A, if A[i] = 1, apply phase rotation 2π/2^(j-i+1)
        to each bit j ≥ i in target register.

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            a_reg: First operand register (addend)
            target_reg: Target register in Fourier basis (contains B, will become A+B)
            width_a: Bit width of operand A
            op_width: Operation width (width of target register)

        Returns:
            The target register with A added (still in Fourier basis)
        """
        result = target_reg

        for i in range(width_a):
            for j in range(i, op_width):
                phase_angle = 2 * math.pi / (2 ** (j - i + 1))
                result = self.apply_controlled_phase_rotation(
                    builder, a_reg, i, result, j, phase_angle
                )

        return result

    def draper_subtraction(
        self,
        builder: "Builder",
        b_reg: "SSAValue",
        target_reg: "SSAValue",
        width_b: int,
        op_width: int,
    ) -> "SSAValue":
        """
        Draper quantum subtraction using QFT approach with negative phases.

        Subtracts the value in b_reg from target_reg (which should already be in QFT basis).
        The caller is responsible for:
        - Copying operand A into target_reg before calling
        - Applying QFT to target_reg before calling
        - Applying inverse QFT after calling

        Algorithm:
        For each bit i in B, apply negative phase rotation -2π/2^(j-i+1)
        to each bit j ≥ i in target register.

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            b_reg: Subtrahend register (value to subtract)
            target_reg: Target register in Fourier basis (contains A, will become A-B)
            width_b: Bit width of operand B
            op_width: Operation width (width of target register)

        Returns:
            The target register with B subtracted (still in Fourier basis)
        """
        result = target_reg

        for i in range(width_b):
            for j in range(i, op_width):
                phase_angle = -2 * math.pi / (2 ** (j - i + 1))
                result = self.apply_controlled_phase_rotation(
                    builder, b_reg, i, result, j, phase_angle
                )

        return result

    def draper_multiplication(
        self,
        builder: "Builder",
        a_reg: "SSAValue",
        b_reg: "SSAValue",
        product_reg: "SSAValue",
        width_a: int,
        width_b: int,
        width_product: int,
    ) -> "SSAValue":
        """
        Draper quantum multiplication using doubly-controlled phase rotations.

        Computes A * B by accumulating doubly-controlled phase rotations in Fourier space.
        The caller is responsible for:
        - Creating product_reg with appropriate width (width_a + width_b)
        - Applying QFT to product_reg before calling
        - Applying inverse QFT after calling

        Algorithm:
        For each bit i in A and bit j in B, apply doubly-controlled phase rotations
        to product bits k ≥ i+j. The phase represents contribution of A[i] * B[j] * 2^(i+j).

        Args:
            builder: The XDSL Builder for inserting operations (REQUIRED)
            a_reg: First operand register (multiplicand)
            b_reg: Second operand register (multiplier)
            product_reg: Product register in Fourier basis
            width_a: Bit width of operand A
            width_b: Bit width of operand B
            width_product: Bit width of product register

        Returns:
            The product register with A*B (still in Fourier basis)
        """
        result = product_reg

        for i in range(width_a):
            for j in range(width_b):
                for k in range(i + j, width_product):
                    phase_angle = 2 * math.pi / (2 ** (k - (i + j) + 1))
                    result = self.apply_ccphase(
                        builder, a_reg, i, b_reg, j, result, k, phase_angle
                    )

        return result
