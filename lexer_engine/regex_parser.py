"""
Hand-written Regular Expression Parser (Zero `import re`).

Supports:
- Literals & escapes: \\n, \\t, \\r, \\\\, \\|, \\*, \\+, \\?, \\(, \\), \\[, \\], \\., \\-, \\^, \\", \\'
- Shorthand classes: \\d ([0-9]), \\w ([a-zA-Z0-9_]), \\s ([ \\t\\n\\r]), \\e or ε (epsilon)
- Dot wildcard `.` (any character in Sigma except '\\n')
- Character classes `[a-zA-Z0-9_]`, negated classes `[^"\\n]`
- Operators with formal precedence:
    1. Grouping (...) & Atom / CharClass
    2. Quantifiers (unary postfix): *, +, ?
    3. Concatenation (implicit, binary left-associative)
    4. Alternation | (binary left-associative)

Outputs:
- Typed AST (used by both Thompson Construction and Direct RE -> DFA)
- Explicit-concatenation infix & Shunting-Yard Postfix representation (for inspection/UI)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, List, Optional, Set, Tuple

from .models import SIGMA, format_charset


class RegexSyntaxError(ValueError):
    """Raised when a Regular Expression has invalid syntax."""

    def __init__(self, message: str, position: int = -1, pattern: str = "") -> None:
        self.position = position
        self.pattern = pattern
        loc = f" tại vị trí {position}" if position >= 0 else ""
        super().__init__(f"Lỗi cú pháp RE{loc}: {message}")


# ---------------------------------------------------------------------------
# AST Nodes
# ---------------------------------------------------------------------------

class RegexNode:
    """Base class for Regular Expression AST nodes."""

    def is_nullable(self) -> bool:
        raise NotImplementedError

    def to_postfix_tokens(self) -> List[str]:
        raise NotImplementedError

    def to_explicit_infix(self) -> str:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError


@dataclass(frozen=True)
class EpsilonNode(RegexNode):
    def is_nullable(self) -> bool:
        return True

    def to_postfix_tokens(self) -> List[str]:
        return ["ε"]

    def to_explicit_infix(self) -> str:
        return "ε"

    def to_dict(self) -> dict:
        return {"type": "EPSILON", "label": "ε"}


@dataclass(frozen=True)
class CharSetNode(RegexNode):
    chars: FrozenSet[str]
    label: str

    def is_nullable(self) -> bool:
        return False

    def to_postfix_tokens(self) -> List[str]:
        return [self.label]

    def to_explicit_infix(self) -> str:
        return self.label

    def to_dict(self) -> dict:
        return {"type": "CHARSET", "label": self.label, "size": len(self.chars)}


@dataclass(frozen=True)
class ConcatNode(RegexNode):
    left: RegexNode
    right: RegexNode

    def is_nullable(self) -> bool:
        return self.left.is_nullable() and self.right.is_nullable()

    def to_postfix_tokens(self) -> List[str]:
        return self.left.to_postfix_tokens() + self.right.to_postfix_tokens() + ["·"]

    def to_explicit_infix(self) -> str:
        l_str = self.left.to_explicit_infix()
        r_str = self.right.to_explicit_infix()
        if isinstance(self.left, UnionNode):
            l_str = f"({l_str})"
        if isinstance(self.right, UnionNode):
            r_str = f"({r_str})"
        return f"{l_str}·{r_str}"

    def to_dict(self) -> dict:
        return {
            "type": "CONCAT",
            "label": "·",
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


@dataclass(frozen=True)
class UnionNode(RegexNode):
    left: RegexNode
    right: RegexNode

    def is_nullable(self) -> bool:
        return self.left.is_nullable() or self.right.is_nullable()

    def to_postfix_tokens(self) -> List[str]:
        return self.left.to_postfix_tokens() + self.right.to_postfix_tokens() + ["|"]

    def to_explicit_infix(self) -> str:
        return f"({self.left.to_explicit_infix()}|{self.right.to_explicit_infix()})"

    def to_dict(self) -> dict:
        return {
            "type": "UNION",
            "label": "|",
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


@dataclass(frozen=True)
class StarNode(RegexNode):
    child: RegexNode

    def is_nullable(self) -> bool:
        return True

    def to_postfix_tokens(self) -> List[str]:
        return self.child.to_postfix_tokens() + ["*"]

    def to_explicit_infix(self) -> str:
        inner = self.child.to_explicit_infix()
        if isinstance(self.child, (ConcatNode, UnionNode)):
            inner = f"({inner})"
        return f"{inner}*"

    def to_dict(self) -> dict:
        return {"type": "STAR", "label": "*", "child": self.child.to_dict()}


@dataclass(frozen=True)
class PlusNode(RegexNode):
    child: RegexNode

    def is_nullable(self) -> bool:
        return self.child.is_nullable()

    def to_postfix_tokens(self) -> List[str]:
        return self.child.to_postfix_tokens() + ["+"]

    def to_explicit_infix(self) -> str:
        inner = self.child.to_explicit_infix()
        if isinstance(self.child, (ConcatNode, UnionNode)):
            inner = f"({inner})"
        return f"{inner}+"

    def to_dict(self) -> dict:
        return {"type": "PLUS", "label": "+", "child": self.child.to_dict()}


@dataclass(frozen=True)
class OptionalNode(RegexNode):
    child: RegexNode

    def is_nullable(self) -> bool:
        return True

    def to_postfix_tokens(self) -> List[str]:
        return self.child.to_postfix_tokens() + ["?"]

    def to_explicit_infix(self) -> str:
        inner = self.child.to_explicit_infix()
        if isinstance(self.child, (ConcatNode, UnionNode)):
            inner = f"({inner})"
        return f"{inner}?"

    def to_dict(self) -> dict:
        return {"type": "OPTIONAL", "label": "?", "child": self.child.to_dict()}


# ---------------------------------------------------------------------------
# Shorthand sets
# ---------------------------------------------------------------------------

SHORTHAND_CLASSES = {
    "d": frozenset("0123456789"),
    "w": frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"),
    "s": frozenset(" \t\n\r"),
}

ESCAPE_CHARS = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "\\": "\\",
    "|": "|",
    "*": "*",
    "+": "+",
    "?": "?",
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    ".": ".",
    "-": "-",
    "^": "^",
    '"': '"',
    "'": "'",
    " ": " ",
}


# ---------------------------------------------------------------------------
# Recursive-Descent Regular Expression Parser
# ---------------------------------------------------------------------------

class RegexParser:
    """
    Formal Grammar for Regular Expressions:
        expr   -> concat ('|' concat)*
        concat -> repeat+
        repeat -> atom ('*' | '+' | '?')*
        atom   -> '(' expr ')' | char_class | '.' | escape | 'ε' | literal
    """

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)

    def _peek(self) -> Optional[str]:
        if self.pos < self.length:
            return self.pattern[self.pos]
        return None

    def _advance(self) -> str:
        ch = self.pattern[self.pos]
        self.pos += 1
        return ch

    def parse(self) -> RegexNode:
        if self.length == 0:
            raise RegexSyntaxError("Biểu thức chính quy không được rỗng", 0, self.pattern)
        node = self._parse_expr()
        if self.pos < self.length:
            raise RegexSyntaxError(
                f"Ký tự dư thừa không hợp lệ '{self.pattern[self.pos]}'",
                self.pos,
                self.pattern,
            )
        return node

    def _parse_expr(self) -> RegexNode:
        left = self._parse_concat()
        while self._peek() == "|":
            bar_pos = self.pos
            self._advance()
            if self._peek() in (None, ")", "|"):
                raise RegexSyntaxError("Thiếu vế phải sau toán tử '|'", bar_pos, self.pattern)
            right = self._parse_concat()
            left = UnionNode(left, right)
        return left

    def _parse_concat(self) -> RegexNode:
        if self._peek() in (None, "|", ")"):
            raise RegexSyntaxError(
                "Biểu thức con bị rỗng (thiếu toán hạng)",
                self.pos,
                self.pattern,
            )
        node = self._parse_repeat()
        while self._peek() not in (None, "|", ")"):
            rhs = self._parse_repeat()
            node = ConcatNode(node, rhs)
        return node

    def _parse_repeat(self) -> RegexNode:
        node = self._parse_atom()
        while self._peek() in ("*", "+", "?"):
            op = self._advance()
            if op == "*":
                node = StarNode(node)
            elif op == "+":
                node = PlusNode(node)
            elif op == "?":
                node = OptionalNode(node)
        return node

    def _parse_atom(self) -> RegexNode:
        ch = self._peek()
        if ch is None:
            raise RegexSyntaxError("Kết thúc biểu thức bất ngờ", self.pos, self.pattern)

        if ch in ("*", "+", "?", "|", ")"):
            raise RegexSyntaxError(
                f"Toán tử '{ch}' không có toán hạng đứng trước",
                self.pos,
                self.pattern,
            )

        if ch == "(":
            open_pos = self.pos
            self._advance()
            if self._peek() == ")":
                raise RegexSyntaxError("Cặp ngoặc rỗng '()' không hợp lệ", open_pos, self.pattern)
            inner = self._parse_expr()
            if self._peek() != ")":
                raise RegexSyntaxError("Thiếu dấu đóng ngoặc ')'", open_pos, self.pattern)
            self._advance()
            return inner

        if ch == "[":
            return self._parse_char_class()

        if ch == ".":
            self._advance()
            chars = SIGMA - {"\n"}
            return CharSetNode(chars=chars, label=".")

        if ch == "ε":
            self._advance()
            return EpsilonNode()

        if ch == "\\":
            return self._parse_escape_atom()

        self._advance()
        if ch not in SIGMA:
            raise RegexSyntaxError(
                f"Ký tự '{ch}' (U+{ord(ch):04X}) nằm ngoài bảng chữ cái Σ hỗ trợ",
                self.pos - 1,
                self.pattern,
            )
        fset = frozenset({ch})
        return CharSetNode(chars=fset, label=format_charset(fset))

    def _parse_escape_atom(self) -> RegexNode:
        esc_pos = self.pos
        self._advance()  # consume '\'
        ch = self._peek()
        if ch is None:
            raise RegexSyntaxError("Dấu '\\' ở cuối biểu thức không có ký tự theo sau", esc_pos, self.pattern)
        self._advance()

        if ch == "e":
            return EpsilonNode()
        if ch in SHORTHAND_CLASSES:
            fset = SHORTHAND_CLASSES[ch]
            return CharSetNode(chars=fset, label=f"\\{ch}")
        if ch in ESCAPE_CHARS:
            val = ESCAPE_CHARS[ch]
            fset = frozenset({val})
            return CharSetNode(chars=fset, label=format_charset(fset))
        # Allow escaping any ASCII character in SIGMA as literal
        if ch in SIGMA:
            fset = frozenset({ch})
            return CharSetNode(chars=fset, label=format_charset(fset))
        raise RegexSyntaxError(f"Chuỗi escape '\\{ch}' không được hỗ trợ", esc_pos, self.pattern)

    def _parse_class_item(self) -> Tuple[Optional[str], FrozenSet[str]]:
        """
        Parse one item inside [...].
        Returns (single_char_if_applicable, charset).
        """
        ch = self._peek()
        if ch is None:
            raise RegexSyntaxError("Thiếu dấu đóng ']'", self.pos, self.pattern)
        if ch == "\\":
            esc_pos = self.pos
            self._advance()
            nxt = self._peek()
            if nxt is None:
                raise RegexSyntaxError("Dấu '\\' chưa hoàn tất trong [...]", esc_pos, self.pattern)
            self._advance()
            if nxt in SHORTHAND_CLASSES:
                return None, SHORTHAND_CLASSES[nxt]
            val = ESCAPE_CHARS.get(nxt, nxt)
            if val not in SIGMA:
                raise RegexSyntaxError(f"Ký tự '\\{nxt}' ngoài bảng chữ cái Σ", esc_pos, self.pattern)
            return val, frozenset({val})
        self._advance()
        if ch not in SIGMA:
            raise RegexSyntaxError(
                f"Ký tự '{ch}' trong lớp ký tự nằm ngoài bảng chữ cái Σ",
                self.pos - 1,
                self.pattern,
            )
        return ch, frozenset({ch})

    def _parse_char_class(self) -> CharSetNode:
        start_pos = self.pos
        self._advance()  # consume '['
        negated = False
        if self._peek() == "^":
            negated = True
            self._advance()

        chars: Set[str] = set()
        if self._peek() == "]":
            raise RegexSyntaxError("Lớp ký tự rỗng '[]' hoặc '[^]'", start_pos, self.pattern)

        while self._peek() is not None and self._peek() != "]":
            single_start, item_set = self._parse_class_item()
            # Check for range a-z (only if '-' is followed by something other than ']')
            if (
                single_start is not None
                and self._peek() == "-"
                and self.pos + 1 < self.length
                and self.pattern[self.pos + 1] != "]"
            ):
                dash_pos = self.pos
                self._advance()  # consume '-'
                single_end, end_set = self._parse_class_item()
                if single_end is None:
                    raise RegexSyntaxError(
                        "Không thể dùng lớp viết tắt (như \\d) làm đầu mút khoảng '-'",
                        dash_pos,
                        self.pattern,
                    )
                if ord(single_start) > ord(single_end):
                    raise RegexSyntaxError(
                        f"Khoảng ký tự không hợp lệ '{single_start}-{single_end}'",
                        dash_pos,
                        self.pattern,
                    )
                for code in range(ord(single_start), ord(single_end) + 1):
                    c = chr(code)
                    if c in SIGMA:
                        chars.add(c)
            else:
                chars.update(item_set)

        if self._peek() != "]":
            raise RegexSyntaxError("Thiếu dấu đóng ']' cho lớp ký tự", start_pos, self.pattern)
        self._advance()  # consume ']'

        final_set = (SIGMA - chars) if negated else frozenset(chars)
        if not final_set:
            raise RegexSyntaxError("Lớp ký tự sau khi phủ định là tập rỗng ∅", start_pos, self.pattern)
        raw_label = self.pattern[start_pos : self.pos]
        label = raw_label if len(raw_label) <= 18 else format_charset(final_set)
        return CharSetNode(chars=final_set, label=label)


def parse_regex(pattern: str) -> RegexNode:
    """Parse a regular expression string into its AST."""
    return RegexParser(pattern).parse()


def regex_to_postfix(pattern: str) -> List[str]:
    """Return postfix token list for a regex (for display & educational inspection)."""
    return parse_regex(pattern).to_postfix_tokens()
