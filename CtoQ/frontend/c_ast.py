from __future__ import annotations

from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from enum import Enum

from .location import Location

INDENT = 2


@dataclass
class VarType:
    "A variable type with shape information."

    shape: list[int]


class ExprASTKind(Enum):
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
    lines: list[str]
    indentation: int = 0

    def append(self, prefix: str, line: str):
        self.lines.append(" " * self.indentation * INDENT + prefix + line)

    def append_list(
        self,
        prefix: str,
        open_paren: str,
        exprs: Iterable[ExprAST | FunctionAST],
        close_paren: str,
        block: Callable[[Dumper, ExprAST | FunctionAST], None],
    ):
        self.append(prefix, open_paren)
        child = self.child()
        for expr in exprs:
            block(child, expr)
        self.append("", close_paren)

    def child(self):
        return Dumper(self.lines, self.indentation + 1)

    @property
    def message(self):
        return "\n".join(self.lines)


@dataclass
class ExprAST:
    loc: Location

    def __init__(self, loc: Location):
        self.loc = loc
        print(self.dump())

    @property
    def kind(self) -> ExprASTKind:
        raise AssertionError(f"ExprAST kind not defined for {type(self)}")

    def inner_dump(self, prefix: str, dumper: Dumper):
        dumper.append(prefix, self.__class__.__name__)

    def dump(self):
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message


@dataclass
class VarDeclExprAST(ExprAST):
    "Expression class for defining a variable."

    name: str
    type_name: str  # C type (int, float, etc.)
    varType: VarType = None  # For tensor dimensions if needed
    expr: ExprAST = None  # Make initialization optional

    @property
    def kind(self):
        return ExprASTKind.Expr_VarDecl

    def inner_dump(self, prefix: str, dumper: Dumper):
        dims_str = ""
        if self.varType and self.varType.shape:
            dims_str = "<" + ", ".join(f"{int(dim)}" for dim in self.varType.shape) + ">"
        
        # Remove location info
        dumper.append("Variable declaration: ", f"{self.type_name} {self.name}{dims_str}")
        if self.expr:
            child = dumper.child()
            self.expr.inner_dump("Initial value: ", child)


@dataclass
class ReturnExprAST(ExprAST):
    "Expression class for a return operator."

    expr: ExprAST | None

    @property
    def kind(self):
        return ExprASTKind.Expr_Return

    def inner_dump(self, prefix: str, dumper: Dumper):
        dumper.append(prefix, "Return statement")
        if self.expr is not None:
            expr_child = dumper.child()
            self.expr.inner_dump("Return value: ", expr_child)


@dataclass
class NumberExprAST(ExprAST):
    'Expression class for numeric literals like "1.0".'

    val: float

    @property
    def kind(self):
        return ExprASTKind.Expr_Number

    def inner_dump(self, prefix: str, dumper: Dumper):
        # Format number more nicely without scientific notation for small integers
        if self.val.is_integer() and abs(self.val) < 1000000:
            dumper.append(prefix, f"{int(self.val)}")
        else:
            dumper.append(prefix, f"{self.val:.6g}")


@dataclass
class LiteralExprAST(ExprAST):
    "Expression class for a literal value."

    values: list[LiteralExprAST | NumberExprAST]
    dims: list[int]

    @property
    def kind(self):
        return ExprASTKind.Expr_Literal

    def __dump(self) -> str:
        dims_str = ", ".join(f"{int(dim)}" for dim in self.dims)
        vals_str = ",".join(
            val.__dump() if isinstance(val, LiteralExprAST) else val.dump()
            for val in self.values
        )
        return f" <{dims_str}>[{vals_str}]"

    def inner_dump(self, prefix: str, dumper: Dumper):
        dumper.append("Literal:", self.__dump() + f" @{self.loc}")

    def iter_flattened_values(self) -> Generator[float, None, None]:
        for value in self.values:
            if isinstance(value, NumberExprAST):
                yield value.val
            else:
                yield from value.iter_flattened_values()

    def flattened_values(self) -> list[float]:
        return list(self.iter_flattened_values())


@dataclass
class VariableExprAST(ExprAST):
    'Expression class for referencing a variable, like "a".'

    name: str
    type_name: str = None  # Add type information for C variables

    @property
    def kind(self):
        return ExprASTKind.Expr_Var

    def inner_dump(self, prefix: str, dumper: Dumper):
        type_info = f":{self.type_name}" if self.type_name else ""
        # Remove location info
        dumper.append("Variable: ", f"{self.name}{type_info}")


@dataclass
class BinaryExprAST(ExprAST):
    "Expression class for a binary operator."

    op: str
    lhs: ExprAST
    rhs: ExprAST

    @property
    def kind(self):
        return ExprASTKind.Expr_BinOp

    def inner_dump(self, prefix: str, dumper: Dumper):
        # Replace with more readable format without location
        dumper.append(f"Operation: {self.op}", "")
        lhs_child = dumper.child()
        self.lhs.inner_dump("Left operand: ", lhs_child)
        rhs_child = dumper.child()
        self.rhs.inner_dump("Right operand: ", rhs_child)


@dataclass
class CallExprAST(ExprAST):
    "Expression class for a function call."

    callee: str
    args: list[ExprAST]

    @property
    def kind(self):
        return ExprASTKind.Expr_Call

    def inner_dump(self, prefix: str, dumper: Dumper):
        # Remove location info
        dumper.append(prefix, f"Function call: '{self.callee}'")
        
        if self.args:
            args_child = dumper.child()
            args_child.append("Arguments:", "")
            for i, arg in enumerate(self.args):
                arg_child = args_child.child()
                arg.inner_dump(f"Arg {i}: ", arg_child)


@dataclass
class PrintExprAST(ExprAST):
    "Expression class for builtin print calls."

    arg: ExprAST

    @property
    def kind(self):
        return ExprASTKind.Expr_Print

    def inner_dump(self, prefix: str, dumper: Dumper):
        super().inner_dump(prefix, dumper)
        child = dumper.child()
        self.arg.inner_dump("arg: ", child)


@dataclass
class PrototypeAST:
    """
    This class represents the "prototype" for a function, which captures its
    name, its return type, and its argument names and types.
    """

    loc: Location
    name: str
    args: list[VariableExprAST]
    return_type: str = "void"  

    def dump(self):
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message

    def inner_dump(self, prefix: str, dumper: Dumper):
        # Remove location info and use more descriptive name
        dumper.append("", f"Function signature: '{self.name}' -> {self.return_type}")
        params = ", ".join(f"{arg.type_name} {arg.name}" for arg in self.args)
        dumper.append("Parameters: ", f"[{params}]")


@dataclass
class FunctionAST:
    """
    This class represents a function definition itself.
    """

    loc: Location
    proto: PrototypeAST
    body: tuple[ExprAST, ...]

    def dump(self):
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message

    def inner_dump(self, prefix: str, dumper: Dumper):
        # Use more descriptive format without location info
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
    "This class represents a list of functions to be processed together"

    funcs: tuple[FunctionAST, ...]

    def dump(self):
        dumper = Dumper([])
        self.inner_dump("", dumper)
        return dumper.message

    def inner_dump(self, prefix: str, dumper: Dumper):
        dumper.append_list(
            prefix, "Module:", self.funcs, "", lambda dd, func: func.inner_dump("", dd)
        )
