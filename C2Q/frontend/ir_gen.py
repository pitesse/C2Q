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
    OnQubitNotOp,
    OnQubitCNotOp,
    OnQubitCCnotOp,
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
        @brief generate ir for a function call by inlining the function body.

        this method retrieves the function's ast and generates ir for its body,
        substituting the arguments with the provided values.

        @param func_ast: the functionast node representing the function to be called
        @param args: the list of arguments passed to the function
        """
        # TODO handle function return value
        # self.add_comment(f"// function call: {func_ast.proto.name}")

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
            # self.add_comment(f"// function call: {expr.callee}")

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
        elif isinstance(expr, VariableExprAST):
            return self.ir_gen_variable_expr(expr)
        else:
            raise IRGenError(f"Unsupported expression type: {type(expr)}")

    # TODO
    def ir_gen_binary_expr(self, expr: BinaryExprAST):
        """
        @brief generate quantum operations for binary expressions with improved tracking.
    
        @param expr: the binaryexprast node representing a binary operation
        @return the resulting quantum value
        """
        # Handle special case: 0 - constant (negative literal that wasn't caught by parser)
        if (expr.op == "-" and 
            isinstance(expr.lhs, NumberExprAST) and expr.lhs.val == 0 and
            isinstance(expr.rhs, NumberExprAST)):
            # This is a negative literal, handle it directly
            negative_expr = NumberExprAST(expr.rhs.loc, -expr.rhs.val)
            return self.ir_gen_number_expr(negative_expr)
    
        # handle cases where lhs or rhs might be none
        if expr.lhs is None or expr.rhs is None:
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res
    
        # handle binary operations
        if expr.op == "+":
            return self.ir_gen_quantum_addition(expr.lhs, expr.rhs)
        elif expr.op == "-":
            return self.ir_gen_quantum_subtraction(expr.lhs, expr.rhs)
        else:
            return expr.lhs

    # ==== operations ====

    def ir_gen_quantum_addition(self, a_expr: ExprAST, b_expr: ExprAST) -> SSAValue:
        """
        Generate quantum circuit for addition of multi-qubit registers using reversible ripple carry adder.
    
        Implements a quantum adder for registers representing integers based on the
        reversible methodology with no ancilla inputs.
    
        @param a_expr: First operand expression
        @param b_expr: Second operand expression
        @return: The resulting register representing the sum
        """
        # Evaluate expressions to get the quantum registers
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)
    
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            # Handle the case where inputs might be single qubits
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                self.set_qubit(a_temp, 0, a)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                self.set_qubit(b_temp, 0, b)
                b = b_temp
    
        # Initialize result register
        result = self.ir_gen_init(None)
        
        # Initialize carry register
        z_reg = self.ir_gen_init(None)  
        z_reg._name = "z_0"  
    
        bit_width = 32  # For 32-bit integers
    
        # Step 1: CNOT between Ai and Bi for i=1 to n-1
        for i in range(1, bit_width):
            # Use direct CNOT operation on bits
            b = self.apply_cnot_on_bits(a, i, b, i)
    
        # Step 2: CNOT between Ai and Ai+1 from n-1 down to 1
        temp_a = a  # Create a separate copy for tracking changes
        for i in range(bit_width - 1, 0, -1):
            temp_a = self.apply_cnot_on_bits(temp_a, i-1, temp_a, i)
    
        # Step 3: Toffoli gate at Bi, Ai, and Ai+1 for i=0 to n-2
        for i in range(0, bit_width - 1):
            # Use direct CCNOT operation on bits
            temp_a = self.apply_ccnot_on_bits(b, i, temp_a, i, temp_a, i+1)
    
        # Step 4: Peres gate (which is Toffoli + CNOT)
        for i in range(bit_width - 1, -1, -1):
            # First part of Peres (Toffoli): C' = C ⊕ (A·B)
            if i == bit_width - 1:
                # For highest bit, use z_reg as carry bit
                z_reg = self.apply_ccnot_on_bits(temp_a, i, b, i, z_reg, 0)
            else:
                temp_a = self.apply_ccnot_on_bits(temp_a, i, b, i, temp_a, i+1)
    
            # Second part of Peres (CNOT): B' = B ⊕ A
            b = self.apply_cnot_on_bits(temp_a, i, b, i)
    
        # Step 5: CNOT between Ai and Ai+1 for i=1 to n-2
        for i in range(1, bit_width - 1):
            temp_a = self.apply_cnot_on_bits(temp_a, i, temp_a, i+1)
    
        # Step 6: CNOT between Bi and Ai for i=1 to n-1
        for i in range(1, bit_width):
            b = self.apply_cnot_on_bits(temp_a, i, b, i)
    
        # Copy the result from b (which now contains the sum bits) to result register
        for i in range(bit_width):
            result = self.apply_cnot_on_bits(b, i, result, i)
    
        # Set the carry in the highest bit if needed
        if z_reg._name != "z_0":  # Only if the carry bit was modified
            result = self.apply_cnot_on_bits(z_reg, 0, result, bit_width-1)
    
        # Update the register version to track the changes
        # result = self.update_qubit_status(result)
    
        return result

    # TODO test this
    def ir_gen_quantum_subtraction(self, a_expr: ExprAST, b_expr: ExprAST) -> SSAValue:
        """
        Generate quantum circuit for subtraction using direct bit operations.
    
        This implementation follows the paper's approach for reversible subtraction
        where we first complement a, then add b, then complement the result.
    
        @param a_expr: First operand expression (minuend)
        @param b_expr: Second operand expression (subtrahend)
        @return: The resulting register representing the difference
        """
        # Evaluate expressions to get the quantum registers
        a = self.ir_gen_expr(a_expr)
        b = self.ir_gen_expr(b_expr)
    
        if not isinstance(a.type, VectorType) or not isinstance(b.type, VectorType):
            # Handle single qubits (same as in addition)
            if not isinstance(a.type, VectorType):
                a_temp = self.ir_gen_init(None)
                self.set_qubit(a_temp, 0, a)
                a = a_temp
            if not isinstance(b.type, VectorType):
                b_temp = self.ir_gen_init(None)
                self.set_qubit(b_temp, 0, b)
                b = b_temp
    
        # Initialize result register
        result = self.ir_gen_init(None)
        
        bit_width = 32  # For 32-bit integers
    
        # Step 1: Complement input 'a' (NOT all bits in a)
        not_a = self.ir_gen_init(None)
        for i in range(bit_width):
            # First copy the bits directly
            not_a = self.apply_cnot_on_bits(a, i, not_a, i)
            # Then complement each bit directly
            not_a = self.flip_qubit(not_a, i)
    
        # Step 2: Use the addition algorithm to compute (NOT a) + b with direct operations
        # Initialize a temporary 'z' bit to hold the final carry
        z_reg = self.ir_gen_init(None)
        z_reg._name = "z_0"
    
        temp_a = not_a  # Use not_a as our 'a' input for addition
        temp_b = b      # Use b directly  
    
        # Steps 1-6 from the ripple carry adder - same as in addition but with direct operations
        # Step 1: CNOT between Ai and Bi for i=1 to n-1
        for i in range(1, bit_width):
            temp_b = self.apply_cnot_on_bits(temp_a, i, temp_b, i)
    
        # Step 2: CNOT between Ai and Ai+1 from n-1 down to 1
        for i in range(bit_width - 1, 0, -1):
            temp_a = self.apply_cnot_on_bits(temp_a, i-1, temp_a, i)
    
        # Step 3: Toffoli gate at Bi, Ai, and Ai+1 for i=0 to n-2
        for i in range(0, bit_width - 1):
            temp_a = self.apply_ccnot_on_bits(temp_b, i, temp_a, i, temp_a, i+1)
    
        # Step 4: Peres gate (which is Toffoli + CNOT)
        for i in range(bit_width - 1, -1, -1):
            if i == bit_width - 1:
                z_reg = self.apply_ccnot_on_bits(temp_a, i, temp_b, i, z_reg, 0)
            else:
                temp_a = self.apply_ccnot_on_bits(temp_a, i, temp_b, i, temp_a, i+1)
                
            temp_b = self.apply_cnot_on_bits(temp_a, i, temp_b, i)
    
        # Step 5: CNOT between Ai and Ai+1 for i=1 to n-2
        for i in range(1, bit_width - 1):
            temp_a = self.apply_cnot_on_bits(temp_a, i, temp_a, i+1)
    
        # Step 6: CNOT between Bi and Ai for i=1 to n-1
        for i in range(1, bit_width):
            temp_b = self.apply_cnot_on_bits(temp_a, i, temp_b, i)
    
        # Step 3: Complement the result (apply NOT to all bits) using direct operations
        for i in range(bit_width):
            # First copy the bit directly
            result = self.apply_cnot_on_bits(temp_b, i, result, i)
            # Then complement it directly
            result = self.flip_qubit(result, i)
    
        # Update the register version to track the changes
        # result = self.update_qubit_status(result)
    
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
        @brief Generate IR for a variable reference.

        Looks up the variable in the symbol table and returns its SSA value.

        @param expr: the VariableExprAST node representing a variable reference
        @return the SSA value associated with the variable
        """
        var_name = expr.name
        # self.add_comment(f"// variable reference: {var_name}")

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
        bit_width = 32  # default bit width for integers

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
            
            # For negative numbers, use two's complement representation
            if value < 0:
                # Convert to 32-bit two's complement
                value = (1 << 32) + value  # This gives us the two's complement representation
            
            binary_str = bin(value)[2:].zfill(32)[-32:]  # Zero-pad and take last 32 bits
    
            # Apply NOT gates to each qubit position where the binary digit is 1
            for i, bit in enumerate(reversed(binary_str)):  # LSB first
                if bit == "1":
                    register = self.flip_qubit(register, i)
    
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
        # self.add_comment(f"// declare variable: {expr.name}")

        # variable will be initialized with an expression or default to zero
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
                    bit_width = 32  # Default bit width
                    for i in range(bit_width):
                        qubit = self.apply_cnot_on_bits(source, i, qubit, i)
                    return qubit
                else:
                    raise IRGenError(f"Referenced undefined variable: {var_name}")

            # handle binary expressions
            elif isinstance(expr.expr, BinaryExprAST):
                # self.add_comment(f"// initializing with binary expression")
                # evaluate the binary expression first
                expr_result = self.ir_gen_expr(expr.expr)

                if expr_result is None:
                    raise IRGenError("Binary expression evaluation failed")

                # no need to create a new qubit - use the result directly
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
        @brief generate ir for a return statement with improved return value handling.

        @param expr: the returnexprast node representing a return statement
        @return the quantum value to be returned
        """
        # TODO use mesureop to get the return value?
        if expr.expr is not None:
            # self.add_comment(f"// process return value expression")
            return_value = self.ir_gen_expr(expr.expr)

            if return_value is None:
                # self.add_comment("// warning: return expression evaluated to none")
                return_value = self.builder.insert(
                    InitOp.from_value(IntegerType(1))
                ).res

            return return_value
        else:
            # for void returns
            # self.add_comment("// void return (default to 0)")
            return self.builder.insert(InitOp.from_value(IntegerType(1))).res

    # ==== helper ====

    def flip_qubit(self, register: SSAValue, index: int) -> SSAValue:
        """
        Flip a specific qubit in a multi-qubit register using a direct NOT operation.

        @param register: The multi-qubit register to modify
        @param index: The index of the qubit to flip (0 is LSB)
        @return: The updated register with the flipped bit
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
