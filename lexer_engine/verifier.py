"""
Formal Automaton Equivalence, Minimality, and Static Intersection Verification Module.

Provides:
1. Product Automaton DFA Equivalence Checker (exact mathematical proof over dynamic Sigma(U)):
   Checks whether two (single-token or multi-token) DFAs A and B recognize the
   exact same language AND assign the exact same token type to every string w in Sigma(U)*.
   If not equivalent, returns the shortest human-readable counterexample string w via BFS!
2. Myhill-Nerode Minimality Verifier (`verify_dfa_is_minimal`):
   Proves pairwise distinguishability for all C(|Q|, 2) state pairs with shortest witnesses.
3. Static Pairwise Language Intersection Matrix Analyzer (`analyze_token_intersections`):
   Computes L(R_i) ∩ L(R_j) across all C(k, 2) token rule pairs via Product Automaton BFS,
   returning shortest witness strings w in L(R_i) ∩ L(R_j) and classifying set-theoretic
   relations (Disjoint, Safe Priority Subset L(R_i) c L(R_j), Partial Overlap, Identical,
   or Critical Superset Shadowing L(R_j) <= L(R_i)).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .models import (
    DFA,
    NFA,
    NON_ASCII,
    TokenSpec,
    compute_alphabet_partition,
    lift_charset_to_unicode,
)


def _pick_concrete_non_ascii(excluded_unicode: FrozenSet[str]) -> str:
    """Pick a clean concrete Unicode character (e.g. 'à') representing NON_ASCII outside `excluded_unicode`."""
    preferred = ("à", "á", "ê", "ô", "ư", "đ", "α", "β", "π")
    for ch in preferred:
        if ch not in excluded_unicode:
            return ch
    code = 0x0100
    while chr(code) in excluded_unicode or code == ord(NON_ASCII):
        code += 1
    return chr(code)


def _pick_readable_rep(charset: FrozenSet[str], joint_unicode: FrozenSet[str]) -> str:
    """
    Choose the most human-readable character from an equivalence class `charset`
    so counterexamples and intersection witnesses prefer letters/digits over control bytes.
    """
    concrete = [c for c in charset if c != NON_ASCII]
    if not concrete:
        return _pick_concrete_non_ascii(joint_unicode)

    # Priority tiers: 0=a-z, 1=0-9, 2=A-Z, 3=printable ASCII, 4=explicit Unicode, 5=whitespace, 6=ctrl
    def _rank(ch: str) -> Tuple[int, int]:
        o = ord(ch)
        if 97 <= o <= 122:
            return (0, o)
        if 48 <= o <= 57:
            return (1, o)
        if 65 <= o <= 90:
            return (2, o)
        if 33 <= o <= 126:
            return (3, o)
        if o >= 128:
            return (4, o)
        if ch in (" ", "\t", "\n", "\r"):
            return (5, o)
        return (6, o)

    return min(concrete, key=_rank)


def _joint_partition_for_dfas(dfa_a: DFA, dfa_b: DFA) -> Tuple[List[FrozenSet[str]], List[str]]:
    """
    Compute the joint min-term alphabet partition and readable representatives for two DFAs,
    properly lifting both onto their shared dynamic Unicode set U_A u U_B.
    """
    joint_u = dfa_a.unicode_chars | dfa_b.unicode_chars
    lifted_a = [
        lift_charset_to_unicode(cs, dfa_a.unicode_chars, joint_u)
        for cs in dfa_a.char_classes
    ]
    lifted_b = [
        lift_charset_to_unicode(cs, dfa_b.unicode_chars, joint_u)
        for cs in dfa_b.char_classes
    ]
    joint_classes = compute_alphabet_partition(lifted_a + lifted_b)
    reps = [_pick_readable_rep(cs, joint_u) for cs in joint_classes]
    return joint_classes, reps


@dataclass
class EquivalenceResult:
    equivalent: bool
    visited_pairs: int
    counterexample: Optional[str] = None
    token_a: Optional[str] = None
    token_b: Optional[str] = None
    message: str = ""

    def to_dict(self) -> Dict:
        return {
            "equivalent": self.equivalent,
            "visited_pairs": self.visited_pairs,
            "counterexample": self.counterexample,
            "token_a": self.token_a,
            "token_b": self.token_b,
            "message": self.message,
        }


def check_dfa_equivalence(
    dfa_a: DFA, dfa_b: DFA, check_token_names: bool = True
) -> EquivalenceResult:
    """
    Formally prove whether L(dfa_a) == L(dfa_b) (and token classification matches)
    via BFS on the Product Automaton A x B with explicit virtual DEAD state (-1).
    """
    DEAD = -1
    _, representatives = _joint_partition_for_dfas(dfa_a, dfa_b)

    def accept_sig(dfa: DFA, state: int) -> Optional[str]:
        if state == DEAD or state not in dfa.accept_states:
            return None
        if check_token_names:
            return dfa.accept_states[state].token_name
        return "ACCEPT"

    start_pair = (dfa_a.start_state, dfa_b.start_state)
    parent: Dict[Tuple[int, int], Optional[Tuple[Tuple[int, int], str]]] = {start_pair: None}
    queue: deque[Tuple[int, int]] = deque([start_pair])

    def reconstruct(pair: Tuple[int, int]) -> str:
        chars: List[str] = []
        cur = pair
        while parent[cur] is not None:
            prev, ch = parent[cur]  # type: ignore[misc]
            chars.append(ch)
            cur = prev
        chars.reverse()
        return "".join(chars)

    while queue:
        qa, qb = queue.popleft()
        sig_a = accept_sig(dfa_a, qa)
        sig_b = accept_sig(dfa_b, qb)
        if sig_a != sig_b:
            cex = reconstruct((qa, qb))
            return EquivalenceResult(
                equivalent=False,
                visited_pairs=len(parent),
                counterexample=cex,
                token_a=sig_a,
                token_b=sig_b,
                message=(
                    f"KHÔNG tương đương! Phản ví dụ ngắn nhất: {cex!r} "
                    f"(A → {sig_a or 'REJECT'}, B → {sig_b or 'REJECT'})"
                ),
            )

        for rep in representatives:
            na = dfa_a.step(qa, rep) if qa != DEAD else None
            nb = dfa_b.step(qb, rep) if qb != DEAD else None
            na_id = na if na is not None else DEAD
            nb_id = nb if nb is not None else DEAD
            if na_id == DEAD and nb_id == DEAD:
                continue
            nxt_pair = (na_id, nb_id)
            if nxt_pair not in parent:
                parent[nxt_pair] = ((qa, qb), rep)
                queue.append(nxt_pair)

    return EquivalenceResult(
        equivalent=True,
        visited_pairs=len(parent),
        counterexample=None,
        message=(
            f"Hai DFA tương đương (kiểm tra bằng Product Automaton, "
            f"duyệt {len(parent)} cặp trạng thái, 0 phản ví dụ)."
        ),
    )


def verify_nfa_dfa_on_strings(nfa: NFA, dfa: DFA, strings: List[str]) -> Dict:
    """Cross-check NFA simulator vs DFA simulator on a list of test strings."""
    mismatches: List[Dict] = []
    for s in strings:
        nfa_ok, nfa_acc, _ = nfa.simulate(s)
        dfa_ok, dfa_acc, _ = dfa.simulate(s)
        nfa_tok = nfa_acc.token_name if nfa_acc else None
        dfa_tok = dfa_acc.token_name if dfa_acc else None
        if nfa_ok != dfa_ok or nfa_tok != dfa_tok:
            mismatches.append(
                {
                    "input": s,
                    "nfa": nfa_tok if nfa_ok else "REJECT",
                    "dfa": dfa_tok if dfa_ok else "REJECT",
                }
            )
    return {
        "total_tested": len(strings),
        "passed": len(strings) - len(mismatches),
        "mismatches": mismatches,
        "all_passed": len(mismatches) == 0,
    }


@dataclass
class MinimalityResult:
    """Formal Myhill-Nerode minimality proof result for a DFA."""

    is_minimal: bool
    state_count: int
    total_pairs: int
    distinguishable_pairs: int
    equivalent_pairs: List[Tuple[int, int]]
    unreachable_states: List[int]
    dead_states: List[int]
    sample_witnesses: List[Dict]
    message: str

    def to_dict(self) -> Dict:
        return {
            "is_minimal": self.is_minimal,
            "state_count": self.state_count,
            "total_pairs": self.total_pairs,
            "distinguishable_pairs": self.distinguishable_pairs,
            "equivalent_pairs": [[p, q] for p, q in self.equivalent_pairs],
            "unreachable_states": self.unreachable_states,
            "dead_states": self.dead_states,
            "sample_witnesses": self.sample_witnesses,
            "message": self.message,
        }

    def __getitem__(self, key: str):
        return self.to_dict()[key]

    def __bool__(self) -> bool:
        return self.is_minimal


def verify_dfa_is_minimal(dfa: DFA, check_token_names: bool = True) -> MinimalityResult:
    """
    Mathematically prove that `dfa` is strictly minimal under the Myhill-Nerode theorem:
    1. Every state q in Q is reachable from q0.
    2. No dead sink state exists in Q (every state q != q0 can reach at least one accepting state).
    3. For every pair of distinct states (p, q) in Q (p < q), there exists a distinguishing
      string w in Sigma(U)* such that tau(delta_hat(p, w)) != tau(delta_hat(q, w)).
    """
    DEAD = -1
    real_states = sorted(dfa.states)
    n_states = len(real_states)
    total_pairs = n_states * (n_states - 1) // 2

    # 1. Reachability from start_state
    reachable: set[int] = {dfa.start_state}
    rq: deque[int] = deque([dfa.start_state])
    while rq:
        u = rq.popleft()
        for v in dfa.transitions.get(u, {}).values():
            if v not in reachable:
                reachable.add(v)
                rq.append(v)
    unreachable = sorted(dfa.states - reachable)

    # 2. Co-reachability (liveness: can reach an accepting state)
    rev_adj: Dict[int, List[int]] = {}
    for u, trans in dfa.transitions.items():
        for v in trans.values():
            rev_adj.setdefault(v, []).append(u)
    live: set[int] = set(dfa.accept_states.keys())
    lq: deque[int] = deque(live)
    while lq:
        u = lq.popleft()
        for prev in rev_adj.get(u, ()):
            if prev not in live:
                live.add(prev)
                lq.append(prev)
    dead_states = sorted(
        s for s in dfa.states if s not in live and s != dfa.start_state
    )

    # 3. Pairwise distinguishability via Reverse BFS Table-Filling with shortest readable witnesses
    num_classes = len(dfa.char_classes)
    representatives = [
        _pick_readable_rep(cs, dfa.unicode_chars) for cs in dfa.char_classes
    ]
    all_nodes = real_states + [DEAD]

    def tau(s: int) -> Optional[Tuple[str, bool, str]]:
        if s == DEAD or s not in dfa.accept_states:
            return None
        info = dfa.accept_states[s]
        if check_token_names:
            return (info.token_name, info.skip, info.category)
        return ("ACCEPT", False, "")

    rev_by_class: List[Dict[int, List[int]]] = [{} for _ in range(num_classes)]
    for s in all_nodes:
        trans = dfa.transitions.get(s, {}) if s != DEAD else {}
        for cid in range(num_classes):
            dst = trans.get(cid, DEAD)
            rev_by_class[cid].setdefault(dst, []).append(s)

    witness: Dict[Tuple[int, int], str] = {}
    bfs_q: deque[Tuple[int, int]] = deque()

    for i in range(len(all_nodes)):
        u = all_nodes[i]
        tu = tau(u)
        for j in range(i + 1, len(all_nodes)):
            v = all_nodes[j]
            tv = tau(v)
            if tu != tv:
                pair = (u, v) if u < v else (v, u)
                witness[pair] = ""
                bfs_q.append(pair)

    while bfs_q:
        u, v = bfs_q.popleft()
        w_uv = witness[(u, v)]
        for cid, rep in enumerate(representatives):
            rev_map = rev_by_class[cid]
            preds_u = rev_map.get(u, ())
            if not preds_u:
                continue
            preds_v = rev_map.get(v, ())
            if not preds_v:
                continue
            for pu in preds_u:
                for pv in preds_v:
                    if pu == pv:
                        continue
                    pair = (pu, pv) if pu < pv else (pv, pu)
                    if pair not in witness:
                        witness[pair] = rep + w_uv
                        bfs_q.append(pair)

    equivalent_pairs: List[Tuple[int, int]] = []
    sample_witnesses: List[Dict] = []

    for i in range(n_states):
        p = real_states[i]
        for j in range(i + 1, n_states):
            q = real_states[j]
            pair = (p, q)
            if pair not in witness:
                equivalent_pairs.append(pair)
            elif len(sample_witnesses) < 8:
                w = witness[pair]
                sample_witnesses.append(
                    {
                        "pair": [f"D{p}", f"D{q}"],
                        "witness": w,
                    }
                )

    distinguishable_count = total_pairs - len(equivalent_pairs)
    is_minimal = (
        len(unreachable) == 0
        and len(dead_states) == 0
        and len(equivalent_pairs) == 0
    )

    if is_minimal:
        msg = (
            f"DFA đã tối giản theo Myhill-Nerode: cả {distinguishable_count}/{total_pairs} cặp trạng thái "
            f"(p, q) đều có chuỗi phân biệt w, không còn cặp tương đương dư thừa."
        )
    else:
        msg = (
            f"Chưa tối giản: còn {len(equivalent_pairs)} cặp trạng thái tương đương chưa gộp, "
            f"{len(unreachable)} trạng thái không đạt tới, {len(dead_states)} trạng thái chết."
        )

    return MinimalityResult(
        is_minimal=is_minimal,
        state_count=n_states,
        total_pairs=total_pairs,
        distinguishable_pairs=distinguishable_count,
        equivalent_pairs=equivalent_pairs,
        unreachable_states=unreachable,
        dead_states=dead_states,
        sample_witnesses=sample_witnesses,
        message=msg,
    )


def compare_regex_equivalence(pattern_a: str, pattern_b: str) -> Dict:
    """
    Formally prove whether two regular expressions R1 and R2 generate the exact same language
    L(R1) == L(R2) over their shared dynamic Unicode alphabet Sigma(U1 u U2).
    """
    from .dfa_minimizer import minimize_dfa
    from .regex_parser import parse_regex
    from .subset_construction import nfa_to_dfa
    from .thompson import build_token_nfa

    ast_a = parse_regex(pattern_a)
    ast_b = parse_regex(pattern_b)
    joint_u = ast_a.explicit_unicode_chars() | ast_b.explicit_unicode_chars()

    nfa_a, _ = build_token_nfa(pattern_a, "R1", extra_unicode=joint_u)
    sub_a, _ = nfa_to_dfa(nfa_a, record_steps=False)
    min_a = minimize_dfa(sub_a).minimized_dfa

    nfa_b, _ = build_token_nfa(pattern_b, "R2", extra_unicode=joint_u)
    sub_b, _ = nfa_to_dfa(nfa_b, record_steps=False)
    min_b = minimize_dfa(sub_b).minimized_dfa

    eq = check_dfa_equivalence(min_a, min_b, check_token_names=False)
    return {
        "pattern_a": pattern_a,
        "pattern_b": pattern_b,
        "equivalent": eq.equivalent,
        "counterexample": eq.counterexample,
        "r1_accepts_counterexample": eq.token_a is not None if not eq.equivalent else None,
        "r2_accepts_counterexample": eq.token_b is not None if not eq.equivalent else None,
        "visited_pairs": eq.visited_pairs,
        "min_dfa_a_states": len(min_a.states),
        "min_dfa_b_states": len(min_b.states),
        "message": eq.message,
    }


# ---------------------------------------------------------------------------
# Static Pairwise Intersection Matrix Analyzer: L(R_i) ∩ L(R_j)
# ---------------------------------------------------------------------------


@dataclass
class PairIntersectionInfo:
    """Result of static Product Automaton analysis on a pair of token rules (R_i, R_j) with i < j."""

    rule_i: str
    rule_j: str
    priority_i: int
    priority_j: int
    pattern_i: str
    pattern_j: str
    intersects: bool
    relation: str  # disjoint | subset_ok | partial_overlap | identical_shadow | superset_shadow
    relation_symbol: str  # ∅ | ⊂ | ∩ | ≡ | ⊃
    shortest_witness: Optional[str]
    witness_only_i: Optional[str]
    witness_only_j: Optional[str]
    winner: Optional[str]
    severity: str  # ok | info | danger
    description: str

    def to_dict(self) -> Dict:
        return {
            "rule_i": self.rule_i,
            "rule_j": self.rule_j,
            "priority_i": self.priority_i,
            "priority_j": self.priority_j,
            "pattern_i": self.pattern_i,
            "pattern_j": self.pattern_j,
            "intersects": self.intersects,
            "relation": self.relation,
            "relation_symbol": self.relation_symbol,
            "shortest_witness": self.shortest_witness,
            "witness_only_i": self.witness_only_i,
            "witness_only_j": self.witness_only_j,
            "winner": self.winner,
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class IntersectionMatrixResult:
    """Complete k x k pairwise intersection matrix and witness report for k token specifications."""

    rule_names: List[str]
    rule_priorities: List[int]
    total_pairs: int
    disjoint_count: int
    overlap_count: int
    safe_priority_count: int
    shadow_conflict_count: int
    overlaps: List[PairIntersectionInfo]
    matrix_cells: List[List[str]]
    elapsed_ms: float

    def to_dict(self) -> Dict:
        return {
            "rule_names": self.rule_names,
            "rule_priorities": self.rule_priorities,
            "total_pairs": self.total_pairs,
            "disjoint_count": self.disjoint_count,
            "overlap_count": self.overlap_count,
            "safe_priority_count": self.safe_priority_count,
            "shadow_conflict_count": self.shadow_conflict_count,
            "overlaps": [ov.to_dict() for ov in self.overlaps],
            "matrix_cells": self.matrix_cells,
            "elapsed_ms": round(self.elapsed_ms, 4),
        }


def check_dfa_intersection(
    dfa_i: DFA,
    dfa_j: DFA,
    rule_i: str = "R_i",
    rule_j: str = "R_j",
    priority_i: int = 1,
    priority_j: int = 2,
    pattern_i: str = "",
    pattern_j: str = "",
) -> PairIntersectionInfo:
    """
    Analyze L(dfa_i) and L(dfa_j) simultaneously via Product Automaton BFS on
    (Q_i u {DEAD}) x (Q_j u {DEAD}) to find:
      - shortest w_both in L(R_i) ∩ L(R_j)
      - shortest w_only_i in L(R_i) \\ L(R_j)
      - shortest w_only_j in L(R_j) \\ L(R_i)
    Assuming rule_i has higher priority than rule_j (priority_i < priority_j).
    """
    DEAD = -1
    _, representatives = _joint_partition_for_dfas(dfa_i, dfa_j)

    start_pair = (dfa_i.start_state, dfa_j.start_state)
    parent: Dict[Tuple[int, int], Optional[Tuple[Tuple[int, int], str]]] = {start_pair: None}
    queue: deque[Tuple[int, int]] = deque([start_pair])

    def reconstruct(pair: Tuple[int, int]) -> str:
        chars: List[str] = []
        cur = pair
        while parent[cur] is not None:
            prev, ch = parent[cur]  # type: ignore[misc]
            chars.append(ch)
            cur = prev
        chars.reverse()
        return "".join(chars)

    w_both: Optional[str] = None
    w_only_i: Optional[str] = None
    w_only_j: Optional[str] = None

    while queue:
        qi, qj = queue.popleft()
        acc_i = qi != DEAD and qi in dfa_i.accept_states
        acc_j = qj != DEAD and qj in dfa_j.accept_states

        if acc_i and acc_j and w_both is None:
            w_both = reconstruct((qi, qj))
        elif acc_i and not acc_j and w_only_i is None:
            w_only_i = reconstruct((qi, qj))
        elif not acc_i and acc_j and w_only_j is None:
            w_only_j = reconstruct((qi, qj))

        if w_both is not None and w_only_i is not None and w_only_j is not None:
            break

        for rep in representatives:
            ni = dfa_i.step(qi, rep) if qi != DEAD else None
            nj = dfa_j.step(qj, rep) if qj != DEAD else None
            ni_id = ni if ni is not None else DEAD
            nj_id = nj if nj is not None else DEAD
            if ni_id == DEAD and nj_id == DEAD:
                continue
            nxt = (ni_id, nj_id)
            if nxt not in parent:
                parent[nxt] = ((qi, qj), rep)
                queue.append(nxt)

    if w_both is None:
        return PairIntersectionInfo(
            rule_i=rule_i,
            rule_j=rule_j,
            priority_i=priority_i,
            priority_j=priority_j,
            pattern_i=pattern_i,
            pattern_j=pattern_j,
            intersects=False,
            relation="disjoint",
            relation_symbol="∅",
            shortest_witness=None,
            witness_only_i=w_only_i,
            witness_only_j=w_only_j,
            winner=None,
            severity="ok",
            description=f"L({rule_i}) ∩ L({rule_j}) = ∅ (Rời nhau hoàn toàn)",
        )

    if w_only_i is None and w_only_j is None:
        return PairIntersectionInfo(
            rule_i=rule_i,
            rule_j=rule_j,
            priority_i=priority_i,
            priority_j=priority_j,
            pattern_i=pattern_i,
            pattern_j=pattern_j,
            intersects=True,
            relation="identical_shadow",
            relation_symbol="≡",
            shortest_witness=w_both,
            witness_only_i=None,
            witness_only_j=None,
            winner=rule_i,
            severity="danger",
            description=(
                f"TRÙNG NGÔN NGỮ L({rule_i}) = L({rule_j}) (chứng nhân {w_both!r}): "
                f"`{rule_j}` bị `{rule_i}` che khuất 100%!"
            ),
        )

    if w_only_j is None and w_only_i is not None:
        return PairIntersectionInfo(
            rule_i=rule_i,
            rule_j=rule_j,
            priority_i=priority_i,
            priority_j=priority_j,
            pattern_i=pattern_i,
            pattern_j=pattern_j,
            intersects=True,
            relation="superset_shadow",
            relation_symbol="⊃",
            shortest_witness=w_both,
            witness_only_i=w_only_i,
            witness_only_j=None,
            winner=rule_i,
            severity="danger",
            description=(
                f"CHE KHUẤT TOÀN PHẦN L({rule_j}) ⊂ L({rule_i}) (chứng nhân {w_both!r}): "
                f"`{rule_i}` (ưu tiên {priority_i}) bao hàm hoàn toàn `{rule_j}` (ưu tiên {priority_j})!"
            ),
        )

    if w_only_i is None and w_only_j is not None:
        return PairIntersectionInfo(
            rule_i=rule_i,
            rule_j=rule_j,
            priority_i=priority_i,
            priority_j=priority_j,
            pattern_i=pattern_i,
            pattern_j=pattern_j,
            intersects=True,
            relation="subset_ok",
            relation_symbol="⊂",
            shortest_witness=w_both,
            witness_only_i=None,
            witness_only_j=w_only_j,
            winner=rule_i,
            severity="info",
            description=(
                f"Tập con hợp lệ L({rule_i}) ⊂ L({rule_j}): trên chứng nhân {w_both!r}, "
                f"`{rule_i}` thắng nhờ ưu tiên {priority_i} < {priority_j}; `{rule_j}` vẫn khớp {w_only_j!r}."
            ),
        )

    return PairIntersectionInfo(
        rule_i=rule_i,
        rule_j=rule_j,
        priority_i=priority_i,
        priority_j=priority_j,
        pattern_i=pattern_i,
        pattern_j=pattern_j,
        intersects=True,
        relation="partial_overlap",
        relation_symbol="∩",
        shortest_witness=w_both,
        witness_only_i=w_only_i,
        witness_only_j=w_only_j,
        winner=rule_i,
        severity="info",
        description=(
            f"Giao nhau một phần L({rule_i}) ∩ L({rule_j}) ≠ ∅: chứng nhân ngắn nhất {w_both!r} "
            f"thuộc về `{rule_i}` (ưu tiên {priority_i} < {priority_j})."
        ),
    )


def analyze_token_intersections(specs: List[TokenSpec]) -> IntersectionMatrixResult:
    """
    Build the complete k x k static pairwise language intersection matrix L(R_i) ∩ L(R_j)
    across all token rules in `specs`, ordered by rule priority.
    """
    from .dfa_minimizer import minimize_dfa_hopcroft
    from .direct_dfa import build_direct_dfa
    from .regex_parser import parse_regex

    t0 = time.perf_counter()
    ordered_specs = sorted(
        enumerate(specs),
        key=lambda item: (item[1].priority if item[1].priority is not None else item[0], item[0]),
    )
    sorted_specs = [sp for _, sp in ordered_specs]
    k = len(sorted_specs)

    raw_asts = [parse_regex(sp.pattern) for sp in sorted_specs]
    global_u = frozenset().union(*(a.explicit_unicode_chars() for a in raw_asts))

    single_dfas: List[DFA] = []
    first_charsets: List[Set[str]] = []
    nullables: List[bool] = []

    for sp in sorted_specs:
        dir_dfa = build_direct_dfa(sp.pattern, token_name=sp.name, extra_unicode=global_u).dfa
        min_d = minimize_dfa_hopcroft(dir_dfa).minimized_dfa
        single_dfas.append(min_d)
        fchars: Set[str] = set()
        for cid in min_d.transitions.get(min_d.start_state, {}).keys():
            fchars.update(min_d.char_classes[cid])
        first_charsets.append(fchars)
        nullables.append(min_d.start_state in min_d.accept_states)

    matrix_cells: List[List[str]] = [["disjoint"] * k for _ in range(k)]
    for i in range(k):
        matrix_cells[i][i] = "self"

    overlaps: List[PairIntersectionInfo] = []
    total_pairs = k * (k - 1) // 2

    for i in range(k):
        sp_i = sorted_specs[i]
        prio_i = sp_i.priority if sp_i.priority is not None else i + 1
        for j in range(i + 1, k):
            # O(1) first-character disjointness filter
            if not (nullables[i] and nullables[j]) and first_charsets[i].isdisjoint(
                first_charsets[j]
            ):
                continue

            sp_j = sorted_specs[j]
            prio_j = sp_j.priority if sp_j.priority is not None else j + 1
            info = check_dfa_intersection(
                single_dfas[i],
                single_dfas[j],
                rule_i=sp_i.name,
                rule_j=sp_j.name,
                priority_i=prio_i,
                priority_j=prio_j,
                pattern_i=sp_i.pattern,
                pattern_j=sp_j.pattern,
            )
            if info.intersects:
                overlaps.append(info)
                matrix_cells[i][j] = info.relation
                # Symmetric transpose marker for lower triangle (j, i)
                if info.relation == "subset_ok":
                    matrix_cells[j][i] = "superset_of_higher"
                elif info.relation == "superset_shadow":
                    matrix_cells[j][i] = "shadowed_by_higher"
                else:
                    matrix_cells[j][i] = info.relation

    shadow_cnt = sum(
        1 for ov in overlaps if ov.relation in ("identical_shadow", "superset_shadow")
    )
    safe_cnt = len(overlaps) - shadow_cnt
    disjoint_cnt = total_pairs - len(overlaps)
    elapsed = (time.perf_counter() - t0) * 1000.0

    return IntersectionMatrixResult(
        rule_names=[sp.name for sp in sorted_specs],
        rule_priorities=[
            sp.priority if sp.priority is not None else idx + 1
            for idx, sp in enumerate(sorted_specs)
        ],
        total_pairs=total_pairs,
        disjoint_count=disjoint_cnt,
        overlap_count=len(overlaps),
        safe_priority_count=safe_cnt,
        shadow_conflict_count=shadow_cnt,
        overlaps=overlaps,
        matrix_cells=matrix_cells,
        elapsed_ms=elapsed,
    )
