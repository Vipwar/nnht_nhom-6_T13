"""
Thompson's Construction: Regular Expression (AST) -> Epsilon-NFA,
plus Multi-token Combined Epsilon-NFA Construction for Lexical Analysis.

Implements the exact inductive rules from Hopcroft-Motwani-Ullman & UEH Chap 3.1:
- Base cases: epsilon, single symbol / character class
- Inductive cases: Union (r|s), Concatenation (rs), Kleene Star (r*),
  Positive Closure (r+), Optional (r?)
- Multi-token union: fresh global start q0 with epsilon edges to each token's NFA,
  preserving per-token priority and metadata on each accepting state.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .models import NFA, AcceptInfo, TokenSpec
from .regex_parser import (
    CharSetNode,
    ConcatNode,
    EpsilonNode,
    OptionalNode,
    PlusNode,
    RegexNode,
    StarNode,
    UnionNode,
    parse_regex,
)


class _ThompsonBuilder:
    """Internal stateful builder preserving Thompson's invariant (in-deg(start)=0, out-deg(end)=0)."""

    def __init__(self, start_id: int = 0) -> None:
        self._next_id = start_id
        self.transitions: Dict[int, List[Tuple[Optional[frozenset], int, str]]] = {}
        self.states: set[int] = set()

    def _new_state(self) -> int:
        sid = self._next_id
        self._next_id += 1
        self.states.add(sid)
        return sid

    def _add_eps(self, src: int, dst: int) -> None:
        self.transitions.setdefault(src, []).append((None, dst, "ε"))

    def _add_char(self, src: int, dst: int, chars: frozenset, label: str) -> None:
        self.transitions.setdefault(src, []).append((chars, dst, label))

    def build_node(self, node: RegexNode) -> Tuple[int, int]:
        if isinstance(node, EpsilonNode):
            s = self._new_state()
            e = self._new_state()
            self._add_eps(s, e)
            return s, e

        if isinstance(node, CharSetNode):
            s = self._new_state()
            e = self._new_state()
            self._add_char(s, e, node.chars, node.label)
            return s, e

        if isinstance(node, ConcatNode):
            l_s, l_e = self.build_node(node.left)
            r_s, r_e = self.build_node(node.right)
            # Invariant guarantees out-degree(l_e) == 0 and in-degree(r_s) == 0,
            # so merging r_s into l_e is exact and eliminates redundant epsilon chains.
            for edge in self.transitions.pop(r_s, []):
                self.transitions.setdefault(l_e, []).append(edge)
            self.states.discard(r_s)
            return l_s, r_e

        if isinstance(node, UnionNode):
            s = self._new_state()
            l_s, l_e = self.build_node(node.left)
            r_s, r_e = self.build_node(node.right)
            e = self._new_state()
            self._add_eps(s, l_s)
            self._add_eps(s, r_s)
            self._add_eps(l_e, e)
            self._add_eps(r_e, e)
            return s, e

        if isinstance(node, StarNode):
            s = self._new_state()
            c_s, c_e = self.build_node(node.child)
            e = self._new_state()
            self._add_eps(s, c_s)
            self._add_eps(s, e)
            self._add_eps(c_e, c_s)
            self._add_eps(c_e, e)
            return s, e

        if isinstance(node, PlusNode):
            s = self._new_state()
            c_s, c_e = self.build_node(node.child)
            e = self._new_state()
            self._add_eps(s, c_s)
            self._add_eps(c_e, c_s)
            self._add_eps(c_e, e)
            return s, e

        if isinstance(node, OptionalNode):
            s = self._new_state()
            c_s, c_e = self.build_node(node.child)
            e = self._new_state()
            self._add_eps(s, c_s)
            self._add_eps(s, e)
            self._add_eps(c_e, e)
            return s, e

        raise TypeError(f"Không hỗ trợ nút AST: {type(node)}")

    def renumber_compact(self, start: int, accept_map: Dict[int, AcceptInfo]) -> Tuple[NFA, Dict[int, int]]:
        """Renumber states cleanly to 0..N-1 in ascending creation order (no gaps)."""
        ordered = sorted(self.states)
        # Ensure start state is always 0
        if start in ordered:
            ordered.remove(start)
            ordered.insert(0, start)
        mapping = {old: new for new, old in enumerate(ordered)}

        new_transitions: Dict[int, List[Tuple[Optional[frozenset], int, str]]] = {}
        for src, edges in self.transitions.items():
            if src not in mapping:
                continue
            new_src = mapping[src]
            new_transitions[new_src] = [
                (chars, mapping[dst], lbl) for chars, dst, lbl in edges if dst in mapping
            ]

        new_accept = {mapping[q]: info for q, info in accept_map.items() if q in mapping}
        nfa = NFA(
            states=set(mapping.values()),
            start_state=mapping[start],
            accept_states=new_accept,
            transitions=new_transitions,
        )
        return nfa, mapping


def build_token_nfa(
    pattern: str,
    token_name: str = "ACCEPT",
    priority: int = 0,
    skip: bool = False,
    category: str = "other",
) -> Tuple[NFA, RegexNode]:
    """Build a single-token epsilon-NFA from a regular expression string."""
    ast = parse_regex(pattern)
    builder = _ThompsonBuilder(start_id=0)
    start, end = builder.build_node(ast)
    accept_info = AcceptInfo(
        token_name=token_name,
        priority=priority,
        skip=skip,
        category=category,
    )
    nfa, _ = builder.renumber_compact(start, {end: accept_info})
    nfa.name = f"ε-NFA({token_name})"
    nfa.pattern = pattern
    return nfa, ast


def build_combined_nfa(specs: List[TokenSpec]) -> Tuple[NFA, List[Dict]]:
    """
    Combine k token specifications R_1, ..., R_k into a single multi-token epsilon-NFA:
        - Global start state q0 = 0
        - For each token spec i, build N(R_i) and add epsilon edge q0 --ε--> start(N(R_i))
        - Tag accept(N(R_i)) with (token_name_i, priority_i, skip_i, category_i)

    Also returns per-token compilation metadata (including nullable warning check).
    """
    if not specs:
        raise ValueError("Danh sách đặc tả token không được rỗng")

    builder = _ThompsonBuilder(start_id=0)
    global_start = builder._new_state()  # state 0
    accept_map: Dict[int, AcceptInfo] = {}
    token_reports: List[Dict] = []

    for idx, spec in enumerate(specs):
        effective_priority = spec.priority if spec.priority is not None else idx
        ast = parse_regex(spec.pattern)
        nullable = ast.is_nullable()

        before_states = len(builder.states)
        sub_start, sub_end = builder.build_node(ast)
        sub_state_count = len(builder.states) - before_states

        builder._add_eps(global_start, sub_start)
        accept_map[sub_end] = AcceptInfo(
            token_name=spec.name,
            priority=effective_priority,
            skip=spec.skip,
            category=spec.category,
        )

        token_reports.append(
            {
                "name": spec.name,
                "pattern": spec.pattern,
                "priority": effective_priority,
                "skip": spec.skip,
                "category": spec.category,
                "nullable": nullable,
                "postfix": " ".join(ast.to_postfix_tokens()),
                "explicit_infix": ast.to_explicit_infix(),
                "nfa_states": sub_state_count,
            }
        )

    combined, _ = builder.renumber_compact(global_start, accept_map)
    combined.name = f"Combined ε-NFA ({len(specs)} tokens)"
    combined.pattern = " | ".join(spec.name for spec in specs)
    return combined, token_reports
