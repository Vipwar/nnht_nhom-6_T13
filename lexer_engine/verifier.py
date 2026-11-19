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
