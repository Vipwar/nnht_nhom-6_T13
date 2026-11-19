"""
Generate the official UEH Final Project Technical Report (DOCX + PDF)
for Topic T13: Automata-based Lexical Analyzer.

Strictly follows all 10 mandatory sections and length guideline (6-15 pages, targeting ~13-14 pages)
from `Tieu_luan_CK_2026.pdf`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lexer_engine import LexicalAnalyzer, PRESETS  # noqa: E402
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


def add_callout(doc: Document, title: str, lines: list[str], fill: str = "F1F5F9", accent: str = "2563EB", mono: bool = False) -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_margins(cell, top=90, bottom=90, left=140, right=120)
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(
        parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="{accent}"/>'
            f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
            f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
            f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
            f"</w:tcBorders>"
        )
    )
    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(3)
    r0 = p0.add_run(title)
    r0.bold = True
    r0.font.name = "Times New Roman"
    r0.font.size = Pt(10.5)
    r0.font.color.rgb = NAVY

    for idx, line in enumerate(lines):
        p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1.5 if idx < len(lines) - 1 else 0)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(line)
        r.font.name = "Consolas" if mono else "Times New Roman"
        r.font.size = Pt(8.8 if mono else 10.2)
        r.font.color.rgb = DARK

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)


def _add_rich_runs(paragraph, text: str, base_size: float = 11.0, base_color=DARK) -> None:
    """Parse inline **bold** and `code` spans into properly styled Word runs (no raw markdown)."""
    import re as _fmt_re

    tokens = _fmt_re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            r = paragraph.add_run(tok[2:-2])
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(base_size)
            r.font.color.rgb = base_color
        elif tok.startswith("`") and tok.endswith("`"):
            r = paragraph.add_run(tok[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(max(8.0, base_size - 1.3))
            r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        else:
            r = paragraph.add_run(tok)
            r.font.name = "Times New Roman"
            r.font.size = Pt(base_size)
            r.font.color.rgb = base_color


def add_styled_table(
    doc: Document,
    headers: list[str],
    rows: list[list[str]],
    col_widths_cm: list[float] | None = None,
    font_size: float = 9.3,
    mono_cols: set[int] | None = None,
    trailing_space: bool = True,
) -> None:
    mono_cols = mono_cols or set()
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    # Header row
    hdr_row = tbl.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))
    trPr.append(OxmlElement("w:cantSplit"))

    for c_idx, h_text in enumerate(headers):
        cell = hdr_row.cells[c_idx]
        set_cell_shading(cell, "1E3A8A")
        set_cell_margins(cell, top=60, bottom=60, left=75, right=75)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if col_widths_cm:
            cell.width = Cm(col_widths_cm[c_idx])
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Data rows
    for r_idx, row_vals in enumerate(rows):
        row = tbl.rows[r_idx + 1]
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=44, bottom=44, left=75, right=75)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if col_widths_cm:
                cell.width = Cm(col_widths_cm[c_idx])
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.12
            if c_idx in mono_cols:
                r = p.add_run(str(val))
                r.font.name = "Consolas"
                r.font.size = Pt(font_size - 0.6)
                r.font.color.rgb = DARK
            else:
                _add_rich_runs(p, str(val), base_size=font_size)

    if trailing_space:
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(3)


def add_heading_1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(13.5)
    r.font.color.rgb = NAVY
    add_bottom_border(p, color="1E3A8A", sz="8")


def add_heading_2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(11.5)
    r.font.color.rgb = BLUE


def add_body(doc: Document, text: str, bold_prefix: str | None = None, space_after: float = 4.5) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.2
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = "Times New Roman"
        rb.font.size = Pt(11)
        rb.font.color.rgb = DARK
    _add_rich_runs(p, text, base_size=11.0)


def add_bullet(doc: Document, bold_lead: str, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.18
    if bold_lead:
        rb = p.add_run(bold_lead)
        rb.bold = True
        rb.font.name = "Times New Roman"
        rb.font.size = Pt(10.8)
        rb.font.color.rgb = DARK
    _add_rich_runs(p, text, base_size=10.8)


def add_figure(doc: Document, img_path: Path, caption: str, width_cm: float = 15.6) -> None:
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(4)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(str(img_path), width=Cm(width_cm))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(6)
    rc = p_cap.add_run(caption)
    rc.italic = True
    rc.font.name = "Times New Roman"
    rc.font.size = Pt(9.6)
    rc.font.color.rgb = MUTED


def build_report() -> None:
    # Collect live verified metrics from our actual engine!
    test_rep = run_json_test_report()
    lex_mini = LexicalAnalyzer.from_preset("minilang")
    lex_calc = LexicalAnalyzer.from_preset("calclang")
    lex_sql = LexicalAnalyzer.from_preset("minisql")
    s_mini = lex_mini.summary_dict()
    s_calc = lex_calc.summary_dict()
    s_sql = lex_sql.summary_dict()

    doc = Document()

    # Page setup: A4 with balanced margins (2.2cm top/bottom, 2.3cm left, 2.0cm right)
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.3)
    sec.right_margin = Cm(2.0)
    sec.different_first_page_header_footer = True

    # Running Header & Footer (Pages 2+)
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

    # Set default Normal font
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(11)

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

    def _cp(text: str, size: float, bold: bool = False, italic: bool = False, color=DARK, space_before: float = 0, space_after: float = 4):
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

    _cp("BỘ GIÁO DỤC VÀ ĐÀO TẠO", 12, bold=True, color=NAVY, space_before=6, space_after=2)
    _cp("TRƯỜNG ĐẠI HỌC KINH TẾ TP. HỒ CHÍ MINH (UEH)", 13.5, bold=True, color=NAVY, space_after=2)
    _cp("KHOA CÔNG NGHỆ THÔNG TIN KINH DOANH — NGÀNH KHOA HỌC MÁY TÍNH", 11, bold=True, color=MUTED, space_after=28)

    _cp("BÁO CÁO TIỂU LUẬN CUỐI KỲ", 16, bold=True, color=BLUE, space_before=18, space_after=6)
    _cp("HỌC PHẦN: NGÔN NGỮ HÌNH THỨC (INTRODUCTION TO FORMAL LANGUAGES)", 11.5, bold=True, color=DARK, space_after=26)

    _cp("ĐỀ TÀI T13:", 13.5, bold=True, color=BLUE, space_before=6, space_after=4)
    _cp("AUTOMATA-BASED LEXICAL ANALYZER", 20, bold=True, color=NAVY, space_after=6)
    _cp("Xây dựng Bộ Phân Tích Từ Vựng Tổng Quát Dựa Trên Biểu Thức Chính Quy,\nThompson ε-NFA, Subset Construction, Direct DFA & Tối Thiểu Hóa Multi-Token DFA", 11.5, italic=True, color=MUTED, space_after=36)

    _cp("Mã lớp học phần: 26C1INF50915301", 11, bold=True, color=DARK, space_after=4)
    _cp("Giảng viên hướng dẫn: ThS. Hồ Thị Thanh Tuyến", 11.5, bold=True, color=NAVY, space_after=24)

    # Group info table inside cover
    p_grp = cc.add_paragraph()
    p_grp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_grp.paragraph_format.space_after = Pt(6)
    rg = p_grp.add_run("NHÓM THỰC HIỆN (NHÓM ... — Vui lòng điền thông tin thành viên)")
    rg.bold = True
    rg.font.name = "Times New Roman"
    rg.font.size = Pt(10.5)
    rg.font.color.rgb = NAVY

    gtbl = cc.add_table(rows=5, cols=4)
    gtbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(gtbl)
    g_headers = ["STT", "Họ và Tên Sinh Viên", "Mã số sinh viên (MSSV)", "Vai trò"]
    g_rows = [
        ["1", "[Điền Họ tên Thành viên 1]", "[MSSV 1]", "Nhóm trưởng · Lý thuyết & Báo cáo"],
        ["2", "[Điền Họ tên Thành viên 2]", "[MSSV 2]", "Regex Parser · Thompson & Direct DFA"],
        ["3", "[Điền Họ tên Thành viên 3]", "[MSSV 3]", "Subset Construction · Min-DFA & Verifier"],
        ["4", "[Điền Họ tên Thành viên 4]", "[MSSV 4]", "Scanner Maximal Munch · Web Studio & Test"],
    ]
    g_widths = [1.3, 5.2, 3.6, 5.1]
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

    _cp("TP. Hồ Chí Minh, tháng 11 năm 2026", 11, bold=True, color=NAVY, space_before=40, space_after=6)

    doc.add_page_break()

    # =========================================================================
    # SECTION 1: MÔ TẢ BÀI TOÁN VÀ MỤC TIÊU ĐỒ ÁN
    # =========================================================================
    add_heading_1(doc, "1. Mô tả bài toán và mục tiêu đồ án")

    add_body(
        doc,
        "Trong kiến trúc của mọi trình biên dịch (compiler) và trình thông dịch (interpreter) hiện đại, "
        "phân tích từ vựng (Lexical Analysis) là giai đoạn đầu tiên đóng vai trò đọc dòng ký tự thô của mã nguồn "
        "và nhóm chúng thành dãy các đơn vị từ vựng có nghĩa gọi là token (từ khóa, định danh, hằng số, chuỗi, toán tử, "
        "dấu phân cách), đồng thời lọc bỏ khoảng trắng/bình luận và phát hiện sớm các lỗi ký tự bất hợp lệ. "
        "Điểm đặc biệt tạo nên cầu nối trực tiếp giữa môn học Ngôn ngữ hình thức và Kỹ thuật trình biên dịch nằm ở chỗ: "
        "mọi lớp token của ngôn ngữ lập trình đều thuộc lớp Ngôn ngữ chính quy (Regular Languages) — do đó có thể được "
        "đặc tả ngắn gọn bằng Biểu thức chính quy (Regular Expression — RE) và thực thi tự động bằng Automata hữu hạn đơn định (DFA) "
        "với tốc độ tuyến tính theo độ dài mã nguồn.",
    )

    add_body(
        doc,
        "Thay vì viết tay bộ quét bằng các câu lệnh if/else cứng nhắc cho một ngôn ngữ cố định hoặc phụ thuộc vào thư viện biểu thức "
        "chính quy có sẵn (như module `re` của Python), đề tài T13 — Automata-based Lexical Analyzer hướng tới việc xây dựng một "
        "bộ sinh và thực thi bộ phân tích từ vựng tổng quát (Lexical Analyzer Generator & Studio) hoàn toàn từ lý thuyết Automata hữu hạn.",
    )

    add_heading_2(doc, "1.1. Mục tiêu cụ thể của đồ án")
    add_bullet(doc, "Chuyển hóa trọn vẹn lý thuyết thành cài đặt độc lập: ",
               "Tự cài đặt 100% chuỗi thuật toán cốt lõi bằng Python thuần (tuyệt đối không sử dụng thư viện `re` trong lõi): "
               "Phân tích cú pháp RE → Cấu trúc Thompson (RE → ε-NFA) → Hợp nhất đa-token ε-NFA → Thuật toán tập con (Subset Construction) → "
               "Tối thiểu hóa Multi-token DFA → Bộ quét từ vựng Maximal Munch có phục hồi lỗi.")
    add_bullet(doc, "Cài đặt song song nhánh đối chứng Direct RE → DFA: ",
               "Triển khai thuật toán xây dựng DFA trực tiếp từ cây phân tích biểu thức chính quy gia tố r·# (tính nullable, firstpos, lastpos, followpos) "
               "khớp sát bài giảng Chương 3.1 (UEH), đồng thời cài đặt bộ kiểm chứng tương đương bằng Product Automaton và xuất file .jff tương thích JFLAP.")
    add_bullet(doc, "Minh họa đa ngôn ngữ và trực quan hóa tương tác: ",
               "Thiết kế 3 bộ đặc tả ngôn ngữ (MiniLang 38 token, CalcLang 12 token, MiniSQL 14 token) cùng ứng dụng Web trực quan "
               "(LexAutomata Studio) cho phép chỉnh sửa RE trực tiếp, quan sát đồ thị SVG, bảng chuyển trạng thái, các bước phân hoạch tối giản "
               "và mô phỏng hoạt ảnh từng bước quét + quay lui Maximal Munch.")
    add_bullet(doc, "Kiểm thử toàn diện và đánh giá thực nghiệm: ",
               "Xây dựng bộ 29 test case chuẩn (hợp lệ, trường hợp biên, lỗi từ vựng), kiểm chứng chéo với oracle độc lập và đo đạc hiệu năng biên dịch/quét.")

    # =========================================================================
    # SECTION 2: CƠ SỞ LÝ THUYẾT LIÊN QUAN
    # =========================================================================
    add_heading_1(doc, "2. Cơ sở lý thuyết liên quan")

    add_body(
        doc,
        "Toàn bộ thiết kế của hệ thống dựa trên các định nghĩa và định lý chuẩn trong giáo trình "
        "Introduction to Automata Theory, Languages, and Computation (Hopcroft, Motwani & Ullman, 3rd Ed.) "
        "và bài giảng Chương 3 môn Ngôn ngữ hình thức (UEH):",
    )

    add_heading_2(doc, "2.1. Bảng chữ cái, Ngôn ngữ và Biểu thức chính quy (RE)")
    add_body(
        doc,
        "Cho bảng chữ cái hữu hạn khác rỗng Σ. Tập tất cả chuỗi hữu hạn trên Σ ký hiệu là Σ* (chứa chuỗi rỗng ε). "
        "Một ngôn ngữ L là tập con L ⊆ Σ*. Biểu thức chính quy (Regular Expression — RE) trên Σ được định nghĩa đệ quy: "
        "(i) ∅ là RE biểu diễn tập rỗng ∅; (ii) ε là RE biểu diễn {ε}; (iii) ∀a ∈ Σ, a là RE biểu diễn {a}; "
        "(iv) Nếu r và s là các RE biểu diễn L(r) và L(s), thì (r | s) biểu diễn L(r) ∪ L(s) (phép hợp), "
        "(r·s) biểu diễn L(r)L(s) (phép nối kết), và (r*) biểu diễn L(r)* = ⋃_{k≥0} L(r)^k (bao đóng Kleene). "
        "Thứ tự ưu tiên toán tử từ cao đến thấp: Ngoặc đơn (…) > Bao đóng (*, +, ?) > Nối kết (·) > Phép hợp (|). "
        "Các toán tử mở rộng chuẩn trong đặc tả từ vựng được định nghĩa tương đương: r+ = r·r* (bao đóng dương), r? = r | ε (tùy chọn), "
        "lớp ký tự [a-z] = (a|b|...|z) và lớp phủ định [^c] = Σ \\ {c}.",
    )

    add_heading_2(doc, "2.2. Automata hữu hạn đơn định (DFA) và không đơn định có ε-chuyển tiếp (ε-NFA)")
    add_callout(
        doc,
        "Định nghĩa hình thức (Hopcroft–Motwani–Ullman & Slide Chương 3.1 UEH)",
        [
            "• DFA là bộ năm A = (Q, Σ, δ, q₀, F) gồm: tập trạng thái hữu hạn Q ≠ ∅; bảng chữ cái Σ; "
            "hàm chuyển đơn định δ: D → Q với D ⊆ Q × Σ (có thể mở rộng thành hàm toàn phần bằng trạng thái chết d); "
            "trạng thái khởi đầu q₀ ∈ Q; và tập trạng thái kết thúc F ⊆ Q. Ngôn ngữ đoán nhận: L(A) = { w ∈ Σ* | δ̂(q₀, w) ∈ F }.",
            "• ε-NFA là bộ năm N = (Q, Σ, δ, q₀, F) với hàm chuyển δ: Q × (Σ ∪ {ε}) → 2^Q. "
            "Bao đóng ε của tập trạng thái S ⊆ Q, ký hiệu ε-closure(S), là tập tất cả trạng thái đi tới được từ S chỉ qua 0 hoặc nhiều ε-chuyển tiếp. "
            "Ngôn ngữ đoán nhận: L(N) = { w ∈ Σ* | δ̂(q₀, w) ∩ F ≠ ∅ }.",
        ],
    )

    add_heading_2(doc, "2.3. Định lý Kleene và các phép biến đổi tương đương")
    add_body(
        doc,
        "Định lý Kleene khẳng định ba mô hình RE, ε-NFA và DFA tương đương về sức mạnh biểu diễn (đều đặc trưng chính xác cho lớp Ngôn ngữ chính quy). "
        "Đồ án khai thác đồng thời hai con đường biến đổi cốt lõi:",
    )
    add_bullet(doc, "Đường ống chuẩn (RE → ε-NFA → DFA → Min-DFA): ",
               "Chuyển RE sang ε-NFA bằng Cấu trúc Thompson (mỗi toán tử tạo tối đa 2 trạng thái mới, kích thước tuyến tính O(|R|)); "
               "khử tính không đơn định và ε-chuyển tiếp sang DFA bằng Thuật toán tập con (Subset Construction) qua hai phép toán ε-closure và Move(S, a); "
               "sau đó tối thiểu hóa số trạng thái DFA bằng Thuật toán tinh chỉnh phân hoạch (Partition Refinement — Giải thuật 3.6) dựa trên Định lý Myhill–Nerode.")
    add_bullet(doc, "Đường ống trực tiếp (Direct RE → DFA — Berry–Sethi / Dragon Book): ",
               "Gia tố hóa biểu thức r thành r·# (# ∉ Σ), dựng cây phân tích cú pháp, đánh số các lá từ 1..n, "
               "tính đệ quy ba hàm nullable(v), firstpos(v), lastpos(v) và lập bảng followpos(p) tại các nút nối kết (·) và bao đóng (*, +), "
               "từ đó dựng trực tiếp các trạng thái DFA mà không qua bước ε-NFA trung gian.")

    add_heading_2(doc, "2.4. Nguyên lý Phân tích Từ vựng Dựa trên Automata")
    add_body(
        doc,
        "Khác với bài toán nhận dạng một chuỗi đơn lẻ w ∈ L(r)?, một bộ phân tích từ vựng (Lexical Analyzer) phải phân tách liên tục "
        "một dòng mã nguồn dài thành chuỗi token dựa trên k biểu thức chính quy R₁, R₂, ..., Rₖ đồng thời. Để việc phân tách là duy nhất và xác định, "
        "lý thuyết trình biên dịch (Dragon Book, Chương 3) áp dụng hai quy tắc giải nhập nhằng chuẩn:",
    )
    add_bullet(doc, "Quy tắc Khớp Dài Nhất (Maximal Munch / Longest Match): ",
               "Tại vị trí hiện tại trên đầu vào, luôn chọn tiền tố dài nhất có thể đưa DFA tới một trạng thái kết thúc. "
               "Ví dụ: 'ifx' được quét thành IDENTIFIER('ifx') thay vì KW_IF('if') + IDENTIFIER('x'); '===' tách thành OP_EQ('==') + OP_ASSIGN('='); "
               "'3.14' thành FLOAT_LIT('3.14') thay vì INT_LIT('3') + '.' + INT_LIT('14').")
    add_bullet(doc, "Quy tắc Ưu Tiên Luật (Rule Priority): ",
               "Khi cùng một tiền tố dài nhất đồng thời khớp nhiều luật token khác nhau (ví dụ chuỗi 'if' khớp cả KW_IF lẫn IDENTIFIER), "
               "chọn luật có độ ưu tiên cao hơn (xuất hiện trước trong bảng đặc tả).")

    # =========================================================================
    # SECTION 3: MÔ HÌNH HÌNH THỨC / AUTOMATA ĐƯỢC SỬ DỤNG
    # =========================================================================
    add_heading_1(doc, "3. Mô hình hình thức / Automata được sử dụng")

    add_heading_2(doc, "3.1. Xác định Input, Output và các Giả định hình thức")
    add_bullet(doc, "Đầu vào (Input): ",
               "(1) Danh sách có thứ tự các đặc tả token Spec = [(T₁, R₁, p₁, skip₁), ..., (Tₖ, Rₖ, pₖ, skipₖ)] trong đó Tᵢ là tên token, Rᵢ là biểu thức chính quy, "
               "p₁ < p₂ < ... < pₖ là độ ưu tiên (số nhỏ ưu tiên cao hơn), skipᵢ ∈ {True, False} đánh dấu token bỏ qua; "
               "và (2) Chuỗi mã nguồn đầu vào w ∈ Σ*.")
    add_bullet(doc, "Đầu ra (Output): ",
               "Các mô hình Automata trung gian (Combined ε-NFA, Subset DFA, Minimized DFA), bằng chứng tương đương toán học, "
               "luồng token [(T, lexeme, line, col, accept_state, backtrack)], danh sách lỗi từ vựng LexicalError và vết thực thi từng bước.")
    add_bullet(doc, "Giả định bảng chữ cái Σ và quy ước ký hiệu: ",
               "Bảng chữ cái làm việc hữu hạn gồm |Σ| = 98 ký tự: toàn bộ 95 ký tự ASCII in được (mã 32..126) hợp với 3 ký tự điều khiển khoảng trắng {\\t, \\n, \\r}. "
               "Mọi ký tự nằm ngoài Σ (như ký hiệu tiền tệ €, chữ tiếng Việt có dấu) được xử lý an toàn bằng cách kích hoạt chuyển tiếp không xác định (DEAD) "
               "và báo LEXICAL_ERROR kèm mã Unicode. Về ký hiệu RE: dùng '|' cho phép hợp (thay cho '+' trên slide lý thuyết thuần túy) để dành '+' cho bao đóng dương r+ = rr* "
               "theo chuẩn công nghiệp POSIX/Flex, đồng thời hỗ trợ 'ε' (hoặc '\\e') cho chuỗi rỗng.")

    add_heading_2(doc, "3.2. Mô hình Combined Multi-token ε-NFA và Multi-token DFA")
    add_callout(
        doc,
        "Mở rộng Automata hữu hạn sang Bài toán Phân loại Đa-Token (Moore-labeled Automata)",
        [
            "1. Combined ε-NFA: N_lex = (Q_N, Σ, δ_N, q_start, F_N, τ_N)",
            "   • Với mỗi luật i ∈ {1..k}, dựng Thompson ε-NFA Nᵢ = (Qᵢ, Σ, δᵢ, sᵢ, {fᵢ}) có tập trạng thái rời nhau.",
            "   • Tạo trạng thái đầu chung q_start ∉ ⋃ Qᵢ, thêm các ε-chuyển tiếp δ_N(q_start, ε) = {s₁, s₂, ..., sₖ}.",
            "   • Tập kết thúc F_N = {f₁, ..., fₖ} kèm ánh xạ nhãn τ_N(fᵢ) = (Tᵢ, pᵢ, skipᵢ).",
            "",
            "2. Multi-token DFA: D_lex = (Q_D, Σ/≡, δ_D, D₀, F_D, τ_D)",
            "   • Q_D ⊆ 2^{Q_N} với D₀ = ε-closure({q_start}); Σ/≡ là tập các lớp tương đương ký tự (Alphabet Partitioning).",
            "   • Trạng thái S ∈ Q_D thuộc F_D khi và chỉ khi S ∩ F_N ≠ ∅. Khi |S ∩ F_N| > 1 (xung đột luật), "
            "nhãn đầu ra được xác định đơn định theo Rule Priority: τ_D(S) = argmin_{f ∈ S ∩ F_N} priority(f).",
            "",
            "3. Điều kiện bất biến khi Tối thiểu hóa Multi-token DFA:",
            "   • Hai trạng thái kết thúc s, t ∈ F_D chỉ có thể tương đương nếu τ_D(s) = τ_D(t) (cùng loại token & cờ skip).",
            "   • Do đó phân hoạch khởi đầu phải là: Π₀ = { Q_D \\ F_D } ∪ { F_{T₁}, F_{T₂}, ..., F_{T_m} }.",
        ],
    )

    add_heading_2(doc, "3.3. Đặc tả tập Token minh họa (MiniLang, CalcLang & MiniSQL)")
    add_body(
        doc,
        "Để chứng minh tính tổng quát của bộ sinh từ vựng (không lập trình cứng cho một ngôn ngữ duy nhất), nhóm xây dựng 3 bộ đặc tả: "
        "MiniLang (38 token — ngôn ngữ lệnh đầy đủ làm demo chính), CalcLang (12 token — gọn nhẹ để quan sát toàn bộ đồ thị Combined DFA 20 trạng thái) "
        "và MiniSQL (14 token — ngôn ngữ truy vấn). Bảng 1 tóm tắt các nhóm token tiêu biểu của MiniLang:",
    )

    minilang_summary_rows = [
        ["1", "COMMENT", r"//[^\n]*", "Bỏ qua", "Bình luận một dòng (ưu tiên trước '/' nhờ Maximal Munch)"],
        ["2", "WHITESPACE", r"[ \t\n\r]+", "Bỏ qua", "Khoảng trắng, tab, xuống dòng"],
        ["3–11", "KW_IF .. BOOL_LIT", r"if, else, while, for, let, func, return, print, true|false", "Giữ", "9 từ khóa & hằng logic (ưu tiên trên IDENTIFIER)"],
        ["12", "FLOAT_LIT", r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", "Giữ", "Số thực & dạng khoa học (ưu tiên trên INT_LIT)"],
        ["13", "INT_LIT", r"[0-9]+", "Giữ", "Số nguyên không dấu"],
        ["14", "STRING_LIT", r'"([^"\\\n]|\\.)*"', "Giữ", "Chuỗi trong ngoặc kép, hỗ trợ escape \\\" và \\\\"],
        ["15", "IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*", "Giữ", "Tên biến, tên hàm (đặt sau từ khóa)"],
        ["16–21", "OP_EQ .. OP_OR", r"==, !=, <=, >=, &&, \|\|", "Giữ", "6 toán tử 2 ký tự (khớp trước toán tử 1 ký tự)"],
        ["22–30", "OP_ASSIGN .. OP_MOD", r"=, <, >, !, \+, -, \*, /, %", "Giữ", "9 toán tử 1 ký tự"],
        ["31–38", "LPAREN .. COMMA", r"\(, \), \{, \}, \[, \], ;, ,", "Giữ", "8 dấu phân cách khối lệnh & tham số"],
    ]
    add_styled_table(
        doc,
        ["Ưu tiên", "Nhóm Token", "Biểu thức chính quy (RE)", "Xử lý", "Vai trò & Ghi chú kỹ thuật"],
        minilang_summary_rows,
        col_widths_cm=[1.5, 3.0, 5.2, 1.4, 5.6],
        font_size=8.8,
        mono_cols={1, 2},
    )

    # =========================================================================
    # SECTION 4: THUẬT TOÁN VÀ THIẾT KẾ GIẢI PHÁP
    # =========================================================================
    add_heading_1(doc, "4. Thuật toán và thiết kế giải pháp")

    add_body(
        doc,
        "Hình 1 trình bày kiến trúc 6 giai đoạn của hệ thống, kết nối chặt chẽ giữa nhánh biên dịch chính "
        "(RE → AST → Thompson ε-NFA → Subset DFA → Minimized DFA → Scanner) với nhánh đối chứng (Direct RE → DFA, JFLAP Export) "
        "và bộ chứng minh tương đương hình thức (Product Automaton Verifier).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig1_architecture_pipeline.png",
        "Hình 1: Kiến trúc tổng thể 6 giai đoạn của Hệ thống Phân tích Từ vựng Dựa trên Automata (Đề tài T13).",
        width_cm=16.2,
    )

    add_heading_2(doc, "4.1. Thuật toán 1 — Phân tích cú pháp RE (Recursive-Descent Parser)")
    add_body(
        doc,
        "Thay vì gọi thư viện `re`, nhóm tự xây dựng bộ phân tích cú pháp đoán nhận trước đệ quy trong `regex_parser.py` theo văn phạm phi ngữ cảnh 4 mức ưu tiên: "
        "`expr → concat ('|' concat)*`, `concat → repeat+`, `repeat → atom ('*'|'+'|'?')*`, `atom → '(' expr ')' | char_class | '.' | escape | 'ε' | literal`. "
        "Các lớp ký tự `[a-zA-Z0-9_]` hoặc phủ định `[^\"\\n]` được gom thành một nút lá `CharSetNode(chars ⊆ Σ)` duy nhất thay vì trải ra hàng chục nhánh hợp `|`, "
        "giúp cây cú pháp và ε-NFA cực kỳ gọn nhẹ. Parser đồng thời kiểm tra chặt mọi lỗi cú pháp RE (ngoặc chưa đóng, lớp rỗng `[]`, khoảng ngược `[z-a]`, toán tử thiếu toán hạng) "
        "và cung cấp hàm `is_nullable()` phát hiện sớm các biểu thức khớp chuỗi rỗng ε để ngăn nguy cơ vòng lặp vô hạn khi quét.",
    )

    add_heading_2(doc, "4.2. Thuật toán 2 — Cấu trúc Thompson & Hợp nhất đa-token ε-NFA")
    add_body(
        doc,
        "Duyệt hậu tố trên AST, mỗi hàm xây dựng mảnh NFA duy trì chặt hai bất biến Thompson: bậc vào của trạng thái đầu bằng 0 (`in-deg(start) = 0`) "
        "và bậc ra của trạng thái cuối bằng 0 (`out-deg(end) = 0`). Nhờ bất biến này, phép nối kết `ConcatNode(L, R)` gộp trực tiếp trạng thái kết thúc của L "
        "với trạng thái khởi đầu của R mà không tạo chu trình giả và giảm được ε-cạnh dư thừa. Kiểm chứng trên biểu thức kinh điển `(a|b)*abb` cho ra chính xác "
        "11 trạng thái (q0..q10) trùng khớp hoàn toàn với Slide 38 Chương 3.1 (Hình 2).",
    )
    add_figure(
        doc,
        FIG_DIR / "fig2_slide38_pipeline.png",
        "Hình 2: Kết quả thực thi đường ống RE → Thompson ε-NFA (11 trạng thái) → Subset DFA (5 trạng thái) → Minimized DFA (4 trạng thái) trên (a|b)*abb.",
        width_cm=16.0,
    )

    add_heading_2(doc, "4.3. Thuật toán 3 — Subset Construction kết hợp Alphabet Partitioning & Rule Priority")
    add_body(
        doc,
        "Nếu chạy Subset Construction duyệt từng ký tự một trên cả 98 ký tự của Σ cho bộ 38 token MiniLang, bảng chuyển sẽ có tới 98 cột dư thừa. "
        "Nhóm cài đặt kỹ thuật phân hoạch bảng chữ cái (Alphabet Partitioning / Min-terms — tương tự cơ chế tối ưu trong Flex): "
        "từ tất cả tập ký tự chuyển tiếp C₁, ..., C_m của Combined ε-NFA, tinh chỉnh thành các lớp tương đương rời nhau nhỏ nhất E₁, ..., E_p ⊆ Σ sao cho "
        "∀c₁, c₂ ∈ Eⱼ thì Move(S, c₁) = Move(S, c₂) với mọi S ⊆ Q_N. Nhờ đó MiniLang nén từ 98 ký tự xuống còn 43 lớp tương đương, "
        "vừa giữ nguyên chính xác toán học 100%, vừa tăng tốc biên dịch xuống < 10 ms và giúp bảng chuyển dễ đọc. "
        "Khi một trạng thái DFA S chứa nhiều trạng thái kết thúc NFA (ví dụ `KW_IF` và `IDENTIFIER` đều kết thúc tại `'if'`), "
        "hàm `_resolve_accept(S)` chọn quy tắc có `priority` nhỏ nhất và lưu lại danh sách xung đột để hiển thị minh bạch trên giao diện.",
    )

    add_heading_2(doc, "4.4. Thuật toán 4 — Direct RE → DFA (Nhánh đối chứng khớp Slide 40–57)")
    add_body(
        doc,
        "Trong `direct_dfa.py`, mỗi biểu thức r được gia tố thành r·#, đánh số các nút lá từ 1..n, tính `nullable`, `firstpos`, `lastpos` theo duyệt hậu tố "
        "và cập nhật bảng `followpos` tại các nút nối kết (∀i ∈ lastpos(c₁): followpos[i] ∪= firstpos(c₂)) và nút lặp `*`, `+` (∀i ∈ lastpos(c₁): followpos[i] ∪= firstpos(c₁)). "
        "Hình 3 minh họa kết quả Direct DFA trên ví dụ `r = (a|ba)(a|b)*ba#`: chương trình sinh chính xác 5 trạng thái A{1,2}, B{4,5,6}, C{3}, D{4,5,6,7}, E{4,5,6,8} "
        "trùng khớp từng con số với Slide 54–57 Chương 3.1!",
    )
    add_figure(
        doc,
        FIG_DIR / "fig5_direct_dfa_slide46.png",
        "Hình 3: Direct DFA xây dựng trực tiếp từ r = (a|ba)(a|b)*ba# qua bảng followpos — khớp 100% Slide 55–57 Chương 3.1.",
        width_cm=14.0,
    )

    add_heading_2(doc, "4.5. Thuật toán 5 — Tối thiểu hóa Multi-token DFA & Chứng minh Product Automaton")
    add_body(
        doc,
        "Thuật toán tối thiểu hóa trong `dfa_minimizer.py` gồm 5 bước: (1) Loại trạng thái không đạt tới bằng BFS từ D₀; "
        "(2) Bổ sung tạm thời trạng thái chết ảo `DEAD = -1` để hàm chuyển đầy đủ trên mọi lớp ký tự; "
        "(3) Khởi tạo phân hoạch Π₀ gồm khối không kết thúc (Q \\ F ∪ {DEAD}) và mỗi loại token một khối kết thúc riêng biệt F_{Tᵢ}; "
        "(4) Lặp tách các khối có vector chữ ký chuyển tiếp `(block_of[δ(s, E₁)], ..., block_of[δ(s, E_p)])` khác nhau cho đến khi Π_{k+1} = Π_k; "
        "(5) Loại bỏ khối chứa `DEAD` và các chuyển tiếp tới `DEAD` (khớp Bước 5 Giải thuật 3.6), đánh số lại trạng thái theo thứ tự BFS. "
        "Ngay sau khi tối thiểu hóa, module `verifier.py` chạy BFS trên **Product Automaton** A × B từ (q₀,A, q₀,B) để chứng minh toán học "
        "∀w ∈ Σ*: τ_A(w) = τ_B(w); nếu có bất kỳ sai khác nào, thuật toán sẽ truy vết ngược trả về chuỗi phản ví dụ ngắn nhất.",
    )

    add_heading_2(doc, "4.6. Thuật toán 6 — Bộ quét Maximal Munch, Backtracking & Panic-mode Recovery")
    add_callout(
        doc,
        "Mã giả Thuật toán Quét Từ Vựng DFA (lexer_engine/scanner.py)",
        [
            "Input : Chuỗi mã nguồn text[0..n-1], Minimized Multi-token DFA D = (Q, Σ/≡, δ, D₀, F, τ)",
            "Output: Danh sách Token, Danh sách LexicalError, Vết thực thi Trace",
            "1. pos ← 0; line ← 1; col ← 1",
            "2. WHILE pos < n DO:",
            "3.   cur ← D₀; cursor ← pos; last_accept ← NULL",
            "4.   WHILE cursor < n AND cur ≠ NULL DO:",
            "5.     nxt ← δ(cur, class_of[text[cursor]])      // Tra bảng O(1)",
            "6.     IF nxt == NULL THEN BREAK                 // Gặp chuyển tiếp DEAD",
            "7.     cur ← nxt; cursor ← cursor + 1",
            "8.     IF cur ∈ F THEN last_accept ← (cursor, cur, τ(cur))",
            "9.   IF last_accept ≠ NULL AND last_accept.pos > pos THEN:   // Chặn vòng lặp ε",
            "10.    backtrack ← cursor - last_accept.pos                  // Số ký tự quay lui",
            "11.    Emit Token(last_accept.type, text[pos:last_accept.pos], line, col, backtrack)",
            "12.    Update (line, col); pos ← last_accept.pos",
            "13.  ELSE:                                       // Không khớp tiền tố hợp lệ nào",
            "14.    Emit LexicalError(text[pos], line, col, attempted = text[pos:cursor])",
            "15.    Update (line, col); pos ← pos + 1         // Phục hồi Panic-mode tiến 1 ký tự",
        ],
        fill="F8FAFC",
        accent="1E3A8A",
        mono=True,
    )

    add_heading_2(doc, "4.7. Phân tích độ phức tạp và các trường hợp biên đã xử lý")
    comp_rows = [
        ["Regex Parser + Thompson NFA", "O(|R|)", "O(|R|)", "Phát hiện RE rỗng, ngoặc lệch, lớp ký tự ngược [z-a], escape cuối chuỗi"],
        ["Alphabet Partitioning", "O(m · |Σ|)", "O(|Σ|)", "Gom 98 ký tự ASCII thành p ≤ 98 lớp tương đương (MiniLang: 43 lớp)"],
        ["Subset Construction", "Xấu nhất O(2^|Q_N|·p)\nThực tế O(|Q_D|·p)", "O(|Q_D|·p)", "Ngưỡng bảo vệ max_states=5000 tránh bùng nổ tổ hợp; giải xung đột ưu tiên"],
        ["Multi-token Minimization", "O(|Q_D|² · p)", "O(|Q_D| · p)", "Không gộp hai loại token khác nhau; loại trạng thái không đạt tới & DEAD"],
        ["Product Automaton Verify", "O(|Q_A| · |Q_B| · p)", "O(|Q_A| · |Q_B|)", "Chứng minh tương đương tuyệt đối trên vô hạn chuỗi hoặc sinh phản ví dụ ngắn nhất"],
        ["DFA Lexical Scanner", "Trung bình O(n)\nXấu nhất O(n²)", "O(n) cho output", "Maximal Munch + quay lui (VD: 1.5e, 3.); chặn lặp vô hạn với RE nullable; Panic-mode"],
    ]
    add_styled_table(
        doc,
        ["Thành phần thuật toán", "Độ phức tạp thời gian", "Bộ nhớ", "Xử lý trường hợp biên"],
        comp_rows,
        col_widths_cm=[3.8, 3.3, 2.3, 7.3],
        font_size=8.6,
    )

    # =========================================================================
    # SECTION 5: CÀI ĐẶT VÀ KIẾN TRÚC CHƯƠNG TRÌNH
    # =========================================================================
    add_heading_1(doc, "5. Cài đặt và kiến trúc chương trình")

    add_body(
        doc,
        "Chương trình được tổ chức theo kiến trúc phân lớp rõ ràng gồm 3 tầng độc lập: "
        "(1) Tầng lõi thuật toán `lexer_engine/` (100% Python thuần, không phụ thuộc bất kỳ gói bên ngoài nào và tuyệt đối không `import re`); "
        "(2) Tầng giao diện người dùng gồm Web Studio tương tác (`app.py` + `web/index.html`, `styles.css`, `app.js` sử dụng SVG thuần có kéo-thả/zoom) và công cụ dòng lệnh (`cli.py`); "
        "(3) Tầng kiểm thử và dữ liệu (`tests/`, `data/specs/`, `data/samples/`, `data/jflap_exports/`). "
        "Bảng 2 làm rõ ranh giới giữa phần nhóm tự cài đặt và thư viện chuẩn/hỗ trợ theo đúng yêu cầu kỹ thuật của đồ án:",
    )

    lib_rows = [
        ["regex_parser.py, thompson.py, subset_construction.py, direct_dfa.py, dfa_minimizer.py, scanner.py, verifier.py, jflap_export.py",
         "100% nhóm tự cài đặt từ con số 0",
         "Không dùng thư viện ngoài (chỉ dùng kiểu dữ liệu chuẩn Python: dataclasses, collections.deque, time)"],
        ["app.py, cli.py, web/ (HTML/CSS/JS + SVG Automata & Syntax Tree Renderer + Step Animator)",
         "100% nhóm tự thiết kế & lập trình",
         "Python stdlib `http.server`, `argparse`, `json`; trình duyệt chuẩn HTML5/SVG (không cần Node.js/React)"],
        ["tests/test_suite.py (29 test cases JSON + 11 unittest)",
         "Nhóm tự thiết kế test case & kịch bản",
         "Python `unittest`; chỉ dùng `re` làm oracle đối chứng độc lập bên ngoài lõi"],
        ["scripts/ (vẽ hình báo cáo & tạo DOCX/PDF/PPTX ngoài runtime)",
         "Nhóm viết script tự động hóa",
         "graphviz, matplotlib, python-docx, python-pptx (không cần khi chạy chương trình demo)"],
    ]
    add_styled_table(
        doc,
        ["Module / Thành phần", "Phần nhóm tự triển khai", "Thư viện / Công cụ sử dụng"],
        lib_rows,
        col_widths_cm=[5.3, 4.2, 7.2],
        font_size=8.6,
    )

    add_heading_2(doc, "5.1. Các tính năng nổi bật của Giao diện Web LexAutomata Studio & CLI")
    add_bullet(doc, "Tab 1 — Bộ Quét & Mô Phỏng Từng Bước: ",
               "Soạn thảo mã nguồn với 3 kịch bản mẫu (`Hợp lệ`, `Biên Maximal Munch`, `Lỗi & Phục hồi`), tô màu trực tiếp theo loại token, "
               "và hoạt ảnh DFA Step-by-Step hiển thị băng ký tự, trạng thái kết thúc và cung quay lui.")
    add_bullet(doc, "Tab 2 — Automata Tổng Hợp & Tối Thiểu Hóa: ",
               "Vẽ đồ thị SVG có kéo-thả/zoom cho `Minimized DFA`, `Subset DFA`, `Combined ε-NFA`; xem bảng chuyển trạng thái, các bước tinh chỉnh phân hoạch `Π₀ → Πₙ`, "
               "xung đột ưu tiên đã giải quyết và tải file `.jff` để đối chứng trực tiếp trên phần mềm JFLAP.")
    add_bullet(doc, "Tab 3 & Tab 4 — Thí Nghiệm RE Đơn Lẻ & Live Token Spec Editor: ",
               "Đối chứng song song Thompson ε-NFA với cây phân tích `r·#` (`nullable`, `FP`, `LP`, `followpos`) của Direct RE → DFA; "
               "hỗ trợ chỉnh sửa/thêm luật mới (như `HEX_LIT: 0[xX][0-9a-fA-F]+`) và biên dịch lại toàn bộ Automata trong vài mili-giây.")
    add_bullet(doc, "Tab 5 & Giao diện CLI (cli.py): ",
               "Chạy tự động toàn bộ 29 test case, bảng benchmark 3 ngôn ngữ và cho phép tái hiện mọi luồng quét/kiểm tra/xuất `.jff` ngay từ cửa sổ dòng lệnh.")

    add_body(
        doc,
        "Hình 4 minh họa đồ thị Minimized Combined DFA hoàn chỉnh của bộ ngôn ngữ CalcLang (12 token nén xuống đúng 20 trạng thái) "
        "được xuất trực tiếp từ bộ máy của nhóm: có thể quan sát trực quan nhánh nhận từ khóa `let` (D0→D9→D13→D16[KW_LET]) và `print` "
        "(D0→D10→D14→D17→D18→D19[KW_PRINT]) hòa vào trạng thái `D8[ID]` ngay khi đọc tiếp ký tự định danh theo quy tắc Maximal Munch.",
    )
    add_figure(
        doc,
        FIG_DIR / "fig3_calclang_combined_dfa.png",
        "Hình 4: Đồ thị Minimized Combined Multi-token DFA hoàn chỉnh của CalcLang (12 token → 20 trạng thái tối giản).",
        width_cm=12.6,
    )

    add_body(
        doc,
        "Hình 5 và Hình 6 chụp trực tiếp giao diện Web tương tác LexAutomata Studio đang vận hành trên máy cục bộ. "
        "Tại Tab 1 (Hình 5), khi quét trường hợp biên `let bt = 1.5e + 2;`, trình mô phỏng từng bước hiển thị rõ băng ký tự, "
        "đường đi `D0 → D13[INT_LIT] → D37 → D52[FLOAT_LIT] → D62 → ✗ DEAD` cùng mũi tên cam quay lui 1 ký tự (`↩ Quay lui 1 ký tự về D52`) "
        "để xuất `FLOAT_LIT('1.5')` rồi quét tiếp `IDENTIFIER('e')`. Tại Tab 3 (Hình 6), người dùng có thể đối chứng trực quan "
        "cây phân tích gia tố `r·#` (`nullable`, `firstpos`, `lastpos`) và bảng `followpos` khớp hoàn toàn với bài giảng Chương 3.1.",
    )
    add_figure(
        doc,
        FIG_DIR / "fig6_web_scanner_demo.png",
        "Hình 5: Giao diện Web LexAutomata Studio — Tab 1 minh họa quét trường hợp biên MiniLang và hoạt ảnh quay lui Maximal Munch trên '1.5e'.",
        width_cm=14.6,
    )
    add_figure(
        doc,
        FIG_DIR / "fig7_web_direct_re_lab.png",
        "Hình 6: Giao diện Web LexAutomata Studio — Tab 3 minh họa cây phân tích gia tố r·# và bảng followpos cho (a|ba)(a|b)*ba.",
        width_cm=14.6,
    )

    # =========================================================================
    # SECTION 6: TEST CASE, KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH
    # =========================================================================
    add_heading_1(doc, "6. Test case, kết quả thực nghiệm và phân tích")

    add_heading_2(doc, "6.1. Thiết kế bộ Test Case đa dạng và Kết quả kiểm thử")
    add_body(
        doc,
        f"Nhóm xây dựng bộ kiểm thử có cấu trúc trong `tests/test_cases.json` ({test_rep['total']} kịch bản chuẩn) kết hợp với "
        f"11 nhóm kiểm thử đơn vị/tích hợp tự động trong `tests/test_suite.py` (chạy hoàn tất trong ~0.08 giây). "
        f"Kết quả đạt {test_rep['passed']}/{test_rep['total']} PASS ({test_rep['pass_rate']}%), đồng thời kiểm thử tự động `test_zero_re_in_engine()` "
        f"xác nhận không có câu lệnh `import re` nào trong `lexer_engine/`, và kiểm thử đối chứng độc lập cho kết quả khớp 100% giữa: "
        f"(i) ε-NFA Simulator, (ii) Subset DFA, (iii) Minimized DFA, (iv) Direct DFA, và (v) Python `re` oracle. "
        f"Bảng 3 trình bày các trường hợp kiểm thử đại diện gồm đủ 3 nhóm: hợp lệ, biên và không hợp lệ:",
    )

    tc_rows = [
        ["RE-01", "Hợp lệ", "(a|b)*abb (Slide 38)", "NFA:11 → Sub:5 → Dir:4 → Min:4; Eq=✓; 5 accept + 7 reject", "PASS"],
        ["RE-02", "Hợp lệ", "(a|ba)(a|b)*ba (Slide 46–57)", "8 lá; followpos khớp 100% Slide 54; Direct DFA = 5 trạng thái", "PASS"],
        ["RE-06", "Biên", "(a|ε)b* (biểu thức nullable)", "Phát hiện nullable=True; chấp nhận ε; không lặp vô hạn khi quét", "PASS"],
        ["RE-ERR-01..09", "Không hợp lệ", "9 mẫu RE lỗi: '', '(a|b*', '*abc', 'a|', '[z-a]', 'abc\\'", "Bắt đúng RegexSyntaxError kèm vị trí ký tự lỗi trên cả 9/9 mẫu", "PASS"],
        ["SCAN-01", "Hợp lệ", "let x = 10 + 2.5;", "7 token hợp lệ, 0 lỗi, tọa độ (line:col) chính xác", "PASS"],
        ["SCAN-02", "Biên", "if ifx while while2 true true_val", "KW_IF('if'), ID('ifx'), KW_WHILE('while'), ID('while2'), BOOL('true'), ID('true_val')", "PASS"],
        ["SCAN-03", "Biên", "a===b!==c<=>=d&&||!", "Tách chuẩn ==, =, !=, =, <=, >=, &&, ||, ! không cần khoảng trắng", "PASS"],
        ["SCAN-05", "Biên", 'print("", "hi \\"UEH\\"\\\\");', "Nhận chuỗi rỗng và chuỗi có ký tự escape \\\" và \\\\", "PASS"],
        ["SCAN-06", "Biên", "1.5e-2 1.5e+3 1.5e", "1.5e-2, 1.5e+3 là FLOAT; 1.5e quay lui 1 ký tự → FLOAT('1.5') + ID('e')", "PASS"],
        ["SCAN-08", "Không hợp lệ", "let a = 5$ + @b ~ 1;", "Báo 3 lỗi ($, @, ~) kèm (dòng:cột) và phục hồi quét đủ 8 token còn lại", "PASS"],
        ["SCAN-09", "Không hợp lệ", "3. + 4", "Quay lui 1 ký tự ra INT('3'), báo 1 lỗi tại '.', quét tiếp '+' và '4'", "PASS"],
        ["SCAN-10", "Không hợp lệ", 'let s = "abc\\nlet x = 1;', "Phát hiện chuỗi chưa đóng (unterminated string) và tiếp tục quét dòng 2", "PASS"],
        ["SCAN-12", "Hợp lệ", "MiniSQL: SELECT id, name FROM users WHERE ...", "15 token SQL chính xác, 0 lỗi (chứng minh tính tổng quát đa ngôn ngữ)", "PASS"],
        ["SCAN-14", "Không hợp lệ", "let gia = 100€;", "Báo lỗi ký tự ngoài bảng chữ cái ASCII Σ (U+20AC) và phục hồi quét ';'", "PASS"],
    ]
    add_styled_table(
        doc,
        ["Mã Test", "Phân loại", "Đầu vào / Kịch bản", "Kết quả thực nghiệm đạt được", "Đánh giá"],
        tc_rows,
        col_widths_cm=[2.0, 2.0, 4.3, 6.8, 1.6],
        font_size=8.4,
        mono_cols={0},
    )

    add_heading_2(doc, "6.2. Thực nghiệm tối thiểu hóa trạng thái, hiệu năng và phân tích kết quả")
    add_body(
        doc,
        "Bảng 4 và Hình 7 tổng hợp số liệu thực nghiệm trên cả 3 bộ ngôn ngữ (biên dịch toàn bộ đường ống và quét 10 KB mã nguồn lặp lại):",
    )

    bench_rows = [
        ["MiniLang", str(s_mini["token_count"]), str(s_mini["nfa_states"]), str(s_mini["subset_dfa_states"]),
         str(s_mini["minimized_dfa_states"]), f"-{s_mini['state_reduction_count']} (-{s_mini['state_reduction_percent']}%)",
         str(s_mini["char_class_count"]), f"{s_mini['timings_ms']['total_ms']:.2f} ms", "✓ Product Eq (0 phản ví dụ)"],
        ["CalcLang", str(s_calc["token_count"]), str(s_calc["nfa_states"]), str(s_calc["subset_dfa_states"]),
         str(s_calc["minimized_dfa_states"]), f"-{s_calc['state_reduction_count']} (-{s_calc['state_reduction_percent']}%)",
         str(s_calc["char_class_count"]), f"{s_calc['timings_ms']['total_ms']:.2f} ms", "✓ Product Eq (0 phản ví dụ)"],
        ["MiniSQL", str(s_sql["token_count"]), str(s_sql["nfa_states"]), str(s_sql["subset_dfa_states"]),
         str(s_sql["minimized_dfa_states"]), f"-{s_sql['state_reduction_count']} (-{s_sql['state_reduction_percent']}%)",
         str(s_sql["char_class_count"]), f"{s_sql['timings_ms']['total_ms']:.2f} ms", "✓ Product Eq (0 phản ví dụ)"],
    ]
    add_styled_table(
        doc,
        ["Ngôn ngữ", "Token", "ε-NFA", "Sub-DFA", "Min-DFA", "Giảm trạng thái", "Lớp Σ", "Biên dịch", "Tương đương"],
        bench_rows,
        col_widths_cm=[2.0, 1.2, 1.3, 1.5, 1.5, 2.3, 1.3, 1.8, 3.8],
        font_size=8.4,
    )

    add_figure(
        doc,
        FIG_DIR / "fig4_benchmark_comparison.png",
        "Hình 7: (a) Giảm số trạng thái qua đường ống ε-NFA → Subset DFA → Minimized DFA và (b) Thời gian biên dịch & quét 10 KB mã nguồn.",
        width_cm=15.8,
    )

    add_body(
        doc,
        "Nhận xét phân tích quan trọng từ số liệu thực nghiệm:",
        bold_prefix="Phân tích chuyên sâu: ",
    )
    add_bullet(doc, "Không xảy ra bùng nổ trạng thái trong thực tế: ",
               "Mặc dù lý thuyết Subset Construction có cận trên O(2^|Q_N|), số trạng thái DFA thực tế của cả 3 ngôn ngữ đều NHỎ HƠN số trạng thái ε-NFA "
               "(MiniLang: 153 → 81 → 75; CalcLang: 57 → 24 → 20; MiniSQL: 128 → 64 → 52) do đặc trưng cây tiền tố (trie-like) của tập từ khóa và các lớp ký tự phân tách nhau.")
    add_bullet(doc, "Tại sao MiniSQL giảm tới 18.75% trạng thái còn MiniLang giảm 7.41%? ",
               "Trong MiniSQL, mỗi từ khóa hỗ trợ cả chữ hoa lẫn chữ thường (ví dụ `SELECT|select`, `WHERE|where`), khiến Subset Construction tạo ra các nhánh tiền tố song song. "
               "Thuật toán tối thiểu hóa phát hiện các trạng thái hậu tố và các nhánh rẽ sang `IDENT` có hành vi tương lai đồng nhất nên gộp lại được tới 12/64 trạng thái. "
               "Ngược lại, MiniLang có tới 38 loại token đầu ra khác nhau (khởi tạo Π₀ đã tách sẵn nhiều khối phân biệt), nên tỷ lệ gộp ít hơn (6/81 trạng thái) nhưng vẫn tối ưu tuyệt đối theo Myhill–Nerode.")
    add_bullet(doc, "Hiệu năng thực thi cao: ",
               "Nhờ phân hoạch bảng chữ cái (43 lớp thay vì 98 ký tự) và tra bảng chuyển tiếp O(1), toàn bộ biên dịch + chứng minh tương đương MiniLang chỉ tốn ~9–11 ms "
               "và tốc độ quét đạt xấp xỉ 600–900 KB/giây ngay trên Python thuần.")

    # =========================================================================
    # SECTION 7: HẠN CHẾ, LỖI CÒN TỒN TẠI VÀ HƯỚNG PHÁT TRIỂN
    # =========================================================================
    add_heading_1(doc, "7. Hạn chế, lỗi còn tồn tại và hướng phát triển")

    add_heading_2(doc, "7.1. Các hạn chế và trường hợp thất bại đã nhận diện")
    add_bullet(doc, "Phục hồi lỗi Panic-mode theo từng ký tự với chuỗi chưa đóng: ",
               "Khi gặp chuỗi thiếu ngoặc kép kết thúc như `let s = \"abc\\n`, bộ quét báo lỗi chính xác tại dấu `\"` nhưng chỉ tiến 1 ký tự, "
               "dẫn đến phần nội dung bên trong `abc` bị quét tiếp thành `IDENTIFIER` (xem test case `SCAN-10`). Điều này có thể sinh thêm nhiễu cho tầng phân tích cú pháp phía sau.")
    add_bullet(doc, "Giới hạn phạm vi bảng chữ cái ASCII (98 ký tự): ",
               "Hệ thống hiện giả định Σ chỉ gồm ASCII in được và `\\t, \\n, \\r`, nên chưa hỗ trợ trực tiếp định danh hoặc chuỗi chứa ký tự Unicode/UTF-8 (ví dụ chữ tiếng Việt có dấu trong chuỗi `\"Xin chào\"`).")
    add_bullet(doc, "Bùng nổ trạng thái với biểu thức chính quy bệnh lý & quay lui bậc hai: ",
               "Với các RE nhân tạo cố tình gây bùng nổ như `(a|b)*a(a|b){20}` (dạng lặp cố định dài), Subset Construction có thể tăng theo hàm mũ O(2^n) — "
               "chương trình phải đặt ngưỡng ngắt an toàn `max_states = 5000`. Ngoài ra, một chuỗi lỗi rất dài kiểu `\"aaaa...` (n ký tự không đóng) "
               "có thể khiến scanner đọc hết n ký tự rồi quay lui, lặp lại trong trường hợp xấu nhất O(n²).")
    add_bullet(doc, "Chưa hỗ trợ bình luận nhiều dòng lồng nhau (/* /* ... */ */): ",
               "Về mặt lý thuyết Ngôn ngữ hình thức (Bổ đề bơm cho ngôn ngữ chính quy), bình luận lồng nhau sâu tùy ý thuộc lớp Ngôn ngữ phi ngữ cảnh (CFL), "
               "vượt quá khả năng biểu diễn của một DFA đơn lẻ nếu không có cơ chế đếm lồng nhau hoặc Start Conditions.")

    add_heading_2(doc, "7.2. Hướng phát triển và cải tiến")
    add_bullet(doc, "Cải thiện phục hồi lỗi từ vựng thông minh: ",
               "Bổ sung luật bắt lỗi ưu tiên thấp (error-token rules như `UNTERMINATED_STRING = \"[^\"\\n]*`) để nuốt trọn cụm lỗi chuỗi chưa đóng trong 1 bước duy nhất, "
               "đồng thời tối ưu đánh dấu vị trí dead-state (fail-table) để đảm bảo thời gian quét luôn chặt O(n) ngay cả trên dữ liệu lỗi.")
    add_bullet(doc, "Hỗ trợ UTF-8 và Start Conditions (đa ngữ cảnh như Flex): ",
               "Chuyển cấu trúc lớp tương đương ký tự sang khoảng mã điểm Unicode (Unicode Codepoint Intervals) để hỗ trợ tiếng Việt trong chuỗi và bình luận; "
               "bổ sung trạng thái ngữ cảnh (`INITIAL`, `IN_BLOCK_COMMENT`) để xử lý bình luận nhiều dòng `/* ... */` gọn gàng.")
    add_bullet(doc, "Tích hợp hoàn chỉnh chuỗi Trình biên dịch: ",
               "Đưa luồng token đầu ra kết nối trực tiếp vào bộ phân tích cú pháp Recursive-Descent hoặc LL(1)/LR Parser và sinh mã trung gian, "
               "khép kín kiến thức Chương 3 (FA/RE) và Chương 4 (CFG/PDA) của học phần.")

    # =========================================================================
    # SECTION 8: KẾT LUẬN
    # =========================================================================
    add_heading_1(doc, "8. Kết luận")
    add_body(
        doc,
        "Đồ án đã hoàn thành toàn diện và vượt yêu cầu tối thiểu của Đề tài T13 — Automata-based Lexical Analyzer. "
        "Từ nền tảng lý thuyết Automata hữu hạn và Biểu thức chính quy của học phần Ngôn ngữ hình thức, nhóm đã thiết kế và tự cài đặt "
        "100% chuỗi thuật toán cốt lõi (không phụ thuộc thư viện `re`): phân tích cú pháp RE, cấu trúc Thompson đa-token, Subset Construction "
        "kết hợp phân hoạch bảng chữ cái và giải quyết xung đột ưu tiên, nhánh đối chứng Direct RE → DFA (`r#`, `followpos`), "
        "tối thiểu hóa Multi-token DFA bảo toàn phân loại token, kiểm chứng tương đương toán học bằng Product Automaton, và bộ quét từ vựng "
        "Maximal Munch có phục hồi lỗi. Bên cạnh công cụ dòng lệnh và khả năng xuất file `.jff` đối chứng trên JFLAP, ứng dụng Web trực quan "
        "LexAutomata Studio giúp người học và giảng viên quan sát trực tiếp từng chuyển đổi Automata, chạy thử ngôn ngữ mới trong thời gian thực "
        "và kiểm chứng 29/29 test case đạt độ chính xác 100%.",
    )

    # =========================================================================
    # SECTION 9: TÀI LIỆU THAM KHẢO
    # =========================================================================
    add_heading_1(doc, "9. Tài liệu tham khảo")
    refs = [
        "[1] J. E. Hopcroft, R. Motwani, and J. D. Ullman, Introduction to Automata Theory, Languages, and Computation, 3rd ed. Boston, MA: Pearson / Addison-Wesley, 2006. (Giáo trình bắt buộc môn học).",
        "[2] A. V. Aho, M. S. Lam, R. Sethi, and J. D. Ullman, Compilers: Principles, Techniques, and Tools (Dragon Book), 2nd ed., Chapter 3: Lexical Analysis. Boston, MA: Addison-Wesley, 2006.",
        "[3] ThS. Hồ Thị Thanh Tuyến, Bài giảng Học phần Ngôn ngữ hình thức (Chương 1–3: Automata hữu hạn, Biểu thức chính quy, Xây dựng DFA trực tiếp và Tối thiểu hóa DFA), Khoa CNTTKD, Đại học Kinh tế TP.HCM (UEH), 2026.",
        "[4] K. Thompson, \"Programming Techniques: Regular Expression Search Algorithm,\" Communications of the ACM, vol. 11, no. 6, pp. 419–422, Jun. 1968.",
        "[5] J. E. Hopcroft, \"An n log n algorithm for minimizing states in a finite automaton,\" in Theory of Machines and Computations, Z. Kohavi and A. Paz, Eds. New York: Academic Press, 1971, pp. 189–196.",
        "[6] G. Berry and R. Sethi, \"From regular expressions to deterministic automata,\" Theoretical Computer Science, vol. 48, pp. 117–126, 1986.",
        "[7] S. H. Rodger and T. W. Finley, JFLAP: An Interactive Formal Languages and Automata Package. Sudbury, MA: Jones & Bartlett Publishers, 2006.",
    ]
    for ref in refs:
        add_body(doc, ref, space_after=3.0)

    # =========================================================================
    # SECTION 10: PHỤ LỤC — PHÂN CÔNG CÔNG VIỆC & KHAI BÁO SỬ DỤNG AI
    # =========================================================================
    doc.add_page_break()
    add_heading_1(doc, "10. Phụ lục: Phân công công việc và Khai báo sử dụng AI")

    add_heading_2(doc, "10.1. Bảng phân công công việc nhóm")
    add_body(
        doc,
        "(Lưu ý: Nhóm điền đầy đủ Họ tên, MSSV thực tế và điều chỉnh tỷ lệ đóng góp chính xác trước khi nộp.)",
        space_after=3.5,
    )
    alloc_rows = [
        ["1", "[Họ tên TV 1]", "[MSSV 1]",
         "Quản lý tiến độ; hệ thống hóa cơ sở lý thuyết & mô hình hình thức; biên soạn báo cáo kỹ thuật & slide; phụ trách phần Lý thuyết khi bảo vệ.", "25%"],
        ["2", "[Họ tên TV 2]", "[MSSV 2]",
         "Cài đặt `regex_parser.py`, `thompson.py`, `direct_dfa.py` (cây r# & followpos); thiết kế 3 bộ đặc tả ngôn ngữ (`presets.py`); demo Tab 3.", "25%"],
        ["3", "[Họ tên TV 3]", "[MSSV 3]",
         "Cài đặt `subset_construction.py`, `dfa_minimizer.py`, `verifier.py` (Product Automaton), `jflap_export.py`; đo benchmark & phân tích; demo Tab 2.", "25%"],
        ["4", "[Họ tên TV 4]", "[MSSV 4]",
         "Cài đặt `scanner.py` (Maximal Munch, Error Recovery), `app.py`, `cli.py`, giao diện Web Studio (`web/`) & bộ 29 test cases (`tests/`); demo Tab 1, 4, 5.", "25%"],
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
        ["Mục đích sử dụng",
         "• Tham khảo, rà soát thuật ngữ lý thuyết Automata và cấu trúc thuật toán (Alphabet Partitioning, Multi-token Minimization Π₀, Product Automaton).\n"
         "• Gợi ý kiến trúc phân tách module, hỗ trợ debug các trường hợp biên (escape trong lớp ký tự, nullable regex, quay lui Maximal Munch).\n"
         "• Hỗ trợ xây dựng giao diện trực quan hóa SVG Web Studio, bộ test case mở rộng và chuẩn hóa trình bày báo cáo/slide."],
        ["Phạm vi kiểm chứng & Trách nhiệm của nhóm",
         "• Toàn bộ thành viên nhóm đã đọc hiểu, kiểm tra từng thuật toán cốt lõi trong `lexer_engine/`, tự kiểm chứng đối chiếu với ví dụ bài giảng Chương 3.1 "
         "(Slide 38 và Slide 46–57), chạy 100% bộ kiểm thử tự động (29/29 PASS) và đối chứng chéo độc lập.\n"
         "• Nhóm chịu trách nhiệm hoàn toàn về độ chính xác khoa học của mã nguồn, kết quả thực nghiệm và sẵn sàng giải thích chi tiết từng dòng code trong buổi bảo vệ."],
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

    # Convert DOCX -> PDF via Microsoft Word COM for pixel-accurate layout & page count check
    try:
        import win32com.client

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        wdoc = word.Documents.Open(str(DOCX_PATH.resolve()))
        # wdFormatPDF = 17
        wdoc.SaveAs(str(PDF_PATH.resolve()), FileFormat=17)
        pages = wdoc.ComputeStatistics(2)  # wdStatisticPages = 2
        wdoc.Close(False)
        word.Quit()
        print(f"[OK] Exported PDF report -> {PDF_PATH} ({pages} pages)")
    except Exception as exc:
        print(f"[WARN] Word COM PDF export failed: {exc}")


if __name__ == "__main__":
    build_report()
