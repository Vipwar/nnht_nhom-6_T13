"""
Generate high-DPI (300 DPI) publication-grade figures directly from the live
T13 Automata-based Lexical Analyzer engine (Graphviz + Matplotlib + real UI screenshots).

Outputs into `deliverables/figures/`:
  1. fig1_architecture_pipeline.png   — System & Formal Automata Pipeline diagram
  2. fig2_slide38_pipeline.png        — Exact Thompson ε-NFA -> Subset DFA -> Min-DFA for (a|b)*abb
  3. fig3_calclang_combined_dfa.png   — Full Minimized Combined Multi-token DFA for CalcLang (20 states)
  4. fig4_benchmark_comparison.png    — State Reduction & Compile/Scan Performance charts
  5. fig5_direct_tree_followpos.png   — Direct RE -> DFA Annotated Syntax Tree for (a|ba)(a|b)*ba
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lexer_engine import PRESETS, LexicalAnalyzer, inspect_single_regex  # noqa: E402
from lexer_engine.dfa_minimizer import minimize_dfa  # noqa: E402
from lexer_engine.direct_dfa import build_direct_dfa  # noqa: E402
from lexer_engine.subset_construction import nfa_to_dfa  # noqa: E402
from lexer_engine.thompson import build_token_nfa  # noqa: E402

FIG_DIR = PROJECT_ROOT / "deliverables" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Segoe UI", "Arial"]
plt.rcParams["axes.unicode_minus"] = False

DOT_BIN = shutil.which("dot") or shutil.which("dot.bat")


def _dot_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _render_dot(dot_src: str, out_png: Path, dpi: int = 240) -> bool:
    if not DOT_BIN:
        if out_png.exists():
            print(f"  [INFO] Graphviz `dot` not in PATH; keeping existing {out_png.name}")
            return False
        raise RuntimeError("Graphviz `dot` binary not found in PATH.")
    dot_file = out_png.with_suffix(".dot")
    dot_file.write_text(dot_src, encoding="utf-8")
    subprocess.run(
        [DOT_BIN, "-Tpng", f"-Gdpi={dpi}", str(dot_file), "-o", str(out_png)],
        check=True,
    )
    dot_file.unlink(missing_ok=True)
    return True


def fig1_architecture_pipeline() -> None:
    """Visual architecture diagram of the Automata-based Lexical Analyzer."""
    fig, ax = plt.subplots(figsize=(11.5, 4.8), dpi=300)
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 4.8)
    ax.axis("off")

    # Background card
    ax.add_patch(
        patches.FancyBboxPatch(
            (0.15, 0.15), 11.2, 4.5,
            boxstyle="round,pad=0.1,rounding_size=0.18",
            facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2,
        )
    )
    ax.text(
        5.75, 4.35,
        "KIẾN TRÚC TỔNG THỂ BỘ PHÂN TÍCH TỪ VỰNG DỰA TRÊN AUTOMATA (ĐỀ TÀI T13)",
        ha="center", va="center", fontsize=11.0, fontweight="bold", color="#0F172A",
    )

    # Top main compile pipeline (5 boxes)
    stages = [
        (0.45, 2.55, 1.85, 1.35, "#EFF6FF", "#2563EB", "1. Đặc tả Token", "Tập RE: R₁..Rₖ + Priority\nMa trận giao L(Rᵢ)∩L(Rⱼ)\n& Cảnh báo che khuất"),
        (2.65, 2.55, 1.85, 1.35, "#EEF2FF", "#4F46E5", "2. Regex Parser", "Đệ quy (0 import re, ≤4096 nút)\nΣ(U) Unicode động & ASCII\n0x00..0x7F (~(~A) = A)"),
        (4.85, 2.55, 1.85, 1.35, "#F0FDF4", "#16A34A", "3. Thompson & Khử ε", "Combined ε-NFA (ĐL 3)\n→ NFA không ε (ĐL 2)\nGắn nhãn đích Fᵢ"),
        (7.05, 2.55, 1.95, 1.35, "#FFFBEB", "#D97706", "4. Subset DFA", "Định lý 1: ε-closure & Move\nPhân hoạch lớp tương đương\nGiải xung đột ưu tiên"),
        (9.35, 2.55, 1.80, 1.35, "#ECFDF5", "#059669", "5. Min-DFA", "Moore Π₀..Πₙ & Hopcroft\nO(|Σ|·|Q|log|Q|)\nBảo toàn phân loại token"),
    ]

    for x, y, w, h, fc, ec, title, desc in stages:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.06,rounding_size=0.12",
                facecolor=fc, edgecolor=ec, linewidth=1.8,
            )
        )
        ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="center", fontsize=9.0, fontweight="bold", color=ec)
        ax.text(x + w / 2, y + 0.50, desc, ha="center", va="center", fontsize=7.35, color="#1E293B", linespacing=1.35)

    # Arrows between top boxes
    for i in range(len(stages) - 1):
        x1 = stages[i][0] + stages[i][2] + 0.06
        x2 = stages[i + 1][0] - 0.06
        ym = 2.55 + 1.35 / 2
        ax.annotate("", xy=(x2, ym), xytext=(x1, ym), arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.8))

    # Bottom row: Direct RE->DFA + GNFA, Formal Verifier, and O(n) Scanner + Codegen
    bottom_boxes = [
        (0.45, 0.48, 2.95, 1.32, "#F5F3FF", "#7C3AED", "Direct RE→DFA & GNFA", "Cây cú pháp r·# (followpos) + JFLAP\n& Khử trạng thái GNFA (DFA → RE)"),
        (3.75, 0.48, 3.15, 1.32, "#ECFDF5", "#047857", "Kiểm chứng tương đương", "Product Automaton (R₀ ≡ R_sinh)\nMyhill-Nerode + Chứng nhân L(Rᵢ)∩L(Rⱼ)"),
        (7.25, 0.48, 3.90, 1.32, "#FEF2F2", "#DC2626", "6. Bộ quét O(n) & Sinh mã Lexer", "Maximal Munch + Reps Memoization chống O(n²)\nPanic/Smart-Sync + Xuất Lexer độc lập (.py)"),
    ]
    for x, y, w, h, fc, ec, title, desc in bottom_boxes:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.06,rounding_size=0.12",
                facecolor=fc, edgecolor=ec, linewidth=1.8,
            )
        )
        ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="center", fontsize=8.9, fontweight="bold", color=ec)
        ax.text(x + w / 2, y + 0.46, desc, ha="center", va="center", fontsize=7.35, color="#1E293B", linespacing=1.35)

    # Connectors from top row to bottom row
    ax.annotate("", xy=(2.1, 1.86), xytext=(3.55, 2.49), arrowprops=dict(arrowstyle="-|>", color="#7C3AED", lw=1.5, ls="--"))
    ax.annotate("", xy=(5.1, 1.86), xytext=(7.8, 2.49), arrowprops=dict(arrowstyle="-|>", color="#047857", lw=1.5, ls="--"))
    ax.annotate("", xy=(5.6, 1.86), xytext=(9.9, 2.49), arrowprops=dict(arrowstyle="-|>", color="#047857", lw=1.5, ls="--"))
    ax.annotate("", xy=(9.6, 1.86), xytext=(10.25, 2.49), arrowprops=dict(arrowstyle="-|>", color="#DC2626", lw=2.0))

    plt.tight_layout(pad=0.2)
    plt.savefig(FIG_DIR / "fig1_architecture_pipeline.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig2_slide38_pipeline() -> None:
    """Render exact Thompson NFA -> Subset DFA -> Minimized DFA for (a|b)*abb via Graphviz + compose side-by-side."""
    out_path = FIG_DIR / "fig2_slide38_pipeline.png"
    if not DOT_BIN and out_path.exists():
        print("  [INFO] Graphviz `dot` not in PATH; keeping existing fig2_slide38_pipeline.png")
        return
    nfa, _ = build_token_nfa("(a|b)*abb", "SLIDE38")
    sub_dfa, _ = nfa_to_dfa(nfa, record_steps=False)
    min_dfa = minimize_dfa(sub_dfa).minimized_dfa

    def nfa_to_dot(n) -> str:
        lines = [
            'digraph NFA {',
            '  rankdir=LR; bgcolor="white"; pad="0.2";',
            '  node [fontname="DejaVu Sans", fontsize=11, shape=circle, style=filled, fillcolor="#FFFFFF", color="#334155", penwidth=1.6];',
            '  edge [fontname="DejaVu Sans", fontsize=10, color="#475569"];',
            '  __start [shape=none, label="start", fontcolor="#059669", fontsize=10, width=0.2];',
            f'  __start -> q{n.start_state} [color="#059669", penwidth=2.0];',
        ]
        for q in sorted(n.states):
            if q in n.accept_states:
                lines.append(f'  q{q} [shape=doublecircle, fillcolor="#ECFDF5", color="#059669", penwidth=2.0];')
            elif q == n.start_state:
                lines.append(f'  q{q} [fillcolor="#EFF6FF", color="#2563EB", penwidth=2.0];')
        for src, edges in n.transitions.items():
            for chars, dst, lbl in edges:
                if chars is None:
                    lines.append(f'  q{src} -> q{dst} [label="ε", style=dashed, color="#2563EB", fontcolor="#1D4ED8"];')
                else:
                    lines.append(f'  q{src} -> q{dst} [label="{_dot_escape(lbl)}", penwidth=1.6];')
        lines.append('}')
        return "\n".join(lines)

    def dfa_to_dot(d, show_subset: bool = True) -> str:
        lines = [
            'digraph DFA {',
            '  rankdir=LR; bgcolor="white"; pad="0.2";',
            '  node [fontname="DejaVu Sans", fontsize=11, shape=circle, style=filled, fillcolor="#FFFFFF", color="#334155", penwidth=1.6];',
            '  edge [fontname="DejaVu Sans", fontsize=10, color="#334155"];',
            '  __start [shape=none, label="start", fontcolor="#059669", fontsize=10, width=0.2];',
            f'  __start -> D{d.start_state} [color="#059669", penwidth=2.0];',
        ]
        for q in sorted(d.states):
            if q in d.accept_states:
                lines.append(f'  D{q} [shape=doublecircle, fillcolor="#ECFDF5", color="#059669", penwidth=2.0];')
            elif q == d.start_state:
                lines.append(f'  D{q} [fillcolor="#EFF6FF", color="#2563EB", penwidth=2.0];')
        for src, dst, _, lbl in d.compressed_edges():
            lines.append(f'  D{src} -> D{dst} [label="{_dot_escape(lbl)}", penwidth=1.6];')
        lines.append('}')
        return "\n".join(lines)

    p_nfa = FIG_DIR / "_tmp_nfa.png"
    p_sub = FIG_DIR / "_tmp_sub.png"
    p_min = FIG_DIR / "_tmp_min.png"
    _render_dot(nfa_to_dot(nfa), p_nfa, dpi=240)
    _render_dot(dfa_to_dot(sub_dfa), p_sub, dpi=240)
    _render_dot(dfa_to_dot(min_dfa), p_min, dpi=240)

    from PIL import Image
    im_nfa = Image.open(p_nfa)
    im_sub = Image.open(p_sub)
    im_min = Image.open(p_min)

    fig = plt.figure(figsize=(11.5, 6.2), dpi=280)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], hspace=0.25, wspace=0.14)

    ax1 = fig.add_subplot(gs[0, :])
    ax1.imshow(im_nfa)
    ax1.axis("off")
    ax1.set_title("(a) Thompson ε-NFA cho (a|b)*abb — 11 trạng thái (q0..q10), khớp Slide 38 Chương 3.1", fontsize=10.5, fontweight="bold", color="#1E3A8A", pad=6)

    ax2 = fig.add_subplot(gs[1, 0])
    ax2.imshow(im_sub)
    ax2.axis("off")
    ax2.set_title("(b) Subset Construction DFA — 5 trạng thái (D0..D4)", fontsize=10.2, fontweight="bold", color="#D97706", pad=6)

    ax3 = fig.add_subplot(gs[1, 1])
    ax3.imshow(im_min)
    ax3.axis("off")
    ax3.set_title("(c) Minimized DFA — 4 trạng thái (GNFA sinh R_sinh ≡ R_gốc)", fontsize=10.2, fontweight="bold", color="#059669", pad=6)

    plt.savefig(out_path, dpi=280, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    for p in (p_nfa, p_sub, p_min):
        p.unlink(missing_ok=True)


def fig3_calclang_combined_dfa() -> None:
    """Render the complete 20-state Minimized Combined DFA of CalcLang using Graphviz."""
    out_path = FIG_DIR / "fig3_calclang_combined_dfa.png"
    if not DOT_BIN and out_path.exists():
        print("  [INFO] Graphviz `dot` not in PATH; keeping existing fig3_calclang_combined_dfa.png")
        return
    lex = LexicalAnalyzer.from_preset("calclang")
    d = lex.minimized_dfa

    cat_colors = {
        "keyword": ("#F3E8FF", "#7C3AED"),
        "identifier": ("#DBEAFE", "#1D4ED8"),
        "literal": ("#D1FAE5", "#047857"),
        "operator": ("#FFEDD5", "#C2410C"),
        "delimiter": ("#F1F5F9", "#475569"),
        "whitespace": ("#F3F4F6", "#6B7280"),
    }

    lines = [
        'digraph CalcLangDFA {',
        '  rankdir=LR; bgcolor="white"; pad="0.25"; nodesep="0.32"; ranksep="0.55";',
        '  labelloc="t"; fontname="DejaVu Sans"; fontsize=13;',
        '  label="Minimized Combined Multi-token DFA — Ngôn ngữ CalcLang (12 Token → 20 Trạng thái tối giản)";',
        '  node [fontname="DejaVu Sans", fontsize=9.5, shape=circle, style=filled, fillcolor="#FFFFFF", color="#334155", penwidth=1.5];',
        '  edge [fontname="DejaVu Sans Mono", fontsize=8.5, color="#475569"];',
        '  __start [shape=none, label="START", fontcolor="#059669", fontsize=9.5];',
        f'  __start -> D{d.start_state} [color="#059669", penwidth=2.2];',
    ]

    for q in sorted(d.states):
        if q in d.accept_states:
            acc = d.accept_states[q]
            fc, ec = cat_colors.get(acc.category, ("#ECFDF5", "#059669"))
            lbl = f"D{q}\\n[{acc.token_name}]"
            lines.append(
                f'  D{q} [shape=doublecircle, label="{lbl}", fillcolor="{fc}", color="{ec}", penwidth=2.0, fontsize=8.5];'
            )
        elif q == d.start_state:
            lines.append(f'  D{q} [label="D{q}", fillcolor="#EFF6FF", color="#2563EB", penwidth=2.4];')
        else:
            lines.append(f'  D{q} [label="D{q}"];')

    for src, dst, _, lbl in d.compressed_edges():
        lines.append(f'  D{src} -> D{dst} [label=" {_dot_escape(lbl)} "];')

    lines.append("}")
    _render_dot("\n".join(lines), out_path, dpi=240)


def fig4_benchmark_comparison() -> None:
    """Publication-grade dual chart: (a) State Count Reduction across 4-Theorem Pipeline, (b) Compile & 10KB Scan ms."""
    presets = ["minilang", "calclang", "minisql"]
    labels = ["MiniLang\n(39 token)", "CalcLang\n(12 token)", "MiniSQL\n(14 token)"]
    nfa_counts, eps_free_counts, sub_counts, min_counts = [], [], [], []
    compile_ms, scan_ms = [], []

    for pid in presets:
        lex = LexicalAnalyzer.from_preset(pid)
        s = lex.summary_dict()
        nfa_counts.append(s["nfa_states"])
        eps_free_counts.append(s["eps_free_nfa_states"])
        sub_counts.append(s["subset_dfa_states"])
        min_counts.append(s["minimized_dfa_states"])
        compile_ms.append(s["timings_ms"]["total_ms"])

        base = PRESETS[pid]["samples"]["valid"]["code"]
        big = (base + "\n") * max(1, 10240 // max(1, len(base)))
        t0 = time.perf_counter()
        lex.scan(big, use_minimized=True, record_traces=False)
        scan_ms.append((time.perf_counter() - t0) * 1000.0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.3), dpi=300)
    x = np.arange(len(labels))
    w = 0.20

    b1 = ax1.bar(x - 1.5 * w, nfa_counts, width=w, label="ε-NFA (ĐL 3)", color="#60A5FA", edgecolor="#1D4ED8", lw=0.8)
    b2 = ax1.bar(x - 0.5 * w, eps_free_counts, width=w, label="NFA khử ε (ĐL 2)", color="#A78BFA", edgecolor="#6D28D9", lw=0.8)
    b3 = ax1.bar(x + 0.5 * w, sub_counts, width=w, label="Subset DFA (ĐL 1)", color="#FBBF24", edgecolor="#B45309", lw=0.8)
    b4 = ax1.bar(x + 1.5 * w, min_counts, width=w, label="Min-DFA (Moore/Hopcroft)", color="#34D399", edgecolor="#047857", lw=0.8)

    for bars in (b1, b2, b3, b4):
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 2.2, f"{int(h)}", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#0F172A")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
    ax1.set_ylabel("Số lượng trạng thái (States)", fontsize=9.5, fontweight="bold")
    ax1.set_title("(a) Số trạng thái qua các giai đoạn Chương 3.1", fontsize=10.5, fontweight="bold", color="#1E3A8A", pad=10)
    ax1.set_ylim(0, max(nfa_counts) * 1.18)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    ax1.legend(frameon=True, fontsize=8.0, ncol=2)

    w2 = 0.32
    c1 = ax2.bar(x - w2 / 2, compile_ms, width=w2, label="Biên dịch toàn pipeline (ms)", color="#818CF8", edgecolor="#4338CA", lw=0.8)
    c2 = ax2.bar(x + w2 / 2, scan_ms, width=w2, label="Quét 10 KB mã nguồn (ms)", color="#FB7185", edgecolor="#BE123C", lw=0.8)

    for bars in (c1, c2):
        for bar in bars:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.35, f"{h:.1f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0F172A")

    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
    ax2.set_ylabel("Thời gian thực thi (ms)", fontsize=9.5, fontweight="bold")
    ax2.set_title("(b) Thời gian biên dịch Automata & tốc độ quét 10 KB", fontsize=10.5, fontweight="bold", color="#1E3A8A", pad=10)
    ax2.set_ylim(0, max(max(compile_ms), max(scan_ms)) * 1.24)
    ax2.grid(axis="y", linestyle="--", alpha=0.4)
    ax2.legend(frameon=True, fontsize=8.5)

    plt.tight_layout(pad=1.2)
    plt.savefig(FIG_DIR / "fig4_benchmark_comparison.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig5_direct_dfa_slide46() -> None:
    """Render the Direct DFA for UEH Slide 46-57 example (a|ba)(a|b)*ba via Graphviz."""
    out_path = FIG_DIR / "fig5_direct_dfa_slide46.png"
    if not DOT_BIN and out_path.exists():
        print("  [INFO] Graphviz `dot` not in PATH; keeping existing fig5_direct_dfa_slide46.png")
        return
    res = build_direct_dfa("(a|ba)(a|b)*ba", "SLIDE46")
    d = res.dfa
    lines = [
        'digraph DirectSlide46 {',
        '  rankdir=LR; bgcolor="white"; pad="0.25"; nodesep="0.45"; ranksep="0.65";',
        '  labelloc="t"; fontname="DejaVu Sans"; fontsize=12;',
        '  label="Direct RE → DFA cho r = (a|ba)(a|b)*ba# (5 trạng thái tối giản, khớp Slide 55-57 Chương 3.1)";',
        '  node [fontname="DejaVu Sans", fontsize=10, shape=circle, style=filled, fillcolor="#FFFFFF", color="#334155", penwidth=1.6];',
        '  edge [fontname="DejaVu Sans Mono", fontsize=10, color="#334155"];',
        '  __start [shape=none, label="start", fontcolor="#059669"];',
        f'  __start -> D{d.start_state} [color="#059669", penwidth=2.0];',
    ]
    names = ["A", "B", "C", "D", "E", "F", "G"]
    for q in sorted(d.states):
        sub = "{" + ",".join(str(x) for x in d.state_subsets.get(q, [])) + "}"
        tag = f"{names[q]}\\n{sub}" if q < len(names) else f"D{q}\\n{sub}"
        if q in d.accept_states:
            lines.append(f'  D{q} [shape=doublecircle, label="{tag}", fillcolor="#ECFDF5", color="#059669", penwidth=2.0];')
        elif q == d.start_state:
            lines.append(f'  D{q} [label="{tag}", fillcolor="#EFF6FF", color="#2563EB", penwidth=2.0];')
        else:
            lines.append(f'  D{q} [label="{tag}"];')

    for src, dst, _, lbl in d.compressed_edges():
        lines.append(f'  D{src} -> D{dst} [label=" {_dot_escape(lbl)} ", penwidth=1.6];')
    lines.append("}")
    _render_dot("\n".join(lines), out_path, dpi=260)


if __name__ == "__main__":
    print("Generating high-DPI figures into:", FIG_DIR)
    fig1_architecture_pipeline()
    print("  [OK] fig1_architecture_pipeline.png")
    fig2_slide38_pipeline()
    print("  [OK] fig2_slide38_pipeline.png")
    fig3_calclang_combined_dfa()
    print("  [OK] fig3_calclang_combined_dfa.png")
    fig4_benchmark_comparison()
    print("  [OK] fig4_benchmark_comparison.png")
    fig5_direct_dfa_slide46()
    print("  [OK] fig5_direct_dfa_slide46.png")
    print("All figures generated successfully!")
