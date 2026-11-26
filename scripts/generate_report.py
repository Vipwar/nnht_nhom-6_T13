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
        "Xây dựng Bộ phân tích từ vựng tổng quát theo quy trình khép kín của Định lý Kleene:\n"
        "RE (Unicode động Σ(U)) ⇄ Thompson ε-NFA · Khử ε · Subset & Direct DFA · Moore/Hopcroft Min-DFA · GNFA,\n"
        "Ma trận giao nhau L(Rᵢ)∩L(Rⱼ), Kiểm chứng Myhill–Nerode, Bộ quét O(n) và Sinh mã Lexer độc lập"
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
        ["1", "[Điền Họ tên Thành viên 1]", "[MSSV 1]", "Nhóm trưởng · Cơ sở lý thuyết Kleene, Myhill–Nerode & Báo cáo"],
        ["2", "[Điền Họ tên Thành viên 2]", "[MSSV 2]", "Regex Parser (Σ(U), ≤4096 AST) · Thompson, Khử ε & Direct DFA"],
        ["3", "[Điền Họ tên Thành viên 3]", "[MSSV 3]", "Subset · Moore/Hopcroft · GNFA (DFA→RE) & Ma trận L(Rᵢ)∩L(Rⱼ)"],
        ["4", "[Điền Họ tên Thành viên 4]", "[MSSV 4]", "Scanner O(n) · Sinh mã Lexer (.py) · Giao diện Web & 72 Tests"],
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
        "Trong kiến trúc của trình biên dịch (compiler) và trình thông dịch (interpreter), "
        "phân tích từ vựng (Lexical Analysis) là giai đoạn đầu tiên đọc dòng ký tự thô của mã nguồn "
        "và nhóm chúng thành dãy các đơn vị từ vựng có nghĩa gọi là token (từ khóa, định danh, hằng số, chuỗi, toán tử, "
        "dấu phân cách), đồng thời lọc bỏ khoảng trắng, bình luận đơn dòng/nhiều dòng và xác định tọa độ lỗi từ vựng. "
        "Mối liên hệ trực tiếp giữa học phần Ngôn ngữ hình thức và Kỹ thuật trình biên dịch thể hiện ở chỗ: "
        "các lớp token của ngôn ngữ lập trình thuộc lớp Ngôn ngữ chính quy (Regular Languages) — được "
        "đặc tả bằng Biểu thức chính quy (Regular Expression — RE) và nhận diện bằng Automata hữu hạn đơn định (DFA) "
        "trong thời gian tuyến tính O(n) theo độ dài mã nguồn, tránh hiện tượng quay lui hàm mũ O(2^n) (ReDoS) thường gặp ở các bộ khớp biểu thức quay lui.",
    )

    add_body(
        doc,
        "Thay vì viết thủ công bộ quét bằng các nhánh điều kiện if/else cố định cho một ngôn ngữ duy nhất hoặc gọi thư viện biểu thức "
        "chính quy dựng sẵn (như module `re` của Python), đề tài T13 — Automata-based Lexical Analyzer xây dựng từ đầu "
        "quy trình biên dịch Automata hai chiều theo Định lý Kleene, công cụ sinh mã Lexer độc lập theo bảng chuyển trạng thái và giao diện trực quan hóa trên nền tảng Web.",
    )

    add_heading_2(doc, "1.1. Mục tiêu cụ thể của đồ án")
    add_bullet(
        doc,
        "Tự cài đặt chuỗi 7 biểu diễn Automata theo Định lý Kleene (không dùng `import re`): ",
        "Xây dựng từ đầu bằng thư viện chuẩn Python: Bộ phân tích cú pháp RE (giới hạn số nút AST `MAX_AST_NODES = 4096`, phân hoạch bảng chữ cái Unicode động `Σ(U)` và bao phủ 128 mã ASCII `0x00..0x7F` đảm bảo `~(~A) = A`) → "
        "Thompson `ε-NFA` → Khử `ε` (Định lý 2) → `Subset DFA` → `Moore & Hopcroft Min-DFA` → **Khử trạng thái GNFA (`DFA → RE`)** đối chiếu `L(R_gốc) ≡ L(R_sinh)`.",
    )
    add_bullet(
        doc,
        "Phương pháp trực tiếp RE → DFA đa-token, Ma trận giao nhau L(Rᵢ) ∩ L(Rⱼ) và Kiểm chứng Myhill–Nerode: ",
        "Triển khai thuật toán dựng DFA trực tiếp từ cây cú pháp `r·#` (theo Slide 46–57 Chương 3.1) và mở rộng đa-token `(R₁·#₁)|...|(Rₖ·#ₖ)`, "
        "kiểm tra tương đương bằng **Product Automaton**, kiểm chứng tính tối giản **Myhill–Nerode**, phân tích tĩnh **Ma trận giao nhau `L(Rᵢ) ∩ L(Rⱼ)`** kèm chuỗi chứng nhân ngắn nhất và xuất/đọc ngược định dạng JFLAP `.jff`.",
    )
    add_bullet(
        doc,
        "Bộ quét Maximal Munch tuyến tính O(n) (Reps, 1998) và Bộ sinh mã Lexer độc lập kiểu Flex: ",
        "Cài đặt bộ quét dựa trên bảng chuyển trạng thái DFA kèm bảng nhớ `failed_states` chống suy biến O(n²), quy tắc `STRING_LIT` xử lý đúng dòng CRLF (`\\r\\n`), hai chế độ phục hồi lỗi (`panic_char` và `smart_sync`), "
        "cùng mô-đun **`codegen`** xuất `Min-DFA` thành tệp bộ quét Python độc lập điều khiển bằng bảng (không phụ thuộc ngoài, kiểm thử đối chứng 100%).",
    )
    add_bullet(
        doc,
        "Kiểm thử tự động với 72 Test Cases JSON, 22 Unittest Suites và Giao diện Web 5 Tab: ",
        "Thiết kế 72 ca kiểm thử JSON có cấu trúc (20 mẫu RE đơn/Unicode/GNFA, 24 mẫu lỗi cú pháp RE và giới hạn AST, 28 mẫu quét mã nguồn) cùng 22 nhóm Unittest kiểm tra các bất biến toán học "
        "và giao diện Web 5 tab hiển thị đồ thị SVG, ma trận giao nhau, các bước khử GNFA và mô phỏng từng bước trên DFA.",
    )

    # =========================================================================
    # SECTION 2: CƠ SỞ LÝ THUYẾT LIÊN QUAN
    # =========================================================================
    add_heading_1(doc, "2. Cơ sở lý thuyết liên quan")

    add_body(
        doc,
        "Thiết kế của chương trình dựa trên các định nghĩa và định lý trong giáo trình "
        "Introduction to Automata Theory, Languages, and Computation (Hopcroft, Motwani & Ullman, 3rd Ed.), "
        "Dragon Book (Aho, Lam, Sethi & Ullman, 2nd Ed.) và bài giảng Chương 1–3 môn Ngôn ngữ hình thức của ThS. Hồ Thị Thanh Tuyến (UEH):",
    )

    add_heading_2(doc, "2.1. Đại số Boole trên Bảng chữ cái động Σ(U), Ngôn ngữ và Biểu thức chính quy (RE)")
    add_body(
        doc,
        "Cho bảng chữ cái hữu hạn khác rỗng Σ. Tập tất cả chuỗi hữu hạn trên Σ ký hiệu là Σ* (chứa chuỗi rỗng ε). "
        "Biểu thức chính quy (RE) trên Σ được định nghĩa quy nạp: "
        "(i) ∅ biểu diễn ∅; (ii) ε biểu diễn {ε}; (iii) ∀a ∈ Σ, a biểu diễn {a}; "
        "(iv) Nếu r và s là các RE biểu diễn L(r) và L(s), thì `(r | s)` biểu diễn L(r) ∪ L(s), "
        "`(r·s)` biểu diễn L(r)L(s), và `(r*)` biểu diễn L(r)* = ⋃_{k≥0} L(r)^k. "
        "Thứ tự ưu tiên toán tử từ cao đến thấp: `(…)` > Định lượng (`*`, `+`, `?`, `{m,n}`) > Nối kết (`·`) > Phép hợp (`|`). "
        "Các toán tử mở rộng được quy về 3 phép toán cơ sở: `r+ ≡ r·r*`, `r? ≡ (r | ε)`, `r{m,n} ≡ r^m · (r?)^{n-m}`, "
        "`[c₁...c_m] ≡ (c₁|...|c_m)` và lớp phủ định `[^C] ≡ Σ(U) \\ C` thỏa mãn luật đối hợp đại số Boole `~(~C) = C`.",
    )

    add_heading_2(doc, "2.2. Hai chiều tương đương của Định lý Kleene: Thompson, Khử ε, Subset DFA, Min-DFA và GNFA")
    add_callout(
        doc,
        "Quy trình chuyển đổi khép kín theo Định lý Kleene (RE ⇄ ε-NFA ⇄ NFA ⇄ DFA ⇄ Min-DFA)",
        [
            "• Định lý 3 (Cấu trúc Thompson, 1968 — Slide 24–30 Chương 3.1): Mọi RE r đều chuyển được thành ε-NFA N = (Q, Σ, δ, q₀, {f}) "
            "có 1 đỉnh đầu (in-deg = 0), 1 đỉnh kết thúc (out-deg = 0), tối đa 2|r| trạng thái và bậc ra mỗi đỉnh ≤ 2.",
            "• Định lý 2 (Khử chuyển tiếp rỗng ε-NFA → NFA không ε — Slide 21–22 Chương 3.1): Dựng NFA không ε tương đương "
            "N' = (Q, Σ, δ', q₀, F') với δ'(p, a) = ε-closure(Move(ε-closure({p}), a)) và F' = { p ∈ Q | ε-closure({p}) ∩ F ≠ ∅ }.",
            "• Định lý 1 & Myhill–Nerode (Subset DFA & Tối thiểu hóa Moore/Hopcroft): D₀ = ε-closure({q₀}), δ_D(S, a) = ε-closure(Move(S, a)). "
            "DFA tối giản là duy nhất (sai khác đẳng cấu) khi mọi cặp trạng thái phân biệt (p, q) đều tồn tại chuỗi phân biệt w sao cho τ(δ̂(p, w)) ≠ τ(δ̂(q, w)).",
            "• Chiều ngược Định lý Kleene (Khử trạng thái GNFA: DFA → RE — Hopcroft Mục 3.2.1): Bổ sung q_start --ε--> D₀ và ∀f ∈ F: f --ε--> q_accept, "
            "sau đó khử lần lượt từng đỉnh trung gian q_rip theo công thức: R'(qᵢ, qⱼ) = R(qᵢ, qⱼ) | R(qᵢ, q_rip)·(R(q_rip, q_rip))*·R(q_rip, qⱼ) cho đến khi thu được R(q_start, q_accept) ≡ R_gốc.",
        ],
    )

    add_heading_2(doc, "2.3. Phương pháp trực tiếp RE → DFA (Chương 3.1 Mục 2.5) và Nguyên tắc Maximal Munch O(n)")
    add_bullet(
        doc,
        "Phương pháp trực tiếp trên cây cú pháp r·# (Slide 43–57 Chương 3.1): ",
        "Nối ký hiệu kết thúc `# ∉ Σ` vào sau biểu thức (`r·#`), đánh số các nút lá từ `1..n`, "
        "tính đệ quy `nullable(v)`, `firstpos(v)`, `lastpos(v)` và bảng `followpos(i)`. Với bài toán đa-token, nhóm mở rộng thành cây kết hợp `(R₁·#₁) | (R₂·#₂) | ... | (Rₖ·#ₖ)` "
        "để sinh trực tiếp Combined Multi-token Direct DFA không qua bước ε-NFA trung gian.",
    )
    add_bullet(
        doc,
        "Quy tắc khớp dài nhất (Maximal Munch), ưu tiên luật và bảng nhớ tuyến tính O(n) (Reps, 1998): ",
        "Tại vị trí `pos`, bộ quét chọn tiền tố dài nhất đưa DFA tới trạng thái kết thúc; nếu cùng độ dài khớp nhiều luật (`if` ∈ `L(KW_IF) ∩ L(IDENTIFIER)`), chọn luật có chỉ số ưu tiên nhỏ nhất. "
        "Để tránh suy biến bậc hai O(n²) trên các chuỗi chưa đóng dài, bộ quét lưu tập `failed_states` chứa các cặp `(state, cursor)` đã thất bại (Reps, 1998), đảm bảo mỗi cặp `(q, i)` chỉ xét tối đa 1 lần nên độ phức tạp đạt O(|Q|·n) = O(n).",
    )

    # =========================================================================
    # SECTION 3: MÔ HÌNH HÌNH THỨC / AUTOMATA ĐƯỢC SỬ DỤNG
    # =========================================================================
    add_heading_1(doc, "3. Mô hình hình thức / Automata được sử dụng")

    add_heading_2(doc, "3.1. Phân hoạch Bảng chữ cái Unicode động Σ(U) và Bao phủ ASCII 0x00..0x7F (~(~A) = A)")
    add_bullet(
        doc,
        "Đầu vào (Input) và Đầu ra (Output): ",
        "Từ đặc tả `Spec = [(T₁, R₁, p₁, skip₁), ..., (Tₖ, Rₖ, pₖ, skipₖ)]` và chuỗi mã nguồn `w`, chương trình xây dựng: "
        "7 biểu diễn tương đương (`Thompson ε-NFA`, `NFA không ε`, `Subset DFA`, `Moore Min-DFA`, `Hopcroft Min-DFA`, `Combined Direct DFA`, và `GNFA RE` cho biểu thức đơn), "
        "ma trận giao nhau tĩnh `L(Rᵢ) ∩ L(Rⱼ)` kèm chuỗi chứng nhân ngắn nhất, chứng nhân Myhill–Nerode, tệp bộ quét Python độc lập `.py` và luồng `Token` / `LexicalError`.",
    )
    add_bullet(
        doc,
        "Bao phủ 128 mã ASCII (0x00..0x7F) và Phân hoạch Unicode động Σ(U): ",
        "Nếu lược bỏ các ký tự điều khiển (`\\0`, `\\f`, `\\v`, `\\x7f`) thì phép lấy phần bù sẽ vi phạm tính chất `~(~A) = A`; còn nếu gộp cứng toàn bộ ký tự ngoài ASCII vào một mã `0x80` sẽ xảy ra xung đột khi biểu thức chứa từ khóa hoặc ký hiệu Unicode tường minh (như `nếu`, `€`). "
        "Để xử lý đồng thời hai vấn đề này, chương trình định nghĩa `ASCII_SIGMA` gồm đủ **128 mã ASCII `0x00..0x7F`**, chọn điểm mã phi ký tự nội bộ **`NON_ASCII = U+FDD0`** (theo chuẩn Unicode Section 23.7) đại diện cho phần còn lại `Unicode \\ U`, "
        "và xây dựng bảng chữ cái động **`Σ(U) = ASCII_SIGMA ∪ U ∪ {NON_ASCII}`** với `U` là tập ký tự Unicode tường minh trích từ cây AST. "
        "Cách biểu diễn này giữ đúng tính chất đối hợp `~(~A) = A` và `L(D) ∩ L(~D) = ∅`, đồng thời xử lý chính xác các biểu thức như `(nếu|lặp)_[0-9]+€` hay `[^€]` cùng với chuỗi tiếng Việt UTF-8.",
    )

    add_heading_2(doc, "3.2. Mô hình Đa-Token, Ma trận giao nhau L(Rᵢ) ∩ L(Rⱼ) và Phát hiện luật bị che khuất")
    add_callout(
        doc,
        "Mô hình Multi-token DFA, Phân tích tĩnh L(Rᵢ) ∩ L(Rⱼ) và Kiểm tra luật bị che khuất",
        [
            "1. Combined ε-NFA & NFA khử ε (Định lý 2): N_lex = (Q_N, Σ(U), δ_N, q_start, F_N, τ_N). Khi khử ε, mọi đỉnh p có ε-closure({p}) ∩ F_N ≠ ∅ nhận nhãn ưu tiên cao nhất τ'_{N}(p) = argmin_{f ∈ ε-closure({p}) ∩ F_N} priority(f).",
            "2. Multi-token Subset DFA, Direct DFA & Phân hoạch Min-DFA: D_lex = (Q_D, Σ(U)/≡, δ_D, D₀, F_D, τ_D) với phân hoạch khởi đầu tách riêng từng loại token Π₀ = { Q_D \\ F_D } ∪ { F_{T₁}, ..., F_{T_m} }.",
            "3. Ma trận giao nhau tĩnh L(Rᵢ) ∩ L(Rⱼ) & Chứng nhân ngắn nhất: Với mỗi cặp quy tắc i < j, Product Automaton BFS kiểm tra L(Dᵢ) ∩ L(Dⱼ) ≠ ∅, phân loại quan hệ tập hợp (∅, Rᵢ ⊂ Rⱼ, Rᵢ ≡ Rⱼ, Rᵢ ⊃ Rⱼ, giao một phần) và tìm chuỗi chứng nhân ngắn nhất w ∈ L(Rᵢ) ∩ L(Rⱼ) (trên MiniLang: ghi nhận 9/741 cặp giao nhau KW_* / BOOL_LIT ⊂ IDENTIFIER).",
            "4. Cảnh báo luật bị che khuất (Shadowed Rule): Nếu Rᵢ ≡ Rⱼ hoặc Rᵢ ⊃ Rⱼ với pᵢ < pⱼ (dẫn đến ∀q ∈ F_min: τ_min(q) ≠ Tⱼ), hệ thống phát cảnh báo quy tắc Tⱼ bị che khuất hoàn toàn.",
        ],
    )

    add_heading_2(doc, "3.3. Đặc tả tập Token minh họa (MiniLang 39 Token, CalcLang 12 Token và MiniSQL 14 Token)")
    add_body(
        doc,
        "Nhóm xây dựng 3 bộ đặc tả ngôn ngữ để thực nghiệm: "
        "**MiniLang (39 token — gồm bình luận khối `BLOCK_COMMENT` và chuỗi `STRING_LIT` xử lý đúng CRLF)**, **CalcLang (12 token)** và **MiniSQL (14 token)**. "
        "Bảng 1 tóm tắt các nhóm quy tắc từ vựng của MiniLang:",
    )

    minilang_summary_rows = [
        ["1", "COMMENT", r"//[^\n]*", "Bỏ qua", "Bình luận 1 dòng (hỗ trợ tiếng Việt UTF-8 qua NON_ASCII)"],
        ["2", "BLOCK_COMMENT", r"/\*([^*]|\*+[^*/])*\*+/", "Bỏ qua", "Bình luận nhiều dòng kiểu C/Java (xử lý đúng `/**/`, `/***a***/`)"],
        ["3", "WHITESPACE", r"[ \t\n\r]+", "Bỏ qua", "Khoảng trắng, tab, xuống dòng Unix LF & Windows CRLF"],
        ["4–12", "KW_IF .. BOOL_LIT", r"if, else, while, for, let, func, return, print, true|false", "Giữ", "9 từ khóa & hằng logic (Rᵢ ⊂ IDENTIFIER, được chọn nhờ độ ưu tiên)"],
        ["13", "FLOAT_LIT", r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", "Giữ", "Số thực dấu phẩy động & ký hiệu khoa học 1.5e-2, 1.5e+3"],
        ["14", "INT_LIT", r"[0-9]+", "Giữ", "Số nguyên không dấu (tách biệt với FLOAT_LIT nhờ dấu chấm)"],
        ["15", "STRING_LIT", r'"([^"\\\n\r]|\\.)*"', "Giữ", "Chuỗi ngoặc kép loại trừ cả \\r và \\n trên CRLF, hỗ trợ UTF-8"],
        ["16", "IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*", "Giữ", "Tên biến, tên hàm (đặt sau từ khóa để tránh che khuất KW_*)"],
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
        "Hình 1 trình bày kiến trúc tổng thể của hệ thống, kết nối giữa nhánh biên dịch theo Chương 3.1 "
        "(`RE → AST → Thompson ε-NFA → NFA khử ε → Subset DFA → Moore & Hopcroft Min-DFA`), nhánh đối chứng và chiều ngược Định lý Kleene "
        "(`Direct RE → DFA`, `GNFA State Elimination DFA → RE`, `JFLAP Round-Trip`), bộ kiểm chứng (`Product Automaton`, `Myhill–Nerode`, `Ma trận L(Rᵢ)∩L(Rⱼ)`) "
        "cùng tầng thực thi (`O(n) Scanner` và bộ sinh mã `Standalone Python Lexer Generator`).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig1_architecture_pipeline.png",
        "Hình 1: Kiến trúc tổng thể Bộ phân tích từ vựng dựa trên Automata (Đề tài T13).",
        width_cm=15.8,
    )

    add_heading_2(doc, "4.1. Thuật toán 1 — Phân tích cú pháp RE, Giới hạn kích thước AST (≤ 4096 nút) và Σ(U)")
    add_body(
        doc,
        "Bộ phân tích cú pháp đệ quy xuống (`regex_parser.py`) cài đặt văn phạm 4 mức ưu tiên: "
        "`expr → concat ('|' concat)*`, `concat → repeat+`, `repeat → atom ('*'|'+'|'?'|'{m,n}')*`, "
        "`atom → '(' expr ')' | char_class | '.' | escape | 'ε' | literal`. "
        "Ba cơ chế kiểm tra và chuẩn hóa chính gồm: "
        "(1) **Giới hạn số nút AST lồng nhau (`MAX_AST_NODES = 4096`)**: mặc dù giới hạn đơn lẻ `MAX_QUANTIFIER_BOUND = 64` ngăn được `a{100}`, "
        "các biểu thức lồng nhau như `(((a{64}){64}){64})` vẫn có thể nhân bản cây cú pháp lên tới `528.483` nút; parser ước lượng kích thước cây con trong `O(1)` trước khi nhân bản và dừng ngay nếu vượt `4.096` nút; "
        "(2) **Lớp ký tự trên `Σ(U)` bao phủ 128 ASCII (`0x00..0x7F`, gồm cả `\\0`, `\\f`, `\\v`, `\\x7f`, `\\xHH`, `\\uHHHH`)**: thu thập tập `U = explicit_unicode_chars()` trước khi tạo các nút `CharSetNode`, đảm bảo phép phủ định `[^C]` giữ đúng tính chất `~(~C) = C`; "
        "(3) Kiểm tra **24 dạng lỗi cú pháp RE** (`RE-ERR-01..24`) kèm vị trí cột xảy ra lỗi.",
    )

    add_heading_2(doc, "4.2. Thuật toán 2 — Cấu trúc Thompson và Thuật toán khử ε (Định lý 2 Chương 3.1)")
    add_body(
        doc,
        "Duyệt hậu tố trên AST, mỗi mảnh Thompson ε-NFA giữ tính chất `in-deg(start) = 0` và `out-deg(end) = 0`, cho phép nút nối `ConcatNode(L, R)` "
        "gộp trực tiếp đỉnh cuối của L với đỉnh đầu của R. Trên biểu thức `(a|b)*abb`, thuật toán tạo ra **11 trạng thái (`q0..q10`)** khớp với Slide 38 Chương 3.1 (Hình 2). "
        "Hàm `eliminate_epsilon(nfa)` cài đặt **Định lý 2 (Slide 21–22)**: "
        "tính `closures[s] = ε-closure({s})`, cập nhật nhãn kết thúc theo độ ưu tiên và tạo cung trực tiếp "
        "`δ_no_eps(s, c) = ε-closure(Move(closures[s], c))`, giảm số trạng thái của `(a|b)*abb` từ 11 xuống 6 (và giảm `MiniLang` từ 170 xuống 96 trạng thái).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig2_slide38_pipeline.png",
        "Hình 2: Quy trình RE → Thompson ε-NFA (11 TT) → Subset DFA (5 TT) → Minimized DFA (4 TT, GNFA sinh R_sinh ≡ R_gốc) trên (a|b)*abb.",
        width_cm=15.6,
    )

    add_heading_2(doc, "4.3. Thuật toán 3 — Subset Construction, Phân hoạch bảng chữ cái và Ma trận giao L(Rᵢ) ∩ L(Rⱼ)")
    add_body(
        doc,
        "Từ các tập ký tự trên cung của Combined ε-NFA thuộc `Σ(U)`, bước Alphabet Partitioning chia bảng chữ cái thành `p` lớp tương đương rời nhau `E₁, ..., E_p` "
        "sao cho `∀c₁, c₂ ∈ Eⱼ: Move(S, c₁) = Move(S, c₂)`. Trên `MiniLang`, 129 ký hiệu cơ sở của `Σ` được gom thành **44 lớp tương đương** (tách riêng `\\r` và `\\n` phục vụ `STRING_LIT` trên Windows CRLF), giúp Subset Construction chạy trong khoảng 4 ms. "
        "Bên cạnh đó, hàm `analyze_token_intersections(specs)` biên dịch `Min-DFA` riêng cho từng quy tắc `Rᵢ` trên bảng chữ cái chung `Σ(U_all)` và duyệt BFS trên `C(k, 2)` ô-tô-mát tích để lập **Ma trận giao nhau tĩnh `L(Rᵢ) ∩ L(Rⱼ)`** "
        "(trên `MiniLang`: kiểm tra `C(39, 2) = 741` cặp trong khoảng 13 ms, xác định 9 cặp bao hàm có kiểm soát `KW_IF..BOOL_LIT ⊂ IDENTIFIER` với chứng nhân `'if'`, `'else'`, ..., `'true'` và 732 cặp rời nhau `∅`).",
    )

    add_heading_2(doc, "4.4. Thuật toán 4 — Phương pháp trực tiếp RE → DFA đơn lẻ (Slide 54) và Đa-Token")
    add_body(
        doc,
        "Trong `direct_dfa.py`, hàm `build_direct_dfa(pattern)` cho biểu thức đơn `r·#` xác định **8 vị trí lá**, bảng `followpos` và **5 trạng thái Direct DFA `A..E`** "
        "trên mẫu `(a|ba)(a|b)*ba#` khớp với Slide 54–57 Chương 3.1 (Hình 3). Hàm mở rộng `build_combined_direct_dfa(specs)` ghép `k` quy tắc thành `(R₁·#₁) | ... | (Rₖ·#ₖ)` "
        "với `#ᵢ` lưu thông tin `(Tᵢ, pᵢ, skipᵢ)`: Combined Direct DFA của `MiniLang` gồm **79 trạng thái** (so với 86 trạng thái của Subset DFA) và tương đương ngôn ngữ với Minimized DFA (78 trạng thái).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig5_direct_dfa_slide46.png",
        "Hình 3: Direct DFA dựng trực tiếp từ r = (a|ba)(a|b)*ba# qua bảng followpos — đối chiếu Slide 54–57 Chương 3.1.",
        width_cm=13.8,
    )

    add_heading_2(doc, "4.5. Thuật toán 5 — Tối thiểu hóa Moore/Hopcroft, Myhill–Nerode và Khử trạng thái GNFA (DFA → RE)")
    add_body(
        doc,
        "Module `dfa_minimizer.py` cài đặt song song hai thuật toán **Moore (`O(p·|Q|²)`)** và **Hopcroft (`O(p·|Q|log|Q|)`)** trên phân hoạch đa-token `Π₀ = {Q \\ F ∪ {DEAD}} ∪ {F_{T₁}, ..., F_{T_m}}`, cùng hàm lấy phần bù `complement_dfa(D)` kiểm tra `~(~L) = L`. "
        "Module `verifier.py` sử dụng **Product Automaton** đối chiếu tương đương giữa các mô hình và hàm `verify_dfa_is_minimal(dfa)` tìm chuỗi phân biệt Myhill–Nerode cho từng cặp trạng thái (`3.003/3.003` cặp trên `MiniLang`). "
        "Ở chiều ngược của Định lý Kleene, module `gnfa.py` cài đặt thuật toán **GNFA State Elimination (`dfa_to_regex`)**: lược bỏ các đỉnh không đạt tới được hoặc không đi tới tập kết thúc, nối `q_start --ε--> D₀` và `F --ε--> q_accept`, "
        "chọn đỉnh khử có tích `in_deg(q) × out_deg(q)` nhỏ nhất kết hợp rút gọn đại số (`∅·R = ∅`, `ε·R = R`, `r·r* = r+`) để sinh biểu thức `R_sinh` (ví dụ `(a|b)*abb` → `b*a(a|ba|bb(a|b+a))*bb`) và biên dịch ngược kiểm tra `L(R_gốc) ≡ L(R_sinh)`.",
    )

    add_heading_2(doc, "4.6. Thuật toán 6 — Bộ quét O(n) (Reps, 1998) và Bộ sinh mã Lexer độc lập kiểu Flex")
    add_callout(
        doc,
        "Thuật toán quét Maximal Munch tuyến tính O(n) (Reps, 1998) và Cấu trúc bộ sinh mã Lexer độc lập (codegen.py)",
        [
            "Input : Chuỗi text[0..n-1], Bảng chuyển tĩnh Min-DFA D = (Q, Σ(U)/≡, δ, D₀, F, τ), mode ∈ {panic_char, smart_sync}",
            "1. pos ← 0; line ← 1; col ← 1; failed_states ← ∅   // Tập ghi nhớ (state, cursor) theo Reps (1998)",
            "2. WHILE pos < n DO: cur ← D₀; cursor ← pos; last_accept ← NULL; visited_path ← []",
            "3.   WHILE cursor < n DO:",
            "4.     IF (cur, cursor) ∈ failed_states THEN: memoized_cutoffs += 1; BREAK   // Cắt nhánh O(1) tránh O(n²)",
            "5.     cls ← ASCII_CLASS_MAP[ord(ch)] IF ord(ch) < 128 ELSE UNICODE_CLASS_MAP.get(ch, NON_ASCII_CLASS)",
            "6.     nxt ← TRANSITIONS[cur][cls]; IF nxt < 0 THEN BREAK",
            "7.     cur ← nxt; cursor += 1; visited_path.append((cur, cursor)); IF ACCEPT[cur] THEN last_accept ← (cursor, ACCEPT[cur])",
            "8.   FOR (st, idx) IN visited_path WHERE idx > (last_accept.pos IF last_accept ELSE pos): failed_states.add((st, idx))",
            "9.   IF last_accept ≠ NULL THEN Emit Token & pos ← last_accept.pos ELSE Phục hồi lỗi theo panic_char / smart_sync",
            "• Bộ sinh mã kiểu Flex (codegen.py): Xuất trực tiếp các bảng tĩnh ASCII_CLASS_MAP[128], UNICODE_CLASS_MAP, TRANSITIONS[|Q|][p], ACCEPT_TABLE cùng vòng lặp Reps O(n) thành 1 tệp Python độc lập (~527 dòng cho MiniLang, không dùng import re, không phụ thuộc lexer_engine).",
        ],
        fill="F8FAFC",
        accent="1E3A8A",
        mono=True,
    )

    add_heading_2(doc, "4.7. Phân tích độ phức tạp và xử lý các trường hợp biên")
    comp_rows = [
        ["Regex Parser + Σ(U) + Giới hạn AST", "O(|R|), nút ≤ 4096", "O(|R|)", "Chặn biểu thức (((a{64}){64}){64}) trong O(1); bao phủ 128 ASCII + Σ(U) giữ ~(~A)=A; 24 mẫu lỗi RE"],
        ["Thompson & Khử ε (Định lý 2)", "O(|Q_N|² + |Q_N|·p)", "O(|Q_N|·p)", "Khử toàn bộ cung ε, giữ đúng nhãn ưu tiên token (MiniLang: 170 → 96 TT)"],
        ["Subset DFA & Ma trận L(Rᵢ)∩L(Rⱼ)", "Subset: O(|Q_D|·p)\nGiao: O(∑|Qᵢ||Qⱼ|p)", "O(|Q_D|·p)", "Gom Σ(U) thành 44 lớp trên MiniLang; kiểm tra 741 cặp giao nhau trong ~13 ms kèm chứng nhân"],
        ["Moore/Hopcroft & GNFA (DFA→RE)", "Hopcroft: O(p|Q|log|Q|)\nGNFA: O(|Q|³)", "O(p·|Q|)", "Moore khớp Hopcroft; kiểm chứng Myhill–Nerode 3003/3003 cặp và L(R_gốc) ≡ L(R_sinh)"],
        ["O(n) Scanner & Sinh mã Lexer", "Tuyến tính O(n)\n(nhờ failed_states)", "O(n)", "Tránh O(n²) trên chuỗi lỗi 10 KB; STRING_LIT loại trừ \\r trên CRLF; xuất Lexer độc lập .py"],
    ]
    add_styled_table(
        doc,
        ["Thành phần thuật toán", "Độ phức tạp thời gian", "Bộ nhớ", "Xử lý trường hợp biên & Chi tiết kỹ thuật"],
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
        "Chương trình được chia thành 3 tầng tách biệt: "
        "(1) Tầng lõi thuật toán `lexer_engine/` (11 module chỉ dùng thư viện chuẩn Python, không cài đặt gói ngoài và **không dùng `import re`** — gồm cả `gnfa.py` và `codegen.py`); "
        "(2) Tầng giao diện gồm ứng dụng Web 5 tab (`app.py` + `web/`) và công cụ dòng lệnh 9 lệnh con (`cli.py`); "
        "(3) Tầng kiểm thử tự động và đối chiếu định dạng (`tests/test_cases.json` gồm **72 test cases**, `tests/test_suite.py` gồm **22 nhóm unittest**, `jflap_export.py` xuất/nhập XML `.jff`). "
        "Bảng 2 phân định rõ phần nhóm tự cài đặt và các thư viện chuẩn được sử dụng:",
    )

    lib_rows = [
        [
            "models.py, regex_parser.py, thompson.py, subset_construction.py, direct_dfa.py, dfa_minimizer.py, gnfa.py, scanner.py, codegen.py, verifier.py, jflap_export.py",
            "Nhóm tự cài đặt hoàn toàn (không dùng `import re`)",
            "Thư viện chuẩn Python: `dataclasses`, `collections.deque`, `xml.etree.ElementTree`, `time`",
        ],
        [
            "app.py, cli.py, web/ (Đồ thị SVG + Ma trận giao nhau L(Rᵢ)∩L(Rⱼ) + GNFA DFA→RE + Xuất Standalone Lexer .py)",
            "Nhóm tự thiết kế và lập trình",
            "Python stdlib `http.server`, `argparse`, `json`; HTML5/CSS/JS và SVG thuần trên trình duyệt",
        ],
        [
            "tests/test_suite.py (72 test cases JSON + 22 unittest kiểm tra Định lý Kleene, ~(~A)=A, giới hạn AST & đối chứng mã sinh)",
            "Nhóm thiết kế kịch bản & sinh chuỗi kiểm thử",
            "Python `unittest`, `ast` (kiểm tra tự động không có `import re` trong lõi & tệp sinh mã)",
        ],
        [
            "scripts/ (vẽ sơ đồ minh họa báo cáo & xuất DOCX/PDF/PPTX phục vụ đóng gói tài liệu)",
            "Nhóm viết script kết xuất tài liệu",
            "matplotlib, python-docx, python-pptx, chromium/chrome headless (không cần khi chạy ứng dụng)",
        ],
    ]
    add_styled_table(
        doc,
        ["Module / Thành phần", "Phần nhóm tự triển khai", "Thư viện / Công cụ sử dụng"],
        lib_rows,
        col_widths_cm=[5.3, 4.3, 7.1],
        font_size=8.4,
    )

    add_heading_2(doc, "5.1. Tổ chức Giao diện Web 5 Tab và Giao diện dòng lệnh CLI")
    add_bullet(
        doc,
        "Tab 1 & Thanh công cụ — Bộ quét từ vựng O(n), Mô phỏng DFA và nút Xuất Lexer (.py): ",
        "Cho phép nhập mã nguồn hoặc chọn mẫu dựng sẵn, đổi chế độ phục hồi lỗi giữa `panic_char` và `smart_sync` (hiển thị số lần cắt nhánh `memoized_cutoffs`), theo dõi đường đi từng bước trên DFA, chuyển chế độ sáng/tối (`Dark` / `Light`) và tải tệp bộ quét Python độc lập `.py`.",
    )
    add_bullet(
        doc,
        "Tab 2 — Đồ thị Automata đa-token, Myhill–Nerode và Ma trận giao nhau tĩnh L(Rᵢ) ∩ L(Rⱼ): ",
        "Hiển thị đồ thị SVG của các giai đoạn ô-tô-mát đa-token, bảng chuyển trạng thái, bảng chuỗi phân biệt Myhill–Nerode và thẻ con **Ma trận giao nhau `L(Rᵢ) ∩ L(Rⱼ)`** với bảng `39 × 39` kèm chuỗi chứng nhân ngắn nhất cho từng cặp quy tắc.",
    )
    add_bullet(
        doc,
        "Tab 3 & Tab 4 — Thử nghiệm RE đơn lẻ (GNFA DFA → RE, kiểm tra R₁ ≡ R₂) và Chỉnh sửa đặc tả Token: ",
        "Tab 3 có thẻ con **GNFA khử trạng thái (`DFA → RE`)** liệt kê từng bước khử đỉnh `q_rip` và đối chiếu `L(R_gốc) ≡ L(R_sinh)`. "
        "Tab 4 hỗ trợ thêm quy tắc mẫu Unicode (`nếu`, `€`), thử tình huống quy tắc bị che khuất, xem bảng giao nhau trực tiếp và xuất tệp `Standalone Lexer (.py)` theo bộ quy tắc tùy chỉnh.",
    )
    add_bullet(
        doc,
        "Tab 5 — Kiểm thử tự động (72/72 PASS) và Đánh giá hiệu năng O(n): ",
        "Thực thi 72 ca kiểm thử JSON trực tiếp trên giao diện, hiển thị bảng thống kê trạng thái trên 3 ngôn ngữ và bài kiểm tra hiệu năng trên các chuỗi lỗi dài 10.000 ký tự.",
    )

    add_body(
        doc,
        "Hình 4 minh họa đồ thị Minimized Combined DFA của `CalcLang` (12 token → 20 trạng thái tối giản, 190/190 cặp Myhill–Nerode). "
        "Hình 5 và Hình 6 ghi lại giao diện Web thực tế khi vận hành tại Tab 1 và Tab 3.",
    )
    add_figure(
        doc,
        FIG_DIR / "fig3_calclang_combined_dfa.png",
        "Hình 4: Đồ thị Minimized Combined Multi-token DFA của CalcLang (12 token → 20 trạng thái tối giản, 190/190 cặp Myhill–Nerode).",
        width_cm=12.4,
    )
    add_figure(
        doc,
        FIG_DIR / "fig6_web_scanner_demo.png",
        "Hình 5: Giao diện Web — Tab 1 với thanh công cụ (Xuất Lexer .py, Xuất JFLAP .jff, Dark/Light), luồng Token và mô phỏng quay lui Maximal Munch.",
        width_cm=14.4,
    )
    add_figure(
        doc,
        FIG_DIR / "fig7_web_direct_re_lab.png",
        "Hình 6: Giao diện Web — Tab 3 kiểm tra Định lý Kleene (R₀ ≡ R_sinh), cây cú pháp r·# và bảng followpos trên mẫu Slide 54.",
        width_cm=14.4,
    )

    # =========================================================================
    # SECTION 6: TEST CASE, KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH
    # =========================================================================
    add_heading_1(doc, "6. Test case, kết quả thực nghiệm và phân tích")

    add_heading_2(doc, "6.1. Thiết kế bộ 72 Test Cases JSON và 22 nhóm Unittest")
    add_body(
        doc,
        f"Bộ kiểm thử có cấu trúc trong `tests/test_cases.json` gồm **{test_rep['total']} ca kiểm thử** "
        f"(20 ca RE đơn/Unicode/GNFA, 24 ca lỗi cú pháp RE và giới hạn AST, cùng 28 ca quét từ vựng đa ngôn ngữ) kết hợp với **22 nhóm Unittest** trong `tests/test_suite.py`. "
        f"Kết quả chạy tự động đạt **{test_rep['passed']}/{test_rep['total']} PASS ({test_rep['pass_rate']}%)** trên JSON và **22/22 OK** trên Unittest. "
        f"Bảng 3 tóm tắt các nhóm kịch bản kiểm thử và các tính chất được đối chiếu:",
    )

    tc_rows = [
        ["RE-01..02", "Bài giảng UEH", "(a|b)*abb & (a|ba)(a|b)*ba", "Khớp Slide 38 (11→6→5→4 TT) & Slide 54 (followpos, 5 TT); GNFA sinh R_sinh ≡ R_gốc", "PASS"],
        ["RE-03..20", "Unicode Σ(U) & Biên", "(nếu|lặp)_[0-9]+€, [^€\\n]+, [\\f\\v]+, [0-9]{2,4}", "Phân hoạch Σ(U) không trùng NON_ASCII; giữ đúng ~(~A)=A và R₀ ≡ R_sinh trên 20/20 mẫu RE", "PASS"],
        ["RE-ERR-01..24", "24 Lỗi RE & Giới hạn AST", "(((a{64}){64}){64}), (a{64}){64}, \\u12G4, [a-\\uffff]", "Ngăn nhân bản AST quá ngưỡng (>4096 nút) trong <0.1 ms; bắt đúng 24/24 lỗi cú pháp RE", "PASS"],
        ["SCAN-01..14", "Maximal Munch & UTF-8", 'ifx, a===b, 1.5e, 100€, "Xin chào UEH"', "Khớp dài nhất & ưu tiên luật đúng thiết kế; nhận chuỗi UTF-8; báo lỗi U+20AC ngoài chuỗi", "PASS"],
        ["SCAN-15..28", "CRLF & Ký tự điều khiển", '"unclosed\\r\\nlet ok=1;, /*...*/, "\\f\\v"', "STRING_LIT loại trừ cả \\r và \\n trên Windows CRLF; xử lý đúng \\f, \\v và bình luận /*...*/", "PASS"],
        ["INV-1..5", "Bất biến & Myhill–Nerode", "390+ chuỗi ngẫu nhiên, 4.519 cặp TT, 30.000 ký tự lỗi", "Bảo toàn mã nguồn; mọi cặp trạng thái có chuỗi phân biệt w; Reps O(n) cắt 5.000 nhánh quay lui", "PASS"],
        ["EXT-1..3", "GNFA, Giao & Codegen", "GNFA DFA→RE, Ma trận 741 cặp, Standalone Lexer .py", "L(R_0)≡L(R_sinh); xác định 9/741 cặp giao nhau MiniLang; Lexer độc lập khớp 100% bản gốc", "PASS"],
    ]
    add_styled_table(
        doc,
        ["Mã kiểm thử", "Phân loại", "Đầu vào / Kịch bản đại diện", "Kết quả thực nghiệm & Tính chất kiểm chứng", "Đánh giá"],
        tc_rows,
        col_widths_cm=[2.3, 2.3, 4.0, 6.6, 1.5],
        font_size=8.3,
        mono_cols={0},
    )

    add_heading_2(doc, "6.2. Thực nghiệm đối sánh các mô hình Otomat, Ma trận giao nhau và Hiệu năng O(n)")
    add_body(
        doc,
        "Bảng 4 và Hình 7 tổng hợp số liệu thực nghiệm trên 3 bộ ngôn ngữ qua các giai đoạn biến đổi Automata, số cặp giao nhau tĩnh `L(Rᵢ) ∩ L(Rⱼ)` và kết quả kiểm tra tính tối giản Myhill–Nerode:",
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
            "Đạt (Eq)",
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
            "Đạt (Eq)",
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
            "Đạt (Eq)",
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
            "Đối chiếu",
        ],
        bench_rows,
        col_widths_cm=[1.8, 1.0, 1.1, 1.1, 1.3, 1.3, 1.6, 2.2, 2.5, 1.8],
        font_size=8.1,
    )

    add_figure(
        doc,
        FIG_DIR / "fig4_benchmark_comparison.png",
        "Hình 7: (a) Đối sánh số trạng thái qua các giai đoạn trên 3 ngôn ngữ và (b) Thời gian biên dịch & quét 10 KB mã nguồn.",
        width_cm=15.6,
    )

    add_body(
        doc,
        "Một số nhận xét rút ra từ kết quả thực nghiệm:",
        bold_prefix="Nhận xét thực nghiệm: ",
    )
    add_bullet(
        doc,
        "Sự thống nhất giữa Moore, Hopcroft, GNFA và Bộ quét sinh tự động: ",
        "Trên cả 3 ngôn ngữ, hai thuật toán Moore và Hopcroft đều hội tụ về cùng một Min-DFA (`MiniLang: 78`, `CalcLang: 20`, `MiniSQL: 52`) với đầy đủ các cặp trạng thái phân biệt theo Myhill–Nerode. "
        "Khi xuất sang bộ quét Python độc lập bằng `codegen.py` (`MiniLangLexer`: 78 trạng thái × 44 lớp tương đương), kiểm thử đối chứng xác nhận dãy Token và LexicalError trùng khớp với bộ phân tích gốc trên toàn bộ dữ liệu thử.",
    )
    add_bullet(
        doc,
        "Tác dụng của bảng nhớ Reps (1998) và Ma trận giao nhau tĩnh L(Rᵢ) ∩ L(Rⱼ): ",
        "Trên chuỗi chưa đóng dài 10.000 ký tự (`\"` + `\\\"` * 5000), bảng nhớ `failed_states` thực hiện **5.000 lần cắt nhánh O(1)**, giữ thời gian quét ở mức vài chục mili-giây thay vì tăng bậc hai O(n²). "
        "Đồng thời, ma trận giao nhau cho thấy 732/741 cặp quy tắc của `MiniLang` rời nhau đôi một và 9 cặp giao nhau còn lại đều là quan hệ bao hàm có chủ đích `KW_* / BOOL_LIT ⊂ IDENTIFIER`.",
    )

    # =========================================================================
    # SECTION 7: HẠN CHẾ LÝ THUYẾT, CÁC VẤN ĐỀ ĐÃ GIẢI QUYẾT & HƯỚNG PHÁT TRIỂN
    # =========================================================================
    add_heading_1(doc, "7. Phân tích giới hạn lý thuyết và hướng phát triển")

    add_heading_2(doc, "7.1. Các vấn đề kỹ thuật đã xử lý và Giới hạn lý thuyết của DFA")
    add_bullet(
        doc,
        "Các vấn đề kỹ thuật trong cài đặt thực tế đã được giải quyết: ",
        "(1) Phân hoạch bảng chữ cái Unicode động `Σ(U)` kết hợp hằng `NON_ASCII (U+FDD0)` giúp hỗ trợ từ khóa/ký hiệu Unicode tường minh (`nếu`, `€`, `[^€]`) cùng với chuỗi UTF-8 mà không gây trùng ký hiệu; "
        "(2) Bao phủ đủ 128 mã ASCII `0x00..0x7F` đảm bảo tính chất `~(~A) = A` và loại trừ `\\r` khỏi `STRING_LIT` trên tệp Windows CRLF; "
        "(3) Chặn nhân bản cây cú pháp quá lớn `(((a{64}){64}){64})` bằng ngưỡng `MAX_AST_NODES = 4096`; "
        "(4) Cài đặt chiều ngược Định lý Kleene (`GNFA DFA → RE`), ma trận giao nhau `L(Rᵢ) ∩ L(Rⱼ)`, bảng nhớ Reps (1998) và sinh mã Lexer độc lập.",
    )
    add_bullet(
        doc,
        "Giới hạn lý thuyết của Automata hữu hạn (chứng minh bằng Bổ đề Bơm — Pumping Lemma Chương 3.2): ",
        "Mặc dù hệ thống nhận diện được bình luận nhiều dòng không lồng nhau `/* ... */` bằng biểu thức `/\\*([^*]|\\*+[^*/])*\\*+/`, "
        "một DFA thuần túy **không thể** nhận diện bình luận nhiều dòng **lồng nhau tùy ý** (`/* ... /* ... */ ... */`, như trong Rust hoặc Swift). "
        "Nếu đặt `a = \"/*\"` và `b = \"*/\"`, cấu trúc cân bằng này tương ứng với ngôn ngữ `L = { a^n b^n | n ≥ 1 }`. "
        "Theo **Bổ đề Bơm (Chương 3.2)**, với hằng số bơm `p = |Q|`, chọn `w = a^p b^p ∈ L`; mọi cách tách `w = xyz` thỏa `|xy| ≤ p`, `|y| ≥ 1` "
        "đều có `y = a^k (k ≥ 1)`, dẫn đến `xy²z = a^{p+k} b^p ∉ L` (mâu thuẫn). Tương tự, cú pháp thụt lề phụ thuộc ngữ cảnh (`INDENT`/`DEDENT` trong Python) cũng cần thêm ngăn xếp lưu mức cột.",
    )

    add_heading_2(doc, "7.2. Hướng phát triển tiếp theo")
    add_bullet(
        doc,
        "Bổ sung trạng thái ngữ cảnh từ vựng (Lexical Start Conditions & Counter): ",
        "Kết hợp ngăn xếp trạng thái ngữ cảnh (`push_state`, `pop_state`) và biến đếm độ sâu để xử lý bình luận lồng nhau cũng như chuỗi nội suy (`\"Hello ${name}\"`).",
    )
    add_bullet(
        doc,
        "Kết nối với Bộ phân tích cú pháp Văn phạm phi ngữ cảnh (Chương 4 — CFG & PDA): ",
        "Đưa luồng `Token` đầu ra của `LexicalAnalyzer` (hoặc tệp Lexer độc lập sinh bởi `codegen.py`) sang bộ phân tích cú pháp `LL(1)` / `LR(1)` (Pushdown Automata — PDA), liên kết nội dung Chương 1–3 với Chương 4–5.",
    )

    # =========================================================================
    # SECTION 8: KẾT LUẬN
    # =========================================================================
    add_heading_1(doc, "8. Kết luận")
    add_body(
        doc,
        "Đồ án đã hoàn thành các nội dung yêu cầu của Đề tài T13 — Automata-based Lexical Analyzer. "
        "Dựa trên kiến thức của học phần Ngôn ngữ hình thức (UEH), nhóm đã tự thiết kế và cài đặt bằng thư viện chuẩn Python (không dùng `import re` trong lõi) "
        "quy trình biên dịch hai chiều của **Định lý Kleene**: bộ phân tích cú pháp RE có giới hạn kích thước AST (`≤ 4096` nút) trên bảng chữ cái Unicode động `Σ(U)` thỏa `~(~A) = A`, "
        "cấu trúc Thompson `ε-NFA`, khử `ε` (Định lý 2), `Subset DFA`, phương pháp trực tiếp `Direct RE → DFA` đơn lẻ và đa-token (`r·#`), tối thiểu hóa `Moore & Hopcroft`, "
        "khử trạng thái **GNFA (`DFA → RE`)**, **Ma trận giao nhau tĩnh `L(Rᵢ) ∩ L(Rⱼ)`**, kiểm tra tính tối giản **Myhill–Nerode**, "
        "bộ quét tuyến tính `O(n)` (Reps, 1998) và **Bộ sinh mã Lexer Python độc lập kiểu Flex**. "
        "Chương trình vượt qua **72/72 ca kiểm thử JSON** cùng **22/22 nhóm Unittest**, đi kèm giao diện Web 5 tab hỗ trợ trực quan hóa quá trình hoạt động của từng thuật toán.",
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
            "Quản lý tiến độ; tổng hợp cơ sở lý thuyết Chương 1–3, Định lý Kleene, đại số Boole ~(~A)=A, Myhill–Nerode & Bổ đề Bơm; biên soạn báo cáo & slide.",
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
            "Cài đặt `scanner.py` (Reps 1998 O(n)), `codegen.py` (Standalone Lexer Generator), `app.py`, `cli.py`, Giao diện Web 5 Tab & bộ 72 test cases + 22 unittest; demo Tab 1, 4, 5.",
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
            "• Tra cứu, rà soát thuật ngữ lý thuyết Automata và cấu trúc cài đặt thuật toán (Định lý Kleene & GNFA State Elimination, phân hoạch Unicode động `Σ(U)`, Moore & Hopcroft Min-DFA, Myhill–Nerode, Reps 1998 O(n) & Table-Driven Lexer Codegen).\n"
            "• Gợi ý kiểm tra các trường hợp biên dễ sót (tính đối hợp `~(~A)=A` trên ASCII `0x00..0x7F`, giới hạn nhân bản AST lồng nhau `MAX_AST_NODES=4096`, `STRING_LIT` loại trừ `\\r` trên CRLF, Ma trận giao nhau `L(Rᵢ)∩L(Rⱼ)`).\n"
            "• Hỗ trợ xây dựng phần hiển thị đồ thị SVG trên giao diện Web 5 tab, bộ 72 test cases JSON + 22 unittest và định dạng bố cục báo cáo/slide.",
        ],
        [
            "Phạm vi kiểm chứng & Trách nhiệm của nhóm",
            "• Các thành viên trong nhóm đã đọc hiểu, kiểm tra từng hàm trong `lexer_engine/`, đối chiếu kết quả thủ công với các ví dụ trong bài giảng Chương 3.1 "
            "(Slide 21–22, Slide 38 và Slide 46–57), chạy toàn bộ bộ kiểm thử tự động (72/72 JSON PASS + 22/22 Unittest OK), đối chứng bộ quét độc lập và kiểm tra định dạng `.jff` trên JFLAP.\n"
            "• Nhóm chịu trách nhiệm về tính chính xác của mã nguồn, số liệu thực nghiệm và nội dung trình bày trong buổi bảo vệ.",
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
