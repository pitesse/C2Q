"""Source code location tracking for the C to Quantum compiler.

This module provides utilities for tracking and representing source code locations
in the C to Quantum compiler. It's used primarily to map compiled quantum code
back to the original C source, which is essential for debugging and error reporting.
"""

import re
from dataclasses import dataclass

from typing_extensions import Any

from xdsl.utils.lexer import Token


@dataclass
class Location:
    """Structure representing a location in a source file.

    This dataclass stores the file path, line number, and column number
    that pinpoints a specific location in the source code. It's used for
    error reporting and debugging to provide precise information about
    where issues occur in the original source.
    
    Attributes:
        file: Path to the source file.
        line: Line number (1-based).
        col: Column number (1-based).
    """

    file: str
    line: int
    col: int

    def __repr__(self):
        """String representation of the location.

        Returns:
            String in the format "file:line:column".
        """
        return f"{self.file}:{self.line}:{self.col}"


_NEWLINE = re.compile(r"\n")


def loc(token: Token[Any]) -> Location:
    """Convert a lexer token to a source code location.

    This function calculates the line and column numbers for a token
    by counting newlines in the source text. It's used to map tokens
    from the lexer to their original positions in the source file.

    Args:
        token: The token whose location needs to be determined.
        
    Returns:
        A Location object with file, line, and column information.
        
    Raises:
        AssertionError: If the token's location cannot be determined.
    """
    file = token.span.input.name

    remaining = token.span.start
    prev_end = 0

    for line, newline_match in enumerate(
        re.finditer(_NEWLINE, token.span.input.content)
    ):
        len_line = newline_match.start() - prev_end
        if remaining < len_line:
            return Location(file, line + 1, remaining + 1)
        remaining -= len_line + 1
        prev_end = newline_match.end()

    raise AssertionError(f"Could not find location of token {token}")
