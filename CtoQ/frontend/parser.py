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
    def __init__(self, file: Path, program: str):
        super().__init__(ParserState(CLexer(Input(program, str(file)))))

    def getToken(self):
        """Returns current token in parser"""
        return self._current_token

    def getTokenPrecedence(self) -> int:
        """Returns precedence if the current token is a binary operation, -1 otherwise"""
        PRECEDENCE = {
            "=": 10,   # Assignment has lower precedence
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
        Returns token matching pattern or None
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
        Verifies that the current token fits the pattern,
        returns False otherwise
        """
        return self.peek(pattern) is not None

    def pop(self) -> CToken:
        return self._consume_token()

    def pop_pattern(self, pattern: str) -> CToken:
        """
        Verifies that the current token fits the pattern,
        raises ParseError otherwise
        """
        token = self._consume_token()
        if token.text != pattern:
            self.raise_error(f"Expected '{pattern}'", token.span.start, token.span.end)
        return token

    def pop_token(self, tokenType: CTokenKind) -> CToken:
        """
        Verifies that the current token is of expected type,
        raises ParseError otherwise
        """
        return self._consume_token(tokenType)

    def parseModule(self):
        """
        Parse a full C module (a collection of function definitions)
        module ::= definition*
        """
        functions: list[FunctionAST] = []
        
        while not self.check(CTokenKind.EOF):
            functions.append(self.parseDefinition())
        
        # If we didn't reach EOF, there was an error during parsing
        self.pop_token(CTokenKind.EOF)
        
        return ModuleAST(tuple(functions))

    def parseReturn(self):
        """
        Parse a return statement:
        return_statement ::= 'return' [expression] ';'
        """
        returnToken = self.pop_pattern("return")
        expr = None
        
        # Return takes an optional expression
        if not self.check(";"):
            expr = self.parseExpression()
        
        return ReturnExprAST(loc(returnToken), expr)

    def parseNumberExpr(self):
        """
        Parse a literal number.
        numberexpr ::= number
        """
        numberToken = self.pop_token(CTokenKind.NUMBER)
        return NumberExprAST(loc(numberToken), float(numberToken.span.text))

    def parseTensorLiteralExpr(self) -> LiteralExprAST | NumberExprAST:
        """
        Parse a literal array expression.
        tensorLiteral ::= [ literalList ] | number
        literalList ::= tensorLiteral | tensorLiteral, literalList
        """
        if self.check(CTokenKind.NUMBER):
            return self.parseNumberExpr()

        openBracket = self.pop_pattern("[")

        # Hold the list of values at this nesting level.
        values: list[LiteralExprAST | NumberExprAST] = []
        # Hold the dimensions for all the nesting inside this level.
        dims: list[int] = []

        while True:
            # We can have either another nested array or a number literal.
            if self.check("["):
                values.append(self.parseTensorLiteralExpr())
            else:
                if not self.check(CTokenKind.NUMBER):
                    self.raise_error("Expected <num> or [ in literal expression")
                values.append(self.parseNumberExpr())

            # End of this list on ']'
            if self.check("]"):
                break

            # Elements are separated by a comma.
            self.pop_pattern(",")

        self.pop_pattern("]")

        # Fill in the dimensions now. First the current nesting level:
        dims.append(len(values))

        # If there is any nested array, process all of them and ensure
        # that dimensions are uniform.
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
        "parenexpr ::= '(' expression ')'"
        self.pop_pattern("(")
        v = self.parseExpression()
        self.pop_pattern(")")
        return v

    def parseIdentifierExpr(self):
        """
        identifierexpr
        ::= identifier
        ::= identifier '(' expression ')'
        """
        name = self.pop_token(CTokenKind.IDENTIFIER)
        if not self.check("("):
            # Simple variable ref.
            return VariableExprAST(loc(name), name.text)

        # This is a function call.
        self.pop_pattern("(")
        args: list[ExprAST] = []
        while True:
            args.append(self.parseExpression())
            if self.check(")"):
                break
            self.pop_pattern(",")
        self.pop_pattern(")")

        if name.text == "print":
            # It can be a builtin call to print
            if len(args) != 1:
                self.raise_error("Expected <single arg> as argument to print()")

            return PrintExprAST(loc(name), args[0])

        return CallExprAST(loc(name), name.text, args)

    def parsePrimary(self) -> ExprAST | None:
        """
        primary
        ::= identifierexpr
        ::= numberexpr
        ::= parenexpr
        ::= tensorliteral
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
        primary
        ::= identifierexpr
        ::= numberexpr
        ::= parenexpr
        ::= tensorliteral
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
        # If this is a binop, find its precedence.
        while True:
            tokPrec = self.getTokenPrecedence()
    
            # If this is a binop that binds at least as tightly as the current binop,
            # consume it, otherwise we are done.
            if tokPrec < exprPrec:
                return lhs
    
            # Okay, we know this is a binop - could be +, -, *, /, % or =
            if self.check(CTokenKind.ASSIGN):
                binOp = self.pop_token(CTokenKind.ASSIGN).text
            else:
                # Check for other operators in SINGLE_CHAR_TOKENS
                current_token = self.getToken()
                if current_token.text in ["+", "-", "*", "/", "%"]:
                    binOp = self.pop().text
                else:
                    return lhs  # Not an operator we recognize
    
            # Parse the primary expression after the binary operator.
            rhs = self.parsePrimary()
    
            if rhs is None:
                self.raise_error("Expected expression to complete binary operator")
    
            # If BinOp binds less tightly with rhs than the operator after rhs, let
            # the pending operator take rhs as its lhs.
            nextPrec = self.getTokenPrecedence()
            if tokPrec < nextPrec:
                rhs = self.parseBinOpRHS(tokPrec + 1, rhs)
    
            # Merge lhs/rhs
            lhs = BinaryExprAST(rhs.loc, binOp, lhs, rhs)

    def parseExpression(self) -> ExprAST:
        """expression::= primary binop rhs"""
        lhs = self.parsePrimaryNotNone()
        return self.parseBinOpRHS(0, lhs)

    def parseType(self):
        """
        type ::= < shape_list >
        shape_list ::= num | num , shape_list
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
        Parse a C variable declaration
        declaration ::= type identifier ['=' expr] ';'
        """
        # Get variable type
        if not self.check(CTokenKind.INT) and not self.check(CTokenKind.FLOAT) and \
           not self.check(CTokenKind.DOUBLE) and not self.check(CTokenKind.CHAR):
            self.raise_error("Expected variable type")
        
        type_token = self.pop()
        var_type = type_token.text
        
        # Get variable name
        if not self.check(CTokenKind.IDENTIFIER):
            self.raise_error("Expected variable name")
        
        name_token = self.pop_token(CTokenKind.IDENTIFIER)
        var_name = name_token.text
        
        # Check for initialization
        expr = None
        if self.check("="):
            self.pop_pattern("=")
            expr = self.parseExpression()
        
        return VarDeclExprAST(loc(type_token), var_name, var_type, expr=expr)

    def parseDeclarationList(self):
        """
        Parse a list of C variable declarations of the same type
        declaration_list ::= type identifier ['=' expr] [, identifier ['=' expr]]* ';'
        """
        # Get variable type
        if not self.check(CTokenKind.INT) and not self.check(CTokenKind.FLOAT) and \
        not self.check(CTokenKind.DOUBLE) and not self.check(CTokenKind.CHAR):
            self.raise_error("Expected variable type")
        
        type_token = self.pop()
        var_type = type_token.text
        
        # List to collect all declarations
        declarations = []
        
        # Process variables until we hit a semicolon
        while True:
            # Get variable name
            if not self.check(CTokenKind.IDENTIFIER):
                self.raise_error("Expected variable name")
            
            name_token = self.pop_token(CTokenKind.IDENTIFIER)
            var_name = name_token.text
            
            # Check for initialization
            expr = None
            if self.check("="):
                self.pop_pattern("=")
                expr = self.parseExpression()
            
            # Add declaration to the list
            declarations.append(VarDeclExprAST(loc(type_token), var_name, var_type, expr=expr))
            
            # If no comma follows, we're done with this declaration list
            if not self.check(","):
                break
                
            # Consume the comma and continue to the next variable
            self.pop_pattern(",")
        
        # Expect a semicolon after all declarations
        self.pop_pattern(";")
        
        return declarations

    def parseBlock(self) -> tuple[ExprAST, ...]:
        """
        Parse a C block: a list of statements wrapped in curly braces
        block ::= '{' statement_list '}'
        statement_list ::= statement | statement statement_list
        statement ::= declaration_list | expression_statement | return_statement
        """
        self.pop_pattern("{")
        exprList: list[ExprAST] = []
        
        while not self.check("}"):
            # Check for type declaration
            if self.check(CTokenKind.INT) or self.check(CTokenKind.FLOAT) or \
               self.check(CTokenKind.DOUBLE) or self.check(CTokenKind.CHAR) or \
               self.check(CTokenKind.VOID):
                # This is a variable declaration list
                declarations = self.parseDeclarationList()
                exprList.extend(declarations)
            elif self.check("return"):
                # Return statement
                exprList.append(self.parseReturn())
                self.pop_pattern(";")
            else:
                # Expression statement
                expr = self.parseExpression()
                exprList.append(expr)
                self.pop_pattern(";")
        
        self.pop_pattern("}")
        return tuple(exprList)

    def parsePrototype(self):
        """
        Parse a C function prototype
        prototype ::= return_type id '(' param_list ')'
        param_list ::= param | param, param_list
        param ::= type id
        """
        # Parse return type
        if not self.check(CTokenKind.INT) and not self.check(CTokenKind.FLOAT) and \
           not self.check(CTokenKind.DOUBLE) and not self.check(CTokenKind.VOID) and \
           not self.check(CTokenKind.CHAR):
            self.raise_error("Expected return type")
            
        returnTypeToken = self.pop()
        return_type = returnTypeToken.text
        
        # Parse function name
        if not self.check(CTokenKind.IDENTIFIER):
            self.raise_error("Expected function name")
        
        name_token = self.pop_token(CTokenKind.IDENTIFIER)
        fnName = name_token.text
        
        # Parse parameter list
        self.pop_pattern("(")
        args: list[VariableExprAST] = []
        
        if not self.check(")"):
            while True:
                # Parameter type
                if not self.check(CTokenKind.INT) and not self.check(CTokenKind.FLOAT) and \
                   not self.check(CTokenKind.DOUBLE) and not self.check(CTokenKind.VOID) and \
                   not self.check(CTokenKind.CHAR):
                    self.raise_error("Expected parameter type")
                
                param_type_token = self.pop()
                param_type = param_type_token.text
                
                # Parameter name
                if not self.check(CTokenKind.IDENTIFIER):
                    self.raise_error("Expected parameter name")
                
                arg_token = self.pop_token(CTokenKind.IDENTIFIER)
                arg_name = arg_token.text
                
                # Create variable expression with type information
                args.append(VariableExprAST(loc(arg_token), arg_name, param_type))
                
                # Check for more parameters
                if not self.check(","):
                    break
                self.pop_pattern(",")
        
        self.pop_pattern(")")
        return PrototypeAST(loc(returnTypeToken), fnName, args, return_type)

    def parseDefinition(self):
        """
        Parse a C function definition
        definition ::= prototype '{' statement_list '}'
        """
        proto = self.parsePrototype()
        block = self.parseBlock()
        return FunctionAST(proto.loc, proto, block)
