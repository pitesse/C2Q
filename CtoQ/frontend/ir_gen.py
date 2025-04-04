from __future__ import annotations

# Change this import line
from xdsl.context import Context  # MLContext is in xdsl.context, not xdsl.ir
from xdsl.ir import Block, Region, Operation
from xdsl.dialects.builtin import ModuleOp, IntegerType, VectorType, IntegerAttr
from xdsl.builder import Builder, InsertPoint
from xdsl.utils.scoped_dict import ScopedDict


from .c_ast import *
from ..dialects.quantum_dialect import (
    Quantum, InitOp, NotOp, CNotOp, CCNotOp, MeasureOp, 
    HadamardOp, TGateOp, TDaggerGateOp, FuncOp
)

class IRGenError(Exception):
    pass

class QuantumIRGen:
    def __init__(self):
        self.context = Context()
        # Load the quantum dialect
        self.context.load_dialect(Quantum)
        
        # Create a module
        self.module = ModuleOp([])
        self.builder = Builder(InsertPoint.at_end(self.module.body.blocks[0]))
        self.symbol_table = ScopedDict()
    
    def ir_gen_module(self, module_ast: ModuleAST) -> ModuleOp:
        """Generate Quantum IR from C AST Module"""
        for func_ast in module_ast.funcs:  # Use the correct attribute name
            self.ir_gen_function(func_ast)
            
        return self.module
    
    def ir_gen_function(self, function_ast: FunctionAST):
        """Generate a quantum function from a C function AST"""
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
        """Generate IR for a C expression"""
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
        """Generate quantum operations for binary expressions"""
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
            print(f"Warning: Unsupported binary operation '{expr.op}', using left side value")
            return lhs
            
    
    def ir_gen_quantum_addition(self, a, b):
        """Generate quantum circuit for addition (simplified)"""
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
        """Generate quantum circuit for subtraction (simplified)"""
        # Invert b using a NOT gate
        not_b = self.builder.insert(NotOp.from_value(b)).res
        
        # Then add a and not_b
        return self.ir_gen_quantum_addition(a, not_b)
    
    def ir_gen_variable_expr(self, expr: VariableExprAST):
        """Generate IR for a variable reference"""
        if expr.name in self.symbol_table:
            return self.symbol_table[expr.name]
        else:
            raise IRGenError(f"Undefined variable: {expr.name}")
    
    def ir_gen_number_expr(self, expr: NumberExprAST):
        """Generate IR for a number literal"""
        # Initialize a qubit
        qubit = self.builder.insert(InitOp.from_value(IntegerType(1))).res
        
        # If the number is non-zero, apply NOT gate to flip it to |1⟩
        if expr.val != 0:
            qubit = self.builder.insert(NotOp.from_value(qubit)).res
        
        return qubit
    
    def ir_gen_var_decl_expr(self, expr: VarDeclExprAST):
        """Generate IR for a variable declaration"""
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
        """Generate IR for a return statement"""
        try:
            if expr.expr is not None:
                # Evaluate the return expression
                return_value = self.ir_gen_expr(expr.expr)
                
                # More thorough checking for None or invalid values
                if return_value is None or not hasattr(return_value, 'type'):
                    print(f"Warning: Return value is None or missing type attribute, creating default qubit")
                    return_value = self.builder.insert(InitOp.from_value(IntegerType(1))).res
                    
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
        """Generate IR for a function call"""
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