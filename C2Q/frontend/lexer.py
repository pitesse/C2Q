"""
@file lexer.py
@brief Lexical analyzer for C source code in the C to Quantum compiler.

This module implements a lexical analyzer (lexer) for a subset of the C
programming language. It tokenizes C source code by breaking it into individual
tokens such as identifiers, keywords, operators, and literals, which can then
be processed by the parser to build an Abstract Syntax Tree (AST).

The lexer handles C constructs such as comments, identifiers, numbers, operators,
and punctuation. It is built on top of the xdsl lexer utilities.
"""

import re
from enum import Enum, auto
from string import hexdigits
from typing import TypeAlias, cast

from xdsl.utils.exceptions import ParseError
from xdsl.utils.lexer import Lexer, Position, Span, Token


class CTokenKind(Enum):
    """
    @brief Enumeration of token types recognized by the C lexer.

    This enum defines all the different types of tokens that the lexer can
    identify in the C source code, such as punctuation, operators, types,
    keywords, and other language constructs.
    """

    # punctuation
    SEMICOLON = auto()
    PARENTHESE_OPEN = auto()
    PARENTHESE_CLOSE = auto()
    BRACKET_OPEN = auto()
    BRACKET_CLOSE = auto()
    COMMA = auto()

    # operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    ASSIGN = auto()

    # c types
    INT = auto()
    FLOAT = auto()
    DOUBLE = auto()
    CHAR = auto()
    VOID = auto()

    # keywords
    RETURN = auto()

    # other token types
    IDENTIFIER = auto()
    NUMBER = auto()
    EOF = auto()


SINGLE_CHAR_TOKENS = {
    ";": CTokenKind.SEMICOLON,
    "(": CTokenKind.PARENTHESE_OPEN,
    ")": CTokenKind.PARENTHESE_CLOSE,
    "{": CTokenKind.BRACKET_OPEN,
    "}": CTokenKind.BRACKET_CLOSE,
    ",": CTokenKind.COMMA,
    "+": CTokenKind.PLUS,
    "-": CTokenKind.MINUS,
    "*": CTokenKind.MULTIPLY,
    "/": CTokenKind.DIVIDE,
    "%": CTokenKind.MODULO,
    "=": CTokenKind.ASSIGN,
}

C_KEYWORDS = {
    "int": CTokenKind.INT,
    "float": CTokenKind.FLOAT,
    "double": CTokenKind.DOUBLE,
    "char": CTokenKind.CHAR,
    "void": CTokenKind.VOID,
    "return": CTokenKind.RETURN,
}

IDENTIFIER_CHARS = re.compile(r"[\w]|[\d]|_")
SPECIAL_CHARS = set(",")


CToken: TypeAlias = Token[CTokenKind]


class CLexer(Lexer[CTokenKind]):
    """
    @brief Lexical analyzer for C source code.

    This class implements a lexer for a subset of the C programming language.
    It processes C source code character by character and produces a stream of
    tokens that can be consumed by the parser.

    The lexer handles whitespace, comments, identifiers, keywords, numbers,
    and various operators and punctuation marks defined in the C language.

    @see CTokenKind
    @see CParser
    """

    def _is_in_bounds(self, size: Position = 1) -> bool:
        """
        @brief Check if the current position is within the bounds of the input.

        @param size: Number of characters ahead to check
        @return True if the position plus size is within bounds, False otherwise
        """
        return self.pos + size - 1 < self.input.len

    def _get_chars(self, size: int = 1) -> str | None:
        """
        @brief Get the character at the current location and advance the position.

        Retrieves one or more characters starting at the current position and
        advances the lexer position accordingly.

        @param size: Number of characters to retrieve
        @return The retrieved characters or None if position is out of bounds
        """
        res = self.input.slice(self.pos, self.pos + size)
        self.pos += size
        return res

    def _peek_chars(self, size: int = 1) -> str | None:
        """
        @brief Peek at the character(s) at the current location without advancing.

        @param size: Number of characters to peek at
        @return The characters at the current position or None if out of bounds
        """
        return self.input.slice(self.pos, self.pos + size)

    def _consume_chars(self, size: int = 1) -> None:
        """
        @brief Advance the lexer position in the input by the given amount.

        @param size: Number of characters to skip
        """
        self.pos += size

    def _consume_regex(self, regex: re.Pattern[str]) -> re.Match[str] | None:
        """
        @brief Advance the lexer position to the end of the next regex match.

        Attempts to match the given regular expression at the current position
        and advances the position to the end of the match if successful.

        @param regex: Regular expression pattern to match
        @return The match object if matched, None otherwise
        """
        match = regex.match(self.input.content, self.pos)
        if match is None:
            return None
        self.pos = match.end()
        return match

    _whitespace_regex = re.compile(
        r"(\s+|(//[^\n]*(\n)?)|(/\*([^*]|\*[^/])*\*/))*", re.DOTALL
    )

    def _consume_whitespace(self) -> None:
        """
        @brief Consume whitespace and comments.

        Advances the lexer position past any whitespace characters and C-style
        comments (both // line comments and /* block comments */).
        """
        self._consume_regex(self._whitespace_regex)

    def lex(self) -> CToken:
        """
        @brief Lex the next token from the input.

        This is the main lexing function that identifies and returns the next
        token from the input. It handles whitespace, identifiers, keywords,
        numbers, and single-character tokens.

        @return The next token from the input
        @throws ParseError if an unexpected character is encountered
        """
        # first, skip whitespaces and comments
        self._consume_whitespace()

        start_pos = self.pos
        current_char = self._get_chars()

        # handle end of file
        if current_char is None:
            return self._form_token(CTokenKind.EOF, start_pos)

        # process identifier or keyword
        if current_char.isalpha() or current_char == "_":
            return self._lex_bare_identifier(start_pos)

        # handle single-char punctuation
        single_char_token_kind = SINGLE_CHAR_TOKENS.get(current_char)
        if single_char_token_kind is not None:
            return self._form_token(single_char_token_kind, start_pos)

        # process numeric literal
        if current_char.isnumeric():
            return self._lex_number(start_pos)

        raise ParseError(
            Span(start_pos, start_pos + 1, self.input),
            f"Unexpected character: {current_char}",
        )

    IDENTIFIER_SUFFIX = r"[a-zA-Z0-9_$.]*"
    bare_identifier_suffix_regex = re.compile(IDENTIFIER_SUFFIX)

    def _lex_bare_identifier(self, start_pos: Position) -> CToken:
        """
        @brief Lex a bare identifier or keyword.

        Processes an identifier or keyword according to the following grammar:
        `bare-id ::= (letter|[_]) (letter|digit|[_])*`

        The first character is expected to have already been consumed.

        @param start_pos: Starting position of the identifier
        @return A token of type IDENTIFIER or the appropriate keyword type
        """
        self._consume_regex(self.bare_identifier_suffix_regex)

        # get the entire identifier
        identifier = self.input.slice(start_pos, self.pos)

        # check if it's a keyword
        if identifier in C_KEYWORDS:
            return self._form_token(C_KEYWORDS[identifier], start_pos)

        return self._form_token(CTokenKind.IDENTIFIER, start_pos)

    _hexdigits_star_regex = re.compile(r"[0-9a-fA-F]*")
    _digits_star_regex = re.compile(r"[0-9]*")
    _fractional_suffix_regex = re.compile(r"\.[0-9]*([eE][+-]?[0-9]+)?")

    def _lex_number(self, start_pos: Position) -> CToken:
        """
        @brief Lex a numeric literal.

        Processes a numeric literal, which can be either:
        - A decimal number (possibly with fractional part)
        - A hexadecimal number (0x prefix followed by hex digits)

        The first character is expected to have already been consumed.

        @param start_pos: Starting position of the number
        @return A token of type NUMBER
        """
        first_digit = self.input.at(self.pos - 1)

        # handle hexadecimal numbers (starting with 0x)
        # a string like '0xi32' would be parsed incorrectly without this check
        if (
            first_digit == "0"
            and self._peek_chars() == "x"
            and self._is_in_bounds(2)
            and cast(str, self.input.at(self.pos + 1)) in hexdigits
        ):
            self._consume_chars(2)
            self._consume_regex(self._hexdigits_star_regex)
            return self._form_token(CTokenKind.NUMBER, start_pos)

        # handle decimal numbers
        self._consume_regex(self._digits_star_regex)

        # check for floating point with decimal part
        match = self._consume_regex(self._fractional_suffix_regex)
        if match is not None:
            return self._form_token(CTokenKind.NUMBER, start_pos)
        return self._form_token(CTokenKind.NUMBER, start_pos)