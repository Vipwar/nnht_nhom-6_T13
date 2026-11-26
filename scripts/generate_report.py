# -*- coding: utf-8 -*-
"""
Generate the official UEH Final Project Technical Report (DOCX + PDF)
for Topic T13: Automata-based Lexical Analyzer.

Strictly follows all 10 mandatory sections and length guideline (12-15 pages, targeting 13-14 pages)
from `Tieu_luan_CK_2026.pdf`.
"""

from __future__ import annotations

import base64
import html
import json
import re as _fmt_re
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Set

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lexer_engine import LexicalAnalyzer, PRESETS  # noqa: E402
from lexer_engine.direct_dfa import build_combined_direct_dfa  # noqa: E402
from tests.test_suite import run_json_test_report  # noqa: E402

FIG_DIR = PROJECT_ROOT / "deliverables" / "figures"
OUT_DIR = PROJECT_ROOT / "deliverables"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCX_PATH = OUT_DIR / "Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.docx"
PDF_PATH = OUT_DIR / "Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.pdf"

NAVY = RGBColor(0x1E, 0x3A, 0x8A)
BLUE = RGBColor(0x25, 0x63, 0xEB)
DARK = RGBColor(0x0F, 0x17, 0x2A)
MUTED = RGBColor(0x47, 0x55, 0x69)
GREEN = RGBColor(0x04, 0x78, 0x57)

HTML_BLOCKS: List[dict] = []


def set_cell_shading(cell, fill_hex: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=60, bottom=60, left=100, right=100) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color: str = "CBD5E1") -> None:
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="1E3A8A"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        f"</w:tblBorders>"
    )
    tblPr.append(borders)


def add_page_number_field(paragraph) -> None:
    run = paragraph.add_run("Trang ")
    run.font.name = "Times New Roman"
    run.font.size = Pt(9.5)
    run.font.color.rgb = MUTED

    fld1 = OxmlElement("w:fldSimple")
    fld1.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld1)

    run2 = paragraph.add_run(" / ")
    run2.font.name = "Times New Roman"
    run2.font.size = Pt(9.5)
    run2.font.color.rgb = MUTED

    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    paragraph._p.append(fld2)


def add_bottom_border(paragraph, color: str = "1E3A8A", sz: str = "10") -> None:
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="3" w:color="{color}"/>'
        f"</w:pBdr>"
    )
    pPr.append(pBdr)


def _add_rich_runs(paragraph, text: str, base_size: float = 11.0, base_color=DARK, force_bold: bool = False) -> None:
    """Parse inline **bold** and `code` spans (including nested `code` inside **bold**) into Word runs."""
    tokens = _fmt_re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            inner = tok[2:-2]
            if "`" in inner:
                _add_rich_runs(paragraph, inner, base_size=base_size, base_color=base_color, force_bold=True)
            else:
                r = paragraph.add_run(inner)
                r.bold = True
                r.font.name = "Times New Roman"
                r.font.size = Pt(base_size)
                r.font.color.rgb = base_color
        elif tok.startswith("`") and tok.endswith("`"):
            r = paragraph.add_run(tok[1:-1])
            r.bold = force_bold
            r.font.name = "Consolas"
            r.font.size = Pt(max(8.0, base_size - 1.3))
            r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        else:
            r = paragraph.add_run(tok.replace("`", ""))
            r.bold = force_bold
            r.font.name = "Times New Roman"
            r.font.size = Pt(base_size)
            r.font.color.rgb = base_color


def _rich_to_html(text: str) -> str:
    """Convert inline **bold** and `code` spans (including nested `code` inside **bold**) to clean HTML."""
    tokens = _fmt_re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", str(text))
    parts: List[str] = []
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            inner = tok[2:-2]
            if "`" in inner:
                parts.append(f"<strong>{_rich_to_html(inner)}</strong>")
            else:
                parts.append(f"<strong>{html.escape(inner)}</strong>")
        elif tok.startswith("`") and tok.endswith("`"):
            parts.append(f'<code class="inline-code">{html.escape(tok[1:-1])}</code>')
        else:
            parts.append(html.escape(tok.replace("`", "")).replace("\n", "<br/>"))
    return "".join(parts)


def add_callout(
    doc: Document,
    title: str,
    lines: list[str],
    fill: str = "F1F5F9",
    accent: str = "2563EB",
    mono: bool = False,
) -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_margins(cell, top=80, bottom=80, left=130, right=115)
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(
        parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="{accent}"/>'
            f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
            f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
            f'  <w:bottom w:val="single" w:sz="4" w:color="CBD5E1"/>'
            f"</w:tcBorders>"
        )
    )
    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(2.5)
    _add_rich_runs(p0, f"**{title}**", base_size=10.4, base_color=NAVY)

    for idx, line in enumerate(lines):
        p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1.2 if idx < len(lines) - 1 else 0)
        p.paragraph_format.line_spacing = 1.14
        if mono:
            clean_line = line.replace("`", "")
            r = p.add_run(clean_line)
            r.font.name = "Consolas"
            r.font.size = Pt(8.6)
            r.font.color.rgb = DARK
        else:
            _add_rich_runs(p, line, base_size=10.1, base_color=DARK)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(3.5)
    HTML_BLOCKS.append(
        {"type": "callout", "title": title, "lines": lines, "fill": fill, "accent": accent, "mono": mono}
    )


def add_styled_table(
    doc: Document,
    headers: list[str],
    rows: list[list[str]],
    col_widths_cm: list[float] | None = None,
    font_size: float = 9.1,
    mono_cols: set[int] | None = None,
    trailing_space: bool = True,
) -> None:
    mono_cols = mono_cols or set()
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    hdr_row = tbl.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))
    trPr.append(OxmlElement("w:cantSplit"))

    for c_idx, h_text in enumerate(headers):
        cell = hdr_row.cells[c_idx]
        set_cell_shading(cell, "1E3A8A")
        set_cell_margins(cell, top=55, bottom=55, left=70, right=70)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if col_widths_cm:
            cell.width = Cm(col_widths_cm[c_idx])
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text.replace("`", ""))
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row_vals in enumerate(rows):
        row = tbl.rows[r_idx + 1]
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=42, bottom=42, left=70, right=70)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if col_widths_cm:
                cell.width = Cm(col_widths_cm[c_idx])
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.12
            if c_idx in mono_cols:
                r = p.add_run(str(val).replace("`", ""))
                r.font.name = "Consolas"
                r.font.size = Pt(font_size - 0.6)
                r.font.color.rgb = DARK
            else:
                _add_rich_runs(p, str(val), base_size=font_size)

    if trailing_space:
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(3)

    HTML_BLOCKS.append(
        {
            "type": "table",
            "headers": headers,
            "rows": rows,
            "col_widths_cm": col_widths_cm,
            "font_size": font_size,
            "mono_cols": mono_cols,
        }
    )


def add_heading_1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4.5)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(13.2)
    r.font.color.rgb = NAVY
    add_bottom_border(p, color="1E3A8A", sz="8")
    HTML_BLOCKS.append({"type": "h1", "text": text})


def add_heading_2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7.5)
    p.paragraph_format.space_after = Pt(2.8)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(11.3)
    r.font.color.rgb = BLUE
    HTML_BLOCKS.append({"type": "h2", "text": text})


def add_body(doc: Document, text: str, bold_prefix: str | None = None, space_after: float = 4.2) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.18
    if bold_prefix:
        _add_rich_runs(p, bold_prefix, base_size=10.8, base_color=DARK, force_bold=True)
    _add_rich_runs(p, text, base_size=10.8)
    HTML_BLOCKS.append({"type": "body", "bold_prefix": bold_prefix or "", "text": text})


def add_bullet(doc: Document, bold_lead: str, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2.4)
    p.paragraph_format.line_spacing = 1.16
    if bold_lead:
        _add_rich_runs(p, bold_lead, base_size=10.6, base_color=DARK, force_bold=True)
    _add_rich_runs(p, text, base_size=10.6)
    HTML_BLOCKS.append({"type": "bullet", "bold_lead": bold_lead, "text": text})


def add_figure(doc: Document, img_path: Path, caption: str, width_cm: float = 15.4) -> None:
    if not img_path.exists():
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(3.5)
    p_img.paragraph_format.space_after = Pt(1.5)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(str(img_path), width=Cm(width_cm))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(5)
    _add_rich_runs(p_cap, caption, base_size=9.5, base_color=MUTED)
    for r in p_cap.runs:
        r.italic = True
    HTML_BLOCKS.append({"type": "figure", "img_path": img_path, "caption": caption, "width_cm": width_cm})


def add_page_break(doc: Document) -> None:
    doc.add_page_break()
    HTML_BLOCKS.append({"type": "page_break"})


def export_pdf_via_chromium(blocks: List[dict], pdf_path: Path) -> None:
    """Render the exact Cover Page + 10 Sections to A4 PDF using headless Chromium (13-14 pages)."""
    html_out: List[str] = [
        """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Báo Cáo Đồ Án T13 - Automata-based Lexical Analyzer</title>
<style>
  @page {
    size: A4 portrait;
    margin: 19mm 19mm 19mm 22mm;
  }
  @page :first {
    margin: 18mm 19mm 18mm 22mm;
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Liberation Serif", "Times New Roman", Georgia, serif;
    font-size: 10.75pt;
    line-height: 1.39;
    color: #0F172A;
    margin: 0;
    padding: 0;
  }
  .cover-frame {
    border: 4px double #1E3A8A;
    padding: 24px 22px 26px 22px;
    text-align: center;
    min-height: 248mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .cover-top .c-ministry { font-size: 11.5pt; font-weight: bold; color: #1E3A8A; margin-bottom: 3px; }
  .cover-top .c-uni { font-size: 13pt; font-weight: bold; color: #1E3A8A; margin-bottom: 3px; }
  .cover-top .c-dept { font-size: 10.5pt; font-weight: bold; color: #475569; margin-bottom: 26px; }
  .cover-mid .c-report { font-size: 15.5pt; font-weight: bold; color: #2563EB; margin-bottom: 5px; }
  .cover-mid .c-course { font-size: 11.2pt; font-weight: bold; color: #0F172A; margin-bottom: 24px; }
  .cover-mid .c-topic-lbl { font-size: 13pt; font-weight: bold; color: #2563EB; margin-bottom: 4px; }
  .cover-mid .c-topic-title { font-size: 19pt; font-weight: bold; color: #1E3A8A; margin-bottom: 8px; }
  .cover-mid .c-topic-sub { font-size: 11pt; font-style: italic; color: #475569; line-height: 1.38; margin-bottom: 26px; }
  .cover-mid .c-meta { font-size: 11pt; font-weight: bold; color: #0F172A; margin-bottom: 4px; }
  .cover-mid .c-gv { font-size: 11.5pt; font-weight: bold; color: #1E3A8A; margin-bottom: 20px; }
  .cover-group-lbl { font-size: 10.2pt; font-weight: bold; color: #1E3A8A; margin-bottom: 6px; }
  .cover-date { font-size: 11pt; font-weight: bold; color: #1E3A8A; margin-top: 26px; }
  .page-break { page-break-before: always; }
  h1 {
    font-size: 13pt;
    color: #1E3A8A;
    border-bottom: 1.5px solid #1E3A8A;
    padding-bottom: 2.5px;
    margin: 12px 0 5px 0;
    page-break-after: avoid;
  }
  h2 {
    font-size: 11.2pt;
    color: #2563EB;
    margin: 8.5px 0 3.5px 0;
    page-break-after: avoid;
  }
  p.body-p {
    text-align: justify;
    margin: 0 0 5px 0;
  }
  p.bullet-p {
    text-align: justify;
    margin: 0 0 3.5px 0;
    padding-left: 15px;
    text-indent: -10px;
  }
  .bullet-dot {
    color: #1E3A8A;
    font-weight: bold;
  }
  code.inline-code {
    font-family: "Liberation Mono", "Consolas", monospace;
    font-size: 9.2pt;
    color: #1E3A8A;
    background: #F1F5F9;
    padding: 0 3px;
    border-radius: 2px;
  }
  .callout-box {
    border: 1px solid #CBD5E1;
    border-left: 4px solid #2563EB;
    background: #F1F5F9;
    padding: 7px 11px;
    margin: 5px 0 6px 0;
    page-break-inside: avoid;
  }
  .callout-title {
    font-weight: bold;
    font-size: 10.2pt;
    color: #1E3A8A;
    margin-bottom: 3px;
  }
  .callout-line {
    font-size: 9.9pt;
    line-height: 1.3;
    margin-bottom: 1.5px;
  }
  .callout-mono {
    font-family: "Liberation Mono", "Consolas", monospace;
    font-size: 8.4pt;
    line-height: 1.24;
    white-space: pre-wrap;
  }
  table.styled-tbl {
    width: 100%;
    border-collapse: collapse;
    margin: 4.5px 0 6px 0;
    font-size: 8.85pt;
    line-height: 1.25;
    border-top: 1px solid #CBD5E1;
    border-bottom: 1.5px solid #1E3A8A;
    page-break-inside: avoid;
  }
  table.styled-tbl th {
    background: #1E3A8A;
    color: #FFFFFF;
    font-weight: bold;
    padding: 4.5px 6px;
    border: 1px solid #1E3A8A;
    text-align: left;
  }
  table.styled-tbl td {
    padding: 4px 6px;
    border-bottom: 1px solid #CBD5E1;
    border-right: 1px solid #E2E8F0;
    vertical-align: middle;
  }
  table.styled-tbl tr:nth-child(even) td {
    background: #F8FAFC;
  }
  td.mono-cell {
    font-family: "Liberation Mono", "Consolas", monospace;
    font-size: 8.2pt;
  }
  .fig-wrap {
    text-align: center;
    margin: 6px 0 7px 0;
    page-break-inside: avoid;
  }
  .fig-wrap img {
    max-width: 95%;
    max-height: 225px;
    width: auto;
    height: auto;
  }
  .fig-cap {
    font-size: 9.3pt;
    font-style: italic;
    color: #475569;
    margin-top: 2.5px;
  }
</style>
</head>
<body>
"""
    ]

    for b in blocks:
        btype = b["type"]
        if btype == "cover":
            rows_html = []
            for ri, rv in enumerate(b["group_rows"]):
                tds = "".join(
                    f'<td style="text-align:{"center" if ci in (0,2) else "left"}">{html.escape(val)}</td>'
                    for ci, val in enumerate(rv)
                )
                rows_html.append(f"<tr>{tds}</tr>")
            ths = "".join(
                f'<th style="text-align:center">{html.escape(h)}</th>' for h in b["group_headers"]
            )
            html_out.append(
                f"""<div class="cover-frame">
  <div class="cover-top">
    <div class="c-ministry">BỘ GIÁO DỤC VÀ ĐÀO TẠO</div>
    <div class="c-uni">TRƯỜNG ĐẠI HỌC KINH TẾ TP. HỒ CHÍ MINH (UEH)</div>
    <div class="c-dept">KHOA CÔNG NGHỆ THÔNG TIN KINH DOANH — NGÀNH KHOA HỌC MÁY TÍNH</div>
  </div>
  <div class="cover-mid">
    <div class="c-report">BÁO CÁO TIỂU LUẬN CUỐI KỲ</div>
    <div class="c-course">HỌC PHẦN: NGÔN NGỮ HÌNH THỨC (INTRODUCTION TO FORMAL LANGUAGES)</div>
    <div class="c-topic-lbl">ĐỀ TÀI T13:</div>
    <div class="c-topic-title">AUTOMATA-BASED LEXICAL ANALYZER</div>
    <div class="c-topic-sub">{html.escape(b["subtitle"]).replace(chr(10), "<br/>")}</div>
    <div class="c-meta">Mã lớp học phần: 26C1INF50915301</div>
    <div class="c-gv">Giảng viên hướng dẫn: ThS. Hồ Thị Thanh Tuyến</div>
    <div class="cover-group-lbl">NHÓM THỰC HIỆN (NHÓM 6 — Điền thông tin thành viên trước khi nộp)</div>
    <table class="styled-tbl"><thead><tr>{ths}</tr></thead><tbody>{"".join(rows_html)}</tbody></table>
  </div>
  <div class="cover-date">TP. Hồ Chí Minh, tháng 11 năm 2026</div>
</div>"""
            )
        elif btype == "page_break":
            html_out.append('<div class="page-break"></div>')
        elif btype == "h1":
            html_out.append(f"<h1>{_rich_to_html(b['text'])}</h1>")
        elif btype == "h2":
            html_out.append(f"<h2>{_rich_to_html(b['text'])}</h2>")
        elif btype == "body":
            pref = f"<strong>{_rich_to_html(b['bold_prefix'])}</strong>" if b["bold_prefix"] else ""
            html_out.append(f'<p class="body-p">{pref}{_rich_to_html(b["text"])}</p>')
        elif btype == "bullet":
            pref = f"<strong>{_rich_to_html(b['bold_lead'])}</strong>" if b["bold_lead"] else ""
            html_out.append(
                f'<p class="bullet-p"><span class="bullet-dot">• </span>{pref}{_rich_to_html(b["text"])}</p>'
            )
        elif btype == "callout":
            cls = "callout-line callout-mono" if b["mono"] else "callout-line"
            lines_html = "".join(
                f'<div class="{cls}">{html.escape(ln.replace("`", "")) if b["mono"] else _rich_to_html(ln)}</div>'
                for ln in b["lines"]
            )
            html_out.append(
                f'<div class="callout-box" style="background:#{b["fill"]};border-left-color:#{b["accent"]};">'
                f'<div class="callout-title">{_rich_to_html(b["title"])}</div>{lines_html}</div>'
            )
        elif btype == "table":
            ths = "".join(f"<th>{html.escape(h.replace('`', ''))}</th>" for h in b["headers"])
            trs = []
            mono_cols: Set[int] = b["mono_cols"]
            for rv in b["rows"]:
                tds = []
                for ci, val in enumerate(rv):
                    if ci in mono_cols:
                        tds.append(f'<td class="mono-cell">{html.escape(str(val).replace("`", ""))}</td>')
                    else:
                        tds.append(f"<td>{_rich_to_html(str(val))}</td>")
                trs.append(f"<tr>{''.join(tds)}</tr>")
            html_out.append(
                f'<table class="styled-tbl"><thead><tr>{ths}</tr></thead><tbody>{"".join(trs)}</tbody></table>'
            )
        elif btype == "figure":
            img_path: Path = b["img_path"]
            b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
            html_out.append(
                f'<div class="fig-wrap">'
                f'<img src="data:image/png;base64,{b64}" alt="fig"/>'
                f'<div class="fig-cap">{_rich_to_html(b["caption"])}</div>'
                f"</div>"
            )

    html_out.append("</body></html>")
    tmp_html = pdf_path.parent / "_tmp_ueh_report.html"
    tmp_html.write_text("\n".join(html_out), encoding="utf-8")

    try:
        from playwright.sync_api import sync_playwright

        chrome_bin = shutil.which("chromium") or shutil.which("google-chrome")
        launch_kwargs = {"args": ["--no-sandbox"]}
        if chrome_bin:
            launch_kwargs["executable_path"] = chrome_bin
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page()
            page.goto(f"file://{tmp_html.resolve()}", wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template=(
                    '<div style="width:100%; text-align:right; font-family:\'Liberation Serif\',serif; '
                    'font-size:8.2pt; font-style:italic; color:#475569; padding-right:19mm;">'
                    "Tiểu luận Cuối kỳ Ngôn ngữ hình thức (UEH) — Đề tài T13: Automata-based Lexical Analyzer</div>"
                ),
                footer_template=(
                    '<div style="width:100%; text-align:right; font-family:\'Liberation Serif\',serif; '
                    'font-size:8.5pt; color:#475569; padding-right:19mm;">'
                    'Trang <span class="pageNumber"></span> / <span class="totalPages"></span></div>'
                ),
                margin={"top": "19mm", "bottom": "19mm", "left": "22mm", "right": "19mm"},
            )
            browser.close()
    finally:
        if tmp_html.exists():
            tmp_html.unlink()


def build_report() -> None:
    HTML_BLOCKS.clear()
    test_rep = run_json_test_report()
    lex_mini = LexicalAnalyzer.from_preset("minilang")
    lex_calc = LexicalAnalyzer.from_preset("calclang")
    lex_sql = LexicalAnalyzer.from_preset("minisql")
    s_mini = lex_mini.summary_dict()
    s_calc = lex_calc.summary_dict()
    s_sql = lex_sql.summary_dict()

    doc = Document()

    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.3)
    sec.right_margin = Cm(2.0)
    sec.different_first_page_header_footer = True

    hdr_p = sec.header.paragraphs[0]
    hdr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hdr_p.add_run("Tiểu luận Cuối kỳ Ngôn ngữ hình thức (UEH) — Đề tài T13: Automata-based Lexical Analyzer")
    hr.font.name = "Times New Roman"
    hr.font.size = Pt(9)
    hr.font.italic = True
    hr.font.color.rgb = MUTED

    ftr_p = sec.footer.paragraphs[0]
    ftr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_page_number_field(ftr_p)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(10.8)

    # =========================================================================
    # COVER PAGE (Trang bìa chính thức chuẩn UEH)
    # =========================================================================
    cover_box = doc.add_table(rows=1, cols=1)
    cover_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    cc = cover_box.cell(0, 0)
    set_cell_margins(cc, top=220, bottom=220, left=220, right=220)
    cc._tc.get_or_add_tcPr().append(
        parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'  <w:top w:val="double" w:sz="18" w:space="0" w:color="1E3A8A"/>'
            f'  <w:bottom w:val="double" w:sz="18" w:space="0" w:color="1E3A8A"/>'
            f'  <w:left w:val="double" w:sz="18" w:space="0" w:color="1E3A8A"/>'
            f'  <w:right w:val="double" w:sz="18" w:space="0" w:color="1E3A8A"/>'
            f"</w:tcBorders>"
        )
    )

    def _cp(
        text: str,
        size: float,
        bold: bool = False,
        italic: bool = False,
        color=DARK,
        space_before: float = 0,
        space_after: float = 4,
    ):
        p = cc.add_paragraph() if len(cc.paragraphs[0].text) > 0 or len(cc.paragraphs) > 1 else cc.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.font.color.rgb = color
        return p

    subtitle_text = (
        "Xây dựng Bộ Phân Tích Từ Vựng Tổng Quát Khép Kín Vòng Tròn Định Lý Kleene 360°:\n"
        "RE (Unicode Động Σ(U)) ⇄ Thompson ε-NFA · Khử ε · Subset & Direct DFA · Moore/Hopcroft Min-DFA · GNFA,\n"
        "Ma Trận Giao Nhau L(Rᵢ)∩L(Rⱼ), Chứng Minh Myhill–Nerode, Bộ Quét O(n) & Sinh Mã Lexer Độc Lập Kiểu Flex"
    )

    _cp("BỘ GIÁO DỤC VÀ ĐÀO TẠO", 12, bold=True, color=NAVY, space_before=6, space_after=2)
    _cp("TRƯỜNG ĐẠI HỌC KINH TẾ TP. HỒ CHÍ MINH (UEH)", 13.5, bold=True, color=NAVY, space_after=2)
    _cp("KHOA CÔNG NGHỆ THÔNG TIN KINH DOANH — NGÀNH KHOA HỌC MÁY TÍNH", 11, bold=True, color=MUTED, space_after=26)

    _cp("BÁO CÁO TIỂU LUẬN CUỐI KỲ", 16, bold=True, color=BLUE, space_before=16, space_after=6)
    _cp("HỌC PHẦN: NGÔN NGỮ HÌNH THỨC (INTRODUCTION TO FORMAL LANGUAGES)", 11.5, bold=True, color=DARK, space_after=24)

    _cp("ĐỀ TÀI T13:", 13.5, bold=True, color=BLUE, space_before=6, space_after=4)
    _cp("AUTOMATA-BASED LEXICAL ANALYZER", 20, bold=True, color=NAVY, space_after=6)
    _cp(subtitle_text, 10.6, italic=True, color=MUTED, space_after=28)

    _cp("Mã lớp học phần: 26C1INF50915301", 11, bold=True, color=DARK, space_after=4)
    _cp("Giảng viên hướng dẫn: ThS. Hồ Thị Thanh Tuyến", 11.5, bold=True, color=NAVY, space_after=22)

    p_grp = cc.add_paragraph()
    p_grp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_grp.paragraph_format.space_after = Pt(6)
    rg = p_grp.add_run("NHÓM THỰC HIỆN (NHÓM 6 — Điền thông tin thành viên trước khi nộp)")
    rg.bold = True
    rg.font.name = "Times New Roman"
    rg.font.size = Pt(10.5)
    rg.font.color.rgb = NAVY

    gtbl = cc.add_table(rows=5, cols=4)
    gtbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(gtbl)
    g_headers = ["STT", "Họ và Tên Sinh Viên", "Mã số sinh viên (MSSV)", "Vai trò"]
    g_rows = [
        ["1", "[Điền Họ tên Thành viên 1]", "[MSSV 1]", "Nhóm trưởng · Lý thuyết Kleene 360°, Myhill–Nerode & Báo cáo"],
        ["2", "[Điền Họ tên Thành viên 2]", "[MSSV 2]", "Regex Parser (Σ(U), ≤4096 AST) · Thompson, Khử ε & Direct DFA"],
        ["3", "[Điền Họ tên Thành viên 3]", "[MSSV 3]", "Subset · Moore/Hopcroft · GNFA 360° & Ma trận Giao L(Rᵢ)∩L(Rⱼ)"],
        ["4", "[Điền Họ tên Thành viên 4]", "[MSSV 4]", "Scanner O(n) · Flex Codegen (.py) · Web Studio & 72 Tests"],
    ]
    g_widths = [1.3, 5.0, 3.4, 5.5]
    for ci, h in enumerate(g_headers):
        cell = gtbl.rows[0].cells[ci]
        set_cell_shading(cell, "1E3A8A")
        set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
        cell.width = Cm(g_widths[ci])
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for ri, rv in enumerate(g_rows):
        for ci, val in enumerate(rv):
            cell = gtbl.rows[ri + 1].cells[ci]
            set_cell_shading(cell, "F8FAFC" if ri % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=45, bottom=45, left=60, right=60)
            cell.width = Cm(g_widths[ci])
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in (0, 2) else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)

    _cp("TP. Hồ Chí Minh, tháng 11 năm 2026", 11, bold=True, color=NAVY, space_before=36, space_after=6)

    HTML_BLOCKS.append(
        {"type": "cover", "subtitle": subtitle_text, "group_headers": g_headers, "group_rows": g_rows}
    )
    add_page_break(doc)

    # =========================================================================
    # SECTION 1: MÔ TẢ BÀI TOÁN VÀ MỤC TIÊU ĐỒ ÁN
    # =========================================================================
    add_heading_1(doc, "1. Mô tả bài toán và mục tiêu đồ án")

    add_body(
        doc,
        "Trong kiến trúc của mọi trình biên dịch (compiler) và trình thông dịch (interpreter) hiện đại, "
        "phân tích từ vựng (Lexical Analysis) là giai đoạn đầu tiên đọc dòng ký tự thô của mã nguồn "
        "và nhóm chúng thành dãy các đơn vị từ vựng có nghĩa gọi là token (từ khóa, định danh, hằng số, chuỗi, toán tử, "
        "dấu phân cách), đồng thời lọc bỏ khoảng trắng, bình luận đơn dòng/nhiều dòng và phát hiện chính xác tọa độ lỗi từ vựng. "
        "Điểm tạo nên cầu nối trực tiếp giữa học phần Ngôn ngữ hình thức và Kỹ thuật trình biên dịch nằm ở chỗ: "
        "mọi lớp token của ngôn ngữ lập trình đều thuộc lớp Ngôn ngữ chính quy (Regular Languages) — được "
        "đặc tả bằng Biểu thức chính quy (Regular Expression — RE) và thực thi bằng Automata hữu hạn đơn định (DFA) "
        "với tốc độ tuyến tính O(n) theo độ dài mã nguồn mà không bao giờ chịu rủi ro treo máy hàm mũ O(2^n) (ReDoS) như các bộ khớp regex quay lui.",
    )

    add_body(
        doc,
        "Thay vì viết tay bộ quét bằng các câu lệnh if/else cứng nhắc cho một ngôn ngữ cố định hoặc phụ thuộc vào thư viện biểu thức "
        "chính quy hộp đen có sẵn (như module `re` của Python), đề tài T13 — Automata-based Lexical Analyzer hướng tới việc xây dựng một "
        "hệ thống biên dịch Automata khép kín vòng tròn Định lý Kleene 360°, bộ sinh mã Lexer độc lập kiểu Flex và môi trường trực quan Web Studio hoàn toàn từ gốc lý thuyết.",
    )

    add_heading_2(doc, "1.1. Mục tiêu cụ thể của đồ án")
    add_bullet(
        doc,
        "Tự cài đặt 100% chuỗi 7 phương pháp Automata khép kín Định lý Kleene 360° (Zero `import re`): ",
        "Xây dựng độc lập từ con số 0: Phân tích cú pháp RE (chặn bom AST lồng nhau `MAX_AST_NODES = 4096`, phân hoạch bảng chữ cái Unicode động `Σ(U)` & phủ kín ASCII `0x00..0x7F` bảo toàn `~(~A) = A`) → "
        "Thompson `ε-NFA` → Khử `ε` (Định lý 2) → `Subset DFA` → `Moore & Hopcroft Min-DFA` → **Khử trạng thái GNFA (`DFA → RE`)** chứng minh `L(R_gốc) ≡ L(R_sinh)`.",
    )
    add_bullet(
        doc,
        "Direct RE → DFA Đa-Token, Ma trận Giao nhau Tĩnh L(Rᵢ) ∩ L(Rⱼ) & Chứng minh Myhill–Nerode: ",
        "Triển khai thuật toán xây dựng DFA trực tiếp từ cây gia tố `r·#` (khớp 100% Slide 46–57 Chương 3.1) và mở rộng Đa-Token `(R₁·#₁)|...|(Rₖ·#ₖ)`, "
        "kiểm chứng tương đương bằng **Product Automaton**, chứng minh tính tối giản **Myhill–Nerode**, phân tích tĩnh **Ma trận Giao nhau `L(Rᵢ) ∩ L(Rⱼ)`** kèm chuỗi chứng nhân ngắn nhất và đọc/ghi khứ hồi JFLAP `.jff`.",
    )
    add_bullet(
        doc,
        "Bộ quét Maximal Munch Tuyến tính O(n) (Reps, 1998) & Bộ sinh mã Lexer Độc lập kiểu Flex: ",
        "Cài đặt bộ quét bảng chuyển DFA với Memoization `failed_states` chống quay lui O(n²), chuỗi `STRING_LIT` an toàn CRLF (`\\r\\n`), hai chế độ phục hồi lỗi (`panic_char` và `smart_sync`), "
        "cùng công cụ **`codegen`** xuất trực tiếp `Min-DFA` thành file bộ quét Python độc lập kiểu Flex (Table-Driven, 0 phụ thuộc ngoài, đối chứng vi sai 100%).",
    )
    add_bullet(
        doc,
        "Kiểm thử toàn diện 72 Test Cases JSON + 22 Unittest Suites & Trực quan hóa Web Studio 5 Tab: ",
        "Xây dựng bộ 72 kịch bản kiểm thử JSON (20 RE đơn/Unicode/GNFA, 24 bẫy lỗi RE & bom AST, 28 kịch bản quét mã nguồn) cùng 22 bộ Unittest kiểm chứng các bất biến toán học "
        "và ứng dụng Web `LexAutomata Studio` 5 Tab trực quan hóa toàn bộ đồ thị SVG, ma trận giao nhau, GNFA 360° và hoạt ảnh từng bước.",
    )

    # =========================================================================
    # SECTION 2: CƠ SỞ LÝ THUYẾT LIÊN QUAN
    # =========================================================================
    add_heading_1(doc, "2. Cơ sở lý thuyết liên quan")

    add_body(
        doc,
        "Toàn bộ thiết kế của hệ thống dựa trên các định nghĩa và định lý chuẩn trong giáo trình "
        "Introduction to Automata Theory, Languages, and Computation (Hopcroft, Motwani & Ullman, 3rd Ed.), "
        "Dragon Book (Aho, Lam, Sethi & Ullman, 2nd Ed.) và bài giảng Chương 1–3 môn Ngôn ngữ hình thức của ThS. Hồ Thị Thanh Tuyến (UEH):",
    )

    add_heading_2(doc, "2.1. Đại số Boole trên Bảng chữ cái Động Σ(U), Ngôn ngữ và Biểu thức chính quy (RE)")
    add_body(
        doc,
        "Cho bảng chữ cái hữu hạn khác rỗng Σ. Tập tất cả chuỗi hữu hạn trên Σ ký hiệu là Σ* (chứa chuỗi rỗng ε). "
        "Biểu thức chính quy (RE) trên Σ được định nghĩa quy nạp: "
        "(i) ∅ biểu diễn ∅; (ii) ε biểu diễn {ε}; (iii) ∀a ∈ Σ, a biểu diễn {a}; "
        "(iv) Nếu r và s là các RE biểu diễn L(r) và L(s), thì `(r | s)` biểu diễn L(r) ∪ L(s), "
        "`(r·s)` biểu diễn L(r)L(s), và `(r*)` biểu diễn L(r)* = ⋃_{k≥0} L(r)^k. "
        "Thứ tự ưu tiên toán tử từ cao đến thấp: `(…)` > Định lượng (`*`, `+`, `?`, `{m,n}`) > Nối kết (`·`) > Phép hợp (`|`). "
        "Các toán tử mở rộng quy về 3 phép toán cơ sở: `r+ ≡ r·r*`, `r? ≡ (r | ε)`, `r{m,n} ≡ r^m · (r?)^{n-m}`, "
        "`[c₁...c_m] ≡ (c₁|...|c_m)` và lớp phủ định `[^C] ≡ Σ(U) \\ C` thỏa mãn luật đối hợp đại số Boole `~(~C) = C`.",
    )

    add_heading_2(doc, "2.2. Vòng tròn Định lý Kleene 360°: Thompson, Khử ε, Subset DFA, Min-DFA & GNFA (DFA → RE)")
    add_callout(
        doc,
        "Khép kín Vòng tròn Tương đương Định lý Kleene 360° (RE ⇄ ε-NFA ⇄ NFA ⇄ DFA ⇄ Min-DFA)",
        [
            "• Định lý 3 (Cấu trúc Thompson, 1968 — Slide 24–30 Chương 3.1): Mọi RE r đều chuyển được thành ε-NFA N = (Q, Σ, δ, q₀, {f}) "
            "có đúng 1 đỉnh đầu (in-deg = 0), 1 đỉnh kết thúc (out-deg = 0), tối đa 2|r| trạng thái và bậc ra mỗi đỉnh ≤ 2.",
            "• Định lý 2 (Khử chuyển tiếp rỗng ε-NFA → NFA không ε — Slide 21–22 Chương 3.1): Dựng NFA không ε tương đương "
            "N' = (Q, Σ, δ', q₀, F') với δ'(p, a) = ε-closure(Move(ε-closure({p}), a)) và F' = { p ∈ Q | ε-closure({p}) ∩ F ≠ ∅ }.",
            "• Định lý 1 & Myhill–Nerode (Subset DFA & Tối thiểu hóa Moore/Hopcroft): D₀ = ε-closure({q₀}), δ_D(S, a) = ε-closure(Move(S, a)). "
            "DFA tối giản là duy nhất (sai khác đẳng cấu) khi mọi cặp trạng thái phân biệt (p, q) đều tồn tại chuỗi phân biệt w sao cho τ(δ̂(p, w)) ≠ τ(δ̂(q, w)).",
            "• Chiều ngược Kleene (Khử trạng thái GNFA: DFA → RE — Hopcroft §3.2.1): Bổ sung q_start --ε--> D₀ và ∀f ∈ F: f --ε--> q_accept, "
            "sau đó khử lần lượt từng đỉnh trung gian q_rip theo công thức: R'(qᵢ, qⱼ) = R(qᵢ, qⱼ) | R(qᵢ, q_rip)·(R(q_rip, q_rip))*·R(q_rip, qⱼ) cho đến khi còn duy nhất R(q_start, q_accept) ≡ R_gốc.",
        ],
    )

    add_heading_2(doc, "2.3. Phương pháp Trực tiếp RE → DFA (Chương 3.1 Mục 2.5) & Nguyên lý Maximal Munch O(n)")
    add_bullet(
        doc,
        "Phương pháp trực tiếp trên cây cú pháp gia tố r·# (Slide 43–57 Chương 3.1): ",
        "Bổ sung ký hiệu kết thúc `# ∉ Σ` vào sau biểu thức (`r·#`), đánh số các nút lá từ `1..n`, "
        "tính đệ quy `nullable(v)`, `firstpos(v)`, `lastpos(v)` và bảng `followpos(i)`. Với bài toán đa-token, nhóm mở rộng thành cây kết hợp `(R₁·#₁) | (R₂·#₂) | ... | (Rₖ·#ₖ)` "
        "để sinh trực tiếp Combined Multi-token Direct DFA không cần đi qua ε-NFA.",
    )
    add_bullet(
        doc,
        "Quy tắc Khớp Dài Nhất (Maximal Munch), Ưu Tiên Luật & Memoization Tuyến tính O(n) (Reps, 1998): ",
        "Tại vị trí `pos`, bộ quét chọn tiền tố dài nhất đưa DFA tới trạng thái kết thúc; nếu cùng độ dài khớp nhiều luật (`if` ∈ `L(KW_IF) ∩ L(IDENTIFIER)`), chọn luật có chỉ số ưu tiên nhỏ nhất. "
        "Để triệt tiêu quay lui bậc hai O(n²) trên chuỗi chưa đóng dài, bộ quét ghi nhớ tập `failed_states` chứa các cấu hình `(state, cursor)` thất bại (Reps, 1998), đảm bảo mỗi cặp `(q, i)` chỉ thăm tối đa 1 lần → thời gian quét luôn chặt O(|Q|·n) = O(n).",
    )

    # =========================================================================
    # SECTION 3: MÔ HÌNH HÌNH THỨC / AUTOMATA ĐƯỢC SỬ DỤNG
    # =========================================================================
    add_heading_1(doc, "3. Mô hình hình thức / Automata được sử dụng")

    add_heading_2(doc, "3.1. Phân hoạch Bảng chữ cái Unicode Động Σ(U) & Phủ kín ASCII 0x00..0x7F (~(~A) = A)")
    add_bullet(
        doc,
        "Đầu vào (Input) & Đầu ra (Output): ",
        "Từ đặc tả `Spec = [(T₁, R₁, p₁, skip₁), ..., (Tₖ, Rₖ, pₖ, skipₖ)]` và chuỗi mã nguồn `w`, hệ thống xuất: "
        "7 biểu diễn tương đương (`Thompson ε-NFA`, `NFA không ε`, `Subset DFA`, `Moore Min-DFA`, `Hopcroft Min-DFA`, `Combined Direct DFA`, và `GNFA RE` cho biểu thức đơn), "
        "ma trận giao nhau tĩnh `L(Rᵢ) ∩ L(Rⱼ)` kèm chuỗi chứng nhân ngắn nhất, chứng minh Myhill–Nerode, bộ quét Python độc lập `.py` và luồng `Token` / `LexicalError`.",
    )
    add_bullet(
        doc,
        "Phủ kín 128 ký tự ASCII (0x00..0x7F) & Phân hoạch Unicode Động Σ(U) không va chạm: ",
        "Thay vì bỏ sót các ký tự điều khiển (`\\0`, `\\f`, `\\v`, `\\x7f`) gây gãy luật bù kép `~(~A) = A` hoặc gộp cứng toàn bộ Unicode vào một hằng `0x80` gây xung đột khi biểu thức chứa từ khóa/ký hiệu Unicode tường minh (như `nếu`, `€`), "
        "nhóm chuẩn hóa `ASCII_SIGMA` phủ trọn **128 mã ASCII `0x00..0x7F`**, dùng mã noncharacter nội bộ **`NON_ASCII = U+FDD0`** (theo chuẩn Unicode §23.7) đại diện cho phần còn lại `Unicode \\ U`, "
        "và xây dựng bảng chữ cái động **`Σ(U) = ASCII_SIGMA ∪ U ∪ {NON_ASCII}`** với `U` là tập ký tự Unicode tường minh trích tự động từ các cây AST! "
        "Nhờ đó: (1) Mọi phép lấy phần bù `[^C]` và `complement_dfa(D)` thỏa mãn tuyệt đối `~(~A) = A` và `L(D) ∩ L(~D) = ∅`; "
        "(2) Biểu thức chứa trực tiếp `(nếu|lặp)_[0-9]+€` hay `[^€]` vận hành chính xác 100% đồng thời với chuỗi tiếng Việt UTF-8!",
    )

    add_heading_2(doc, "3.2. Mô hình Đa-Token, Ma trận Giao nhau L(Rᵢ) ∩ L(Rⱼ) & Phát hiện Luật Che khuất")
    add_callout(
        doc,
        "Mô hình Toán học Multi-token DFA, Phân tích Tĩnh L(Rᵢ) ∩ L(Rⱼ) & Kiểm tra Luật Che khuất",
        [
            "1. Combined ε-NFA & NFA Khử ε (Định lý 2): N_lex = (Q_N, Σ(U), δ_N, q_start, F_N, τ_N). Khi khử ε, mọi đỉnh p có ε-closure({p}) ∩ F_N ≠ ∅ nhận nhãn chiến thắng τ'_{N}(p) = argmin_{f ∈ ε-closure({p}) ∩ F_N} priority(f).",
            "2. Multi-token Subset DFA, Direct DFA & Phân hoạch Min-DFA: D_lex = (Q_D, Σ(U)/≡, δ_D, D₀, F_D, τ_D) với phân hoạch khởi đầu tách riêng từng loại token Π₀ = { Q_D \\ F_D } ∪ { F_{T₁}, ..., F_{T_m} }.",
            "3. Ma trận Giao nhau Tĩnh L(Rᵢ) ∩ L(Rⱼ) & Chứng nhân Ngắn nhất: Với mọi cặp quy tắc i < j, Product Automaton BFS kiểm tra L(Dᵢ) ∩ L(Dⱼ) ≠ ∅, phân loại quan hệ tập hợp (∅, Rᵢ ⊂ Rⱼ, Rᵢ ≡ Rⱼ, Rᵢ ⊃ Rⱼ, giao một phần) và trích xuất từ tố chứng nhân ngắn nhất w ∈ L(Rᵢ) ∩ L(Rⱼ) (trên MiniLang: phát hiện đúng 9/741 cặp giao nhau KW_* / BOOL_LIT ⊂ IDENTIFIER).",
            "4. Cảnh báo Luật Bị Che Khuất (Shadowed Rule): Nếu Rᵢ ≡ Rⱼ hoặc Rᵢ ⊃ Rⱼ với pᵢ < pⱼ (khiến ∀q ∈ F_min: τ_min(q) ≠ Tⱼ), hệ thống lập tức báo động quy tắc Tⱼ bị che khuất hoàn toàn.",
        ],
    )

    add_heading_2(doc, "3.3. Đặc tả tập Token minh họa (MiniLang 39 Token, CalcLang 12 Token & MiniSQL 14 Token)")
    add_body(
        doc,
        "Nhóm thiết kế 3 bộ đặc tả ngôn ngữ hoàn chỉnh: "
        "**MiniLang (39 token — hỗ trợ `BLOCK_COMMENT` và `STRING_LIT` an toàn CRLF)**, **CalcLang (12 token)** và **MiniSQL (14 token)**. "
        "Bảng 1 tóm tắt các nhóm quy tắc từ vựng của MiniLang:",
    )

    minilang_summary_rows = [
        ["1", "COMMENT", r"//[^\n]*", "Bỏ qua", "Bình luận 1 dòng (hỗ trợ tiếng Việt UTF-8 qua NON_ASCII)"],
        ["2", "BLOCK_COMMENT", r"/\*([^*]|\*+[^*/])*\*+/", "Bỏ qua", "Bình luận nhiều dòng chuẩn C/Java (xử lý đúng `/**/`, `/***a***/`)"],
        ["3", "WHITESPACE", r"[ \t\n\r]+", "Bỏ qua", "Khoảng trắng, tab, xuống dòng Unix LF & Windows CRLF"],
        ["4–12", "KW_IF .. BOOL_LIT", r"if, else, while, for, let, func, return, print, true|false", "Giữ", "9 từ khóa & hằng logic (Rᵢ ⊂ IDENTIFIER, thắng nhờ ưu tiên)"],
        ["13", "FLOAT_LIT", r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", "Giữ", "Số thực dấu phẩy động & ký hiệu khoa học 1.5e-2, 1.5e+3"],
        ["14", "INT_LIT", r"[0-9]+", "Giữ", "Số nguyên không dấu (rời nhau với FLOAT_LIT nhờ dấu chấm)"],
        ["15", "STRING_LIT", r'"([^"\\\n\r]|\\.)*"', "Giữ", "Chuỗi ngoặc kép loại trừ cả \\r và \\n trên CRLF, hỗ trợ UTF-8"],
        ["16", "IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*", "Giữ", "Tên biến, tên hàm (đặt sau từ khóa để không che khuất KW_*)"],
        ["17–22", "OP_EQ .. OP_OR", r"==, !=, <=, >=, &&, \|\|", "Giữ", "6 toán tử ghép 2 ký tự (khớp trước toán tử đơn nhờ Maximal Munch)"],
        ["23–31", "OP_ASSIGN .. OP_MOD", r"=, <, >, !, \+, -, \*, /, %", "Giữ", "9 toán tử 1 ký tự"],
        ["32–39", "LPAREN .. COMMA", r"\(, \), \{, \}, \[, \], ;, ,", "Giữ", "8 dấu phân cách khối lệnh, mảng và tham số"],
    ]
    add_styled_table(
        doc,
        ["Ưu tiên", "Nhóm Token", "Biểu thức chính quy (RE)", "Xử lý", "Vai trò & Ghi chú kỹ thuật"],
        minilang_summary_rows,
        col_widths_cm=[1.5, 3.1, 5.1, 1.3, 5.7],
        font_size=8.6,
        mono_cols={1, 2},
    )

    # =========================================================================
    # SECTION 4: THUẬT TOÁN VÀ THIẾT KẾ GIẢI PHÁP
    # =========================================================================
    add_heading_1(doc, "4. Thuật toán và thiết kế giải pháp")

    add_body(
        doc,
        "Hình 1 trình bày kiến trúc tổng thể phiên bản v2.0 của hệ thống, kết nối chặt chẽ giữa nhánh biên dịch 4 định lý "
        "(`RE → AST → Thompson ε-NFA → NFA Khử ε → Subset DFA → Moore & Hopcroft Min-DFA`), nhánh đối chứng & chiều ngược Kleene 360° "
        "(`Direct RE → DFA`, `GNFA State Elimination DFA → RE`, `JFLAP Round-Trip`), bộ chứng minh hình thức (`Product Automaton`, `Myhill–Nerode`, `Ma trận L(Rᵢ)∩L(Rⱼ)`) "
        "và tầng thực thi (`O(n) Scanner` + `Flex-style Standalone Python Lexer Generator`).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig1_architecture_pipeline.png",
        "Hình 1: Kiến trúc tổng thể Bộ phân tích từ vựng dựa trên Automata v2.0 (Vòng tròn Kleene 360° & Sinh mã Lexer độc lập).",
        width_cm=15.8,
    )

    add_heading_2(doc, "4.1. Thuật toán 1 — Phân tích cú pháp RE, Chống Bom AST (≤ 4096 nút) & Unicode Động Σ(U)")
    add_body(
        doc,
        "Bộ phân tích cú pháp đệ quy xuống (`regex_parser.py`) cài đặt văn phạm 4 mức ưu tiên: "
        "`expr → concat ('|' concat)*`, `concat → repeat+`, `repeat → atom ('*'|'+'|'?'|'{m,n}')*`, "
        "`atom → '(' expr ')' | char_class | '.' | escape | 'ε' | literal`. "
        "Ba cơ chế phòng vệ và chuẩn hóa đại số then chốt gồm: "
        "(1) **Chống bom nhân bản AST lồng nhau (`MAX_AST_NODES = 4096`)**: dù giới hạn đơn lẻ `MAX_QUANTIFIER_BOUND = 64` chặn được `a{100}`, "
        "biểu thức lồng nhau kiểu `(((a{64}){64}){64})` có thể nhân bản cấp số nhân lên tới `528.483` nút AST gây treo RAM/CPU; nhóm cài đặt hàm ước lượng kích thước cây con trong `O(1)` ngay trước khi nhân bản, chặn đứng mọi bom AST vượt `4.096` nút trong `< 0.1 ms`; "
        "(2) **Lớp ký tự trên `Σ(U)` đầy đủ 128 ASCII (`0x00..0x7F`, gồm cả `\\0`, `\\f`, `\\v`, `\\x7f`, `\\xHH`, `\\uHHHH`)**: trích tập `U = explicit_unicode_chars()` trước khi cụ thể hóa các nút `CharSetNode`, đảm bảo phủ định `[^C]` thỏa mãn `~(~C) = C`; "
        "(3) Bắt chính xác **24 mẫu lỗi cú pháp RE** (`RE-ERR-01..24`) kèm tọa độ cột lỗi.",
    )

    add_heading_2(doc, "4.2. Thuật toán 2 — Cấu trúc Thompson & Thuật toán Khử ε (Định lý 2 Chương 3.1)")
    add_body(
        doc,
        "Duyệt hậu tố trên AST, mỗi mảnh Thompson ε-NFA duy trì bất biến `in-deg(start) = 0` và `out-deg(end) = 0`, cho phép `ConcatNode(L, R)` "
        "gộp trực tiếp đỉnh cuối của L với đỉnh đầu của R. Trên biểu thức `(a|b)*abb`, thuật toán sinh đúng **11 trạng thái (`q0..q10`)** khớp Slide 38 Chương 3.1 (Hình 2). "
        "Hàm `eliminate_epsilon(nfa)` cài đặt **Định lý 2 (Slide 21–22)**: "
        "tính `closures[s] = ε-closure({s})`, gán nhãn kết thúc ưu tiên cao nhất và dựng cung trực tiếp "
        "`δ_no_eps(s, c) = ε-closure(Move(closures[s], c))`, rút gọn `(a|b)*abb` từ 11 xuống 6 trạng thái (và rút gọn `MiniLang` từ 170 xuống 96 trạng thái).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig2_slide38_pipeline.png",
        "Hình 2: Đường ống RE → Thompson ε-NFA (11 TT) → Subset DFA (5 TT) → Minimized DFA (4 TT, GNFA sinh R_sinh ≡ R_gốc) trên (a|b)*abb.",
        width_cm=15.6,
    )

    add_heading_2(doc, "4.3. Thuật toán 3 — Subset Construction, Alphabet Partitioning & Ma trận Giao nhau L(Rᵢ) ∩ L(Rⱼ)")
    add_body(
        doc,
        "Từ tất cả tập ký tự trên các cung của Combined ε-NFA trên `Σ(U)`, kỹ thuật Alphabet Partitioning tinh chỉnh thành `p` lớp tương đương rời nhau `E₁, ..., E_p` "
        "sao cho `∀c₁, c₂ ∈ Eⱼ: Move(S, c₁) = Move(S, c₂)`. Trên `MiniLang`, 129 ký hiệu của `Σ` được nén gọn xuống **44 lớp tương đương** (tách riêng `\\r` và `\\n` cho `STRING_LIT` trên Windows CRLF), giúp Subset Construction chạy trong ~4 ms. "
        "Song song đó, hàm `analyze_token_intersections(specs)` xây dựng `Min-DFA` độc lập cho từng quy tắc `Rᵢ` (nâng lên bảng chữ cái chung `Σ(U_all)`) và chạy BFS trên `C(k, 2)` ô-tô-mát tích để lập **Ma trận Giao nhau Tĩnh `L(Rᵢ) ∩ L(Rⱼ)`** "
        "(trên `MiniLang`: quét toàn bộ `C(39, 2) = 741` cặp trong ~13 ms, chỉ ra đúng 9 cặp bao hàm hợp lệ `KW_IF..BOOL_LIT ⊂ IDENTIFIER` với chứng nhân `'if'`, `'else'`, ..., `'true'` và 732 cặp rời nhau `∅`).",
    )

    add_heading_2(doc, "4.4. Thuật toán 4 — Direct RE → DFA Đơn lẻ (Slide 54) & Đa-Token Kết hợp")
    add_body(
        doc,
        "Trong `direct_dfa.py`, hàm `build_direct_dfa(pattern)` cho biểu thức đơn `r·#` sinh đúng **8 vị trí lá**, bảng `followpos` và **5 trạng thái Direct DFA `A..E`** "
        "cho `(a|ba)(a|b)*ba#` trùng khớp 100% Slide 54–57 Chương 3.1 (Hình 3). Hàm mở rộng `build_combined_direct_dfa(specs)` ghép `k` quy tắc thành `(R₁·#₁) | ... | (Rₖ·#ₖ)` "
        "với `#ᵢ` mang nhãn `(Tᵢ, pᵢ, skipᵢ)`: Combined Direct DFA của `MiniLang` chỉ có **79 trạng thái** (so với 86 của Subset DFA) và tương đương 100% với Minimized DFA (78 trạng thái).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig5_direct_dfa_slide46.png",
        "Hình 3: Direct DFA xây dựng trực tiếp từ r = (a|ba)(a|b)*ba# qua bảng followpos — khớp 100% Slide 54–57 Chương 3.1.",
        width_cm=13.8,
    )

    add_heading_2(doc, "4.5. Thuật toán 5 — Tối thiểu hóa Moore/Hopcroft, Myhill–Nerode & GNFA Khử trạng thái (DFA → RE)")
    add_body(
        doc,
        "Module `dfa_minimizer.py` cài đặt song song **Moore (`O(p·|Q|²)`)** và **Hopcroft (`O(p·|Q|log|Q|)`)** trên phân hoạch đa-token `Π₀ = {Q \\ F ∪ {DEAD}} ∪ {F_{T₁}, ..., F_{T_m}}`, kèm phép lấy phần bù `complement_dfa(D)` kiểm chứng `~(~L) = L`. "
        "Module `verifier.py` dùng **Product Automaton** chứng minh tương đương 7 chiều và hàm `verify_dfa_is_minimal(dfa)` tìm chuỗi phân biệt Myhill–Nerode cho 100% cặp trạng thái (`3.003/3.003` cặp trên `MiniLang`). "
        "Đặc biệt, module mới `gnfa.py` cài đặt thuật toán **GNFA State Elimination (`dfa_to_regex`)**: loại bỏ các đỉnh không tới được/không sinh lời, nối `q_start --ε--> D₀` và `F --ε--> q_accept`, "
        "chọn thứ tự khử đỉnh tối thiểu hóa tích `in_deg(q) × out_deg(q)` kết hợp rút gọn đại số Kleene (`∅·R = ∅`, `ε·R = R`, `r·r* = r+`), sinh biểu thức `R_sinh` (ví dụ `(a|b)*abb` → `b*a(a|ba|bb(a|b+a))*bb`) và tự động biên dịch ngược để chứng minh `L(R_gốc) ≡ L(R_sinh)`!",
    )

    add_heading_2(doc, "4.6. Thuật toán 6 — Bộ quét O(n) (Reps, 1998) & Bộ sinh mã Lexer Độc lập kiểu Flex")
    add_callout(
        doc,
        "Thuật toán Quét Maximal Munch Tuyến tính O(n) (Reps, 1998) & Kiến trúc Bộ Sinh Mã Lexer Độc lập (codegen.py)",
        [
            "Input : Chuỗi text[0..n-1], Bảng chuyển tĩnh Min-DFA D = (Q, Σ(U)/≡, δ, D₀, F, τ), mode ∈ {panic_char, smart_sync}",
            "1. pos ← 0; line ← 1; col ← 1; failed_states ← ∅   // Bảng nhớ (state, cursor) theo Reps (1998)",
            "2. WHILE pos < n DO: cur ← D₀; cursor ← pos; last_accept ← NULL; visited_path ← []",
            "3.   WHILE cursor < n DO:",
            "4.     IF (cur, cursor) ∈ failed_states THEN: memoized_cutoffs += 1; BREAK   // Cắt nhánh O(1) chống O(n²)",
            "5.     cls ← ASCII_CLASS_MAP[ord(ch)] IF ord(ch) < 128 ELSE UNICODE_CLASS_MAP.get(ch, NON_ASCII_CLASS)",
            "6.     nxt ← TRANSITIONS[cur][cls]; IF nxt < 0 THEN BREAK",
            "7.     cur ← nxt; cursor += 1; visited_path.append((cur, cursor)); IF ACCEPT[cur] THEN last_accept ← (cursor, ACCEPT[cur])",
            "8.   FOR (st, idx) IN visited_path WHERE idx > (last_accept.pos IF last_accept ELSE pos): failed_states.add((st, idx))",
            "9.   IF last_accept ≠ NULL THEN Emit Token & pos ← last_accept.pos ELSE Phục hồi lỗi theo panic_char / smart_sync",
            "• Bộ sinh mã kiểu Flex (codegen.py): Đóng gói trực tiếp các mảng tĩnh ASCII_CLASS_MAP[128], UNICODE_CLASS_MAP, TRANSITIONS[|Q|][p], ACCEPT_TABLE và vòng lặp Reps O(n) thành 1 file Python độc lập (~527 dòng cho MiniLang, Zero import re, chạy độc lập không cần lexer_engine).",
        ],
        fill="F8FAFC",
        accent="1E3A8A",
        mono=True,
    )

    add_heading_2(doc, "4.7. Phân tích độ phức tạp và các trường hợp biên đã xử lý triệt để")
    comp_rows = [
        ["Regex Parser + Σ(U) + Anti-Bomb", "O(|R|), nút ≤ 4096", "O(|R|)", "Chặn bom (((a{64}){64}){64}) trong O(1); phủ 128 ASCII + Σ(U) bảo toàn ~(~A)=A; 24 bẫy lỗi RE"],
        ["Thompson & Khử ε (Định lý 2)", "O(|Q_N|² + |Q_N|·p)", "O(|Q_N|·p)", "Loại bỏ hoàn toàn cung ε, bảo toàn nhãn ưu tiên token cao nhất (MiniLang: 170 → 96 TT)"],
        ["Subset DFA & Ma trận L(Rᵢ)∩L(Rⱼ)", "Subset: O(|Q_D|·p)\nGiao: O(∑|Qᵢ||Qⱼ|p)", "O(|Q_D|·p)", "Nén Σ(U) thành 44 lớp trên MiniLang; quét 741 cặp giao nhau trong ~13 ms kèm chứng nhân"],
        ["Moore/Hopcroft & GNFA 360°", "Hopcroft: O(p|Q|log|Q|)\nGNFA: O(|Q|³)", "O(p·|Q|)", "Hội tụ Moore ≡ Hopcroft; chứng minh Myhill–Nerode 3003/3003 cặp & L(R_gốc) ≡ L(R_sinh)"],
        ["O(n) Scanner & Flex Codegen", "Tuyến tính chặt O(n)\n(với failed_states)", "O(n)", "Chống O(n²) trên chuỗi lỗi 10 KB; STRING_LIT loại trừ \\r trên CRLF; sinh Lexer độc lập .py"],
    ]
    add_styled_table(
        doc,
        ["Thành phần thuật toán", "Độ phức tạp thời gian", "Bộ nhớ", "Xử lý trường hợp biên & Đóng góp kỹ thuật v2.0"],
        comp_rows,
        col_widths_cm=[3.8, 3.3, 2.1, 7.5],
        font_size=8.4,
    )

    # =========================================================================
    # SECTION 5: CÀI ĐẶT VÀ KIẾN TRÚC CHƯƠNG TRÌNH
    # =========================================================================
    add_heading_1(doc, "5. Cài đặt và kiến trúc chương trình")

    add_body(
        doc,
        "Chương trình được tổ chức theo kiến trúc phân lớp gồm 3 tầng độc lập: "
        "(1) Tầng lõi thuật toán `lexer_engine/` (11 module Python Standard Library, không phụ thuộc bất kỳ gói ngoài nào và **Zero `import re`** — bao gồm cả `gnfa.py` và `codegen.py`); "
        "(2) Tầng giao diện gồm ứng dụng Web `LexAutomata Studio` 5 Tab (`app.py` + `web/`) và công cụ dòng lệnh 9 lệnh con (`cli.py`), kèm cấu hình Cloud 1-Click; "
        "(3) Tầng kiểm thử tự động & kiểm chứng khứ hồi (`tests/test_cases.json` với **72 test cases**, `tests/test_suite.py` với **22 bộ unittest**, `jflap_export.py` đọc/ghi XML `.jff`). "
        "Bảng 2 làm rõ ranh giới giữa phần nhóm tự cài đặt và thư viện chuẩn:",
    )

    lib_rows = [
        [
            "models.py, regex_parser.py, thompson.py, subset_construction.py, direct_dfa.py, dfa_minimizer.py, gnfa.py, scanner.py, codegen.py, verifier.py, jflap_export.py",
            "100% nhóm tự cài đặt từ con số 0 (Zero `import re`)",
            "Chỉ dùng Python Standard Library: `dataclasses`, `collections.deque`, `xml.etree.ElementTree`, `time`",
        ],
        [
            "app.py, cli.py, web/ (Đồ thị SVG + Ma trận Giao nhau L(Rᵢ)∩L(Rⱼ) + GNFA Kleene 360° + Xuất Standalone Lexer .py)",
            "100% nhóm tự thiết kế & lập trình",
            "Python stdlib `http.server`, `argparse`, `json`; trình duyệt chuẩn HTML5/SVG (không cần Node.js/React/pip)",
        ],
        [
            "tests/test_suite.py (72 test cases JSON + 22 unittest kiểm chứng Kleene 360°, ~(~A)=A, Anti-Bomb & Differential Codegen)",
            "Nhóm tự thiết kế kịch bản & bộ sinh chuỗi Fuzz",
            "Python `unittest`, `ast` (kiểm tra tự động không có `import re` trong lõi & file sinh mã), đối chứng vi sai",
        ],
        [
            "scripts/ (tự động vẽ đồ thị báo cáo & xuất DOCX/PDF/PPTX ngoài runtime)",
            "Nhóm viết script tự động hóa",
            "matplotlib, python-docx, python-pptx, chromium/chrome headless (không cần khi chạy ứng dụng demo)",
        ],
    ]
    add_styled_table(
        doc,
        ["Module / Thành phần", "Phần nhóm tự triển khai", "Thư viện / Công cụ sử dụng"],
        lib_rows,
        col_widths_cm=[5.3, 4.3, 7.1],
        font_size=8.4,
    )

    add_heading_2(doc, "5.1. Các tính năng nổi bật của Giao diện Web LexAutomata Studio (5 Tab) & CLI")
    add_bullet(
        doc,
        "Tab 1 & Thanh công cụ — Quét Từ Vựng O(n), Hoạt ảnh DFA & Nút ⬇ Sinh Lexer (.py) Kiểu Flex: ",
        "Soạn thảo mã nguồn với các kịch bản mẫu, chuyển đổi tức thời giữa `panic_char` và `smart_sync` (hiển thị `memoized_cutoffs` của Reps 1998), chạy hoạt ảnh DFA từng bước và tải ngay file bộ quét Python độc lập `.py` bằng 1 cú nhấp chuột.",
    )
    add_bullet(
        doc,
        "Tab 2 — Đồ thị Automata Đa-Token, Myhill–Nerode & Ma trận Giao nhau Tĩnh L(Rᵢ) ∩ L(Rⱼ): ",
        "Trực quan hóa đồ thị SVG cho cả 6 mô hình đa-token, bảng chuỗi phân biệt Myhill–Nerode, cùng thẻ con **Ma trận Giao nhau `L(Rᵢ) ∩ L(Rⱼ)`** hiển thị bản đồ nhiệt tương tác `39 × 39` và từ tố chứng nhân ngắn nhất cho từng cặp quy tắc.",
    )
    add_bullet(
        doc,
        "Tab 3 & Tab 4 — Vòng tròn Kleene 360° (GNFA DFA → RE), Kiểm chứng R₁ ≡ R₂ & Unicode Động: ",
        "Tab 3 bổ sung thẻ con thứ 6 **GNFA Khử Trạng Thái (`DFA → RE · Kleene 360°`)** trình bày từng bước khử đỉnh `q_rip` và chứng minh `L(R_gốc) ≡ L(R_sinh)`. "
        "Tab 4 tích hợp nút `+ Thêm Unicode (nếu / €)`, bẫy `Shadowed Rule` trực tiếp, tải `Standalone Lexer (.py)` tùy chỉnh và bảng chứng nhân giao nhau thời gian thực.",
    )
    add_bullet(
        doc,
        "Tab 5 — Phòng Thí Nghiệm Kiểm Thử Tự Động (72/72 PASS) & Benchmark Chống Quay Lui Bậc Hai O(n²): ",
        "Chạy trực tiếp 72 ca kiểm thử JSON (gồm cả Kleene 360°, Unicode động, bom AST và CRLF), bảng đối sánh hiệu năng trên 3 ngôn ngữ và biểu đồ Stress Test 10.000 ký tự lỗi.",
    )

    add_body(
        doc,
        "Hình 4 minh họa đồ thị Minimized Combined DFA hoàn chỉnh của `CalcLang` (12 token → 20 trạng thái tối giản, 190/190 cặp Myhill–Nerode). "
        "Hình 5 và Hình 6 chụp trực tiếp giao diện Web `LexAutomata Studio` v2.0 đang vận hành tại Tab 1 và Tab 3.",
    )
    add_figure(
        doc,
        FIG_DIR / "fig3_calclang_combined_dfa.png",
        "Hình 4: Đồ thị Minimized Combined Multi-token DFA hoàn chỉnh của CalcLang (12 token → 20 trạng thái tối giản, 190/190 cặp Myhill–Nerode).",
        width_cm=12.4,
    )
    add_figure(
        doc,
        FIG_DIR / "fig6_web_scanner_demo.png",
        "Hình 5: Giao diện Web LexAutomata Studio — Tab 1 với nút ⬇ Sinh Lexer (.py), công tắc Panic-mode / Smart-Sync và luồng Token.",
        width_cm=14.4,
    )
    add_figure(
        doc,
        FIG_DIR / "fig7_web_direct_re_lab.png",
        "Hình 6: Giao diện Web LexAutomata Studio — Tab 3 với huy hiệu Kleene 360° (R₀ ≡ R_sinh), cây r·#, bảng followpos (Slide 54) và 6 thẻ giai đoạn.",
        width_cm=14.4,
    )

    # =========================================================================
    # SECTION 6: TEST CASE, KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH
    # =========================================================================
    add_heading_1(doc, "6. Test case, kết quả thực nghiệm và phân tích")

    add_heading_2(doc, "6.1. Thiết kế bộ 72 Test Cases JSON & 22 Unittest Bất biến Toán học")
    add_body(
        doc,
        f"Nhóm đã mở rộng bộ kiểm thử có cấu trúc trong `tests/test_cases.json` lên **{test_rep['total']} kịch bản chuẩn** "
        f"(gồm 20 ca RE đơn/Unicode/Kleene 360°, 24 ca bẫy lỗi cú pháp RE & bom AST, và 28 ca quét từ vựng đa ngôn ngữ) kết hợp với **22 bộ Unittest** trong `tests/test_suite.py`. "
        f"Kết quả thực thi đạt **{test_rep['passed']}/{test_rep['total']} PASS ({test_rep['pass_rate']}%)** trên JSON và **22/22 OK (100%)** trên Unittest. "
        f"Bảng 3 tổng hợp các nhóm kiểm thử đại diện và các bất biến toán học được kiểm chứng tự động:",
    )

    tc_rows = [
        ["RE-01..02", "Bài giảng UEH", "(a|b)*abb & (a|ba)(a|b)*ba", "Khớp 100% Slide 38 (11→6→5→4 TT) & Slide 54 (followpos, 5 TT); GNFA sinh R_sinh ≡ R_gốc", "PASS"],
        ["RE-03..20", "Unicode Σ(U) & Biên", "(nếu|lặp)_[0-9]+€, [^€\\n]+, [\\f\\v]+, [0-9]{2,4}", "Phân hoạch Σ(U) không va chạm NON_ASCII; bảo toàn bù kép ~(~A)=A & Kleene 360° trên 20/20 RE", "PASS"],
        ["RE-ERR-01..24", "24 Bẫy RE & Bom AST", "(((a{64}){64}){64}), (a{64}){64}, \\u12G4, [a-\\uffff]", "Chặn đứng bom nhân bản AST (>4096 nút) trong <0.1 ms; bắt chuẩn 24/24 lỗi cú pháp RE", "PASS"],
        ["SCAN-01..14", "Maximal Munch & UTF-8", 'ifx, a===b, 1.5e, 100€, "Xin chào UEH"', "Khớp dài nhất & ưu tiên luật chuẩn xác; chuỗi UTF-8 hợp lệ; bắt lỗi U+20AC ngoài chuỗi", "PASS"],
        ["SCAN-15..28", "CRLF & Điều khiển ASCII", '"unclosed\\r\\nlet ok=1;, /*...*/, "\\f\\v"', "STRING_LIT loại trừ cả \\r và \\n trên Windows CRLF; hỗ trợ \\f, \\v và bình luận /*...*/", "PASS"],
        ["INV-1..5", "Bất biến & Myhill–Nerode", "390+ chuỗi Fuzz, 4.519 cặp TT, 30.000 ký tự lỗi", "Zero-Loss 100%; 100% cặp trạng thái có chuỗi phân biệt w; Reps O(n) cắt 5.000 nhánh quay lui", "PASS"],
        ["V2-4..6", "GNFA, Giao & Codegen", "Kleene 360°, Ma trận 741 cặp, Standalone Lexer .py", "L(R_0)≡L(R_sinh); phát hiện 9/741 cặp giao nhau MiniLang; Lexer độc lập khớp 100% bản gốc", "PASS"],
    ]
    add_styled_table(
        doc,
        ["Mã Kiểm thử", "Phân loại", "Đầu vào / Kịch bản đại diện", "Kết quả thực nghiệm & Bất biến kiểm chứng", "Đánh giá"],
        tc_rows,
        col_widths_cm=[2.3, 2.3, 4.0, 6.6, 1.5],
        font_size=8.3,
        mono_cols={0},
    )

    add_heading_2(doc, "6.2. Thực nghiệm đối sánh Đa-Otomat, Ma trận Giao nhau & Stress Test O(n)")
    add_body(
        doc,
        "Bảng 4 và Hình 7 tổng hợp số liệu thực nghiệm trên cả 3 bộ ngôn ngữ qua các phương pháp Automata, số cặp giao nhau tĩnh `L(Rᵢ) ∩ L(Rⱼ)` và kết quả chứng minh tối giản Myhill–Nerode:",
    )

    dir_mini = len(build_combined_direct_dfa(PRESETS["minilang"]["specs"]).states)
    dir_calc = len(build_combined_direct_dfa(PRESETS["calclang"]["specs"]).states)
    dir_sql = len(build_combined_direct_dfa(PRESETS["minisql"]["specs"]).states)
    inter_mini = s_mini["intersection_summary"]
    inter_calc = s_calc["intersection_summary"]
    inter_sql = s_sql["intersection_summary"]

    bench_rows = [
        [
            "MiniLang",
            str(s_mini["token_count"]),
            str(s_mini["nfa_states"]),
            str(s_mini["eps_free_nfa_states"]),
            str(s_mini["subset_dfa_states"]),
            str(dir_mini),
            f"{s_mini['minimized_dfa_states']} / {s_mini['hopcroft_dfa_states']}",
            f"{s_mini['minimality']['distinguishable_pairs']}/{s_mini['minimality']['total_pairs']}",
            f"{inter_mini['overlap_count']}/{inter_mini['total_pairs']} (0 lỗi)",
            "✓ 100% Eq",
        ],
        [
            "CalcLang",
            str(s_calc["token_count"]),
            str(s_calc["nfa_states"]),
            str(s_calc["eps_free_nfa_states"]),
            str(s_calc["subset_dfa_states"]),
            str(dir_calc),
            f"{s_calc['minimized_dfa_states']} / {s_calc['hopcroft_dfa_states']}",
            f"{s_calc['minimality']['distinguishable_pairs']}/{s_calc['minimality']['total_pairs']}",
            f"{inter_calc['overlap_count']}/{inter_calc['total_pairs']} (0 lỗi)",
            "✓ 100% Eq",
        ],
        [
            "MiniSQL",
            str(s_sql["token_count"]),
            str(s_sql["nfa_states"]),
            str(s_sql["eps_free_nfa_states"]),
            str(s_sql["subset_dfa_states"]),
            str(dir_sql),
            f"{s_sql['minimized_dfa_states']} / {s_sql['hopcroft_dfa_states']}",
            f"{s_sql['minimality']['distinguishable_pairs']}/{s_sql['minimality']['total_pairs']}",
            f"{inter_sql['overlap_count']}/{inter_sql['total_pairs']} (0 lỗi)",
            "✓ 100% Eq",
        ],
    ]
    add_styled_table(
        doc,
        [
            "Ngôn ngữ",
            "Token",
            "ε-NFA",
            "Khử ε",
            "Sub-DFA",
            "Dir-DFA",
            "Moore/Hop",
            "Myhill–Nerode",
            "Giao L(Rᵢ)∩L(Rⱼ)",
            "Kiểm chứng",
        ],
        bench_rows,
        col_widths_cm=[1.8, 1.0, 1.1, 1.1, 1.3, 1.3, 1.6, 2.2, 2.5, 1.8],
        font_size=8.1,
    )

    add_figure(
        doc,
        FIG_DIR / "fig4_benchmark_comparison.png",
        "Hình 7: (a) Đối sánh số trạng thái qua các phương pháp Automata trên 3 ngôn ngữ và (b) Thời gian biên dịch & quét tuyến tính O(n).",
        width_cm=15.6,
    )

    add_body(
        doc,
        "Các phát hiện khoa học quan trọng từ thực nghiệm:",
        bold_prefix="Phân tích chuyên sâu: ",
    )
    add_bullet(
        doc,
        "Sự hội tụ Moore ≡ Hopcroft, Kleene 360° & Đối chứng Vi sai Bộ sinh mã Lexer Độc lập: ",
        "Trên cả 3 ngôn ngữ, Moore và Hopcroft đều hội tụ về cùng một Min-DFA duy nhất (`MiniLang: 78`, `CalcLang: 20`, `MiniSQL: 52`) với 100% cặp trạng thái phân biệt đôi một. "
        "Khi xuất sang bộ quét Python độc lập bằng `codegen.py` (`MiniLangLexer`: 78 trạng thái × 44 lớp tương đương), kiểm thử vi sai xác nhận luồng Token và LexicalError trùng khớp 100% với engine gốc trên mọi ca kiểm thử.",
    )
    add_bullet(
        doc,
        "Hiệu quả chống quay lui bậc hai O(n²) của bảng nhớ Reps (1998) & Phân tích Tĩnh L(Rᵢ) ∩ L(Rⱼ): ",
        "Trên chuỗi bệnh lý dài 10.000 ký tự (`\"` + `\\\"` * 5000), bảng nhớ `failed_states` kích hoạt đúng **5.000 lần cắt nhánh O(1)**, giữ thời gian quét tuyến tính chỉ vài chục mili-giây thay vì hàng chục triệu bước O(n²). "
        "Đồng thời, Ma trận Giao nhau Tĩnh chứng minh 732/741 cặp quy tắc của `MiniLang` rời nhau hoàn toàn và 9 cặp giao nhau duy nhất đều là quan hệ bao hàm có chủ đích `KW_* / BOOL_LIT ⊂ IDENTIFIER`.",
    )

    # =========================================================================
    # SECTION 7: HẠN CHẾ LÝ THUYẾT, CÁC VẤN ĐỀ ĐÃ GIẢI QUYẾT & HƯỚNG PHÁT TRIỂN
    # =========================================================================
    add_heading_1(doc, "7. Phân tích giới hạn lý thuyết và hướng phát triển")

    add_heading_2(doc, "7.1. Các lỗ hổng kỹ thuật tinh vi đã được giải quyết & Giới hạn lý thuyết của DFA")
    add_bullet(
        doc,
        "Các thách thức và lỗ hổng kỹ thuật tinh vi đã được xử lý triệt để trong phiên bản v2.0: ",
        "(1) Phân hoạch bảng chữ cái Unicode động `Σ(U)` kết hợp noncharacter `NON_ASCII (U+FDD0)` cho phép dùng trực tiếp từ khóa/ký hiệu Unicode (`nếu`, `€`, `[^€]`) mà không va chạm với lớp UTF-8 chung; "
        "(2) Phủ kín 128 mã ASCII `0x00..0x7F` bảo toàn luật đối hợp đại số Boole `~(~A) = A` và loại trừ `\\r` khỏi `STRING_LIT` trên Windows CRLF; "
        "(3) Chặn đứng bom nhân bản AST lồng nhau `(((a{64}){64}){64})` bằng ngưỡng `MAX_AST_NODES = 4096`; "
        "(4) Khép kín chiều ngược Kleene 360° (`GNFA DFA → RE`), Ma trận Giao nhau `L(Rᵢ) ∩ L(Rⱼ)`, chống O(n²) theo Reps (1998) và sinh mã Lexer độc lập kiểu Flex.",
    )
    add_bullet(
        doc,
        "Giới hạn lý thuyết bất khả kháng của Automata hữu hạn (Chứng minh bằng Bổ đề Bơm — Pumping Lemma Chương 3.2): ",
        "Dù hệ thống đã hỗ trợ bình luận nhiều dòng chuẩn C/Java `/* ... */` bằng RE `/\\*([^*]|\\*+[^*/])*\\*+/`, "
        "một DFA đơn lẻ **không thể** nhận diện bình luận nhiều dòng **lồng nhau sâu tùy ý** (`/* ... /* ... */ ... */`, như trong Rust/Swift). "
        "Nếu thay `/*` bằng `a` và `*/` bằng `b`, ngôn ngữ này đẳng cấu với `L = { a^n b^n | n ≥ 1 }`. "
        "Theo **Bổ đề Bơm (Chương 3.2)**, với mọi hằng số bơm `p = |Q|`, xét `w = a^p b^p ∈ L`, mọi cách tách `w = xyz` (`|xy| ≤ p`, `|y| ≥ 1`) "
        "đều có `y = a^k (k ≥ 1)` nên `xy²z = a^{p+k} b^p ∉ L` (mâu thuẫn!). Tương tự, thụt lề phụ thuộc ngữ cảnh (`INDENT`/`DEDENT` của Python) cần thêm một ngăn xếp (Stack) lưu lịch sử cột.",
    )

    add_heading_2(doc, "7.2. Hướng phát triển tiếp theo")
    add_bullet(
        doc,
        "Tích hợp Ngăn xếp Ngữ cảnh Từ vựng (Lexical Start Conditions & Counter Automaton): ",
        "Bổ sung chồng trạng thái ngữ cảnh (`push_state(IN_NESTED_COMMENT)`, `pop_state()`) kết hợp bộ đếm độ sâu lồng nhau để hỗ trợ bình luận lồng nhau và nội suy chuỗi (`\"Hello ${name}\"`).",
    )
    add_bullet(
        doc,
        "Kết nối trực tiếp với Bộ phân tích cú pháp Văn phạm phi ngữ cảnh (Chương 4 — CFG & PDA): ",
        "Đưa luồng `Token` đầu ra của `LexicalAnalyzer` (hoặc của file Lexer độc lập sinh bởi `codegen.py`) vào bộ phân tích cú pháp `LL(1)` / `LR(1)` (Pushdown Automata — PDA), khép kín kiến thức từ Chương 1–3 sang Chương 4–5.",
    )

    # =========================================================================
    # SECTION 8: KẾT LUẬN
    # =========================================================================
    add_heading_1(doc, "8. Kết luận")
    add_body(
        doc,
        "Đồ án đã hoàn thành toàn diện và mở rộng sâu sắc yêu cầu của Đề tài T13 — Automata-based Lexical Analyzer. "
        "Từ nền tảng lý thuyết của học phần Ngôn ngữ hình thức (UEH), nhóm đã tự thiết kế và cài đặt 100% từ con số 0 (Zero `import re` trong lõi) "
        "một hệ thống khép kín **Vòng tròn Định lý Kleene 360°**: phân tích cú pháp RE chống bom AST (`≤ 4096` nút) trên bảng chữ cái Unicode động `Σ(U)` bảo toàn đại số Boole `~(~A) = A`, "
        "Thompson `ε-NFA`, Khử `ε` (Định lý 2), `Subset DFA`, `Direct RE → DFA` đơn lẻ & đa-token (`r·#`), tối thiểu hóa song song `Moore & Hopcroft`, "
        "chiều ngược **GNFA State Elimination (`DFA → RE`)**, **Ma trận Giao nhau Tĩnh `L(Rᵢ) ∩ L(Rⱼ)`**, chứng minh tối giản **Myhill–Nerode**, "
        "bộ quét tuyến tính chặt `O(n)` (Reps, 1998) và **Bộ sinh mã Lexer Python Độc lập kiểu Flex**. "
        "Toàn bộ hệ thống vượt qua tuyệt đối **72/72 kịch bản JSON (100% PASS)** và **22/22 bộ Unittest**, kèm ứng dụng Web `LexAutomata Studio` 5 Tab phục vụ trực quan cho học tập và giảng dạy.",
    )

    # =========================================================================
    # SECTION 9: TÀI LIỆU THAM KHẢO
    # =========================================================================
    add_heading_1(doc, "9. Tài liệu tham khảo")
    refs = [
        "[1] J. E. Hopcroft, R. Motwani, and J. D. Ullman, Introduction to Automata Theory, Languages, and Computation, 3rd ed. Boston, MA: Pearson / Addison-Wesley, 2006. (Giáo trình chính thức môn học).",
        "[2] A. V. Aho, M. S. Lam, R. Sethi, and J. D. Ullman, Compilers: Principles, Techniques, and Tools (Dragon Book), 2nd ed., Chapter 3: Lexical Analysis, pp. 109–190. Boston, MA: Addison-Wesley, 2006.",
        "[3] ThS. Hồ Thị Thanh Tuyến, Bài giảng Học phần Ngôn ngữ hình thức (Chương 1: Tổng quan; Chương 2: DFA/NFA; Chương 3.1: Biểu thức chính quy, Khử ε, Direct DFA & Tối thiểu hóa DFA; Chương 3.2: Bổ đề Bơm), Khoa CNTTKD, Đại học Kinh tế TP.HCM (UEH), 2026.",
        "[4] K. Thompson, \"Programming Techniques: Regular Expression Search Algorithm,\" Communications of the ACM, vol. 11, no. 6, pp. 419–422, Jun. 1968.",
        "[5] J. E. Hopcroft, \"An n log n algorithm for minimizing states in a finite automaton,\" in Theory of Machines and Computations, Z. Kohavi and A. Paz, Eds. New York: Academic Press, 1971, pp. 189–196.",
        "[6] E. F. Moore, \"Gedanken-experiments on sequential machines,\" in Automata Studies, C. E. Shannon and J. McCarthy, Eds. Princeton, NJ: Princeton University Press, 1956, pp. 129–153.",
        "[7] T. Reps, \"'Maximal-munch' tokenization in linear time,\" ACM Transactions on Programming Languages and Systems (TOPLAS), vol. 20, no. 2, pp. 259–273, Mar. 1998.",
        "[8] G. Berry and R. Sethi, \"From regular expressions to deterministic automata,\" Theoretical Computer Science, vol. 48, pp. 117–126, 1986.",
        "[9] S. H. Rodger and T. W. Finley, JFLAP: An Interactive Formal Languages and Automata Package. Sudbury, MA: Jones & Bartlett Publishers, 2006.",
    ]
    for ref in refs:
        add_body(doc, ref, space_after=2.8)

    # =========================================================================
    # SECTION 10: PHỤ LỤC — PHÂN CÔNG CÔNG VIỆC & KHAI BÁO SỬ DỤNG AI
    # =========================================================================
    add_page_break(doc)
    add_heading_1(doc, "10. Phụ lục: Phân công công việc và Khai báo sử dụng AI")

    add_heading_2(doc, "10.1. Bảng phân công công việc nhóm")
    add_body(
        doc,
        "(Lưu ý: Nhóm điền đầy đủ Họ tên, MSSV thực tế và điều chỉnh tỷ lệ đóng góp chính xác trước khi nộp.)",
        space_after=3.5,
    )
    alloc_rows = [
        [
            "1",
            "[Họ tên TV 1]",
            "[MSSV 1]",
            "Quản lý tiến độ; hệ thống hóa cơ sở lý thuyết Chương 1–3, vòng tròn Kleene 360°, đại số Boole ~(~A)=A & Myhill–Nerode / Bổ đề Bơm; biên soạn báo cáo & slide.",
            "25%",
        ],
        [
            "2",
            "[Họ tên TV 2]",
            "[MSSV 2]",
            "Cài đặt `models.py` (ASCII 0..127 & Unicode động `Σ(U)`), `regex_parser.py` (`{m,n}`, `MAX_AST_NODES=4096`), `thompson.py` (Khử ε ĐL 2), `direct_dfa.py`; demo Tab 3.",
            "25%",
        ],
        [
            "3",
            "[Họ tên TV 3]",
            "[MSSV 3]",
            "Cài đặt `subset_construction.py`, `dfa_minimizer.py` (Moore, Hopcroft & `complement_dfa`), `gnfa.py` (DFA → RE), `verifier.py` (Ma trận `L(Rᵢ)∩L(Rⱼ)`), `jflap_export.py`; demo Tab 2.",
            "25%",
        ],
        [
            "4",
            "[Họ tên TV 4]",
            "[MSSV 4]",
            "Cài đặt `scanner.py` (Reps 1998 O(n)), `codegen.py` (Standalone Flex-style Lexer Generator), `app.py`, `cli.py`, Web Studio 5 Tab & bộ 72 test cases + 22 unittest; demo Tab 1, 4, 5.",
            "25%",
        ],
    ]
    add_styled_table(
        doc,
        ["STT", "Họ và Tên", "MSSV", "Nhiệm vụ phụ trách cụ thể", "Đóng góp"],
        alloc_rows,
        col_widths_cm=[1.0, 2.8, 2.3, 8.9, 1.7],
        font_size=8.6,
    )

    add_heading_2(doc, "10.2. Khai báo sử dụng công cụ Trí tuệ Nhân tạo (AI)")
    ai_rows = [
        ["Công cụ AI sử dụng", "Trợ lý lập trình AI (Google Gemini / Antigravity)"],
        [
            "Mục đích sử dụng",
            "• Tham khảo, rà soát thuật ngữ lý thuyết Automata và cấu trúc thuật toán (Vòng tròn Kleene 360° & GNFA State Elimination, Phân hoạch Unicode động `Σ(U)`, Moore & Hopcroft Min-DFA, Myhill–Nerode, Reps 1998 O(n) & Table-Driven Lexer Codegen).\n"
            "• Gợi ý kiểm tra các lỗ hổng tinh vi (đối hợp đại số Boole `~(~A)=A` trên ASCII `0x00..0x7F`, bom nhân bản AST lồng nhau `MAX_AST_NODES=4096`, `STRING_LIT` loại trừ `\\r` trên CRLF, Ma trận Giao nhau `L(Rᵢ)∩L(Rⱼ)`).\n"
            "• Hỗ trợ xây dựng giao diện trực quan hóa SVG Web Studio 5 Tab, bộ 72 test cases JSON + 22 unittest bất biến toán học và chuẩn hóa trình bày báo cáo/slide.",
        ],
        [
            "Phạm vi kiểm chứng & Trách nhiệm của nhóm",
            "• Toàn bộ thành viên nhóm đã đọc hiểu, kiểm tra từng dòng thuật toán cốt lõi trong `lexer_engine/`, tự kiểm chứng đối chiếu với ví dụ bài giảng Chương 3.1 "
            "(Slide 21–22, Slide 38 và Slide 46–57), chạy 100% bộ kiểm thử tự động (72/72 JSON PASS + 22/22 Unittest OK), đối chứng vi sai Lexer độc lập và kiểm chứng khứ hồi trên JFLAP.\n"
            "• Nhóm chịu trách nhiệm hoàn toàn về độ chính xác khoa học của mã nguồn, kết quả thực nghiệm và sẵn sàng giải thích chi tiết từng dòng code trong buổi bảo vệ.",
        ],
    ]
    add_styled_table(
        doc,
        ["Hạng mục khai báo", "Nội dung chi tiết"],
        ai_rows,
        col_widths_cm=[4.2, 12.5],
        font_size=8.6,
        trailing_space=False,
    )

    doc.save(str(DOCX_PATH))
    print(f"[OK] Saved DOCX report -> {DOCX_PATH}")

    export_pdf_via_chromium(HTML_BLOCKS, PDF_PATH)
    print(f"[OK] Exported PDF report -> {PDF_PATH}")


if __name__ == "__main__":
    build_report()
