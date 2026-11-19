"""
Core formal-language data models for the Automata-based Lexical Analyzer (Topic T13).

Zero external dependencies. Does NOT use Python's `re` module.
Formal definitions follow Hopcroft, Motwani & Ullman (3rd Ed.) and UEH Formal Languages slides:
- Alphabet Sigma (printable ASCII 32..126 + tab/LF/CR)
- Regular Expression AST nodes
- Epsilon-NFA: N = (Q, Sigma, delta, q0, F) with multi-token accept annotations
- DFA: D = (Q, Sigma, delta, q0, F) using exact character equivalence classes (min-terms)
- Token, LexicalError, Execution Trace & Statistics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# Working finite alphabet Sigma:
# - 98 standard ASCII characters: printable ASCII (32..126) + whitespace control chars (\t, \n, \r)
# - NON_ASCII representative class (chr(128)) standing for all UTF-8 / Unicode characters (ord(c) >= 128)
NON_ASCII: str = "\x80"

ASCII_SIGMA_LIST: Tuple[str, ...] = tuple(
    ["\t", "\n", "\r"] + [chr(code) for code in range(32, 127)]
)
ASCII_SIGMA: FrozenSet[str] = frozenset(ASCII_SIGMA_LIST)

SIGMA_LIST: Tuple[str, ...] = ASCII_SIGMA_LIST + (NON_ASCII,)
SIGMA: FrozenSet[str] = frozenset(SIGMA_LIST)

EPSILON: Optional[str] = None  # Symbolic marker for epsilon transitions


def normalize_char(ch: str) -> str:
    """Map any non-ASCII Unicode character (ord >= 128) to the NON_ASCII representative."""
    return NON_ASCII if ord(ch) >= 128 else ch


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
        " ": "␣",
        "\\": "\\\\",
    }
    if ch in special:
        return special[ch]
    if ord(ch) < 32 or ord(ch) == 127:
        return f"\\x{ord(ch):02X}"
    return ch


def escape_char_in_class(ch: str) -> str:
    """Format a character inside [...] notation."""
    if ch == NON_ASCII:
        return "\\u0080+"
    special = {
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "\v": "\\v",
        "\f": "\\f",
        " ": " ",
        "\\": "\\\\",
        "]": "\\]",
        "-": "\\-",
        "^": "\\^",
    }
    if ch in special:
        return special[ch]
    if ord(ch) < 32 or ord(ch) == 127:
        return f"\\x{ord(ch):02X}"
    return ch


def format_charset(chars: FrozenSet[str], max_len: int = 18) -> str:
    """
    Compress a set of characters into a concise, human-readable label.
    Examples:
        {'a'} -> "a"
        {'0'..'9'} -> "[0-9]"
        SIGMA - {'"', '\\n'} -> '[^"\\n]'
    """
    if not chars:
        return "∅"
    if len(chars) == 1:
        ch = next(iter(chars))
        return escape_char_display(ch)
    if chars == SIGMA:
        return "Σ"

    # If the complement inside SIGMA is very small (<= 4 chars), use negated class [^...]
    complement = SIGMA - chars
    if 0 < len(complement) <= 4 and len(chars) > len(complement) + 6:
        ordered_comp = sorted(complement, key=lambda c: ord(c))
        body = "".join(escape_char_in_class(c) for c in ordered_comp)
        return f"[^{body}]"

    # Build contiguous ASCII ranges
    ordered = sorted(chars, key=lambda c: ord(c))
    # Separate control whitespace, printable ASCII, and NON_ASCII for cleaner ranges
    ctrl = [c for c in ordered if ord(c) < 32]
    printable = [c for c in ordered if 32 <= ord(c) < 127]
    non_ascii = [c for c in ordered if ord(c) >= 128]

    parts: List[str] = []
    if ctrl:
        for c in ctrl:
            parts.append(escape_char_in_class(c))

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

    if non_ascii:
        for c in non_ascii:
            parts.append(escape_char_in_class(c))

    label = "[" + "".join(parts) + "]"
    if len(label) > max_len:
        return label[: max_len - 4] + "...]"
    return label


def compute_alphabet_partition(charsets: List[FrozenSet[str]]) -> List[FrozenSet[str]]:
    """
    Partition the alphabet Sigma into minimal disjoint equivalence classes (min-terms)
    induced by all transition character sets `charsets`.

    Mathematical guarantee:
        For every equivalence class E and every transition set C in `charsets`,
        either E is a subset of C or E is disjoint from C.
        Hence all characters in E induce identical transitions in the entire automaton.
    """
    # Only characters that actually appear in at least one charset need to be tracked;
    # characters outside the union of all charsets can never match any transition.
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

    # Deterministic canonical order by smallest ASCII code in each class
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
    Formal Epsilon-NFA: N = (Q, Sigma, delta, q0, F)
    Supports both single-token NFA and combined multi-token NFA.
    """

    states: Set[int]
    start_state: int
    accept_states: Dict[int, AcceptInfo]
    # Adjacency list: state -> list of (Optional[FrozenSet[str]], target_state, label)
    transitions: Dict[int, List[Tuple[Optional[FrozenSet[str]], int, str]]] = field(
        default_factory=dict
    )
    name: str = "NFA"
    pattern: str = ""

    def add_epsilon(self, src: int, dst: int) -> None:
        self.states.add(src)
        self.states.add(dst)
        self.transitions.setdefault(src, []).append((None, dst, "ε"))

    def add_transition(self, src: int, dst: int, chars: FrozenSet[str], label: Optional[str] = None) -> None:
        self.states.add(src)
        self.states.add(dst)
        lbl = label if label is not None else format_charset(chars)
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
        return sum(1 for edges in self.transitions.values() for chars, _, _ in edges if chars is None)

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
        """Compute Move(S, ch) = { p | exists q in S, p in delta(q, ch) }."""
        norm_ch = NON_ASCII if ord(ch) >= 128 else ch
        result: Set[int] = set()
        for q in state_set:
            for chars, nxt, _ in self.transitions.get(q, ()):
                if chars is not None and (ch in chars or norm_ch in chars):
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
            "nodes": nodes,
            "edges": edges,
        }


@dataclass
class DFA:
    """
    Formal Deterministic Finite Automaton: D = (Q, Sigma, delta, q0, F)
    Uses exact character equivalence classes (min-terms) for O(1) lookup and compact tables.
    """

    states: Set[int]
    start_state: int
    accept_states: Dict[int, AcceptInfo]
    char_classes: List[FrozenSet[str]]
    # transitions[state][class_id] = next_state
    transitions: Dict[int, Dict[int, int]] = field(default_factory=dict)
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
        for cid, charset in enumerate(self.char_classes):
            for ch in charset:
                self._char_to_class[ch] = cid

    def step(self, state: int, ch: str) -> Optional[int]:
        """O(1) deterministic transition delta(state, ch). Returns None if dead/undefined."""
        cid = self._char_to_class.get(ch)
        if cid is None and ord(ch) >= 128:
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
            result.append((src, dst, fset, format_charset(fset)))
        return result

    def edge_count(self) -> int:
        return len(self.compressed_edges())

    def to_transition_table(self) -> Dict:
        """Return a structured transition table (states x character classes) for UI & reports."""
        class_labels = [format_charset(cs, max_len=14) for cs in self.char_classes]
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
