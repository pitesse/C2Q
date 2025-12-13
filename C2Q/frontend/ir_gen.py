"""IR Generator for C AST to Quantum IR conversion.

This module implements the IR generation phase of the C-to-Quantum compiler.
It takes an Abstract Syntax Tree (AST) produced by the parser and generates
corresponding quantum IR operations using the quantum dialect.

The generator supports basic C constructs including:
- Variable declarations and assignments
- Arithmetic operations (addition, subtraction, multiplication)
- Function calls and return statements
- Quantum register management and operations

All operations are mapped to appropriate quantum gate sequences using
Draper's QFT-based arithmetic algorithms.
"""

from __future__ import annotations

import math
from xdsl.context import Context
from xdsl.ir import Block, Region, SSAValue
from xdsl.dialects.builtin import (
    ModuleOp,
    IntegerType,
    VectorType,
    IntegerAttr,
    StringAttr,
)
from xdsl.builder import Builder
from xdsl.rewriter import InsertPoint
from xdsl.utils.scoped_dict import ScopedDict


from .c_ast import *
from .quantum_arithmetic import QuantumArithmetic
from ..dialects.quantum_dialect import (
    InitOp,
    NotOp,
    CNotOp,
    CCNotOp,
    MeasureOp,
    HadamardOp,
    TGateOp,
    TDaggerGateOp,
    FuncOp,
    CommentOp,
    ExtractBitOp,
    InsertBitOp,
    OnQubitNotOp,
    OnQubitCNotOp,
    OnQubitCCnotOp,
    OnQubitHadamardOp,
    OnQubitControlledPhaseOp,
    OnQubitSwapOp,
)

# Import Quantum dialect separately to avoid registration issues
from ..dialects import quantum_dialect


class IRGenError(Exception):
    """
    Exception raised for errors during IR generation.

    This exception is raised when the IR generator encounters an issue that
    prevents it from generating valid quantum IR, such as:
    - Unsupported expressions or operations
    - Undefined variables or functions
    - Type mismatches or invalid register operations
    """

    pass


class QuantumIRGen:
    """
    IR Generator for C AST to Quantum IR conversion.

    This class transforms C Abstract Syntax Trees into quantum intermediate
    representation using quantum gate operations. It implements Draper's
    QFT-based algorithms for arithmetic operations.

    Key Features:
    - Variable declarations mapped to quantum register initialization
    - Arithmetic operations using QFT-based quantum algorithms
    - Symbol table management for variable scoping
    - Register naming conventions (qN_M format)

    Attributes:
        module: MLIR module containing all generated operations
        builder: Helper for creating IR with insertion point management
        symbol_table: Maps variable names to quantum registers in current scope
        n_qubit: Number of qubits used in current generation
        n_args: Number of function arguments processed
        function_map: Maps function names to their AST representations
    """

    module: ModuleOp
    """MLIR module containing quantum operations and functions."""

    builder: Builder
    """
    Builder for creating IR operations with stateful insertion point.
    The insertion point determines where new operations are added.
    """

    symbol_table: ScopedDict[str, SSAValue] | None = None
    """
    Symbol table mapping variable names to quantum register values.
    Creates new scopes for functions and maintains proper variable visibility.
    """

    n_qubit: int = 0
    """Number of qubits used when generating initial IR."""

    function_map: dict[str, FunctionAST] = {}
    """Maps function names to their AST representations for inlining."""

    def __init__(self):
        """
        Initialize the Quantum IR Generator.

        Sets up the XDSL context, loads the quantum dialect, creates the
        MLIR module, and initializes the builder and symbol table.
        """
        self.context = Context()
        # load dialect, handling case where it's already loaded
        try:
            self.context.load_dialect(quantum_dialect.Quantum)
        except Exception:
            pass

        self.module = ModuleOp([])
        self.builder = Builder(InsertPoint.at_end(self.module.body.blocks[0]))
        self.function_map = {}

        # note: it pass self.builder to each quantum_arith method call, not storing it here
        self.quantum_arith = QuantumArithmetic()

    # =========================================================================
    # module generation
    # =========================================================================

    def ir_gen_module(self, module_ast: ModuleAST) -> ModuleOp:
        """
        Generate quantum IR from C AST module with main as entry point.

        Processes all functions in the module, building a function map for
        inlining, then generates IR for the main function.

        Args:
            module_ast: The ModuleAST node representing the C module

        Returns:
            ModuleOp: The generated MLIR module containing quantum IR

        Raises:
            IRGenError: If main function is not found
        """
        for func_ast in module_ast.funcs:
            self.function_map[func_ast.proto.name] = func_ast

        # find and process main function
        main_func = next((f for f in module_ast.funcs if f.proto.name == "main"), None)
        if main_func:
            self.ir_gen_main_function(main_func)
        else:
            raise IRGenError("No main function found in the C module")

        return self.module

    def ir_gen_main_function(self, main_func: FunctionAST) -> FuncOp:
        """
        Generate IR for the main function with function call inlining.

        Creates the main function scope, processes parameters, and generates
        IR for all expressions in the function body. Function calls are
        automatically inlined during processing.

        Args:
            main_func: The FunctionAST node representing the main function

        Returns:
            FuncOp: The generated quantum function operation
        """
        self.symbol_table = ScopedDict[str, SSAValue]()
        region = Region() # control flow graph of blocks
        block = Block() # sequence of operations
        region.add_block(block)

        func_op = self.builder.insert(FuncOp("main", region))

        self.builder = Builder(InsertPoint.at_end(block))

        for arg in func_op.regions[0].blocks[0]._args:
            qubit = self.builder.insert(InitOp.from_value(IntegerType(1)))
            if self.symbol_table is not None and arg._name is not None:
                self.symbol_table[arg._name] = qubit.res

        result = None
        for expr in main_func.body:
            self.ir_gen_expr(expr)

        return func_op

    def ir_gen_func_call(self, func_ast: FunctionAST, args: list[ExprAST]):
        """
        Generate IR for a function call by inlining the function body.

        Creates a new scope for the function call, substitutes parameters
        with provided arguments, and generates IR for the function body.

        Args:
            func_ast: The FunctionAST node representing the function to be called
            args: List of arguments passed to the function
        """
        self.symbol_table = ScopedDict(parent=self.symbol_table)

        for param, arg in zip(func_ast.proto.args, args):
            qubit = self.ir_gen_expr(arg)
            if self.symbol_table is not None and qubit is not None:
                self.symbol_table[param.name] = qubit

        for expr in func_ast.body:
            self.ir_gen_expr(expr)

    def ir_gen_call_expr(self, expr: CallExprAST):
        """
        Generate IR for a function call expression.

        Looks up the function in the function map and inlines it by calling
        ir_gen_func_call with the provided arguments.

        Args:
            expr: The CallExprAST node representing a function call

        Raises:
            IRGenError: If the called function is not found
        """
        called_func = next((f for f in self.function_map if f == expr.callee), None)

        if called_func is None:
            raise IRGenError(f"Function {expr.callee} not found")
        else:
            func_ast = self.function_map[expr.callee]
            self.ir_gen_func_call(func_ast, expr.args)

    # =========================================================================
    # expression generation
    # =========================================================================

    def ir_gen_expr(self, expr: ExprAST):
        """
        Generate IR for a C expression using pattern matching dispatch.

        Dispatches to the appropriate method based on the expression type.
        Supports binary operations, literals, variable declarations, returns,
        function calls, and variable references.

        Args:
            expr: The ExprAST node representing a C expression

        Returns:
            The resulting quantum value (usually a qubit reference)

        Raises:
            IRGenError: If the expression type is unsupported
        """
        if isinstance(expr, BinaryExprAST):
            return self.ir_gen_binary_expr(expr)
        elif isinstance(expr, NumberExprAST):
            return self.ir_gen_number_expr(expr)
        elif isinstance(expr, VarDeclExprAST):
            return self.ir_gen_var_decl_expr(expr)
        elif isinstance(expr, ReturnExprAST):
            return self.ir_gen_return_expr(expr)
        elif isinstance(expr, CallExprAST):
            return self.ir_gen_call_expr(expr)
        elif isinstance(expr, VariableExprAST):
            return self.ir_gen_variable_expr(expr)
        else:
            raise IRGenError(f"Unsupported expression type: {type(expr)}")

    def ir_gen_binary_expr(self, expr: BinaryExprAST):
        """
        Generate quantum operations for binary expressions.

        Handles arithmetic operations (+, -, *) using Draper QFT algorithms
        and assignment operations (=). Special handling for negative literals
        that appear as (0 - constant) expressions.

        Args:
            expr: The BinaryExprAST node representing a binary operation

        Returns:
            The resulting quantum register value

        Raises:
            IRGenError: If assignment target is not a variable or operation is unsupported
        """
        # handle special case: 0 - constant (negative literal from parser)
        if (
            expr.op == "-"
            and isinstance(expr.lhs, NumberExprAST)
            and expr.lhs.val == 0
            and isinstance(expr.rhs, NumberExprAST)
        ):
            # This is a negative literal, handle it directly
            negative_expr = NumberExprAST(expr.rhs.loc, -expr.rhs.val)
            return self.ir_gen_number_expr(negative_expr)

        # handle cases where operands might be None
        if expr.lhs is None or expr.rhs is None:
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

        # handle binary operations
        if expr.op == "+":
            return self.draper_quantum_addition(expr.lhs, expr.rhs)
        elif expr.op == "-":
            return self.draper_quantum_subtraction(expr.lhs, expr.rhs)
        elif expr.op == "*":
            return self.draper_quantum_multiplication(expr.lhs, expr.rhs)
        elif expr.op == "=":
            if not isinstance(expr.lhs, VariableExprAST):
                raise IRGenError("Assignment target must be a variable")

            var_name = expr.lhs.name

            # self-assignment like a = a + b: evaluate normally and update symbol table
            if (
                isinstance(expr.rhs, BinaryExprAST)
                and isinstance(expr.rhs.lhs, VariableExprAST)
                and expr.rhs.lhs.name == var_name
            ):
                rhs_value = self.ir_gen_expr(expr.rhs)
            else:
                rhs_value = self.ir_gen_expr(expr.rhs)

            if self.symbol_table is not None and rhs_value is not None:
                if var_name in self.symbol_table._local_scope:
                    del self.symbol_table._local_scope[var_name]
                self.symbol_table[var_name] = rhs_value

            return rhs_value
        else:
            raise IRGenError(f"Unsupported binary operation: {expr.op}")

    # =========================================================================
    # quantum operations (delegated to quantumarithmetic)
    # =========================================================================

    # def apply_hadamard_gate(self, register: SSAValue, qubit_index: int) -> SSAValue:
    #     """
    #     Apply Hadamard gate to a specific qubit in the register.
    #     H|0⟩ = (|0⟩ + |1⟩)/√2, H|1⟩ = (|0⟩ - |1⟩)/√2

    #     Delegates to QuantumArithmetic, passing the current builder.
    #     """
    #     return self.quantum_arith.apply_hadamard_gate(self.builder, register, qubit_index)

    # def apply_controlled_phase_rotation(self, control_register: SSAValue, control_index: int,
    #                                    target_register: SSAValue, target_index: int,
    #                                    phase_angle: float) -> SSAValue:
    #     """
    #     Apply controlled phase rotation.
    #     Delegates to QuantumArithmetic, passing the current builder.
    #     """
    #     return self.quantum_arith.apply_controlled_phase_rotation(
    #         self.builder, control_register, control_index,
    #         target_register, target_index, phase_angle
    #     )

    # def apply_swap_gate(self, register: SSAValue, qubit1: int, qubit2: int) -> SSAValue:
    #     """
    #     Swap two qubits using the dedicated swap operation.
    #     Delegates to QuantumArithmetic, passing the current builder.
    #     """
    #     return self.quantum_arith.apply_swap_gate(self.builder, register, qubit1, qubit2)

    # def apply_phase_gate(self, register: SSAValue, qubit_index: int, phase: float) -> SSAValue:
    #     """
    #     Apply a phase gate to a specific qubit in a register.
    #     Phase gate: |0⟩ → |0⟩, |1⟩ → e^(iθ)|1⟩
    #     Delegates to QuantumArithmetic, passing the current builder.
    #     """
    #     return self.quantum_arith.apply_phase_gate(self.builder, register, qubit_index, phase)

    # def reverse_qubit_order(self, register: SSAValue, n_qubits: int) -> SSAValue:
    #     """
    #     Reverse the order of qubits in the register using SWAP operations.
    #     Delegates to QuantumArithmetic, passing the current builder.
    #     """
    #     return self.quantum_arith.reverse_qubit_order(self.builder, register, n_qubits)

    # def apply_ccphase(self, control1_reg: SSAValue, control1_bit: int,
    #                  control2_reg: SSAValue, control2_bit: int,
    #                  target_reg: SSAValue, target_bit: int,
    #                  phase_angle: float) -> SSAValue:
    #     """
    #     Apply doubly-controlled phase gate: CCPhase(theta).
    #     Only applies phase if BOTH control qubits are |1⟩.
    #     Delegates to QuantumArithmetic, passing the current builder.
    #     """
    #     return self.quantum_arith.apply_ccphase(
    #         self.builder,
    #         control1_reg, control1_bit,
    #         control2_reg, control2_bit,
    #         target_reg, target_bit,
    #         phase_angle
    #     )

    def apply_cnot_on_bits(
        self,
        control_register: SSAValue,
        control_index: int,
        target_register: SSAValue,
        target_index: int,
    ) -> SSAValue:
        """
        Apply a CNOT gate directly between bits in two registers.

        Args:
            control_register: The register containing the control qubit
            control_index: The index of the control bit
            target_register: The register containing the target qubit
            target_index: The index of the target bit

        Returns:
            The updated target register after applying CNOT
        """
        # use OnQubitCNotOp to apply CNOT directly
        result = self.builder.insert(
            OnQubitCNotOp.from_values(
                control_register, control_index, target_register, target_index
            )
        ).res

        # maintain the naming convention
        if hasattr(target_register, "_name") and target_register._name:
            parts = target_register._name.split("_")
            if len(parts) == 2:
                register_num = parts[0].lstrip("q")
                version_num = int(parts[1]) + 1
                result._name = f"q{register_num}_{version_num}"

        return result

    def apply_qft(self, register: SSAValue, n_qubits: int) -> SSAValue:
        """
        Apply Quantum Fourier Transform to a register.
        Delegates to QuantumArithmetic, passing the current builder.
        """
        return self.quantum_arith.apply_qft(self.builder, register, n_qubits)

    def apply_inverse_qft(self, register: SSAValue, n_qubits: int) -> SSAValue:
        """
        Apply Inverse Quantum Fourier Transform.
        Delegates to QuantumArithmetic, passing the current builder.
        """
        return self.quantum_arith.apply_inverse_qft(self.builder, register, n_qubits)

    def draper_quantum_addition(
        self, a_expr: ExprAST, b_expr: ExprAST, target_reg: SSAValue | None = None
    ) -> SSAValue:
        """
        Draper quantum addition using QFT approach with dynamic width support.

        Supports mixed-width operands (e.g., adding an 8-bit number to a 16-bit number).
        The result width is the maximum of the two operand widths.

        Args:
            a_expr: First operand expression
            b_expr: Second operand expression
            target_reg: Optional target register to store the result. If None, creates new register.

        Returns:
            The resulting register containing A + B
        """
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)

        if a is None or b is None:
            raise IRGenError(
                "Failed to generate quantum register for addition operands"
            )

        # handle single qubit inputs
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                a_temp = self.apply_cnot_on_bits(a, 0, a_temp, 0)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                b_temp = self.apply_cnot_on_bits(b, 0, b_temp, 0)
                b = b_temp

        width_a = self.get_bit_width(a)
        width_b = self.get_bit_width(b)
        op_width = max(width_a, width_b)

        if target_reg is None:
            target = self.ir_gen_init_with_width(op_width)
            for i in range(min(width_b, op_width)):
                target = self.apply_cnot_on_bits(b, i, target, i)
        else:
            target = target_reg
            target_width = self.get_bit_width(target)
            for i in range(min(width_b, target_width)):
                target = self.apply_cnot_on_bits(b, i, target, i)
            op_width = target_width

        # apply qft, draper addition, inverse qft
        result = self.apply_qft(target, op_width)
        result = self.quantum_arith.draper_addition(
            self.builder, a, result, width_a, op_width
        )
        result = self.apply_inverse_qft(result, op_width)

        return result

    def draper_quantum_subtraction(
        self, a_expr: ExprAST, b_expr: ExprAST, target_reg: SSAValue | None = None
    ) -> SSAValue:
        """
        Generate quantum circuit for subtraction using Draper's QFT-based subtractor.

        Supports mixed-width operands (e.g., subtracting an 8-bit number from a 16-bit number).
        The result width is the maximum of the two operand widths.

        Args:
            a_expr: Left operand expression (minuend)
            b_expr: Right operand expression (subtrahend)
            target_reg: Optional target register for in-place operation

        Returns:
            The resulting quantum register containing the difference
        """
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)

        if a is None or b is None:
            raise IRGenError(
                "Failed to generate quantum register for subtraction operands"
            )

        # handle single qubit inputs
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                a_temp = self.apply_cnot_on_bits(a, 0, a_temp, 0)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                b_temp = self.apply_cnot_on_bits(b, 0, b_temp, 0)
                b = b_temp

        width_a = self.get_bit_width(a)
        width_b = self.get_bit_width(b)
        op_width = max(width_a, width_b)

        if target_reg is None:
            target = self.ir_gen_init_with_width(op_width)
            for i in range(min(width_a, op_width)):
                target = self.apply_cnot_on_bits(a, i, target, i)
        else:
            target = target_reg
            target_width = self.get_bit_width(target)
            for i in range(min(width_a, target_width)):
                target = self.apply_cnot_on_bits(a, i, target, i)
            op_width = target_width

        # apply qft, draper subtraction, inverse qft
        result = self.apply_qft(target, op_width)
        result = self.quantum_arith.draper_subtraction(
            self.builder, b, result, width_b, op_width
        )
        result = self.apply_inverse_qft(result, op_width)

        return result

    def draper_quantum_multiplication(
        self, a_expr: ExprAST, b_expr: ExprAST
    ) -> SSAValue:
        """
        Generate quantum circuit for multiplication using Draper's QFT-based algorithm.
        Computes A * B by accumulating doubly-controlled phase rotations in Fourier space.

        Supports dynamic operand widths - the product register width is the sum of operand widths.

        Args:
            a_expr: First operand expression (multiplicand)
            b_expr: Second operand expression (multiplier)

        Returns:
            The resulting quantum register containing A * B
        """
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)

        if a is None or b is None:
            raise IRGenError(
                "Failed to generate quantum register for multiplication operands"
            )

        # handle single qubit inputs
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                a_temp = self.apply_cnot_on_bits(a, 0, a_temp, 0)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                b_temp = self.apply_cnot_on_bits(b, 0, b_temp, 0)
                b = b_temp

        width_a = self.get_bit_width(a)
        width_b = self.get_bit_width(b)
        width_product = width_a + width_b

        product = self.ir_gen_init_with_width(width_product)

        # apply qft, draper multiplication, inverse qft
        product = self.apply_qft(product, width_product)
        product = self.quantum_arith.draper_multiplication(
            self.builder, a, b, product, width_a, width_b, width_product
        )
        product = self.apply_inverse_qft(product, width_product)

        return product

    # =========================================================================
    # register width helpers
    # =========================================================================

    def get_bit_width(self, register: SSAValue) -> int:
        """
        Get the bit width of a quantum register.

        Inspects the register's VectorType to determine how many qubits it contains.
        This is essential for supporting mixed-width arithmetic operations.

        Args:
            register: The SSA value representing a quantum register

        Returns:
            The number of qubits (bits) in the register, defaults to 8 if unable to determine
        """
        try:
            if hasattr(register, "type") and isinstance(register.type, VectorType):
                shape = register.type.shape
                if hasattr(shape, "data") and len(shape.data) > 0:
                    first_dim = shape.data[0]
                    if hasattr(first_dim, "data"):
                        return int(first_dim.data)
                    else:
                        return 8
        except Exception:
            pass
        return 8

    def ir_gen_init_with_width(self, width: int) -> SSAValue:
        """
        Initialize a new multi-qubit register with specified width.

        Args:
            width: Number of qubits in the register

        Returns:
            SSA value representing the multi-qubit register
        """
        register_num = self.n_qubit // 8
        status_num = 0

        register_name = f"q{register_num}_{status_num}"

        register = self.builder.insert(
            InitOp.from_value(VectorType(IntegerType(1), [width]))
        )

        register.res._name = register_name

        self.n_qubit += width

        return register.res

    # =========================================================================
    # declarations and assignment
    # =========================================================================

    def ir_gen_variable_expr(self, expr: VariableExprAST) -> SSAValue:
        """
        Generate IR for a variable reference.

        Looks up the variable in the symbol table and returns its SSA value.
        Creates a new quantum register if the variable is not found.

        Args:
            expr: The VariableExprAST node representing a variable reference

        Returns:
            The SSA value associated with the variable
        """
        var_name = expr.name

        if self.symbol_table is not None and var_name in self.symbol_table:
            return self.symbol_table[var_name]
        else:
            raise IRGenError(f"Referenced undefined variable: {var_name}")

    def ir_gen_init(self, expr: NumberExprAST | None = None) -> SSAValue:
        """
        Initialize a new multi-qubit register for integer representation.

        Creates a vector of qubits with proper naming convention qx_y where:
        - x is the register number
        - y is the version tracking write operations

        Args:
            expr: Optional expression for context (typically a NumberExprAST)

        Returns:
            SSA value representing the multi-qubit register
        """
        bit_width = 8

        register_num = self.n_qubit // bit_width
        status_num = 0

        register_name = f"q{register_num}_{status_num}"

        register = self.builder.insert(
            InitOp.from_value(VectorType(IntegerType(1), [bit_width]))
        )

        register.res._name = register_name

        self.n_qubit += bit_width

        return register.res

    def ir_gen_number_expr(self, expr: NumberExprAST) -> SSAValue:
        """Generate IR for a number literal using binary representation across multiple qubits."""
        register = self.ir_gen_init(expr)

        if expr.val != 0:
            value = int(expr.val)
            bit_width = 8

            # use two's complement for negative numbers
            if value < 0:
                value = (1 << bit_width) + value

            value = value & ((1 << bit_width) - 1)

            binary_str = bin(value)[2:].zfill(bit_width)[-bit_width:]

            for i, bit in enumerate(reversed(binary_str)):
                if bit == "1":
                    register = self.flip_qubit(register, i)

        return register

    def ir_gen_var_decl_expr(self, expr: VarDeclExprAST) -> SSAValue:
        """
        Generate IR for a variable declaration with proper qubit tracking.

        Creates a new quantum register with appropriate bit width based on the
        initializer value. Maintains SSA form by tracking qubit state changes
        and applies NOT gates to initialize the register to the correct value.

        Args:
            expr: The VarDeclExprAST node representing a variable declaration

        Returns:
            The SSA value representing the new quantum register
        """
        if expr.expr is not None:
            if isinstance(expr.expr, NumberExprAST):
                qubit = self.ir_gen_number_expr(expr.expr)

            elif isinstance(expr.expr, VariableExprAST):
                var_name = expr.expr.name
                if self.symbol_table is not None and var_name in self.symbol_table:
                    source = self.symbol_table[var_name]
                    qubit = self.ir_gen_init(None)
                    bit_width = 8
                    for i in range(bit_width):
                        qubit = self.apply_cnot_on_bits(source, i, qubit, i)
                    return qubit
                else:
                    raise IRGenError(f"Referenced undefined variable: {var_name}")

            elif isinstance(expr.expr, BinaryExprAST):
                # let operations auto-detect widths and create appropriately-sized registers
                if expr.expr.op == "+":
                    expr_result = self.draper_quantum_addition(
                        expr.expr.lhs, expr.expr.rhs
                    )
                elif expr.expr.op == "-":
                    expr_result = self.draper_quantum_subtraction(
                        expr.expr.lhs, expr.expr.rhs
                    )
                elif expr.expr.op == "*":
                    expr_result = self.draper_quantum_multiplication(
                        expr.expr.lhs, expr.expr.rhs
                    )
                else:
                    expr_result = self.ir_gen_expr(expr.expr)
                    if expr_result is None:
                        raise IRGenError("Binary expression evaluation failed")

                qubit = expr_result

            else:
                try:
                    qubit = self.ir_gen_expr(expr.expr)
                    if qubit is None:
                        raise IRGenError("Expression evaluation returned None")
                except Exception as e:
                    raise IRGenError(f"Failed to initialize {expr.name}: {str(e)}")

        else:
            qubit = self.ir_gen_init(None)

        if (
            self.symbol_table is not None
            and expr.name in self.symbol_table._local_scope
        ):
            self.symbol_table = ScopedDict(parent=self.symbol_table)

        if self.symbol_table is not None:
            self.symbol_table[expr.name] = qubit

        return qubit

    def ir_gen_return_expr(self, expr: ReturnExprAST) -> SSAValue:
        """
        Generate IR for a return statement with improved return value handling.

        Processes the return expression and creates appropriate quantum operations.
        For void returns, creates a default quantum register.

        Args:
            expr: The ReturnExprAST node representing a return statement

        Returns:
            The quantum value to be returned
        """
        if expr.expr is not None:
            return_value = self.ir_gen_expr(expr.expr)

            if return_value is None:
                return_value = self.builder.insert(
                    InitOp.from_value(IntegerType(1))
                ).res

            return return_value
        else:
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

    # =========================================================================
    # helper functions
    # =========================================================================

    def flip_qubit(self, register: SSAValue, index: int) -> SSAValue:
        """
        Flip a specific qubit in a multi-qubit register using a direct NOT operation.

        Args:
            register: The multi-qubit register to modify
            index: The index of the qubit to flip (0 is LSB)

        Returns:
            The updated register with the flipped bit
        """
        if not isinstance(register.type, VectorType):
            return self.builder.insert(NotOp.from_value(register)).res

        flipped_register = self.builder.insert(
            OnQubitNotOp.from_value(register, index)
        ).res

        if hasattr(register, "_name") and register._name:
            parts = register._name.split("_")
            if len(parts) == 2:
                register_num = parts[0].lstrip("q")
                version_num = int(parts[1]) + 1
                flipped_register._name = f"q{register_num}_{version_num}"

        return flipped_register


# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣶⣾⣿⣿⣶⣦⣤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⢀⣠⣴⣶⣾⣿⣿⣿⡷⢀⣠⣴⣶⣾⣿⣿⣷⡄⠀⠀⠉⠛⠛⢻⣿⣿⠿⠿⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⣰⣿⣿⡿⠟⠛⠉⠉⠉⣱⣿⣿⡿⠛⠛⠛⣿⣿⣿⡀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⣿⣿⣏⠀⠀⠀⠀⠀⠀⣿⣿⣯⠀⠀⠀⢠⣿⣿⣿⣷⠀⠀⠀⠀⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠸⣿⣿⣷⣶⣾⣿⣆⠀⢹⣿⣿⣶⣀⣶⣿⣿⡿⣿⣿⣇⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠈⠛⠿⠿⠿⠛⠃⠀⠀⠙⠿⣿⣿⣿⠿⠛⠀⠙⢿⣿⠇⠀⠀⠈⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⢀⣶⣶⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⣶⣦⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⠻⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⣿⣿⡇⠈⠻⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⡟⠁⠀⠸⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⢸⣿⣿⠃⠀⠀⠈⢻⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⠟⠀⠀⠀⠀⠹⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⠀⠙⢿⣿⣷⣀⣀⣀⣀⣀⣀⣾⣿⡿⠋⠀⠀⠀⠀⠀⠀⢻⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⣿⣿⡏⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⢀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣷⡀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠘⠿⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⣠⣶⣶⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠿⣿⣿⣆⠀⠀⠀⠀
# ⠀⠀⢀⣼⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠹⣿⣿⣆⠀⠀⠀
# ⠀⢠⣿⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⣆⠀⠀⠀⠀⠀⠀⠈⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠹⣿⣿⡆⠀⠀
# ⢀⣿⣿⡏⠀⠀⠀⠀⢠⣴⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠋⠀⠀⠀⠀⠀⠀⢠⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⡿⠀⠀⠀⢹⣿⣿⡄⠀
# ⢸⣿⣿⠀⠀⠀⠀⠀⠘⠻⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⢻⣿⣷⠀
# ⠘⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠃⠀⠀⠀⠀⢸⣿⣿⠆
# ⠀⠹⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⣿⣿⠿⣿⣿⣿⣶⣄⡀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⠀⢸⣿⣿⠃
# ⠀⠀⠹⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣴⣾⣿⣿⠟⠁⠀⠀⠉⠛⢿⣿⣿⣶⣄⠀⠀⠀⠀⣼⣿⣿⠀⠀⠀⠀⠀⣾⣿⡿⠀
# ⠀⠀⠀⠈⠻⣿⣿⣶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣶⣿⣿⣿⡿⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠈⠛⢿⣿⣷⣄⠀⠀⣿⣿⣿⠀⠀⠀⢀⣼⣿⣿⠃⠀
# ⠀⠀⠀⠀⠀⠈⠛⠿⣿⣿⣿⣷⣶⣶⣶⣶⣶⣦⣶⣶⣶⣶⣶⣿⣿⣿⣿⠿⠿⠛⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣿⣷⡀⢻⣿⣿⠀⢀⣴⣿⣿⠟⠁⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣩⣽⡛⠛⠛⠻⠿⠿⠿⠿⠿⠛⠛⠛⠋⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣆⠉⠉⠀⠈⠻⠛⠁⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣻⣿⣿⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣾⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣷⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣰⣾⣿⣿⣶⣀⠀⢀⣾⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⠿⠿⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣦⡀⠀⠀⠀⢀⣀⣤⣶⣿⣿⡿⠟⠿⢿⣿⣿⣿⣿⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢿⣿⣿⣷⣿⣿⣿⣿⡿⠟⠛⠁⠀⠀⠀⠀⠈⠙⠛⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
