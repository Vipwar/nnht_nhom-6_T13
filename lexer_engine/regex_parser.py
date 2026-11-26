"""
Hand-written Regular Expression Parser (Zero `import re`).

Supports:
- Full 7-bit ASCII (0x00..0x7F, including \\0, \\t, \\n, \\v, \\f, \\r) + Explicit Unicode literals/classes
  (e.g., `nếu`, `€`, `[à-ỹ]`, `[^€]`) via Dynamic Unicode Alphabet Partitioning
- Hex & Unicode escapes: \\xHH, \\uHHHH, \\0, \\n, \\t, \\r, \\f, \\v, \\\\, \\|, \\*, \\+, \\?, etc.
- Shorthand classes: \\d ([0-9]), \\w ([a-zA-Z0-9_]), \\s ([ \\t\\n\\r\\f\\v]), \\e or ε (epsilon)
- Dot wildcard `.` (any character in Sigma(U) except '\\n')
- Character classes `[a-zA-Z0-9_]`, negated classes `[^"\\\\\\n\\r]`
- Operators with formal precedence:
    1. Grouping (...) & Atom / CharClass
    2. Quantifiers (unary postfix): *, +, ?, {m}, {m,}, {m,n}
    3. Concatenation (implicit, binary left-associative)
    4. Alternation | (binary left-associative)
- Anti-DoS AST Replication Bomb Protection:
    Enforces both `MAX_QUANTIFIER_BOUND = 64` and `MAX_AST_NODES = 4096` on unfolded AST size
    so nested counted quantifiers like `(((a{64}){64}){64})` are rejected in O(1) time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional, Set, Tuple

from .models import (
    NON_ASCII,
    build_dynamic_sigma,
    format_charset,
    lift_charset_to_unicode,
)

MAX_QUANTIFIER_BOUND = 64
MAX_AST_NODES = 4096
MAX_CHAR_RANGE_SPAN = 4096
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


class RegexSyntaxError(ValueError):
    """Raised when a Regular Expression has invalid syntax or exceeds safety bounds."""

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

    def node_count(self) -> int:
        """Exact number of nodes in the unfolded AST tree."""
        raise NotImplementedError

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        """All explicit non-ASCII code points referenced positively or negatively in this AST."""
        raise NotImplementedError

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "RegexNode":
        """Lift all character sets in this AST onto Sigma(target_unicode)."""
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

    def node_count(self) -> int:
        return 1

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        return frozenset()

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "RegexNode":
        return self

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
    own_unicode: FrozenSet[str] = field(default_factory=frozenset)

    def is_nullable(self) -> bool:
        return False

    def node_count(self) -> int:
        return 1

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        pos_u = frozenset(c for c in self.chars if ord(c) >= 128 and c != NON_ASCII)
        return pos_u | self.own_unicode

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "CharSetNode":
        merged_u = self.explicit_unicode_chars() | frozenset(
            c for c in target_unicode if ord(c) >= 128 and c != NON_ASCII
        )
        if merged_u == self.own_unicode:
            return self
        lifted = lift_charset_to_unicode(self.chars, self.own_unicode, merged_u)
        return CharSetNode(chars=lifted, label=self.label, own_unicode=merged_u)

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
    _size: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_size", 1 + self.left.node_count() + self.right.node_count())

    def is_nullable(self) -> bool:
        return self.left.is_nullable() and self.right.is_nullable()

    def node_count(self) -> int:
        return self._size

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        return self.left.explicit_unicode_chars() | self.right.explicit_unicode_chars()

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "ConcatNode":
        nl = self.left.materialize_unicode(target_unicode)
        nr = self.right.materialize_unicode(target_unicode)
        if nl is self.left and nr is self.right:
            return self
        return ConcatNode(nl, nr)

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
    _size: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_size", 1 + self.left.node_count() + self.right.node_count())

    def is_nullable(self) -> bool:
        return self.left.is_nullable() or self.right.is_nullable()

    def node_count(self) -> int:
        return self._size

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        return self.left.explicit_unicode_chars() | self.right.explicit_unicode_chars()

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "UnionNode":
        nl = self.left.materialize_unicode(target_unicode)
        nr = self.right.materialize_unicode(target_unicode)
        if nl is self.left and nr is self.right:
            return self
        return UnionNode(nl, nr)

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
    _size: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_size", 1 + self.child.node_count())

    def is_nullable(self) -> bool:
        return True

    def node_count(self) -> int:
        return self._size

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        return self.child.explicit_unicode_chars()

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "StarNode":
        nc = self.child.materialize_unicode(target_unicode)
        return self if nc is self.child else StarNode(nc)

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
    _size: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_size", 1 + self.child.node_count())

    def is_nullable(self) -> bool:
        return self.child.is_nullable()

    def node_count(self) -> int:
        return self._size

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        return self.child.explicit_unicode_chars()

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "PlusNode":
        nc = self.child.materialize_unicode(target_unicode)
        return self if nc is self.child else PlusNode(nc)

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
    _size: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_size", 1 + self.child.node_count())

    def is_nullable(self) -> bool:
        return True

    def node_count(self) -> int:
        return self._size

    def explicit_unicode_chars(self) -> FrozenSet[str]:
        return self.child.explicit_unicode_chars()

    def materialize_unicode(self, target_unicode: FrozenSet[str]) -> "OptionalNode":
        nc = self.child.materialize_unicode(target_unicode)
        return self if nc is self.child else OptionalNode(nc)

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
# Shorthand sets & Escapes
# ---------------------------------------------------------------------------

SHORTHAND_CLASSES = {
    "d": frozenset("0123456789"),
    "w": frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"),
    "s": frozenset(" \t\n\r\f\v"),
}

ESCAPE_CHARS = {
    "0": "\0",
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "f": "\f",
    "v": "\v",
    "\\": "\\",
    "|": "|",
    "*": "*",
    "+": "+",
    "?": "?",
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    "{": "{",
    "}": "}",
    "/": "/",
    ".": ".",
    "-": "-",
    "^": "^",
    '"': '"',
    "'": "'",
    " ": " ",
}


def _is_valid_symbol_char(ch: str) -> bool:
    """Return True if `ch` is a valid character in ASCII_SIGMA or Unicode (excluding internal sentinel)."""
    if ch == NON_ASCII:
        return False
    code = ord(ch)
    if 0xD800 <= code <= 0xDFFF:
        return False
    return 0 <= code <= 0x10FFFF


# ---------------------------------------------------------------------------
# Recursive-Descent Regular Expression Parser
# ---------------------------------------------------------------------------


class RegexParser:
    """
    Formal Grammar for Regular Expressions:
        expr   -> concat ('|' concat)*
        concat -> repeat+
        repeat -> atom ('*' | '+' | '?' | '{' m [',' [n]] '}')*
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

    def _guard_ast_size(self, projected_size: int, pos: int) -> None:
        if projected_size > MAX_AST_NODES:
            raise RegexSyntaxError(
                f"Cây cú pháp RE ({projected_size} nút) vượt quá giới hạn an toàn "
                f"MAX_AST_NODES = {MAX_AST_NODES} (chống bom nhân bản AST lồng nhau)",
                pos,
                self.pattern,
            )

    def parse(self, extra_unicode: FrozenSet[str] = frozenset()) -> RegexNode:
        if self.length == 0:
            raise RegexSyntaxError("Biểu thức chính quy không được rỗng", 0, self.pattern)
        node = self._parse_expr()
        if self.pos < self.length:
            raise RegexSyntaxError(
                f"Ký tự dư thừa không hợp lệ '{self.pattern[self.pos]}'",
                self.pos,
                self.pattern,
            )
        self._guard_ast_size(node.node_count(), 0)
        u_all = node.explicit_unicode_chars() | frozenset(
            c for c in extra_unicode if ord(c) >= 128 and c != NON_ASCII
        )
        if u_all:
            node = node.materialize_unicode(u_all)
        return node

    def _parse_expr(self) -> RegexNode:
        left = self._parse_concat()
        while self._peek() == "|":
            bar_pos = self.pos
            self._advance()
            if self._peek() in (None, ")", "|"):
                raise RegexSyntaxError("Thiếu vế phải sau toán tử '|'", bar_pos, self.pattern)
            right = self._parse_concat()
            self._guard_ast_size(1 + left.node_count() + right.node_count(), bar_pos)
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
            cat_pos = self.pos
            rhs = self._parse_repeat()
            self._guard_ast_size(1 + node.node_count() + rhs.node_count(), cat_pos)
            node = ConcatNode(node, rhs)
        return node

    def _parse_repeat(self) -> RegexNode:
        node = self._parse_atom()
        while self._peek() in ("*", "+", "?", "{"):
            ch = self._peek()
            if ch == "{":
                node = self._parse_counted_quantifier(node)
            else:
                op_pos = self.pos
                op = self._advance()
                self._guard_ast_size(1 + node.node_count(), op_pos)
                if op == "*":
                    node = StarNode(node)
                elif op == "+":
                    node = PlusNode(node)
                elif op == "?":
                    node = OptionalNode(node)
        return node

    def _parse_counted_quantifier(self, child: RegexNode) -> RegexNode:
        """
        Parse `{m}`, `{m,}`, or `{m,n}` and expand it into pure AST nodes
        (`EpsilonNode`, `ConcatNode`, `OptionalNode`, `StarNode`) with strict
        O(1) pre-allocation guard against `MAX_AST_NODES`.
        """
        open_pos = self.pos
        self._advance()  # consume '{'
        content_chars: List[str] = []
        while self._peek() is not None and self._peek() != "}":
            content_chars.append(self._advance())

        if self._peek() != "}":
            raise RegexSyntaxError("Thiếu dấu đóng '}' cho bộ định lượng", open_pos, self.pattern)
        self._advance()  # consume '}'

        content = "".join(content_chars)
        if not content:
            raise RegexSyntaxError("Bộ định lượng '{}' rỗng không hợp lệ", open_pos, self.pattern)

        if "," not in content:
            if not content.isdigit() or not content.isascii():
                raise RegexSyntaxError(
                    f"Cú pháp định lượng '{{{content}}}' không hợp lệ (cần số nguyên không âm)",
                    open_pos,
                    self.pattern,
                )
            m = int(content)
            n = m
            unbounded = False
        else:
            parts = content.split(",")
            if len(parts) != 2:
                raise RegexSyntaxError(
                    f"Cú pháp định lượng '{{{content}}}' có quá nhiều dấu phẩy",
                    open_pos,
                    self.pattern,
                )
            m_str, n_str = parts
            if not m_str or not m_str.isdigit() or not m_str.isascii():
                raise RegexSyntaxError(
                    f"Cận dưới trong định lượng '{{{content}}}' không hợp lệ",
                    open_pos,
                    self.pattern,
                )
            m = int(m_str)
            if n_str == "":
                unbounded = True
                n = m
            else:
                if not n_str.isdigit() or not n_str.isascii():
                    raise RegexSyntaxError(
                        f"Cận trên trong định lượng '{{{content}}}' không hợp lệ",
                        open_pos,
                        self.pattern,
                    )
                unbounded = False
                n = int(n_str)
                if m > n:
                    raise RegexSyntaxError(
                        f"Định lượng '{{{content}}}' không hợp lệ: cận dưới m={m} > cận trên n={n}",
                        open_pos,
                        self.pattern,
                    )

        if m > MAX_QUANTIFIER_BOUND or (not unbounded and n > MAX_QUANTIFIER_BOUND):
            raise RegexSyntaxError(
                f"Định lượng '{{{content}}}' vượt quá giới hạn an toàn ({MAX_QUANTIFIER_BOUND})",
                open_pos,
                self.pattern,
            )

        c_size = child.node_count()
        if unbounded:
            if m == 0:
                self._guard_ast_size(1 + c_size, open_pos)
                return StarNode(child)
            projected = (m + 1) * c_size + 1 + m
            self._guard_ast_size(projected, open_pos)
            acc = child
            for _ in range(m - 1):
                acc = ConcatNode(acc, child)
            return ConcatNode(acc, StarNode(child))

        if n == 0:
            return EpsilonNode()

        projected = n * c_size + (n - m) + (n - 1)
        self._guard_ast_size(projected, open_pos)

        factors: List[RegexNode] = []
        for _ in range(m):
            factors.append(child)
        for _ in range(n - m):
            factors.append(OptionalNode(child))

        acc = factors[0]
        for f in factors[1:]:
            acc = ConcatNode(acc, f)
        return acc

    def _read_hex_escape(self, digits: int, esc_pos: int, prefix: str) -> str:
        hex_chars: List[str] = []
        for _ in range(digits):
            c = self._peek()
            if c is None or c not in _HEX_DIGITS:
                raise RegexSyntaxError(
                    f"Chuỗi escape '\\{prefix}' cần đúng {digits} chữ số hệ 16 (0-9a-fA-F)",
                    esc_pos,
                    self.pattern,
                )
            hex_chars.append(self._advance())
        code = int("".join(hex_chars), 16)
        ch = chr(code)
        if not _is_valid_symbol_char(ch):
            raise RegexSyntaxError(
                f"Mã ký tự U+{code:04X} nằm ngoài vùng Unicode hợp lệ",
                esc_pos,
                self.pattern,
            )
        return ch

    def _make_single_char_node(self, ch: str, pos: int) -> CharSetNode:
        if not _is_valid_symbol_char(ch):
            raise RegexSyntaxError(
                f"Ký tự '{ch}' (U+{ord(ch):04X}) không hợp lệ trong bảng chữ cái",
                pos,
                self.pattern,
            )
        own_u = frozenset({ch}) if ord(ch) >= 128 else frozenset()
        fset = frozenset({ch})
        return CharSetNode(chars=fset, label=format_charset(fset, unicode_chars=own_u), own_unicode=own_u)

    def _parse_atom(self) -> RegexNode:
        ch = self._peek()
        if ch is None:
            raise RegexSyntaxError("Kết thúc biểu thức bất ngờ", self.pos, self.pattern)

        if ch in ("*", "+", "?", "|", ")", "{", "}"):
            raise RegexSyntaxError(
                f"Toán tử hoặc ký hiệu '{ch}' không có toán hạng đứng trước",
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
            chars = build_dynamic_sigma() - {"\n"}
            return CharSetNode(chars=chars, label=".", own_unicode=frozenset())

        if ch == "ε":
            self._advance()
            return EpsilonNode()

        if ch == "\\":
            return self._parse_escape_atom()

        char_pos = self.pos
        self._advance()
        return self._make_single_char_node(ch, char_pos)

    def _parse_escape_atom(self) -> RegexNode:
        esc_pos = self.pos
        self._advance()  # consume '\'
        ch = self._peek()
        if ch is None:
            raise RegexSyntaxError(
                "Dấu '\\' ở cuối biểu thức không có ký tự theo sau", esc_pos, self.pattern
            )
        self._advance()

        if ch == "e":
            return EpsilonNode()
        if ch in SHORTHAND_CLASSES:
            fset = SHORTHAND_CLASSES[ch]
            return CharSetNode(chars=fset, label=f"\\{ch}", own_unicode=frozenset())
        if ch == "x":
            val = self._read_hex_escape(2, esc_pos, "x")
            return self._make_single_char_node(val, esc_pos)
        if ch == "u":
            val = self._read_hex_escape(4, esc_pos, "u")
            return self._make_single_char_node(val, esc_pos)
        if ch in ESCAPE_CHARS:
            return self._make_single_char_node(ESCAPE_CHARS[ch], esc_pos)
        # Allow escaping any valid non-alphanumeric ASCII or explicit Unicode character as literal
        if _is_valid_symbol_char(ch) and not (ch.isascii() and ch.isalnum()):
            return self._make_single_char_node(ch, esc_pos)
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
            if nxt == "e":
                raise RegexSyntaxError(
                    "Không thể dùng ε (\\e) bên trong lớp ký tự [...]", esc_pos, self.pattern
                )
            if nxt in SHORTHAND_CLASSES:
                return None, SHORTHAND_CLASSES[nxt]
            if nxt == "x":
                val = self._read_hex_escape(2, esc_pos, "x")
                return val, frozenset({val})
            if nxt == "u":
                val = self._read_hex_escape(4, esc_pos, "u")
                return val, frozenset({val})
            if nxt in ESCAPE_CHARS:
                val = ESCAPE_CHARS[nxt]
                return val, frozenset({val})
            if _is_valid_symbol_char(nxt) and not (nxt.isascii() and nxt.isalnum()):
                return nxt, frozenset({nxt})
            raise RegexSyntaxError(
                f"Chuỗi escape '\\{nxt}' không hợp lệ trong [...]", esc_pos, self.pattern
            )
        item_pos = self.pos
        self._advance()
        if not _is_valid_symbol_char(ch):
            raise RegexSyntaxError(
                f"Ký tự '{ch}' (U+{ord(ch):04X}) trong lớp ký tự không hợp lệ",
                item_pos,
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
            if (
                single_start is not None
                and self._peek() == "-"
                and self.pos + 1 < self.length
                and self.pattern[self.pos + 1] != "]"
            ):
                dash_pos = self.pos
                self._advance()  # consume '-'
                single_end, _ = self._parse_class_item()
                if single_end is None:
                    raise RegexSyntaxError(
                        "Không thể dùng lớp viết tắt (như \\d) làm đầu mút khoảng '-'",
                        dash_pos,
                        self.pattern,
                    )
                lo = ord(single_start)
                hi = ord(single_end)
                if lo > hi:
                    raise RegexSyntaxError(
                        f"Khoảng ký tự không hợp lệ '{single_start}-{single_end}'",
                        dash_pos,
                        self.pattern,
                    )
                if hi - lo > MAX_CHAR_RANGE_SPAN:
                    raise RegexSyntaxError(
                        f"Khoảng ký tự '{single_start}-{single_end}' ({hi - lo + 1} mã) vượt giới hạn {MAX_CHAR_RANGE_SPAN}",
                        dash_pos,
                        self.pattern,
                    )
                for code in range(lo, hi + 1):
                    c = chr(code)
                    if _is_valid_symbol_char(c):
                        chars.add(c)
            else:
                chars.update(item_set)

        if self._peek() != "]":
            raise RegexSyntaxError("Thiếu dấu đóng ']' cho lớp ký tự", start_pos, self.pattern)
        self._advance()  # consume ']'

        own_u = frozenset(c for c in chars if ord(c) >= 128 and c != NON_ASCII)
        if negated:
            final_set = build_dynamic_sigma(own_u) - chars
        else:
            final_set = frozenset(chars)

        if not final_set:
            raise RegexSyntaxError("Lớp ký tự sau khi phủ định là tập rỗng ∅", start_pos, self.pattern)
        raw_label = self.pattern[start_pos : self.pos]
        label = raw_label if len(raw_label) <= 18 else format_charset(final_set, unicode_chars=own_u)
        return CharSetNode(chars=final_set, label=label, own_unicode=own_u)


def parse_regex(pattern: str, extra_unicode: FrozenSet[str] = frozenset()) -> RegexNode:
    """Parse a regular expression string into its AST (optionally lifted over `extra_unicode`)."""
    return RegexParser(pattern).parse(extra_unicode=extra_unicode)


def regex_to_postfix(pattern: str) -> List[str]:
    """Return postfix token list for a regex (for display & educational inspection)."""
    return parse_regex(pattern).to_postfix_tokens()
