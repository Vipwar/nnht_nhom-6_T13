"""
Comprehensive Automated Test Suite for Topic T13: Automata-based Lexical Analyzer.

Covers:
1. Regex Parser (valid syntax, escapes, char classes, negated classes, invalid syntax rejection)
2. Thompson's Construction (exact state counts on textbook examples, epsilon-NFA simulation)
3. Subset Construction (exact equivalence with epsilon-NFA, priority conflict resolution)
4. Direct RE -> DFA Construction (nullable, firstpos, lastpos, followpos, UEH slide verification)
5. Multi-token DFA Minimization (state reduction, preserving token types, unreachable/dead removal)
6. Product Automaton Equivalence Verification (positive equivalence + negative counterexample)
7. Automata-based Scanner (Maximal Munch, backtracking, rule priority, line/col, error recovery)
8. Independent Oracle Cross-Check (verifying our zero-re automata engine against Python's `re`
   on every single test case — note `re` is ONLY used here as an external test oracle!)
9. JFLAP .jff XML Export validity
10. Custom live rule editing (adding HEX_LIT, changing priorities, nullable rule safety)
"""

from __future__ import annotations

import json
import os
import re as _oracle_re  # Used ONLY as an independent test oracle!
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lexer_engine import (  # noqa: E402
    PRESETS,
    LexicalAnalyzer,
    RegexSyntaxError,
    TokenSpec,
    check_dfa_equivalence,
    export_dfa_to_jflap,
    export_nfa_to_jflap,
    inspect_single_regex,
    verify_nfa_dfa_on_strings,
)
from lexer_engine.dfa_minimizer import minimize_dfa  # noqa: E402
from lexer_engine.direct_dfa import build_direct_dfa  # noqa: E402
from lexer_engine.regex_parser import parse_regex  # noqa: E402
from lexer_engine.subset_construction import nfa_to_dfa  # noqa: E402
from lexer_engine.thompson import build_token_nfa  # noqa: E402

TEST_CASES_PATH = Path(__file__).resolve().parent / "test_cases.json"


def load_test_cases() -> Dict:
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


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

    # 1. Single Regex equivalence & membership tests
    for tc in data["single_regex_cases"]:
        info = inspect_single_regex(tc["pattern"], tc["id"])
        nfa, _ = build_token_nfa(tc["pattern"], tc["id"])
        sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
        min_dfa = minimize_dfa(sub_dfa).minimized_dfa
        dir_dfa = build_direct_dfa(tc["pattern"], tc["id"]).dfa

        eq1 = check_dfa_equivalence(sub_dfa, min_dfa, check_token_names=False)
        eq2 = check_dfa_equivalence(sub_dfa, dir_dfa, check_token_names=False)

        failures = []
        if not eq1.equivalent:
            failures.append(f"Subset != MinDFA: {eq1.message}")
        if not eq2.equivalent:
            failures.append(f"Subset != DirectDFA: {eq2.message}")

        for s in tc["accept"]:
            ok_nfa, _, _ = nfa.simulate(s)
            ok_min, _, _ = min_dfa.simulate(s)
            ok_dir, _, _ = dir_dfa.simulate(s)
            if not (ok_nfa and ok_min and ok_dir):
                failures.append(f"Expected ACCEPT for {s!r}, got NFA={ok_nfa}, Min={ok_min}, Dir={ok_dir}")

        for s in tc["reject"]:
            ok_nfa, _, _ = nfa.simulate(s)
            ok_min, _, _ = min_dfa.simulate(s)
            ok_dir, _, _ = dir_dfa.simulate(s)
            if ok_nfa or ok_min or ok_dir:
                failures.append(f"Expected REJECT for {s!r}, got NFA={ok_nfa}, Min={ok_min}, Dir={ok_dir}")

        results.append(
            {
                "id": tc["id"],
                "group": "Single RE Pipeline",
                "category": tc["category"],
                "name": tc["name"],
                "input": tc["pattern"],
                "passed": len(failures) == 0,
                "detail": (
                    f"NFA:{info['nfa']['state_count']} → Sub:{info['subset_dfa']['state_count']} "
                    f"→ Dir:{info['direct_dfa']['dfa']['state_count']} → Min:{info['minimized_dfa']['state_count']} "
                    f"| {len(tc['accept'])} accept + {len(tc['reject'])} reject | Eq=✓"
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

    # 3. Scanner tests (valid, edge, invalid) + Subset vs MinDFA consistency
    for tc in data["scanner_cases"]:
        lex = get_lexer(tc["preset"])
        res_min = lex.scan(tc["input"], use_minimized=True, record_traces=False)
        res_sub = lex.scan(tc["input"], use_minimized=False, record_traces=False)

        got_min = [[t.token_type, t.lexeme] for t in res_min.visible_tokens]
        got_sub = [[t.token_type, t.lexeme] for t in res_sub.visible_tokens]

        ok_tokens = got_min == tc["expected_tokens"]
        ok_errors = len(res_min.errors) == tc["expected_errors"]
        ok_consistent = (got_min == got_sub) and (len(res_min.errors) == len(res_sub.errors))

        passed = ok_tokens and ok_errors and ok_consistent
        if passed:
            detail = (
                f"[{tc['preset']}] {len(got_min)} tokens, {len(res_min.errors)} lỗi, "
                f"{res_min.elapsed_ms:.3f} ms (Subset ≡ MinDFA)"
            )
        else:
            detail = (
                f"Expected {len(tc['expected_tokens'])} tokens / {tc['expected_errors']} errors, "
                f"got {got_min} / {len(res_min.errors)} errors"
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
    """Full unit & integration test suite."""

    def test_zero_re_in_engine(self) -> None:
        """Verify that NO file inside lexer_engine/ imports Python's `re` module."""
        engine_dir = PROJECT_ROOT / "lexer_engine"
        for py_file in engine_dir.glob("*.py"):
            src = py_file.read_text(encoding="utf-8")
            for line in src.splitlines():
                stripped = line.strip()
                self.assertFalse(
                    stripped == "import re" or stripped.startswith("import re ") or stripped.startswith("from re "),
                    f"lexer_engine file {py_file.name} must not import `re`!",
                )

    def test_all_json_cases(self) -> None:
        report = run_json_test_report()
        for item in report["results"]:
            with self.subTest(case=item["id"], name=item["name"]):
                self.assertTrue(item["passed"], f"{item['id']} failed: {item['detail']}")

    def test_ueh_slide_exact_counts(self) -> None:
        """Verify exact state counts against UEH Chap 3.1 lecture slides."""
        # Slide 38: Thompson NFA for (a|b)*abb has 11 states (0..10), Subset DFA has 5 states
        info1 = inspect_single_regex("(a|b)*abb", "SLIDE38")
        self.assertEqual(info1["nfa"]["state_count"], 11)
        self.assertEqual(info1["subset_dfa"]["state_count"], 5)
        self.assertEqual(info1["minimized_dfa"]["state_count"], 4)
        self.assertTrue(info1["equivalence"]["subset_vs_minimized"]["equivalent"])
        self.assertTrue(info1["equivalence"]["subset_vs_direct"]["equivalent"])

        # Slides 46-57: Direct DFA for (a|ba)(a|b)*ba has 5 states (A, B, C, D, E) and 8 leaf positions (1..8)
        info2 = inspect_single_regex("(a|ba)(a|b)*ba", "SLIDE46")
        self.assertEqual(info2["direct_dfa"]["end_marker_pos"], 8)
        self.assertEqual(info2["direct_dfa"]["dfa"]["state_count"], 5)
        self.assertEqual(info2["minimized_dfa"]["state_count"], 5)
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
        """Prove Subset DFA ≡ Minimized DFA formally via Product Automaton on all 3 presets."""
        for pid in PRESETS:
            with self.subTest(preset=pid):
                lex = LexicalAnalyzer.from_preset(pid)
                self.assertTrue(lex.equivalence.equivalent, lex.equivalence.message)
                self.assertLessEqual(len(lex.minimized_dfa.states), len(lex.subset_dfa.states))

    def test_non_equivalent_counterexample(self) -> None:
        """Verify Product Automaton finds the exact shortest counterexample for non-equivalent DFAs."""
        dfa_a = build_direct_dfa("a+b", "A").dfa
        dfa_b = build_direct_dfa("a*b", "A").dfa
        eq = check_dfa_equivalence(dfa_a, dfa_b)
        self.assertFalse(eq.equivalent)
        self.assertEqual(eq.counterexample, "b")

    def test_independent_re_oracle_crosscheck(self) -> None:
        """Cross-check our zero-re automata engine against Python's `re` on single-token patterns."""
        patterns_and_samples = [
            (r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", ["0.0", "3.14", "1.2e-5", "9.0E+2", "3.", ".5", "123", "1.2e"]),
            (r"[a-zA-Z_][a-zA-Z0-9_]*", ["x", "_a1", "ABC_9", "0a", "a-b", "", "while"]),
            (r'"([^"\\\n]|\\.)*"', ['""', '"abc"', r'"a\"b"', '"no_end', '"a\nb"', 'plain']),
            (r"//[^\n]*", ["//", "// hello world", "/ not comment", "//a\nb"]),
        ]
        for pat, samples in patterns_and_samples:
            nfa, _ = build_token_nfa(pat, "T")
            sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
            min_dfa = minimize_dfa(sub_dfa).minimized_dfa
            dir_dfa = build_direct_dfa(pat, "T").dfa

            oracle = _oracle_re.compile(f"^(?:{pat})$")
            for s in samples:
                expected = bool(oracle.match(s))
                ok_nfa, _, _ = nfa.simulate(s)
                ok_min, _, _ = min_dfa.simulate(s)
                ok_dir, _, _ = dir_dfa.simulate(s)
                self.assertEqual(ok_nfa, expected, f"NFA mismatch on {pat} with {s!r}")
                self.assertEqual(ok_min, expected, f"MinDFA mismatch on {pat} with {s!r}")
                self.assertEqual(ok_dir, expected, f"DirectDFA mismatch on {pat} with {s!r}")

    def test_nfa_vs_dfa_combined_crosscheck(self) -> None:
        """Verify Combined NFA and Minimized Combined DFA classify individual lexemes identically."""
        lex = LexicalAnalyzer.from_preset("minilang")
        lexemes = [
            "if", "else", "while", "ifx", "true", "false", "true1",
            "0", "42", "3.14", "2.5e-4", '"ok"', '""', "// hi",
            "==", "!=", "<=", ">=", "&&", "||", "=", "+", "/", ";",
            "@", "$", "3.", '"unclosed',
        ]
        report = verify_nfa_dfa_on_strings(lex.combined_nfa, lex.minimized_dfa, lexemes)
        self.assertTrue(report["all_passed"], f"Mismatches: {report['mismatches']}")

    def test_line_and_column_tracking(self) -> None:
        lex = LexicalAnalyzer.from_preset("minilang")
        src = "let a = 1;\n  if (a == 1) {\n    print(a);\n  }"
        res = lex.scan(src)
        self.assertEqual(len(res.errors), 0)
        by_lex = [(t.lexeme, t.line, t.col) for t in res.visible_tokens]
        self.assertEqual(by_lex[0], ("let", 1, 1))
        self.assertEqual(by_lex[4], (";", 1, 10))
        self.assertEqual(by_lex[5], ("if", 2, 3))
        self.assertEqual(by_lex[11], ("{", 2, 15))
        self.assertEqual(by_lex[12], ("print", 3, 5))

    def test_custom_spec_live_extension(self) -> None:
        """Verify adding a brand-new token rule (HEX_LIT) and priority swap works dynamically."""
        custom_specs = [
            TokenSpec("WS", r"[ \t\n\r]+", 1, True, "whitespace"),
            TokenSpec("HEX_LIT", r"0[xX][0-9a-fA-F]+", 2, False, "literal"),
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
        """Ensure nullable token pattern triggers warning and NEVER loops infinitely during scanning."""
        specs = [
            TokenSpec("BAD_NULLABLE", r"a*", 1, False, "other"),
            TokenSpec("B_TOK", r"b", 2, False, "other"),
        ]
        lex = LexicalAnalyzer.compile(specs)
        self.assertTrue(len(lex.warnings) >= 1)
        res = lex.scan("aabcb")
        # 'aa' matches BAD_NULLABLE, 'b' matches B_TOK, 'c' is LEXICAL_ERROR (NOT infinite loop!), 'b' matches B_TOK
        self.assertEqual([(t.token_type, t.lexeme) for t in res.visible_tokens], [("BAD_NULLABLE", "aa"), ("B_TOK", "b"), ("B_TOK", "b")])
        self.assertEqual(len(res.errors), 1)

    def test_jflap_xml_export_valid(self) -> None:
        """Verify exported JFLAP .jff XML is well-formed and has expected structure."""
        nfa, _ = build_token_nfa("(a|b)*abb", "SLIDE38")
        sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
        min_dfa = minimize_dfa(sub_dfa).minimized_dfa

        xml_nfa = export_nfa_to_jflap(nfa, expand_char_classes=True)
        root_nfa = ET.fromstring(xml_nfa)
        self.assertEqual(root_nfa.findtext("type"), "fa")
        self.assertEqual(len(root_nfa.findall("./automaton/state")), 11)

        xml_dfa = export_dfa_to_jflap(min_dfa, expand_char_classes=True)
        root_dfa = ET.fromstring(xml_dfa)
        self.assertEqual(root_dfa.findtext("type"), "fa")
        self.assertEqual(len(root_dfa.findall("./automaton/state")), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
