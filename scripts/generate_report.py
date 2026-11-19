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

        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
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
        "Xây dựng Bộ Phân Tích Từ Vựng Tổng Quát Dựa Trên Biểu Thức Chính Quy,\n"
        "Thompson ε-NFA, Khử ε (Định lý 2), Subset Construction, Direct DFA Đa-Token,\n"
        "Tối Thiểu Hóa Moore & Hopcroft O(|E|·|Q|log|Q|), Chứng Minh Myhill–Nerode & Bộ Quét O(n)"
    )

    _cp("BỘ GIÁO DỤC VÀ ĐÀO TẠO", 12, bold=True, color=NAVY, space_before=6, space_after=2)
    _cp("TRƯỜNG ĐẠI HỌC KINH TẾ TP. HỒ CHÍ MINH (UEH)", 13.5, bold=True, color=NAVY, space_after=2)
    _cp("KHOA CÔNG NGHỆ THÔNG TIN KINH DOANH — NGÀNH KHOA HỌC MÁY TÍNH", 11, bold=True, color=MUTED, space_after=26)

    _cp("BÁO CÁO TIỂU LUẬN CUỐI KỲ", 16, bold=True, color=BLUE, space_before=16, space_after=6)
    _cp("HỌC PHẦN: NGÔN NGỮ HÌNH THỨC (INTRODUCTION TO FORMAL LANGUAGES)", 11.5, bold=True, color=DARK, space_after=24)

    _cp("ĐỀ TÀI T13:", 13.5, bold=True, color=BLUE, space_before=6, space_after=4)
    _cp("AUTOMATA-BASED LEXICAL ANALYZER", 20, bold=True, color=NAVY, space_after=6)
    _cp(subtitle_text, 11.0, italic=True, color=MUTED, space_after=30)

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
        ["1", "[Điền Họ tên Thành viên 1]", "[MSSV 1]", "Nhóm trưởng · Lý thuyết, Myhill–Nerode & Báo cáo"],
        ["2", "[Điền Họ tên Thành viên 2]", "[MSSV 2]", "Regex Parser ({m,n}, UTF-8) · Thompson, Khử ε & Direct DFA"],
        ["3", "[Điền Họ tên Thành viên 3]", "[MSSV 3]", "Subset Construction · Moore & Hopcroft Min-DFA · Verifier"],
        ["4", "[Điền Họ tên Thành viên 4]", "[MSSV 4]", "Scanner Maximal Munch O(n) · Web Studio 5 Tab & 62 Tests"],
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
        "phân tích từ vựng (Lexical Analysis) là giai đoạn đầu tiên đóng vai trò đọc dòng ký tự thô của mã nguồn "
        "và nhóm chúng thành dãy các đơn vị từ vựng có nghĩa gọi là token (từ khóa, định danh, hằng số, chuỗi, toán tử, "
        "dấu phân cách), đồng thời lọc bỏ khoảng trắng, bình luận đơn dòng/nhiều dòng và phát hiện chính xác tọa độ lỗi từ vựng. "
        "Điểm đặc biệt tạo nên cầu nối trực tiếp giữa học phần Ngôn ngữ hình thức và Kỹ thuật trình biên dịch nằm ở chỗ: "
        "mọi lớp token của ngôn ngữ lập trình đều thuộc lớp Ngôn ngữ chính quy (Regular Languages) — do đó có thể được "
        "đặc tả ngắn gọn bằng Biểu thức chính quy (Regular Expression — RE) và thực thi tự động bằng Automata hữu hạn đơn định (DFA) "
        "với tốc độ tuyến tính O(n) theo độ dài mã nguồn mà không bao giờ chịu rủi ro treo máy hàm mũ O(2^n) (ReDoS) như các bộ khớp regex quay lui.",
    )

    add_body(
        doc,
        "Thay vì viết tay bộ quét bằng các câu lệnh if/else cứng nhắc cho một ngôn ngữ cố định hoặc phụ thuộc vào thư viện biểu thức "
        "chính quy hộp đen có sẵn (như module `re` của Python), đề tài T13 — Automata-based Lexical Analyzer hướng tới việc xây dựng một "
        "bộ sinh và thực thi bộ phân tích từ vựng tổng quát (Lexical Analyzer Generator & Interactive Web Studio) hoàn toàn từ gốc lý thuyết Automata hữu hạn.",
    )

    add_heading_2(doc, "1.1. Mục tiêu cụ thể của đồ án")
    add_bullet(
        doc,
        "Tự cài đặt 100% chuỗi 6 phương pháp Automata bằng Python thuần (Zero `import re` trong lõi): ",
        "Xây dựng độc lập từ con số 0 toàn bộ đường ống: Phân tích cú pháp RE (hỗ trợ cả định lượng đếm `{m}`, `{m,}`, `{m,n}` và đại diện Unicode `NON_ASCII`) → "
        "Cấu trúc Thompson (`RE → ε-NFA`) → Khử chuyển tiếp rỗng theo Định lý 2 Chương 3.1 (`ε-NFA → NFA không ε`) → "
        "Thuật toán tập con (`Subset Construction`) → Tối thiểu hóa Multi-token DFA bằng cả hai thuật toán **Moore Partition Refinement** và **Hopcroft O(|E|·|Q|log|Q|)**.",
    )
    add_bullet(
        doc,
        "Mở rộng nhánh Direct RE → DFA cho cả Biểu thức đơn lẻ và Đa-Token kết hợp: ",
        "Triển khai thuật toán xây dựng DFA trực tiếp từ cây cú pháp gia tố `r·#` (`nullable`, `firstpos`, `lastpos`, `followpos`) khớp 100% Slide 46–57 Chương 3.1, "
        "đồng thời mở rộng sang biểu thức đa-token `(R₁·#₁) | (R₂·#₂) | ... | (Rₖ·#ₖ)`, kiểm chứng tương đương 6 chiều bằng **Product Automaton**, "
        "chứng minh tính tối giản tuyệt đối theo **Định lý Myhill–Nerode** và kiểm chứng đọc/ghi khứ hồi file `.jff` chuẩn JFLAP 7.x.",
    )
    add_bullet(
        doc,
        "Bộ quét Maximal Munch Tuyến tính O(n) (Reps, 1998), Phát hiện Luật Che khuất & Phục hồi lỗi kép: ",
        "Cài đặt bộ quét bảng chuyển DFA với kỹ thuật Memoization `failed_states` cắt nhánh quay lui bậc hai O(n²), tự động phát hiện quy tắc từ vựng bị che khuất "
        "(Shadowed / Dead Token Rules), hỗ trợ bình luận nhiều dòng `/* ... */`, chuỗi tiếng Việt UTF-8 và 2 chế độ phục hồi lỗi (`panic_char` và `smart_sync`).",
    )
    add_bullet(
        doc,
        "Kiểm thử toàn diện 62 Test Cases + 16 Unittest Bất biến & Trực quan hóa Web Studio 5 Tab: ",
        "Xây dựng bộ 62 kịch bản kiểm thử JSON (16 RE đơn & biên, 20 bẫy lỗi cú pháp RE, 26 kịch bản quét mã nguồn) cùng 16 bộ Unittest kiểm chứng 5 bất biến toán học "
        "và ứng dụng Web LexAutomata Studio 5 Tab trực quan hóa toàn bộ đồ thị SVG, bảng chuyển và hoạt ảnh từng bước.",
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

    add_heading_2(doc, "2.1. Bảng chữ cái mở rộng UTF-8 hữu hạn, Ngôn ngữ và Biểu thức chính quy (RE)")
    add_body(
        doc,
        "Cho bảng chữ cái hữu hạn khác rỗng Σ. Tập tất cả chuỗi hữu hạn trên Σ ký hiệu là Σ* (chứa chuỗi rỗng ε). "
        "Một ngôn ngữ L là tập con L ⊆ Σ*. Biểu thức chính quy (Regular Expression — RE) trên Σ được định nghĩa quy nạp: "
        "(i) ∅ biểu diễn ∅; (ii) ε biểu diễn {ε}; (iii) ∀a ∈ Σ, a biểu diễn {a}; "
        "(iv) Nếu r và s là các RE biểu diễn L(r) và L(s), thì `(r | s)` biểu diễn L(r) ∪ L(s) (phép hợp), "
        "`(r·s)` biểu diễn L(r)L(s) (phép nối kết), và `(r*)` biểu diễn L(r)* = ⋃_{k≥0} L(r)^k (bao đóng Kleene). "
        "Thứ tự ưu tiên toán tử từ cao đến thấp: Ngoặc đơn `(…)` > Định lượng (`*`, `+`, `?`, `{m,n}`) > Nối kết (`·`) > Phép hợp (`|`). "
        "Các toán tử mở rộng được quy về 3 phép toán cơ sở theo luật đại số: `r+ ≡ r·r*`, `r? ≡ (r | ε)`, `r{m,n} ≡ r^m · (r?)^{n-m}`, "
        "`r{m,} ≡ r^m · r*`, lớp ký tự `[c₁...c_m] ≡ (c₁|...|c_m)` và lớp phủ định `[^C] ≡ Σ \\ C`.",
    )

    add_heading_2(doc, "2.2. Chuỗi 4 Định lý Chương 3.1: ε-NFA, NFA không ε (Định lý 2), Subset DFA & Min-DFA")
    add_callout(
        doc,
        "Chuỗi Định lý Chuyển đổi Tương đương RE → ε-NFA → NFA không ε → Subset DFA → Minimized DFA",
        [
            "• Định lý 3 (Cấu trúc Thompson, 1968 — Slide 24–30 Chương 3.1): Mọi biểu thức chính quy r đều chuyển được thành ε-NFA N = (Q, Σ, δ, q₀, {f}) "
            "có đúng 1 trạng thái đầu (in-deg = 0), 1 trạng thái kết thúc (out-deg = 0), tối đa 2|r| trạng thái và bậc ra mỗi đỉnh ≤ 2.",
            "• Định lý 2 (Khử chuyển tiếp rỗng ε-NFA → NFA không ε — Slide 21–22 Chương 3.1): Từ ε-NFA N = (Q, Σ, δ, q₀, F), ta dựng NFA không có ε-chuyển tiếp "
            "N' = (Q, Σ, δ', q₀, F') tương đương (L(N') = L(N)) với: δ'(p, a) = ε-closure(Move(ε-closure({p}), a)) và F' = { p ∈ Q | ε-closure({p}) ∩ F ≠ ∅ }.",
            "• Định lý 1 (Đơn định hóa Tập con — Rabin & Scott, 1959; Slide 18 Chương 3.1): Từ ε-NFA N, thuật toán Subset Construction dựng DFA D = (Q_D, Σ, δ_D, D₀, F_D) "
            "với D₀ = ε-closure({q₀}) và δ_D(S, a) = ε-closure(Move(S, a)), trong đó Move(S, a) = ⋃_{p ∈ S} δ(p, a).",
            "• Định lý Myhill–Nerode & Tối thiểu hóa DFA (Moore, 1956; Hopcroft, 1971; Giải thuật 3.6): Với mọi ngôn ngữ chính quy L, tồn tại duy nhất (sai khác đẳng cấu) "
            "một DFA tối giản có số trạng thái nhỏ nhất. Một DFA không có trạng thái dư thừa là tối giản tuyệt đối khi và chỉ khi mọi cặp trạng thái phân biệt (p, q) "
            "đều tồn tại chuỗi phân biệt w ∈ Σ* sao cho τ(δ̂(p, w)) ≠ τ(δ̂(q, w)).",
        ],
    )

    add_heading_2(doc, "2.3. Phương pháp Trực tiếp RE → DFA (Chương 3.1 Mục 2.5) & Nguyên lý Maximal Munch O(n)")
    add_bullet(
        doc,
        "Phương pháp trực tiếp trên cây cú pháp gia tố r·# (Slide 43–57 Chương 3.1): ",
        "Bổ sung ký hiệu kết thúc `# ∉ Σ` vào sau biểu thức (`r·#`), đánh số các nút lá mang ký hiệu thuộc Σ ∪ {#} từ `1..n`, "
        "tính đệ quy 3 hàm `nullable(v)`, `firstpos(v)`, `lastpos(v)` và bảng `followpos(i)` tại các nút nối kết (`∀i ∈ lastpos(c₁): followpos(i) ∪= firstpos(c₂)`) "
        "và nút sao (`∀i ∈ lastpos(c₁): followpos(i) ∪= firstpos(c₁)`). Với bài toán đa-token, nhóm mở rộng thành cây kết hợp `(R₁·#₁) | (R₂·#₂) | ... | (Rₖ·#ₖ)` "
        "để sinh trực tiếp Combined Multi-token Direct DFA mà không cần đi qua ε-NFA.",
    )
    add_bullet(
        doc,
        "Quy tắc Khớp Dài Nhất (Maximal Munch), Ưu Tiên Luật (Rule Priority) & Memoization Tuyến tính O(n) (Reps, 1998): ",
        "Tại vị trí `pos`, bộ quét chọn tiền tố dài nhất đưa DFA tới trạng thái kết thúc (`ifx` → `IDENTIFIER('ifx')`, `===` → `OP_EQ('==') + OP_ASSIGN('=')`); "
        "nếu cùng độ dài khớp nhiều luật (`if` khớp cả `KW_IF` và `IDENTIFIER`), chọn luật có chỉ số ưu tiên nhỏ nhất. "
        "Đặc biệt, để ngăn chặn trường hợp xấu nhất quay lui bậc hai O(n²) trên chuỗi lỗi dài (ví dụ chuỗi `\"aaaa...` chưa đóng), "
        "bộ quét ghi nhớ tập `failed_states` chứa các cặp `(state, cursor)` đã chứng minh không dẫn tới trạng thái kết thúc nào (Reps, 1998), đảm bảo mỗi cặp `(q, i)` chỉ thăm tối đa 1 lần → thời gian quét luôn chặt O(|Q|·n) = O(n).",
    )

    # =========================================================================
    # SECTION 3: MÔ HÌNH HÌNH THỨC / AUTOMATA ĐƯỢC SỬ DỤNG
    # =========================================================================
    add_heading_1(doc, "3. Mô hình hình thức / Automata được sử dụng")

    add_heading_2(doc, "3.1. Xác định Input, Output và Bảng chữ cái Hữu hạn Mở rộng UTF-8 (|Σ| = 99)")
    add_bullet(
        doc,
        "Đầu vào (Input): ",
        "(1) Danh sách có thứ tự các đặc tả token `Spec = [(T₁, R₁, p₁, skip₁), ..., (Tₖ, Rₖ, pₖ, skipₖ)]` với `p₁ < p₂ < ... < pₖ` là thứ tự ưu tiên; "
        "và (2) Chuỗi mã nguồn đầu vào `w` (hỗ trợ cả ASCII chuẩn, ký tự tiếng Việt UTF-8 và xuống dòng hỗn hợp `\\n`, `\\r\\n`, `\\r`).",
    )
    add_bullet(
        doc,
        "Đầu ra (Output): ",
        "Chuỗi 6 mô hình Automata (`Thompson ε-NFA`, `NFA không ε`, `Subset DFA`, `Moore Min-DFA`, `Hopcroft Min-DFA`, `Combined Direct DFA`), "
        "cảnh báo quy tắc bị che khuất (`shadowed_rules`), chứng minh tương đương Product Automaton, chứng minh tối giản Myhill–Nerode kèm chuỗi phân biệt `w`, "
        "luồng `Token` và danh sách `LexicalError` theo chế độ `panic_char` hoặc `smart_sync`.",
    )
    add_bullet(
        doc,
        "Bảng chữ cái hữu hạn mở rộng UTF-8 (|Σ| = 99 ký hiệu): ",
        "Thay vì bị giới hạn cứng ở ASCII hoặc làm nổ kích thước bảng chuyển với 1.114.112 mã Unicode, nhóm phân hoạch tập ký tự thành **98 ký tự ASCII** "
        "(95 ký tự in được mã `32..126` hợp với `{\\t, \\n, \\r}`) cộng thêm **1 ký hiệu đại diện lớp tương đương `NON_ASCII` (`\\x80`)** cho mọi ký tự `ord(c) ≥ 128`. "
        "Nhờ thiết kế này, dấu chấm `.` và các lớp phủ định như `[^\"\\\\\\n]` hoặc `[^\\n]` tự động bao gồm `NON_ASCII`, giúp chuỗi và bình luận chứa tiếng Việt "
        "(`\"Xin chào UEH\"`, `/* Tính tổng */`) được quét hợp lệ 100%, trong khi ký tự Unicode lạ nằm ngoài chuỗi như `let gia = 100€;` vẫn bị chặn đứng tại trạng thái `DEAD` và báo `LEXICAL_ERROR` kèm mã `U+20AC`!",
    )

    add_heading_2(doc, "3.2. Mô hình Combined Multi-token Automata & Phát hiện Luật Bị Che Khuất (Shadowed Rules)")
    add_callout(
        doc,
        "Mô hình Toán học Multi-token DFA, Khử ε, Tối thiểu hóa Hopcroft/Moore & Kiểm tra Luật Che khuất",
        [
            "1. Combined ε-NFA & NFA Khử ε (Định lý 2): N_lex = (Q_N, Σ, δ_N, q_start, F_N, τ_N) với δ_N(q_start, ε) = {s₁, ..., sₖ} và τ_N(fᵢ) = (Tᵢ, pᵢ, skipᵢ). "
            "Khi khử ε theo Định lý 2, mọi trạng thái p có ε-closure({p}) ∩ F_N ≠ ∅ nhận nhãn ưu tiên cao nhất τ'_{N}(p) = argmin_{f ∈ ε-closure({p}) ∩ F_N} priority(f).",
            "2. Multi-token Subset DFA & Combined Direct DFA: D_lex = (Q_D, Σ/≡, δ_D, D₀, F_D, τ_D) với nhãn chiến thắng τ_D(S) = argmin_{f ∈ S ∩ F_N} priority(f).",
            "3. Phân hoạch khởi đầu bảo toàn phân loại Token: Π₀ = { Q_D \\ F_D } ∪ { F_{T₁}, F_{T₂}, ..., F_{T_m} } (tách riêng từng loại token kết thúc).",
            "4. Điều kiện Phát hiện Luật Bị Che Khuất (Shadowed / Dead Token Rule): Sau khi thu được Minimized DFA D_min = (Q_min, Σ/≡, δ_min, q₀, F_min, τ_min), "
            "nếu tồn tại quy tắc (Tᵢ, Rᵢ, pᵢ) sao cho ∀q ∈ F_min: τ_min(q) ≠ Tᵢ (tức L(Rᵢ) ⊆ ⋃_{j < i} L(Rⱼ)), hệ thống tự động kết luận quy tắc Tᵢ bị che khuất hoàn toàn bởi quy tắc ưu tiên cao hơn.",
        ],
    )

    add_heading_2(doc, "3.3. Đặc tả tập Token minh họa (MiniLang 39 Token, CalcLang 12 Token & MiniSQL 14 Token)")
    add_body(
        doc,
        "Để chứng minh tính tổng quát của bộ sinh từ vựng, nhóm thiết kế 3 bộ đặc tả ngôn ngữ hoàn chỉnh: "
        "**MiniLang (39 token — bổ sung cả bình luận nhiều dòng `BLOCK_COMMENT`)**, **CalcLang (12 token)** và **MiniSQL (14 token)**. "
        "Bảng 1 tóm tắt các nhóm quy tắc từ vựng của MiniLang:",
    )

    minilang_summary_rows = [
        ["1", "COMMENT", r"//[^\n]*", "Bỏ qua", "Bình luận 1 dòng (hỗ trợ tiếng Việt UTF-8 qua NON_ASCII)"],
        ["2", "BLOCK_COMMENT", r"/\*([^*]|\*+[^*/])*\*+/", "Bỏ qua", "Bình luận nhiều dòng chuẩn C/Java (xử lý đúng `/**/`, `/***a***/`)"],
        ["3", "WHITESPACE", r"[ \t\n\r]+", "Bỏ qua", "Khoảng trắng, tab, xuống dòng Unix LF & Windows CRLF"],
        ["4–12", "KW_IF .. BOOL_LIT", r"if, else, while, for, let, func, return, print, true|false", "Giữ", "9 từ khóa & hằng logic (ưu tiên cao hơn IDENTIFIER)"],
        ["13", "FLOAT_LIT", r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", "Giữ", "Số thực dấu phẩy động & ký hiệu khoa học 1.5e-2, 1.5e+3"],
        ["14", "INT_LIT", r"[0-9]+", "Giữ", "Số nguyên không dấu"],
        ["15", "STRING_LIT", r'"([^"\\\n]|\\.)*"', "Giữ", "Chuỗi ngoặc kép hỗ trợ escape \\\", \\\\ và tiếng Việt UTF-8"],
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
        "Hình 1 trình bày kiến trúc tổng thể của hệ thống, kết nối chặt chẽ giữa nhánh biên dịch chuẩn 4 định lý "
        "(`RE → AST → Thompson ε-NFA → NFA Khử ε → Subset DFA → Moore & Hopcroft Min-DFA → Linear-Time Scanner`) "
        "với nhánh đối chứng trực tiếp (`Direct RE → DFA đơn lẻ & Đa-Token kết hợp`, `JFLAP Round-Trip XML`) "
        "và bộ chứng minh hình thức (`Product Automaton Equivalence` & `Myhill–Nerode Minimality Witness Verifier`).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig1_architecture_pipeline.png",
        "Hình 1: Kiến trúc tổng thể 6 phương pháp Automata và Bộ kiểm chứng tương đương / tối giản của Hệ thống (Đề tài T13).",
        width_cm=15.8,
    )

    add_heading_2(doc, "4.1. Thuật toán 1 — Phân tích cú pháp RE, Định lượng đếm {m,n} & Lớp NON_ASCII")
    add_body(
        doc,
        "Bộ phân tích cú pháp đệ quy xuống (`regex_parser.py`) cài đặt văn phạm 4 mức ưu tiên: "
        "`expr → concat ('|' concat)*`, `concat → repeat+`, `repeat → atom ('*'|'+'|'?'|'{m,n}')*`, "
        "`atom → '(' expr ')' | char_class | '.' | escape | 'ε' | literal`. "
        "Các điểm nâng cấp kỹ thuật then chốt gồm: (1) Mọi lớp ký tự (`[a-z]`, `[-a]`, `[a-]`, `[^^]`, `\\d`, `\\w`, `\\s`) được biên dịch thành một nút lá `CharSetNode(chars ⊆ Σ)` duy nhất; "
        "lớp phủ định `[^C]` tự động lấy phần bù trên toàn bộ `Σ = ASCII_SIGMA ∪ {NON_ASCII}` (có kiểm tra từ chối lớp phủ định rỗng phủ hết Σ); "
        "(2) Định lượng đếm `R{m}`, `R{m,}`, `R{m,n}` được khai triển trực tiếp sang cây AST thuần túy (`ConcatNode`, `OptionalNode`, `StarNode`) "
        "với ngưỡng bảo vệ `MAX_QUANTIFIER_BOUND = 64` chống bùng nổ tổ hợp; "
        "(3) Kiểm tra và bắt chính xác 20 mẫu lỗi cú pháp RE (`\"\"`, `()`, `(|a)`, `a||b`, `*a`, `[z-a]`, `a{5,2}`, `abc\\`) kèm vị trí cột lỗi.",
    )

    add_heading_2(doc, "4.2. Thuật toán 2 — Cấu trúc Thompson & Thuật toán Khử ε (Định lý 2 Chương 3.1)")
    add_body(
        doc,
        "Duyệt hậu tố trên AST, mỗi mảnh Thompson ε-NFA duy trì bất biến `in-deg(start) = 0` và `out-deg(end) = 0`, cho phép phép nối `ConcatNode(L, R)` "
        "gộp trực tiếp đỉnh cuối của L với đỉnh đầu của R. Trên biểu thức `(a|b)*abb`, thuật toán sinh chính xác **11 trạng thái (`q0..q10`)** khớp tuyệt đối Slide 38 Chương 3.1 (Hình 2). "
        "Để hoàn thiện chuỗi lý thuyết Chương 3.1, hàm `eliminate_epsilon(nfa)` trong `thompson.py` cài đặt **Định lý 2 (Slide 21–22)**: "
        "tính `closures[s] = ε-closure({s})`, gán nhãn kết thúc `τ(s) = argmin_{q ∈ closures[s] ∩ F_N} priority(q)` và dựng cung trực tiếp "
        "`δ_no_eps(s, c) = ε-closure(Move(closures[s], c))`, giúp rút gọn `(a|b)*abb` từ 11 trạng thái ε-NFA xuống 6 trạng thái NFA không ε (và rút gọn `MiniLang` từ 170 xuống 96 trạng thái).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig2_slide38_pipeline.png",
        "Hình 2: Kết quả thực thi đường ống RE → Thompson ε-NFA (11 trạng thái) → Subset DFA (5 trạng thái) → Minimized DFA (4 trạng thái) trên (a|b)*abb.",
        width_cm=15.6,
    )

    add_heading_2(doc, "4.3. Thuật toán 3 — Subset Construction kết hợp Alphabet Partitioning & Phát hiện Luật Che khuất")
    add_body(
        doc,
        "Nhóm cài đặt kỹ thuật phân hoạch bảng chữ cái (Alphabet Partitioning / Min-terms): từ tất cả tập ký tự trên các cung của Combined ε-NFA, "
        "tinh chỉnh thành `p ≤ 99` lớp tương đương rời nhau `E₁, ..., E_p` sao cho `∀c₁, c₂ ∈ Eⱼ: Move(S, c₁) = Move(S, c₂)` với mọi `S ⊆ Q_N`. "
        "Nhờ đó `MiniLang` nén từ 99 ký hiệu xuống **43 lớp tương đương**, giúp Subset Construction chạy trong ~4 ms. "
        "Khi một tập trạng thái `S` chứa nhiều trạng thái kết thúc NFA (ví dụ `KW_IF` ưu tiên 4 và `IDENTIFIER` ưu tiên 16 cùng khớp `'if'`), "
        "hàm `_resolve_accept(S)` chọn quy tắc có `priority` nhỏ nhất và ghi nhận vào bảng xung đột. "
        "Đồng thời, sau khi biên dịch xong DFA tối giản, hệ thống đối chiếu tập quy tắc đầu vào với tập nhãn chiến thắng `{τ(q) | q ∈ F_min}`: "
        "nếu người dùng đặt `IDENTIFIER` lên trước `KW_IF`, hệ thống lập tức phát cảnh báo **Shadowed Rule**: "
        "\"Quy tắc `KW_IF` bị che khuất hoàn toàn bởi quy tắc ưu tiên cao hơn (`IDENTIFIER`) và sẽ không bao giờ được khớp!\".",
    )

    add_heading_2(doc, "4.4. Thuật toán 4 — Direct RE → DFA Đơn lẻ (Slide 54) & Đa-Token Kết hợp")
    add_body(
        doc,
        "Trong `direct_dfa.py`, bên cạnh hàm `build_direct_dfa(pattern)` cho biểu thức đơn `r·#` — sinh chính xác **8 vị trí lá**, bảng `followpos` và **5 trạng thái Direct DFA `A..E`** "
        "cho `(a|ba)(a|b)*ba#` trùng khớp từng con số với Slide 54–57 Chương 3.1 (Hình 3) — nhóm đã mở rộng thêm hàm `build_combined_direct_dfa(specs)`: "
        "ghép trực tiếp `k` quy tắc thành cây cú pháp tổng hợp `(R₁·#₁) | (R₂·#₂) | ... | (Rₖ·#ₖ)` với `#ᵢ` mang thông tin `(Tᵢ, pᵢ, skipᵢ)`. "
        "Mọi trạng thái `S` chứa các vị trí kết thúc `#ᵢ` được gán nhãn theo `argmin_{#ᵢ ∈ S} pᵢ`. Thực nghiệm cho thấy Combined Direct DFA của `MiniLang` chỉ có **79 trạng thái** "
        "(so với 86 trạng thái của Subset DFA) và được Product Automaton chứng minh tương đương 100% với Minimized DFA (78 trạng thái)!",
    )
    add_figure(
        doc,
        FIG_DIR / "fig5_direct_dfa_slide46.png",
        "Hình 3: Direct DFA xây dựng trực tiếp từ r = (a|ba)(a|b)*ba# qua bảng followpos — khớp 100% Slide 54–57 Chương 3.1.",
        width_cm=13.8,
    )

    add_heading_2(doc, "4.5. Thuật toán 5 — Tối thiểu hóa Song song Moore & Hopcroft + Chứng minh Myhill–Nerode")
    add_body(
        doc,
        "Module `dfa_minimizer.py` cài đặt song song cả hai thuật toán tối thiểu hóa kinh điển trên cùng phân hoạch khởi đầu đa-token "
        "`Π₀ = {Q \\ F ∪ {DEAD}} ∪ {F_{T₁}, ..., F_{T_m}}`: "
        "(1) **Thuật toán Moore Partition Refinement (`O(|Σ|·|Q|²)`)** lặp tách khối theo vector chữ ký chuyển tiếp và xuất trọn vẹn vết phân hoạch `Π₀ → Π₁ → ... → Πₖ` để phục vụ giảng dạy; "
        "(2) **Thuật toán Hopcroft (`O(|Σ|·|Q|log|Q|)`)** xây dựng đồ thị chuyển tiếp ngược `δ⁻¹(A, Eⱼ)` và hàng đợi phân tách `W`, khi một khối `Y` bị tập tiền ảnh `X` cắt đôi thành `Y₁, Y₂` "
        "sẽ luôn đẩy khối nhỏ hơn (`min(|Y₁|, |Y₂|)`) vào `W`. "
        "Sau đó, module `verifier.py` thực hiện hai bước chứng minh toán học độc lập: "
        "(i) Dùng **Product Automaton BFS** chứng minh `Moore Min-DFA ≡ Hopcroft Min-DFA ≡ Subset DFA ≡ Combined Direct DFA` (0 phản ví dụ); "
        "(ii) Dùng hàm **`verify_dfa_is_minimal(dfa)`** kiểm chứng **Định lý Myhill–Nerode**: tìm chuỗi phân biệt ngắn nhất `w` cho toàn bộ `C(|Q_min|, 2)` cặp trạng thái "
        "(`3.003/3.003` cặp trên `MiniLang`, `190/190` cặp trên `CalcLang`, `1.326/1.326` cặp trên `MiniSQL`), chứng minh không còn bất kỳ cặp trạng thái nào có thể gộp thêm!",
    )

    add_heading_2(doc, "4.6. Thuật toán 6 — Bộ quét Maximal Munch Tuyến tính O(n) (Reps, 1998) & Phục hồi lỗi kép")
    add_callout(
        doc,
        "Mã giả Thuật toán Quét Từ Vựng Maximal Munch Tuyến tính O(n) với Bảng nhớ failed_states & Phục hồi lỗi kép",
        [
            "Input : Chuỗi mã nguồn text[0..n-1], Minimized Multi-token DFA D = (Q, Σ/≡, δ, D₀, F, τ), mode ∈ {panic_char, smart_sync}",
            "Output: Danh sách Token, Danh sách LexicalError, Vết thực thi Trace, Số lần cắt nhánh memoized_cutoffs",
            "1. pos ← 0; line ← 1; col ← 1; failed_states ← ∅   // Bảng nhớ (state, cursor) theo Reps (1998)",
            "2. WHILE pos < n DO:",
            "3.   cur ← D₀; cursor ← pos; last_accept ← NULL; visited_path ← []",
            "4.   WHILE cursor < n DO:",
            "5.     IF (cur, cursor) ∈ failed_states THEN: memoized_cutoffs += 1; BREAK   // Cắt nhánh O(1) chống O(n²)",
            "6.     nxt ← δ(cur, class_of(text[cursor]))                                   // NON_ASCII nếu ord(c) ≥ 128",
            "7.     IF nxt == NULL THEN BREAK",
            "8.     cur ← nxt; cursor ← cursor + 1; visited_path.append((cur, cursor))",
            "9.     IF cur ∈ F THEN last_accept ← (cursor, cur, τ(cur))",
            "10.  FOR (st, idx) IN visited_path WHERE idx > (last_accept.pos IF last_accept ELSE pos):",
            "11.    failed_states.add((st, idx))                                            // Ghi nhớ cấu hình thất bại",
            "12.  IF last_accept ≠ NULL AND last_accept.pos > pos THEN:",
            "13.    Emit Token(last_accept.type, text[pos:last_accept.pos], line, col); Advance pos ← last_accept.pos",
            "14.  ELSE:",
            "15.    IF mode == smart_sync AND text[pos] starts unclosed '\"...' or '/*...':",
            "16.      Consume entire unclosed string (to '\\n'/EOF) or unclosed block comment (to EOF) as 1 LexicalError",
            "17.    ELSE: Emit LexicalError(text[pos], line, col); Advance pos ← pos + 1   // Panic-mode chuẩn tiến 1 ký tự",
        ],
        fill="F8FAFC",
        accent="1E3A8A",
        mono=True,
    )

    add_heading_2(doc, "4.7. Phân tích độ phức tạp và các trường hợp biên đã xử lý triệt để")
    comp_rows = [
        ["Regex Parser + {m,n} + Thompson", "O(|R|)", "O(|R|)", "Hỗ trợ {m,n} (n≤64), [-a], [a-], [^^], \\f, \\v, NON_ASCII; bắt 20 mẫu lỗi RE"],
        ["Khử ε (Định lý 2 Chương 3.1)", "O(|Q_N|² + |Q_N|·|Σ|)", "O(|Q_N|·|Σ|)", "Loại bỏ hoàn toàn ε-chuyển tiếp, bảo toàn nhãn ưu tiên token cao nhất"],
        ["Alphabet Partitioning + Subset DFA", "Thực tế O(|Q_D|·p)", "O(|Q_D|·p)", "Nén 99 ký hiệu Σ thành p ≤ 99 lớp (MiniLang: 43 lớp); phát hiện Shadowed Rules"],
        ["Moore & Hopcroft Minimization", "Moore: O(p·|Q|²)\nHopcroft: O(p·|Q|log|Q|)", "O(p·|Q|)", "Bảo toàn phân loại đa-token Π₀; chứng minh Moore ≡ Hopcroft trên cả 3 ngôn ngữ"],
        ["Product Eq & Myhill–Nerode Verify", "O(|Q_A|·|Q_B|·p)", "O(|Q|²)", "Tìm chuỗi phân biệt ngắn nhất w cho 100% cặp trạng thái (MiniLang: 3003/3003 cặp)"],
        ["Linear-Time Maximal Munch Scanner", "Tuyến tính chặt O(n)\n(với failed_states)", "O(n)", "Chống quay lui O(n²) trên chuỗi lỗi 10.000 ký tự (<25 ms); hỗ trợ panic_char & smart_sync"],
    ]
    add_styled_table(
        doc,
        ["Thành phần thuật toán", "Độ phức tạp thời gian", "Bộ nhớ", "Xử lý trường hợp biên & Đóng góp kỹ thuật"],
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
        "(1) Tầng lõi thuật toán `lexer_engine/` (100% Python Standard Library, không phụ thuộc bất kỳ gói bên ngoài nào và **Zero `import re`**); "
        "(2) Tầng giao diện người dùng gồm ứng dụng Web `LexAutomata Studio` 5 Tab (`app.py` + `web/`) và công cụ dòng lệnh (`cli.py`), kèm cấu hình Cloud 1-Click (`.devcontainer/devcontainer.json`, `render.yaml`); "
        "(3) Tầng kiểm thử tự động & kiểm chứng khứ hồi (`tests/test_cases.json` với 62 test cases, `tests/test_suite.py` với 16 bộ unittest, `jflap_export.py` hỗ trợ cả xuất và đọc ngược XML `.jff`). "
        "Bảng 2 làm rõ ranh giới giữa phần nhóm tự cài đặt và thư viện chuẩn:",
    )

    lib_rows = [
        [
            "models.py, regex_parser.py, thompson.py, subset_construction.py, direct_dfa.py, dfa_minimizer.py, scanner.py, verifier.py, jflap_export.py",
            "100% nhóm tự cài đặt từ con số 0 (Zero `import re`)",
            "Chỉ dùng Python Standard Library: `dataclasses`, `collections.deque`, `xml.etree.ElementTree`, `time`",
        ],
        [
            "app.py, cli.py, web/ (HTML5/CSS3/JS + Đồ thị SVG tương tác + Bảng Myhill–Nerode + So sánh 2 RE + Benchmark Dashboard)",
            "100% nhóm tự thiết kế & lập trình",
            "Python stdlib `http.server`, `argparse`, `json`; trình duyệt chuẩn HTML5/SVG (không cần Node.js/React/pip)",
        ],
        [
            "tests/test_suite.py (62 test cases JSON + 16 unittest kiểm chứng 5 bất biến toán học & Fuzzing)",
            "Nhóm tự thiết kế kịch bản & bộ sinh chuỗi Fuzz",
            "Python `unittest`, `ast` (kiểm tra tự động không có `import re` trong lõi), đối chứng 6 chiều",
        ],
        [
            "scripts/ (tự động vẽ đồ thị báo cáo & xuất DOCX/PDF/PPTX ngoài runtime)",
            "Nhóm viết script tự động hóa",
            "matplotlib, python-docx, python-pptx, chromium headless (không cần khi chạy ứng dụng demo)",
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
        "Tab 1 — Bộ Quét Từ Vựng, Công tắc Phục hồi lỗi (Panic-mode / Smart-Sync) & Hoạt ảnh Từng bước: ",
        "Soạn thảo mã nguồn với các kịch bản mẫu (`Hợp lệ`, `Biên Maximal Munch`, `Lỗi & Phục hồi`), chuyển đổi tức thời giữa hai chế độ phục hồi lỗi "
        "`panic_char` và `smart_sync` (hiển thị cả chỉ số cắt nhánh `memoized_cutoffs` của Reps 1998), tô màu token trực tiếp và chạy hoạt ảnh DFA Step-by-Step.",
    )
    add_bullet(
        doc,
        "Tab 2 — 6 Phương pháp Automata Tổng Hợp, Đối sánh Moore vs. Hopcroft & Chứng minh Myhill–Nerode: ",
        "Trực quan hóa đồ thị SVG có kéo-thả/zoom cho cả 6 mô hình (`Moore Min-DFA`, `Hopcroft Min-DFA`, `Subset DFA`, `Combined Direct DFA`, `NFA Khử ε`, `Thompson ε-NFA`); "
        "hiển thị bảng chuỗi phân biệt Myhill–Nerode `w` cho các cặp trạng thái, cảnh báo `Shadowed Rules` và xuất/đọc file `.jff` chuẩn JFLAP.",
    )
    add_bullet(
        doc,
        "Tab 3 & Tab 4 — Thí Nghiệm RE Đơn Lẻ, Kiểm tra Tương đương 2 RE (R₁ ≡ R₂?) & Live Spec Editor: ",
        "Tại Tab 3, ngoài việc đối chứng Thompson → Khử ε → Subset → Moore/Hopcroft với cây `r·#` (`nullable`, `firstpos`, `lastpos`, `followpos`), "
        "người dùng có thể nhập hai biểu thức `R₁` và `R₂` bất kỳ (ví dụ `(a|b)*` và `(a*b*)*`) để máy chứng minh tương đương hoặc chỉ ra chuỗi phản ví dụ ngắn nhất. "
        "Tại Tab 4, nếu người dùng thử đẩy `IDENTIFIER` lên trên `KW_IF`, hệ thống lập tức bật biểu ngữ cảnh báo đỏ phát hiện quy tắc bị che khuất!",
    )
    add_bullet(
        doc,
        "Tab 5 — Phòng Thí Nghiệm Kiểm Thử Tự Động (62/62 PASS) & Benchmark Chống Quay Lui Bậc Hai O(n²): ",
        "Chạy trực tiếp 62 ca kiểm thử JSON, bảng đối sánh 6 phương pháp trên 3 ngôn ngữ và biểu đồ Stress Test 10.000 ký tự lỗi (`\"aaaa...`, `/*xxxx...`, `\"\\\"\\\"...`).",
    )

    add_body(
        doc,
        "Hình 4 minh họa đồ thị Minimized Combined DFA hoàn chỉnh của bộ ngôn ngữ `CalcLang` (12 token nén xuống đúng 20 trạng thái tối giản, toàn bộ 190/190 cặp trạng thái đều phân biệt đôi một theo Myhill–Nerode). "
        "Hình 5 và Hình 6 chụp trực tiếp giao diện Web `LexAutomata Studio` đang vận hành thực tế tại Tab 1 và Tab 3.",
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
        "Hình 5: Giao diện Web LexAutomata Studio — Tab 1 minh họa bộ quét đa-token với công tắc Panic-mode / Smart-Sync và vết đường đi DFA.",
        width_cm=14.4,
    )
    add_figure(
        doc,
        FIG_DIR / "fig7_web_direct_re_lab.png",
        "Hình 6: Giao diện Web LexAutomata Studio — Tab 3 minh họa cây phân tích gia tố r·#, bảng followpos (Slide 54) và công cụ kiểm chứng R₁ ≡ R₂.",
        width_cm=14.4,
    )

    # =========================================================================
    # SECTION 6: TEST CASE, KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH
    # =========================================================================
    add_heading_1(doc, "6. Test case, kết quả thực nghiệm và phân tích")

    add_heading_2(doc, "6.1. Thiết kế bộ 62 Test Cases JSON & 16 Unittest Bất biến Toán học")
    add_body(
        doc,
        f"Nhóm đã mở rộng bộ kiểm thử có cấu trúc trong `tests/test_cases.json` lên **{test_rep['total']} kịch bản chuẩn** "
        f"(gồm 16 ca RE đơn & biên, 20 ca bẫy lỗi cú pháp RE và 26 ca quét từ vựng đa ngôn ngữ) kết hợp với **16 bộ Unittest** trong `tests/test_suite.py`. "
        f"Kết quả thực thi đạt **{test_rep['passed']}/{test_rep['total']} PASS ({test_rep['pass_rate']}%)** trên JSON và **16/16 OK (100%)** trên Unittest. "
        f"Bảng 3 tổng hợp các nhóm kiểm thử đại diện và 5 bất biến toán học được kiểm chứng tự động:",
    )

    tc_rows = [
        ["RE-01..02", "Bài giảng UEH", "(a|b)*abb & (a|ba)(a|b)*ba", "Khớp 100% Slide 38 (11→6→5→4 trạng thái) và Slide 54 (8 lá, followpos, 5 trạng thái A..E)", "PASS"],
        ["RE-03..16", "Biên RE & {m,n}", "[-a], [a-], [^^], [0-9]{2,4}, (a*)*, (a|ε)b*", "Khai triển chuẩn định lượng {m,n}, lớp ký tự biên & biểu thức nullable; 6 Otomat khớp 100%", "PASS"],
        ["RE-ERR-01..20", "20 Bẫy lỗi RE", "'', '()', '(|a)', 'a||b', '*a', '[z-a]', 'a{5,2}', 'a{100}'", "Bắt chính xác RegexSyntaxError kèm vị trí cột lỗi trên cả 20/20 mẫu biểu thức sai", "PASS"],
        ["SCAN-01..07", "Maximal Munch", "ifx, a===b!==c, 1.5e-2, 1.5e, 3., 0.0.0", "Khớp dài nhất & ưu tiên luật chuẩn xác; quay lui đúng 1 ký tự tại 1.5e và 3.", "PASS"],
        ["SCAN-08..14", "Lỗi & UTF-8", 'let gia = 100€; "Xin chào UEH"; "abc\\nlet x=1;', "Khớp chuỗi tiếng Việt UTF-8; bắt lỗi U+20AC ngoài chuỗi; đối sánh panic_char vs smart_sync", "PASS"],
        ["SCAN-15..26", "Block Comment & CRLF", "`/**/`, `/***a*b***/`, `/*dòng 1\\r\\ndòng 2*/`, `/*chưa đóng`", "Khớp chuẩn bình luận nhiều dòng `/*...*/`; tính đúng (line, col) với `\\n`, `\\r\\n`, `\\r`", "PASS"],
        ["INV-1 & INV-2", "Bất biến Toán học", "120+ chuỗi Fuzz Zero-Loss & 270+ chuỗi 6-Way Eq", "Ghép mọi lexeme (token + skip + lỗi) tái tạo 100% mã nguồn; 6 Otomat tương đương tuyệt đối", "PASS"],
        ["INV-3..5", "Myhill–Nerode & O(n)", "4.519 cặp trạng thái + 30.000 ký tự lỗi + JFLAP .jff", "100% cặp trạng thái có chuỗi phân biệt w; quét 10.000 ký tự lỗi < 25 ms; JFLAP khứ hồi 100%", "PASS"],
    ]
    add_styled_table(
        doc,
        ["Mã Kiểm thử", "Phân loại", "Đầu vào / Kịch bản đại diện", "Kết quả thực nghiệm & Bất biến kiểm chứng", "Đánh giá"],
        tc_rows,
        col_widths_cm=[2.3, 2.2, 4.1, 6.6, 1.5],
        font_size=8.3,
        mono_cols={0},
    )

    add_heading_2(doc, "6.2. Thực nghiệm đối sánh 6 phương pháp Automata, Myhill–Nerode & Stress Test O(n)")
    add_body(
        doc,
        "Bảng 4 và Hình 7 tổng hợp số liệu thực nghiệm trên cả 3 bộ ngôn ngữ qua toàn bộ 6 phương pháp Automata cùng kết quả chứng minh tối giản Myhill–Nerode:",
    )

    dir_mini = len(build_combined_direct_dfa(PRESETS["minilang"]["specs"]).states)
    dir_calc = len(build_combined_direct_dfa(PRESETS["calclang"]["specs"]).states)
    dir_sql = len(build_combined_direct_dfa(PRESETS["minisql"]["specs"]).states)

    bench_rows = [
        [
            "MiniLang",
            str(s_mini["token_count"]),
            str(s_mini["nfa_states"]),
            str(s_mini["eps_free_nfa_states"]),
            str(s_mini["subset_dfa_states"]),
            str(dir_mini),
            f"{s_mini['minimized_dfa_states']} / {s_mini['hopcroft_dfa_states']}",
            f"-{s_mini['state_reduction_count']} (-{s_mini['state_reduction_percent']}%)",
            f"{s_mini['minimality']['distinguishable_pairs']}/{s_mini['minimality']['total_pairs']}",
            "✓ 6-Way Eq",
        ],
        [
            "CalcLang",
            str(s_calc["token_count"]),
            str(s_calc["nfa_states"]),
            str(s_calc["eps_free_nfa_states"]),
            str(s_calc["subset_dfa_states"]),
            str(dir_calc),
            f"{s_calc['minimized_dfa_states']} / {s_calc['hopcroft_dfa_states']}",
            f"-{s_calc['state_reduction_count']} (-{s_calc['state_reduction_percent']}%)",
            f"{s_calc['minimality']['distinguishable_pairs']}/{s_calc['minimality']['total_pairs']}",
            "✓ 6-Way Eq",
        ],
        [
            "MiniSQL",
            str(s_sql["token_count"]),
            str(s_sql["nfa_states"]),
            str(s_sql["eps_free_nfa_states"]),
            str(s_sql["subset_dfa_states"]),
            str(dir_sql),
            f"{s_sql['minimized_dfa_states']} / {s_sql['hopcroft_dfa_states']}",
            f"-{s_sql['state_reduction_count']} (-{s_sql['state_reduction_percent']}%)",
            f"{s_sql['minimality']['distinguishable_pairs']}/{s_sql['minimality']['total_pairs']}",
            "✓ 6-Way Eq",
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
            "Giảm TT",
            "Myhill–Nerode",
            "Kiểm chứng",
        ],
        bench_rows,
        col_widths_cm=[1.8, 1.0, 1.2, 1.2, 1.4, 1.4, 1.7, 1.9, 2.2, 1.9],
        font_size=8.2,
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
        "Sự hội tụ tuyệt đối giữa Moore, Hopcroft và Combined Direct DFA: ",
        "Trên cả 3 ngôn ngữ, thuật toán Moore và thuật toán Hopcroft đều hội tụ về đúng cùng một số trạng thái tối giản (`MiniLang: 78`, `CalcLang: 20`, `MiniSQL: 52`) "
        "và được `verify_dfa_is_minimal()` chứng minh 100% cặp trạng thái phân biệt đôi một (`3.003/3.003`, `190/190`, `1.326/1.326`). "
        "Đáng chú ý, nhánh `Combined Direct DFA` sinh trực tiếp ra DFA tối giản cho `CalcLang` (20) và `MiniSQL` (52), và chỉ dư đúng 1 trạng thái trên `MiniLang` (79 vs. 78) do nhánh `BLOCK_COMMENT`.",
    )
    add_bullet(
        doc,
        "Hiệu quả chống quay lui bậc hai O(n²) của bảng nhớ Reps (1998) & Chế độ Smart-Sync: ",
        "Khi thử nghiệm quét chuỗi bệnh lý dài 10.000 ký tự chứa 5.000 cặp dấu ngoặc kép thoát nhưng không đóng (`\"` + `\\\"` * 5000), "
        "nếu không có bảng nhớ `failed_states`, bộ quét cổ điển phải duyệt lại hậu tố tới 5.000 lần (tốn hàng chục triệu bước O(n²)). "
        "Nhờ kỹ thuật Memoization của Reps (1998), hệ thống kích hoạt đúng **5.000 lần cắt nhánh O(1)** (`memoized_cutoffs = 5000`) và hoàn tất quét trong **~24 ms** (chế độ `panic_char`) hoặc **~4.3 ms** (chế độ `smart_sync` gom thành 1 lỗi duy nhất)!",
    )

    # =========================================================================
    # SECTION 7: HẠN CHẾ LÝ THUYẾT, CÁC VẤN ĐỀ ĐÃ GIẢI QUYẾT & HƯỚNG PHÁT TRIỂN
    # =========================================================================
    add_heading_1(doc, "7. Phân tích giới hạn lý thuyết và hướng phát triển")

    add_heading_2(doc, "7.1. Các thách thức kỹ thuật đã được giải quyết triệt để & Giới hạn lý thuyết của DFA")
    add_bullet(
        doc,
        "Các lỗ hổng thường gặp của bộ phân tích từ vựng cơ bản đã được xử lý trọn vẹn trong đồ án: ",
        "(1) Hiện tượng quay lui bậc hai O(n²) trên chuỗi chưa đóng dài đã được triệt tiêu bằng bảng nhớ `failed_states` (Reps, 1998); "
        "(2) Vấn đề chuỗi/bình luận chưa đóng sinh nhiều token rác đã được giải quyết bằng chế độ `smart_sync` đối sánh trực tiếp với `panic_char`; "
        "(3) Hạn chế bảng chữ cái ASCII đã được khắc phục bằng lớp tương đương `NON_ASCII` (`0x80`) hỗ trợ hoàn chỉnh tiếng Việt UTF-8 trong chuỗi và bình luận mà vẫn giữ DFA hữu hạn 99 ký hiệu; "
        "(4) Rủi ro người dùng đặt sai thứ tự quy tắc đã được tự động bắt bằng cơ chế phát hiện **Shadowed Token Rules**.",
    )
    add_bullet(
        doc,
        "Giới hạn lý thuyết bất khả kháng của Automata hữu hạn (Chứng minh bằng Bổ đề Bơm — Pumping Lemma Chương 3.2): ",
        "Mặc dù hệ thống đã hỗ trợ hoàn chỉnh bình luận nhiều dòng chuẩn C/Java `/* ... */` bằng biểu thức chính quy `/\\*([^*]|\\*+[^*/])*\\*+/`, "
        "một DFA đơn lẻ **không thể** nhận diện bình luận nhiều dòng **lồng nhau sâu tùy ý** (`/* ... /* ... */ ... */`, như trong Rust/Swift). "
        "Lý do toán học: nếu thay `/*` bằng `a` và `*/` bằng `b`, ngôn ngữ các bình luận lồng nhau cân bằng đẳng cấu với ngôn ngữ `L = { a^n b^n | n ≥ 1 }`. "
        "Theo **Bổ đề Bơm cho ngôn ngữ chính quy (Chương 3.2)**, với mọi hằng số bơm `p = |Q|`, chọn chuỗi `w = a^p b^p ∈ L`, mọi cách tách `w = xyz` với `|xy| ≤ p` và `|y| ≥ 1` "
        "đều có `y = a^k (k ≥ 1)`, dẫn tới `xy²z = a^{p+k} b^p ∉ L` (mâu thuẫn!). Tương tự, cấu trúc thụt lề phụ thuộc ngữ cảnh (`INDENT`/`DEDENT` của Python) đòi hỏi một ngăn xếp (Stack) lưu lịch sử cột.",
    )

    add_heading_2(doc, "7.2. Hướng phát triển tiếp theo")
    add_bullet(
        doc,
        "Tích hợp Ngăn xếp Ngữ cảnh Từ vựng (Lexical Start Conditions & Counter Automaton): ",
        "Bổ sung chồng trạng thái ngữ cảnh (`push_state(IN_NESTED_COMMENT)`, `pop_state()`) kết hợp bộ đếm độ sâu lồng nhau để hỗ trợ cả bình luận lồng nhau và nội suy chuỗi (`\"Hello ${name}\"`).",
    )
    add_bullet(
        doc,
        "Kết nối trực tiếp với Bộ phân tích cú pháp Văn phạm phi ngữ cảnh (Chương 4 — CFG & PDA): ",
        "Sử dụng luồng `Token` đầu ra của `LexicalAnalyzer` làm đầu vào trực tiếp cho bộ phân tích cú pháp `LL(1)` / `LR(1)` (Pushdown Automata — PDA), "
        "khép kín trọn vẹn kiến thức từ Chương 1–3 (FA/RE) sang Chương 4–5 (CFG/PDA) của học phần Ngôn ngữ hình thức.",
    )

    # =========================================================================
    # SECTION 8: KẾT LUẬN
    # =========================================================================
    add_heading_1(doc, "8. Kết luận")
    add_body(
        doc,
        "Đồ án đã hoàn thành toàn diện và vượt xa yêu cầu của Đề tài T13 — Automata-based Lexical Analyzer. "
        "Từ nền tảng lý thuyết Automata hữu hạn và Biểu thức chính quy của học phần Ngôn ngữ hình thức (UEH), nhóm đã tự thiết kế và cài đặt "
        "100% chuỗi 6 phương pháp Automata từ con số 0 (Zero `import re` trong lõi): phân tích cú pháp RE hỗ trợ `{m,n}` và `NON_ASCII` UTF-8, "
        "cấu trúc Thompson đa-token, thuật toán Khử ε (Định lý 2 Chương 3.1), Subset Construction kết hợp Alphabet Partitioning và phát hiện luật che khuất, "
        "nhánh đối chứng Direct RE → DFA đơn lẻ và Đa-Token kết hợp (`r·#`, `followpos`), tối thiểu hóa song song bằng cả hai thuật toán Moore và Hopcroft `O(|E|·|Q|log|Q|)`, "
        "chứng minh tương đương 6 chiều bằng Product Automaton, chứng minh tính tối giản tuyệt đối bằng Định lý Myhill–Nerode, kiểm chứng khứ hồi JFLAP `.jff`, "
        "và bộ quét từ vựng Maximal Munch tuyến tính chặt `O(n)` (Reps, 1998) hỗ trợ hai chế độ phục hồi lỗi (`panic_char` và `smart_sync`). "
        "Toàn bộ hệ thống được kiểm chứng nghiêm ngặt qua **62/62 kịch bản kiểm thử JSON (100% PASS)** và **16/16 bộ Unittest bất biến toán học**, "
        "cùng ứng dụng Web tương tác `LexAutomata Studio` 5 Tab sẵn sàng phục vụ giảng dạy và thực hành.",
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
            "Quản lý tiến độ; hệ thống hóa cơ sở lý thuyết Chương 1–3 & chứng minh Myhill–Nerode / Bổ đề Bơm; biên soạn báo cáo kỹ thuật & slide; phụ trách Lý thuyết khi bảo vệ.",
            "25%",
        ],
        [
            "2",
            "[Họ tên TV 2]",
            "[MSSV 2]",
            "Cài đặt `models.py` (`NON_ASCII` UTF-8), `regex_parser.py` (`{m,n}`), `thompson.py` (Thompson & Định lý 2 Khử ε), `direct_dfa.py` (Đơn lẻ & Đa-Token kết hợp); demo Tab 3.",
            "25%",
        ],
        [
            "3",
            "[Họ tên TV 3]",
            "[MSSV 3]",
            "Cài đặt `subset_construction.py` (Alphabet Partitioning & Shadowed Rules), `dfa_minimizer.py` (Moore & Hopcroft), `verifier.py` (Product Automaton & Myhill–Nerode), `jflap_export.py` (Round-Trip); demo Tab 2.",
            "25%",
        ],
        [
            "4",
            "[Họ tên TV 4]",
            "[MSSV 4]",
            "Cài đặt `scanner.py` (Maximal Munch O(n) Reps 1998, `panic_char` & `smart_sync`), `app.py`, `cli.py`, giao diện Web Studio 5 Tab (`web/`) & bộ 62 test cases + 16 unittest (`tests/`); demo Tab 1, 4, 5.",
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
            "• Tham khảo, rà soát thuật ngữ lý thuyết Automata và cấu trúc thuật toán (Định lý 2 Khử ε, Alphabet Partitioning, Multi-token Moore & Hopcroft Minimization, Myhill–Nerode Witness, Reps 1998 Linear-Time Maximal Munch).\n"
            "• Gợi ý kiến trúc phân tách module, hỗ trợ kiểm tra các trường hợp biên (lớp ký tự `[-a]`, `[a-]`, `[^^]`, định lượng `{m,n}`, `NON_ASCII` UTF-8, phát hiện luật bị che khuất Shadowed Rules).\n"
            "• Hỗ trợ xây dựng giao diện trực quan hóa SVG Web Studio 5 Tab, bộ 62 test cases JSON + 16 unittest bất biến toán học và chuẩn hóa trình bày báo cáo/slide.",
        ],
        [
            "Phạm vi kiểm chứng & Trách nhiệm của nhóm",
            "• Toàn bộ thành viên nhóm đã đọc hiểu, kiểm tra từng dòng thuật toán cốt lõi trong `lexer_engine/`, tự kiểm chứng đối chiếu với ví dụ bài giảng Chương 3.1 "
            "(Slide 21–22, Slide 38 và Slide 46–57), chạy 100% bộ kiểm thử tự động (62/62 JSON PASS + 16/16 Unittest OK) và đối chứng khứ hồi trên JFLAP.\n"
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
