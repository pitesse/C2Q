"""
@file ir_gen.py
@brief ir generator that converts c ast to quantum ir.

this module implements the ir generation phase of the c to quantum compiler.
it takes an abstract syntax tree (ast) produced by the parser and generates
corresponding quantum ir operations using the quantum dialect.

the generator supports basic c constructs such as variable declarations,
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
    CommentOp,
    ExtractBitOp,
    InsertBitOp,
)


class IRGenError(Exception):
    """
    @brief exception raised for errors during ir generation.

    this exception is raised when the ir generator encounters an issue that
    prevents it from generating valid quantum ir, such as unsupported expressions
    or undefined variables.
    """

    pass


class QuantumIRGen:
    """
    @brief ir generator that converts c ast to quantum ir.

    this class is responsible for transforming the c abstract syntax tree (ast)
    into quantum intermediate representation (ir) using quantum operations.
    it traverses the ast recursively and generates equivalent quantum operations
    for each c language construct.

    the class maintains a symbol table to keep track of variables and their
    corresponding quantum registers during compilation.

    @see moduleast
    @see functionast
    @see quantum
    """

    module: ModuleOp
    """a "module" matches a system verilog source file: containing a list of assignements, functions 
    and processes."""

    builder: Builder
    """the builder is a helper class to create ir inside a function. the builder
    is stateful, in particular it keeps an "insertion point": this is where
    the next operations will be introduced."""

    symbol_table: ScopedDict[str, SSAValue] | None = None
    """the symbol table maps a variable name to a value in the current scope.
    entering a function creates a new scope, and the function arguments are
    added to the mapping. when the processing of a function is terminated, the
    scope is destroyed and the mappings created in this scope are dropped."""

    n_qubit: int = 0  # n_qubits that used when generating the first ir
    n_args: int = 0  # n_args taken as input

    def __init__(self):
        """
        @brief initialize the quantum ir generator.

        creates a new context, loads the quantum dialect, initializes the module,
        builder, and symbol table for ir generation.
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
        @brief generate quantum ir from c ast module with main as entry point.

        finds the main function and inlines any function calls within it.

        @param module_ast: the moduleast node representing the c module
        @return the generated moduleop containing quantum ir
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
        @brief generate ir for the main function, finding and unrolling function calls.

        parses operations inside main and when it finds a function call,
        retrieves that function from the ast and unrolls it using ir_func_call.

        @param main_func: the functionast node representing the main function
        """
        self.add_comment("// begin main function")

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
            self.add_comment(f"// initialize main parameter: {arg.name}")
            qubit = self.builder.insert(InitOp.from_value(IntegerType(1)))
            self.symbol_table[arg._name] = qubit.res

        # process main function body
        result = None
        for expr in main_func.body:
            self.ir_gen_expr(expr)

        self.add_comment("// end main function")

    def ir_gen_func_call(self, func_ast: FunctionAST, args: list[ExprAST]):
        """
        @brief generate ir for a function call by inlining the function body.

        this method retrieves the function's ast and generates ir for its body,
        substituting the arguments with the provided values.

        @param func_ast: the functionast node representing the function to be called
        @param args: the list of arguments passed to the function
        """
        # TODO handle function return value
        self.add_comment(f"// function call: {func_ast.proto.name}")

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
        @brief generate ir for a function call.

        evaluates the function arguments and combines them using quantum operations.
        this is a simplified implementation that doesn't handle actual function calls.

        @param expr: the callexprast node representing a function call
        @return the resulting quantum value
        """
        called_func = next((f for f in self.function_map if f == expr.callee), None)

        if called_func is None:
            raise IRGenError(f"Function {expr.callee} not found")
        else:
            self.add_comment(f"// function call: {expr.callee}")

            # unroll the function call
            func_ast = self.function_map[expr.callee]
            self.ir_gen_func_call(func_ast, expr.args)

    # ==== ast parsing handler ====

    def ir_gen_expr(self, expr: ExprAST):
        """
        @brief generate ir for a c expression.

        this method dispatches to the appropriate method based on the expression type.

        @param expr: the exprast node representing a c expression
        @return the resulting quantum value (usually a qubit reference)
        @throws irgenerror if the expression type is unsupported
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
        @brief generate quantum operations for binary expressions with improved tracking.

        @param expr: the binaryexprast node representing a binary operation
        @return the resulting quantum value
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

        self.add_comment(f"// binary operation: {lhs_str} {expr.op} {rhs_str}")

        # handle assignment separately
        if expr.op == "=":
            if isinstance(expr.lhs, VariableExprAST):
                lhs_name = expr.lhs.name
                self.add_comment(f"// assignment to variable: {lhs_name}")
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

        # handle cases where lhs or rhs might be none
        if lhs is None or rhs is None:
            self.add_comment("// warning: null operand in binary operation")
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

        if expr.op == "+":
            self.add_comment(f"// perform quantum addition")
            return self.ir_gen_quantum_addition(lhs, rhs)
        elif expr.op == "-":
            self.add_comment(f"// perform quantum subtraction")
            return self.ir_gen_quantum_subtraction(lhs, rhs)
        else:
            self.add_comment(f"// unsupported binary operation: {expr.op}")
            return lhs

    # ==== operations ====

    def ir_gen_quantum_addition(self, a: SSAValue, b: SSAValue) -> SSAValue:
        """
        Generate quantum circuit for addition of multi-qubit registers.
        
        Implements a quantum adder for registers representing integers.
        
        @param a: First multi-qubit operand register
        @param b: Second multi-qubit operand register
        @return: The resulting register representing the sum
        """
        self.add_comment(f"quantum addition of registers {a._name} and {b._name}")
        
        # Create a result register
        result = self.ir_gen_init(None)
        
        # Implement a quantum adder circuit that works bit by bit
        bit_width = 32  # Same as in ir_gen_init
        carry = None
        
        for i in range(bit_width):
            # Extract bits from both operands
            a_bit = self.get_qubit(a, i)
            b_bit = self.get_qubit(b, i)
            
            if i == 0:
                # First bit - simpler addition without previous carry
                self.add_comment(f"adding least significant bits (position {i})")
                
                # Apply Hadamard to put a_bit in superposition
                temp1 = self.builder.insert(HadamardOp.from_value(a_bit)).res
                
                # Use CNOT to entangle with b_bit
                temp2 = self.builder.insert(CNotOp(temp1, b_bit)).res
                
                # Initialize result bit
                result_bit = self.builder.insert(InitOp.from_value(IntegerType(1))).res
                
                # Use Toffoli (CCNOT) for the sum bit
                sum_bit = self.builder.insert(CCNotOp(temp1, temp2, result_bit)).res
                
                # Set this bit in the result register
                result = self.set_qubit(result, i, sum_bit)
                
                # Generate carry bit for next position using CNOT
                carry = self.builder.insert(InitOp.from_value(IntegerType(1))).res
                carry = self.builder.insert(CNotOp(a_bit, b_bit)).res
            else:
                # For subsequent bits, include carry from previous bit
                self.add_comment(f"adding bits with carry at position {i}")
                
                # Create a temporary qubit for this bit's result
                sum_bit = self.builder.insert(InitOp.from_value(IntegerType(1))).res
                
                # Simplified quantum full adder
                # (In a real implementation, this would be more complex)
                sum_bit = self.builder.insert(CNotOp(a_bit, sum_bit)).res
                sum_bit = self.builder.insert(CNotOp(b_bit, sum_bit)).res
                sum_bit = self.builder.insert(CNotOp(carry, sum_bit)).res
                
                # Set this bit in the result register
                result = self.set_qubit(result, i, sum_bit)
                
                # Update carry for next bit
                new_carry = self.builder.insert(InitOp.from_value(IntegerType(1))).res
                new_carry = self.builder.insert(CCNotOp(a_bit, b_bit, new_carry)).res
                carry = new_carry
        
        # Apply proper naming to the result register
        result = self.update_qubit_status(result)
        
        return result

    def ir_gen_quantum_subtraction(self, a, b) -> SSAValue:
        """
        @brief generate quantum circuit for subtraction.

        implements subtraction by first inverting the second operand using a not gate,
        and then performing addition. this is a simplified implementation.

        @param a: first quantum operand (minuend)
        @param b: second quantum operand (subtrahend)
        @return the resulting quantum value representing the difference
        """
        # invert b using a not gate
        not_b = self.builder.insert(NotOp.from_value(b)).res

        # then add a and not_b
        return self.ir_gen_quantum_addition(a, not_b)

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

    def ir_gen_init(self, expr: NumberExprAST = None) -> SSAValue:
        """
        Initialize a new multi-qubit register for integer representation.
        
        Creates a vector of qubits with proper naming convention qx_y where:
        - x is the register number
        - y is the version tracking write operations
        
        @param expr: Optional expression for context (typically a NumberExprAST)
        @return: SSA value representing the multi-qubit register
        """
        bit_width = 32  # default bit width for integers
        
        # Get base register number
        register_num = self.n_qubit // bit_width
        status_num = 0
        
        # Register name follows qX_Y convention
        register_name = f"q{register_num}_{status_num}"
        self.add_comment(f"// creating register {register_name} with {bit_width} qubits")
        
        # Create a vector of qubits (each with 1 bit) with vector size = bit_width
        register = self.builder.insert(
            InitOp.from_value(VectorType(IntegerType(1), [bit_width]))
        )
        
        # Set the result name to follow our convention
        register.res._name = register_name
        
        # Increment the global qubit counter
        self.n_qubit += bit_width
        
        return register.res
    
    def update_qubit_status(self, register: SSAValue) -> SSAValue:
        """
        Update the version number of a register after a modification.
        
        @param register: The register SSA value to update
        @return: The same register with updated version number
        """
        if register and register._name:
            parts = register._name.split('_')
            if len(parts) == 2:
                register_num = parts[0].lstrip('q')
                version_num = int(parts[1]) + 1
                register._name = f"q{register_num}_{version_num}"
                self.add_comment(f"// updated register to version: {register._name}")
        return register

    def ir_gen_number_expr(self, expr: NumberExprAST) -> SSAValue:
        """
        Generate IR for a number literal using binary representation across multiple qubits.
        
        @param expr: the NumberExprAST node representing a number literal
        @return the quantum register representing the number
        """
        self.add_comment(f"initialize number literal: {expr.val}")
        
        # Create multi-qubit register
        register = self.ir_gen_init(expr)
        
        # If value is non-zero, we need to encode it using binary representation
        if expr.val != 0:
            value = int(expr.val)
            self.add_comment(f"encoding value {value} in binary across qubits")
            
            # Convert to binary and remove '0b' prefix
            binary_str = bin(value)[2:]  
            
            # Handle proper bit width for the register
            bit_width = 32  # Same as in ir_gen_init
            binary_str = binary_str.zfill(bit_width)[-bit_width:]  # Zero-pad and take last bit_width bits
            
            # Apply NOT gates to each qubit position where the binary digit is 1
            for i, bit in enumerate(reversed(binary_str)):  # LSB first
                if bit == '1':
                    self.add_comment(f"flipping bit {i} for value {value}")
                    
                    # Extract the qubit
                    qubit = self.get_qubit(register, i)
                    
                    # Apply NOT operation to flip from |0⟩ to |1⟩
                    flipped_qubit = self.builder.insert(NotOp.from_value(qubit)).res
                    
                    # Update the register with the modified qubit
                    register = self.set_qubit(register, i, flipped_qubit)
            
            # Update the register version to track the changes
            register = self.update_qubit_status(register)
            self.add_comment(f"binary encoding complete for {expr.val}")
        
        return register

    def ir_gen_var_decl_expr(self, expr: VarDeclExprAST) -> SSAValue:
        """
        @brief generate ir for a variable declaration with proper qubit tracking.
    
        creates a new qubit register with the qx_y naming convention where:
        - x represents the qubit number (position)
        - y represents the status number tracking write operations
        
        maintains ssa (static single assignment) form by tracking qubit state changes.
    
        @param expr: the vardeclexprast node representing a variable declaration
        @return the quantum value associated with the new variable
        """
        self.add_comment(f"// declare variable: {expr.name}")
        
        # variable will be initialized with an expression or default to zero
        if expr.expr is not None:
            self.add_comment(f"// initialize {expr.name} with expression")
            
            # handle direct number initialization
            if isinstance(expr.expr, NumberExprAST):
                value = expr.expr.val
                self.add_comment(f"// direct number initialization: {value}")
                
                # use ir_gen_init to create a properly tracked qubit
                qubit = self.ir_gen_init(expr.expr)
                
                # apply not gate for non-zero values and update status
                if value != 0:
                    result = self.builder.insert(NotOp.from_value(qubit)).res
                    result = self.update_qubit_status(result)
                    qubit = result
            
            # handle variable-to-variable copy
            elif isinstance(expr.expr, VariableExprAST):
                var_name = expr.expr.name
                self.add_comment(f"// copying from variable: {var_name}")
                
                if var_name in self.symbol_table:
                    source = self.symbol_table[var_name]
                    # initialize target qubit
                    qubit = self.ir_gen_init(None)
                    # use cnot to copy state
                    result = self.builder.insert(CNotOp(source, qubit)).res
                    # update the status to track the operation
                    result = self.update_qubit_status(result)
                    qubit = result
                else:
                    raise IRGenError(f"Referenced undefined variable: {var_name}")
            
            # handle binary expressions
            elif isinstance(expr.expr, BinaryExprAST):
                self.add_comment(f"// initializing with binary expression")
                # evaluate the binary expression first
                expr_result = self.ir_gen_expr(expr.expr)
                
                if expr_result is None:
                    raise IRGenError("Binary expression evaluation failed")
                    
                # no need to create a new qubit - use the result directly
                qubit = expr_result
            
            # handle other expression types
            else:
                self.add_comment(f"// general expression initialization")
                # let ir_gen_expr handle the expression
                try:
                    qubit = self.ir_gen_expr(expr.expr)
                    if qubit is None:
                        raise IRGenError("Expression evaluation returned None")
                except Exception as e:
                    raise IRGenError(f"Failed to initialize {expr.name}: {str(e)}")
        
        # default initialization (to |0⟩)
        else:
            self.add_comment(f"// default initialization of {expr.name} to |0⟩")
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
        @brief generate ir for a return statement with improved return value handling.

        @param expr: the returnexprast node representing a return statement
        @return the quantum value to be returned
        """
        # TODO use mesureop to get the return value?
        if expr.expr is not None:
            self.add_comment(f"// process return value expression")
            return_value = self.ir_gen_expr(expr.expr)

            if return_value is None:
                self.add_comment("// warning: return expression evaluated to none")
                return_value = self.builder.insert(
                    InitOp.from_value(IntegerType(1))
                ).res

            return return_value
        else:
            # for void returns
            self.add_comment("// void return (default to 0)")
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

# ==== helper ====

    def get_qubit(self, register: SSAValue, index: int) -> SSAValue:
        """
        Extract a single qubit from a multi-qubit register.
        
        @param register: The multi-qubit register
        @param index: The index of the qubit to extract (0 is LSB)
        @return: The extracted qubit as an SSA value
        """
        if not isinstance(register.type, VectorType):
            # If it's already a single qubit, just return it
            return register
        
        self.add_comment(f"extracting qubit {index} from register {register._name}")
        
        # Use ExtractBitOp to extract the qubit at the specified index
        extracted = self.builder.insert(ExtractBitOp.from_value(register, index)).res
        
        # Maintain traceability with naming
        if register._name:
            extracted._name = f"{register._name}[{index}]"
            
        return extracted
    
    def set_qubit(self, register: SSAValue, index: int, value: SSAValue) -> SSAValue:
        """
        Set a specific qubit in a multi-qubit register.
        
        @param register: The multi-qubit register to modify
        @param index: The index of the qubit to set (0 is LSB)
        @param value: The new value for the qubit
        @return: The updated register with the modified bit
        """
        if not isinstance(register.type, VectorType):
            # If it's just a single qubit, replace it entirely
            return value
        
        self.add_comment(f"setting qubit {index} in register {register._name}")
        
        # Use InsertBitOp to insert the value at the specified index
        new_register = self.builder.insert(
            InsertBitOp.from_values(register, value, index)
        ).res
        
        # Update the version tracking to maintain SSA form
        if register._name:
            parts = register._name.split('_')
            if len(parts) == 2:
                register_num = parts[0].lstrip('q')
                version_num = int(parts[1]) + 1
                new_register._name = f"q{register_num}_{version_num}"
        
        return new_register

    def add_comment(self, comment_text):
        """
        @brief add a comment to the ir for debugging and clarity without creating dummy qubits.
        
        @param comment_text: the comment text to add
        """
        # just create a dedicated comment operation instead of a dummy qubit
        self.builder.insert(CommentOp(comment_text.lstrip("// ")))
