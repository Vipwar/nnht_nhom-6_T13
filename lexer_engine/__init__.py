"""
T13: Automata-based Lexical Analyzer Engine
(100% from scratch in Python Standard Library, zero `import re` usage).

Exposes:
- LexicalAnalyzer: Multi-token compilation pipeline
      Token REs -> Dynamic Unicode Alphabet Sigma(U) -> Combined ε-NFA
      -> ε-free NFA (Theorem 2) -> Subset DFA -> Moore & Hopcroft Minimized DFA
      -> Myhill-Nerode Minimality Proof -> Static Intersection Matrix L(R_i) ∩ L(R_j)
      -> Shadowed Rule Detector -> Standalone Table-Driven Codegen -> Reps O(n) Scanner
- inspect_single_regex: Kleene Theorem pipeline for a single RE
      RE -> AST & Postfix -> Thompson ε-NFA -> ε-free NFA -> Subset DFA
      -> Direct DFA (r# / followpos) -> Minimized DFA (Moore & Hopcroft)
      -> GNFA State Elimination (DFA -> Synthesized RE) -> Equivalence & Minimality Checks
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .codegen import generate_standalone_lexer
from .dfa_minimizer import (
    MinimizationResult,
    complement_dfa,
    minimize_dfa,
    minimize_dfa_hopcroft,
)
from .direct_dfa import DirectDFAResult, build_combined_direct_dfa, build_direct_dfa
from .gnfa import GNFAEliminationResult, dfa_to_regex
from .jflap_export import (
    export_dfa_to_jflap,
    export_nfa_to_jflap,
    import_jflap_to_dfa,
    import_jflap_to_nfa,
)
from .models import DFA, NFA, ScanResult, TokenSpec, build_dynamic_sigma, complement_charset
from .presets import PRESETS, SINGLE_REGEX_EXAMPLES
from .regex_parser import MAX_AST_NODES, MAX_QUANTIFIER_BOUND, RegexSyntaxError, parse_regex
from .scanner import scan_source
from .subset_construction import nfa_to_dfa
from .thompson import build_combined_nfa, build_token_nfa, eliminate_epsilon
from .verifier import (
    EquivalenceResult,
    IntersectionMatrixResult,
    MinimalityResult,
    PairIntersectionInfo,
    analyze_token_intersections,
    check_dfa_equivalence,
    check_dfa_intersection,
    compare_regex_equivalence,
    verify_dfa_is_minimal,
    verify_nfa_dfa_on_strings,
)


@dataclass
class LexicalAnalyzer:
    """Compiled Automata-based Lexical Analyzer holding every intermediate artifact."""

    specs: List[TokenSpec]
    combined_nfa: NFA
    eps_free_nfa: NFA
    subset_dfa: DFA
    minimized_dfa: DFA
    minimization: MinimizationResult
    hopcroft_minimization: MinimizationResult
    equivalence: EquivalenceResult
    moore_vs_hopcroft_equivalence: EquivalenceResult
    minimality_proof: MinimalityResult
    intersection_analysis: IntersectionMatrixResult
    token_reports: List[Dict]
    warnings: List[str]
    compile_timings_ms: Dict[str, float]
    shadowed_rules: List[Dict] = field(default_factory=list)

    @classmethod
    def compile(
        cls,
        specs: List[TokenSpec],
        verify_equivalence: bool = True,
        reject_nullable: bool = False,
    ) -> "LexicalAnalyzer":
        """Compile a list of TokenSpec (defined by REs) through the full Automata pipeline."""
        timings: Dict[str, float] = {}

        t0 = time.perf_counter()
        combined_nfa, token_reports = build_combined_nfa(specs)
        timings["thompson_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)

        t_eps = time.perf_counter()
        eps_free_nfa = eliminate_epsilon(combined_nfa)
        timings["eps_eliminate_ms"] = round((time.perf_counter() - t_eps) * 1000.0, 3)

        warnings: List[str] = []
        for rep in token_reports:
            if rep["nullable"]:
                msg = (
                    f"Cảnh báo: Token '{rep['name']}' (RE: {rep['pattern']}) có thể khớp chuỗi rỗng ε. "
                    "Bộ quét sẽ chỉ chấp nhận khớp có độ dài ≥ 1 để tránh vòng lặp vô hạn."
                )
                if reject_nullable:
                    raise RegexSyntaxError(msg)
                warnings.append(msg)

        t1 = time.perf_counter()
        subset_dfa, _ = nfa_to_dfa(combined_nfa, record_steps=False)
        timings["subset_ms"] = round((time.perf_counter() - t1) * 1000.0, 3)

        t2 = time.perf_counter()
        min_res = minimize_dfa(subset_dfa)
        timings["minimize_ms"] = round((time.perf_counter() - t2) * 1000.0, 3)

        t_hop = time.perf_counter()
        hopcroft_res = minimize_dfa_hopcroft(subset_dfa)
        timings["hopcroft_ms"] = round((time.perf_counter() - t_hop) * 1000.0, 3)

        t_inter = time.perf_counter()
        intersection_res = analyze_token_intersections(specs)
        timings["intersection_ms"] = round((time.perf_counter() - t_inter) * 1000.0, 3)

        # Detect shadowed / dead token rules (rules that never win at any reachable accepting state)
        winning_tokens = {
            info.token_name for info in min_res.minimized_dfa.accept_states.values()
        }
        shadowed_rules: List[Dict] = []
        for rep in token_reports:
            tname = rep["name"]
            if tname not in winning_tokens:
                shadowers: List[str] = []
                for q, matched_list in sorted(subset_dfa.all_matched_tokens.items()):
                    if tname in matched_list and q in subset_dfa.accept_states:
                        winner = subset_dfa.accept_states[q].token_name
                        if winner != tname and winner not in shadowers:
                            shadowers.append(winner)
                if not shadowers:
                    for ov in intersection_res.overlaps:
                        if ov.rule_j == tname and ov.rule_i not in shadowers:
                            shadowers.append(ov.rule_i)
                by_str = ", ".join(shadowers) if shadowers else "quy tắc ưu tiên cao hơn"
                warn_msg = (
                    f"Cảnh báo: Quy tắc '{tname}' bị che khuất hoàn toàn bởi quy tắc ưu tiên cao hơn "
                    f"({by_str}) và không bao giờ được khớp."
                )
                warnings.append(warn_msg)
                rep["shadowed"] = True
                rep["shadowed_by"] = shadowers
                shadowed_rules.append(
                    {
                        "token_name": tname,
                        "pattern": rep["pattern"],
                        "priority": rep["priority"],
                        "shadowed_by": shadowers,
                        "message": warn_msg,
                    }
                )
            else:
                rep["shadowed"] = False
                rep["shadowed_by"] = []

        t3 = time.perf_counter()
        if verify_equivalence:
            eq_res = check_dfa_equivalence(
                subset_dfa, min_res.minimized_dfa, check_token_names=True
            )
            eq_moore_hop = check_dfa_equivalence(
                min_res.minimized_dfa, hopcroft_res.minimized_dfa, check_token_names=True
            )
            min_proof = verify_dfa_is_minimal(min_res.minimized_dfa, check_token_names=True)
        else:
            eq_res = EquivalenceResult(True, 0, None, message="Bỏ qua kiểm chứng tự động.")
            eq_moore_hop = EquivalenceResult(True, 0, None, message="Bỏ qua kiểm chứng tự động.")
            min_proof = MinimalityResult(
                is_minimal=True,
                state_count=len(min_res.minimized_dfa.states),
                total_pairs=0,
                distinguishable_pairs=0,
                equivalent_pairs=[],
                unreachable_states=[],
                dead_states=[],
                sample_witnesses=[],
                message="Bỏ qua kiểm chứng tự động.",
            )
        timings["verify_ms"] = round((time.perf_counter() - t3) * 1000.0, 3)
        timings["total_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)

        return cls(
            specs=list(specs),
            combined_nfa=combined_nfa,
            eps_free_nfa=eps_free_nfa,
            subset_dfa=subset_dfa,
            minimized_dfa=min_res.minimized_dfa,
            minimization=min_res,
            hopcroft_minimization=hopcroft_res,
            equivalence=eq_res,
            moore_vs_hopcroft_equivalence=eq_moore_hop,
            minimality_proof=min_proof,
            intersection_analysis=intersection_res,
            token_reports=token_reports,
            warnings=warnings,
            compile_timings_ms=timings,
            shadowed_rules=shadowed_rules,
        )

    @classmethod
    def from_preset(cls, preset_id: str) -> "LexicalAnalyzer":
        if preset_id not in PRESETS:
            raise KeyError(f"Không tìm thấy preset '{preset_id}'")
        return cls.compile(PRESETS[preset_id]["specs"])

    def scan(
        self,
        source: str,
        use_minimized: bool = True,
        record_traces: bool = True,
        error_recovery: str = "panic_char",
    ) -> ScanResult:
        """Scan input source code using either the Minimized DFA (default) or Subset DFA."""
        target_dfa = self.minimized_dfa if use_minimized else self.subset_dfa
        return scan_source(
            source,
            target_dfa,
            record_traces=record_traces,
            error_recovery=error_recovery,
        )

    def generate_standalone_code(
        self, class_name: str = "GeneratedLexer", preset_name: str = "custom"
    ) -> str:
        """Generate a standalone zero-dependency table-driven Python lexer source file."""
        return generate_standalone_lexer(self, class_name=class_name, preset_name=preset_name)

    def summary_dict(self) -> Dict:
        conflict_states = [
            {
                "state": f"D{q}",
                "winner": self.minimized_dfa.accept_states[q].token_name,
                "all_matched": toks,
            }
            for q, toks in sorted(self.minimized_dfa.all_matched_tokens.items())
            if len(toks) > 1
        ]
        return {
            "token_count": len(self.specs),
            "warnings": self.warnings,
            "shadowed_rules": self.shadowed_rules,
            "timings_ms": self.compile_timings_ms,
            "nfa_states": len(self.combined_nfa.states),
            "nfa_edges": self.combined_nfa.edge_count(),
            "nfa_epsilon_edges": self.combined_nfa.epsilon_edge_count(),
            "eps_free_nfa_states": len(self.eps_free_nfa.states),
            "eps_free_nfa_edges": self.eps_free_nfa.edge_count(),
            "subset_dfa_states": len(self.subset_dfa.states),
            "subset_dfa_edges": self.subset_dfa.edge_count(),
            "minimized_dfa_states": len(self.minimized_dfa.states),
            "minimized_dfa_edges": self.minimized_dfa.edge_count(),
            "hopcroft_dfa_states": len(self.hopcroft_minimization.minimized_dfa.states),
            "char_class_count": len(self.minimized_dfa.char_classes),
            "unicode_char_count": len(self.minimized_dfa.unicode_chars),
            "unicode_chars": sorted(self.minimized_dfa.unicode_chars),
            "state_reduction_count": self.minimization.reduction_count,
            "state_reduction_percent": self.minimization.reduction_percent,
            "equivalence": self.equivalence.to_dict(),
            "moore_vs_hopcroft": self.moore_vs_hopcroft_equivalence.to_dict(),
            "minimality": self.minimality_proof.to_dict(),
            "intersection_summary": {
                "total_pairs": self.intersection_analysis.total_pairs,
                "disjoint_count": self.intersection_analysis.disjoint_count,
                "overlap_count": self.intersection_analysis.overlap_count,
                "safe_priority_count": self.intersection_analysis.safe_priority_count,
                "shadow_conflict_count": self.intersection_analysis.shadow_conflict_count,
            },
            "priority_conflicts_resolved": conflict_states,
            "token_reports": self.token_reports,
        }


def inspect_single_regex(
    pattern: str,
    token_name: str = "TOKEN",
    test_strings: Optional[List[str]] = None,
) -> Dict:
    """
    Run the complete 360° Kleene Theorem formal-languages pipeline on a SINGLE regular expression:
      Path A: RE -> AST/Postfix -> Thompson ε-NFA -> ε-free NFA (Theorem 2)
                 -> Subset DFA -> Minimized DFA (Moore & Hopcroft)
      Path B: RE -> Augmented Syntax Tree (r#) -> nullable/firstpos/lastpos/followpos -> Direct DFA
      Path C: Minimized DFA -> GNFA State Elimination -> Synthesized RE (R_syn)
    And formally verify Subset DFA ≡ Direct DFA ≡ Moore Min-DFA ≡ Hopcroft Min-DFA ≡ L(R_syn)
    plus Myhill-Nerode Minimality!
    """
    ast = parse_regex(pattern)
    nfa, _ = build_token_nfa(pattern, token_name=token_name)
    eps_free_nfa = eliminate_epsilon(nfa)
    subset_dfa, subset_steps = nfa_to_dfa(nfa, record_steps=True)
    min_res = minimize_dfa(subset_dfa)
    hopcroft_res = minimize_dfa_hopcroft(subset_dfa)
    direct_res: DirectDFAResult = build_direct_dfa(pattern, token_name=token_name)
    gnfa_res: GNFAEliminationResult = dfa_to_regex(min_res.minimized_dfa, verify_roundtrip=True)

    eq_subset_min = check_dfa_equivalence(subset_dfa, min_res.minimized_dfa, check_token_names=False)
    eq_subset_direct = check_dfa_equivalence(subset_dfa, direct_res.dfa, check_token_names=False)
    eq_moore_hopcroft = check_dfa_equivalence(
        min_res.minimized_dfa, hopcroft_res.minimized_dfa, check_token_names=False
    )
    minimality = verify_dfa_is_minimal(min_res.minimized_dfa, check_token_names=False)

    string_tests = []
    if test_strings:
        for s in test_strings:
            nfa_ok, _, _ = nfa.simulate(s)
            eps_free_ok, _, _ = eps_free_nfa.simulate(s)
            dfa_ok, _, dfa_trace = min_res.minimized_dfa.simulate(s)
            hop_ok, _, _ = hopcroft_res.minimized_dfa.simulate(s)
            dir_ok, _, _ = direct_res.dfa.simulate(s)
            string_tests.append(
                {
                    "input": s,
                    "nfa_accepted": nfa_ok,
                    "eps_free_nfa_accepted": eps_free_ok,
                    "min_dfa_accepted": dfa_ok,
                    "hopcroft_dfa_accepted": hop_ok,
                    "direct_dfa_accepted": dir_ok,
                    "consistent": (nfa_ok == eps_free_ok == dfa_ok == hop_ok == dir_ok),
                    "dfa_trace": dfa_trace,
                }
            )

    return {
        "pattern": pattern,
        "token_name": token_name,
        "nullable": ast.is_nullable(),
        "ast_nodes": ast.node_count(),
        "unicode_chars": sorted(ast.explicit_unicode_chars()),
        "explicit_infix": ast.to_explicit_infix(),
        "postfix": " ".join(ast.to_postfix_tokens()),
        "nfa": nfa.to_graph_dict(),
        "eps_free_nfa": eps_free_nfa.to_graph_dict(),
        "subset_dfa": subset_dfa.to_graph_dict(),
        "subset_table": subset_dfa.to_transition_table(),
        "subset_steps": subset_steps,
        "direct_dfa": direct_res.to_dict(),
        "minimized_dfa": min_res.minimized_dfa.to_graph_dict(),
        "minimized_table": min_res.minimized_dfa.to_transition_table(),
        "minimization": min_res.to_dict(),
        "hopcroft_minimization": hopcroft_res.to_dict(),
        "gnfa": gnfa_res.to_dict(),
        "minimality": minimality.to_dict(),
        "equivalence": {
            "subset_vs_minimized": eq_subset_min.to_dict(),
            "subset_vs_direct": eq_subset_direct.to_dict(),
            "moore_vs_hopcroft": eq_moore_hopcroft.to_dict(),
            "kleene_roundtrip": {
                "equivalent": gnfa_res.kleene_equivalent,
                "visited_pairs": gnfa_res.visited_pairs,
                "synthesized_regex": gnfa_res.synthesized_regex,
                "message": gnfa_res.verification_message,
            },
        },
        "string_tests": string_tests,
    }


__all__ = [
    "LexicalAnalyzer",
    "TokenSpec",
    "RegexSyntaxError",
    "MAX_AST_NODES",
    "MAX_QUANTIFIER_BOUND",
    "PRESETS",
    "SINGLE_REGEX_EXAMPLES",
    "inspect_single_regex",
    "eliminate_epsilon",
    "minimize_dfa",
    "minimize_dfa_hopcroft",
    "complement_dfa",
    "complement_charset",
    "build_dynamic_sigma",
    "build_direct_dfa",
    "build_combined_direct_dfa",
    "dfa_to_regex",
    "GNFAEliminationResult",
    "generate_standalone_lexer",
    "export_nfa_to_jflap",
    "export_dfa_to_jflap",
    "import_jflap_to_nfa",
    "import_jflap_to_dfa",
    "check_dfa_equivalence",
    "check_dfa_intersection",
    "analyze_token_intersections",
    "IntersectionMatrixResult",
    "PairIntersectionInfo",
    "verify_dfa_is_minimal",
    "compare_regex_equivalence",
    "verify_nfa_dfa_on_strings",
]
