"""Abstract Syntax Tree (AST) definitions for the C to Quantum compiler.

This module defines the AST node classes used to represent C code after parsing.
These classes form a hierarchical structure that captures the semantic meaning
of the original C code, which can then be transformed into quantum IR.

The AST is designed to represent a subset of C language constructs that are
relevant for quantum computing transformations, including variable declarations,
function definitions, expressions, and control flow.
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from enum import Enum

from .location import Location

INDENT = 2


@dataclass
class VarType:
    """A variable type with shape information.

    Represents the type of a variable in the AST, including any shape information
    for array or tensor types that may be needed for quantum representations.

    Attributes:
        shape: List of integers representing the dimensions of the type.
    """

    shape: list[int]


class ExprASTKind(Enum):
    """Enumeration of expression AST node types.

    This enum defines the different kinds of expression nodes that can exist
    in the AST, which is useful for type checking and visitor pattern implementations.
    """

    Expr_VarDecl = 1
    Expr_Return = 2
    Expr_Num = 3
    Expr_Literal = 4
    Expr_Var = 5
    Expr_BinOp = 6
    Expr_Call = 7
    Expr_Print = 8


@dataclass()
class Dumper:
    """Utility class for pretty-printing AST nodes.

    This class provides methods to format and output the structure of AST nodes
    with proper indentation, making it easier to visualize and debug the AST.

    Attributes:
        lines: List of strings representing the output lines.
        indentation: Current indentation level.
    """

    lines: list[str]
    indentation: int = 0

    def append(self, prefix: str, line: str):
        """Append a line to the output with the current indentation.

        Args:
            prefix: String to prepend to the line.
            line: The line content to append.
        """
        self.lines.append(" " * self.indentation * INDENT + prefix + line)

    def append_list(
        self,
        prefix: str,
        open_paren: str,
        exprs: Iterable[ExprAST | FunctionAST],
        close_paren: str,
        block: Callable[[Dumper, ExprAST | FunctionAST], None],
    ):
        """Append a list of expressions with opening and closing delimiters.

        Args:
            prefix: String to prepend to the opening delimiter.
            open_paren: Opening delimiter string.
            exprs: Iterable of expressions to format.
            close_paren: Closing delimiter string.
            block: Callback function to format each expression.
        """
        self.append(prefix, open_paren)
        child = self.child()
        for expr in exprs:
            block(child, expr)
        self.append("", close_paren)

    def child(self):
        """Create a new Dumper with increased indentation.

        Returns:
            A new Dumper instance with indentation incremented.
        """
        return Dumper(self.lines, self.indentation + 1)

    @property
    def message(self):
        """Get the complete formatted output as a string.

        Returns:
            The joined lines as a single string.
        """
        return "\n".join(self.lines)


@dataclass
class ExprAST:
    """Base class for all expression AST nodes.

    This abstract class serves as the parent for all expression types in the AST.
    It provides common functionality like source location tracking and debugging output.

    Attributes:
        loc: Source code location information for this expression.
    """

    loc: Location

    def __init__(self, loc: Location):
        """Initialize an expression AST node.

        Args:
            loc: Source code location information for this expression.
        """
        self.loc = loc

    @property
    def kind(self) -> ExprASTKind:
        """Get the kind of this expression.

        Returns:
            The ExprASTKind enumeration value for this expression type.

        Raises:
            AssertionError: If not implemented by subclass.
        """
        raise AssertionError(f"ExprAST kind not defined for {type(self)}")

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this expression for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append(prefix, self.__class__.__name__)

    def dump(self):
        """Create a string representation of this expression.

        Returns:
            Formatted string representation of the expression.
        """
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message


@dataclass
class VarDeclExprAST(ExprAST):
    """Expression class for defining a variable.

    Represents a variable declaration in the source code, including its name,
    type information, and optional initialization expression.

    Attributes:
        name: The variable name.
        type_name: The C type name (int, float, etc.).
        varType: Optional tensor dimensions information.
        expr: Optional initialization expression.
    """

    name: str
    type_name: str  # c type (int, float, etc.)
    varType: VarType | None = None  # for tensor dimensions if needed
    expr: ExprAST | None = None  # initialization is optional

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_VarDecl.
        """
        return ExprASTKind.Expr_VarDecl

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this variable declaration for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dims_str = ""
        if self.varType and self.varType.shape:
            dims_str = (
                "<" + ", ".join(f"{int(dim)}" for dim in self.varType.shape) + ">"
            )

        dumper.append(
            "Variable declaration: ", f"{self.type_name} {self.name}{dims_str}"
        )
        if self.expr:
            child = dumper.child()
            self.expr.inner_dump("Initial value: ", child)


@dataclass
class ReturnExprAST(ExprAST):
    """Expression class for a return statement.

    Represents a return statement in the source code, including its
    optional return value expression.

    Attributes:
        expr: Optional expression representing the return value.
    """

    expr: ExprAST | None

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_Return.
        """
        return ExprASTKind.Expr_Return

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this return statement for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append(prefix, "Return statement")
        if self.expr is not None:
            expr_child = dumper.child()
            self.expr.inner_dump("Return value: ", expr_child)


@dataclass
class NumberExprAST(ExprAST):
    """Expression class for numeric literals like "1.0".

    Represents a numeric literal in the source code.

    Attributes:
        val: The floating-point value of the numeric literal.
    """

    val: float

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_Num.
        """
        return ExprASTKind.Expr_Num

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this numeric literal for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        # format number more nicely without scientific notation for small integers
        if self.val.is_integer() and abs(self.val) < 1000000:
            dumper.append(prefix, f"{int(self.val)}")
        else:
            dumper.append(prefix, f"{self.val:.6g}")


@dataclass
class LiteralExprAST(ExprAST):
    """Expression class for a literal array or tensor value.

    Represents a multi-dimensional array or tensor literal in the source code.

    Attributes:
        values: Nested list of literal or number expressions.
        dims: List of dimensions for this literal.
    """

    values: list[LiteralExprAST | NumberExprAST]
    dims: list[int]

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_Literal.
        """
        return ExprASTKind.Expr_Literal

    def __dump(self) -> str:
        """Helper method to create a string representation of this literal.

        Returns:
            Formatted string representation of the literal.
        """
        dims_str = ", ".join(f"{int(dim)}" for dim in self.dims)
        vals_str = ",".join(
            val.__dump() if isinstance(val, LiteralExprAST) else val.dump()
            for val in self.values
        )
        return f" <{dims_str}>[{vals_str}]"

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this literal for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append("Literal:", self.__dump() + f" @{self.loc}")

    def iter_flattened_values(self) -> Generator[float, None, None]:
        """Iterate through all numeric values in this literal.

        Recursively traverses the literal structure and yields all numeric values.

        Yields:
            Each numeric value in the literal.
        """
        for value in self.values:
            if isinstance(value, NumberExprAST):
                yield value.val
            else:
                yield from value.iter_flattened_values()

    def flattened_values(self) -> list[float]:
        """Get all numeric values in this literal as a flat list.

        Returns:
            List containing all numeric values in the literal.
        """
        return list(self.iter_flattened_values())


@dataclass
class VariableExprAST(ExprAST):
    """Expression class for referencing a variable, like "a".

    Represents a variable reference in the source code.

    Attributes:
        name: The name of the referenced variable.
        type_name: Optional type information for the variable.
    """

    name: str
    type_name: str | None = None  # add type information for C variables

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_Var.
        """
        return ExprASTKind.Expr_Var

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this variable reference for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        type_info = f":{self.type_name}" if self.type_name else ""
        dumper.append("Variable: ", f"{self.name}{type_info}")


@dataclass
class BinaryExprAST(ExprAST):
    """Expression class for a binary operator.

    Represents a binary operation in the source code, such as addition,
    subtraction, or assignment.

    Attributes:
        op: The operator string (e.g., "+", "-", "=").
        lhs: The left-hand side expression.
        rhs: The right-hand side expression.
    """

    op: str
    lhs: ExprAST
    rhs: ExprAST

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_BinOp.
        """
        return ExprASTKind.Expr_BinOp

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this binary operation for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append(f"Operation: {self.op}", "")
        lhs_child = dumper.child()
        self.lhs.inner_dump("Left operand: ", lhs_child)
        rhs_child = dumper.child()
        self.rhs.inner_dump("Right operand: ", rhs_child)


@dataclass
class CallExprAST(ExprAST):
    """Expression class for a function call.

    Represents a function call in the source code, including the function
    name and its arguments.

    Attributes:
        callee: The name of the called function.
        args: List of argument expressions.
    """

    callee: str
    args: list[ExprAST]

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_Call.
        """
        return ExprASTKind.Expr_Call

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this function call for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append(prefix, f"Function call: '{self.callee}'")

        if self.args:
            args_child = dumper.child()
            args_child.append("Arguments:", "")
            for i, arg in enumerate(self.args):
                arg_child = args_child.child()
                arg.inner_dump(f"Arg {i}: ", arg_child)


@dataclass
class PrintExprAST(ExprAST):
    """Expression class for builtin print calls.

    Represents a call to the builtin print function in the source code.

    Attributes:
        arg: The expression to be printed.
    """

    arg: ExprAST

    @property
    def kind(self):
        """Get the kind of this expression.

        Returns:
            ExprASTKind.Expr_Print.
        """
        return ExprASTKind.Expr_Print

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this print statement for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        super().inner_dump(prefix, dumper)
        child = dumper.child()
        self.arg.inner_dump("arg: ", child)


@dataclass
class PrototypeAST:
    """Class representing a function prototype.

    This class captures the signature of a function, including its name,
    return type, and parameter information. It's used both for function
    declarations and definitions.

    Attributes:
        loc: Source code location information for this prototype.
        name: The function name.
        args: List of parameter variable expressions.
        return_type: The function's return type as a string.
    """

    loc: Location
    name: str
    args: list[VariableExprAST]
    return_type: str = "void"

    def dump(self):
        """Create a string representation of this prototype.

        Returns:
            Formatted string representation of the prototype.
        """
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this prototype for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append("", f"Function signature: '{self.name}' -> {self.return_type}")
        params = ", ".join(f"{arg.type_name} {arg.name}" for arg in self.args)
        dumper.append("Parameters: ", f"[{params}]")


@dataclass
class FunctionAST:
    """Class representing a function definition.

    This class represents a complete function definition, including its
    prototype (signature) and body (sequence of statements).

    Attributes:
        loc: Source code location information for this function.
        proto: The function prototype/signature.
        body: Tuple of expressions forming the function body.
    """

    loc: Location
    proto: PrototypeAST
    body: tuple[ExprAST, ...]

    def dump(self):
        """Create a string representation of this function.

        Returns:
            Formatted string representation of the function.
        """
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this function for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append("Function Definition:", "")
        proto_child = dumper.child()
        self.proto.inner_dump("", proto_child)

        if self.body:
            body_child = dumper.child()
            body_child.append("Body:", "")
            for stmt in self.body:
                stmt_child = body_child.child()
                stmt.inner_dump("", stmt_child)
            body_child.append("End of function body", "")


@dataclass
class ModuleAST:
    """Class representing a module (compilation unit).

    This class represents a complete C module, which consists of a collection
    of function definitions that are processed together.

    Attributes:
        funcs: Tuple of function definitions in this module.
    """

    funcs: tuple[FunctionAST, ...]

    def dump(self):
        """Create a string representation of this module.

        Returns:
            Formatted string representation of the module.
        """
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message

    def inner_dump(self, prefix: str, dumper: Dumper):
        """Format this module for debugging output.

        Args:
            prefix: String to prepend to the output.
            dumper: Dumper instance to append formatted output to.
        """
        dumper.append_list(
            prefix, "Module:", self.funcs, "", lambda dd, func: func.inner_dump("", dd)
        )
