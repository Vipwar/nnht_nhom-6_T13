"""
Comprehensive Automated Test Suite for Topic T13: Automata-based Lexical Analyzer.

Covers:
1. Regex Parser (valid syntax, escapes, char classes, boundary classes, counted quantifiers {m,n}, invalid syntax rejection)
2. Thompson's Construction & Theorem 2 Epsilon Elimination (exact UEH slide state counts, ε-NFA & ε-free NFA simulation)
3. Subset Construction (exact equivalence with ε-NFA & ε-free NFA, priority conflict resolution)
4. Direct RE -> DFA Construction (nullable, firstpos, lastpos, followpos, UEH slide verification, Combined Multi-token Direct DFA)
5. Multi-token DFA Minimization (Moore Partition Refinement + Hopcroft O(|E|·|Q|log|Q|) + Myhill-Nerode Absolute Minimality Proof)
6. Product Automaton Equivalence Verification (6-way equivalence + negative shortest counterexample + Regex Equivalence Checker)
7. Automata-based Scanner (Maximal Munch, Reps O(n) memoized cutoffs, BLOCK_COMMENT, UTF-8, CRLF/LF/CR line/col, panic_char vs smart_sync)
8. Shadowed / Dead Token Rule Detection (priority conflict warning when a rule is completely shadowed)
9. Independent Oracle Cross-Check & Fuzz Testing (verifying our zero-re automata engine against Python's `re` on 200+ random strings)
10. JFLAP .jff XML Export & Round-Trip Import Verification
11. Mathematical Invariants (Zero-Loss Reconstruction, 6-Way Equivalence, Proven Minimality, Anti-O(n^2) Linear Stress, Zero `import re` AST Check)
"""

from __future__ import annotations

import ast
import json
import random
import re as _oracle_re  # Used ONLY as an independent external test oracle!
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lexer_engine import (  # noqa: E402
    MAX_AST_NODES,
    PRESETS,
    LexicalAnalyzer,
    RegexSyntaxError,
    TokenSpec,
    analyze_token_intersections,
    build_combined_direct_dfa,
    build_dynamic_sigma,
    check_dfa_equivalence,
    check_dfa_intersection,
    compare_regex_equivalence,
    complement_charset,
    complement_dfa,
    dfa_to_regex,
    eliminate_epsilon,
    export_dfa_to_jflap,
    export_nfa_to_jflap,
    generate_standalone_lexer,
    import_jflap_to_dfa,
    import_jflap_to_nfa,
    inspect_single_regex,
    minimize_dfa_hopcroft,
    verify_dfa_is_minimal,
    verify_nfa_dfa_on_strings,
)
from lexer_engine.dfa_minimizer import minimize_dfa  # noqa: E402
from lexer_engine.direct_dfa import build_direct_dfa  # noqa: E402
from lexer_engine.models import ASCII_SIGMA, NON_ASCII, SIGMA  # noqa: E402
from lexer_engine.regex_parser import parse_regex  # noqa: E402
from lexer_engine.scanner import scan_source  # noqa: E402
from lexer_engine.subset_construction import nfa_to_dfa  # noqa: E402
from lexer_engine.thompson import build_token_nfa  # noqa: E402

TEST_CASES_PATH = Path(__file__).resolve().parent / "test_cases.json"


def load_test_cases() -> Dict:
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def assert_zero_loss_reconstruction(source: str, scan_result) -> Tuple[bool, str]:
    """
    Invariant 1 (Zero-Loss Reconstruction):
    Verify that merging all tokens (including skipped whitespace/comments) and lexical errors
    ordered by start_pos forms contiguous non-overlapping intervals [start_pos, end_pos)
    covering [0, len(source)) and concatenates to 100% of `source`.
    """
    items = []
    for tok in scan_result.tokens:
        items.append((tok.start_pos, tok.end_pos, tok.lexeme))
    for err in scan_result.errors:
        items.append((err.start_pos, err.end_pos, err.lexeme))
    items.sort(key=lambda x: (x[0], x[1]))

    cursor = 0
    reconstructed = []
    for start_pos, end_pos, lexeme in items:
        if start_pos != cursor:
            return False, f"Gap/overlap at {cursor} vs {start_pos}"
        if end_pos - start_pos != len(lexeme):
            return False, f"Length mismatch [{start_pos}, {end_pos}) vs len({lexeme!r})"
        reconstructed.append(lexeme)
        cursor = end_pos

    if cursor != len(source):
        return False, f"Final cursor {cursor} != len(source) {len(source)}"
    joined = "".join(reconstructed)
    if joined != source:
        return False, "Reconstructed string differs from original source"
    return True, "OK"


def run_json_test_report() -> Dict:
    """
    Execute all structured test cases in test_cases.json and return a detailed JSON report
    (used by both CLI `test` command and the Web UI Test Suite Dashboard).
    """
    data = load_test_cases()
    results: List[Dict] = []
    compiled_cache: Dict[str, LexicalAnalyzer] = {}

    def get_lexer(preset_id: str) -> LexicalAnalyzer:
        if preset_id not in compiled_cache:
            compiled_cache[preset_id] = LexicalAnalyzer.from_preset(preset_id)
        return compiled_cache[preset_id]

    # 1. Single Regex 7-way Kleene 360° equivalence & membership tests
    for tc in data["single_regex_cases"]:
        info = inspect_single_regex(tc["pattern"], tc["id"])
        nfa, _ = build_token_nfa(tc["pattern"], tc["id"])
        eps_free = eliminate_epsilon(nfa)
        sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
        min_dfa = minimize_dfa(sub_dfa).minimized_dfa
        hop_dfa = minimize_dfa_hopcroft(sub_dfa).minimized_dfa
        dir_dfa = build_direct_dfa(tc["pattern"], tc["id"]).dfa

        eq1 = check_dfa_equivalence(sub_dfa, min_dfa, check_token_names=False)
        eq2 = check_dfa_equivalence(sub_dfa, dir_dfa, check_token_names=False)
        eq3 = check_dfa_equivalence(min_dfa, hop_dfa, check_token_names=False)
        kleene_ok = info["gnfa"]["kleene_equivalent"]
        min_proof = verify_dfa_is_minimal(min_dfa, check_token_names=False)

        failures = []
        if not eq1.equivalent:
            failures.append(f"Subset != MooreMinDFA: {eq1.message}")
        if not eq2.equivalent:
            failures.append(f"Subset != DirectDFA: {eq2.message}")
        if not eq3.equivalent:
            failures.append(f"MooreMin != HopcroftMin: {eq3.message}")
        if not kleene_ok:
            failures.append(f"GNFA Kleene 360° failed: {info['gnfa']['verification_message']}")
        if not min_proof.is_minimal:
            failures.append(f"Not minimal: {min_proof.message}")

        for s in tc["accept"]:
            ok_nfa, _, _ = nfa.simulate(s)
            ok_ef, _, _ = eps_free.simulate(s)
            ok_min, _, _ = min_dfa.simulate(s)
            ok_hop, _, _ = hop_dfa.simulate(s)
            ok_dir, _, _ = dir_dfa.simulate(s)
            if not (ok_nfa and ok_ef and ok_min and ok_hop and ok_dir):
                failures.append(
                    f"Expected ACCEPT for {s!r}, got εNFA={ok_nfa}, NFA={ok_ef}, Min={ok_min}, Hop={ok_hop}, Dir={ok_dir}"
                )

        for s in tc["reject"]:
            ok_nfa, _, _ = nfa.simulate(s)
            ok_ef, _, _ = eps_free.simulate(s)
            ok_min, _, _ = min_dfa.simulate(s)
            ok_hop, _, _ = hop_dfa.simulate(s)
            ok_dir, _, _ = dir_dfa.simulate(s)
            if ok_nfa or ok_ef or ok_min or ok_hop or ok_dir:
                failures.append(
                    f"Expected REJECT for {s!r}, got εNFA={ok_nfa}, NFA={ok_ef}, Min={ok_min}, Hop={ok_hop}, Dir={ok_dir}"
                )

        results.append(
            {
                "id": tc["id"],
                "group": "Single RE Pipeline",
                "category": tc["category"],
                "name": tc["name"],
                "input": tc["pattern"],
                "passed": len(failures) == 0,
                "detail": (
                    f"εNFA:{info['nfa']['state_count']} → NFA:{len(eps_free.states)} → Sub:{info['subset_dfa']['state_count']} "
                    f"→ Dir:{info['direct_dfa']['dfa']['state_count']} → Min:{info['minimized_dfa']['state_count']} "
                    f"→ GNFA:OK | {len(tc['accept'])} accept + {len(tc['reject'])} reject | Kleene=OK"
                    if not failures
                    else "; ".join(failures)
                ),
            }
        )

    # 2. Invalid Regex rejection tests
    for tc in data["invalid_regex_cases"]:
        caught = False
        err_msg = ""
        try:
            parse_regex(tc["pattern"])
        except RegexSyntaxError as exc:
            caught = True
            err_msg = str(exc)

        results.append(
            {
                "id": tc["id"],
                "group": "Regex Error Handling",
                "category": "invalid",
                "name": tc["name"],
                "input": tc["pattern"],
                "passed": caught,
                "detail": err_msg if caught else "FAILED: Không phát hiện lỗi cú pháp RE!",
            }
        )

    # 3. Scanner tests (valid, edge, invalid) + Subset vs MinDFA consistency + Zero-Loss Reconstruction
    for tc in data["scanner_cases"]:
        lex = get_lexer(tc["preset"])
        res_min = lex.scan(tc["input"], use_minimized=True, record_traces=False)
        res_sub = lex.scan(tc["input"], use_minimized=False, record_traces=False)

        got_min = [[t.token_type, t.lexeme] for t in res_min.visible_tokens]
        got_sub = [[t.token_type, t.lexeme] for t in res_sub.visible_tokens]

        ok_tokens = got_min == tc["expected_tokens"]
        ok_errors = len(res_min.errors) == tc["expected_errors"]
        ok_consistent = (got_min == got_sub) and (len(res_min.errors) == len(res_sub.errors))
        ok_reconstruct, recon_msg = assert_zero_loss_reconstruction(tc["input"], res_min)

        passed = ok_tokens and ok_errors and ok_consistent and ok_reconstruct
        if passed:
            detail = (
                f"[{tc['preset']}] {len(got_min)} tokens, {len(res_min.errors)} lỗi, "
                f"{res_min.elapsed_ms:.3f} ms (Subset ≡ MinDFA, Zero-Loss=OK)"
            )
        else:
            detail = (
                f"Expected {len(tc['expected_tokens'])} tokens / {tc['expected_errors']} errors, "
                f"got {got_min} / {len(res_min.errors)} errors ({recon_msg})"
            )

        results.append(
            {
                "id": tc["id"],
                "group": "Lexical Scanner",
                "category": tc["category"],
                "name": tc["name"],
                "input": tc["input"],
                "passed": passed,
                "detail": detail,
            }
        )

    passed_count = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "pass_rate": round(100.0 * passed_count / max(1, len(results)), 2),
        "results": results,
    }


class TestAutomataLexicalAnalyzer(unittest.TestCase):
    """Full unit, integration, mathematical invariant, and stress test suite."""

    def test_zero_re_in_engine(self) -> None:
        """
        Invariant 5: Verify via Python's AST parser that NO file inside lexer_engine/,
        app.py, or cli.py imports Python's `re` module (directly or via __import__).
        """
        engine_dir = PROJECT_ROOT / "lexer_engine"
        target_files = list(engine_dir.glob("*.py")) + [
            PROJECT_ROOT / "app.py",
            PROJECT_ROOT / "cli.py",
        ]
        for py_file in target_files:
            src = py_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(
                            alias.name,
                            "re",
                            f"{py_file.name} must not import `re`!",
                        )
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(
                        node.module,
                        "re",
                        f"{py_file.name} must not import from `re`!",
                    )
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "re":
                        self.fail(f"{py_file.name} must not call __import__('re')!")

    def test_all_json_cases(self) -> None:
        """Execute all 72 structured test cases in tests/test_cases.json."""
        report = run_json_test_report()
        self.assertGreaterEqual(report["total"], 72, "test_cases.json must contain at least 72 test cases")
        for item in report["results"]:
            with self.subTest(case=item["id"], name=item["name"]):
                self.assertTrue(item["passed"], f"{item['id']} failed: {item['detail']}")

    def test_ueh_slide_exact_counts(self) -> None:
        """Verify exact state counts against UEH Chap 3.1 lecture slides."""
        # Slide 38: Thompson NFA for (a|b)*abb has 11 states (0..10), Subset DFA has 5 states, Min-DFA has 4 states
        info1 = inspect_single_regex("(a|b)*abb", "SLIDE38")
        self.assertEqual(info1["nfa"]["state_count"], 11)
        self.assertEqual(info1["subset_dfa"]["state_count"], 5)
        self.assertEqual(info1["minimized_dfa"]["state_count"], 4)
        self.assertEqual(info1["hopcroft_minimization"]["minimized_state_count"], 4)
        self.assertTrue(info1["equivalence"]["subset_vs_minimized"]["equivalent"])
        self.assertTrue(info1["equivalence"]["subset_vs_direct"]["equivalent"])
        self.assertTrue(info1["equivalence"]["moore_vs_hopcroft"]["equivalent"])
        self.assertTrue(info1["minimality"]["is_minimal"])

        # Slides 46-57: Direct DFA for (a|ba)(a|b)*ba has 5 states (A, B, C, D, E) and 8 leaf positions (1..8)
        info2 = inspect_single_regex("(a|ba)(a|b)*ba", "SLIDE46")
        self.assertEqual(info2["direct_dfa"]["end_marker_pos"], 8)
        self.assertEqual(info2["direct_dfa"]["dfa"]["state_count"], 5)
        self.assertEqual(info2["minimized_dfa"]["state_count"], 5)
        self.assertTrue(info2["minimality"]["is_minimal"])
        # Verify followpos table matches Slide 54:
        flp = {row["position"]: row["followpos"] for row in info2["direct_dfa"]["followpos_table"]}
        self.assertEqual(flp[1], [4, 5, 6])
        self.assertEqual(flp[2], [3])
        self.assertEqual(flp[3], [4, 5, 6])
        self.assertEqual(flp[4], [4, 5, 6])
        self.assertEqual(flp[5], [4, 5, 6])
        self.assertEqual(flp[6], [7])
        self.assertEqual(flp[7], [8])
        self.assertEqual(flp[8], [])

    def test_all_presets_formal_equivalence(self) -> None:
        """
        Prove Subset DFA ≡ Moore Min-DFA ≡ Hopcroft Min-DFA ≡ Combined Direct DFA
        formally via Product Automaton on all 3 language presets.
        """
        for pid in PRESETS:
            with self.subTest(preset=pid):
                lex = LexicalAnalyzer.from_preset(pid)
                self.assertTrue(lex.equivalence.equivalent, lex.equivalence.message)
                self.assertTrue(
                    lex.moore_vs_hopcroft_equivalence.equivalent,
                    lex.moore_vs_hopcroft_equivalence.message,
                )
                self.assertEqual(
                    len(lex.minimized_dfa.states),
                    len(lex.hopcroft_minimization.minimized_dfa.states),
                )
                # Verify Combined Multi-token Direct DFA equivalence
                combined_direct = build_combined_direct_dfa(lex.specs)
                eq_direct = check_dfa_equivalence(
                    lex.minimized_dfa, combined_direct, check_token_names=True
                )
                self.assertTrue(eq_direct.equivalent, eq_direct.message)

                # Verify Theorem 2 epsilon-free NFA equivalence
                eps_free_dfa, _ = nfa_to_dfa(lex.eps_free_nfa, record_steps=False)
                eq_eps_free = check_dfa_equivalence(
                    lex.minimized_dfa, eps_free_dfa, check_token_names=True
                )
                self.assertTrue(eq_eps_free.equivalent, eq_eps_free.message)

    def test_invariant_3_proven_myhill_nerode_minimality(self) -> None:
        """
        Invariant 3 (Proven Minimality):
        Verify mathematically via verify_dfa_is_minimal() that every pair of distinct states
        (p, q) in Minimized DFA has a distinguishing witness string w where tau(delta(p, w)) != tau(delta(q, w)).
        """
        for pid in PRESETS:
            with self.subTest(preset=pid):
                lex = LexicalAnalyzer.from_preset(pid)
                proof = lex.minimality_proof
                self.assertTrue(proof.is_minimal, proof.message)
                n_states = len(lex.minimized_dfa.states)
                expected_pairs = n_states * (n_states - 1) // 2
                self.assertEqual(proof.total_pairs, expected_pairs)
                self.assertEqual(proof.distinguishable_pairs, expected_pairs)
                self.assertEqual(len(proof.unreachable_states), 0)
                self.assertEqual(len(proof.dead_states), 0)
                self.assertEqual(len(proof.equivalent_pairs), 0)

    def test_shadowed_rule_detection(self) -> None:
        """
        Verify that placing a broader rule (IDENTIFIER) at a higher priority than a keyword rule (KW_IF)
        is automatically detected as a Shadowed / Dead Token Rule with a detailed Vietnamese warning.
        """
        specs = [
            TokenSpec("WHITESPACE", r"[ \t\n\r]+", 1, True, "whitespace"),
            TokenSpec("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*", 2, False, "identifier"),
            TokenSpec("KW_IF", r"if", 3, False, "keyword"),
            TokenSpec("KW_WHILE", r"while", 4, False, "keyword"),
        ]
        lex = LexicalAnalyzer.compile(specs)
        shadowed_names = [s["token_name"] for s in lex.shadowed_rules]
        self.assertIn("KW_IF", shadowed_names)
        self.assertIn("KW_WHILE", shadowed_names)
        kw_if_entry = next(s for s in lex.shadowed_rules if s["token_name"] == "KW_IF")
        self.assertIn("IDENTIFIER", kw_if_entry["shadowed_by"])
        self.assertTrue(
            any("KW_IF" in w and "IDENTIFIER" in w and "che khuất" in w for w in lex.warnings)
        )

    def test_error_recovery_panic_vs_smart_sync(self) -> None:
        """
        Verify both `panic_char` (1-character advance) and `smart_sync` (swallowing an entire
        unterminated string literal or unterminated block comment as 1 cohesive error).
        """
        lex = LexicalAnalyzer.from_preset("minilang")
        src = 'let s = "chuoi chua dong tren dong 1\nlet x = 42;'

        res_panic = lex.scan(src, error_recovery="panic_char")
        res_smart = lex.scan(src, error_recovery="smart_sync")

        # In panic_char mode, '"' is 1 error, then words inside the unclosed line become stray IDENTIFIER tokens
        self.assertEqual(len(res_panic.errors), 1)
        self.assertEqual(res_panic.errors[0].lexeme, '"')
        self.assertGreater(len(res_panic.visible_tokens), 7)

        # In smart_sync mode, the entire unclosed string up to \n is swallowed as 1 lexical error,
        # so line 2 (`let x = 42;`) is tokenized cleanly without bogus tokens from line 1!
        self.assertEqual(len(res_smart.errors), 1)
        self.assertEqual(res_smart.errors[0].lexeme, '"chuoi chua dong tren dong 1')
        self.assertEqual(
            [(t.token_type, t.lexeme) for t in res_smart.visible_tokens],
            [
                ("KW_LET", "let"),
                ("IDENTIFIER", "s"),
                ("OP_ASSIGN", "="),
                ("KW_LET", "let"),
                ("IDENTIFIER", "x"),
                ("OP_ASSIGN", "="),
                ("INT_LIT", "42"),
                ("SEMICOLON", ";"),
            ],
        )
        ok_p, msg_p = assert_zero_loss_reconstruction(src, res_panic)
        ok_s, msg_s = assert_zero_loss_reconstruction(src, res_smart)
        self.assertTrue(ok_p, msg_p)
        self.assertTrue(ok_s, msg_s)

        # Also test unclosed block comment in smart_sync vs panic_char
        src_blk = "let a = 1; /* chua dong comment"
        blk_panic = lex.scan(src_blk, error_recovery="panic_char")
        blk_smart = lex.scan(src_blk, error_recovery="smart_sync")
        self.assertEqual(blk_panic.errors[0].lexeme, "/")
        self.assertEqual(blk_smart.errors[0].lexeme, "/* chua dong comment")
        self.assertEqual(len(blk_smart.visible_tokens), 5)

    def test_invariant_1_zero_loss_reconstruction(self) -> None:
        """
        Invariant 1 (Zero-Loss Reconstruction):
        Test across all preset sample programs and 40 random fuzz inputs containing ASCII, UTF-8,
        newlines, comments, quotes, and error characters that 100% of input characters are accounted for.
        """
        rng = random.Random(202613)
        alphabet = list("abiflet0123.+-*/=<>!&|\"\\'\n\r\t @#$€XinChàoUEH")
        for pid, pinfo in PRESETS.items():
            lex = LexicalAnalyzer.from_preset(pid)
            for sample_key, sample in pinfo["samples"].items():
                for mode in ("panic_char", "smart_sync"):
                    res = lex.scan(sample["code"], error_recovery=mode)
                    ok, msg = assert_zero_loss_reconstruction(sample["code"], res)
                    self.assertTrue(ok, f"[{pid}:{sample_key}:{mode}] {msg}")

            for idx in range(40):
                fuzz_str = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 120)))
                for mode in ("panic_char", "smart_sync"):
                    res = lex.scan(fuzz_str, error_recovery=mode)
                    ok, msg = assert_zero_loss_reconstruction(fuzz_str, res)
                    self.assertTrue(ok, f"[{pid}:fuzz#{idx}:{mode}] {msg}")

    def test_invariant_2_six_way_equivalence_fuzz(self) -> None:
        """
        Invariant 2 (6-Way Equivalence):
        On 200+ random/fuzz strings across multiple RE patterns, verify:
        Thompson ε-NFA ≡ ε-free NFA ≡ Subset DFA ≡ Direct DFA ≡ Moore Min-DFA ≡ Hopcroft Min-DFA ≡ Python `re`.
        """
        rng = random.Random(1337)
        test_configs = [
            (r"(a|b)*abb", "ab"),
            (r"(a|ba)(a|b)*ba", "ab"),
            (r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", "0129.eE+-a"),
            (r"/\*([^*]|\*+[^*/])*\*+/", "/*ab\n "),
            (r"0[xX][0-9a-fA-F]{2,4}", "0xX19aFg"),
            (r"[-a][a-][-][^^]", "-a^b"),
        ]
        total_checked = 0
        for pat, chars in test_configs:
            nfa, _ = build_token_nfa(pat, "T")
            eps_free = eliminate_epsilon(nfa)
            sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
            moore_dfa = minimize_dfa(sub_dfa).minimized_dfa
            hop_dfa = minimize_dfa_hopcroft(sub_dfa).minimized_dfa
            dir_dfa = build_direct_dfa(pat, "T").dfa
            oracle = _oracle_re.compile(f"^(?:{pat})$")

            for _ in range(45):
                s = "".join(rng.choice(chars) for _ in range(rng.randint(0, 14)))
                expected = bool(oracle.match(s))
                r_nfa, _, _ = nfa.simulate(s)
                r_ef, _, _ = eps_free.simulate(s)
                r_sub, _, _ = sub_dfa.simulate(s)
                r_dir, _, _ = dir_dfa.simulate(s)
                r_moore, _, _ = moore_dfa.simulate(s)
                r_hop, _, _ = hop_dfa.simulate(s)
                self.assertEqual(r_nfa, expected, f"ε-NFA mismatch on {pat} with {s!r}")
                self.assertEqual(r_ef, expected, f"ε-free NFA mismatch on {pat} with {s!r}")
                self.assertEqual(r_sub, expected, f"Subset DFA mismatch on {pat} with {s!r}")
                self.assertEqual(r_dir, expected, f"Direct DFA mismatch on {pat} with {s!r}")
                self.assertEqual(r_moore, expected, f"Moore Min-DFA mismatch on {pat} with {s!r}")
                self.assertEqual(r_hop, expected, f"Hopcroft Min-DFA mismatch on {pat} with {s!r}")
                total_checked += 1
        self.assertGreaterEqual(total_checked, 200)

    def test_invariant_4_anti_quadratic_linear_time_stress(self) -> None:
        """
        Invariant 4 (Anti-O(n^2) Linear-Time Maximal Munch Stress Test):
        Verify that 10,000-character unclosed strings and unclosed block comments scan in < 200 ms
        thanks to Reps (1998) `failed_states` memoization.
        """
        lex = LexicalAnalyzer.from_preset("minilang")

        # 1. 10,000-char unclosed string: '"' + 'a' * 10000
        t0 = time.perf_counter()
        r1 = lex.scan('"' + "a" * 10000, record_traces=False)
        dt1_ms = (time.perf_counter() - t0) * 1000.0
        self.assertLess(dt1_ms, 200.0, f"10k unclosed string took {dt1_ms:.2f} ms (>= 200 ms)")
        self.assertEqual(len(r1.errors), 1)

        # 2. 10,000-char unclosed block comment: '/*' + 'x' * 10000
        t0 = time.perf_counter()
        r2 = lex.scan("/*" + "x" * 10000, record_traces=False)
        dt2_ms = (time.perf_counter() - t0) * 1000.0
        self.assertLess(dt2_ms, 200.0, f"10k unclosed block comment took {dt2_ms:.2f} ms (>= 200 ms)")
        self.assertGreaterEqual(len(r2.errors), 1)

        # 3. Pathological repeated escaped-quote prefix ('"' + '\"' * 5000) that triggers O(n^2) without Reps memoization
        pathological_quotes = '"' + '\\"' * 5000
        t0 = time.perf_counter()
        r3 = lex.scan(pathological_quotes, record_traces=False)
        dt3_ms = (time.perf_counter() - t0) * 1000.0
        self.assertLess(dt3_ms, 200.0, f"Pathological 10k escaped quotes took {dt3_ms:.2f} ms (>= 200 ms)")
        self.assertEqual(r3.memoized_cutoffs, 5000)

    def test_non_equivalent_counterexample_and_regex_comparator(self) -> None:
        """Verify Product Automaton finds shortest counterexample and compare_regex_equivalence works."""
        dfa_a = build_direct_dfa("a+b", "A").dfa
        dfa_b = build_direct_dfa("a*b", "A").dfa
        eq = check_dfa_equivalence(dfa_a, dfa_b)
        self.assertFalse(eq.equivalent)
        self.assertEqual(eq.counterexample, "b")

        cmp_eq = compare_regex_equivalence("(a|b)*abb", "(b|a)*a[b]{2}")
        self.assertTrue(cmp_eq["equivalent"])

        cmp_diff = compare_regex_equivalence("(a|b)*abb", "(a|b)+abb")
        self.assertFalse(cmp_diff["equivalent"])
        self.assertEqual(cmp_diff["counterexample"], "abb")

    def test_nfa_vs_dfa_combined_crosscheck(self) -> None:
        """Verify Combined NFA and Minimized Combined DFA classify individual lexemes identically."""
        lex = LexicalAnalyzer.from_preset("minilang")
        lexemes = [
            "if", "else", "while", "ifx", "true", "false", "true1",
            "0", "42", "3.14", "2.5e-4", '"ok"', '""', '"Xin chào UEH"',
            "// hi", "/* block */", "/**/", "/*** a * b ***/",
            "==", "!=", "<=", ">=", "&&", "||", "=", "+", "/", ";",
            "@", "$", "3.", '"unclosed', "/* unclosed",
        ]
        report = verify_nfa_dfa_on_strings(lex.combined_nfa, lex.minimized_dfa, lexemes)
        self.assertTrue(report["all_passed"], f"Mismatches: {report['mismatches']}")

    def test_line_and_column_tracking_mixed_newlines(self) -> None:
        """Verify exact (line, col) and (start_pos, end_pos) across Unix \\n, Windows \\r\\n, Mac \\r, and multiline comments."""
        lex = LexicalAnalyzer.from_preset("minilang")
        src = "let a = 1;\r\n  /* line2\r\n   line3 */\n\tif (a == 1)\rprint(a);"
        res = lex.scan(src)
        self.assertEqual(len(res.errors), 0)
        by_lex = [(t.lexeme, t.line, t.col) for t in res.visible_tokens]
        self.assertEqual(by_lex[0], ("let", 1, 1))
        self.assertEqual(by_lex[4], (";", 1, 10))
        self.assertEqual(by_lex[5], ("if", 4, 2))
        self.assertEqual(by_lex[11], ("print", 5, 1))

    def test_custom_spec_live_extension(self) -> None:
        """Verify adding a brand-new token rule (HEX_LIT with {2,4}) and priority swap works dynamically."""
        custom_specs = [
            TokenSpec("WS", r"[ \t\n\r]+", 1, True, "whitespace"),
            TokenSpec("HEX_LIT", r"0[xX][0-9a-fA-F]{2,4}", 2, False, "literal"),
            TokenSpec("INT_LIT", r"[0-9]+", 3, False, "literal"),
            TokenSpec("ID", r"[a-zA-Z_][a-zA-Z0-9_]*", 4, False, "identifier"),
            TokenSpec("ASSIGN", r"=", 5, False, "operator"),
        ]
        lex = LexicalAnalyzer.compile(custom_specs)
        self.assertTrue(lex.equivalence.equivalent)
        res = lex.scan("color = 0xFF0A + 42")
        types = [(t.token_type, t.lexeme) for t in res.visible_tokens]
        self.assertEqual(types, [("ID", "color"), ("ASSIGN", "="), ("HEX_LIT", "0xFF0A"), ("INT_LIT", "42")])
        self.assertEqual(len(res.errors), 1)  # '+' is not in custom_specs

    def test_nullable_token_no_infinite_loop(self) -> None:
        """Ensure nullable token patterns (a*, (a|ε)*) trigger warning and NEVER loop infinitely during scanning."""
        specs = [
            TokenSpec("BAD_NULLABLE", r"(a|ε)*", 1, False, "other"),
            TokenSpec("B_TOK", r"b", 2, False, "other"),
        ]
        lex = LexicalAnalyzer.compile(specs)
        self.assertTrue(len(lex.warnings) >= 1)
        res = lex.scan("aabcb")
        self.assertEqual(
            [(t.token_type, t.lexeme) for t in res.visible_tokens],
            [("BAD_NULLABLE", "aa"), ("B_TOK", "b"), ("B_TOK", "b")],
        )
        self.assertEqual(len(res.errors), 1)

    def test_jflap_round_trip_verification(self) -> None:
        """
        Verify exported JFLAP .jff XML is well-formed, escapes XML special characters (<, >, &, ", '),
        and round-trips back via import_jflap_to_nfa / import_jflap_to_dfa with 100% equivalence.
        """
        # 1. Textbook example (a|b)*abb
        nfa, _ = build_token_nfa("(a|b)*abb", "SLIDE38")
        sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
        min_dfa = minimize_dfa(sub_dfa).minimized_dfa

        xml_nfa = export_nfa_to_jflap(nfa, expand_char_classes=True)
        root_nfa = ET.fromstring(xml_nfa)
        self.assertEqual(root_nfa.findtext("type"), "fa")
        self.assertEqual(len(root_nfa.findall("./automaton/state")), 11)
        rt_nfa = import_jflap_to_nfa(xml_nfa)
        rt_nfa_dfa, _ = nfa_to_dfa(rt_nfa, record_steps=False)
        self.assertTrue(check_dfa_equivalence(min_dfa, rt_nfa_dfa, check_token_names=False).equivalent)

        xml_dfa = export_dfa_to_jflap(min_dfa, expand_char_classes=True)
        root_dfa = ET.fromstring(xml_dfa)
        self.assertEqual(root_dfa.findtext("type"), "fa")
        self.assertEqual(len(root_dfa.findall("./automaton/state")), 4)
        rt_dfa = import_jflap_to_dfa(xml_dfa)
        self.assertTrue(check_dfa_equivalence(min_dfa, rt_dfa, check_token_names=False).equivalent)

        # 2. Full presets containing XML special characters (<, >, &, ", ') and control whitespace (\n, \r, \t)
        for pid in PRESETS:
            with self.subTest(preset=pid):
                lex = LexicalAnalyzer.from_preset(pid)
                jff_dfa = export_dfa_to_jflap(lex.minimized_dfa, expand_char_classes=False)
                ET.fromstring(jff_dfa)
                imported_dfa = import_jflap_to_dfa(jff_dfa)
                eq = check_dfa_equivalence(lex.minimized_dfa, imported_dfa, check_token_names=True)
                self.assertTrue(eq.equivalent, f"JFLAP DFA round-trip failed on {pid}: {eq.message}")

                jff_nfa = export_nfa_to_jflap(lex.combined_nfa, expand_char_classes=False)
                ET.fromstring(jff_nfa)
                imported_nfa = import_jflap_to_nfa(jff_nfa)
                imp_nfa_dfa, _ = nfa_to_dfa(imported_nfa, record_steps=False)
                eq_nfa = check_dfa_equivalence(lex.minimized_dfa, imp_nfa_dfa, check_token_names=True)
                self.assertTrue(eq_nfa.equivalent, f"JFLAP NFA round-trip failed on {pid}: {eq_nfa.message}")

    def test_v2_1_dynamic_unicode_alphabet_partitioning(self) -> None:
        """
        Verify Dynamic Unicode Alphabet Partitioning:
        Explicit Unicode keywords/symbols (e.g., `nếu`, `lặp`, `€`, `₫`) coexist cleanly with
        general UTF-8 wildcard/negated classes (`//[^\n]*`, `"([^"\\\n\r]|\\.)*"`, `[^€]+`)
        without colliding with `NON_ASCII`.
        """
        specs = [
            TokenSpec("COMMENT", r"//[^\n]*", 1, True, "comment"),
            TokenSpec("WS", r"[ \t\n\r]+", 2, True, "whitespace"),
            TokenSpec("KW_NEU", r"nếu", 3, False, "keyword"),
            TokenSpec("KW_LAP", r"lặp", 4, False, "keyword"),
            TokenSpec("CURRENCY", r"€|₫", 5, False, "operator"),
            TokenSpec("STRING_LIT", r'"([^"\\\n\r]|\\.)*"', 6, False, "literal"),
            TokenSpec("INT_LIT", r"[0-9]+", 7, False, "literal"),
            TokenSpec("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*", 8, False, "identifier"),
            TokenSpec("ASSIGN", r"=", 9, False, "operator"),
        ]
        lex = LexicalAnalyzer.compile(specs)
        self.assertTrue(lex.equivalence.equivalent)
        self.assertTrue(lex.minimality_proof.is_minimal)
        combined_dir = build_combined_direct_dfa(specs)
        self.assertTrue(check_dfa_equivalence(lex.minimized_dfa, combined_dir, check_token_names=True).equivalent)

        src = 'nếu x = 100€ // nếu lặp 50₫\nlặp y = "Xin chào nếu 200€" 50¥'
        res = lex.scan(src)
        self.assertEqual(
            [(t.token_type, t.lexeme) for t in res.visible_tokens],
            [
                ("KW_NEU", "nếu"),
                ("IDENTIFIER", "x"),
                ("ASSIGN", "="),
                ("INT_LIT", "100"),
                ("CURRENCY", "€"),
                ("KW_LAP", "lặp"),
                ("IDENTIFIER", "y"),
                ("ASSIGN", "="),
                ("STRING_LIT", '"Xin chào nếu 200€"'),
                ("INT_LIT", "50"),
            ],
        )
        self.assertEqual([e.char for e in res.errors], ["¥"])

        # Negated explicit Unicode class [^€] must reject '€' while accepting '¥', 'ế', and 'a'
        no_euro = build_direct_dfa("[^€]+", "NO_EURO").dfa
        self.assertFalse(no_euro.simulate("€")[0])
        self.assertFalse(no_euro.simulate("abc€def")[0])
        self.assertTrue(no_euro.simulate("abc¥ế")[0])

        # Cross-DFA equivalence lifting when one regex has explicit Unicode and the other uses '.'
        cmp_res = compare_regex_equivalence("(nếu|lặp)+", "(lặp|nếu)(nếu|lặp)*")
        self.assertTrue(cmp_res["equivalent"])
        cmp_diff = compare_regex_equivalence("[^€]+", ".+")
        self.assertFalse(cmp_diff["equivalent"])

    def test_v2_2_full_ascii_boolean_algebra_and_crlf_string_lit(self) -> None:
        """
        Verify full 7-bit ASCII (0x00..0x7F, 128 chars including \\0, \\f, \\v, \\x7f) coverage,
        strict Boolean algebra involution ~(~A) == A at both charset and DFA levels,
        and `STRING_LIT` rejecting unescaped `\\r` on Windows CRLF.
        """
        self.assertEqual(len(ASCII_SIGMA), 128)
        self.assertIn("\x00", ASCII_SIGMA)
        self.assertIn("\v", ASCII_SIGMA)
        self.assertIn("\f", ASCII_SIGMA)
        self.assertIn("\x7f", ASCII_SIGMA)
        self.assertEqual(len(SIGMA), 129)

        # 1. Charset-level Boolean involution: ~(~A) == A across ASCII, control chars, explicit Unicode & NON_ASCII
        u_ext = frozenset({"ế", "€"})
        sigma_u = build_dynamic_sigma(u_ext)
        sample_sets = [
            frozenset(),
            sigma_u,
            frozenset({"\x00", "\v", "\f", "\x7f"}),
            frozenset({"a", "ế", "€"}),
            frozenset({NON_ASCII}),
            sigma_u - {"\n", "\r", '"', "\\"},
        ]
        for cset in sample_sets:
            neg1 = complement_charset(cset, u_ext)
            neg2 = complement_charset(neg1, u_ext)
            self.assertEqual(neg2, cset, f"Charset involution ~(~A) == A failed for {cset}")

        # 2. DFA-level Boolean involution: complement_dfa(complement_dfa(D)) ≡ D
        for pat in ["(a|b)*abb", r"[\x00\f\v\x7f]+", r'"([^"\\\n\r]|\\.)*"', r"[^€\n]+", "ε"]:
            dfa = minimize_dfa(nfa_to_dfa(build_token_nfa(pat, "T")[0], record_steps=False)[0]).minimized_dfa
            comp1 = complement_dfa(dfa)
            comp2 = complement_dfa(comp1)
            eq = check_dfa_equivalence(dfa, comp2, check_token_names=False)
            self.assertTrue(eq.equivalent, f"DFA involution ~(~L) == L failed on {pat}: {eq.message}")
            # Verify L(D) ∩ L(~D) == ∅
            inter = check_dfa_intersection(dfa, comp1)
            self.assertFalse(inter.intersects, f"L(D) ∩ L(~D) must be empty for {pat}")

        # 3. Windows CRLF `\r` strictly excluded from MiniLang STRING_LIT
        lex = LexicalAnalyzer.from_preset("minilang")
        crlf_broken = 'let s = "unclosed\r\nlet ok = 1;'
        r_panic = lex.scan(crlf_broken, error_recovery="panic_char")
        r_smart = lex.scan(crlf_broken, error_recovery="smart_sync")
        self.assertEqual(len(r_panic.errors), 1)
        self.assertEqual(len(r_smart.errors), 1)
        # In smart_sync, the unclosed string stops right before `\r\n`, preserving line 2 cleanly (`let ok = 1;`)
        self.assertEqual(r_smart.errors[0].lexeme, '"unclosed')
        self.assertEqual(r_smart.visible_tokens[-5].lexeme, "let")
        self.assertEqual(r_smart.visible_tokens[-5].line, 2)
        self.assertEqual(r_smart.visible_tokens[-5].col, 1)

    def test_v2_3_anti_ast_replication_bomb(self) -> None:
        """
        Verify `MAX_AST_NODES = 4096` blocks nested counted-quantifier AST replication bombs
        like `(((a{64}){64}){64})` instantaneously without memory/CPU exhaustion.
        """
        self.assertEqual(MAX_AST_NODES, 4096)
        bombs = [
            "(((a{64}){64}){64})",
            "((((a{16}){16}){16}){16})",
            "(a{64}){64}",
            "((ab){45}){45}",
            "a" * 2500,  # 2500 leaves + 2499 concats = 4999 > 4096
        ]
        for bomb in bombs:
            t0 = time.perf_counter()
            with self.assertRaises(RegexSyntaxError):
                parse_regex(bomb)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self.assertLess(elapsed_ms, 50.0, f"AST bomb {bomb[:24]} took too long ({elapsed_ms:.2f} ms)")

        # Valid bounded quantifier well within MAX_AST_NODES must still succeed
        ok_ast = parse_regex("[0-9a-fA-F]{32}")
        self.assertLessEqual(ok_ast.node_count(), MAX_AST_NODES)

    def test_v2_4_gnfa_state_elimination_kleene_360(self) -> None:
        """
        Verify GNFA State Elimination (`DFA -> Regular Expression`) closes Kleene's Theorem 360°:
        For every test regex R_0 (including Slide 38, Slide 54, FLOAT_LIT, BLOCK_COMMENT, STRING_LIT,
        Dynamic Unicode, nullable REs, and complemented DFAs), L(R_0) == L(dfa_to_regex(MinDFA(R_0))).
        """
        cases = load_test_cases()["single_regex_cases"]
        for tc in cases:
            with self.subTest(case=tc["id"], pattern=tc["pattern"]):
                nfa, _ = build_token_nfa(tc["pattern"], tc["id"])
                min_d = minimize_dfa(nfa_to_dfa(nfa, record_steps=False)[0]).minimized_dfa
                gnfa_res = dfa_to_regex(min_d, verify_roundtrip=True)
                self.assertFalse(gnfa_res.is_empty_language)
                self.assertTrue(gnfa_res.kleene_equivalent, gnfa_res.verification_message)

        # Also test empty language DFA (complement of Sigma*)
        all_star = minimize_dfa(nfa_to_dfa(build_token_nfa(r"(.|\n)*", "ALL")[0], record_steps=False)[0]).minimized_dfa
        empty_dfa = complement_dfa(all_star)
        empty_gnfa = dfa_to_regex(empty_dfa, verify_roundtrip=True)
        self.assertTrue(empty_gnfa.is_empty_language)
        self.assertEqual(empty_gnfa.synthesized_regex, "∅")

        # Also test complement of (a|b)*abb via GNFA round-trip
        abb_dfa = minimize_dfa(nfa_to_dfa(build_token_nfa("(a|b)*abb", "ABB")[0], record_steps=False)[0]).minimized_dfa
        not_abb = complement_dfa(abb_dfa)
        not_abb_gnfa = dfa_to_regex(not_abb, verify_roundtrip=True)
        self.assertTrue(not_abb_gnfa.kleene_equivalent, not_abb_gnfa.verification_message)

    def test_v2_5_standalone_table_driven_lexer_generator_differential(self) -> None:
        """
        Verify the Flex-style Standalone Table-Driven Python Lexer Generator (`codegen.py` & `cli.py codegen`):
        1. Generated source has ZERO `import re` and ZERO `lexer_engine` imports.
        2. 100% differential parity on all 3 presets, all JSON scanner cases, both `panic_char` & `smart_sync`,
           10,000-char pathological Reps O(n) stress strings, and Dynamic Unicode specs.
        3. Subprocess execution via `cli.py codegen` works standalone out-of-the-box.
        """
        data = load_test_cases()
        generated_instances = {}

        for pid in PRESETS:
            lex = LexicalAnalyzer.from_preset(pid)
            cls_name = f"Standalone_{pid.capitalize()}"
            src_code = generate_standalone_lexer(lex, class_name=cls_name, preset_name=pid)

            # AST guard: zero `re` and zero `lexer_engine` imports
            tree = ast.parse(src_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name, ("re", "lexer_engine"))
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, ("re", "lexer_engine"))

            ns: Dict = {}
            exec(src_code, ns)
            gen_lex = ns[cls_name]()
            generated_instances[pid] = (lex, gen_lex)

            for sample in PRESETS[pid]["samples"].values():
                for mode in ("panic_char", "smart_sync"):
                    r_ref = lex.scan(sample["code"], record_traces=False, error_recovery=mode)
                    r_gen = gen_lex.scan(sample["code"], error_recovery=mode)
                    self.assertEqual(
                        [t.to_dict() for t in r_ref.tokens],
                        [t.to_dict() for t in r_gen.tokens],
                    )
                    self.assertEqual(
                        [e.to_dict() for e in r_ref.errors],
                        [e.to_dict() for e in r_gen.errors],
                    )

        # Differential check across all structured JSON scanner_cases
        for sc in data["scanner_cases"]:
            lex_ref, lex_gen = generated_instances[sc["preset"]]
            for mode in ("panic_char", "smart_sync"):
                r_ref = lex_ref.scan(sc["input"], record_traces=False, error_recovery=mode)
                r_gen = lex_gen.scan(sc["input"], error_recovery=mode)
                self.assertEqual([t.to_dict() for t in r_ref.tokens], [t.to_dict() for t in r_gen.tokens])
                self.assertEqual([e.to_dict() for e in r_ref.errors], [e.to_dict() for e in r_gen.errors])

        # Differential check on 10k pathological Reps O(n) stress test
        ml_ref, ml_gen = generated_instances["minilang"]
        stress_in = '"' + '\\"' * 5000
        s_ref = ml_ref.scan(stress_in, record_traces=False)
        s_gen = ml_gen.scan(stress_in)
        self.assertEqual(s_gen.memoized_cutoffs, 5000)
        self.assertEqual(len(s_ref.errors), len(s_gen.errors))

        # CLI codegen + standalone OS subprocess verification
        with tempfile.TemporaryDirectory() as tmpdir:
            out_py = Path(tmpdir) / "minilang_standalone.py"
            cmd_gen = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "cli.py"), "codegen", "--preset", "minilang", "--out", str(out_py)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("PASS", cmd_gen.stdout)
            cmd_run = subprocess.run(
                [sys.executable, str(out_py), "--code", 'let x = 3.14; print("UEH");', "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            parsed_out = json.loads(cmd_run.stdout)
            self.assertEqual(parsed_out["stats"]["visible_token_count"], 10)
            self.assertEqual(parsed_out["stats"]["error_count"], 0)

    def test_v2_6_static_pairwise_intersection_matrix(self) -> None:
        """
        Verify Static Pairwise Intersection Matrix Analyzer `L(R_i) ∩ L(R_j)` & shortest witnesses:
        - MiniLang: 9 safe keyword/boolean subset overlaps out of 741 pairs, 0 shadow conflicts.
        - CalcLang: 2 safe keyword overlaps out of 66 pairs.
        - MiniSQL: 5 safe keyword overlaps out of 91 pairs.
        - Detects `superset_shadow`, `identical_shadow`, and `partial_overlap` with shortest witnesses.
        """
        ml_inter = LexicalAnalyzer.from_preset("minilang").intersection_analysis
        self.assertEqual(ml_inter.total_pairs, 741)
        self.assertEqual(ml_inter.overlap_count, 9)
        self.assertEqual(ml_inter.disjoint_count, 732)
        self.assertEqual(ml_inter.shadow_conflict_count, 0)
        witness_by_rule = {ov.rule_i: ov.shortest_witness for ov in ml_inter.overlaps}
        self.assertEqual(witness_by_rule["KW_IF"], "if")
        self.assertEqual(witness_by_rule["KW_WHILE"], "while")
        self.assertIn(witness_by_rule["BOOL_LIT"], ("true", "false"))

        cl_inter = LexicalAnalyzer.from_preset("calclang").intersection_analysis
        self.assertEqual((cl_inter.overlap_count, cl_inter.total_pairs), (2, 66))

        sq_inter = LexicalAnalyzer.from_preset("minisql").intersection_analysis
        self.assertEqual((sq_inter.overlap_count, sq_inter.total_pairs), (5, 91))

        # Test superset_shadow, identical_shadow, and partial_overlap classifications
        conflict_specs = [
            TokenSpec("ID", r"[a-z]+", 1, False, "identifier"),
            TokenSpec("KW_IF", r"if", 2, False, "keyword"),          # shadowed by ID (superset_shadow)
            TokenSpec("ID_DUP", r"[a-z][a-z]*", 3, False, "other"),  # identical to ID (identical_shadow)
            TokenSpec("ALNUM_NUM", r"[a-z]?[0-9]+", 4, False, "literal"),
            TokenSpec("HEX_PREFIX", r"a0", 5, False, "literal"),     # subset of ALNUM_NUM
            TokenSpec("PARTIAL_A", r"ab*", 6, False, "other"),
            TokenSpec("PARTIAL_B", r"a*b", 7, False, "other"),       # partial overlap on 'ab'
        ]
        c_inter = analyze_token_intersections(conflict_specs)
        self.assertGreaterEqual(c_inter.shadow_conflict_count, 2)
        rel_map = {(ov.rule_i, ov.rule_j): ov for ov in c_inter.overlaps}
        self.assertEqual(rel_map[("ID", "KW_IF")].relation, "superset_shadow")
        self.assertEqual(rel_map[("ID", "KW_IF")].shortest_witness, "if")
        self.assertEqual(rel_map[("ID", "ID_DUP")].relation, "identical_shadow")
        self.assertEqual(rel_map[("PARTIAL_A", "PARTIAL_B")].relation, "partial_overlap")
        self.assertEqual(rel_map[("PARTIAL_A", "PARTIAL_B")].shortest_witness, "ab")


if __name__ == "__main__":
    unittest.main(verbosity=2)
