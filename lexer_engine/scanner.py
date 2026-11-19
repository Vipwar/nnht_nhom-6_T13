"""
Automata-based Lexical Scanner (Zero `import re`).

Implements the formal DFA-driven scanning engine (Dragon Book Section 3.5 / 3.7):
1. Maximal Munch (Longest Match):
   Starting at `pos`, advance through DFA states while transitions exist,
   recording the furthest accepting state (`last_accept_pos`, `last_accept_state`).
   When a dead transition or EOF is hit, backtrack to `last_accept_pos` and emit
   the longest valid token.
2. Rule Priority:
   Already baked deterministically into the Combined DFA's accepting states
   during Subset Construction (e.g., KEYWORD beats IDENTIFIER on "if").
3. Line & Column Tracking:
   Tracks 1-based (line, col) accurately across '\n' and multi-line lexemes.
4. Panic-mode Error Recovery:
   If no non-empty prefix matches at `pos`, record a detailed LexicalError
   (including partial attempted path, e.g., unterminated string literal `"abc`!)
   and advance by 1 character (or skip to recovery point) to continue scanning.
5. Full Step-by-Step Execution Trace:
   Records every state transition, accept update, dead transition, and backtrack
   event so the Web UI can animate the DFA live on any source program.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

from .models import (
    DFA,
    AcceptInfo,
    LexicalError,
    ScanResult,
    Token,
    TokenTrace,
    escape_char_display,
)


def _advance_line_col(text: str, start: int, end: int, line: int, col: int) -> Tuple[int, int]:
    """Update 1-based (line, col) after consuming text[start:end]."""
    for i in range(start, end):
        if text[i] == "\n":
            line += 1
            col = 1
        else:
            col += 1
    return line, col


def scan_source(
    text: str,
    dfa: DFA,
    record_traces: bool = True,
    max_traces: int = 500,
) -> ScanResult:
    """
    Tokenize `text` using the compiled Deterministic Finite Automaton `dfa`.
    """
    t0 = time.perf_counter()

    tokens: List[Token] = []
    visible_tokens: List[Token] = []
    errors: List[LexicalError] = []
    traces: List[TokenTrace] = []

    pos = 0
    line = 1
    col = 1
    n = len(text)
    total_transitions = 0
    trace_idx = 0

    while pos < n:
        cur_state: Optional[int] = dfa.start_state
        cursor = pos
        last_accept: Optional[Tuple[int, int, AcceptInfo]] = None

        steps: List[Dict] = []
        if record_traces and trace_idx < max_traces:
            steps.append(
                {
                    "step": 0,
                    "pos": pos,
                    "char": None,
                    "char_display": "START",
                    "from_state": None,
                    "to_state": cur_state,
                    "is_accept": cur_state in dfa.accept_states,
                    "accept_token": (
                        dfa.accept_states[cur_state].token_name
                        if cur_state in dfa.accept_states
                        else None
                    ),
                    "status": "start",
                }
            )

        step_num = 0
        while cursor < n and cur_state is not None:
            ch = text[cursor]
            nxt = dfa.step(cur_state, ch)
            total_transitions += 1
            step_num += 1

            if nxt is None:
                if record_traces and trace_idx < max_traces:
                    steps.append(
                        {
                            "step": step_num,
                            "pos": cursor,
                            "char": ch,
                            "char_display": escape_char_display(ch),
                            "from_state": cur_state,
                            "to_state": None,
                            "is_accept": False,
                            "accept_token": None,
                            "status": "dead",
                        }
                    )
                break

            cur_state = nxt
            cursor += 1
            acc_info = dfa.accept_states.get(cur_state)
            if acc_info is not None:
                last_accept = (cursor, cur_state, acc_info)

            if record_traces and trace_idx < max_traces:
                steps.append(
                    {
                        "step": step_num,
                        "pos": cursor - 1,
                        "char": ch,
                        "char_display": escape_char_display(ch),
                        "from_state": steps[-1]["to_state"] if steps else dfa.start_state,
                        "to_state": cur_state,
                        "is_accept": acc_info is not None,
                        "accept_token": acc_info.token_name if acc_info else None,
                        "status": "accept" if acc_info is not None else "move",
                    }
                )

        if last_accept is not None and last_accept[0] > pos:
            end_pos, acc_state, acc_info = last_accept
            backtrack = cursor - end_pos
            lexeme = text[pos:end_pos]

            tok = Token(
                token_type=acc_info.token_name,
                lexeme=lexeme,
                line=line,
                col=col,
                start_pos=pos,
                end_pos=end_pos,
                category=acc_info.category,
                skipped=acc_info.skip,
                accept_state=acc_state,
                backtrack_steps=backtrack,
            )
            tokens.append(tok)
            if not acc_info.skip:
                visible_tokens.append(tok)

            if record_traces and trace_idx < max_traces:
                traces.append(
                    TokenTrace(
                        index=trace_idx,
                        kind="TOKEN",
                        token_type=acc_info.token_name,
                        lexeme=lexeme,
                        line=line,
                        col=col,
                        start_pos=pos,
                        end_pos=end_pos,
                        skipped=acc_info.skip,
                        backtrack_steps=backtrack,
                        final_accept_state=acc_state,
                        steps=steps,
                    )
                )
            trace_idx += 1

            line, col = _advance_line_col(text, pos, end_pos, line, col)
            pos = end_pos
        else:
            # Lexical error: no valid token prefix accepted starting at `pos`
            bad_ch = text[pos]
            attempted = text[pos:cursor] if cursor > pos else bad_ch
            if bad_ch == '"':
                msg = (
                    f"Chuỗi ký tự chưa được đóng (unterminated string) bắt đầu bằng "
                    f"'{attempted[:24]}' tại dòng {line}, cột {col}"
                )
            elif cursor > pos:
                msg = (
                    f"Từ tố không hoàn chỉnh '{attempted[:24]}' không đạt trạng thái kết thúc "
                    f"(bắt đầu bởi '{escape_char_display(bad_ch)}') tại dòng {line}, cột {col}"
                )
            else:
                msg = (
                    f"Ký tự không hợp lệ '{escape_char_display(bad_ch)}' "
                    f"(mã U+{ord(bad_ch):04X}) tại dòng {line}, cột {col}"
                )

            err = LexicalError(
                char=bad_ch,
                line=line,
                col=col,
                pos=pos,
                message=msg,
                attempted_lexeme=attempted,
            )
            errors.append(err)

            if record_traces and trace_idx < max_traces:
                traces.append(
                    TokenTrace(
                        index=trace_idx,
                        kind="ERROR",
                        token_type="LEXICAL_ERROR",
                        lexeme=bad_ch,
                        line=line,
                        col=col,
                        start_pos=pos,
                        end_pos=pos + 1,
                        skipped=False,
                        backtrack_steps=max(0, cursor - (pos + 1)),
                        final_accept_state=None,
                        steps=steps,
                    )
                )
            trace_idx += 1

            # Panic-mode recovery: advance 1 char so remaining tokens are still scanned
            line, col = _advance_line_col(text, pos, pos + 1, line, col)
            pos += 1

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return ScanResult(
        tokens=tokens,
        visible_tokens=visible_tokens,
        errors=errors,
        traces=traces,
        elapsed_ms=elapsed_ms,
        total_chars=n,
        total_transitions=total_transitions,
    )
