"""
Formal Automaton Equivalence Verification Module.

Provides:
1. Product Automaton DFA Equivalence Checker (exact mathematical proof):
   Checks whether two (single-token or multi-token) DFAs A and B recognize the
   exact same language AND assign the exact same token type to every string w in Sigma*.
   If not equivalent, returns the shortest counterexample string w via BFS!
2. Empirical cross-check comparing epsilon-NFA simulation vs Subset DFA vs Minimized DFA
   (and Direct DFA for single-token regexes).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .models import DFA, NFA, compute_alphabet_partition


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


def check_dfa_equivalence(dfa_a: DFA, dfa_b: DFA, check_token_names: bool = True) -> EquivalenceResult:
    """
    Formally prove whether L(dfa_a) == L(dfa_b) (and token classification matches)
    via BFS on the Product Automaton A x B with explicit virtual DEAD state (-1).

    Time complexity: O(|Q_A| * |Q_B| * |JointClasses|) worst-case,
                     typically O(max(|Q_A|, |Q_B|) * |JointClasses|) for equivalent DFAs.
    """
    DEAD = -1

    # Compute joint alphabet partition so every class representative behaves
    # uniformly in BOTH dfa_a and dfa_b.
    all_sets = list(dfa_a.char_classes) + list(dfa_b.char_classes)
    joint_classes = compute_alphabet_partition(all_sets)
    representatives = [next(iter(cs)) for cs in joint_classes]

    def accept_sig(dfa: DFA, state: int) -> Optional[str]:
        if state == DEAD or state not in dfa.accept_states:
            return None
        if check_token_names:
            return dfa.accept_states[state].token_name
        return "ACCEPT"

    start_pair = (dfa_a.start_state, dfa_b.start_state)
    # parent[pair] = (prev_pair, transition_char)
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
            f"TƯƠNG ĐƯƠNG TUYỆT ĐỐI (chứng minh bằng Product Automaton, "
            f"duyệt {len(parent)} cặp trạng thái đạt tới được, 0 phản ví dụ)."
        ),
    )


def verify_nfa_dfa_on_strings(nfa: NFA, dfa: DFA, strings: List[str]) -> Dict:
    """
    Cross-check NFA simulator vs DFA simulator on a list of test strings.
    """
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
       string w in Sigma* such that tau(delta_hat(p, w)) != tau(delta_hat(q, w)).
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

    # 3. Pairwise distinguishability via Reverse BFS Table-Filling with shortest witnesses
    num_classes = len(dfa.char_classes)
    representatives = [next(iter(cs)) for cs in dfa.char_classes]
    all_nodes = real_states + [DEAD]

    def tau(s: int) -> Optional[Tuple[str, bool, str]]:
        if s == DEAD or s not in dfa.accept_states:
            return None
        info = dfa.accept_states[s]
        if check_token_names:
            return (info.token_name, info.skip, info.category)
        return ("ACCEPT", False, "")

    # Build reverse transition table including virtual DEAD state
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
            f"TỐI GIẢN TUYỆT ĐỐI (Myhill-Nerode): Mọi {distinguishable_count}/{total_pairs} cặp trạng thái "
            f"(p, q) đều phân biệt được bởi chuỗi chứng nhân w, 0 cặp tương đương dư thừa."
        )
    else:
        msg = (
            f"CHƯA TỐI GIẢN: còn {len(equivalent_pairs)} cặp trạng thái tương đương chưa gộp, "
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
    L(R1) == L(R2) by compiling both to Minimized DFAs and running Product Automaton BFS.
    If not equivalent, returns the shortest counterexample string w!
    """
    from .dfa_minimizer import minimize_dfa
    from .subset_construction import nfa_to_dfa
    from .thompson import build_token_nfa

    nfa_a, _ = build_token_nfa(pattern_a, "R1")
    sub_a, _ = nfa_to_dfa(nfa_a, record_steps=False)
    min_a = minimize_dfa(sub_a).minimized_dfa

    nfa_b, _ = build_token_nfa(pattern_b, "R2")
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

