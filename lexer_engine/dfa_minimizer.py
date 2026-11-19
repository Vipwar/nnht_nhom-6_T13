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

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Set, Tuple

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
    algorithm: str = "moore"
    elapsed_ms: float = 0.0

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
            "algorithm": self.algorithm,
            "elapsed_ms": round(self.elapsed_ms, 4),
            "original_state_count": self.original_state_count,
            "reachable_state_count": self.reachable_state_count,
            "minimized_state_count": self.minimized_state_count,
            "reduction_count": self.reduction_count,
            "reduction_percent": self.reduction_percent,
            "removed_unreachable": self.removed_unreachable,
            "removed_dead_states": self.removed_dead_states,
            "iterations": max(0, len(self.partition_history) - 1),
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


def _build_minimized_from_partition(
    dfa: DFA,
    partition: List[List[int]],
    delta: Callable[[int, int], int],
    num_classes: int,
) -> Tuple[DFA, List[int]]:
    """Build canonical minimized DFA from final equivalence partition and prune dead sink states."""
    final_block_of: Dict[int, int] = {}
    for b_idx, block in enumerate(partition):
        for s in block:
            final_block_of[s] = b_idx

    start_block = final_block_of[dfa.start_state]
    dead_blocks: Set[int] = set()
    for b_idx, block in enumerate(partition):
        if b_idx == start_block:
            continue
        if DEAD_STATE in block:
            dead_blocks.add(b_idx)
            continue
        rep = block[0]
        if rep not in dfa.accept_states:
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
    return min_dfa, removed_dead_states


def minimize_dfa(dfa: DFA) -> MinimizationResult:
    """
    Minimize a single-token or multi-token DFA using Moore Partition Refinement.
    Preserves exact token recognition and removes unreachable & dead states.
    """
    t0 = time.perf_counter()
    original_count = len(dfa.states)
    reachable = _find_reachable(dfa)
    removed_unreachable = sorted(dfa.states - reachable)

    num_classes = len(dfa.char_classes)

    needs_dead = False
    for q in reachable:
        if len(dfa.transitions.get(q, {})) < num_classes:
            needs_dead = True
            break

    all_states: List[int] = sorted(reachable)
    if needs_dead:
        all_states.append(DEAD_STATE)

    def delta(state: int, cid: int) -> int:
        if state == DEAD_STATE:
            return DEAD_STATE
        return dfa.transitions.get(state, {}).get(cid, DEAD_STATE)

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

    min_dfa, removed_dead_states = _build_minimized_from_partition(
        dfa, partition, delta, num_classes
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return MinimizationResult(
        minimized_dfa=min_dfa,
        original_state_count=original_count,
        reachable_state_count=len(reachable),
        minimized_state_count=len(min_dfa.states),
        removed_unreachable=removed_unreachable,
        removed_dead_states=removed_dead_states,
        partition_history=history,
        algorithm="moore",
        elapsed_ms=elapsed_ms,
    )


def minimize_dfa_hopcroft(dfa: DFA) -> MinimizationResult:
    """
    Minimize a single-token or multi-token DFA using Hopcroft's O(|E| * |Q| log |Q|)
    Worklist & Inverse-Transition Algorithm (Hopcroft 1971).

    Key algorithmic components:
    1. Inverse transition graph inv_delta[cid][dst] = { src | delta(src, cid) == dst }.
    2. Initial multi-token partition P = { Q \\ F } U { F_{t_1}, ..., F_{t_k} }.
    3. Worklist W of splitter pairs (A, cid). When a block Y is split by X = delta^{-1}(A, cid)
       into Y1 = Y ∩ X and Y2 = Y \\ X:
         - If (Y, c) in W, replace it with (Y1, c) and (Y2, c).
         - Else push only the smaller half: (Y1, c) if |Y1| <= |Y2| else (Y2, c).
       This guarantees each state belongs to the smaller half at most log2(|Q|) times!
    """
    t0 = time.perf_counter()
    original_count = len(dfa.states)
    reachable = _find_reachable(dfa)
    removed_unreachable = sorted(dfa.states - reachable)

    num_classes = len(dfa.char_classes)

    needs_dead = False
    for q in reachable:
        if len(dfa.transitions.get(q, {})) < num_classes:
            needs_dead = True
            break

    all_states: List[int] = sorted(reachable)
    if needs_dead:
        all_states.append(DEAD_STATE)

    def delta(state: int, cid: int) -> int:
        if state == DEAD_STATE:
            return DEAD_STATE
        return dfa.transitions.get(state, {}).get(cid, DEAD_STATE)

    # Build inverse transition table: inv_delta[cid][dst] -> list of predecessor states
    inv_delta: List[Dict[int, List[int]]] = [{} for _ in range(num_classes)]
    for s in all_states:
        for cid in range(num_classes):
            dst = delta(s, cid)
            inv_delta[cid].setdefault(dst, []).append(s)

    non_accept: List[int] = []
    accept_buckets: Dict[Tuple[str, bool, str], List[int]] = {}
    for s in all_states:
        if s == DEAD_STATE or s not in dfa.accept_states:
            non_accept.append(s)
        else:
            info = dfa.accept_states[s]
            key = (info.token_name, info.skip, info.category)
            accept_buckets.setdefault(key, []).append(s)

    blocks: List[FrozenSet[int]] = []
    if non_accept:
        blocks.append(frozenset(non_accept))
    for key in sorted(accept_buckets.keys()):
        blocks.append(frozenset(accept_buckets[key]))

    history: List[Dict] = [
        _snapshot_partition(
            0,
            [sorted(b) for b in blocks],
            dfa.accept_states,
            f"Hopcroft Π₀: khởi tạo {len(blocks)} khối và đẩy các khối phân tách vào hàng đợi W",
        )
    ]

    # Initialize worklist W with all blocks (except the single largest block, standard Hopcroft optimization)
    worklist: deque[Tuple[FrozenSet[int], int]] = deque()
    in_worklist: Set[Tuple[FrozenSet[int], int]] = set()

    if len(blocks) > 1 and num_classes > 0:
        largest_idx = max(range(len(blocks)), key=lambda i: len(blocks[i]))
        for idx, blk in enumerate(blocks):
            if idx == largest_idx:
                continue
            for cid in range(num_classes):
                pair = (blk, cid)
                worklist.append(pair)
                in_worklist.add(pair)

    split_steps = 0
    while worklist:
        splitter, cid = worklist.popleft()
        in_worklist.discard((splitter, cid))

        # Predecessor set X = delta^{-1}(splitter, cid)
        inv_map = inv_delta[cid]
        pred_set: Set[int] = set()
        for q in splitter:
            preds = inv_map.get(q)
            if preds:
                pred_set.update(preds)
        if not pred_set:
            continue

        new_blocks: List[FrozenSet[int]] = []
        changed = False
        for y_block in blocks:
            if len(y_block) <= 1:
                new_blocks.append(y_block)
                continue
            y1 = frozenset(y_block & pred_set)
            if not y1 or len(y1) == len(y_block):
                new_blocks.append(y_block)
                continue
            y2 = frozenset(y_block - pred_set)
            changed = True
            new_blocks.append(y1)
            new_blocks.append(y2)

            smaller = y1 if len(y1) <= len(y2) else y2
            for c in range(num_classes):
                old_pair = (y_block, c)
                if old_pair in in_worklist:
                    in_worklist.discard(old_pair)
                    try:
                        worklist.remove(old_pair)
                    except ValueError:
                        pass
                    p1 = (y1, c)
                    p2 = (y2, c)
                    worklist.append(p1)
                    worklist.append(p2)
                    in_worklist.add(p1)
                    in_worklist.add(p2)
                else:
                    ps = (smaller, c)
                    if ps not in in_worklist:
                        worklist.append(ps)
                        in_worklist.add(ps)

        if changed:
            blocks = new_blocks
            split_steps += 1

    final_partition: List[List[int]] = [sorted(b) for b in blocks]
    if split_steps > 0:
        real_groups = sum(1 for b in final_partition if any(s != DEAD_STATE for s in b))
        history.append(
            _snapshot_partition(
                1,
                final_partition,
                dfa.accept_states,
                f"Hopcroft hội tụ sau {split_steps} bước chia tách worklist → {real_groups} nhóm trạng thái tối giản",
            )
        )

    min_dfa, removed_dead_states = _build_minimized_from_partition(
        dfa, final_partition, delta, num_classes
    )
    min_dfa.name = f"Hopcroft Minimized {dfa.name}"
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return MinimizationResult(
        minimized_dfa=min_dfa,
        original_state_count=original_count,
        reachable_state_count=len(reachable),
        minimized_state_count=len(min_dfa.states),
        removed_unreachable=removed_unreachable,
        removed_dead_states=removed_dead_states,
        partition_history=history,
        algorithm="hopcroft",
        elapsed_ms=elapsed_ms,
    )

