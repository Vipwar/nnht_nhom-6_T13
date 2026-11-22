"""
Command-Line Interface for Topic T13: Automata-based Lexical Analyzer.

Usage examples:
  python cli.py scan --preset minilang --file data/samples/demo_minilang_valid.mini
  python cli.py scan --preset calclang --code "let x = 3.14 + 2; print(x == 5.14);"
  python cli.py inspect "(a|b)*abb" --test abb aabb ab aba
  python cli.py benchmark
  python cli.py export-jff --preset calclang --out data/jflap_exports/calclang_min_dfa.jff
  python cli.py test
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import List

from lexer_engine import (
    PRESETS,
    LexicalAnalyzer,
    TokenSpec,
    build_combined_direct_dfa,
    build_direct_dfa,
    check_dfa_equivalence,
    compare_regex_equivalence,
    eliminate_epsilon,
    export_dfa_to_jflap,
    export_nfa_to_jflap,
    inspect_single_regex,
)
from lexer_engine.thompson import build_token_nfa
from tests.test_suite import run_json_test_report


def _load_specs_file(path: Path) -> List[TokenSpec]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw["tokens"] if isinstance(raw, dict) and "tokens" in raw else raw
    return [
        TokenSpec(
            name=item["name"],
            pattern=item["pattern"],
            priority=item.get("priority", idx + 1),
            skip=item.get("skip", False),
            category=item.get("category", "other"),
            description=item.get("description", ""),
        )
        for idx, item in enumerate(items)
    ]


def cmd_scan(args: argparse.Namespace) -> int:
    if args.spec:
        specs = _load_specs_file(Path(args.spec))
        lex = LexicalAnalyzer.compile(specs)
        spec_label = args.spec
    else:
        lex = LexicalAnalyzer.from_preset(args.preset)
        spec_label = f"preset:{args.preset}"

    if args.file:
        source = Path(args.file).read_text(encoding="utf-8")
    elif args.code is not None:
        source = args.code
    else:
        source = PRESETS[args.preset]["samples"]["valid"]["code"]

    summary = lex.summary_dict()
    result = lex.scan(
        source,
        use_minimized=not args.unminimized,
        record_traces=args.trace,
        error_recovery=args.error_recovery,
    )

    print("=" * 84)
    print(f"T13 AUTOMATA-BASED LEXICAL ANALYZER | Spec: {spec_label}")
    print("=" * 84)
    print(
        f"Automata Pipeline: {summary['token_count']} token REs "
        f"-> ε-NFA ({summary['nfa_states']} states) "
        f"-> NFA khử ε ({summary['eps_free_nfa_states']} states) "
        f"-> Subset DFA ({summary['subset_dfa_states']} states) "
        f"-> Min-DFA ({summary['minimized_dfa_states']} states, -{summary['state_reduction_percent']}%)"
    )
    print(
        f"Alphabet Classes: {summary['char_class_count']} | "
        f"Compile: {summary['timings_ms']['total_ms']:.2f} ms | "
        f"Subset≡Min: {'PASS' if summary['equivalence']['equivalent'] else 'FAIL'} | "
        f"Moore≡Hopcroft: {'PASS' if summary['moore_vs_hopcroft']['equivalent'] else 'FAIL'} | "
        f"Myhill-Nerode Minimal: {'PASS' if summary['minimality']['is_minimal'] else 'FAIL'}"
    )
    if lex.warnings:
        print("-" * 84)
        print(f"COMPILER WARNINGS ({len(lex.warnings)}):")
        for w in lex.warnings:
            print(f"  [!] {w}")
    print("-" * 84)
    print(f"{'#':>3}  {'TYPE':<16} {'LEXEME':<24} {'POS (L:C)':<10} {'STATE':<7} {'BACKTRACK'}")
    print("-" * 84)
    tok_list = result.tokens if args.include_skipped else result.visible_tokens
    for idx, tok in enumerate(tok_list, start=1):
        lex_disp = repr(tok.lexeme)
        if len(lex_disp) > 22:
            lex_disp = lex_disp[:19] + "...'"
        skip_tag = " [skip]" if tok.skipped else ""
        print(
            f"{idx:>3}  {tok.token_type:<16} {lex_disp:<24} "
            f"{tok.line}:{tok.col:<7} D{tok.accept_state:<6} {tok.backtrack_steps}{skip_tag}"
        )

    if result.errors:
        print("-" * 84)
        print(f"LEXICAL ERRORS ({len(result.errors)}) [mode={result.error_recovery_mode}]:")
        for e in result.errors:
            print(f"  [Line {e.line}, Col {e.col}] {e.message}")

    print("=" * 84)
    print(
        f"Scanned {result.total_chars} chars in {result.elapsed_ms:.3f} ms | "
        f"{len(result.visible_tokens)} visible tokens | {len(result.errors)} errors | "
        f"{result.total_transitions} DFA transitions | {result.memoized_cutoffs} memoized cutoffs"
    )
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Saved JSON result to: {args.json_out}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    info = inspect_single_regex(args.pattern, token_name=args.name, test_strings=args.test or [])
    print("=" * 84)
    print(f"SINGLE REGEX PIPELINE INSPECTOR: {args.name} = {args.pattern}")
    print("=" * 84)
    print(f"Explicit Infix : {info['explicit_infix']}")
    print(f"Postfix        : {info['postfix']}")
    print(f"Nullable (ε∈L) : {info['nullable']}")
    print(
        f"State Counts   : Thompson ε-NFA = {info['nfa']['state_count']} "
        f"| ε-free NFA (ĐL 2) = {info['eps_free_nfa']['state_count']} "
        f"| Subset DFA = {info['subset_dfa']['state_count']} "
        f"| Direct DFA = {info['direct_dfa']['dfa']['state_count']} "
        f"| Moore Min-DFA = {info['minimized_dfa']['state_count']} "
        f"| Hopcroft Min-DFA = {info['hopcroft_minimization']['minimized_state_count']}"
    )
    print(f"Subset ≡ Min   : {info['equivalence']['subset_vs_minimized']['message']}")
    print(f"Subset ≡ Direct: {info['equivalence']['subset_vs_direct']['message']}")
    print(f"Moore ≡ Hopcr. : {info['equivalence']['moore_vs_hopcroft']['message']}")
    print(f"Myhill-Nerode  : {info['minimality']['message']}")

    print("\n--- Direct RE -> DFA Followpos Table ---")
    for row in info["direct_dfa"]["followpos_table"]:
        print(f"  pos {row['position']:>2} ({row['symbol']:<10}) -> followpos = {row['followpos']}")

    print("\n--- Minimization Partitions (Moore) ---")
    for step in info["minimization"]["partition_history"]:
        groups_str = ", ".join("{" + ",".join(g["states"]) + "}" for g in step["groups"])
        print(f"  Π_{step['iteration']}: {groups_str}")

    if info["string_tests"]:
        print("\n--- String Membership Tests ---")
        for st in info["string_tests"]:
            verdict = "ACCEPT" if st["min_dfa_accepted"] else "REJECT"
            sync = "OK (εNFA=NFA=SubDFA=DirDFA=MinDFA)" if st["consistent"] else "MISMATCH!"
            print(f"  {st['input']!r:<16} -> {verdict:<6} | {sync}")
    return 0


def cmd_benchmark(_args: argparse.Namespace) -> int:
    print("=" * 108)
    print("BENCHMARK: AUTOMATA COMPILATION (6-WAY) & LINEAR-TIME O(n) SCANNER PERFORMANCE")
    print("=" * 108)
    print(
        f"{'Preset':<10} {'Tok':>4} {'ε-NFA':>6} {'No-ε':>6} {'SubDFA':>7} {'DirDFA':>7} {'MinDFA':>7} "
        f"{'Moore(ms)':>10} {'Hopcr(ms)':>10} {'Scan10KB(ms)':>15} {'Myhill-Nerode':>14}"
    )
    print("-" * 108)
    for pid, pinfo in PRESETS.items():
        lex = LexicalAnalyzer.from_preset(pid)
        s = lex.summary_dict()
        combined_direct = build_combined_direct_dfa(lex.specs)
        eq_dir = check_dfa_equivalence(lex.minimized_dfa, combined_direct, check_token_names=True)
        assert eq_dir.equivalent

        base_code = pinfo["samples"]["valid"]["code"]
        repeats = max(1, 10240 // max(1, len(base_code)))
        big_code = (base_code + "\n") * repeats
        t0 = time.perf_counter()
        res = lex.scan(big_code, use_minimized=True, record_traces=False)
        scan_ms = (time.perf_counter() - t0) * 1000.0
        moore_ms = s["timings_ms"].get("minimize_ms", 0.0)
        hop_ms = s["timings_ms"].get("hopcroft_ms", 0.0)
        mn_pairs = f"{s['minimality']['distinguishable_pairs']}/{s['minimality']['total_pairs']}✓"
        print(
            f"{pid:<10} {s['token_count']:>4} {s['nfa_states']:>6} {s['eps_free_nfa_states']:>6} "
            f"{s['subset_dfa_states']:>7} {len(combined_direct.states):>7} {s['minimized_dfa_states']:>7} "
            f"{moore_ms:>10.3f} {hop_ms:>10.3f} "
            f"{scan_ms:>8.2f} ({len(res.visible_tokens):>4}t) {mn_pairs:>14}"
        )

    print("-" * 108)
    ml = LexicalAnalyzer.from_preset("minilang")
    for label, s_in in [
        ("Anti-O(n²) Stress: 10k unclosed string (\" + 'a'*10000)", '"' + "a" * 10000),
        ("Anti-O(n²) Stress: 10k unclosed comment (/* + 'x'*10000)", "/*" + "x" * 10000),
        ("Anti-O(n²) Stress: 10k escaped quotes (\" + '\\\"'*5000)", '"' + '\\"' * 5000),
    ]:
        t0 = time.perf_counter()
        r_p = ml.scan(s_in, record_traces=False, error_recovery="panic_char")
        dt_p = (time.perf_counter() - t0) * 1000.0
        t1 = time.perf_counter()
        r_s = ml.scan(s_in, record_traces=False, error_recovery="smart_sync")
        dt_s = (time.perf_counter() - t1) * 1000.0
        print(
            f"  {label:<56} -> panic_char: {dt_p:>6.2f} ms (cutoffs={r_p.memoized_cutoffs:>4}) | smart_sync: {dt_s:>6.2f} ms"
        )
    print("=" * 108)
    return 0


def cmd_export_jff(args: argparse.Namespace) -> int:
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if args.pattern:
        nfa, _ = build_token_nfa(args.pattern, args.name)
        if args.stage == "nfa":
            xml_str = export_nfa_to_jflap(nfa, expand_char_classes=args.expand)
        elif args.stage == "eps_free_nfa":
            xml_str = export_nfa_to_jflap(eliminate_epsilon(nfa), expand_char_classes=args.expand)
        elif args.stage == "direct_dfa":
            dir_res = build_direct_dfa(args.pattern, token_name=args.name)
            xml_str = export_dfa_to_jflap(dir_res.dfa, expand_char_classes=args.expand)
        else:
            from lexer_engine.dfa_minimizer import minimize_dfa
            from lexer_engine.subset_construction import nfa_to_dfa

            sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
            target = minimize_dfa(sub_dfa).minimized_dfa if args.stage == "min_dfa" else sub_dfa
            xml_str = export_dfa_to_jflap(target, expand_char_classes=args.expand)
    else:
        lex = LexicalAnalyzer.from_preset(args.preset)
        if args.stage == "nfa":
            xml_str = export_nfa_to_jflap(lex.combined_nfa, expand_char_classes=args.expand)
        elif args.stage == "eps_free_nfa":
            xml_str = export_nfa_to_jflap(lex.eps_free_nfa, expand_char_classes=args.expand)
        elif args.stage == "subset_dfa":
            xml_str = export_dfa_to_jflap(lex.subset_dfa, expand_char_classes=args.expand)
        elif args.stage == "direct_dfa":
            xml_str = export_dfa_to_jflap(build_combined_direct_dfa(lex.specs), expand_char_classes=args.expand)
        else:
            xml_str = export_dfa_to_jflap(lex.minimized_dfa, expand_char_classes=args.expand)

    out_path.write_text(xml_str, encoding="utf-8")
    print(f"Exported JFLAP file ({args.stage}) -> {out_path}")
    return 0


def cmd_equiv(args: argparse.Namespace) -> int:
    res = compare_regex_equivalence(args.pattern_a, args.pattern_b)
    print("=" * 84)
    print(f"REGEX EQUIVALENCE VERIFIER: R1 = {args.pattern_a}  vs  R2 = {args.pattern_b}")
    print("=" * 84)
    print(f"R1 Min-DFA States : {res['min_dfa_a_states']}")
    print(f"R2 Min-DFA States : {res['min_dfa_b_states']}")
    print(f"Equivalent (L1=L2): {'YES (TƯƠNG ĐƯƠNG 100%)' if res['equivalent'] else 'NO (KHÔNG TƯƠNG ĐƯƠNG)'}")
    print(f"Detail            : {res['message']}")
    if not res["equivalent"] and res.get("counterexample") is not None:
        print(f"Shortest Witness  : {res['counterexample']!r}")
    print("=" * 84)
    return 0


def cmd_test(_args: argparse.Namespace) -> int:
    report = run_json_test_report()
    print("=" * 84)
    print(f"AUTOMATED TEST REPORT: {report['passed']}/{report['total']} PASSED ({report['pass_rate']}%)")
    print("=" * 84)
    for item in report["results"]:
        mark = "PASS" if item["passed"] else "FAIL"
        print(f"[{mark}] {item['id']:<10} ({item['category']:<7}) {item['name']}")
        print(f"       -> {item['detail']}")
    print("=" * 84)
    return 0 if report["failed"] == 0 else 1


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="T13: Automata-based Lexical Analyzer CLI (Zero `re`, 100% pure Automata)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Scan source code into lexical tokens")
    p_scan.add_argument("--preset", choices=list(PRESETS.keys()), default="minilang")
    p_scan.add_argument("--spec", help="Path to custom JSON token specification file")
    p_scan.add_argument("--file", help="Source code file to scan")
    p_scan.add_argument("--code", help="Inline source code string to scan")
    p_scan.add_argument("--unminimized", action="store_true", help="Use Subset DFA instead of Minimized DFA")
    p_scan.add_argument("--include-skipped", action="store_true", help="Show skipped tokens (whitespace/comments)")
    p_scan.add_argument("--trace", action="store_true", help="Record execution traces")
    p_scan.add_argument(
        "--error-recovery",
        "--recovery",
        dest="error_recovery",
        choices=["panic_char", "smart_sync"],
        default="panic_char",
        help="Lexical error recovery strategy (panic_char or smart_sync)",
    )
    p_scan.add_argument("--json-out", help="Write full scan result to JSON file")
    p_scan.set_defaults(func=cmd_scan)

    p_insp = sub.add_parser("inspect", help="Inspect full RE -> NFA -> Subset/Direct/Min DFA pipeline")
    p_insp.add_argument("pattern", help="Regular expression to analyze")
    p_insp.add_argument("--name", default="TOKEN", help="Token label")
    p_insp.add_argument("--test", nargs="*", help="Test strings to simulate")
    p_insp.set_defaults(func=cmd_inspect)

    p_equiv = sub.add_parser("equiv", help="Prove equivalence L(R1) == L(R2) via Product Automaton")
    p_equiv.add_argument("pattern_a", help="First regular expression R1")
    p_equiv.add_argument("pattern_b", help="Second regular expression R2")
    p_equiv.set_defaults(func=cmd_equiv)

    p_bench = sub.add_parser("benchmark", help="Benchmark compile & scan performance on all presets")
    p_bench.set_defaults(func=cmd_benchmark)

    p_jff = sub.add_parser("export-jff", help="Export NFA/DFA to JFLAP .jff XML")
    p_jff.add_argument("--preset", choices=list(PRESETS.keys()), default="calclang")
    p_jff.add_argument("--pattern", help="Single RE pattern instead of preset")
    p_jff.add_argument("--name", default="TOKEN")
    p_jff.add_argument(
        "--stage",
        choices=["nfa", "eps_free_nfa", "subset_dfa", "direct_dfa", "min_dfa"],
        default="min_dfa",
    )
    p_jff.add_argument("--expand", action="store_true", help="Expand char classes to single-char transitions")
    p_jff.add_argument("--out", required=True, help="Output .jff path")
    p_jff.set_defaults(func=cmd_export_jff)

    p_test = sub.add_parser("test", help="Run all structured test cases")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
