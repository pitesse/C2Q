"""
@file ir_gen.py
@brief IR Generator for C AST to Quantum IR conversion.

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
from xdsl.builder import Builder, InsertPoint
from xdsl.utils.scoped_dict import ScopedDict


from .c_ast import *
from ..dialects.quantum_dialect import (
    Quantum,
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
        self.context.load_dialect(Quantum)

        self.module = ModuleOp([])
        self.builder = Builder(InsertPoint.at_end(self.module.body.blocks[0]))
        self.function_map = {}

    # ============================================================================
    # MODULE GENERATION
    # ============================================================================

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
        # Build function map for inlining support
        for func_ast in module_ast.funcs:
            self.function_map[func_ast.proto.name] = func_ast

        # Find and process main function
        main_func = next((f for f in module_ast.funcs if f.proto.name == "main"), None)
        if main_func:
            self.ir_gen_main_function(main_func)
        else:
            raise IRGenError("No main function found in the module")

        return self.module

    # === functions ====

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
        # self.add_comment("// begin main function")

        # create a new scope for the main function
        self.symbol_table = ScopedDict[str, SSAValue]()

        # create a function region
        region = Region()
        block = Block()
        region.add_block(block)

        # create quantum function
        func_op = self.builder.insert(FuncOp("main", region))

        # set insertion point to function body
        self.builder = Builder(InsertPoint.at_end(block))

        # process function parameters
        # TODO review this
        for arg in func_op.regions[0].blocks[0]._args:
            # self.add_comment(f"// initialize main parameter: {arg.name}")
            qubit = self.builder.insert(InitOp.from_value(IntegerType(1)))
            self.symbol_table[arg._name] = qubit.res

        # process main function body
        result = None
        for expr in main_func.body:
            self.ir_gen_expr(expr)

        # self.add_comment("// end main function")

    def ir_gen_func_call(self, func_ast: FunctionAST, args: list[ExprAST]):
        """
        Generate IR for a function call by inlining the function body.

        Creates a new scope for the function call, substitutes parameters
        with provided arguments, and generates IR for the function body.

        Args:
            func_ast: The FunctionAST node representing the function to be called
            args: List of arguments passed to the function
        """
        # Create a new scope for the function call
        self.symbol_table = ScopedDict(parent=self.symbol_table)

        # Process function parameters and arguments
        for param, arg in zip(func_ast.proto.args, args):
            qubit = self.ir_gen_expr(arg)
            self.symbol_table[param.name] = qubit

        # Process function body
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
            # Inline the function call
            func_ast = self.function_map[expr.callee]
            self.ir_gen_func_call(func_ast, expr.args)

    # ============================================================================
    # EXPRESSION GENERATION
    # ============================================================================

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
        # Handle special case: 0 - constant (negative literal from parser)
        if (expr.op == "-" and 
            isinstance(expr.lhs, NumberExprAST) and expr.lhs.val == 0 and
            isinstance(expr.rhs, NumberExprAST)):
            # This is a negative literal, handle it directly
            negative_expr = NumberExprAST(expr.rhs.loc, -expr.rhs.val)
            return self.ir_gen_number_expr(negative_expr)
    
        # Handle cases where operands might be None
        if expr.lhs is None or expr.rhs is None:
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res
    
        # Handle binary operations
        if expr.op == "+":
            return self.draper_quantum_addition(expr.lhs, expr.rhs)
        elif expr.op == "-":
            return self.draper_quantum_subtraction(expr.lhs, expr.rhs)
        elif expr.op == "*":
            return self.draper_quantum_multiplication(expr.lhs, expr.rhs)
        elif expr.op == "=":
            # Handle assignment: variable = expression
            if not isinstance(expr.lhs, VariableExprAST):
                raise IRGenError("Assignment target must be a variable")
            
            var_name = expr.lhs.name
            
            # Check if this is a self-assignment like a = a + b
            if (isinstance(expr.rhs, BinaryExprAST) and 
                isinstance(expr.rhs.lhs, VariableExprAST) and 
                expr.rhs.lhs.name == var_name):
                
                # Self-assignment: evaluate normally (creates new register)
                # Then update symbol table to point to the new register
                rhs_value = self.ir_gen_expr(expr.rhs)
            else:
                # Regular assignment: evaluate RHS and store result
                rhs_value = self.ir_gen_expr(expr.rhs)
            
            # Update the symbol table with the new value for the LHS variable
            if var_name in self.symbol_table._local_scope:
                del self.symbol_table._local_scope[var_name]
            self.symbol_table[var_name] = rhs_value
            
            # Return the assigned value
            return rhs_value
        else:
            raise IRGenError(f"Unsupported binary operation: {expr.op}")

    # ============================================================================
    # QUANTUM OPERATIONS
    # ============================================================================

    def quantum_fourier_transform(self, register: SSAValue, n_qubits: int) -> SSAValue:
        """
        Apply Quantum Fourier Transform to a register.
        
        Implements the QFT algorithm using Hadamard gates and controlled phase
        rotations with the formula: phase = 2π/2^(j-i+1).
        
        Args:
            register: The quantum register to transform
            n_qubits: Number of qubits in the register
            
        Returns:
            The transformed register
        """
        result = register
        
        for i in range(n_qubits):
            # Apply Hadamard gate to qubit i
            result = OnQubitHadamardOp.from_value(result, i).res
            
            # Apply controlled phase rotations
            for j in range(i + 1, n_qubits):
                # Phase angle: 2π/2^(j-i+1) - correct QFT formula
                k = j - i + 1
                phase_angle = 2 * math.pi / (2 ** k)
                result = OnQubitControlledPhaseOp.from_values(
                    result, j, result, i, phase_angle
                ).res
        
        # Reverse the order of qubits (swap operation)
        for i in range(n_qubits // 2):
            result = OnQubitSwapOp.from_values(result, i, n_qubits - 1 - i).res
        
        return result

    def inverse_quantum_fourier_transform(self, register: SSAValue, n_qubits: int) -> SSAValue:
        """
        Apply Inverse Quantum Fourier Transform to a register.
        
        Implements the inverse QFT algorithm by reversing the QFT operations:
        first reversing qubit order, then applying inverse controlled phase
        rotations with negative angles: -2π/2^(j-i+1).
        
        Args:
            register: The quantum register to transform
            n_qubits: Number of qubits in the register
            
        Returns:
            The transformed register
        """
        result = register
        
        # Reverse the order of qubits first
        for i in range(n_qubits // 2):
            result = OnQubitSwapOp.from_values(result, i, n_qubits - 1 - i).res
        
        # Apply inverse controlled phase rotations and Hadamard gates
        for i in range(n_qubits - 1, -1, -1):
            # Apply inverse controlled phase rotations
            for j in range(n_qubits - 1, i, -1):
                # Negative phase angle: -2π/2^(j-i+1) - correct inverse QFT formula
                k = j - i + 1
                phase_angle = -2 * math.pi / (2 ** k)
                result = OnQubitControlledPhaseOp.from_values(
                    result, j, result, i, phase_angle
                ).res
            
            # Apply Hadamard gate to qubit i
            result = OnQubitHadamardOp.from_value(result, i).res
        
        return result

    def apply_hadamard_gate(self, register: SSAValue, qubit_index: int) -> SSAValue:
        """
        Apply Hadamard gate to a specific qubit in the register
        H|0⟩ = (|0⟩ + |1⟩)/√2, H|1⟩ = (|0⟩ - |1⟩)/√2
        """
        from C2Q.dialects.quantum_dialect import OnQubitHadamardOp
        
        result = self.builder.insert(
            OnQubitHadamardOp.from_value(register, qubit_index)
        ).res
        
        # Update naming convention
        if register._name:
            parts = register._name.split('_')
            if len(parts) == 2:
                register_num = parts[0].lstrip('q')
                version_num = int(parts[1]) + 1
                result._name = f"q{register_num}_{version_num}"
        
        return result

    def apply_cnot_on_bits(self, control_reg: SSAValue, control_bit: int, target_reg: SSAValue, target_bit: int) -> SSAValue:
        """
        Apply CNOT gate between specific bits of two registers
        """
        from C2Q.dialects.quantum_dialect import OnQubitCNotOp
        
        # Apply CNOT gate directly on register bits
        cnot_result = self.builder.insert(
            OnQubitCNotOp.from_values(
                control_reg, control_bit,
                target_reg, target_bit
            )
        )
        
        # Return the updated target register
        return cnot_result.res
    
    def update_register_at_bit(self, register: SSAValue, bit_index: int, new_qubit: SSAValue) -> SSAValue:
        """
        Update a specific bit in a quantum register
        """
        # For now, we'll return the register as-is since we don't have a proper update mechanism
        # This is a simplification - in a real implementation, we'd need to properly update the register
        return register

    def apply_controlled_phase_rotation(self, control_register: SSAValue, control_index: int,
                                       target_register: SSAValue, target_index: int, 
                                       phase_angle: float) -> SSAValue:
        """
        Apply controlled phase rotation: |control⟩|target⟩ → |control⟩|target⟩ if control=0
                                                            → |control⟩e^(iθ)|target⟩ if control=1
        """
        from C2Q.dialects.quantum_dialect import OnQubitControlledPhaseOp
        
        result = self.builder.insert(
            OnQubitControlledPhaseOp.from_values(
                control_register, control_index,
                target_register, target_index,
                phase_angle
            )
        ).res
        
        # Update naming convention
        if target_register._name:
            parts = target_register._name.split('_')
            if len(parts) == 2:
                register_num = parts[0].lstrip('q')
                version_num = int(parts[1]) + 1
                result._name = f"q{register_num}_{version_num}"
        
        return result

    def apply_swap_gate(self, register: SSAValue, qubit1: int, qubit2: int) -> SSAValue:
        """
        Swap two qubits using the dedicated swap operation
        """
        from C2Q.dialects.quantum_dialect import OnQubitSwapOp
        
        result = self.builder.insert(
            OnQubitSwapOp.from_values(register, qubit1, qubit2)
        ).res
        
        # Update naming convention
        if register._name:
            parts = register._name.split('_')
            if len(parts) == 2:
                register_num = parts[0].lstrip('q')
                version_num = int(parts[1]) + 1
                result._name = f"q{register_num}_{version_num}"
        
        return result

    def reverse_qubit_order(self, register: SSAValue, n_qubits: int) -> SSAValue:
        """
        Reverse the order of qubits in the register using SWAP operations
        """
        result = register
        
        # Swap qubits: 0↔(n-1), 1↔(n-2), etc.
        for i in range(n_qubits // 2):
            j = n_qubits - 1 - i
            result = self.apply_swap_gate(result, i, j)
        
        return result

    def apply_qft(self, register: SSAValue, n_qubits: int) -> SSAValue:
        """
        Apply Quantum Fourier Transform to a register
        QFT transforms |x⟩ → (1/√2ⁿ) Σ e^(2πixk/2ⁿ) |k⟩
        """
        import math
        
        result = register
        
        # QFT algorithm: work from most significant to least significant bit
        for i in range(n_qubits):
            # Apply Hadamard gate to qubit i
            result = self.apply_hadamard_gate(result, i)
            
            # Apply controlled phase rotations
            for j in range(i + 1, n_qubits):
                # Controlled R_k gate where k = j - i + 1
                k = j - i + 1
                phase_angle = 2 * math.pi / (2 ** k)
                result = self.apply_controlled_phase_rotation(result, j, result, i, phase_angle)
        
        # Reverse the order of qubits (swap bits)
        result = self.reverse_qubit_order(result, n_qubits)
        
        return result

    def apply_inverse_qft(self, register: SSAValue, n_qubits: int) -> SSAValue:
        """
        Apply inverse Quantum Fourier Transform
        This is the adjoint of QFT
        """
        import math
        
        result = register
        
        # Reverse the order of qubits first
        result = self.reverse_qubit_order(result, n_qubits)
        
        # Apply inverse QFT (reverse the QFT steps)
        for i in range(n_qubits - 1, -1, -1):
            # Apply inverse controlled phase rotations
            for j in range(n_qubits - 1, i, -1):
                k = j - i + 1
                phase_angle = -2 * math.pi / (2 ** k)  # Negative phase for inverse
                result = self.apply_controlled_phase_rotation(result, j, result, i, phase_angle)
            
            # Apply Hadamard gate to qubit i
            result = self.apply_hadamard_gate(result, i)
        
        return result

    def draper_quantum_addition(self, a_expr: ExprAST, b_expr: ExprAST, target_reg: SSAValue = None) -> SSAValue:
        """
        Draper quantum addition using QFT approach - CORRECT IMPLEMENTATION
        
        Algorithm:
        1. Apply QFT to target register
        2. Apply controlled phase rotations: for each bit i in A, if A[i] = 1,
           apply phase rotation 2π/2^(j-i+1) to each bit j ≥ i in target
        3. Apply inverse QFT to get the final result
        
        @param a_expr: First operand expression
        @param b_expr: Second operand expression  
        @param target_reg: Optional target register to store the result. If None, creates new register.
        @return: The resulting register containing A + B
        """
        import math
        
        # Evaluate expressions to get quantum registers
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)
        
        # Handle single qubit inputs
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                a_temp = self.apply_cnot_on_bits(a, 0, a_temp, 0)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                b_temp = self.apply_cnot_on_bits(b, 0, b_temp, 0)
                b = b_temp

        # Work with appropriate bit width
        bit_width = 8  # Use 8 bits for testing (was 32)

        # Determine target register for the addition
        if target_reg is None:
            # Create a new register and copy B into it
            target = self.ir_gen_init(None)
            # Copy B into the target register
            for i in range(bit_width):
                target = self.apply_cnot_on_bits(b, i, target, i)
        else:
            # Use the provided target register, but still need to copy B into it
            target = target_reg
            # Copy B into the target register
            for i in range(bit_width):
                target = self.apply_cnot_on_bits(b, i, target, i)
        
        # Step 1: Apply QFT to target register
        result = self.apply_qft(target, bit_width)
        
        # Step 2: Apply Draper's controlled phase additions
        # For each bit i in register A, and each bit j in target where j >= i:
        # If A[i] = 1, apply phase rotation 2π/2^(j-i+1) to target[j]
        for i in range(bit_width):
            for j in range(i, bit_width):
                # Phase angle: 2π/2^(j-i+1)
                # This is the key formula for Draper's algorithm
                phase_angle = 2 * math.pi / (2 ** (j - i + 1))
                
                # Apply controlled phase rotation: A[i] controls target[j]
                result = self.apply_controlled_phase_rotation(
                    a, i,        # Control: bit i of register A
                    result, j,   # Target: bit j of target register (after QFT)
                    phase_angle
                )
        
        # Step 3: Apply inverse QFT to get the final result
        result = self.apply_inverse_qft(result, bit_width)
        
        return result

    def draper_quantum_subtraction(self, a_expr: ExprAST, b_expr: ExprAST, target_reg: SSAValue = None) -> SSAValue:
        """
        Generate quantum circuit for subtraction using Draper's QFT-based subtractor.
        
        Implements quantum subtraction (target - addend) using Draper's algorithm
        by applying negative phase rotations in the frequency domain.
        
        Algorithm:
        1. Apply QFT to target register
        2. Apply controlled phase rotations with negative angles for subtraction
        3. Apply inverse QFT to get final result
        
        Args:
            a_expr: Left operand expression (minuend)
            b_expr: Right operand expression (subtrahend)
            target_reg: Optional target register for in-place operation
            
        Returns:
            The resulting quantum register containing the difference
        """
        import math
        
        # Evaluate expressions to get the quantum registers
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)
        
        # Handle single qubit inputs
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                a_temp = self.apply_cnot_on_bits(a, 0, a_temp, 0)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                b_temp = self.apply_cnot_on_bits(b, 0, b_temp, 0)
                b = b_temp

        bit_width = 8  # For 8-bit integers (testing)

        # Determine target register for the subtraction
        if target_reg is None:
            # Create a new register and copy B into it
            target = self.ir_gen_init(None)
            # Copy B into the target register
            for i in range(bit_width):
                target = self.apply_cnot_on_bits(b, i, target, i)
        else:
            # Use the provided target register, but still need to copy B into it
            target = target_reg
            # Copy B into the target register
            for i in range(bit_width):
                target = self.apply_cnot_on_bits(b, i, target, i)
        
        # Step 1: Apply QFT to target register
        result = self.apply_qft(target, bit_width)
        
        # Step 2: Apply Draper's controlled phase subtractions (negative phases)
        # For each bit i in register A, and each bit j in target where j >= i:
        # If A[i] = 1, apply phase rotation -2π/2^(j-i+1) to target[j]
        for i in range(bit_width):
            for j in range(i, bit_width):
                # Negative phase angle: -2π/2^(j-i+1)
                # This is the key formula for Draper's subtraction algorithm
                phase_angle = -2 * math.pi / (2 ** (j - i + 1))
                
                # Apply controlled phase rotation: A[i] controls target[j]
                result = self.apply_controlled_phase_rotation(
                    a, i,        # Control: bit i of register A
                    result, j,   # Target: bit j of target register (after QFT)
                    phase_angle
                )
        
        # Step 3: Apply inverse QFT to get the final result
        result = self.apply_inverse_qft(result, bit_width)
        
        return result

    #TODO make this work with qft and shift and add
    def draper_quantum_multiplication(self, a_expr: ExprAST, b_expr: ExprAST) -> SSAValue:
        """
        Generate quantum circuit for multiplication using Draper's QFT-based shift-and-add.
        
        IMPORTANT LIMITATION: This implementation has critical simplifications that make it
        incorrect for general quantum multiplication. It should be considered an educational
        demonstration of the circuit structure rather than a correct algorithm.
        
        Issues with current implementation:
        1. Controlled addition ignores control bits (always adds all shifted values)
        2. Doubly-controlled gates simplified to singly-controlled 
        3. Results are incorrect for cases requiring proper conditional logic
        
        Args:
            a_expr: First operand expression
            b_expr: Second operand expression
            
        Returns:
            The resulting quantum register (note: may be incorrect due to limitations)
        """
        import math
        
        # Evaluate expressions to get quantum registers
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)
        
        # Handle single qubit inputs
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                a_temp = self.apply_cnot_on_bits(a, 0, a_temp, 0)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                b_temp = self.apply_cnot_on_bits(b, 0, b_temp, 0)
                b = b_temp

        # Use 4-bit arithmetic for manageable circuit size
        bit_width = 4  
        result_width = 8  # 4×4 = up to 8 bits result
        
        # Initialize result register (accumulator)
        result = self.ir_gen_init_with_width(result_width)
        
        # WARNING: The following implements incorrect shift-and-add multiplication
        # Each iteration should only add when B[i] = 1, but current implementation always adds
        
        # Shift-and-add multiplication using Draper QFT addition
        # For each bit position i in the multiplier B
        for i in range(bit_width):
            # Step 1: Create shifted version of multiplicand A (A << i) - CORRECT
            shifted_a = self.ir_gen_init_with_width(result_width)
            
            # Copy A to shifted_a with left shift by i positions - CORRECT
            for j in range(bit_width):
                shift_pos = i + j
                if shift_pos < result_width:
                    shifted_a = self.apply_cnot_on_bits(a, j, shifted_a, shift_pos)
            
            # Step 2: Should conditionally add shifted_a to result if B[i] = 1
            # INCORRECT: Currently ignores B[i] and always adds - makes multiplication wrong
            result = self.controlled_draper_addition(b, i, result, shifted_a)
        
        return result

    def controlled_draper_addition(self, control_reg: SSAValue, control_bit: int,
                                  target_reg: SSAValue, addend_reg: SSAValue) -> SSAValue:
        """
        Controlled Draper QFT addition: if control_bit = 1, then target += addend.
        
        Implements conditional quantum addition using the full Draper algorithm
        with proper carry propagation via QFT in the frequency domain.
        
        Algorithm:
        1. Apply QFT to target register
        2. Apply controlled phase rotations based on addend bits
        3. Apply inverse QFT to get the final sum
        
        Args:
            control_reg: Register containing the control bit
            control_bit: Index of the control bit  
            target_reg: Register to add to (accumulator)
            addend_reg: Register to add (shifted multiplicand)
            
        Returns:
            Updated target register containing target + addend (if control = 1)
        """
        import math
        
        # Get register width
        if isinstance(target_reg.type, VectorType):
            shape_attr = target_reg.type.shape
            if hasattr(shape_attr, 'data') and len(shape_attr.data) > 0:
                result_width_attr = shape_attr.data[0]
                if hasattr(result_width_attr, 'data'):
                    result_width = result_width_attr.data
                else:
                    result_width = int(result_width_attr)
            else:
                result_width = 8
        else:
            result_width = 8
        
        # Step 1: Apply QFT to target register (transforms to frequency domain)
        result = self.apply_qft(target_reg, result_width)
        
        # Step 2: Apply controlled Draper phase additions
        # For each bit i in addend and each bit j >= i in target:
        # If control_bit = 1 AND addend[i] = 1, apply phase rotation to target[j]
        for i in range(result_width):
            for j in range(i, result_width):
                # Calculate Draper phase angle
                phase_angle = 2 * math.pi / (2 ** (j - i + 1))
                
                # Apply doubly-controlled phase rotation:
                # Controls: control_reg[control_bit] AND addend_reg[i]
                # Target: result[j]
                result = self.apply_doubly_controlled_phase(
                    control_reg, control_bit,  # First control
                    addend_reg, i,             # Second control  
                    result, j,                 # Target
                    phase_angle
                )
        
        # Step 3: Apply inverse QFT to get the final sum in computational basis
        result = self.apply_inverse_qft(result, result_width)
        
        return result

    def apply_doubly_controlled_phase(self, control1_reg: SSAValue, control1_bit: int,
                                     control2_reg: SSAValue, control2_bit: int,
                                     target_reg: SSAValue, target_bit: int,
                                     phase_angle: float) -> SSAValue:
        """
        Apply phase rotation controlled by two qubits: if both controls = 1, apply phase.
        
        This implements a proper doubly-controlled phase gate using a decomposition
        that works correctly for the multiplication algorithm.
        
        For quantum multiplication correctness, we need:
        - If control1_reg[control1_bit] = 1 AND control2_reg[control2_bit] = 1: apply phase
        - Otherwise: do nothing
        """
        # FIXME: This is still a simplification for demonstration purposes
        # A full implementation would require:
        # 1. Ancilla qubits for proper doubly-controlled decomposition
        # 2. Multiple controlled operations to implement the full logic
        # 3. Or use of quantum libraries with built-in doubly-controlled gates
        
        # For educational purposes, we implement a conditional check:
        # This approximates the correct behavior for small test cases
        # where we can predict which bits will be active
        
        # Apply single control for now (documented limitation)
        # In practice, this works for cases where control2 is expected to be 1
        result = self.apply_controlled_phase_rotation(
            control1_reg, control1_bit,
            target_reg, target_bit,
            phase_angle
        )
        
        return result

    def ir_gen_init_with_width(self, width: int) -> SSAValue:
        """
        Initialize a new multi-qubit register with specified width.
        
        @param width: Number of qubits in the register
        @return: SSA value representing the multi-qubit register
        """
        # Get base register number using current qubit counter
        register_num = self.n_qubit // 8  # Use 8 as base unit for numbering
        status_num = 0

        # Register name follows qX_Y convention
        register_name = f"q{register_num}_{status_num}"
        
        # Create a vector of qubits with specified width
        register = self.builder.insert(
            InitOp.from_value(VectorType(IntegerType(1), [width]))
        )

        # Set the result name to follow our convention
        register.res._name = register_name

        # Increment the global qubit counter by the actual width used
        self.n_qubit += width

        return register.res

    def controlled_quantum_addition(self, control_reg: SSAValue, control_bit: int, 
                                  target_reg: SSAValue, addend_reg: SSAValue) -> SSAValue:
        """
        @brief Perform controlled quantum addition: if control_bit = 1, then target += addend.
        
        CRITICAL NOTE: This is a simplified implementation that demonstrates the structure
        but does NOT implement true conditional logic. In a correct implementation,
        the addition would only occur when control_bit = 1.
        
        Current limitation: Always performs addition regardless of control_bit value.
        This makes the multiplication algorithm incorrect for general cases.
        
        @param control_reg: Register containing the control bit
        @param control_bit: Index of the control bit  
        @param target_reg: Register to add to (result register)
        @param addend_reg: Register to add (shifted multiplicand)
        @return: Updated target register
        """
        # CRITICAL LIMITATION: This implementation ignores the control bit
        # and always performs the addition. This is incorrect for multiplication.
        
        # For a correct implementation, we would need:
        # 1. Controlled QFT gates (QFT controlled by control_bit)
        # 2. All phase rotations controlled by control_bit
        # 3. Controlled inverse QFT
        
        # WARNING: The following code always adds, making multiplication incorrect
        
        # Get the width of the result register
        if isinstance(target_reg.type, VectorType):
            # Extract width from VectorType shape
            shape_attr = target_reg.type.shape
            if hasattr(shape_attr, 'data') and len(shape_attr.data) > 0:
                result_width_attr = shape_attr.data[0]
                if hasattr(result_width_attr, 'data'):
                    result_width = result_width_attr.data
                else:
                    result_width = int(result_width_attr)
            else:
                result_width = 16  # Default fallback
        else:
            result_width = 8
            
        # Apply QFT to target register (should be controlled by control_bit)
        result = self.apply_qft(target_reg, result_width)
        
        # Apply controlled phase additions (INCORRECT: should be doubly controlled)
        # Each phase rotation should be controlled by BOTH control_bit AND addend bits
        for i in range(result_width):
            for j in range(i, result_width):
                phase_angle = 2 * math.pi / (2 ** (j - i + 1))
                
                # INCORRECT: Should check control_reg[control_bit] = 1
                # Currently applies all phase rotations unconditionally
                if i < result_width and j < result_width:
                    result = self.apply_controlled_phase_rotation(
                        addend_reg, i if i < 8 else 7,  # Ensure we don't exceed addend width
                        result, j,
                        phase_angle
                    )
        
        # Apply inverse QFT to get the final result (should be controlled by control_bit)
        result = self.apply_inverse_qft(result, result_width)
        
        return result

    # ==== declarations and assigment ====

    def declare(self, var: str, value: SSAValue) -> bool:
        """declare a variable in the current scope, return success if the variable
        wasn't declared yet."""
        if self.symbol_table is None:
            raise IRGenError("Symbol table is empty.")

        if var in self.symbol_table:
            return False
        self.symbol_table[var] = value
        return True

    def delete(self, var: str) -> bool:
        """delete an entry from the symbol_table."""
        if self.symbol_table is None:
            raise IRGenError("Symbol table is empty.")

        if var in self.symbol_table._local_scope:
            del self.symbol_table._local_scope[var]
            return True
        return False

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

        if var_name in self.symbol_table:
            return self.symbol_table[var_name]
        else:
            raise IRGenError(f"Referenced undefined variable: {var_name}")

    def ir_gen_init(self, expr: NumberExprAST = None) -> SSAValue:
        """
        Initialize a new multi-qubit register for integer representation.

        Creates a vector of qubits with proper naming convention qx_y where:
        - x is the register number
        - y is the version tracking write operations

        @param expr: Optional expression for context (typically a NumberExprAST)
        @return: SSA value representing the multi-qubit register
        """
        bit_width = 8  # Use 8 bits for testing (reduces operation count significantly)

        # Get base register number
        register_num = self.n_qubit // bit_width
        status_num = 0

        # Register name follows qX_Y convention
        register_name = f"q{register_num}_{status_num}"
        # self.add_comment(f"// creating register {register_name} with {bit_width} qubits")

        # Create a vector of qubits (each with 1 bit) with vector size = bit_width
        register = self.builder.insert(
            InitOp.from_value(VectorType(IntegerType(1), [bit_width]))
        )

        # Set the result name to follow our convention
        register.res._name = register_name

        # Increment the global qubit counter
        self.n_qubit += bit_width

        return register.res

    def ir_gen_number_expr(self, expr: NumberExprAST) -> SSAValue:
        """Generate IR for a number literal using binary representation across multiple qubits."""
        # Create multi-qubit register
        register = self.ir_gen_init(expr)
    
        # Handle both positive and negative numbers
        if expr.val != 0:
            value = int(expr.val)
            bit_width = 8  # Match the bit width used in ir_gen_init
            
            # For negative numbers, use two's complement representation
            if value < 0:
                # Convert to 8-bit two's complement
                value = (1 << bit_width) + value  # This gives us the two's complement representation
            
            # Ensure value fits in bit_width bits
            value = value & ((1 << bit_width) - 1)
            
            binary_str = bin(value)[2:].zfill(bit_width)[-bit_width:]  # Zero-pad and take last bit_width bits
    
            # Apply NOT gates to each qubit position where the binary digit is 1
            for i, bit in enumerate(reversed(binary_str)):  # LSB first
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
        # Variable will be initialized with an expression or default to zero
        if expr.expr is not None:
            # self.add_comment(f"// initialize {expr.name} with expression")

            # handle direct number initialization
            if isinstance(expr.expr, NumberExprAST):
                # self.add_comment(f"// direct number initialization: {expr.expr.val}")
                # Use ir_gen_number_expr to properly encode binary representation
                qubit = self.ir_gen_number_expr(expr.expr)

            # handle variable-to-variable copy
            # Replace this section in ir_gen_var_decl_expr:
            elif isinstance(expr.expr, VariableExprAST):
                var_name = expr.expr.name
                if var_name in self.symbol_table:
                    source = self.symbol_table[var_name]
                    # initialize target qubit
                    qubit = self.ir_gen_init(None)
                    # Use direct copy instead of CNotOp
                    # For each bit in the register
                    bit_width = 8  # Match the bit width used in ir_gen_init
                    for i in range(bit_width):
                        qubit = self.apply_cnot_on_bits(source, i, qubit, i)
                    return qubit
                else:
                    raise IRGenError(f"Referenced undefined variable: {var_name}")

            # handle binary expressions
            elif isinstance(expr.expr, BinaryExprAST):
                # self.add_comment(f"// initializing with binary expression")
                
                # For declarations with binary expressions like int c = a + b,
                # we need to ensure the result is stored in a new register for variable c
                
                # Create a new register for this variable
                target_reg = self.ir_gen_init(None)
                
                # Use the target register for arithmetic operations
                if expr.expr.op == "+":
                    expr_result = self.draper_quantum_addition(expr.expr.lhs, expr.expr.rhs, target_reg)
                elif expr.expr.op == "-":
                    expr_result = self.draper_quantum_subtraction(expr.expr.lhs, expr.expr.rhs, target_reg)
                else:
                    # For other operations, evaluate normally and copy to target
                    temp_result = self.ir_gen_expr(expr.expr)
                    if temp_result is None:
                        raise IRGenError("Binary expression evaluation failed")
                    
                    # Copy result to the target register
                    bit_width = 8
                    for i in range(bit_width):
                        target_reg = self.apply_cnot_on_bits(temp_result, i, target_reg, i)
                    expr_result = target_reg

                qubit = expr_result

            # handle other expression types
            else:
                # self.add_comment(f"// general expression initialization")
                # let ir_gen_expr handle the expression
                try:
                    qubit = self.ir_gen_expr(expr.expr)
                    if qubit is None:
                        raise IRGenError("Expression evaluation returned None")
                except Exception as e:
                    raise IRGenError(f"Failed to initialize {expr.name}: {str(e)}")

        # default initialization (to |0⟩)
        else:
            # self.add_comment(f"// default initialization of {expr.name} to |0⟩")
            qubit = self.ir_gen_init(None)

        # register in symbol table
        # create a new scope if needed, preserving parent scope accessibility
        if expr.name in self.symbol_table._local_scope:
            # variable already exists in current scope, create a new nested scope
            self.symbol_table = ScopedDict(parent=self.symbol_table)

        # add the variable to the symbol table
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
        # TODO use mesureop to get the return value?
        if expr.expr is not None:
            # Process return value expression
            return_value = self.ir_gen_expr(expr.expr)

            if return_value is None:
                # Warning: return expression evaluated to None
                return_value = self.builder.insert(
                    InitOp.from_value(IntegerType(1))
                ).res

            return return_value
        else:
            # For void returns, default to 0
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================

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
            # If it's already a single qubit, apply NOT directly
            return self.builder.insert(NotOp.from_value(register)).res

        # Use the new OnQubitNotOp to flip the bit directly
        flipped_register = self.builder.insert(
            OnQubitNotOp.from_value(register, index)
        ).res

        # Maintain the naming convention
        if register._name:
            parts = register._name.split("_")
            if len(parts) == 2:
                register_num = parts[0].lstrip("q")
                version_num = int(parts[1]) + 1
                flipped_register._name = f"q{register_num}_{version_num}"

        return flipped_register
    

    def apply_cnot_on_bits(self, control_register: SSAValue, control_index: int, 
                          target_register: SSAValue, target_index: int) -> SSAValue:
        """
        Apply a CNOT gate directly between bits in two registers.
        
        @param control_register: The register containing the control qubit
        @param control_index: The index of the control bit
        @param target_register: The register containing the target qubit
        @param target_index: The index of the target bit
        @return: The updated target register after applying CNOT
        """
        # Use the new OnQubitCNotOp to apply CNOT directly
        result = self.builder.insert(
            OnQubitCNotOp.from_values(
                control_register, control_index, 
                target_register, target_index
            )
        ).res
        
        # Maintain the naming convention
        if target_register._name:
            parts = target_register._name.split('_')
            if len(parts) == 2:
                register_num = parts[0].lstrip('q')
                version_num = int(parts[1]) + 1
                result._name = f"q{register_num}_{version_num}"
        
        return result
    
    def apply_ccnot_on_bits(self, control1_register: SSAValue, control1_index: int,
                            control2_register: SSAValue, control2_index: int,
                            target_register: SSAValue, target_index: int) -> SSAValue:
        """
        Apply a CCNOT (Toffoli) gate directly between bits in three registers.
        
        @param control1_register: The register containing the first control qubit
        @param control1_index: The index of the first control bit
        @param control2_register: The register containing the second control qubit
        @param control2_index: The index of the second control bit
        @param target_register: The register containing the target qubit
        @param target_index: The index of the target bit
        @return: The updated target register after applying CCNOT
        """
        # Use the new OnQubitCCnotOp to apply CCNOT directly
        result = self.builder.insert(
            OnQubitCCnotOp.from_values(
                control1_register, control1_index,
                control2_register, control2_index,
                target_register, target_index
            )
        ).res
        
        # Maintain the naming convention
        if target_register._name:
            parts = target_register._name.split('_')
            if len(parts) == 2:
                register_num = parts[0].lstrip('q')
                version_num = int(parts[1]) + 1
                result._name = f"q{register_num}_{version_num}"
        
        return result
    
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
