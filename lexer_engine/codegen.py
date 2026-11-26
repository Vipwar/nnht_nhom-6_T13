"""
Flex-style Standalone Table-Driven Python Lexer Generator (Zero `import re`).

Compiles any `DFA` (or `LexicalAnalyzer`) into a 100% self-contained, zero-dependency
Python source file implementing:
- Precomputed O(1) 128-entry ASCII equivalence-class lookup table (`ASCII_CLASS_MAP`)
- Dynamic Unicode code-point lookup table (`UNICODE_CLASS_MAP`) + `NON_ASCII_CLASS`
- Dense 2D integer transition matrix `TRANSITIONS[state][class_id]` (like Flex `yy_nxt`)
- Pre-baked token priority acceptance table `ACCEPT_TABLE[state]`
- Linear-time O(n) Maximal Munch driver with Reps (1998) `failed_states` memoization,
  exact CRLF/LF/CR `(line, col)` tracking, dual error recovery (`panic_char` & `smart_sync`),
  and a ready-to-run command-line interface (`python generated_lexer.py <source_file>`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

from .models import DFA, NON_ASCII

if TYPE_CHECKING:
    from . import LexicalAnalyzer


def _sanitize_identifier(raw: str, default: str = "GeneratedLexer") -> str:
    cleaned = "".join(ch if (ch.isascii() and (ch.isalnum() or ch == "_")) else "_" for ch in raw)
    cleaned = cleaned.strip("_")
    if not cleaned:
        return default
    if cleaned[0].isdigit():
        cleaned = "Lexer_" + cleaned
    return cleaned


def generate_standalone_lexer(
    target: "LexicalAnalyzer | DFA",
    class_name: str = "GeneratedLexer",
    preset_name: str = "custom",
) -> str:
    """
    Generate a 100% self-contained, zero-dependency Python lexer module from a compiled
    `LexicalAnalyzer` or `DFA`.
    """
    if isinstance(target, DFA):
        dfa = target
        rule_count = len({info.token_name for info in dfa.accept_states.values()})
    else:
        dfa = target.minimized_dfa
        rule_count = len(target.specs)

    cls_name = _sanitize_identifier(class_name, "GeneratedLexer")
    num_states = len(dfa.states)
    num_classes = len(dfa.char_classes)

    if sorted(dfa.states) != list(range(num_states)):
        raise ValueError("DFA states must be canonically numbered 0..N-1 before code generation.")

    # 1. Build 128-entry ASCII character-to-class table (-1 = unmapped/dead)
    ascii_map: List[int] = [-1] * 128
    unicode_map: Dict[int, int] = {ord(u): -1 for u in sorted(dfa.unicode_chars, key=ord)}
    non_ascii_class: int = -1

    for cid, cset in enumerate(dfa.char_classes):
        for ch in cset:
            if ch == NON_ASCII:
                non_ascii_class = cid
            elif ord(ch) < 128:
                ascii_map[ord(ch)] = cid
            else:
                unicode_map[ord(ch)] = cid

    # 2. Build dense 2D transition matrix TRANSITIONS[state][cid] -> next_state (-1 = dead)
    trans_rows: List[Tuple[int, ...]] = []
    for st in range(num_states):
        row_dict = dfa.transitions.get(st, {})
        trans_rows.append(tuple(row_dict.get(cid, -1) for cid in range(num_classes)))

    # 3. Build accept lookup table: state -> (token_name, priority, skip, category)
    accept_entries: Dict[int, Tuple[str, int, bool, str]] = {}
    for st in sorted(dfa.accept_states.keys()):
        acc = dfa.accept_states[st]
        accept_entries[st] = (acc.token_name, acc.priority, acc.skip, acc.category)

    # Format tables cleanly for readable generated Python code
    ascii_chunks = [
        "    " + ", ".join(f"{v:>3d}" for v in ascii_map[i : i + 16]) + ","
        for i in range(0, 128, 16)
    ]
    ascii_block = "(\n" + "\n".join(ascii_chunks) + "\n)"

    unicode_items = [f"    0x{code:04X}: {cid}," for code, cid in sorted(unicode_map.items())]
    unicode_block = "{\n" + "\n".join(unicode_items) + "\n}" if unicode_items else "{}"

    trans_lines = [
        f"    ({', '.join(str(x) for x in row) + (',' if len(row) == 1 else '')}),  # D{st}"
        for st, row in enumerate(trans_rows)
    ]
    trans_block = "(\n" + "\n".join(trans_lines) + "\n)"

    accept_lines = [
        f"    {st}: ({tname!r}, {prio}, {skip!r}, {cat!r}),"
        for st, (tname, prio, skip, cat) in accept_entries.items()
    ]
    accept_block = "{\n" + "\n".join(accept_lines) + "\n}" if accept_lines else "{}"

    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-generated Standalone Table-Driven Lexical Analyzer ({cls_name}).

Spec / Preset : {preset_name} ({rule_count} token rules -> {num_states} Minimized DFA states, {num_classes} char classes)
Generator     : T13 Automata-based Lexical Analyzer (UEH Formal Languages)
Dependencies  : 100% Python Standard Library ONLY (Zero `import re`, Zero external packages).

Algorithm:
- O(1) table-driven DFA transition matrix (`ASCII_CLASS_MAP`, `UNICODE_CLASS_MAP`, `TRANSITIONS`)
- Maximal Munch (Longest Prefix Match) + Deterministic Rule Priority
- Reps (1998) `failed_states` memoization guaranteeing strict O(n) linear-time complexity
- Dual Lexical Error Recovery (`panic_char` and `smart_sync`)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

START_STATE: int = {dfa.start_state}
NON_ASCII_CLASS: int = {non_ascii_class}

# 128-entry O(1) lookup table for 7-bit ASCII (0x00..0x7F) -> equivalence class ID (-1 = dead)
ASCII_CLASS_MAP: Tuple[int, ...] = {ascii_block}

# Explicit Unicode code-point lookup table (code point >= 0x80) -> equivalence class ID (-1 = excluded)
UNICODE_CLASS_MAP: Dict[int, int] = {unicode_block}

# Dense 2D DFA transition table: TRANSITIONS[state][class_id] -> next_state (-1 = dead)
TRANSITIONS: Tuple[Tuple[int, ...], ...] = {trans_block}

# Accepting state metadata: state -> (token_name, priority, skip, category)
ACCEPT_TABLE: Dict[int, Tuple[str, int, bool, str]] = {accept_block}


@dataclass
class Token:
    token_type: str
    lexeme: str
    line: int
    col: int
    start_pos: int
    end_pos: int
    category: str = "other"
    skipped: bool = False
    accept_state: int = -1
    backtrack_steps: int = 0

    def to_dict(self) -> Dict:
        return {{
            "type": self.token_type,
            "lexeme": self.lexeme,
            "line": self.line,
            "col": self.col,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "length": self.end_pos - self.start_pos,
            "category": self.category,
            "skipped": self.skipped,
            "accept_state": self.accept_state,
            "backtrack_steps": self.backtrack_steps,
        }}


@dataclass
class LexicalError:
    char: str
    line: int
    col: int
    pos: int
    message: str
    attempted_lexeme: str = ""

    @property
    def lexeme(self) -> str:
        return self.char

    @property
    def start_pos(self) -> int:
        return self.pos

    @property
    def end_pos(self) -> int:
        return self.pos + len(self.char)

    def to_dict(self) -> Dict:
        return {{
            "char": self.char,
            "lexeme": self.char,
            "line": self.line,
            "col": self.col,
            "pos": self.pos,
            "start_pos": self.pos,
            "end_pos": self.pos + len(self.char),
            "message": self.message,
            "attempted_lexeme": self.attempted_lexeme,
        }}


@dataclass
class ScanResult:
    tokens: List[Token]
    visible_tokens: List[Token]
    errors: List[LexicalError]
    elapsed_ms: float
    total_chars: int
    total_transitions: int
    error_recovery_mode: str = "panic_char"
    memoized_cutoffs: int = 0

    def to_dict(self) -> Dict:
        return {{
            "tokens": [t.to_dict() for t in self.tokens],
            "visible_tokens": [t.to_dict() for t in self.visible_tokens],
            "errors": [e.to_dict() for e in self.errors],
            "stats": {{
                "elapsed_ms": round(self.elapsed_ms, 4),
                "total_chars": self.total_chars,
                "total_tokens_all": len(self.tokens),
                "visible_token_count": len(self.visible_tokens),
                "skipped_token_count": len(self.tokens) - len(self.visible_tokens),
                "error_count": len(self.errors),
                "total_transitions": self.total_transitions,
                "error_recovery_mode": self.error_recovery_mode,
                "memoized_cutoffs": self.memoized_cutoffs,
            }},
        }}


def _escape_char_display(ch: str) -> str:
    special = {{
        "\\n": "\\\\n",
        "\\t": "\\\\t",
        "\\r": "\\\\r",
        "\\v": "\\\\v",
        "\\f": "\\\\f",
        "\\0": "\\\\0",
        " ": "␣",
        "\\\\": "\\\\\\\\",
    }}
    if ch in special:
        return special[ch]
    code = ord(ch)
    if code < 32 or code == 127:
        return f"\\\\x{{code:02X}}"
    return ch


def _advance_line_col(text: str, start: int, end: int, line: int, col: int) -> Tuple[int, int]:
    n = len(text)
    for i in range(start, end):
        ch = text[i]
        if ch == "\\n":
            line += 1
            col = 1
        elif ch == "\\r":
            if i + 1 < n and text[i + 1] == "\\n":
                pass
            else:
                line += 1
                col = 1
        else:
            col += 1
    return line, col


class {cls_name}:
    """Standalone O(n) table-driven lexical scanner generated from Minimized Multi-token DFA."""

    @staticmethod
    def step(state: int, ch: str) -> int:
        code = ord(ch)
        if code < 128:
            cid = ASCII_CLASS_MAP[code]
        elif code in UNICODE_CLASS_MAP:
            cid = UNICODE_CLASS_MAP[code]
        else:
            cid = NON_ASCII_CLASS
        if cid < 0:
            return -1
        return TRANSITIONS[state][cid]

    def scan(self, text: str, error_recovery: str = "panic_char") -> ScanResult:
        if error_recovery not in ("panic_char", "smart_sync"):
            raise ValueError(f"Invalid error_recovery mode: {{error_recovery!r}}")

        t0 = time.perf_counter()
        tokens: List[Token] = []
        visible_tokens: List[Token] = []
        errors: List[LexicalError] = []
        failed_states: Set[Tuple[int, int]] = set()
        memoized_cutoffs = 0

        pos = 0
        line = 1
        col = 1
        n = len(text)
        total_transitions = 0

        while pos < n:
            cur_state = START_STATE
            cursor = pos
            last_accept: Optional[Tuple[int, int, Tuple[str, int, bool, str]]] = None
            visited_since_accept: List[Tuple[int, int]] = []

            while cursor < n:
                ch = text[cursor]
                nxt = self.step(cur_state, ch)
                total_transitions += 1
                if nxt < 0:
                    break
                cur_state = nxt
                cursor += 1

                if (cur_state, cursor) in failed_states:
                    memoized_cutoffs += 1
                    visited_since_accept.append((cur_state, cursor))
                    break

                acc = ACCEPT_TABLE.get(cur_state)
                if acc is not None:
                    last_accept = (cursor, cur_state, acc)
                    visited_since_accept.clear()
                else:
                    visited_since_accept.append((cur_state, cursor))

            if visited_since_accept:
                failed_states.update(visited_since_accept)

            is_unclosed_block_comment = (
                text[pos : pos + 2] == "/*"
                and cursor >= pos + 2
                and (last_accept is None or last_accept[0] == pos + 1)
            )
            if is_unclosed_block_comment:
                last_accept = None

            if last_accept is not None and last_accept[0] > pos:
                end_pos, acc_state, (tok_name, _prio, is_skip, category) = last_accept
                backtrack = cursor - end_pos
                lexeme = text[pos:end_pos]
                tok = Token(
                    token_type=tok_name,
                    lexeme=lexeme,
                    line=line,
                    col=col,
                    start_pos=pos,
                    end_pos=end_pos,
                    category=category,
                    skipped=is_skip,
                    accept_state=acc_state,
                    backtrack_steps=backtrack,
                )
                tokens.append(tok)
                if not is_skip:
                    visible_tokens.append(tok)
                line, col = _advance_line_col(text, pos, end_pos, line, col)
                pos = end_pos
            else:
                bad_ch = text[pos]
                if error_recovery == "smart_sync":
                    if is_unclosed_block_comment:
                        sync_end = n
                    elif bad_ch == \'"\' or (bad_ch == "\'" and cursor > pos + 1):
                        sync_end = max(cursor, pos + 1)
                        while sync_end < n and text[sync_end] not in ("\\n", "\\r"):
                            sync_end += 1
                    else:
                        sync_end = pos + 1
                else:
                    sync_end = pos + 1

                consumed_err = text[pos:sync_end]
                display_attempt = text[pos : max(cursor, sync_end)]

                if is_unclosed_block_comment:
                    msg = (
                        f"Bình luận nhiều dòng \'/*\' chưa được đóng (unterminated block comment) "
                        f"bắt đầu bằng \'{{display_attempt[:24]}}\' tại dòng {{line}}, cột {{col}}"
                    )
                elif bad_ch == \'"\' or (bad_ch == "\'" and cursor > pos + 1):
                    msg = (
                        f"Chuỗi ký tự chưa được đóng (unterminated string) bắt đầu bằng "
                        f"\'{{display_attempt[:24]}}\' tại dòng {{line}}, cột {{col}}"
                    )
                elif cursor > pos:
                    msg = (
                        f"Từ tố không hoàn chỉnh \'{{display_attempt[:24]}}\' không đạt trạng thái kết thúc "
                        f"(bắt đầu bởi \'{{_escape_char_display(bad_ch)}}\') tại dòng {{line}}, cột {{col}}"
                    )
                else:
                    msg = (
                        f"Ký tự không hợp lệ \'{{_escape_char_display(bad_ch)}}\' "
                        f"(mã U+{{ord(bad_ch):04X}}) tại dòng {{line}}, cột {{col}}"
                    )

                errors.append(
                    LexicalError(
                        char=consumed_err if error_recovery == "smart_sync" else bad_ch,
                        line=line,
                        col=col,
                        pos=pos,
                        message=msg,
                        attempted_lexeme=display_attempt,
                    )
                )
                line, col = _advance_line_col(text, pos, sync_end, line, col)
                pos = sync_end

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return ScanResult(
            tokens=tokens,
            visible_tokens=visible_tokens,
            errors=errors,
            elapsed_ms=elapsed_ms,
            total_chars=n,
            total_transitions=total_transitions,
            error_recovery_mode=error_recovery,
            memoized_cutoffs=memoized_cutoffs,
        )


def tokenize(text: str, error_recovery: str = "panic_char") -> ScanResult:
    """Convenience entry point for tokenizing a string with `{cls_name}`."""
    return {cls_name}().scan(text, error_recovery=error_recovery)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Standalone Table-Driven Lexer ({cls_name})")
    parser.add_argument("file", nargs="?", help="Input source file path")
    parser.add_argument("--code", help="Inline source string to scan")
    parser.add_argument(
        "--error-recovery",
        choices=["panic_char", "smart_sync"],
        default="panic_char",
        help="Lexical error recovery mode",
    )
    parser.add_argument("--include-skipped", action="store_true", help="Include skipped tokens")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args(argv)

    if args.file:
        src = Path(args.file).read_text(encoding="utf-8")
    elif args.code is not None:
        src = args.code
    else:
        src = sys.stdin.read()

    res = tokenize(src, error_recovery=args.error_recovery)
    if args.json:
        print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return 0 if not res.errors else 1

    tok_list = res.tokens if args.include_skipped else res.visible_tokens
    for idx, tok in enumerate(tok_list, start=1):
        print(f"{{idx:>4}}  {{tok.token_type:<16}} {{tok.lexeme!r:<24}} ({{tok.line}}:{{tok.col}})")
    for err in res.errors:
        print(f"[ERROR {{err.line}}:{{err.col}}] {{err.message}}", file=sys.stderr)
    return 0 if not res.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
