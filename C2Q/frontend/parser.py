"""
@file parser.py
@brief C language parser implementation for the C to Quantum compiler.

This module implements a recursive descent parser for a subset of the C programming
language. It uses the CtoQ lexer to tokenize C source code and builds an Abstract
Syntax Tree (AST) representation that can be further transformed into quantum IR.

The parser supports basic C constructs such as function definitions, variable
declarations, expressions, function calls, and return statements.
"""

from pathlib import Path
from typing import cast

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


class CParser(GenericParser[CTokenKind]):
    """
    @brief Parser for C language source code.

    This parser implements a recursive descent algorithm to parse a subset of the
    C programming language. It builds an Abstract Syntax Tree (AST) that represents
    the structure and semantics of the C program, which can be further processed
    for quantum transformation.

    The parser supports function definitions, variable declarations, expressions,
    function calls, and control flow constructs like conditionals and loops.

    @see CLexer
    @see c_ast.py
    """

    def __init__(self, file: Path, program: str):
        """
        @brief Initialize the C parser with source file and program text.

        @param file: Path object representing the source file path
        @param program: String containing the C program text to parse
        """
        super().__init__(ParserState(CLexer(Input(program, str(file)))))

    def getToken(self):
        """
        @brief Returns current token in parser.

        @return The current token being processed
        """
        return self._current_token

    def getTokenPrecedence(self) -> int:
        """
        @brief Returns precedence if the current token is a binary operation.

        Determines the precedence level of the current token if it's a binary
        operator. Higher values indicate higher precedence.

        @return Precedence value or -1 if the token is not a binary operator
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
        """
        @brief Check if the current token matches a pattern without consuming it.

        @param pattern: String or token kind to match against
        @return The matching token or None if no match
        """
        token = self._current_token

        if isinstance(pattern, str):
            if token.text == pattern:
                return token
        else:
            if token.kind == pattern:
                return token

    def check(self, pattern: str | CTokenKind) -> bool:
        """
        @brief Verifies that the current token fits the pattern.

        @param pattern: String or token kind to match against
        @return True if the current token matches the pattern, False otherwise
        """
        return self.peek(pattern) is not None

    def pop(self) -> CToken:
        """
        @brief Consume and return the current token.

        @return The consumed token
        """
        return self._consume_token()

    def pop_pattern(self, pattern: str) -> CToken:
        """
        @brief Verify that the current token matches a pattern and consume it.

        @param pattern: String pattern to match against
        @return The consumed token
        @throws ParseError if the current token doesn't match the pattern
        """
        token = self._consume_token()
        if token.text != pattern:
            self.raise_error(f"Expected '{pattern}'", token.span.start, token.span.end)
        return token

    def pop_token(self, tokenType: CTokenKind) -> CToken:
        """
        @brief Verify that the current token is of expected type and consume it.

        @param tokenType: Expected token kind
        @return The consumed token
        @throws ParseError if the current token is not of the expected type
        """
        return self._consume_token(tokenType)

    def parseModule(self):
        """
        @brief Parse a full C module (a collection of function definitions).

        module ::= definition*

        @return ModuleAST object containing the parsed functions
        """
        functions: list[FunctionAST] = []

        while not self.check(CTokenKind.EOF):
            functions.append(self.parseDefinition())

        # if we didn't reach EOF, there was an error during parsing
        self.pop_token(CTokenKind.EOF)

        return ModuleAST(tuple(functions))

    def parseReturn(self):
        """
        @brief Parse a return statement.

        return_statement ::= 'return' [expression] ';'

        @return ReturnExprAST representing the return statement
        """
        returnToken = self.pop_pattern("return")
        expr = None

        # return takes an optional expression
        if not self.check(";"):
            expr = self.parseExpression()

        return ReturnExprAST(loc(returnToken), expr)

    def parseNumberExpr(self):
        """
        @brief Parse a literal number.

        numberexpr ::= number

        @return NumberExprAST representing the parsed number
        """
        numberToken = self.pop_token(CTokenKind.NUMBER)
        return NumberExprAST(loc(numberToken), float(numberToken.span.text))

    def parseTensorLiteralExpr(self) -> LiteralExprAST | NumberExprAST:
        """
        @brief Parse a literal array expression.

        tensorLiteral ::= [ literalList ] | number
        literalList ::= tensorLiteral | tensorLiteral, literalList

        @return LiteralExprAST or NumberExprAST representing the parsed tensor/array
        @throws ParseError if the tensor literal is malformed
        """
        if self.check(CTokenKind.NUMBER):
            return self.parseNumberExpr()

        openBracket = self.pop_pattern("[")

        # hold the list of values at this nesting level
        values: list[LiteralExprAST | NumberExprAST] = []
        # hold the dimensions for all the nesting inside this level
        dims: list[int] = []

        while True:
            # we can have either another nested array or a number literal
            if self.check("["):
                values.append(self.parseTensorLiteralExpr())
            else:
                if not self.check(CTokenKind.NUMBER):
                    self.raise_error("Expected <num> or [ in literal expression")
                values.append(self.parseNumberExpr())

            # end of this list on ']'
            if self.check("]"):
                break

            # elements are separated by a comma
            self.pop_pattern(",")

        self.pop_pattern("]")

        # fill in the dimensions now. first the current nesting level:
        dims.append(len(values))

        # if there is any nested array, process all of them and ensure
        # that dimensions are uniform
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
        """
        @brief Parse a parenthesized expression.

        parenexpr ::= '(' expression ')'

        @return ExprAST representing the parsed expression
        """
        self.pop_pattern("(")
        v = self.parseExpression()
        self.pop_pattern(")")
        return v

    def parseIdentifierExpr(self):
        """
        @brief Parse an identifier expression (variable or function call).

        identifierexpr ::= identifier
                        ::= identifier '(' expression ')'

        @return VariableExprAST, CallExprAST, or PrintExprAST for the parsed expression
        """
        name = self.pop_token(CTokenKind.IDENTIFIER)
        if not self.check("("):
            # simple variable ref
            return VariableExprAST(loc(name), name.text)

        # this is a function call
        self.pop_pattern("(")
        args: list[ExprAST] = []
        while True:
            args.append(self.parseExpression())
            if self.check(")"):
                break
            self.pop_pattern(",")
        self.pop_pattern(")")

        if name.text == "print":
            # it can be a builtin call to print
            if len(args) != 1:
                self.raise_error("Expected <single arg> as argument to print()")

            return PrintExprAST(loc(name), args[0])

        return CallExprAST(loc(name), name.text, args)

    def parsePrimary(self) -> ExprAST | None:
        """
        @brief Parse a primary expression.

        primary ::= identifierexpr
                ::= numberexpr
                ::= parenexpr
                ::= tensorliteral

        @return ExprAST representing the parsed expression or None if end of block
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
        elif current.text == ";":
            return None
        elif current.text == "}":
            return None
        else:
            self.raise_error("Expected expression or one of `;`, `}`")

    def parsePrimaryNotNone(self) -> ExprAST:
        """
        @brief Parse a primary expression, requiring a valid expression.

        primary ::= identifierexpr
                ::= numberexpr
                ::= parenexpr
                ::= tensorliteral

        @return ExprAST representing the parsed expression
        @throws ParseError if no valid expression is found
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
        else:
            self.raise_error("Expected expression")

    def parseBinOpRHS(self, exprPrec: int, lhs: ExprAST) -> ExprAST:
        """
        @brief Parse the right-hand side of a binary expression.

        This method handles operator precedence and builds the appropriate
        expression tree based on operator precedence.

        @param exprPrec: Current precedence level
        @param lhs: Left-hand side expression
        @return Complete binary expression with correct precedence handling
        """
        # if this is a binop, find its precedence
        while True:
            tokPrec = self.getTokenPrecedence()

            # if this is a binop that binds at least as tightly as the current binop,
            # consume it, otherwise we are done
            if tokPrec < exprPrec:
                return lhs

            # okay, we know this is a binop - could be +, -, *, /, % or =
            if self.check(CTokenKind.ASSIGN):
                binOp = self.pop_token(CTokenKind.ASSIGN).text
            else:
                # check for other operators in SINGLE_CHAR_TOKENS
                current_token = self.getToken()
                if current_token.text in ["+", "-", "*", "/", "%"]:
                    binOp = self.pop().text
                else:
                    return lhs  # not an operator we recognize

            # parse the primary expression after the binary operator
            rhs = self.parsePrimary()

            if rhs is None:
                self.raise_error("Expected expression to complete binary operator")

            # if BinOp binds less tightly with rhs than the operator after rhs, let
            # the pending operator take rhs as its lhs
            nextPrec = self.getTokenPrecedence()
            if tokPrec < nextPrec:
                rhs = self.parseBinOpRHS(tokPrec + 1, rhs)

            # merge lhs/rhs
            lhs = BinaryExprAST(rhs.loc, binOp, lhs, rhs)

    def parseExpression(self) -> ExprAST:
        """
        @brief Parse a complete expression.

        expression ::= primary binop rhs

        @return ExprAST representing the full expression
        """
        lhs = self.parsePrimaryNotNone()
        return self.parseBinOpRHS(0, lhs)

    def parseType(self):
        """
        @brief Parse a variable type with shape information.

        type ::= < shape_list >
        shape_list ::= num | num , shape_list

        @return VarType object with shape information
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
        """
        @brief Parse a C variable declaration.

        declaration ::= type identifier ['=' expr] ';'

        @return VarDeclExprAST representing the variable declaration
        @throws ParseError if the declaration syntax is invalid
        """
        # get variable type
        if (
            not self.check(CTokenKind.INT)
            and not self.check(CTokenKind.FLOAT)
            and not self.check(CTokenKind.DOUBLE)
            and not self.check(CTokenKind.CHAR)
        ):
            self.raise_error("Expected variable type")

        type_token = self.pop()
        var_type = type_token.text

        # get variable name
        if not self.check(CTokenKind.IDENTIFIER):
            self.raise_error("Expected variable name")

        name_token = self.pop_token(CTokenKind.IDENTIFIER)
        var_name = name_token.text

        # check for initialization
        expr = None
        if self.check("="):
            self.pop_pattern("=")
            expr = self.parseExpression()

        return VarDeclExprAST(loc(type_token), var_name, var_type, expr=expr)

    def parseDeclarationList(self):
        """
        @brief Parse a list of C variable declarations of the same type.

        declaration_list ::= type identifier ['=' expr] [, identifier ['=' expr]]* ';'

        @return List of VarDeclExprAST objects representing the variable declarations
        @throws ParseError if the declaration syntax is invalid
        """
        # get variable type
        if (
            not self.check(CTokenKind.INT)
            and not self.check(CTokenKind.FLOAT)
            and not self.check(CTokenKind.DOUBLE)
            and not self.check(CTokenKind.CHAR)
        ):
            self.raise_error("Expected variable type")

        type_token = self.pop()
        var_type = type_token.text

        # list to collect all declarations
        declarations = []

        # process variables until we hit a semicolon
        while True:
            # get variable name
            if not self.check(CTokenKind.IDENTIFIER):
                self.raise_error("Expected variable name")

            name_token = self.pop_token(CTokenKind.IDENTIFIER)
            var_name = name_token.text

            # check for initialization
            expr = None
            if self.check("="):
                self.pop_pattern("=")
                expr = self.parseExpression()

            # add declaration to the list
            declarations.append(
                VarDeclExprAST(loc(type_token), var_name, var_type, expr=expr)
            )

            # if no comma follows, we're done with this declaration list
            if not self.check(","):
                break

            # consume the comma and continue to the next variable
            self.pop_pattern(",")

        # expect a semicolon after all declarations
        self.pop_pattern(";")

        return declarations

    def parseBlock(self) -> tuple[ExprAST, ...]:
        """
        @brief Parse a C block: a list of statements wrapped in curly braces.

        block ::= '{' statement_list '}'
        statement_list ::= statement | statement statement_list
        statement ::= declaration_list | expression_statement | return_statement

        @return Tuple of ExprAST objects representing the statements in the block
        @throws ParseError if the block syntax is invalid
        """
        self.pop_pattern("{")
        exprList: list[ExprAST] = []

        while not self.check("}"):
            # check for type declaration
            if (
                self.check(CTokenKind.INT)
                or self.check(CTokenKind.FLOAT)
                or self.check(CTokenKind.DOUBLE)
                or self.check(CTokenKind.CHAR)
                or self.check(CTokenKind.VOID)
            ):
                # this is a variable declaration list
                declarations = self.parseDeclarationList()
                exprList.extend(declarations)
            elif self.check("return"):
                # return statement
                exprList.append(self.parseReturn())
                self.pop_pattern(";")
            else:
                # expression statement
                expr = self.parseExpression()
                exprList.append(expr)
                self.pop_pattern(";")

        self.pop_pattern("}")
        return tuple(exprList)

    def parsePrototype(self):
        """
        @brief Parse a C function prototype.

        prototype ::= return_type id '(' param_list ')'
        param_list ::= param | param, param_list
        param ::= type id

        @return PrototypeAST representing the function prototype
        @throws ParseError if the prototype syntax is invalid
        """
        # parse return type
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

        # parse function name
        if not self.check(CTokenKind.IDENTIFIER):
            self.raise_error("Expected function name")

        name_token = self.pop_token(CTokenKind.IDENTIFIER)
        fnName = name_token.text

        # parse parameter list
        self.pop_pattern("(")
        args: list[VariableExprAST] = []

        if not self.check(")"):
            while True:
                # parameter type
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

                # parameter name
                if not self.check(CTokenKind.IDENTIFIER):
                    self.raise_error("Expected parameter name")

                arg_token = self.pop_token(CTokenKind.IDENTIFIER)
                arg_name = arg_token.text

                # create variable expression with type information
                args.append(VariableExprAST(loc(arg_token), arg_name, param_type))

                # check for more parameters
                if not self.check(","):
                    break
                self.pop_pattern(",")

        self.pop_pattern(")")
        return PrototypeAST(loc(returnTypeToken), fnName, args, return_type)

    def parseDefinition(self):
        """
        @brief Parse a C function definition.

        definition ::= prototype '{' statement_list '}'

        @return FunctionAST representing the complete function definition
        @throws ParseError if the function definition syntax is invalid
        """
        proto = self.parsePrototype()
        block = self.parseBlock()
        return FunctionAST(proto.loc, proto, block)