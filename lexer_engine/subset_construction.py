"""
Subset Construction (Powerset Construction): Epsilon-NFA -> DFA.

Implements:
- epsilon-closure(S)
- Move(S, E) over exact character equivalence classes (Alphabet Partitioning)
- BFS exploration from D0 = epsilon-closure({q0})
- Multi-token conflict resolution via Rule Priority (lowest priority value wins)
- Full step-by-step pedagogical construction trace
"""

from __future__ import annotations

from collections import deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .models import (
    DFA,
    NFA,
    AcceptInfo,
    compute_alphabet_partition,
    format_charset,
)


def _resolve_accept(
    nfa_subset: FrozenSet[int], nfa: NFA
) -> Tuple[Optional[AcceptInfo], List[str]]:
    """
    If a DFA state S contains multiple NFA accepting states,
    resolve the conflict by selecting the rule with highest priority (smallest priority integer).
    Returns (winning_accept_info, sorted_list_of_all_matched_token_names).
    """
    matched: List[AcceptInfo] = [
        nfa.accept_states[q] for q in nfa_subset if q in nfa.accept_states
    ]
    if not matched:
        return None, []
    matched.sort(key=lambda info: (info.priority, info.token_name))
    # Deduplicate token names while preserving priority order
    seen: Set[str] = set()
    all_names: List[str] = []
    for info in matched:
        if info.token_name not in seen:
            seen.add(info.token_name)
            all_names.append(info.token_name)
    return matched[0], all_names


def nfa_to_dfa(
    nfa: NFA,
    record_steps: bool = True,
    max_states: int = 5000,
) -> Tuple[DFA, List[Dict]]:
    """
    Convert an epsilon-NFA (single-token or multi-token combined) to an equivalent DFA
    using Subset Construction + Character Equivalence Class Partitioning.

    Returns:
        (dfa, construction_steps)
    """
    char_classes = compute_alphabet_partition(nfa.all_charsets())

    # Precompute epsilon-closure for every single NFA state (big speedup for combined NFAs)
    single_closure: Dict[int, FrozenSet[int]] = {
        q: nfa.epsilon_closure({q}) for q in nfa.states
    }

    # Precompute per-state transitions indexed by char class representative char
    representatives: List[str] = [next(iter(cs)) for cs in char_classes]
    # nfa_class_moves[q][cid] = set of target NFA states
    nfa_class_moves: Dict[int, Dict[int, Set[int]]] = {}
    for q, edges in nfa.transitions.items():
        q_moves: Dict[int, Set[int]] = {}
        for chars, dst, _ in edges:
            if chars is None:
                continue
            for cid, rep in enumerate(representatives):
                if rep in chars:
                    q_moves.setdefault(cid, set()).add(dst)
        if q_moves:
            nfa_class_moves[q] = q_moves

    def closure_of_set(states: Set[int]) -> FrozenSet[int]:
        res: Set[int] = set()
        for q in states:
            res.update(single_closure[q])
        return frozenset(res)

    start_subset = single_closure[nfa.start_state]
    subset_to_id: Dict[FrozenSet[int], int] = {start_subset: 0}
    queue: deque[FrozenSet[int]] = deque([start_subset])

    transitions: Dict[int, Dict[int, int]] = {}
    accept_states: Dict[int, AcceptInfo] = {}
    state_subsets: Dict[int, List[int]] = {0: sorted(start_subset)}
    all_matched_tokens: Dict[int, List[str]] = {}
    steps: List[Dict] = []

    acc0, matched0 = _resolve_accept(start_subset, nfa)
    if acc0 is not None:
        accept_states[0] = acc0
        all_matched_tokens[0] = matched0

    if record_steps:
        steps.append(
            {
                "action": "INIT",
                "dfa_state": 0,
                "nfa_subset": sorted(start_subset),
                "description": f"D0 = ε-closure({{q{nfa.start_state}}}) = {sorted(start_subset)}",
                "accept_token": acc0.token_name if acc0 else None,
            }
        )

    while queue:
        cur_subset = queue.popleft()
        cur_id = subset_to_id[cur_subset]
        transitions.setdefault(cur_id, {})

        # Collect moves grouped by class_id across all NFA states in cur_subset
        class_targets: Dict[int, Set[int]] = {}
        for q in cur_subset:
            q_moves = nfa_class_moves.get(q)
            if not q_moves:
                continue
            for cid, dsts in q_moves.items():
                class_targets.setdefault(cid, set()).update(dsts)

        for cid in sorted(class_targets.keys()):
            moved = class_targets[cid]
            next_subset = closure_of_set(moved)
            if not next_subset:
                continue

            is_new = next_subset not in subset_to_id
            if is_new:
                new_id = len(subset_to_id)
                if new_id >= max_states:
                    raise RuntimeError(
                        f"Số trạng thái DFA vượt giới hạn an toàn ({max_states}). "
                        "Kiểm tra lại biểu thức chính quy có gây bùng nổ tổ hợp không."
                    )
                subset_to_id[next_subset] = new_id
                state_subsets[new_id] = sorted(next_subset)
                acc, matched = _resolve_accept(next_subset, nfa)
                if acc is not None:
                    accept_states[new_id] = acc
                    all_matched_tokens[new_id] = matched
                queue.append(next_subset)

            dst_id = subset_to_id[next_subset]
            transitions[cur_id][cid] = dst_id

            if record_steps and len(steps) < 250:
                lbl = format_charset(char_classes[cid], max_len=14)
                steps.append(
                    {
                        "action": "NEW_STATE" if is_new else "TRANSITION",
                        "from_state": cur_id,
                        "to_state": dst_id,
                        "symbol_label": lbl,
                        "moved": sorted(moved),
                        "nfa_subset": sorted(next_subset),
                        "description": (
                            f"ε-closure(Move(D{cur_id}, {lbl})) = {sorted(next_subset)} "
                            f"→ D{dst_id}" + (" (mới)" if is_new else "")
                        ),
                    }
                )

    dfa = DFA(
        states=set(range(len(subset_to_id))),
        start_state=0,
        accept_states=accept_states,
        char_classes=char_classes,
        transitions=transitions,
        state_subsets=state_subsets,
        all_matched_tokens=all_matched_tokens,
        name=nfa.name.replace("ε-NFA", "DFA"),
        pattern=nfa.pattern,
    )
    return dfa, steps
