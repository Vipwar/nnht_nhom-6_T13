"""
Multi-token DFA Minimization via Partition Refinement (Moore / Hopcroft-style,
matching UEH Formal Languages Chap 3.1 Algorithm 3.6 + Lexer multi-token extension).

Key formal property for Lexical Analyzers:
- Standard single-language DFA minimization starts with Pi_0 = { Q \\ F, F }.
- For a multi-token Lexical DFA, accepting states carry distinct token types.
  Therefore Pi_0 partitions F into separate blocks by token type:
      Pi_0 = { Q \\ F } U { F_{t_1}, F_{t_2}, ..., F_{t_k} }
  This preserves exact token classification while achieving the provably minimal
  number of DFA states (Myhill-Nerode theorem generalized to Moore outputs).
- Dead/sink states are eliminated at the final step (matching Slide 58 Step 5).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from .models import DFA, AcceptInfo

DEAD_STATE = -1


@dataclass
class MinimizationResult:
    """Result of DFA minimization with full step-by-step partition refinement trace."""

    minimized_dfa: DFA
    original_state_count: int
    reachable_state_count: int
    minimized_state_count: int
    removed_unreachable: List[int]
    removed_dead_states: List[int]
    partition_history: List[Dict]

    @property
    def reduction_count(self) -> int:
        return self.original_state_count - self.minimized_state_count

    @property
    def reduction_percent(self) -> float:
        if self.original_state_count == 0:
            return 0.0
        return round(100.0 * self.reduction_count / self.original_state_count, 2)

    def to_dict(self) -> Dict:
        return {
            "original_state_count": self.original_state_count,
            "reachable_state_count": self.reachable_state_count,
            "minimized_state_count": self.minimized_state_count,
            "reduction_count": self.reduction_count,
            "reduction_percent": self.reduction_percent,
            "removed_unreachable": self.removed_unreachable,
            "removed_dead_states": self.removed_dead_states,
            "iterations": len(self.partition_history) - 1,
            "partition_history": self.partition_history,
        }


def _find_reachable(dfa: DFA) -> Set[int]:
    reachable: Set[int] = {dfa.start_state}
    queue: deque[int] = deque([dfa.start_state])
    while queue:
        cur = queue.popleft()
        for dst in dfa.transitions.get(cur, {}).values():
            if dst not in reachable:
                reachable.add(dst)
                queue.append(dst)
    return reachable


def _snapshot_partition(
    step: int,
    partition: List[List[int]],
    accept_states: Dict[int, AcceptInfo],
    note: str,
) -> Dict:
    groups = []
    for idx, block in enumerate(partition):
        real_states = [s for s in block if s != DEAD_STATE]
        if not real_states:
            continue
        rep = real_states[0]
        acc = accept_states.get(rep)
        groups.append(
            {
                "group_id": idx,
                "states": [f"D{s}" for s in real_states],
                "state_ids": real_states,
                "token": acc.token_name if acc else None,
            }
        )
    return {
        "iteration": step,
        "group_count": len(groups),
        "note": note,
        "groups": groups,
    }


def minimize_dfa(dfa: DFA) -> MinimizationResult:
    """
    Minimize a single-token or multi-token DFA using Partition Refinement.
    Preserves exact token recognition and removes unreachable & dead states.
    """
    original_count = len(dfa.states)
    reachable = _find_reachable(dfa)
    removed_unreachable = sorted(dfa.states - reachable)

    num_classes = len(dfa.char_classes)

    # Check if we need a virtual DEAD state to make transition function total
    needs_dead = False
    for q in reachable:
        if len(dfa.transitions.get(q, {})) < num_classes:
            needs_dead = True
            break

    all_states: List[int] = sorted(reachable)
    if needs_dead:
        all_states.append(DEAD_STATE)

    # Total transition lookup table
    def delta(state: int, cid: int) -> int:
        if state == DEAD_STATE:
            return DEAD_STATE
        return dfa.transitions.get(state, {}).get(cid, DEAD_STATE)

    # Build initial partition Pi_0:
    # - One block for all non-accepting states (+ DEAD_STATE if present)
    # - One separate block per distinct token type (name, skip, category)
    non_accept: List[int] = []
    accept_buckets: Dict[Tuple[str, bool, str], List[int]] = {}

    for s in all_states:
        if s == DEAD_STATE or s not in dfa.accept_states:
            non_accept.append(s)
        else:
            info = dfa.accept_states[s]
            key = (info.token_name, info.skip, info.category)
            accept_buckets.setdefault(key, []).append(s)

    partition: List[List[int]] = []
    if non_accept:
        partition.append(non_accept)
    for key in sorted(accept_buckets.keys()):
        partition.append(accept_buckets[key])

    history: List[Dict] = [
        _snapshot_partition(
            0,
            partition,
            dfa.accept_states,
            f"Phân hoạch khởi đầu Π₀ (tách Q\\F và {len(accept_buckets)} nhóm trạng thái kết thúc theo loại token)",
        )
    ]

    # Iterative Partition Refinement
    iteration = 0
    while True:
        block_of: Dict[int, int] = {}
        for b_idx, block in enumerate(partition):
            for s in block:
                block_of[s] = b_idx

        new_partition: List[List[int]] = []
        splits_in_round = 0

        for block in partition:
            if len(block) <= 1:
                new_partition.append(block)
                continue

            sig_groups: Dict[Tuple[int, ...], List[int]] = {}
            for s in block:
                sig = tuple(block_of[delta(s, cid)] for cid in range(num_classes))
                sig_groups.setdefault(sig, []).append(s)

            if len(sig_groups) > 1:
                splits_in_round += 1
            for sub_block in sig_groups.values():
                new_partition.append(sub_block)

        if len(new_partition) == len(partition):
            break

        iteration += 1
        partition = new_partition
        real_groups = sum(1 for b in partition if any(s != DEAD_STATE for s in b))
        history.append(
            _snapshot_partition(
                iteration,
                partition,
                dfa.accept_states,
                f"Vòng lặp {iteration}: tách {splits_in_round} nhóm → {real_groups} nhóm",
            )
        )

    # Final mapping state -> block index
    final_block_of: Dict[int, int] = {}
    for b_idx, block in enumerate(partition):
        for s in block:
            final_block_of[s] = b_idx

    # Identify dead block(s): contains DEAD_STATE or non-accepting self-loop sink
    start_block = final_block_of[dfa.start_state]
    dead_blocks: Set[int] = set()
    for b_idx, block in enumerate(partition):
        if b_idx == start_block:
            continue  # Never drop the start state
        if DEAD_STATE in block:
            dead_blocks.add(b_idx)
            continue
        rep = block[0]
        if rep not in dfa.accept_states:
            # Check if every transition stays within this block or goes to DEAD
            is_sink = all(
                final_block_of[delta(rep, cid)] == b_idx or delta(rep, cid) == DEAD_STATE
                for cid in range(num_classes)
            )
            if is_sink:
                dead_blocks.add(b_idx)

    removed_dead_states: List[int] = sorted(
        s for b_idx in dead_blocks for s in partition[b_idx] if s != DEAD_STATE
    )

    # BFS order over surviving blocks starting at start_block for clean canonical numbering 0..M-1
    block_to_new_id: Dict[int, int] = {start_block: 0}
    bfs_q: deque[int] = deque([start_block])
    while bfs_q:
        b_idx = bfs_q.popleft()
        rep = next(s for s in partition[b_idx] if s != DEAD_STATE)
        for cid in range(num_classes):
            dst = delta(rep, cid)
            if dst == DEAD_STATE:
                continue
            dst_block = final_block_of[dst]
            if dst_block in dead_blocks:
                continue
            if dst_block not in block_to_new_id:
                block_to_new_id[dst_block] = len(block_to_new_id)
                bfs_q.append(dst_block)

    # Build minimized DFA
    new_transitions: Dict[int, Dict[int, int]] = {}
    new_accept: Dict[int, AcceptInfo] = {}
    new_merged_from: Dict[int, List[int]] = {}
    new_all_matched: Dict[int, List[str]] = {}

    for b_idx, new_id in block_to_new_id.items():
        real_members = sorted(s for s in partition[b_idx] if s != DEAD_STATE)
        new_merged_from[new_id] = real_members
        rep = real_members[0]

        if rep in dfa.accept_states:
            new_accept[new_id] = dfa.accept_states[rep]
            # Union of matched token names across merged states (preserving priority order)
            merged_conflicts: List[str] = []
            for m in real_members:
                for tok in dfa.all_matched_tokens.get(m, []):
                    if tok not in merged_conflicts:
                        merged_conflicts.append(tok)
            if merged_conflicts:
                new_all_matched[new_id] = merged_conflicts

        trans_row: Dict[int, int] = {}
        for cid in range(num_classes):
            dst = delta(rep, cid)
            if dst == DEAD_STATE:
                continue
            dst_block = final_block_of[dst]
            if dst_block in dead_blocks or dst_block not in block_to_new_id:
                continue
            trans_row[cid] = block_to_new_id[dst_block]
        new_transitions[new_id] = trans_row

    min_dfa = DFA(
        states=set(block_to_new_id.values()),
        start_state=0,
        accept_states=new_accept,
        char_classes=list(dfa.char_classes),
        transitions=new_transitions,
        merged_from=new_merged_from,
        all_matched_tokens=new_all_matched,
        name=f"Minimized {dfa.name}",
        pattern=dfa.pattern,
    )

    return MinimizationResult(
        minimized_dfa=min_dfa,
        original_state_count=original_count,
        reachable_state_count=len(reachable),
        minimized_state_count=len(min_dfa.states),
        removed_unreachable=removed_unreachable,
        removed_dead_states=removed_dead_states,
        partition_history=history,
    )
