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
    """
    Update 1-based (line, col) after consuming text[start:end].
    Accurately handles Unix LF (\\n), Windows CRLF (\\r\\n), and legacy Mac CR (\\r).
    """
    n = len(text)
    for i in range(start, end):
        ch = text[i]
        if ch == "\n":
            line += 1
            col = 1
        elif ch == "\r":
            if i + 1 < n and text[i + 1] == "\n":
                pass
            else:
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
    error_recovery: str = "panic_char",
) -> ScanResult:
    """
    Tokenize `text` using the compiled Deterministic Finite Automaton `dfa`.

    Implements Reps (1998) Linear-Time Maximal Munch memoization (`failed_states`)
    to prevent O(n^2) quadratic backtracking on pathological inputs (e.g., 10,000-char
    unclosed strings or block comments), guaranteeing strict O(n) time complexity.

    Supports two error recovery modes:
    - "panic_char" (default): classic 1-character panic-mode recovery
    - "smart_sync": synchronizes by swallowing entire unclosed string literal or
      unclosed multi-line block comment as a single lexical error.
    """
    if error_recovery not in ("panic_char", "smart_sync"):
        raise ValueError(f"Chế độ phục hồi lỗi không hợp lệ: {error_recovery!r}")

    t0 = time.perf_counter()

    tokens: List[Token] = []
    visible_tokens: List[Token] = []
    errors: List[LexicalError] = []
    traces: List[TokenTrace] = []

    # Reps (1998) memoization table: (dfa_state, text_index) known to never reach any accept state
    failed_states: set[Tuple[int, int]] = set()
    memoized_cutoffs = 0

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
        visited_since_accept: List[Tuple[int, int]] = []

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

            prev_state = cur_state
            cur_state = nxt
            cursor += 1

            if (cur_state, cursor) in failed_states:
                memoized_cutoffs += 1
                visited_since_accept.append((cur_state, cursor))
                if record_traces and trace_idx < max_traces:
                    steps.append(
                        {
                            "step": step_num,
                            "pos": cursor - 1,
                            "char": ch,
                            "char_display": escape_char_display(ch),
                            "from_state": prev_state,
                            "to_state": cur_state,
                            "is_accept": False,
                            "accept_token": None,
                            "status": "dead",
                        }
                    )
                break

            acc_info = dfa.accept_states.get(cur_state)
            if acc_info is not None:
                last_accept = (cursor, cur_state, acc_info)
                visited_since_accept.clear()
            else:
                visited_since_accept.append((cur_state, cursor))

            if record_traces and trace_idx < max_traces:
                steps.append(
                    {
                        "step": step_num,
                        "pos": cursor - 1,
                        "char": ch,
                        "char_display": escape_char_display(ch),
                        "from_state": prev_state,
                        "to_state": cur_state,
                        "is_accept": acc_info is not None,
                        "accept_token": acc_info.token_name if acc_info else None,
                        "status": "accept" if acc_info is not None else "move",
                    }
                )

        # Record all states visited after the last accepting state into failed_states (Reps 1998)
        if visited_since_accept:
            failed_states.update(visited_since_accept)

        # Detect unclosed block comment `/* ...` that entered the comment body (cursor >= pos + 2)
        # but hit EOF without closing `*/` (so last_accept is still at pos + 1 on `/`)
        is_unclosed_block_comment = (
            text[pos : pos + 2] == "/*"
            and cursor >= pos + 2
            and (last_accept is None or last_accept[0] == pos + 1)
        )
        if is_unclosed_block_comment:
            last_accept = None

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

            # Determine recovery span based on error_recovery mode
            if error_recovery == "smart_sync":
                if is_unclosed_block_comment:
                    sync_end = n
                elif bad_ch == '"' or (bad_ch == "'" and cursor > pos + 1):
                    sync_end = max(cursor, pos + 1)
                    while sync_end < n and text[sync_end] not in ("\n", "\r"):
                        sync_end += 1
                else:
                    sync_end = pos + 1
            else:
                sync_end = pos + 1

            consumed_err = text[pos:sync_end]
            display_attempt = text[pos : max(cursor, sync_end)]

            if is_unclosed_block_comment:
                msg = (
                    f"Bình luận nhiều dòng '/*' chưa được đóng (unterminated block comment) "
                    f"bắt đầu bằng '{display_attempt[:24]}' tại dòng {line}, cột {col}"
                )
            elif bad_ch == '"' or (bad_ch == "'" and cursor > pos + 1):
                msg = (
                    f"Chuỗi ký tự chưa được đóng (unterminated string) bắt đầu bằng "
                    f"'{display_attempt[:24]}' tại dòng {line}, cột {col}"
                )
            elif cursor > pos:
                msg = (
                    f"Từ tố không hoàn chỉnh '{display_attempt[:24]}' không đạt trạng thái kết thúc "
                    f"(bắt đầu bởi '{escape_char_display(bad_ch)}') tại dòng {line}, cột {col}"
                )
            else:
                msg = (
                    f"Ký tự không hợp lệ '{escape_char_display(bad_ch)}' "
                    f"(mã U+{ord(bad_ch):04X}) tại dòng {line}, cột {col}"
                )

            err = LexicalError(
                char=consumed_err if error_recovery == "smart_sync" else bad_ch,
                line=line,
                col=col,
                pos=pos,
                message=msg,
                attempted_lexeme=display_attempt,
            )
            errors.append(err)

            if record_traces and trace_idx < max_traces:
                traces.append(
                    TokenTrace(
                        index=trace_idx,
                        kind="ERROR",
                        token_type="LEXICAL_ERROR",
                        lexeme=consumed_err,
                        line=line,
                        col=col,
                        start_pos=pos,
                        end_pos=sync_end,
                        skipped=False,
                        backtrack_steps=max(0, cursor - sync_end),
                        final_accept_state=None,
                        steps=steps,
                    )
                )
            trace_idx += 1

            line, col = _advance_line_col(text, pos, sync_end, line, col)
            pos = sync_end

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return ScanResult(
        tokens=tokens,
        visible_tokens=visible_tokens,
        errors=errors,
        traces=traces,
        elapsed_ms=elapsed_ms,
        total_chars=n,
        total_transitions=total_transitions,
        error_recovery_mode=error_recovery,
        memoized_cutoffs=memoized_cutoffs,
    )

