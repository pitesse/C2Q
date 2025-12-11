"""C language parser implementation for the C to Quantum compiler.

This module implements a recursive descent parser for a subset of the C programming
language. It uses the CtoQ lexer to tokenize C source code and builds an Abstract
Syntax Tree (AST) representation that can be further transformed into quantum IR.

The parser supports basic C constructs such as function definitions, variable
declarations, expressions, function calls, and return statements.
"""

from pathlib import Path
from typing import cast, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from xdsl.parser import GenericParser, ParserState
from xdsl.utils.lexer import Input

from .lexer import CLexer, CToken, CTokenKind
from .location import loc
from .c_ast import (
    BinaryExprAST,
    CallExprAST,
    ExprAST,
    FunctionAST,
    LiteralExprAST,
    ModuleAST,
    NumberExprAST,
    PrintExprAST,
    PrototypeAST,
    ReturnExprAST,
    VarDeclExprAST,
    VariableExprAST,
    VarType,
)


class ParseError(Exception):
    """Exception raised when a parsing error occurs."""

    pass


@dataclass
class Symbol:
    """Represents a variable symbol in the symbol table.

    Attributes:
        name: Variable name.
        type: Variable type.
        initialized: Whether the variable has been initialized.
        used: Whether the variable has been used.
    """

    name: str
    type: str
    initialized: bool = False
    used: bool = False


class SymbolTable:
    """A symbol table that manages variable declarations with nested scopes.

    Manages variable scoping, tracks variable usage and initialization,
    and provides semantic validation for variable declarations and references.
    """

    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = [{}]
        self.current_function: Optional[Tuple[str, str]] = None

    def enter_scope(self):
        """Create a new scope for block-level variable declarations."""
        self.scopes.append({})

    def exit_scope(self):
        """Exit the current scope and check for unused variables.

        Raises:
            RuntimeError: If attempting to exit the global scope.
        """
        if len(self.scopes) <= 1:
            raise RuntimeError("Cannot exit global scope")

        scope = self.scopes[-1]
        for name, symbol in scope.items():
            if not symbol.used:
                print(f"Warning: Unused variable '{name}' declared but never used")

        self.scopes.pop()

    def declare(self, name: str, type_str: str, initialized: bool = False) -> bool:
        """Declare a variable in the current scope.

        Args:
            name: Variable name.
            type_str: Variable type.
            initialized: Whether the variable is initialized.

        Returns:
            True if successful, False if already declared in this scope.
        """
        if name in self.scopes[-1]:
            return False

        self.scopes[-1][name] = Symbol(name, type_str, initialized)
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a variable, starting from the innermost scope.

        Args:
            name: Variable name to look up.

        Returns:
            Symbol if found, None otherwise.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def mark_used(self, name: str) -> bool:
        """Mark a variable as used.

        Args:
            name: Variable name.

        Returns:
            True if found and marked, False if not found.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name].used = True
                return True
        return False

    def mark_initialized(self, name: str) -> bool:
        """Mark a variable as initialized.

        Args:
            name: Variable name.

        Returns:
            True if found and marked, False if not found.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name].initialized = True
                return True
        return False

    def enter_function(self, name: str, return_type: str):
        """Set the current function context.

        Args:
            name: Function name.
            return_type: Function return type.
        """
        self.current_function = (name, return_type)

    def exit_function(self):
        """Clear the current function context."""
        self.current_function = None

    def get_current_function(self) -> Optional[Tuple[str, str]]:
        """Get the current function name and return type.

        Returns:
            Tuple of (name, return_type) if in a function, None otherwise.
        """
        return self.current_function


class CParser(GenericParser[CTokenKind]):
    """Parser for C language source code with semantic validation.

    This parser implements a recursive descent algorithm to parse a subset of the
    C programming language. It builds an Abstract Syntax Tree (AST) that represents
    the structure and semantics of the C program, which can be further processed
    for quantum transformation.

    The parser supports function definitions, variable declarations, expressions,
    function calls, and validates variable usage according to C language rules.
    """

    def __init__(self, file: Path, program: str):
        """Initialize the C parser with source file and program text.

        Args:
            file: Path object representing the source file path.
            program: String containing the C program text to parse.
        """
        super().__init__(ParserState(CLexer(Input(program, str(file)))))
        self.symbol_table = SymbolTable()
        self.current_token_loc = None

    def getToken(self):
        """Returns current token in parser.

        Returns:
            The current token being processed.
        """
        token = self._current_token
        self.current_token_loc = token.span
        return token

    def getTokenPrecedence(self) -> int:
        """Returns precedence if the current token is a binary operation.

        Determines the precedence level of the current token if it's a binary
        operator. Higher values indicate higher precedence.

        Returns:
            Precedence value or -1 if the token is not a binary operator.
        """
        PRECEDENCE = {
            "=": 10,  # assignment has lower precedence
            "-": 20,
            "+": 20,
            "*": 40,
            "/": 40,
            "%": 40,
        }
        op = self._current_token.text

        return PRECEDENCE.get(op, -1)

    def peek(self, pattern: str | CTokenKind) -> CToken | None:
        """Check if the current token matches a pattern without consuming it.

        Args:
            pattern: String or token kind to match against.

        Returns:
            The matching token or None if no match.
        """
        token = self._current_token

        if isinstance(pattern, str):
            if token.text == pattern:
                return token
        else:
            if token.kind == pattern:
                return token

    def check(self, pattern: str | CTokenKind) -> bool:
        """Verifies that the current token fits the pattern.

        Args:
            pattern: String or token kind to match against.

        Returns:
            True if the current token matches the pattern, False otherwise.
        """
        return self.peek(pattern) is not None

    def pop(self) -> CToken:
        """Consume and return the current token.

        Returns:
            The consumed token.
        """
        return self._consume_token()

    def pop_pattern(self, pattern: str) -> CToken:
        """Verify that the current token matches a pattern and consume it.

        Args:
            pattern: String pattern to match against.

        Returns:
            The consumed token.

        Raises:
            ParseError: If the current token doesn't match the pattern.
        """
        token = self._consume_token()
        if token.text != pattern:
            self.raise_error(f"Expected '{pattern}'", token.span.start, token.span.end)
        return token

    def pop_token(self, tokenType: CTokenKind) -> CToken:
        """Verify that the current token is of expected type and consume it.

        Args:
            tokenType: Expected token kind.

        Returns:
            The consumed token.

        Raises:
            ParseError: If the current token is not of the expected type.
        """
        return self._consume_token(tokenType)

    def parseModule(self):
        """Parse a full C module (a collection of function definitions).

        Grammar: module ::= definition*

        Returns:
            ModuleAST object containing the parsed functions.

        Raises:
            ParseError: If the global scope contains syntax errors.
        """
        functions: list[FunctionAST] = []

        while not self.check(CTokenKind.EOF):
            functions.append(self.parseDefinition())

        self.pop_token(CTokenKind.EOF)

        return ModuleAST(tuple(functions))

    def parseReturn(self):
        """Parse a return statement and validate against function return type.

        Grammar: return_statement ::= 'return' [expression] ';'

        Returns:
            ReturnExprAST representing the return statement.

        Raises:
            ParseError: If the return type doesn't match function declaration.
        """
        returnToken = self.pop_pattern("return")
        expr = None

        current_function = self.symbol_table.get_current_function()
        if not current_function:
            self.raise_error("Return statement outside of function")

        func_name, return_type = current_function

        if not self.check(";"):
            expr = self.parseExpression()

            if return_type == "void" and expr is not None:
                self.raise_error(
                    f"Function '{func_name}' has void return type but returns a value"
                )
            elif return_type != "void" and expr is None:
                self.raise_error(
                    f"Function '{func_name}' must return a value of type {return_type}"
                )

        return ReturnExprAST(loc(returnToken), expr)

    def parseNumberExpr(self):
        """Parse a literal number.

        Grammar: numberexpr ::= number

        Returns:
            NumberExprAST representing the parsed number.
        """
        numberToken = self.pop_token(CTokenKind.NUMBER)
        return NumberExprAST(loc(numberToken), float(numberToken.span.text))

    def parseTensorLiteralExpr(self) -> LiteralExprAST | NumberExprAST:
        """Parse a literal array expression.

        Grammar:
            tensorLiteral ::= [ literalList ] | number
            literalList ::= tensorLiteral | tensorLiteral, literalList

        Returns:
            LiteralExprAST or NumberExprAST representing the parsed tensor/array.

        Raises:
            ParseError: If the tensor literal is malformed.
        """
        if self.check(CTokenKind.NUMBER):
            return self.parseNumberExpr()

        openBracket = self.pop_pattern("[")

        values: list[LiteralExprAST | NumberExprAST] = []
        dims: list[int] = []

        while True:
            if self.check("["):
                values.append(self.parseTensorLiteralExpr())
            else:
                if not self.check(CTokenKind.NUMBER):
                    self.raise_error("Expected <num> or [ in literal expression")
                values.append(self.parseNumberExpr())

            if self.check("]"):
                break

            self.pop_pattern(",")

        self.pop_pattern("]")

        dims.append(len(values))

        if any(type(val) is LiteralExprAST for val in values):
            allTensors = all(type(val) is LiteralExprAST for val in values)
            if not allTensors:
                self.raise_error(
                    "Expected uniform well-nested dimensions inside literal expression"
                )

            tensor_values = cast(list[LiteralExprAST], values)
            first = tensor_values[0].dims
            allEqual = all(val.dims == first for val in tensor_values)
            if not allEqual:
                self.raise_error(
                    "Expected uniform well-nested dimensions inside literal expression"
                )

            dims += first

        return LiteralExprAST(loc(openBracket), values, dims)

    def parseParenExpr(self) -> ExprAST:
        """Parse a parenthesized expression.

        Grammar: parenexpr ::= '(' expression ')'

        Returns:
            ExprAST representing the parsed expression.
        """
        self.pop_pattern("(")
        v = self.parseExpression()
        self.pop_pattern(")")
        return v

    def parseIdentifierExpr(self):
        """Parse an identifier expression (variable or function call).

        Grammar:
            identifierexpr ::= identifier
                            ::= identifier '(' expression ')'

        Returns:
            VariableExprAST, CallExprAST, or PrintExprAST for the parsed expression.

        Raises:
            ParseError: If the variable is used before declaration.
        """
        name = self.pop_token(CTokenKind.IDENTIFIER)

        if not self.check("("):
            symbol = self.symbol_table.lookup(name.text)
            if not symbol:
                self.raise_error(f"Use of undeclared variable '{name.text}'")

            # usage/initialization checking deferred to parseBinOpRHS to distinguish assignment from usage
            return VariableExprAST(loc(name), name.text, symbol.type)

        self.pop_pattern("(")
        args: list[ExprAST] = []
        while True:
            if self.check(")"):
                break

            arg_expr = self.parseExpression()
            args.append(arg_expr)

            if self.check(")"):
                break

            self.pop_pattern(",")

        self.pop_pattern(")")

        if name.text == "print":
            if len(args) != 1:
                self.raise_error("Expected exactly one argument to print()")
            return PrintExprAST(loc(name), args[0])

        return CallExprAST(loc(name), name.text, args)

    def _check_variable_usage(self, expr):
        """Recursively check variable usage in an expression tree.

        Args:
            expr: Expression AST node to check.
        """
        if isinstance(expr, VariableExprAST):
            self.symbol_table.mark_used(expr.name)

            symbol = self.symbol_table.lookup(expr.name)
            if symbol and not symbol.initialized:
                self.raise_error(
                    f"Variable '{expr.name}' is used before being initialized"
                )
        elif isinstance(expr, BinaryExprAST):
            self._check_variable_usage(expr.lhs)
            self._check_variable_usage(expr.rhs)
        elif isinstance(expr, CallExprAST):
            for arg in expr.args:
                self._check_variable_usage(arg)

    def parsePrimary(self) -> ExprAST | None:
        """Parse a primary expression.

        Grammar:
            primary ::= identifierexpr
                    ::= numberexpr
                    ::= parenexpr
                    ::= tensorliteral
                    ::= unary_expr

        Returns:
            ExprAST representing the parsed expression or None if end of block.
        """
        current = self._current_token
        if current.kind == CTokenKind.IDENTIFIER:
            return self.parseIdentifierExpr()
        elif current.kind == CTokenKind.NUMBER:
            return self.parseNumberExpr()
        elif current.text == "(":
            return self.parseParenExpr()
        elif current.text == "[":
            return self.parseTensorLiteralExpr()
        elif current.text == "-":
            minus_token = self.pop_pattern("-")
            if self.check(CTokenKind.NUMBER):
                number_token = self.pop_token(CTokenKind.NUMBER)
                return NumberExprAST(loc(minus_token), -float(number_token.span.text))
            else:
                expr = self.parsePrimaryNotNone()
                zero_expr = NumberExprAST(loc(minus_token), 0.0)
                return BinaryExprAST(loc(minus_token), "-", zero_expr, expr)
        elif current.text == "+":
            plus_token = self.pop_pattern("+")
            return self.parsePrimaryNotNone()
        elif current.text == ";":
            return None
        elif current.text == "}":
            return None
        else:
            self.raise_error("Expected expression or one of `;`, `}`")

    def parsePrimaryNotNone(self) -> ExprAST:
        """Parse a primary expression, requiring a valid expression.

        Returns:
            ExprAST representing the parsed expression.
        """
        current = self._current_token
        if current.kind == CTokenKind.IDENTIFIER:
            return self.parseIdentifierExpr()
        elif current.kind == CTokenKind.NUMBER:
            return self.parseNumberExpr()
        elif current.text == "(":
            return self.parseParenExpr()
        elif current.text == "[":
            return self.parseTensorLiteralExpr()
        elif current.text == "-":
            minus_token = self.pop_pattern("-")
            if self.check(CTokenKind.NUMBER):
                number_token = self.pop_token(CTokenKind.NUMBER)
                return NumberExprAST(loc(minus_token), -float(number_token.span.text))
            else:
                expr = self.parsePrimaryNotNone()
                zero_expr = NumberExprAST(loc(minus_token), 0.0)
                return BinaryExprAST(loc(minus_token), "-", zero_expr, expr)
        elif current.text == "+":
            plus_token = self.pop_pattern("+")
            return self.parsePrimaryNotNone()
        else:
            self.raise_error("Expected expression")

    def parseBinOpRHS(self, exprPrec: int, lhs: ExprAST) -> ExprAST:
        """Parse the right-hand side of a binary expression.

        This method handles operator precedence and builds the appropriate
        expression tree based on operator precedence.

        Args:
            exprPrec: Current precedence level.
            lhs: Left-hand side expression.

        Returns:
            Complete binary expression with correct precedence handling.

        Raises:
            ParseError: If assignment target is not a variable or types are incompatible.
        """
        while True:
            tokPrec = self.getTokenPrecedence()

            if tokPrec < exprPrec:
                return lhs

            if self.check(CTokenKind.ASSIGN):
                binOp = self.pop_token(CTokenKind.ASSIGN).text

                if not isinstance(lhs, VariableExprAST):
                    self.raise_error("Left side of assignment must be a variable")

                var_name = lhs.name
                symbol = self.symbol_table.lookup(var_name)
                if not symbol:
                    self.raise_error(f"Assignment to undeclared variable '{var_name}'")
            else:
                current_token = self.getToken()
                if current_token.text in ["+", "-", "*", "/", "%"]:
                    binOp = self.pop().text

                    if isinstance(lhs, VariableExprAST):
                        self.symbol_table.mark_used(lhs.name)
                        symbol = self.symbol_table.lookup(lhs.name)
                        if symbol and not symbol.initialized:
                            self.raise_error(
                                f"Variable '{lhs.name}' is used before being initialized"
                            )
                else:
                    if isinstance(lhs, VariableExprAST):
                        self.symbol_table.mark_used(lhs.name)
                        symbol = self.symbol_table.lookup(lhs.name)
                        if symbol and not symbol.initialized:
                            self.raise_error(
                                f"Variable '{lhs.name}' is used before being initialized"
                            )
                    return lhs

            rhs = self.parsePrimary()

            if rhs is None:
                self.raise_error("Expected expression to complete binary operator")

            if binOp != "=":
                self._check_variable_usage(rhs)

            if binOp == "=" and isinstance(lhs, VariableExprAST):
                self.symbol_table.mark_initialized(lhs.name)
                self._check_variable_usage(rhs)

            nextPrec = self.getTokenPrecedence()
            if tokPrec < nextPrec:
                rhs = self.parseBinOpRHS(tokPrec + 1, rhs)

            lhs = BinaryExprAST(rhs.loc, binOp, lhs, rhs)

        return lhs

    def parseExpression(self) -> ExprAST:
        """Parse a complete expression.

        Grammar: expression ::= primary binop rhs

        Returns:
            ExprAST representing the full expression.
        """
        lhs = self.parsePrimaryNotNone()
        return self.parseBinOpRHS(0, lhs)

    def parseType(self):
        """Parse a variable type with shape information.

        Grammar:
            type ::= < shape_list >
            shape_list ::= num | num , shape_list

        Returns:
            VarType object with shape information.
        """
        self.pop_pattern("<")
        shape: list[int] = []

        while token := self.pop_token(CTokenKind.NUMBER):
            shape.append(int(token.span.text))
            if self.parse_optional_characters(">"):
                break
            self.pop_pattern(",")

        return VarType(shape)

    def parseDeclaration(self):
        """Parse a C variable declaration and register in symbol table.

        Grammar: declaration ::= type identifier ['=' expr] ';'

        Returns:
            VarDeclExprAST representing the variable declaration.

        Raises:
            ParseError: If variable is redeclared or has invalid initialization.
        """
        if (
            not self.check(CTokenKind.INT)
            and not self.check(CTokenKind.FLOAT)
            and not self.check(CTokenKind.DOUBLE)
            and not self.check(CTokenKind.CHAR)
        ):
            self.raise_error("Expected variable type")

        type_token = self.pop()
        var_type = type_token.text

        if not self.check(CTokenKind.IDENTIFIER):
            self.raise_error("Expected variable name")

        name_token = self.pop_token(CTokenKind.IDENTIFIER)
        var_name = name_token.text

        if var_name in self.symbol_table.scopes[-1]:
            self.raise_error(
                f"Redeclaration of variable '{var_name}' in the same scope"
            )

        expr = None
        initialized = False

        if self.check("="):
            self.pop_pattern("=")
            expr = self.parseExpression()
            initialized = True

        self.symbol_table.declare(var_name, var_type, initialized)

        return VarDeclExprAST(loc(type_token), var_name, var_type, expr=expr)

    def parseDeclarationList(self):
        """Parse a list of C variable declarations of the same type.

        Grammar: declaration_list ::= type identifier ['=' expr] [, identifier ['=' expr]]* ';'

        Returns:
            List of VarDeclExprAST objects representing the variable declarations.

        Raises:
            ParseError: If declaration syntax is invalid or variables are redeclared.
        """
        if (
            not self.check(CTokenKind.INT)
            and not self.check(CTokenKind.FLOAT)
            and not self.check(CTokenKind.DOUBLE)
            and not self.check(CTokenKind.CHAR)
        ):
            self.raise_error("Expected variable type")

        type_token = self.pop()
        var_type = type_token.text

        declarations = []

        while True:
            if not self.check(CTokenKind.IDENTIFIER):
                self.raise_error("Expected variable name")

            name_token = self.pop_token(CTokenKind.IDENTIFIER)
            var_name = name_token.text

            if var_name in self.symbol_table.scopes[-1]:
                self.raise_error(
                    f"Redeclaration of variable '{var_name}' in the same scope"
                )

            expr = None
            initialized = False

            if self.check("="):
                self.pop_pattern("=")
                expr = self.parseExpression()
                initialized = True

            self.symbol_table.declare(var_name, var_type, initialized)

            declarations.append(
                VarDeclExprAST(loc(type_token), var_name, var_type, expr=expr)
            )

            if not self.check(","):
                break

            self.pop_pattern(",")

        self.pop_pattern(";")

        return declarations

    def parseBlock(self) -> tuple[ExprAST, ...]:
        """Parse a C block: a list of statements wrapped in curly braces.

        Grammar:
            block ::= '{' statement_list '}'
            statement_list ::= statement | statement statement_list
            statement ::= declaration_list | expression_statement | return_statement

        Returns:
            Tuple of ExprAST objects representing the statements in the block.

        Raises:
            ParseError: If the block syntax is invalid.
        """
        self.pop_pattern("{")

        self.symbol_table.enter_scope()

        exprList: list[ExprAST] = []

        while not self.check("}"):
            if (
                self.check(CTokenKind.INT)
                or self.check(CTokenKind.FLOAT)
                or self.check(CTokenKind.DOUBLE)
                or self.check(CTokenKind.CHAR)
                or self.check(CTokenKind.VOID)
            ):
                declarations = self.parseDeclarationList()
                exprList.extend(declarations)
            elif self.check("return"):
                exprList.append(self.parseReturn())
                self.pop_pattern(";")
            else:
                expr = self.parseExpression()
                exprList.append(expr)
                self.pop_pattern(";")

        self.pop_pattern("}")

        self.symbol_table.exit_scope()

        return tuple(exprList)

    def parsePrototype(self):
        """Parse a C function prototype.

        Grammar:
            prototype ::= return_type id '(' param_list ')'
            param_list ::= param | param, param_list
            param ::= type id

        Returns:
            PrototypeAST representing the function prototype.

        Raises:
            ParseError: If the prototype syntax is invalid.
        """
        if (
            not self.check(CTokenKind.INT)
            and not self.check(CTokenKind.FLOAT)
            and not self.check(CTokenKind.DOUBLE)
            and not self.check(CTokenKind.VOID)
            and not self.check(CTokenKind.CHAR)
        ):
            self.raise_error("Expected return type")

        returnTypeToken = self.pop()
        return_type = returnTypeToken.text

        if not self.check(CTokenKind.IDENTIFIER):
            self.raise_error("Expected function name")

        name_token = self.pop_token(CTokenKind.IDENTIFIER)
        fnName = name_token.text

        self.pop_pattern("(")
        args: list[VariableExprAST] = []

        if not self.check(")"):
            while True:
                if (
                    not self.check(CTokenKind.INT)
                    and not self.check(CTokenKind.FLOAT)
                    and not self.check(CTokenKind.DOUBLE)
                    and not self.check(CTokenKind.VOID)
                    and not self.check(CTokenKind.CHAR)
                ):
                    self.raise_error("Expected parameter type")

                param_type_token = self.pop()
                param_type = param_type_token.text

                if not self.check(CTokenKind.IDENTIFIER):
                    self.raise_error("Expected parameter name")

                arg_token = self.pop_token(CTokenKind.IDENTIFIER)
                arg_name = arg_token.text

                args.append(VariableExprAST(loc(arg_token), arg_name, param_type))

                if not self.check(","):
                    break
                self.pop_pattern(",")

        self.pop_pattern(")")
        return PrototypeAST(loc(returnTypeToken), fnName, args, return_type)

    def parseDefinition(self):
        """Parse a C function definition.

        Grammar: definition ::= prototype '{' statement_list '}'

        Returns:
            FunctionAST representing the complete function definition.

        Raises:
            ParseError: If the function definition syntax is invalid.
        """
        proto = self.parsePrototype()

        self.symbol_table.enter_function(proto.name, proto.return_type)

        self.symbol_table.enter_scope()

        for param in proto.args:
            type_name = param.type_name if param.type_name is not None else "int"
            self.symbol_table.declare(param.name, type_name, initialized=True)

        block = self.parseBlock()

        if proto.return_type != "void":
            has_return = any(isinstance(expr, ReturnExprAST) for expr in block)
            if not has_return:
                self.raise_error(
                    f"Function '{proto.name}' has non-void return type but no return statement"
                )

        self.symbol_table.exit_function()

        return FunctionAST(proto.loc, proto, block)
