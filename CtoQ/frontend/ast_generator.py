"""
@file ast_generator.py
@brief AST generator for C to Quantum compiler using Clang's Python bindings.

This module uses the Clang library to parse C source code and generate a simplified
Abstract Syntax Tree (AST) representation. It extracts function declarations,
return statements, binary operations, and other constructs from C files.

The generated AST is represented using Python dataclasses, which can be easily
serialized to JSON for inspection or further processing in the quantum compilation
pipeline.
"""

import sys
from clang.cindex import Index, CursorKind
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union
import json  # For pretty-printing the output


@dataclass
class BinaryOperation:
    """
    @brief Represents a binary operation in the AST.

    Captures a binary expression with an operator and two operands.

    @param operator: The binary operator (e.g., '+', '-', '*', '/')
    @param left: The left operand
    @param right: The right operand
    """

    operator: str
    left: str
    right: str


@dataclass
class ReturnStmt:
    """
    @brief Represents a return statement in the AST.

    Captures a return statement with its return value, which can be a simple
    expression or a more complex binary operation.

    @param value: The value being returned (string or BinaryOperation)
    """

    value: Union[str, BinaryOperation]


@dataclass
class FunctionDecl:
    """
    @brief Represents a function declaration in the AST.

    Captures a function's signature and body, including its name, return type,
    parameters, and the statements within its body.

    @param name: The function name
    @param return_type: The function's return type
    @param parameters: List of parameter types
    @param body: List of statements in the function body
    """

    name: str
    return_type: str
    parameters: List[str]
    body: List[Union[ReturnStmt, BinaryOperation]] = field(default_factory=list)


@dataclass
class TranslationUnit:
    """
    @brief Represents an entire C translation unit (file) in the AST.

    A translation unit contains all the declarations and definitions from a
    single compiled source file.

    @param filename: Name of the source file
    @param functions: List of function declarations in the file
    """

    filename: str
    functions: List[FunctionDecl] = field(default_factory=list)


def parse_ast(filename: str) -> TranslationUnit:
    """
    @brief Parse a C file and generate an AST representation.

    Uses Clang to parse the given C file and extracts function declarations,
    their parameters, and bodies into a simplified AST structure.

    @param filename: Path to the C source file to parse
    @return TranslationUnit object containing the parsed AST
    """
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
            tu.functions.append(
                FunctionDecl(
                    name=func_name,
                    return_type=return_type,
                    parameters=parameters,
                    body=body,
                )
            )

    return tu


def parse_function_body(cursor):
    """
    @brief Parse the body of a function to extract statements and expressions.

    Recursively traverses the function body to extract return statements and
    binary operations.

    @param cursor: Clang cursor pointing to a function declaration
    @return List of statements (ReturnStmt or BinaryOperation objects)
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
    @brief Parse a binary operation to extract the operator and its operands.

    Extracts the operator and operands from a binary operation expression.

    @param cursor: Clang cursor pointing to a binary operation
    @return BinaryOperation object or None if parsing fails
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
    @brief Parse an expression, such as a binary operation or a literal.

    Determines the type of expression and delegates to the appropriate parser.

    @param children: Iterator of Clang cursors representing expression children
    @return Parsed expression (string or BinaryOperation) or None if parsing fails
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


def pretty_print_translation_unit(tu: TranslationUnit):
    """
    @brief Pretty-print the TranslationUnit as an indented JSON-like structure.

    Converts the TranslationUnit object to a dictionary and prints it as
    formatted JSON for easier inspection.

    @param tu: TranslationUnit object to print
    """
    print(json.dumps(asdict(tu), indent=4))


if __name__ == "__main__":
    # Ensure the C file is provided as an argument
    if len(sys.argv) < 2:
        print("Usage: python3 ast_generator.py <filename.c>")
        sys.exit(1)

    # Parse the provided C file
    filename = sys.argv[1]
    translation_unit = parse_ast(filename)

    # Pretty-print the parsed AST
    pretty_print_translation_unit(translation_unit)

    # Write the output to a file
    with open("ast_output.json", "w") as f:
        f.write(json.dumps(asdict(translation_unit), indent=4))
    print("AST output written to ast_output.json")
