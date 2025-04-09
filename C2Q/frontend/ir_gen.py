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
    CommentOp
)


class IRGenError(Exception):
    """
    @brief Exception raised for errors during IR generation.

    This exception is raised when the IR generator encounters an issue that
    prevents it from generating valid quantum IR, such as unsupported expressions
    or undefined variables.
    """

    pass


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

    module: ModuleOp
    """A "module" matches a System Verilog source file: containing a list of assignements, functions 
    and processes."""

    builder: Builder
    """The builder is a helper class to create IR inside a function. The builder
    is stateful, in particular it keeps an "insertion point": this is where
    the next operations will be introduced."""

    symbol_table: ScopedDict[str, SSAValue] | None = None
    """The symbol table maps a variable name to a value in the current scope.
    Entering a function creates a new scope, and the function arguments are
    added to the mapping. When the processing of a function is terminated, the
    scope is destroyed and the mappings created in this scope are dropped."""

    n_qubit: int = 0  # n_qubits that used when generating the first IR
    n_args: int = 0  # n_args taken as input

    def __init__(self):
        """
        @brief Initialize the Quantum IR Generator.

        Creates a new context, loads the quantum dialect, initializes the module,
        builder, and symbol table for IR generation.
        """
        self.context = Context()
        # load the quantum dialect
        self.context.load_dialect(Quantum)

        # create a module
        self.module = ModuleOp([])
        self.builder = Builder(InsertPoint.at_end(self.module.body.blocks[0]))
        self.function_map = {}

    # ==== module ====

    def ir_gen_module(self, module_ast: ModuleAST) -> ModuleOp:
        """
        @brief Generate Quantum IR from C AST Module with main as entry point.

        Finds the main function and inlines any function calls within it.

        @param module_ast: The ModuleAST node representing the C module
        @return The generated ModuleOp containing quantum IR
        """
        # create function map for lookup during inlining

        for func_ast in module_ast.funcs:
            self.function_map[func_ast.proto.name] = func_ast

        # find and process main function
        main_func = next((f for f in module_ast.funcs if f.proto.name == "main"), None)
        if main_func:
            self.ir_gen_main_function(main_func)
        else:
            raise IRGenError("No main function found in the module")

        return self.module

    # === functions ====

    def ir_gen_main_function(self, main_func: FunctionAST) -> FuncOp:
        """
        @brief Generate IR for the main function, finding and unrolling function calls.

        Parses operations inside main and when it finds a function call,
        retrieves that function from the AST and unrolls it using ir_func_call.

        @param main_func: The FunctionAST node representing the main function
        """
        self.add_comment("// Begin main function")

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
        for arg in func_op.regions[0].blocks[0]._args:
            self.add_comment(f"// Initialize main parameter: {arg.name}")
            qubit = self.builder.insert(InitOp.from_value(IntegerType(1)))
            self.symbol_table[arg._name] = qubit.res

        # process main function body
        result = None
        for expr in main_func.body:
            self.ir_gen_expr(expr)

        self.add_comment("// End main function")

    def ir_gen_func_call(self, func_ast: FunctionAST, args: list[ExprAST]):
        """
        @brief Generate IR for a function call by inlining the function body.

        This method retrieves the function's AST and generates IR for its body,
        substituting the arguments with the provided values.

        @param func_ast: The FunctionAST node representing the function to be called
        @param args: The list of arguments passed to the function
        """
        # TODO handle function return value
        self.add_comment(f"// Function call: {func_ast.proto.name}")

        # create a new scope for the function call
        self.symbol_table = ScopedDict(parent=self.symbol_table)

        # process function parameters and arguments
        for param, arg in zip(func_ast.proto.args, args):
            qubit = self.ir_gen_expr(arg)
            self.symbol_table[param.name] = qubit

        # process function body
        for expr in func_ast.body:
            self.ir_gen_expr(expr)

    def ir_gen_call_expr(self, expr: CallExprAST):
        """
        @brief Generate IR for a function call.

        Evaluates the function arguments and combines them using quantum operations.
        This is a simplified implementation that doesn't handle actual function calls.

        @param expr: The CallExprAST node representing a function call
        @return The resulting quantum value
        """
        called_func = next((f for f in self.function_map if f == expr.callee), None)

        if called_func is None:
            raise IRGenError(f"Function {expr.callee} not found")
        else:
            self.add_comment(f"// Function call: {expr.callee}")

            # unroll the function call
            func_ast = self.function_map[expr.callee]
            self.ir_gen_func_call(func_ast, expr.args)

    # ==== ast parsing handler ====

    def ir_gen_expr(self, expr: ExprAST):
        """
        @brief Generate IR for a C expression.

        This method dispatches to the appropriate method based on the expression type.

        @param expr: The ExprAST node representing a C expression
        @return The resulting quantum value (usually a qubit reference)
        @throws IRGenError if the expression type is unsupported
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
        else:
            raise IRGenError(f"Unsupported expression type: {type(expr)}")

    # TODO
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

        # handle assignment separately
        if expr.op == "=":
            if isinstance(expr.lhs, VariableExprAST):
                lhs_name = expr.lhs.name
                self.add_comment(f"// Assignment to variable: {lhs_name}")
                rhs = self.ir_gen_expr(expr.rhs)

                # create a new scope for the updated variable
                self.symbol_table = ScopedDict(parent=self.symbol_table)
                self.symbol_table[lhs_name] = rhs
                return rhs
            else:
                raise IRGenError("Left side of assignment must be a variable")

        # for other operations, evaluate both sides
        lhs = self.ir_gen_expr(expr.lhs)
        rhs = self.ir_gen_expr(expr.rhs)

        # handle cases where lhs or rhs might be None
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

    # ==== operations ====

    def ir_gen_quantum_addition(self, a, b) -> SSAValue:
        """
        @brief Generate quantum circuit for addition.

        Implements a simplified quantum adder using Hadamard gates, CNOT gates,
        and Toffoli gates (CCNOT). This is a simplified implementation that
        demonstrates the concept rather than a full quantum adder.

        @param a: First quantum operand
        @param b: Second quantum operand
        @return The resulting quantum value representing the sum
        """
        # this is a simplified quantum adder implementation
        # in a real quantum computer, addition would be more complex

        # first apply Hadamard to put qubits in superposition
        temp1 = self.builder.insert(HadamardOp.from_value(a)).res

        # use CNOT gates to entangle qubits
        temp2 = self.builder.insert(CNotOp(temp1, b)).res

        # add a third qubit for the result
        result = self.builder.insert(InitOp.from_value(IntegerType(1))).res

        # use a Toffoli gate (CCNOT) for addition
        final = self.builder.insert(CCNotOp(temp1, temp2, result)).res

        return final

    def ir_gen_quantum_subtraction(self, a, b) -> SSAValue:
        """
        @brief Generate quantum circuit for subtraction.

        Implements subtraction by first inverting the second operand using a NOT gate,
        and then performing addition. This is a simplified implementation.

        @param a: First quantum operand (minuend)
        @param b: Second quantum operand (subtrahend)
        @return The resulting quantum value representing the difference
        """
        # invert b using a NOT gate
        not_b = self.builder.insert(NotOp.from_value(b)).res

        # then add a and not_b
        return self.ir_gen_quantum_addition(a, not_b)

    # ==== declarations and assigment ====

    def declare(self, var: str, value: SSAValue) -> bool:
        """Declare a variable in the current scope, return success if the variable
        wasn't declared yet."""
        if self.symbol_table is None:
            raise IRGenError("Symbol table is empty.")

        if var in self.symbol_table:
            return False
        self.symbol_table[var] = value
        return True

    def delete(self, var: str) -> bool:
        """Delete an entry from the symbol_table."""
        if self.symbol_table is None:
            raise IRGenError("Symbol table is empty.")

        if var in self.symbol_table._local_scope:
            del self.symbol_table._local_scope[var]
            return True
        return False

    def ir_gen_init(self, expr: NumberExprAST) -> SSAValue:
        """
        Initialize a new qubit with proper tracking of qubit number and status.
        
        Follows the naming convention qX_Y where:
        - X is the qubit number (position)
        - Y is the status number tracking write operations on that qubit
        
        @param expr: The expression to initialize (typically a NumberExprAST)
        @return: The resulting SSA value with proper tracking information
        """

        bit_width = 32 # Default bit width for integers #TODO add floats in the future

        # Get the next available qubit number
        qubit_num = self.n_qubit
        # Initialize status to 0 for a new qubit
        status_num = 0
        
        # Create the qubit with proper naming convention
        qubit_name = f"q{qubit_num}_{status_num}"
        self.add_comment(f"// Creating qubit with name: {qubit_name}")
        
        # Create the qubit using InitOp
        qubit = self.builder.insert(InitOp.from_value(IntegerType(bit_width)))
        
        # Set the SSA value name to follow our convention
        qubit.res._name = qubit_name
        
        # Increment the global qubit counter
        self.n_qubit += bit_width
        
        return qubit.res
    
    def update_qubit_status(self, qubit: SSAValue) -> SSAValue:
        """
        Update the status number of a qubit after a write operation.
        
        @param qubit: The qubit SSA value to update
        @return: The same qubit with updated status number
        """
        if qubit and qubit._name:
            parts = qubit._name.split('_')
            if len(parts) == 2:
                qubit_num = parts[0].lstrip('q')
                status_num = int(parts[1]) + 1
                qubit._name = f"q{qubit_num}_{status_num}"
        return qubit

    def ir_gen_number_expr(self, expr: NumberExprAST) -> SSAValue:
        """
        @brief Generate IR for a number literal with improved bit representation.
    
        @param expr: The NumberExprAST node representing a number literal
        @return The quantum value representing the number
        """
        self.add_comment(f"// Initialize number literal: {expr.val}")
    
        qubit = self.ir_gen_init(expr)
    
        # If the number is non-zero, apply NOT gate to flip it to |1⟩
        if expr.val != 0:
            result = self.builder.insert(NotOp.from_value(qubit)).res
            result = self.update_qubit_status(result)
            qubit = result
    
        return qubit

    def ir_gen_var_decl_expr(self, expr: VarDeclExprAST) -> SSAValue:
        """
        @brief Generate IR for a variable declaration with proper qubit tracking.
    
        Creates a new qubit register with the qX_Y naming convention where:
        - X represents the qubit number (position)
        - Y represents the status number tracking write operations
        
        Maintains SSA (Static Single Assignment) form by tracking qubit state changes.
    
        @param expr: The VarDeclExprAST node representing a variable declaration
        @return The quantum value associated with the new variable
        """
        self.add_comment(f"// Declare variable: {expr.name}")
        
        # Variable will be initialized with an expression or default to zero
        if expr.expr is not None:
            self.add_comment(f"// Initialize {expr.name} with expression")
            
            # Handle direct number initialization
            if isinstance(expr.expr, NumberExprAST):
                value = expr.expr.val
                self.add_comment(f"// Direct number initialization: {value}")
                
                # Use ir_gen_init to create a properly tracked qubit
                qubit = self.ir_gen_init(expr.expr)
                
                # Apply NOT gate for non-zero values and update status
                if value != 0:
                    result = self.builder.insert(NotOp.from_value(qubit)).res
                    result = self.update_qubit_status(result)
                    qubit = result
            
            # Handle variable-to-variable copy
            elif isinstance(expr.expr, VariableExprAST):
                var_name = expr.expr.name
                self.add_comment(f"// Copying from variable: {var_name}")
                
                if var_name in self.symbol_table:
                    source = self.symbol_table[var_name]
                    # Initialize target qubit
                    qubit = self.ir_gen_init(None)
                    # Use CNOT to copy state
                    result = self.builder.insert(CNotOp(source, qubit)).res
                    # Update the status to track the operation
                    result = self.update_qubit_status(result)
                    qubit = result
                else:
                    raise IRGenError(f"Referenced undefined variable: {var_name}")
            
            # Handle binary expressions
            elif isinstance(expr.expr, BinaryExprAST):
                self.add_comment(f"// Initializing with binary expression")
                # Evaluate the binary expression first
                expr_result = self.ir_gen_expr(expr.expr)
                
                if expr_result is None:
                    raise IRGenError("Binary expression evaluation failed")
                    
                # No need to create a new qubit - use the result directly
                qubit = expr_result
            
            # Handle other expression types
            else:
                self.add_comment(f"// General expression initialization")
                # Let ir_gen_expr handle the expression
                try:
                    qubit = self.ir_gen_expr(expr.expr)
                    if qubit is None:
                        raise IRGenError("Expression evaluation returned None")
                except Exception as e:
                    raise IRGenError(f"Failed to initialize {expr.name}: {str(e)}")
        
        # Default initialization (to |0⟩)
        else:
            self.add_comment(f"// Default initialization of {expr.name} to |0⟩")
            qubit = self.ir_gen_init(None)
        
        # Register in symbol table
        # Create a new scope if needed, preserving parent scope accessibility
        if expr.name in self.symbol_table._local_scope:
            # Variable already exists in current scope, create a new nested scope
            self.symbol_table = ScopedDict(parent=self.symbol_table)
        
        # Add the variable to the symbol table
        self.symbol_table[expr.name] = qubit
        
        return qubit

    def ir_gen_return_expr(self, expr: ReturnExprAST) -> SSAValue:
        """
        @brief Generate IR for a return statement with improved return value handling.

        @param expr: The ReturnExprAST node representing a return statement
        @return The quantum value to be returned
        """
        # TODO use mesureOP to get the return value?
        if expr.expr is not None:
            self.add_comment(f"// Process return value expression")
            return_value = self.ir_gen_expr(expr.expr)

            if return_value is None:
                self.add_comment("// Warning: Return expression evaluated to None")
                return_value = self.builder.insert(
                    InitOp.from_value(IntegerType(1))
                ).res

            return return_value
        else:
            # for void returns
            self.add_comment("// Void return (default to 0)")
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

    def add_comment(self, comment_text):
        """
        @brief Add a comment to the IR for debugging and clarity without creating dummy qubits.
        
        @param comment_text: The comment text to add
        """
        # Just create a dedicated comment operation instead of a dummy qubit
        self.builder.insert(CommentOp(comment_text.lstrip("// ")))
