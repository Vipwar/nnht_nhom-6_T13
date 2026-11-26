"""
Core formal-language data models for the Automata-based Lexical Analyzer (Topic T13).

Zero external dependencies. Does NOT use Python's `re` module.
Formal definitions follow Hopcroft, Motwani & Ullman (3rd Ed.) and UEH Formal Languages slides:
- Full 7-bit ASCII Alphabet (0x00..0x7F, all 128 characters including \\f, \\v, \\0, DEL)
  plus Dynamic Unicode Alphabet Partitioning:
      Sigma(U) = ASCII_SIGMA (128) U U_explicit U {NON_ASCII}
  guaranteeing strict Boolean algebra involution ~(~A) == A over Sigma(U)
  and supporting explicit Unicode literals/identifiers (e.g., `nếu`, `€`) without colliding with NON_ASCII.
- Epsilon-NFA: N = (Q, Sigma(U), delta, q0, F) with multi-token accept annotations
- DFA: D = (Q, Sigma(U), delta, q0, F) using exact character equivalence classes (min-terms)
- Token, LexicalError, Execution Trace & Statistics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

# Internal Unicode Noncharacter sentinel (Unicode Standard Section 23.7: U+FDD0..U+FDEF permanently
# reserved for internal engine use). Represents all Unicode code points >= 0x80 NOT in U_explicit.
NON_ASCII: str = "\ufdd0"

# Full 7-bit ASCII alphabet 0x00..0x7F (128 characters, including \0, \t, \n, \v, \f, \r, 0x20..0x7E, 0x7F)
ASCII_SIGMA_LIST: Tuple[str, ...] = tuple(chr(code) for code in range(128))
ASCII_SIGMA: FrozenSet[str] = frozenset(ASCII_SIGMA_LIST)

# Base symbolic alphabet (128 ASCII + 1 NON_ASCII wildcard representative = 129 base symbols)
SIGMA_LIST: Tuple[str, ...] = ASCII_SIGMA_LIST + (NON_ASCII,)
SIGMA: FrozenSet[str] = frozenset(SIGMA_LIST)

EPSILON: Optional[str] = None  # Symbolic marker for epsilon transitions


def build_dynamic_sigma(unicode_chars: FrozenSet[str] = frozenset()) -> FrozenSet[str]:
    """
    Construct the dynamic finite alphabet:
        Sigma(U) = ASCII_SIGMA (0x00..0x7F) U U_explicit U {NON_ASCII}.
    """
    if not unicode_chars:
        return SIGMA
    cleaned = frozenset(c for c in unicode_chars if ord(c) >= 128 and c != NON_ASCII)
    return SIGMA | cleaned


def complement_charset(
    chars: FrozenSet[str],
    unicode_chars: FrozenSet[str] = frozenset(),
) -> FrozenSet[str]:
    """
    Exact Boolean algebra complement ~A = Sigma(U) \\ A.
    Guarantees strict involution: complement_charset(complement_charset(A, U), U) == A
    for every subset A <= Sigma(U).
    """
    sigma_u = build_dynamic_sigma(unicode_chars)
    return sigma_u - chars


def lift_charset_to_unicode(
    chars: FrozenSet[str],
    own_unicode: FrozenSet[str],
    target_unicode: FrozenSet[str],
) -> FrozenSet[str]:
    """
    Lift a character set defined over Sigma(own_unicode) to a larger alphabet Sigma(target_unicode).
    If `NON_ASCII` belongs to `chars` (meaning `chars` accepts general non-ASCII code points outside
    `own_unicode`), then any newly introduced explicit Unicode symbol u in (target_unicode - own_unicode)
    was previously represented by `NON_ASCII` and therefore belongs to the lifted set.
    """
    if NON_ASCII not in chars:
        return chars
    extra = target_unicode - own_unicode
    if not extra:
        return chars
    return chars | frozenset(c for c in extra if ord(c) >= 128 and c != NON_ASCII)


def normalize_char(ch: str, unicode_chars: FrozenSet[str] = frozenset()) -> str:
    """
    Deterministically project any runtime Unicode character `ch` onto Sigma(U):
    - ASCII (0x00..0x7F) -> `ch`
    - Explicit Unicode symbol (`ch in unicode_chars`) -> `ch`
    - Any other non-ASCII character (`ord(ch) >= 128`) -> `NON_ASCII`
    """
    if ord(ch) < 128 or ch == NON_ASCII or ch in unicode_chars:
        return ch
    return NON_ASCII


def escape_char_display(ch: str) -> str:
    """Format a single character for readable transition labels."""
    if ch == NON_ASCII:
        return "UTF-8"
    special = {
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "\v": "\\v",
        "\f": "\\f",
        "\0": "\\0",
        " ": "␣",
        "\\": "\\\\",
    }
    if ch in special:
        return special[ch]
    if ord(ch) < 32 or ord(ch) == 127:
        return f"\\x{ord(ch):02X}"
    return ch


def escape_char_in_class(ch: str) -> str:
    """Format a character inside [...] human-readable display notation."""
    if ch == NON_ASCII:
        return "\\u0080+"
    special = {
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "\v": "\\v",
        "\f": "\\f",
        "\0": "\\0",
        " ": " ",
        "\\": "\\\\",
        "]": "\\]",
        "[": "\\[",
        "-": "\\-",
        "^": "\\^",
    }
    if ch in special:
        return special[ch]
    if ord(ch) < 32 or ord(ch) == 127:
        return f"\\x{ord(ch):02X}"
    return ch


def format_charset(
    chars: FrozenSet[str],
    max_len: int = 18,
    unicode_chars: FrozenSet[str] = frozenset(),
) -> str:
    """
    Compress a set of characters into a concise, human-readable label.
    Examples:
        {'a'} -> "a"
        {'0'..'9'} -> "[0-9]"
        Sigma(U) - {'"', '\\n', '\\r'} -> '[^"\\n\\r]'
    """
    if not chars:
        return "∅"
    if len(chars) == 1:
        ch = next(iter(chars))
        return escape_char_display(ch)

    inferred_u = unicode_chars | frozenset(
        c for c in chars if ord(c) >= 128 and c != NON_ASCII
    )
    sigma_u = build_dynamic_sigma(inferred_u)
    if chars == sigma_u:
        return "Σ"

    # If NON_ASCII is in chars (or the complement inside Sigma(U) is small <= 6 chars),
    # prefer negated class [^...] when cleaner
    complement = sigma_u - chars
    if NON_ASCII in chars and 0 < len(complement) <= 8:
        ordered_comp = sorted(complement, key=ord)
        body = "".join(escape_char_in_class(c) for c in ordered_comp)
        label = f"[^{body}]"
        if len(label) > max_len:
            return label[: max_len - 4] + "...]"
        return label
    if 0 < len(complement) <= 4 and len(chars) > len(complement) + 6:
        ordered_comp = sorted(complement, key=ord)
        body = "".join(escape_char_in_class(c) for c in ordered_comp)
        label = f"[^{body}]"
        if len(label) > max_len:
            return label[: max_len - 4] + "...]"
        return label

    # Build contiguous ranges
    ordered = sorted(chars, key=ord)
    ctrl = [c for c in ordered if ord(c) < 32 or ord(c) == 127]
    printable = [c for c in ordered if 32 <= ord(c) < 127]
    explicit_uni = [c for c in ordered if ord(c) >= 128 and c != NON_ASCII]
    has_non_ascii = NON_ASCII in chars

    parts: List[str] = []
    if ctrl:
        i = 0
        while i < len(ctrl):
            start = i
            while i + 1 < len(ctrl) and ord(ctrl[i + 1]) == ord(ctrl[i]) + 1:
                i += 1
            if i - start >= 3:
                parts.append(f"{escape_char_in_class(ctrl[start])}-{escape_char_in_class(ctrl[i])}")
            else:
                for k in range(start, i + 1):
                    parts.append(escape_char_in_class(ctrl[k]))
            i += 1

    i = 0
    while i < len(printable):
        start = i
        while i + 1 < len(printable) and ord(printable[i + 1]) == ord(printable[i]) + 1:
            i += 1
        end = i
        if end - start >= 2:
            parts.append(
                f"{escape_char_in_class(printable[start])}-{escape_char_in_class(printable[end])}"
            )
        elif end - start == 1:
            parts.append(escape_char_in_class(printable[start]))
            parts.append(escape_char_in_class(printable[end]))
        else:
            parts.append(escape_char_in_class(printable[start]))
        i += 1

    for c in explicit_uni:
        parts.append(escape_char_in_class(c))
    if has_non_ascii:
        parts.append(escape_char_in_class(NON_ASCII))

    label = "[" + "".join(parts) + "]"
    if len(label) > max_len:
        return label[: max_len - 4] + "...]"
    return label


def _escape_regex_atom_char(ch: str) -> str:
    """Format a single concrete character (ch != NON_ASCII) as a 100% parseable Regex atom."""
    if ch == "\n":
        return "\\n"
    if ch == "\t":
        return "\\t"
    if ch == "\r":
        return "\\r"
    if ch == "\f":
        return "\\f"
    if ch == "\v":
        return "\\v"
    if ch == "ε":
        return "\\u03b5"
    if ch in ("\\", "|", "*", "+", "?", "(", ")", "[", "]", "{", "}", ".", "^"):
        return "\\" + ch
    if ord(ch) < 32 or ord(ch) == 127:
        return f"\\x{ord(ch):02x}"
    return ch


def _escape_regex_class_char(ch: str) -> str:
    """Format a single concrete character (ch != NON_ASCII) inside [...] so it is 100% parseable."""
    if ch == "\n":
        return "\\n"
    if ch == "\t":
        return "\\t"
    if ch == "\r":
        return "\\r"
    if ch == "\f":
        return "\\f"
    if ch == "\v":
        return "\\v"
    if ch == "ε":
        return "\\u03b5"
    if ch in ("\\", "]", "[", "-", "^"):
        return "\\" + ch
    if ord(ch) < 32 or ord(ch) == 127:
        return f"\\x{ord(ch):02x}"
    return ch


def _format_exact_class_body(concrete_chars: Iterable[str]) -> str:
    """Compress concrete characters (no NON_ASCII) into an exact, lossless [...] body."""
    ordered = sorted(concrete_chars, key=ord)
    parts: List[str] = []
    i = 0
    n = len(ordered)
    while i < n:
        start = i
        while i + 1 < n and ord(ordered[i + 1]) == ord(ordered[i]) + 1:
            i += 1
        end = i
        if end - start >= 2:
            parts.append(
                f"{_escape_regex_class_char(ordered[start])}-{_escape_regex_class_char(ordered[end])}"
            )
        else:
            for k in range(start, end + 1):
                parts.append(_escape_regex_class_char(ordered[k]))
        i += 1
    return "".join(parts)


def charset_to_regex_pattern(
    chars: FrozenSet[str],
    unicode_chars: FrozenSet[str] = frozenset(),
) -> str:
    """
    Serialize any non-empty character set `chars <= Sigma(unicode_chars)` into a concise,
    100% lossless, valid Regular Expression string parseable by `regex_parser.parse_regex`.
    """
    if not chars:
        return "∅"

    all_u = unicode_chars | frozenset(
        c for c in chars if ord(c) >= 128 and c != NON_ASCII
    )
    sigma_u = build_dynamic_sigma(all_u)

    if chars == sigma_u:
        return "(.|\\n)"
    if chars == sigma_u - {"\n"}:
        return "."

    if len(chars) == 1:
        ch = next(iter(chars))
        if ch == NON_ASCII:
            excl_u = "".join(_escape_regex_class_char(u) for u in sorted(all_u, key=ord))
            return f"[^\\x00-\\x7f{excl_u}]"
        return _escape_regex_atom_char(ch)

    if NON_ASCII in chars:
        # Complement in Sigma(all_u) is guaranteed non-empty and contains zero NON_ASCII!
        comp = sigma_u - chars
        return f"[^{_format_exact_class_body(comp)}]"

    return f"[{_format_exact_class_body(chars)}]"


def compute_alphabet_partition(charsets: List[FrozenSet[str]]) -> List[FrozenSet[str]]:
    """
    Partition the active alphabet into minimal disjoint equivalence classes (min-terms)
    induced by all transition character sets `charsets`.

    Mathematical guarantee:
        For every equivalence class E and every transition set C in `charsets`,
        either E is a subset of C or E is disjoint from C.
        Hence all characters in E induce identical transitions in the entire automaton.
    """
    used_chars: Set[str] = set()
    for cs in charsets:
        used_chars.update(cs)

    if not used_chars:
        return []

    partitions: List[FrozenSet[str]] = [frozenset(used_chars)]
    for cs in charsets:
        if not cs:
            continue
        new_partitions: List[FrozenSet[str]] = []
        for block in partitions:
            inside = block & cs
            outside = block - cs
            if inside and outside:
                new_partitions.append(inside)
                new_partitions.append(outside)
            else:
                new_partitions.append(block)
        partitions = new_partitions

    partitions.sort(key=lambda b: min(ord(c) for c in b))
    return partitions


@dataclass(frozen=True)
class TokenSpec:
    """Specification of one token class defined by a Regular Expression."""

    name: str
    pattern: str
    priority: int = 0
    skip: bool = False
    category: str = "other"
    description: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "pattern": self.pattern,
            "priority": self.priority,
            "skip": self.skip,
            "category": self.category,
            "description": self.description,
        }


@dataclass(frozen=True)
class AcceptInfo:
    """Acceptance metadata attached to accepting states in multi-token automata."""

    token_name: str
    priority: int
    skip: bool = False
    category: str = "other"

    def to_dict(self) -> Dict:
        return {
            "token_name": self.token_name,
            "priority": self.priority,
            "skip": self.skip,
            "category": self.category,
        }


@dataclass
class NFATransition:
    """Directed transition in an epsilon-NFA: from_state --(chars or epsilon)--> to_state."""

    from_state: int
    to_state: int
    chars: Optional[FrozenSet[str]] = None  # None means epsilon transition
    label: str = "ε"

    @property
    def is_epsilon(self) -> bool:
        return self.chars is None


@dataclass
class NFA:
    """
    Formal Epsilon-NFA: N = (Q, Sigma(U), delta, q0, F)
    Supports both single-token NFA and combined multi-token NFA with dynamic Unicode alphabet.
    """

    states: Set[int]
    start_state: int
    accept_states: Dict[int, AcceptInfo]
    # Adjacency list: state -> list of (Optional[FrozenSet[str]], target_state, label)
    transitions: Dict[int, List[Tuple[Optional[FrozenSet[str]], int, str]]] = field(
        default_factory=dict
    )
    unicode_chars: FrozenSet[str] = field(default_factory=frozenset)
    name: str = "NFA"
    pattern: str = ""

    def add_epsilon(self, src: int, dst: int) -> None:
        self.states.add(src)
        self.states.add(dst)
        self.transitions.setdefault(src, []).append((None, dst, "ε"))

    def add_transition(
        self, src: int, dst: int, chars: FrozenSet[str], label: Optional[str] = None
    ) -> None:
        self.states.add(src)
        self.states.add(dst)
        lbl = label if label is not None else format_charset(chars, unicode_chars=self.unicode_chars)
        self.transitions.setdefault(src, []).append((chars, dst, lbl))

    def all_charsets(self) -> List[FrozenSet[str]]:
        sets: List[FrozenSet[str]] = []
        for edges in self.transitions.values():
            for chars, _, _ in edges:
                if chars is not None:
                    sets.append(chars)
        return sets

    def edge_count(self) -> int:
        return sum(len(edges) for edges in self.transitions.values())

    def epsilon_edge_count(self) -> int:
        return sum(
            1 for edges in self.transitions.values() for chars, _, _ in edges if chars is None
        )

    def epsilon_closure(self, state_set: Set[int]) -> FrozenSet[int]:
        """Compute epsilon-closure(S) via iterative DFS stack."""
        closure: Set[int] = set(state_set)
        stack: List[int] = list(state_set)
        while stack:
            cur = stack.pop()
            for chars, nxt, _ in self.transitions.get(cur, ()):
                if chars is None and nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)
        return frozenset(closure)

    def move(self, state_set: FrozenSet[int], ch: str) -> Set[int]:
        """Compute Move(S, ch) = { p | exists q in S, p in delta(q, normalize(ch)) }."""
        sym = normalize_char(ch, self.unicode_chars)
        result: Set[int] = set()
        for q in state_set:
            for chars, nxt, _ in self.transitions.get(q, ()):
                if chars is not None and sym in chars:
                    result.add(nxt)
        return result

    def simulate(self, text: str) -> Tuple[bool, Optional[AcceptInfo], List[Dict]]:
        """
        Simulate epsilon-NFA on a complete string `text` (Algorithm on Slide 39 of Chap 3.1).
        Returns (accepted, winning_accept_info, step_trace).
        """
        current = self.epsilon_closure({self.start_state})
        trace: List[Dict] = [
            {
                "step": 0,
                "char": None,
                "active_states": sorted(current),
            }
        ]
        for idx, ch in enumerate(text):
            moved = self.move(current, ch)
            current = self.epsilon_closure(moved)
            trace.append(
                {
                    "step": idx + 1,
                    "char": ch,
                    "active_states": sorted(current),
                }
            )
            if not current:
                break

        matched = [self.accept_states[q] for q in current if q in self.accept_states]
        if matched:
            best = min(matched, key=lambda info: info.priority)
            return True, best, trace
        return False, None, trace

    def to_graph_dict(self) -> Dict:
        """Serialize NFA into a clean JSON graph structure for web visualization."""
        nodes = []
        for q in sorted(self.states):
            acc = self.accept_states.get(q)
            nodes.append(
                {
                    "id": q,
                    "label": f"q{q}",
                    "is_start": q == self.start_state,
                    "is_accept": acc is not None,
                    "accept_token": acc.token_name if acc else None,
                    "accept_category": acc.category if acc else None,
                }
            )

        edges = []
        for src in sorted(self.transitions.keys()):
            for chars, dst, lbl in self.transitions[src]:
                edges.append(
                    {
                        "from": src,
                        "to": dst,
                        "label": lbl if chars is not None else "ε",
                        "is_epsilon": chars is None,
                    }
                )

        return {
            "kind": "NFA",
            "name": self.name,
            "pattern": self.pattern,
            "state_count": len(self.states),
            "edge_count": len(edges),
            "epsilon_edge_count": self.epsilon_edge_count(),
            "start_state": self.start_state,
            "accept_count": len(self.accept_states),
            "unicode_chars": sorted(self.unicode_chars),
            "nodes": nodes,
            "edges": edges,
        }


@dataclass
class DFA:
    """
    Formal Deterministic Finite Automaton: D = (Q, Sigma(U), delta, q0, F)
    Uses exact character equivalence classes (min-terms) + dynamic Unicode partitioning
    for O(1) lookup and compact tables.
    """

    states: Set[int]
    start_state: int
    accept_states: Dict[int, AcceptInfo]
    char_classes: List[FrozenSet[str]]
    # transitions[state][class_id] = next_state
    transitions: Dict[int, Dict[int, int]] = field(default_factory=dict)
    unicode_chars: FrozenSet[str] = field(default_factory=frozenset)
    # Diagnostic metadata for pedagogical transparency
    state_subsets: Dict[int, List[int]] = field(default_factory=dict)
    all_matched_tokens: Dict[int, List[str]] = field(default_factory=dict)
    merged_from: Dict[int, List[int]] = field(default_factory=dict)
    name: str = "DFA"
    pattern: str = ""
    _char_to_class: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._rebuild_char_index()

    def _rebuild_char_index(self) -> None:
        self._char_to_class = {}
        inferred_u: Set[str] = set(self.unicode_chars)
        for cid, charset in enumerate(self.char_classes):
            for ch in charset:
                self._char_to_class[ch] = cid
                if ord(ch) >= 128 and ch != NON_ASCII:
                    inferred_u.add(ch)
        if inferred_u != self.unicode_chars:
            self.unicode_chars = frozenset(inferred_u)

    def step(self, state: int, ch: str) -> Optional[int]:
        """O(1) deterministic transition delta(state, ch). Returns None if dead/undefined."""
        cid = self._char_to_class.get(ch)
        if cid is None and ord(ch) >= 128 and ch != NON_ASCII and ch not in self.unicode_chars:
            cid = self._char_to_class.get(NON_ASCII)
        if cid is None:
            return None
        return self.transitions.get(state, {}).get(cid)

    def simulate(self, text: str) -> Tuple[bool, Optional[AcceptInfo], List[Dict]]:
        """Simulate DFA on a complete string `text`. Returns (accepted, accept_info, trace)."""
        cur: Optional[int] = self.start_state
        trace: List[Dict] = [
            {
                "step": 0,
                "char": None,
                "state": cur,
                "is_accept": cur in self.accept_states,
                "token": self.accept_states[cur].token_name if cur in self.accept_states else None,
            }
        ]
        for idx, ch in enumerate(text):
            nxt = self.step(cur, ch) if cur is not None else None
            trace.append(
                {
                    "step": idx + 1,
                    "char": ch,
                    "from_state": cur,
                    "state": nxt,
                    "is_accept": nxt in self.accept_states if nxt is not None else False,
                    "token": (
                        self.accept_states[nxt].token_name
                        if nxt is not None and nxt in self.accept_states
                        else None
                    ),
                }
            )
            cur = nxt
            if cur is None:
                return False, None, trace

        if cur is not None and cur in self.accept_states:
            return True, self.accept_states[cur], trace
        return False, None, trace

    def compressed_edges(self) -> List[Tuple[int, int, FrozenSet[str], str]]:
        """
        Group parallel transitions (src -> dst across multiple character classes)
        into single clean edges with combined character sets and concise labels.
        """
        grouped: Dict[Tuple[int, int], Set[str]] = {}
        for src, trans in self.transitions.items():
            for cid, dst in trans.items():
                grouped.setdefault((src, dst), set()).update(self.char_classes[cid])

        result: List[Tuple[int, int, FrozenSet[str], str]] = []
        for (src, dst), char_set in sorted(grouped.items()):
            fset = frozenset(char_set)
            result.append(
                (src, dst, fset, format_charset(fset, unicode_chars=self.unicode_chars))
            )
        return result

    def edge_count(self) -> int:
        return len(self.compressed_edges())

    def to_transition_table(self) -> Dict:
        """Return a structured transition table (states x character classes) for UI & reports."""
        class_labels = [
            format_charset(cs, max_len=14, unicode_chars=self.unicode_chars)
            for cs in self.char_classes
        ]
        rows = []
        for q in sorted(self.states):
            acc = self.accept_states.get(q)
            row_trans = {}
            for cid in range(len(self.char_classes)):
                dst = self.transitions.get(q, {}).get(cid)
                row_trans[str(cid)] = f"D{dst}" if dst is not None else "—"
            rows.append(
                {
                    "state": q,
                    "label": f"D{q}",
                    "is_start": q == self.start_state,
                    "is_accept": acc is not None,
                    "accept_token": acc.token_name if acc else None,
                    "conflicts": self.all_matched_tokens.get(q, []),
                    "subset": self.state_subsets.get(q, []),
                    "merged_from": self.merged_from.get(q, []),
                    "transitions": row_trans,
                }
            )
        return {
            "columns": [
                {"id": str(cid), "label": lbl, "size": len(self.char_classes[cid])}
                for cid, lbl in enumerate(class_labels)
            ],
            "rows": rows,
        }

    def to_graph_dict(self) -> Dict:
        """Serialize DFA into JSON graph format with merged parallel edges."""
        nodes = []
        for q in sorted(self.states):
            acc = self.accept_states.get(q)
            nodes.append(
                {
                    "id": q,
                    "label": f"D{q}",
                    "is_start": q == self.start_state,
                    "is_accept": acc is not None,
                    "accept_token": acc.token_name if acc else None,
                    "accept_category": acc.category if acc else None,
                    "conflicts": self.all_matched_tokens.get(q, []),
                    "subset": self.state_subsets.get(q, []),
                    "merged_from": self.merged_from.get(q, []),
                }
            )

        edges = [
            {
                "from": src,
                "to": dst,
                "label": lbl,
                "char_count": len(fset),
                "is_epsilon": False,
            }
            for src, dst, fset, lbl in self.compressed_edges()
        ]

        return {
            "kind": "DFA",
            "name": self.name,
            "pattern": self.pattern,
            "state_count": len(self.states),
            "edge_count": len(edges),
            "char_class_count": len(self.char_classes),
            "unicode_chars": sorted(self.unicode_chars),
            "start_state": self.start_state,
            "accept_count": len(self.accept_states),
            "nodes": nodes,
            "edges": edges,
        }


@dataclass
class Token:
    """A single lexical token produced by the Automata-based Scanner."""

    token_type: str
    lexeme: str
    line: int
    col: int
    start_pos: int
    end_pos: int
    category: str = "other"
    skipped: bool = False
    accept_state: int = -1
    backtrack_steps: int = 0

    def to_dict(self) -> Dict:
        return {
            "type": self.token_type,
            "lexeme": self.lexeme,
            "line": self.line,
            "col": self.col,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "length": self.end_pos - self.start_pos,
            "category": self.category,
            "skipped": self.skipped,
            "accept_state": self.accept_state,
            "backtrack_steps": self.backtrack_steps,
        }


@dataclass
class LexicalError:
    """A lexical error detected when no valid token prefix matches at current input position."""

    char: str
    line: int
    col: int
    pos: int
    message: str
    attempted_lexeme: str = ""

    @property
    def lexeme(self) -> str:
        return self.char

    @property
    def start_pos(self) -> int:
        return self.pos

    @property
    def end_pos(self) -> int:
        return self.pos + len(self.char)

    def to_dict(self) -> Dict:
        return {
            "char": self.char,
            "lexeme": self.char,
            "line": self.line,
            "col": self.col,
            "pos": self.pos,
            "start_pos": self.pos,
            "end_pos": self.pos + len(self.char),
            "message": self.message,
            "attempted_lexeme": self.attempted_lexeme,
        }


@dataclass
class TokenTrace:
    """Step-by-step DFA execution trace for scanning one token (or one lexical error)."""

    index: int
    kind: str  # "TOKEN" or "ERROR"
    token_type: str
    lexeme: str
    line: int
    col: int
    start_pos: int
    end_pos: int
    skipped: bool
    backtrack_steps: int
    final_accept_state: Optional[int]
    steps: List[Dict]

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "kind": self.kind,
            "token_type": self.token_type,
            "lexeme": self.lexeme,
            "line": self.line,
            "col": self.col,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "skipped": self.skipped,
            "backtrack_steps": self.backtrack_steps,
            "final_accept_state": self.final_accept_state,
            "steps": self.steps,
        }


@dataclass
class ScanResult:
    """Complete result of lexical analysis over an input source text."""

    tokens: List[Token]
    visible_tokens: List[Token]
    errors: List[LexicalError]
    traces: List[TokenTrace]
    elapsed_ms: float
    total_chars: int
    total_transitions: int
    error_recovery_mode: str = "panic_char"
    memoized_cutoffs: int = 0

    def to_dict(self) -> Dict:
        return {
            "tokens": [t.to_dict() for t in self.tokens],
            "visible_tokens": [t.to_dict() for t in self.visible_tokens],
            "errors": [e.to_dict() for e in self.errors],
            "traces": [tr.to_dict() for tr in self.traces],
            "stats": {
                "elapsed_ms": round(self.elapsed_ms, 4),
                "total_chars": self.total_chars,
                "total_tokens_all": len(self.tokens),
                "visible_token_count": len(self.visible_tokens),
                "skipped_token_count": len(self.tokens) - len(self.visible_tokens),
                "error_count": len(self.errors),
                "total_transitions": self.total_transitions,
                "backtrack_events": sum(1 for t in self.tokens if t.backtrack_steps > 0),
                "total_backtrack_chars": sum(t.backtrack_steps for t in self.tokens),
                "error_recovery_mode": self.error_recovery_mode,
                "memoized_cutoffs": self.memoized_cutoffs,
            },
        }
