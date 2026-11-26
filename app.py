"""
Web Server & REST API for Topic T13: Automata-based Lexical Analyzer.

Zero third-party dependencies (uses Python standard library `http.server` only).
Run:
    python app.py
Opens web interface at http://127.0.0.1:8000 (or cloud PORT/HOST automatically).
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parent
WEB_DIR = PROJECT_ROOT / "web"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lexer_engine import (  # noqa: E402
    PRESETS,
    SINGLE_REGEX_EXAMPLES,
    LexicalAnalyzer,
    RegexSyntaxError,
    TokenSpec,
    build_combined_direct_dfa,
    check_dfa_equivalence,
    compare_regex_equivalence,
    eliminate_epsilon,
    export_dfa_to_jflap,
    export_nfa_to_jflap,
    generate_standalone_lexer,
    inspect_single_regex,
)
from lexer_engine.dfa_minimizer import minimize_dfa  # noqa: E402
from lexer_engine.subset_construction import nfa_to_dfa  # noqa: E402
from lexer_engine.thompson import build_token_nfa  # noqa: E402
from tests.test_suite import run_json_test_report  # noqa: E402


class ServerState:
    """Thread-safe holder for the currently active compiled LexicalAnalyzer."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.preset_id: str = "minilang"
        self.analyzer: LexicalAnalyzer = LexicalAnalyzer.from_preset("minilang")

    def compile_preset(self, preset_id: str) -> LexicalAnalyzer:
        with self._lock:
            self.analyzer = LexicalAnalyzer.from_preset(preset_id)
            self.preset_id = preset_id
            return self.analyzer

    def compile_custom(self, raw_specs: List[Dict[str, Any]]) -> LexicalAnalyzer:
        specs: List[TokenSpec] = []
        seen_names = set()
        for idx, item in enumerate(raw_specs):
            name = str(item.get("name", "")).strip()
            pattern = str(item.get("pattern", ""))
            if not name:
                raise ValueError(f"Quy tắc dòng #{idx + 1} bị thiếu tên token.")
            if name in seen_names:
                raise ValueError(f"Trùng tên token '{name}'. Mỗi quy tắc cần có tên duy nhất.")
            seen_names.add(name)
            specs.append(
                TokenSpec(
                    name=name,
                    pattern=pattern,
                    priority=int(item.get("priority", idx + 1)),
                    skip=bool(item.get("skip", False)),
                    category=str(item.get("category", "other")),
                    description=str(item.get("description", "")),
                )
            )
        specs.sort(key=lambda s: s.priority)
        compiled = LexicalAnalyzer.compile(specs)
        with self._lock:
            self.analyzer = compiled
            self.preset_id = "custom"
            return self.analyzer

    def get_analyzer(self) -> LexicalAnalyzer:
        with self._lock:
            return self.analyzer


STATE = ServerState()


def _presets_payload() -> Dict[str, Any]:
    out = {}
    for pid, pinfo in PRESETS.items():
        out[pid] = {
            "id": pinfo["id"],
            "name": pinfo["name"],
            "description": pinfo["description"],
            "specs": [s.to_dict() for s in pinfo["specs"]],
            "samples": pinfo["samples"],
        }
    return {
        "presets": out,
        "single_regex_examples": SINGLE_REGEX_EXAMPLES,
        "active_preset": STATE.preset_id,
    }


def _automata_payload(analyzer: LexicalAnalyzer) -> Dict[str, Any]:
    return {
        "preset_id": STATE.preset_id,
        "specs": [s.to_dict() for s in analyzer.specs],
        "summary": analyzer.summary_dict(),
        "minimization": analyzer.minimization.to_dict(),
        "hopcroft_minimization": analyzer.hopcroft_minimization.to_dict(),
        "minimality": analyzer.minimality_proof.to_dict(),
        "moore_vs_hopcroft": analyzer.moore_vs_hopcroft_equivalence.to_dict(),
        "intersections": analyzer.intersection_analysis.to_dict(),
        "shadowed_rules": analyzer.shadowed_rules,
        "warnings": analyzer.warnings,
        "minimized_dfa": analyzer.minimized_dfa.to_graph_dict(),
        "minimized_table": analyzer.minimized_dfa.to_transition_table(),
        "subset_dfa": analyzer.subset_dfa.to_graph_dict(),
        "subset_table": analyzer.subset_dfa.to_transition_table(),
        "combined_nfa": analyzer.combined_nfa.to_graph_dict(),
        "eps_free_nfa": analyzer.eps_free_nfa.to_graph_dict(),
    }


def _benchmark_payload() -> Dict[str, Any]:
    rows = []
    for pid, pinfo in PRESETS.items():
        lex = LexicalAnalyzer.from_preset(pid)
        s = lex.summary_dict()

        t_dir0 = time.perf_counter()
        combined_direct = build_combined_direct_dfa(lex.specs)
        direct_ms = round((time.perf_counter() - t_dir0) * 1000.0, 3)
        eq_direct = check_dfa_equivalence(lex.minimized_dfa, combined_direct, check_token_names=True)

        base = pinfo["samples"]["valid"]["code"]
        repeats = max(1, 10240 // max(1, len(base)))
        big = (base + "\n") * repeats
        t0 = time.perf_counter()
        res = lex.scan(big, use_minimized=True, record_traces=False)
        scan_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        rows.append(
            {
                "preset": pid,
                "name": pinfo["name"],
                "tokens": s["token_count"],
                "nfa_states": s["nfa_states"],
                "eps_free_nfa_states": s["eps_free_nfa_states"],
                "subset_dfa_states": s["subset_dfa_states"],
                "combined_direct_dfa_states": len(combined_direct.states),
                "minimized_dfa_states": s["minimized_dfa_states"],
                "hopcroft_dfa_states": s["hopcroft_dfa_states"],
                "reduction_percent": s["state_reduction_percent"],
                "char_classes": s["char_class_count"],
                "moore_ms": s["timings_ms"].get("minimize_ms", 0.0),
                "hopcroft_ms": s["timings_ms"].get("hopcroft_ms", 0.0),
                "direct_ms": direct_ms,
                "compile_ms": s["timings_ms"]["total_ms"],
                "scan_10kb_ms": scan_ms,
                "scan_10kb_tokens": len(res.visible_tokens),
                "equivalent": s["equivalence"]["equivalent"] and eq_direct.equivalent,
                "moore_hopcroft_equivalent": s["moore_vs_hopcroft"]["equivalent"],
                "direct_equivalent": eq_direct.equivalent,
                "is_minimal": s["minimality"]["is_minimal"],
                "minimality_pairs": f"{s['minimality']['distinguishable_pairs']}/{s['minimality']['total_pairs']}",
            }
        )

    # Anti-O(n^2) Linear-Time Maximal Munch Stress Tests on MiniLang
    ml = LexicalAnalyzer.from_preset("minilang")
    stress_cases = [
        ("Chuỗi chưa đóng 10.000 ký tự (\" + 'a'×10000)", '"' + "a" * 10000),
        ("Bình luận khối chưa đóng 10.000 ký tự (/* + 'x'×10000)", "/*" + "x" * 10000),
        ("Chuỗi escape bệnh lý chống O(n²) (\" + '\\\"'×5000)", '"' + '\\"' * 5000),
    ]
    stress_rows = []
    for label, payload_str in stress_cases:
        t0 = time.perf_counter()
        res_panic = ml.scan(payload_str, record_traces=False, error_recovery="panic_char")
        panic_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        t1 = time.perf_counter()
        res_smart = ml.scan(payload_str, record_traces=False, error_recovery="smart_sync")
        smart_ms = round((time.perf_counter() - t1) * 1000.0, 2)

        stress_rows.append(
            {
                "name": label,
                "length": len(payload_str),
                "panic_ms": panic_ms,
                "smart_ms": smart_ms,
                "memoized_cutoffs": res_panic.memoized_cutoffs,
                "panic_errors": len(res_panic.errors),
                "smart_errors": len(res_smart.errors),
                "passed": panic_ms < 200.0 and smart_ms < 200.0,
            }
        )

    return {"benchmarks": rows, "stress_tests": stress_rows}


class LexerHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Handler serving static SPA files + JSON REST API."""

    def log_message(self, format: str, *args: Any) -> None:
        # Keep console output clean during live demos
        pass

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _send_text(
        self,
        text: str,
        content_type: str = "text/plain; charset=utf-8",
        filename: str | None = None,
    ) -> None:
        raw = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        try:
            if path == "/api/presets":
                self._send_json(_presets_payload())
                return

            if path == "/api/automata":
                self._send_json(_automata_payload(STATE.get_analyzer()))
                return

            if path == "/api/tests":
                self._send_json(run_json_test_report())
                return

            if path == "/api/benchmark":
                self._send_json(_benchmark_payload())
                return

            if path == "/api/export-jflap":
                stage = qs.get("stage", ["min_dfa"])[0]
                pattern = qs.get("pattern", [None])[0]
                expand = qs.get("expand", ["false"])[0].lower() == "true"

                if pattern:
                    nfa, _ = build_token_nfa(pattern, "TOKEN")
                    if stage == "nfa":
                        xml_str = export_nfa_to_jflap(nfa, expand_char_classes=expand)
                    elif stage == "eps_free_nfa":
                        xml_str = export_nfa_to_jflap(eliminate_epsilon(nfa), expand_char_classes=expand)
                    else:
                        sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
                        target = minimize_dfa(sub_dfa).minimized_dfa if stage == "min_dfa" else sub_dfa
                        xml_str = export_dfa_to_jflap(target, expand_char_classes=expand)
                    fname = f"single_re_{stage}.jff"
                else:
                    lex = STATE.get_analyzer()
                    if stage == "nfa":
                        xml_str = export_nfa_to_jflap(lex.combined_nfa, expand_char_classes=expand)
                    elif stage == "eps_free_nfa":
                        xml_str = export_nfa_to_jflap(lex.eps_free_nfa, expand_char_classes=expand)
                    elif stage == "subset_dfa":
                        xml_str = export_dfa_to_jflap(lex.subset_dfa, expand_char_classes=expand)
                    else:
                        xml_str = export_dfa_to_jflap(lex.minimized_dfa, expand_char_classes=expand)
                    fname = f"{STATE.preset_id}_{stage}.jff"

                self._send_text(xml_str, "application/xml; charset=utf-8", filename=fname)
                return

            if path == "/api/export-lexer":
                lex = STATE.get_analyzer()
                pid = STATE.preset_id
                cls_map = {
                    "minilang": "MiniLangLexer",
                    "calclang": "CalcLangLexer",
                    "minisql": "MiniSQLLexer",
                }
                cls_name = qs.get("class_name", [cls_map.get(pid, "CustomLexer")])[0]
                py_code = generate_standalone_lexer(lex, class_name=cls_name, preset_name=pid)
                fname = f"{pid}_standalone_lexer.py"
                self._send_text(py_code, "text/x-python; charset=utf-8", filename=fname)
                return

            # Static files from web/
            rel = "index.html" if path in ("/", "") else path.lstrip("/")
            file_path = (WEB_DIR / rel).resolve()
            if not str(file_path).startswith(str(WEB_DIR.resolve())) or not file_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return

            ctype, _ = mimetypes.guess_type(str(file_path))
            if not ctype:
                ctype = "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
                ctype += "; charset=utf-8"

            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            body = self._read_json_body()

            if path == "/api/compile":
                if "preset_id" in body and body["preset_id"] in PRESETS and "specs" not in body:
                    lex = STATE.compile_preset(body["preset_id"])
                elif "specs" in body:
                    lex = STATE.compile_custom(body["specs"])
                else:
                    raise ValueError("Yêu cầu cung cấp 'preset_id' hoặc danh sách 'specs'.")
                self._send_json(_automata_payload(lex))
                return

            if path == "/api/scan":
                code = str(body.get("code", ""))
                use_minimized = bool(body.get("use_minimized", True))
                error_recovery = str(body.get("error_recovery", "panic_char"))
                if error_recovery not in ("panic_char", "smart_sync"):
                    error_recovery = "panic_char"
                lex = STATE.get_analyzer()
                res = lex.scan(
                    code,
                    use_minimized=use_minimized,
                    record_traces=True,
                    error_recovery=error_recovery,
                )
                self._send_json(res.to_dict())
                return

            if path == "/api/inspect-regex":
                pattern = str(body.get("pattern", ""))
                token_name = str(body.get("token_name", "TOKEN")).strip() or "TOKEN"
                test_strings = body.get("test_strings", [])
                if not isinstance(test_strings, list):
                    test_strings = []
                info = inspect_single_regex(
                    pattern,
                    token_name=token_name,
                    test_strings=[str(s) for s in test_strings],
                )
                self._send_json(info)
                return

            if path == "/api/compare-regex":
                pattern_a = str(body.get("pattern_a", ""))
                pattern_b = str(body.get("pattern_b", ""))
                self._send_json(compare_regex_equivalence(pattern_a, pattern_b))
                return

            if path == "/api/codegen":
                if "specs" in body:
                    lex = STATE.compile_custom(body["specs"])
                else:
                    lex = STATE.get_analyzer()
                pid = STATE.preset_id
                cls_map = {
                    "minilang": "MiniLangLexer",
                    "calclang": "CalcLangLexer",
                    "minisql": "MiniSQLLexer",
                }
                cls_name = str(body.get("class_name") or cls_map.get(pid, "CustomLexer"))
                py_code = generate_standalone_lexer(lex, class_name=cls_name, preset_name=pid)
                self._send_json(
                    {
                        "filename": f"{pid}_standalone_lexer.py",
                        "class_name": cls_name,
                        "code": py_code,
                        "state_count": len(lex.minimized_dfa.states),
                        "char_class_count": len(lex.minimized_dfa.char_classes),
                    }
                )
                return

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")
        except (RegexSyntaxError, ValueError, KeyError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": f"Lỗi xử lý máy chủ: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def run_server(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), LexerHTTPHandler)
    url = f"http://{host}:{port}"
    print("-" * 68)
    print("  De tai T13: Bo phan tich tu vung dua tren Automata (UEH)")
    print(f"  Dia chi truy cap : {url}")
    print("  Nhan Ctrl+C de dung may chu.")
    print("-" * 68)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDang dung may chu...")
    finally:
        server.server_close()


if __name__ == "__main__":
    is_cloud = bool(os.environ.get("PORT") or os.environ.get("CODESPACES") or os.environ.get("RENDER"))
    default_host = os.environ.get("HOST", "0.0.0.0" if is_cloud else "127.0.0.1")
    default_port = int(os.environ.get("PORT", "8000"))

    parser = argparse.ArgumentParser(description="Chay giao dien Web cho De tai T13")
    parser.add_argument("--host", default=default_host)
    parser.add_argument("--port", type=int, default=default_port)
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open web browser")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, open_browser=(not args.no_browser and not is_cloud))
