"""
GNFA State Elimination Algorithm: DFA -> Regular Expression (Zero `import re`).

Closes Kleene's Theorem 360° equivalence cycle:
    Regular Expression R_0
      -> Thompson ε-NFA (Theorem 3)
      -> ε-free NFA (Theorem 2)
      -> Subset DFA (Theorem 1) & Direct DFA (r#)
      -> Minimized DFA (Moore & Hopcroft)
      -> GNFA State Elimination -> Synthesized Regular Expression R_syn
      -> Product Automaton Proof: L(R_0) == L(R_syn)!

Follows Hopcroft, Motwani & Ullman (3rd Ed., Section 3.2.2) & Sipser (Theorem 1.54):
1. Prune unreachable and dead states so only productive paths q0 ->* F remain.
2. Construct Generalized NFA G with dedicated START (-1) and ACCEPT (-2) states
   (in-deg(START) = 0, out-deg(ACCEPT) = 0) via epsilon transitions.
3. Eliminate internal states one-by-one using minimum degree-product ordering
   (in_deg * out_deg) and exact Kleene algebraic simplifications:
       R'_{i,j} = R_{i,j} | R_{i,rip} · (R_{rip,rip})* · R_{rip,j}
4. Verify round-trip equivalence L(dfa) == L(R_syn) via Product Automaton BFS.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .models import DFA, charset_to_regex_pattern
from .verifier import check_dfa_equivalence


# ---------------------------------------------------------------------------
# Structured Algebraic Regular Expression Representation for GNFA Edges
# ---------------------------------------------------------------------------


class _REExpr:
    prec: int = 4  # 4=atom, 3=unary(*,+,?), 2=concat, 1=union

    def size(self) -> int:
        return 1

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class _Empty(_REExpr):
    prec: int = 4

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        return "∅"


@dataclass(frozen=True)
class _Eps(_REExpr):
    prec: int = 4

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        return "ε"


@dataclass(frozen=True)
class _Sym(_REExpr):
    chars: FrozenSet[str]
    prec: int = 4

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        return charset_to_regex_pattern(self.chars, unicode_chars=unicode_chars)


@dataclass(frozen=True)
class _Star(_REExpr):
    child: _REExpr
    prec: int = 3

    def size(self) -> int:
        return 1 + self.child.size()

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        s = self.child.to_regex(unicode_chars)
        if self.child.prec < 4:
            return f"({s})*"
        return f"{s}*"


@dataclass(frozen=True)
class _Plus(_REExpr):
    child: _REExpr
    prec: int = 3

    def size(self) -> int:
        return 1 + self.child.size()

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        s = self.child.to_regex(unicode_chars)
        if self.child.prec < 4:
            return f"({s})+"
        return f"{s}+"


@dataclass(frozen=True)
class _Opt(_REExpr):
    child: _REExpr
    prec: int = 3

    def size(self) -> int:
        return 1 + self.child.size()

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        s = self.child.to_regex(unicode_chars)
        if self.child.prec < 4:
            return f"({s})?"
        return f"{s}?"


@dataclass(frozen=True)
class _Concat(_REExpr):
    items: Tuple[_REExpr, ...]
    prec: int = 2

    def size(self) -> int:
        return 1 + sum(it.size() for it in self.items)

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        parts: List[str] = []
        for it in self.items:
            s = it.to_regex(unicode_chars)
            if it.prec < 2:
                parts.append(f"({s})")
            else:
                parts.append(s)
        return "".join(parts)


@dataclass(frozen=True)
class _Union(_REExpr):
    items: Tuple[_REExpr, ...]
    prec: int = 1

    def size(self) -> int:
        return 1 + sum(it.size() for it in self.items)

    def to_regex(self, unicode_chars: FrozenSet[str]) -> str:
        return "|".join(it.to_regex(unicode_chars) for it in self.items)


_EMPTY = _Empty()
_EPS = _Eps()


def _mk_star(expr: _REExpr) -> _REExpr:
    if isinstance(expr, (_Empty, _Eps)):
        return _EPS
    if isinstance(expr, _Star):
        return expr
    if isinstance(expr, (_Plus, _Opt)):
        return _mk_star(expr.child)
    return _Star(expr)


def _mk_opt(expr: _REExpr) -> _REExpr:
    if isinstance(expr, _Empty) or isinstance(expr, _Eps):
        return _EPS
    if isinstance(expr, (_Star, _Opt)):
        return expr
    if isinstance(expr, _Plus):
        return _mk_star(expr.child)
    return _Opt(expr)


def _mk_concat(left: _REExpr, right: _REExpr) -> _REExpr:
    if isinstance(left, _Empty) or isinstance(right, _Empty):
        return _EMPTY
    if isinstance(left, _Eps):
        return right
    if isinstance(right, _Eps):
        return left

    seq: List[_REExpr] = []
    if isinstance(left, _Concat):
        seq.extend(left.items)
    else:
        seq.append(left)
    if isinstance(right, _Concat):
        seq.extend(right.items)
    else:
        seq.append(right)

    # Peephole Kleene contractions: X · X* -> X+  and  X* · X -> X+
    compact: List[_REExpr] = []
    for item in seq:
        if compact:
            prev = compact[-1]
            if isinstance(item, _Star) and prev == item.child:
                compact[-1] = _Plus(prev)
                continue
            if isinstance(prev, _Star) and prev.child == item:
                compact[-1] = _Plus(item)
                continue
        compact.append(item)

    if len(compact) == 1:
        return compact[0]
    return _Concat(tuple(compact))


def _mk_union(left: _REExpr, right: _REExpr) -> _REExpr:
    if isinstance(left, _Empty):
        return right
    if isinstance(right, _Empty):
        return left
    if left == right:
        return left

    raw_terms: List[_REExpr] = []
    for side in (left, right):
        if isinstance(side, _Union):
            raw_terms.extend(side.items)
        else:
            raw_terms.append(side)

    has_eps = False
    merged_chars: Set[str] = set()
    other_terms: List[_REExpr] = []
    seen_others: Set[_REExpr] = set()

    for t in raw_terms:
        if isinstance(t, _Empty):
            continue
        if isinstance(t, _Eps):
            has_eps = True
        elif isinstance(t, (_Star, _Opt)):
            has_eps = True
            if t not in seen_others:
                seen_others.add(t)
                other_terms.append(t)
        elif isinstance(t, _Sym):
            merged_chars.update(t.chars)
        else:
            if t not in seen_others:
                seen_others.add(t)
                other_terms.append(t)

    final_terms: List[_REExpr] = []
    if merged_chars:
        final_terms.append(_Sym(frozenset(merged_chars)))
    final_terms.extend(other_terms)

    if not final_terms:
        return _EPS if has_eps else _EMPTY

    if len(final_terms) == 1:
        only = final_terms[0]
        return _mk_opt(only) if has_eps else only

    if has_eps:
        # Represent (A | B | ε) concisely as (A|B)?
        return _Opt(_Union(tuple(final_terms)))

    return _Union(tuple(final_terms))


@dataclass
class GNFAEliminationResult:
    """Complete result of GNFA State Elimination (DFA -> Regular Expression)."""

    synthesized_regex: str
    is_empty_language: bool
    live_state_count: int
    elimination_steps: List[Dict]
    kleene_equivalent: bool
    visited_pairs: int
    verification_message: str
    elapsed_ms: float

    def to_dict(self) -> Dict:
        return {
            "synthesized_regex": self.synthesized_regex,
            "is_empty_language": self.is_empty_language,
            "live_state_count": self.live_state_count,
            "elimination_steps": self.elimination_steps,
            "kleene_equivalent": self.kleene_equivalent,
            "visited_pairs": self.visited_pairs,
            "verification_message": self.verification_message,
            "elapsed_ms": round(self.elapsed_ms, 4),
        }


def _find_live_states(dfa: DFA) -> Set[int]:
    """Return states that are both reachable from start_state and co-reachable from accept_states."""
    if not dfa.accept_states:
        return set()

    reachable: Set[int] = {dfa.start_state}
    q_fwd: deque[int] = deque([dfa.start_state])
    rev_adj: Dict[int, List[int]] = {}

    while q_fwd:
        u = q_fwd.popleft()
        for v in dfa.transitions.get(u, {}).values():
            rev_adj.setdefault(v, []).append(u)
            if v not in reachable:
                reachable.add(v)
                q_fwd.append(v)

    accepting_reachable = reachable & set(dfa.accept_states.keys())
    if not accepting_reachable:
        return set()

    co_reachable: Set[int] = set(accepting_reachable)
    q_bwd: deque[int] = deque(accepting_reachable)
    while q_bwd:
        v = q_bwd.popleft()
        for u in rev_adj.get(v, ()):
            if u in reachable and u not in co_reachable:
                co_reachable.add(u)
                q_bwd.append(u)

    return reachable & co_reachable


def dfa_to_regex(dfa: DFA, verify_roundtrip: bool = True) -> GNFAEliminationResult:
    """
    Convert any DFA into a strictly equivalent Regular Expression via GNFA State Elimination,
    and optionally prove Kleene 360° equivalence L(dfa) == L(synthesized_regex).
    """
    t0 = time.perf_counter()
    START = -1
    ACCEPT = -2

    live = _find_live_states(dfa)
    if not live or dfa.start_state not in live:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return GNFAEliminationResult(
            synthesized_regex="∅",
            is_empty_language=True,
            live_state_count=0,
            elimination_steps=[],
            kleene_equivalent=True,
            visited_pairs=1,
            verification_message="Ngôn ngữ rỗng L(D) = ∅ (không có trạng thái kết thúc khả đạt).",
            elapsed_ms=elapsed,
        )

    edges: Dict[Tuple[int, int], _REExpr] = {}
    edges[(START, dfa.start_state)] = _EPS
    for f in sorted(live):
        if f in dfa.accept_states:
            edges[(f, ACCEPT)] = _EPS

    for src, dst, fset, _lbl in dfa.compressed_edges():
        if src in live and dst in live and fset:
            edges[(src, dst)] = _mk_union(edges.get((src, dst), _EMPTY), _Sym(fset))

    remaining: Set[int] = set(live)
    steps: List[Dict] = []
    unicode_chars = dfa.unicode_chars

    def state_label(sid: int) -> str:
        if sid == START:
            return "q_start"
        if sid == ACCEPT:
            return "q_accept"
        return f"D{sid}"

    step_idx = 0
    while remaining:
        # Select state minimizing new transition pairs (in_deg * out_deg) & expression complexity
        best_state: Optional[int] = None
        best_score: Optional[Tuple[int, int, int, int]] = None

        for cand in sorted(remaining):
            preds = [u for (u, v) in edges.keys() if v == cand and u != cand]
            succs = [v for (u, v) in edges.keys() if u == cand and v != cand]
            has_loop = 1 if (cand, cand) in edges else 0
            loop_sz = edges[(cand, cand)].size() if has_loop else 0
            in_out_sz = sum(edges[(u, cand)].size() for u in preds) + sum(
                edges[(cand, v)].size() for v in succs
            )
            score = (len(preds) * len(succs), has_loop, loop_sz + in_out_sz, cand)
            if best_score is None or score < best_score:
                best_score = score
                best_state = cand

        assert best_state is not None
        rip = best_state
        remaining.remove(rip)
        step_idx += 1

        loop_expr = edges.pop((rip, rip), _EMPTY)
        loop_star = _mk_star(loop_expr)

        preds_list = sorted(u for (u, v) in list(edges.keys()) if v == rip and u != rip)
        succs_list = sorted(v for (u, v) in list(edges.keys()) if u == rip and v != rip)

        in_exprs = {u: edges.pop((u, rip)) for u in preds_list}
        out_exprs = {v: edges.pop((rip, v)) for v in succs_list}

        updates_trace: List[Dict] = []
        for u in preds_list:
            for v in succs_list:
                if u == ACCEPT or v == START:
                    continue
                bridge = _mk_concat(_mk_concat(in_exprs[u], loop_star), out_exprs[v])
                old_uv = edges.get((u, v), _EMPTY)
                new_uv = _mk_union(old_uv, bridge)
                edges[(u, v)] = new_uv
                if len(updates_trace) < 16:
                    expr_txt = new_uv.to_regex(unicode_chars)
                    updates_trace.append(
                        {
                            "from": state_label(u),
                            "to": state_label(v),
                            "regex": expr_txt if len(expr_txt) <= 120 else expr_txt[:117] + "...",
                        }
                    )

        loop_txt = loop_expr.to_regex(unicode_chars) if not isinstance(loop_expr, _Empty) else "∅"
        steps.append(
            {
                "step": step_idx,
                "eliminated_state": state_label(rip),
                "self_loop": loop_txt if len(loop_txt) <= 80 else loop_txt[:77] + "...",
                "bridge_count": len(preds_list) * len(succs_list),
                "updates": updates_trace,
                "remaining_states": len(remaining),
            }
        )

    final_expr = edges.get((START, ACCEPT), _EMPTY)
    synthesized = final_expr.to_regex(unicode_chars)

    kleene_ok = True
    visited_pairs = 0
    ver_msg = "Bỏ qua kiểm chứng khứ hồi tự động."

    if verify_roundtrip:
        from .dfa_minimizer import minimize_dfa
        from .subset_construction import nfa_to_dfa
        from .thompson import build_token_nfa

        syn_nfa, _ = build_token_nfa(
            synthesized, token_name="GNFA_SYN", extra_unicode=unicode_chars
        )
        syn_sub, _ = nfa_to_dfa(syn_nfa, record_steps=False)
        syn_min = minimize_dfa(syn_sub).minimized_dfa
        eq = check_dfa_equivalence(dfa, syn_min, check_token_names=False)
        kleene_ok = eq.equivalent
        visited_pairs = eq.visited_pairs
        if eq.equivalent:
            ver_msg = (
                f"KHÉP KÍN VÒNG TRÒN ĐỊNH LÝ KLEENE 360°: L(DFA) ≡ L(R_sinh) "
                f"(duyệt {eq.visited_pairs} cặp trạng thái, 0 phản ví dụ)."
            )
        else:
            ver_msg = f"Lệch tương đương Kleene: {eq.message}"

    elapsed = (time.perf_counter() - t0) * 1000.0
    return GNFAEliminationResult(
        synthesized_regex=synthesized,
        is_empty_language=False,
        live_state_count=len(live),
        elimination_steps=steps,
        kleene_equivalent=kleene_ok,
        visited_pairs=visited_pairs,
        verification_message=ver_msg,
        elapsed_ms=elapsed,
    )
