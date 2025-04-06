"""
@file ir_gen.py
@brief IR generator that converts C AST to Quantum IR.

This module implements the IR generation phase of the C to Quantum compiler.
It takes an Abstract Syntax Tree (AST) produced by the parser and generates
corresponding Quantum IR operations using the quantum dialect.

The generator supports basic C constructs such as variable declarations,
assignments, arithmetic operations, function calls, and return statements,
and maps them to appropriate quantum operations.
"""

from __future__ import annotations

# Change this import line
from xdsl.context import Context  # MLContext is in xdsl.context, not xdsl.ir
from xdsl.ir import Block, Region, Operation
from xdsl.dialects.builtin import ModuleOp, IntegerType, VectorType, IntegerAttr
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
)


class IRGenError(Exception):
    """
    @brief Exception raised for errors during IR generation.

    This exception is raised when the IR generator encounters an issue that
    prevents it from generating valid quantum IR, such as unsupported expressions
    or undefined variables.
    """

    pass


# TODO generated IR has nested functions and main is inside operations somehow
class QuantumIRGen:
    """
    @brief IR Generator that converts C AST to Quantum IR.

    This class is responsible for transforming the C Abstract Syntax Tree (AST)
    into Quantum Intermediate Representation (IR) using quantum operations.
    It traverses the AST recursively and generates equivalent quantum operations
    for each C language construct.

    The class maintains a symbol table to keep track of variables and their
    corresponding quantum registers during compilation.

    @see ModuleAST
    @see FunctionAST
    @see Quantum
    """

    def __init__(self):
        """
        @brief Initialize the Quantum IR Generator.

        Creates a new context, loads the quantum dialect, initializes the module,
        builder, and symbol table for IR generation.
        """
        self.context = Context()
        # Load the quantum dialect
        self.context.load_dialect(Quantum)

        # Create a module
        self.module = ModuleOp([])
        self.builder = Builder(InsertPoint.at_end(self.module.body.blocks[0]))
        self.symbol_table = ScopedDict()

    def ir_gen_module(self, module_ast: ModuleAST) -> ModuleOp:
        """
        @brief Generate Quantum IR from C AST Module.

        This is the top-level method that processes an entire C module,
        generating IR for each function defined in the module.

        @param module_ast: The ModuleAST node representing the C module
        @return The generated ModuleOp containing quantum IR
        """
        for func_ast in module_ast.funcs:  # Use the correct attribute name
            self.ir_gen_function(func_ast)

        return self.module

    def ir_gen_function(self, function_ast: FunctionAST):
        """
        @brief Generate a quantum function from a C function AST.

        Creates a new function in the IR with its own region and block,
        processes the function parameters, and generates IR for the function body.

        @param function_ast: The FunctionAST node representing the C function
        """
        # Create a new scope for this function
        self.symbol_table = ScopedDict()

        # Create a function region
        region = Region()
        block = Block()
        region.add_block(block)

        # Create quantum function
        func_name = function_ast.proto.name
        func_op = self.builder.insert(FuncOp(func_name, region))

        # Set insertion point to function body
        self.builder = Builder(InsertPoint.at_end(block))

        # Process function parameters - initialize qubits for each argument
        for arg in function_ast.proto.args:
            # Initialize a qubit for each parameter
            qubit = self.builder.insert(InitOp.from_value(IntegerType(1)))
            self.symbol_table[arg.name] = qubit.res

        # Process function body
        for expr in function_ast.body:
            self.ir_gen_expr(expr)

    def ir_gen_expr(self, expr: ExprAST):
        """
        @brief Generate IR for a C expression.

        This method dispatches to the appropriate method based on the expression type.

        @param expr: The ExprAST node representing a C expression
        @return The resulting quantum value (usually a qubit reference)
        @throws IRGenError if the expression type is unsupported
        """
        # TODO
        if isinstance(expr, BinaryExprAST):
            return self.ir_gen_binary_expr(expr)
        elif isinstance(expr, VariableExprAST):
            return self.ir_gen_variable_expr(expr)
        elif isinstance(expr, NumberExprAST):
            return self.ir_gen_number_expr(expr)
        elif isinstance(expr, VarDeclExprAST):
            return self.ir_gen_var_decl_expr(expr)
        elif isinstance(expr, ReturnExprAST):
            return self.ir_gen_return_expr(expr)
        elif isinstance(expr, CallExprAST):
            return self.ir_gen_call_expr(expr)
        else:
            raise IRGenError(f"Unsupported expression type: {type(expr)}")

    def ir_gen_binary_expr(self, expr: BinaryExprAST):
        """
        @brief Generate quantum operations for binary expressions.

        Handles binary operators like assignment (=), addition (+), and subtraction (-).
        For unsupported operators, uses the left-hand side value as a fallback.

        @param expr: The BinaryExprAST node representing a binary operation
        @return The resulting quantum value
        @throws IRGenError if the left side of an assignment is not a variable
        """
        # Handle assignment separately
        if expr.op == "=":
            if isinstance(expr.lhs, VariableExprAST):
                lhs_name = expr.lhs.name
                rhs = self.ir_gen_expr(expr.rhs)

                # Create a new scope for the updated variable
                # The correct way to create a new scope is with a new ScopedDict instance
                self.symbol_table = ScopedDict(parent=self.symbol_table)
                self.symbol_table[lhs_name] = rhs
                return rhs
            else:
                raise IRGenError("Left side of assignment must be a variable")
        lhs = self.ir_gen_expr(expr.lhs)
        rhs = self.ir_gen_expr(expr.rhs)

        # Handle cases where lhs or rhs might be None
        if lhs is None or rhs is None:
            # Return a default value
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

        if expr.op == "+":
            return self.ir_gen_quantum_addition(lhs, rhs)
        elif expr.op == "-":
            return self.ir_gen_quantum_subtraction(lhs, rhs)
        else:
            # For unsupported operators, use lhs as fallback instead of raising error
            print(
                f"Warning: Unsupported binary operation '{expr.op}', using left side value"
            )
            return lhs

    def ir_gen_quantum_addition(self, a, b):
        """
        @brief Generate quantum circuit for addition.

        Implements a simplified quantum adder using Hadamard gates, CNOT gates,
        and Toffoli gates (CCNOT). This is a simplified implementation that
        demonstrates the concept rather than a full quantum adder.

        @param a: First quantum operand
        @param b: Second quantum operand
        @return The resulting quantum value representing the sum
        """
        # This is a simplified quantum adder implementation
        # In a real quantum computer, addition would be more complex

        # First apply Hadamard to put qubits in superposition
        temp1 = self.builder.insert(HadamardOp.from_value(a)).res

        # Use CNOT gates to entangle qubits
        temp2 = self.builder.insert(CNotOp(temp1, b)).res

        # Add a third qubit for the result
        result = self.builder.insert(InitOp.from_value(IntegerType(1))).res

        # Use a Toffoli gate (CCNOT) for addition
        final = self.builder.insert(CCNotOp(temp1, temp2, result)).res

        return final

    def ir_gen_quantum_subtraction(self, a, b):
        """
        @brief Generate quantum circuit for subtraction.

        Implements subtraction by first inverting the second operand using a NOT gate,
        and then performing addition. This is a simplified implementation.

        @param a: First quantum operand (minuend)
        @param b: Second quantum operand (subtrahend)
        @return The resulting quantum value representing the difference
        """
        # Invert b using a NOT gate
        not_b = self.builder.insert(NotOp.from_value(b)).res

        # Then add a and not_b
        return self.ir_gen_quantum_addition(a, not_b)

    def ir_gen_variable_expr(self, expr: VariableExprAST):
        """
        @brief Generate IR for a variable reference.

        Looks up the variable in the symbol table and returns its quantum value.

        @param expr: The VariableExprAST node representing a variable reference
        @return The quantum value associated with the variable
        @throws IRGenError if the variable is undefined
        """
        if expr.name in self.symbol_table:
            return self.symbol_table[expr.name]
        else:
            raise IRGenError(f"Undefined variable: {expr.name}")

    def ir_gen_number_expr(self, expr: NumberExprAST):
        """
        @brief Generate IR for a number literal.

        Creates a qubit representation of the number. If the number is non-zero,
        applies a NOT gate to flip the qubit to the |1⟩ state.

        @param expr: The NumberExprAST node representing a number literal
        @return The quantum value representing the number
        """
        # Initialize a qubit
        qubit = self.builder.insert(InitOp.from_value(IntegerType(1))).res

        # If the number is non-zero, apply NOT gate to flip it to |1⟩
        if expr.val != 0:
            qubit = self.builder.insert(NotOp.from_value(qubit)).res

        return qubit

    def ir_gen_var_decl_expr(self, expr: VarDeclExprAST):
        """
        @brief Generate IR for a variable declaration.

        Initializes a new qubit for the variable and handles initialization if provided.

        @param expr: The VarDeclExprAST node representing a variable declaration
        @return The quantum value associated with the new variable
        """
        # Initialize a new qubit for this variable
        qubit = self.builder.insert(InitOp.from_value(IntegerType(1))).res

        # Handle initialization if provided
        if expr.expr is not None:
            init_value = self.ir_gen_expr(expr.expr)
            # Update the variable with the initial value
            result = self.builder.insert(CNotOp(init_value, qubit)).res

            # Create a new scope before assigning the initialized value
            self.symbol_table = ScopedDict(parent=self.symbol_table)
            self.symbol_table[expr.name] = result
            return result
        else:
            # Just store the uninitialized qubit
            self.symbol_table[expr.name] = qubit
            return qubit

    def ir_gen_return_expr(self, expr: ReturnExprAST):
        """
        @brief Generate IR for a return statement.

        Evaluates the return expression if provided and measures the quantum state
        to get a classical result. For void returns or errors, provides a default value.

        @param expr: The ReturnExprAST node representing a return statement
        @return The measured quantum value
        """
        try:
            if expr.expr is not None:
                # Evaluate the return expression
                return_value = self.ir_gen_expr(expr.expr)

                # More thorough checking for None or invalid values
                if return_value is None or not hasattr(return_value, "type"):
                    print(
                        f"Warning: Return value is None or missing type attribute, creating default qubit"
                    )
                    return_value = self.builder.insert(
                        InitOp.from_value(IntegerType(1))
                    ).res

                # Measure the quantum state to get a classical result
                result = self.builder.insert(MeasureOp.from_value(return_value)).res
                return result
            else:
                # For void returns, provide a zero qubit
                zero_qubit = self.builder.insert(InitOp.from_value(IntegerType(1))).res
                result = self.builder.insert(MeasureOp.from_value(zero_qubit)).res
                return result
        except Exception as e:
            print(f"Error in return expression: {e}")
            # Fall back to a safe default
            zero_qubit = self.builder.insert(InitOp.from_value(IntegerType(1))).res
            result = self.builder.insert(MeasureOp.from_value(zero_qubit)).res
            return result

    def ir_gen_call_expr(self, expr: CallExprAST):
        """
        @brief Generate IR for a function call.

        Evaluates the function arguments and combines them using quantum operations.
        This is a simplified implementation that doesn't handle actual function calls.

        @param expr: The CallExprAST node representing a function call
        @return The resulting quantum value
        """
        # For simplicity, we'll just evaluate the arguments
        # A full implementation would need to handle function calls properly
        args = [self.ir_gen_expr(arg) for arg in expr.args]

        # For demo purposes, just use the operation results
        if args:
            # Apply some quantum operations to combine the arguments
            result = args[0]
            for arg in args[1:]:
                result = self.builder.insert(CNotOp(result, arg)).res
            return result
        else:
            # Return a new qubit if no arguments
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res
