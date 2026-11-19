"""
Direct Regular Expression -> DFA Construction (Berry-Sethi / Dragon Book Algorithm 3.36,
matching UEH Formal Languages Chap 3.1 Slides 40-57).

Steps:
1. Augment regex r into r·# (factor / augmented regular expression)
2. Build syntax tree & assign leaf positions 1..n (left to right)
3. Compute nullable(n), firstpos(n), lastpos(n) bottom-up
4. Compute followpos(p) for all leaf positions p
5. Construct DFA directly from D0 = firstpos(root) using followpos transitions
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .models import (
    DFA,
    AcceptInfo,
    compute_alphabet_partition,
)
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


@dataclass
class AnnotatedTreeNode:
    """Syntax tree node annotated with nullable, firstpos, lastpos for visualization."""

    node_id: int
    kind: str  # LEAF, END, EPSILON, CONCAT, UNION, STAR, PLUS, OPTIONAL
    label: str
    position: Optional[int] = None
    chars: Optional[FrozenSet[str]] = None
    nullable: bool = False
    firstpos: FrozenSet[int] = field(default_factory=frozenset)
    lastpos: FrozenSet[int] = field(default_factory=frozenset)
    children: List["AnnotatedTreeNode"] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "position": self.position,
            "nullable": self.nullable,
            "firstpos": sorted(self.firstpos),
            "lastpos": sorted(self.lastpos),
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class DirectDFAResult:
    """Complete output of Direct RE -> DFA algorithm including syntax tree & followpos table."""

    dfa: DFA
    syntax_tree: AnnotatedTreeNode
    leaf_symbols: Dict[int, str]
    end_marker_pos: int
    followpos: Dict[int, List[int]]

    def to_dict(self) -> Dict:
        followpos_table = [
            {
                "position": pos,
                "symbol": self.leaf_symbols[pos],
                "is_end_marker": pos == self.end_marker_pos,
                "followpos": self.followpos.get(pos, []),
            }
            for pos in sorted(self.leaf_symbols.keys())
        ]
        return {
            "syntax_tree": self.syntax_tree.to_dict(),
            "end_marker_pos": self.end_marker_pos,
            "followpos_table": followpos_table,
            "dfa": self.dfa.to_graph_dict(),
            "transition_table": self.dfa.to_transition_table(),
        }


def build_direct_dfa(
    pattern: str,
    token_name: str = "ACCEPT",
    priority: int = 0,
    skip: bool = False,
    category: str = "other",
) -> DirectDFAResult:
    """
    Build a DFA directly from Regular Expression `pattern` without constructing an NFA.
    """
    ast = parse_regex(pattern)

    node_counter = 0
    pos_counter = 0
    leaf_chars: Dict[int, FrozenSet[str]] = {}
    leaf_symbols: Dict[int, str] = {}
    followpos_sets: Dict[int, Set[int]] = {}

    def next_nid() -> int:
        nonlocal node_counter
        nid = node_counter
        node_counter += 1
        return nid

    def next_pos() -> int:
        nonlocal pos_counter
        pos_counter += 1
        followpos_sets[pos_counter] = set()
        return pos_counter

    def annotate(node: RegexNode) -> AnnotatedTreeNode:
        if isinstance(node, EpsilonNode):
            return AnnotatedTreeNode(
                node_id=next_nid(),
                kind="EPSILON",
                label="ε",
                nullable=True,
                firstpos=frozenset(),
                lastpos=frozenset(),
            )

        if isinstance(node, CharSetNode):
            p = next_pos()
            leaf_chars[p] = node.chars
            leaf_symbols[p] = node.label
            return AnnotatedTreeNode(
                node_id=next_nid(),
                kind="LEAF",
                label=node.label,
                position=p,
                chars=node.chars,
                nullable=False,
                firstpos=frozenset({p}),
                lastpos=frozenset({p}),
            )

        if isinstance(node, UnionNode):
            c1 = annotate(node.left)
            c2 = annotate(node.right)
            return AnnotatedTreeNode(
                node_id=next_nid(),
                kind="UNION",
                label="|",
                nullable=c1.nullable or c2.nullable,
                firstpos=c1.firstpos | c2.firstpos,
                lastpos=c1.lastpos | c2.lastpos,
                children=[c1, c2],
            )

        if isinstance(node, ConcatNode):
            c1 = annotate(node.left)
            c2 = annotate(node.right)
            fp = (c1.firstpos | c2.firstpos) if c1.nullable else c1.firstpos
            lp = (c1.lastpos | c2.lastpos) if c2.nullable else c2.lastpos
            for p in c1.lastpos:
                followpos_sets[p].update(c2.firstpos)
            return AnnotatedTreeNode(
                node_id=next_nid(),
                kind="CONCAT",
                label="·",
                nullable=c1.nullable and c2.nullable,
                firstpos=fp,
                lastpos=lp,
                children=[c1, c2],
            )

        if isinstance(node, StarNode):
            c1 = annotate(node.child)
            for p in c1.lastpos:
                followpos_sets[p].update(c1.firstpos)
            return AnnotatedTreeNode(
                node_id=next_nid(),
                kind="STAR",
                label="*",
                nullable=True,
                firstpos=c1.firstpos,
                lastpos=c1.lastpos,
                children=[c1],
            )

        if isinstance(node, PlusNode):
            c1 = annotate(node.child)
            for p in c1.lastpos:
                followpos_sets[p].update(c1.firstpos)
            return AnnotatedTreeNode(
                node_id=next_nid(),
                kind="PLUS",
                label="+",
                nullable=c1.nullable,
                firstpos=c1.firstpos,
                lastpos=c1.lastpos,
                children=[c1],
            )

        if isinstance(node, OptionalNode):
            c1 = annotate(node.child)
            return AnnotatedTreeNode(
                node_id=next_nid(),
                kind="OPTIONAL",
                label="?",
                nullable=True,
                firstpos=c1.firstpos,
                lastpos=c1.lastpos,
                children=[c1],
            )

        raise TypeError(f"Unsupported AST node: {type(node)}")

    body_tree = annotate(ast)

    # Augment with end-marker '#'
    end_pos = next_pos()
    leaf_symbols[end_pos] = "#"
    end_node = AnnotatedTreeNode(
        node_id=next_nid(),
        kind="END",
        label="#",
        position=end_pos,
        nullable=False,
        firstpos=frozenset({end_pos}),
        lastpos=frozenset({end_pos}),
    )

    root_fp = (body_tree.firstpos | end_node.firstpos) if body_tree.nullable else body_tree.firstpos
    root_lp = end_node.lastpos  # end_node is never nullable
    for p in body_tree.lastpos:
        followpos_sets[p].update(end_node.firstpos)

    root_tree = AnnotatedTreeNode(
        node_id=next_nid(),
        kind="CONCAT",
        label="·",
        nullable=False,
        firstpos=root_fp,
        lastpos=root_lp,
        children=[body_tree, end_node],
    )

    # Partition alphabet based on leaf character sets
    char_classes = compute_alphabet_partition(list(leaf_chars.values()))
    representatives = [next(iter(cs)) for cs in char_classes]

    # Map each position p (excluding '#') -> list of class_ids it matches
    pos_to_classes: Dict[int, List[int]] = {}
    for p, cset in leaf_chars.items():
        pos_to_classes[p] = [cid for cid, rep in enumerate(representatives) if rep in cset]

    start_set = root_tree.firstpos
    set_to_id: Dict[FrozenSet[int], int] = {start_set: 0}
    queue: deque[FrozenSet[int]] = deque([start_set])

    transitions: Dict[int, Dict[int, int]] = {}
    accept_states: Dict[int, AcceptInfo] = {}
    state_subsets: Dict[int, List[int]] = {0: sorted(start_set)}
    accept_info = AcceptInfo(
        token_name=token_name,
        priority=priority,
        skip=skip,
        category=category,
    )

    if end_pos in start_set:
        accept_states[0] = accept_info

    while queue:
        cur_set = queue.popleft()
        cur_id = set_to_id[cur_set]
        transitions.setdefault(cur_id, {})

        class_follow: Dict[int, Set[int]] = {}
        for p in cur_set:
            if p == end_pos:
                continue
            for cid in pos_to_classes.get(p, ()):
                class_follow.setdefault(cid, set()).update(followpos_sets[p])

        for cid in sorted(class_follow.keys()):
            nxt_set = frozenset(class_follow[cid])
            if not nxt_set:
                continue
            if nxt_set not in set_to_id:
                new_id = len(set_to_id)
                set_to_id[nxt_set] = new_id
                state_subsets[new_id] = sorted(nxt_set)
                if end_pos in nxt_set:
                    accept_states[new_id] = accept_info
                queue.append(nxt_set)
            transitions[cur_id][cid] = set_to_id[nxt_set]

    dfa = DFA(
        states=set(range(len(set_to_id))),
        start_state=0,
        accept_states=accept_states,
        char_classes=char_classes,
        transitions=transitions,
        state_subsets=state_subsets,
        name=f"Direct-DFA({token_name})",
        pattern=pattern,
    )

    followpos_sorted = {p: sorted(s) for p, s in followpos_sets.items()}
    return DirectDFAResult(
        dfa=dfa,
        syntax_tree=root_tree,
        leaf_symbols=leaf_symbols,
        end_marker_pos=end_pos,
        followpos=followpos_sorted,
    )
