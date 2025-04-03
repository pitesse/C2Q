import sys
from clang.cindex import Index, CursorKind
from dataclasses import dataclass, field
from typing import List, Optional, Union

@dataclass
class BinaryOperation:
    operator: str
    left: str
    right: str

@dataclass
class ReturnStmt:
    value: Union[str, BinaryOperation]

@dataclass
class FunctionDecl:
    name: str
    return_type: str
    parameters: List[str]
    body: List[Union[ReturnStmt, BinaryOperation]] = field(default_factory=list)

@dataclass
class TranslationUnit:
    filename: str
    functions: List[FunctionDecl] = field(default_factory=list)

def parse_ast(filename: str) -> TranslationUnit:
    # Initialize the Clang index
    index = Index.create()
    
    # Parse the C file
    translation_unit = index.parse(filename)
    
    # Create a container for the parsed data
    tu = TranslationUnit(filename=filename)
    
    # Traverse the AST
    for cursor in translation_unit.cursor.get_children():
        if cursor.kind == CursorKind.FUNCTION_DECL:
            # Extract function name, return type, and parameters
            func_name = cursor.spelling
            return_type = cursor.result_type.spelling
            parameters = [param.type.spelling for param in cursor.get_arguments()]
            
            # Parse the function body
            body = parse_function_body(cursor)
            
            # Add the function declaration to the translation unit
            tu.functions.append(FunctionDecl(name=func_name, return_type=return_type, parameters=parameters, body=body))
    
    return tu

def parse_function_body(cursor):
    """
    Parse the body of a function to extract statements and expressions.
    """
    body = []
    for child in cursor.get_children():
        if child.kind == CursorKind.COMPOUND_STMT:
            # Compound statements (function body) need to be traversed recursively
            body.extend(parse_function_body(child))
        elif child.kind == CursorKind.RETURN_STMT:
            # Handle return statements
            return_value = parse_expression(child.get_children())
            body.append(ReturnStmt(value=return_value))
        elif child.kind == CursorKind.BINARY_OPERATOR:
            # Handle binary operations
            body.append(parse_binary_operation(child))
    return body

def parse_binary_operation(cursor):
    """
    Parse a binary operation to extract the operator and its operands.
    """
    operands = list(cursor.get_children())
    if len(operands) == 2:
        left = operands[0].spelling
        right = operands[1].spelling

        # Extract the operator from the tokens
        operator = ""
        for token in cursor.get_tokens():
            if token.spelling not in [left, right]:
                operator = token.spelling
                break

        return BinaryOperation(operator=operator, left=left, right=right)
    return None

def parse_expression(children):
    """
    Parse an expression, such as a binary operation or a literal.
    """
    for child in children:
        if child.kind == CursorKind.BINARY_OPERATOR:
            # Handle binary operations
            return parse_binary_operation(child)
        elif child.kind == CursorKind.INTEGER_LITERAL:
            # Handle integer literals
            return child.spelling
        elif child.kind == CursorKind.DECL_REF_EXPR:
            # Handle variable references
            return child.spelling
    return None

if __name__ == "__main__":
    # Ensure the C file is provided as an argument
    if len(sys.argv) < 2:
        print("Usage: python3 ast_generator.py <filename.c>")
        sys.exit(1)
    
    # Parse the provided C file
    filename = sys.argv[1]
    translation_unit = parse_ast(filename)
    
    # Print the parsed AST as Python dataclasses
    print(translation_unit)