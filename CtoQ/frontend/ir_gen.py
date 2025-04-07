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
from xdsl.dialects.builtin import ModuleOp, IntegerType, VectorType, IntegerAttr, StringAttr
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
        @brief Generate Quantum IR from C AST Module with main as entry point.
        
        Finds the main function and inlines any function calls within it.
        
        @param module_ast: The ModuleAST node representing the C module
        @return The generated ModuleOp containing quantum IR
        """
        # Create function map for lookup during inlining
        self.function_map = {}
        for func_ast in module_ast.funcs:
            self.function_map[func_ast.proto.name] = func_ast
            
        # Find and process main function
        main_func = next((f for f in module_ast.funcs if f.proto.name == "main"), None)
        if main_func:
            self.ir_gen_main_function(main_func)
        else:
            # Fallback to old behavior if no main is found
            for func_ast in module_ast.funcs:
                self.ir_gen_function(func_ast)
                
        return self.module
    
    def ir_gen_main_function(self, main_func: FunctionAST):
        """
        @brief Generate IR for the main function with enhanced tracking and inlining.
        
        @param main_func: The FunctionAST node representing the main function
        """
        self.add_comment("// Begin main function")
        
        # Create a new scope for the main function
        self.symbol_table = ScopedDict()
        
        # Create a function region
        region = Region()
        block = Block()
        region.add_block(block)
        
        # Create quantum function
        func_op = self.builder.insert(FuncOp("main", region))
        
        # Set insertion point to function body
        self.builder = Builder(InsertPoint.at_end(block))
        
        # Process function parameters
        for arg in main_func.proto.args:
            self.add_comment(f"// Initialize main parameter: {arg.name}")
            qubit = self.builder.insert(InitOp.from_value(IntegerType(1)))
            self.symbol_table[arg.name] = qubit.res
            
        # Process main function body with inlining
        result = None
        for expr in main_func.body:
            if isinstance(expr, ReturnExprAST):
                self.add_comment("// Return from main")
                if expr.expr:
                    result = self.ir_gen_expr(expr.expr)
                    # Measure the return value
                    self.add_comment("// Measure final return value")
                    measured = self.builder.insert(MeasureOp.from_value(result)).res
                break
            else:
                temp = self.ir_gen_expr_with_inlining(expr)
                # Track the last expression result as potential return value
                if temp is not None:
                    result = temp
        
        # If we didn't already measure a return value, do it now
        if result is not None and not isinstance(expr, ReturnExprAST):
            self.add_comment("// Measure final result value")
            measured = self.builder.insert(MeasureOp.from_value(result)).res
            
        self.add_comment("// End main function")

    def ir_gen_expr_with_inlining(self, expr: ExprAST):
        """
        @brief Generate IR for an expression with function call inlining.
        
        @param expr: The ExprAST node representing a C expression
        @return The resulting quantum value
        """
        if isinstance(expr, CallExprAST):
            return self.ir_gen_call_expr_inlined(expr)
        else:
            return self.ir_gen_expr(expr)
        
    def ir_gen_call_expr_inlined(self, expr: CallExprAST):
        """
        @brief Generate IR for a function call by inlining the function body with enhanced tracking.
        
        @param expr: The CallExprAST node representing a function call
        @return The resulting quantum value from the inlined function
        """
        func_name = expr.callee
        self.add_comment(f"// Begin inlined function: {func_name}")
        
        if func_name not in self.function_map:
            self.add_comment(f"// Function {func_name} not found, using external call")
            return self.ir_gen_call_expr(expr)
            
        called_func = self.function_map[func_name]
        
        # Evaluate all arguments in the caller's context
        arg_values = []
        for i, arg in enumerate(expr.args):
            self.add_comment(f"// Evaluate argument {i} for {func_name}")
            arg_values.append(self.ir_gen_expr(arg))
        
        # Create a new scope for the inlined function
        old_symbol_table = self.symbol_table
        self.symbol_table = ScopedDict(parent=old_symbol_table)
        
        # Map formal parameters to argument values
        for i, (param, arg_val) in enumerate(zip(called_func.proto.args, arg_values)):
            self.add_comment(f"// Map parameter {param.name} to argument value")
            self.symbol_table[param.name] = arg_val
            
        # Execute the function body
        result = None
        for body_expr in called_func.body:
            if isinstance(body_expr, ReturnExprAST):
                # For return statements, evaluate the expression and break
                self.add_comment(f"// Return statement in {func_name}")
                if body_expr.expr:
                    result = self.ir_gen_expr(body_expr.expr)
                break
            else:
                # For other statements, just execute them
                self.ir_gen_expr(body_expr)
                
        # Restore the caller's symbol table
        self.symbol_table = old_symbol_table
        
        # If no return value was found, create a default one
        if result is None:
            self.add_comment(f"// No return value found in {func_name}, creating default")
            result = self.builder.insert(InitOp.from_value(IntegerType(1))).res
        
        self.add_comment(f"// End inlined function: {func_name}")    
        return result

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
        @brief Generate quantum operations for binary expressions with improved tracking.
        
        @param expr: The BinaryExprAST node representing a binary operation
        @return The resulting quantum value
        """
        operation_str = ""
        if isinstance(expr.lhs, VariableExprAST):
            lhs_str = expr.lhs.name
        else:
            lhs_str = "expression"
            
        if isinstance(expr.rhs, VariableExprAST):
            rhs_str = expr.rhs.name
        elif isinstance(expr.rhs, NumberExprAST):
            rhs_str = str(expr.rhs.val)
        else:
            rhs_str = "expression"
            
        self.add_comment(f"// Binary operation: {lhs_str} {expr.op} {rhs_str}")
            
        # Handle assignment separately
        if expr.op == "=":
            if isinstance(expr.lhs, VariableExprAST):
                lhs_name = expr.lhs.name
                self.add_comment(f"// Assignment to variable: {lhs_name}")
                rhs = self.ir_gen_expr(expr.rhs)

                # Create a new scope for the updated variable
                self.symbol_table = ScopedDict(parent=self.symbol_table)
                self.symbol_table[lhs_name] = rhs
                return rhs
            else:
                raise IRGenError("Left side of assignment must be a variable")
                
        # For other operations, evaluate both sides
        lhs = self.ir_gen_expr(expr.lhs)
        rhs = self.ir_gen_expr(expr.rhs)

        # Handle cases where lhs or rhs might be None
        if lhs is None or rhs is None:
            self.add_comment("// Warning: Null operand in binary operation")
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

        if expr.op == "+":
            self.add_comment(f"// Perform quantum addition")
            return self.ir_gen_quantum_addition(lhs, rhs)
        elif expr.op == "-":
            self.add_comment(f"// Perform quantum subtraction")
            return self.ir_gen_quantum_subtraction(lhs, rhs)
        else:
            self.add_comment(f"// Unsupported binary operation: {expr.op}")
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
        @brief Generate IR for a number literal with improved bit representation.
        
        @param expr: The NumberExprAST node representing a number literal
        @return The quantum value representing the number
        """
        self.add_comment(f"// Initialize number literal: {expr.val}")
        
        # For simplicity, we'll use single-bit representation for demo purposes
        # A real implementation would use multiple qubits for integers
        qubit = self.builder.insert(InitOp.from_value(IntegerType(1))).res

        # If the number is non-zero, apply NOT gate to flip it to |1⟩
        if expr.val != 0:
            qubit = self.builder.insert(NotOp.from_value(qubit)).res
            
        return qubit

    def ir_gen_var_decl_expr(self, expr: VarDeclExprAST):
        """
        @brief Generate IR for a variable declaration with improved initialization.
        
        @param expr: The VarDeclExprAST node representing a variable declaration
        @return The quantum value associated with the new variable
        """
        self.add_comment(f"// Declare variable: {expr.name}")
        
        # Initialize a new qubit for this variable
        qubit = self.builder.insert(InitOp.from_value(IntegerType(1))).res

        # Handle initialization if provided
        if expr.expr is not None:
            self.add_comment(f"// Initialize {expr.name} with value")
            init_value = self.ir_gen_expr(expr.expr)
            
            # Use CNOT to copy the value from init_value to qubit
            # This assumes init_value is properly set (0 or 1)
            result = self.builder.insert(CNotOp(init_value, qubit)).res
            
            # Register in symbol table with new scope
            self.symbol_table = ScopedDict(parent=self.symbol_table)
            self.symbol_table[expr.name] = result
            return result
        else:
            # Just store the uninitialized qubit
            self.symbol_table[expr.name] = qubit
            return qubit

    def ir_gen_return_expr(self, expr: ReturnExprAST):
        """
        @brief Generate IR for a return statement with improved return value handling.
        
        @param expr: The ReturnExprAST node representing a return statement
        @return The quantum value to be returned
        """
        if expr.expr is not None:
            self.add_comment(f"// Process return value expression")
            return_value = self.ir_gen_expr(expr.expr)
            
            if return_value is None:
                self.add_comment("// Warning: Return expression evaluated to None")
                return_value = self.builder.insert(InitOp.from_value(IntegerType(1))).res
                
            return return_value
        else:
            # For void returns
            self.add_comment("// Void return (default to 0)")
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

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

    def add_comment(self, comment_text):
            """
            @brief Add a comment to the IR for debugging and clarity
            
            @param comment_text: The comment text to add
            """
            # We'll use a custom attribute in the InitOp with a special marker
            # Since MLIR/xDSL doesn't have direct comment support, this is a workaround
            dummy_op = self.builder.insert(InitOp.from_value(IntegerType(1)))
            dummy_op.attributes["comment"] = StringAttr(comment_text)
            # Don't use the result to ensure it gets eliminated in optimization
