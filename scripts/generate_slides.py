# -*- coding: utf-8 -*-
"""
Generate the 16:9 widescreen PowerPoint Presentation Deck (13 Slides)
for Topic T13: Automata-based Lexical Analyzer (UEH Formal Languages).

Output:
  deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx
"""

from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = PROJECT_ROOT / "deliverables" / "figures"
OUT_DIR = PROJECT_ROOT / "deliverables"
PPTX_PATH = OUT_DIR / "Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx"

# Palette — UEH Academic Sapphire & Slate
C_NAVY = RGBColor(0x0F, 0x17, 0x2A)
C_UEH = RGBColor(0x1E, 0x3A, 0x8A)
C_BLUE = RGBColor(0x25, 0x63, 0xEB)
C_SKY = RGBColor(0x38, 0xBD, 0xF8)
C_BG = RGBColor(0xF8, 0xFA, 0xFC)
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
C_TEXT = RGBColor(0x0F, 0x17, 0x2A)
C_MUTED = RGBColor(0x47, 0x55, 0x69)
C_BORDER = RGBColor(0xCB, 0xD5, 0xE1)
C_GREEN = RGBColor(0x05, 0x96, 0x69)
C_GREEN_BG = RGBColor(0xEC, 0xFD, 0xF5)
C_AMBER = RGBColor(0xD9, 0x77, 0x06)
C_AMBER_BG = RGBColor(0xFF, 0xFB, 0xEB)
C_BLUE_BG = RGBColor(0xEF, 0xF6, 0xFF)
C_ROSE = RGBColor(0xDC, 0x26, 0x26)
C_ROSE_BG = RGBColor(0xFE, 0xF2, 0xF2)
C_PURPLE = RGBColor(0x7C, 0x3A, 0xED)
C_PURPLE_BG = RGBColor(0xF5, 0xF3, 0xFF)

FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"


def set_bg(slide, color: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, fill_color, border_color=None, border_pt=1.0, rounded=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, Inches(left), Inches(top), Inches(width), Inches(height))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    if border_color is not None:
        shp.line.color.rgb = border_color
        shp.line.width = Pt(border_pt)
    else:
        shp.line.fill.background()
    if rounded and len(shp.adjustments) > 0:
        shp.adjustments[0] = 0.06
    return shp


def add_text(
    slide,
    left,
    top,
    width,
    height,
    text: str,
    size: float = 14,
    bold: bool = False,
    italic: bool = False,
    color: RGBColor = C_TEXT,
    align=PP_ALIGN.LEFT,
    font_name: str = FONT_MAIN,
    valign=MSO_ANCHOR.TOP,
):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = font_name
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return tb


def add_bullets(
    slide,
    left,
    top,
    width,
    height,
    items: list[tuple[str, str]],
    size: float = 13.5,
    space_after: float = 6,
    bullet_char: str = "• ",
    lead_color: RGBColor = C_UEH,
    text_color: RGBColor = C_TEXT,
):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.06)
    tf.margin_right = Inches(0.06)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    for idx, (lead, body) in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = 1.18
        r0 = p.add_run()
        r0.text = bullet_char
        r0.font.name = FONT_MAIN
        r0.font.size = Pt(size)
        r0.font.bold = True
        r0.font.color.rgb = C_BLUE
        if lead:
            r1 = p.add_run()
            r1.text = lead
            r1.font.name = FONT_MAIN
            r1.font.size = Pt(size)
            r1.font.bold = True
            r1.font.color.rgb = lead_color
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_MAIN
        r2.font.size = Pt(size)
        r2.font.color.rgb = text_color
    return tb


def add_header(slide, section_tag: str, title: str, slide_num: int, total_slides: int = 13) -> None:
    set_bg(slide, C_BG)
    add_rect(slide, 0, 0, 13.333, 0.88, C_UEH)
    add_rect(slide, 0, 0.88, 13.333, 0.05, C_SKY)
    pill_w = max(2.35, min(3.8, len(section_tag) * 0.105 + 0.55))
    add_rect(slide, 0.45, 0.14, pill_w, 0.28, C_BLUE, rounded=True)
    add_text(
        slide,
        0.45,
        0.14,
        pill_w,
        0.28,
        section_tag,
        size=10,
        bold=True,
        color=C_WHITE,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )
    add_text(slide, 0.45, 0.44, 11.8, 0.40, title, size=20, bold=True, color=C_WHITE)
    add_rect(slide, 0, 7.16, 13.333, 0.34, C_WHITE, border_color=C_BORDER, border_pt=0.5)
    add_text(
        slide,
        0.45,
        7.19,
        9.5,
        0.28,
        "UEH · Học phần Ngôn ngữ hình thức · Đề tài T13: Automata-based Lexical Analyzer",
        size=10,
        color=C_MUTED,
        valign=MSO_ANCHOR.MIDDLE,
    )
    add_text(
        slide,
        11.4,
        7.19,
        1.5,
        0.28,
        f"Trang {slide_num} / {total_slides}",
        size=10,
        bold=True,
        color=C_UEH,
        align=PP_ALIGN.RIGHT,
        valign=MSO_ANCHOR.MIDDLE,
    )


def add_picture_fit(slide, img_path: Path, left: float, top: float, max_w: float, max_h: float):
    """Insert an image centered inside (left, top, max_w, max_h) preserving aspect ratio."""
    from PIL import Image

    with Image.open(img_path) as im:
        iw, ih = im.size
    aspect = iw / ih
    if max_w / max_h > aspect:
        h = max_h
        w = h * aspect
    else:
        w = max_w
        h = w / aspect
    x = left + (max_w - w) / 2.0
    y = top + (max_h - h) / 2.0
    return slide.shapes.add_picture(str(img_path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))


def add_styled_table(slide, left, top, width, height, headers, rows, col_widths, font_size=11):
    tbl_shape = slide.shapes.add_table(
        1 + len(rows), len(headers), Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tbl = tbl_shape.table
    for ci, w in enumerate(col_widths):
        tbl.columns[ci].width = Inches(w)

    for ci, h in enumerate(headers):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_UEH
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = h
        r.font.name = FONT_MAIN
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = C_WHITE

    for ri, rv in enumerate(rows):
        bg = C_WHITE if ri % 2 == 0 else RGBColor(0xF1, 0xF5, 0xF9)
        for ci, val in enumerate(rv):
            cell = tbl.cell(ri + 1, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ci in (0, 2, 3) and len(headers) <= 5 else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(val)
            r.font.name = FONT_MAIN
            r.font.size = Pt(font_size - 0.5)
            r.font.color.rgb = C_GREEN if "PASS" in str(val) or "OK" in str(val) else C_TEXT
            if "PASS" in str(val) or "OK" in str(val):
                r.font.bold = True
    return tbl_shape


def build_slides() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    TOTAL = 13

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank)
    set_bg(s1, C_NAVY)
    add_rect(s1, 0, 0, 0.28, 7.5, C_SKY)
    add_rect(s1, 0.28, 0, 13.053, 0.10, C_BLUE)
    add_rect(
        s1,
        8.9,
        0.6,
        4.0,
        6.3,
        RGBColor(0x16, 0x24, 0x47),
        border_color=RGBColor(0x2B, 0x45, 0x80),
        border_pt=1.2,
        rounded=True,
    )

    add_text(s1, 0.85, 0.65, 7.8, 0.4, "TRƯỜNG ĐẠI HỌC KINH TẾ TP. HỒ CHÍ MINH (UEH)", size=13, bold=True, color=C_SKY)
    add_text(
        s1,
        0.85,
        1.02,
        7.8,
        0.35,
        "KHOA CÔNG NGHỆ THÔNG TIN KINH DOANH · HỌC PHẦN NGÔN NGỮ HÌNH THỨC",
        size=11.5,
        color=RGBColor(0xCB, 0xD5, 0xE1),
    )

    add_rect(s1, 0.85, 1.70, 2.35, 0.40, C_SKY, rounded=True)
    add_text(
        s1,
        0.85,
        1.70,
        2.35,
        0.40,
        "ĐỀ TÀI T13 — TIỂU LUẬN CK",
        size=11.5,
        bold=True,
        color=C_NAVY,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )

    add_text(s1, 0.85, 2.25, 7.9, 1.35, "AUTOMATA-BASED\nLEXICAL ANALYZER", size=38, bold=True, color=C_WHITE)
    add_text(
        s1,
        0.85,
        3.72,
        7.7,
        0.95,
        "Xây dựng Bộ phân tích từ vựng tổng quát theo quy trình khép kín của Định lý Kleene:\n"
        "RE (Unicode động Σ(U)) ⇄ ε-NFA · Khử ε · Subset/Direct DFA · Moore/Hopcroft · GNFA & Sinh mã Lexer",
        size=13.8,
        italic=True,
        color=RGBColor(0xBF, 0xDB, 0xFE),
    )

    add_rect(s1, 0.85, 4.92, 7.5, 0.03, C_SKY)
    add_text(s1, 0.85, 5.15, 7.5, 0.35, "Giảng viên hướng dẫn: ThS. Hồ Thị Thanh Tuyến", size=14, bold=True, color=C_WHITE)
    add_text(
        s1,
        0.85,
        5.52,
        7.5,
        0.35,
        "Mã lớp học phần: 26C1INF50915301  |  TP. Hồ Chí Minh, 11/2026",
        size=12.5,
        color=RGBColor(0x94, 0xA3, 0xB8),
    )

    add_text(s1, 9.15, 0.85, 3.5, 0.4, "TÓM TẮT NỘI DUNG ĐỒ ÁN", size=13, bold=True, color=C_SKY)
    add_bullets(
        s1,
        9.15,
        1.35,
        3.55,
        3.0,
        [
            ("Không dùng import re: ", "128 ASCII (~(~A)=A), Unicode động Σ(U) (nếu, €), giới hạn AST ≤4096."),
            ("Định lý Kleene (7 mô hình): ", "Thompson → Khử ε → Subset/Direct → Moore/Hopcroft → GNFA RE."),
            ("Kiểm chứng & Ma trận giao: ", "Myhill–Nerode + Ma trận L(Rᵢ)∩L(Rⱼ) kèm chứng nhân ngắn nhất."),
            ("Quét O(n) & Sinh mã Lexer: ", "Reps (1998), xuất Lexer độc lập (.py), 72/72 PASS + 22 Suites."),
        ],
        size=11.3,
        space_after=7,
        lead_color=C_SKY,
        text_color=C_WHITE,
    )
    add_rect(s1, 9.15, 4.55, 3.5, 0.02, RGBColor(0x38, 0x54, 0x94))
    add_text(s1, 9.15, 4.72, 3.5, 0.35, "NHÓM THỰC HIỆN (NHÓM 6)", size=12, bold=True, color=C_SKY)
    add_text(
        s1,
        9.15,
        5.10,
        3.5,
        1.65,
        "1. [Họ tên Thành viên 1] — [MSSV]\n"
        "2. [Họ tên Thành viên 2] — [MSSV]\n"
        "3. [Họ tên Thành viên 3] — [MSSV]\n"
        "4. [Họ tên Thành viên 4] — [MSSV]",
        size=11.5,
        color=RGBColor(0xE2, 0xE8, 0xF0),
    )

    # =========================================================================
    # SLIDE 2: BÀI TOÁN & MỤC TIÊU
    # =========================================================================
    s2 = prs.slides.add_slide(blank)
    add_header(s2, "01 · ĐẶT VẤN ĐỀ", "Bài toán Phân tích từ vựng và Mục tiêu Đồ án T13", 2, TOTAL)

    add_rect(s2, 0.45, 1.18, 6.1, 5.72, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s2, 0.70, 1.35, 5.6, 0.4, "Mối liên hệ giữa Ngôn ngữ hình thức và Trình biên dịch", size=15.0, bold=True, color=C_UEH)
    add_bullets(
        s2,
        0.70,
        1.85,
        5.6,
        3.4,
        [
            (
                "Vai trò Lexical Analyzer: ",
                "Chuyển dòng ký tự mã nguồn thành luồng token (từ khóa, định danh, số, chuỗi UTF-8/CRLF, toán tử), lọc khoảng trắng/bình luận (// và /*...*/) và báo lỗi kèm (dòng, cột).",
            ),
            (
                "Vì sao dùng Automata hữu hạn? ",
                "Các lớp token thuộc lớp Ngôn ngữ chính quy — đặc tả bằng Biểu thức chính quy (RE) và nhận diện bằng DFA trong thời gian tuyến tính O(n), tránh ReDoS O(2^n).",
            ),
            (
                "Hạn chế khi viết thủ công: ",
                "Viết nhánh if/else cố định khó mở rộng cho ngôn ngữ mới; còn gọi thư viện dựng sẵn re không thể hiện được các bước biến đổi của Định lý Kleene.",
            ),
        ],
        size=12.5,
        space_after=9,
    )
    add_rect(s2, 0.70, 5.45, 5.6, 1.18, C_BLUE_BG, border_color=C_BLUE, border_pt=1.2, rounded=True)
    add_text(
        s2,
        0.85,
        5.58,
        5.3,
        0.95,
        "Quy trình chuyển đổi hai chiều theo Định lý Kleene (Chương 3.1):\n"
        "RE  ⇄  ε-NFA  ⇄  NFA khử ε  ⇄  Subset/Direct DFA  ⇄  Min-DFA  ⇄  GNFA RE",
        size=12.0,
        bold=True,
        color=C_UEH,
        valign=MSO_ANCHOR.MIDDLE,
    )

    add_rect(s2, 6.78, 1.18, 6.1, 5.72, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s2, 7.03, 1.35, 5.6, 0.4, "4 Mục tiêu chính của Đồ án Nhóm 6", size=15.5, bold=True, color=C_GREEN)

    goals = [
        (
            "1",
            C_BLUE,
            C_BLUE_BG,
            "Không dùng import re · Đại số Σ(U) & Giới hạn AST",
            "Bao phủ 128 ASCII (~(~A)=A), phân hoạch Unicode động Σ(U) (nếu, €), chặn (((a{64}){64}){64}) ≤ 4096 nút.",
        ),
        (
            "2",
            C_PURPLE,
            C_PURPLE_BG,
            "Định lý Kleene (GNFA) & Ma trận giao L(Rᵢ)∩L(Rⱼ)",
            "Thompson, Khử ε, Subset, Direct r#, Moore/Hopcroft, GNFA (DFA→RE), Myhill–Nerode & chứng nhân giao nhau.",
        ),
        (
            "3",
            C_AMBER,
            C_AMBER_BG,
            "Bộ quét O(n) Reps (1998) & Sinh mã Lexer (.py)",
            "Bảng nhớ failed_states tránh O(n²), STRING_LIT xử lý đúng CRLF, xuất tệp Lexer Python độc lập kiểu Flex.",
        ),
        (
            "4",
            C_GREEN,
            C_GREEN_BG,
            "Giao diện Web 5 Tab & 72/72 Test Cases + 22 Suites",
            "3 ngôn ngữ (MiniLang 39, CalcLang 12, MiniSQL 14), đối chứng đầu ra giữa bộ phân tích gốc & Lexer sinh mã.",
        ),
    ]
    for i, (num, col, bgc, g_title, g_desc) in enumerate(goals):
        y = 1.92 + i * 1.18
        add_rect(s2, 7.03, y, 5.6, 1.03, bgc, border_color=col, border_pt=1.0, rounded=True)
        add_rect(s2, 7.18, y + 0.22, 0.52, 0.56, col, rounded=True)
        add_text(
            s2,
            7.18,
            y + 0.22,
            0.52,
            0.56,
            num,
            size=16,
            bold=True,
            color=C_WHITE,
            align=PP_ALIGN.CENTER,
            valign=MSO_ANCHOR.MIDDLE,
        )
        add_text(s2, 7.82, y + 0.08, 4.65, 0.32, g_title, size=12.4, bold=True, color=col)
        add_text(s2, 7.82, y + 0.40, 4.65, 0.55, g_desc, size=10.9, color=C_TEXT)

    # =========================================================================
    # SLIDE 3: MÔ HÌNH HÌNH THỨC & MỞ RỘNG ĐA-TOKEN
    # =========================================================================
    s3 = prs.slides.add_slide(blank)
    add_header(s3, "02 · MÔ HÌNH HÌNH THỨC", "Mô hình Đa-Token, Phân hoạch Unicode động Σ(U) và Ma trận giao L(Rᵢ)∩L(Rⱼ)", 3, TOTAL)

    cards3 = [
        (
            0.45,
            C_BLUE,
            C_BLUE_BG,
            "1. Combined ε-NFA & Khử ε (ĐL 2)",
            "N_lex = (Q_N, Σ(U), δ_N, q_start, F_N, τ_N)\n\n"
            "• Dựng N(Rᵢ) rời nhau; nối q_start --ε--> s₁..sₖ.\n"
            "• Khử ε (Định lý 2, Slide 21–22):\n"
            "  δ'(p,a) = ε-closure(Move(ε-closure({p}),a))\n"
            "• MiniLang giảm 170 → 96 trạng thái.",
        ),
        (
            4.65,
            C_AMBER,
            C_AMBER_BG,
            "2. Subset DFA & Ma trận L(Rᵢ)∩L(Rⱼ)",
            "D_lex = (Q_D, Σ(U)/≡, δ_D, D₀, F_D, τ_D)\n\n"
            "• Σ(U)/≡ gom thành 44 lớp tương đương.\n"
            "• Phân tích tĩnh C(39,2) = 741 cặp quy tắc:\n"
            "  xác định 9 cặp KW_*/BOOL ⊂ IDENTIFIER\n"
            "  kèm chứng nhân ('if'..'true') & 0 che khuất.",
        ),
        (
            8.85,
            C_GREEN,
            C_GREEN_BG,
            "3. Moore/Hopcroft & GNFA (DFA→RE)",
            "Phân hoạch Π₀ = {Q\\F} ∪ {F_{T₁}..F_{Tₘ}}\n\n"
            "• Moore O(p·|Q|²) & Hopcroft O(p·|Q|log|Q|).\n"
            "• Myhill–Nerode: 3003/3003 cặp phân biệt.\n"
            "• GNFA State Elimination (DFA → RE):\n"
            "  kiểm tra tự động L(R_gốc) ≡ L(R_sinh).",
        ),
    ]
    for x, col, bgc, heading, body in cards3:
        add_rect(s3, x, 1.18, 4.03, 3.65, C_WHITE, border_color=col, border_pt=1.5, rounded=True)
        add_rect(s3, x, 1.18, 4.03, 0.48, col, rounded=False)
        add_text(s3, x + 0.12, 1.21, 3.8, 0.42, heading, size=13.3, bold=True, color=C_WHITE, valign=MSO_ANCHOR.MIDDLE)
        add_text(s3, x + 0.16, 1.76, 3.72, 2.95, body, size=12.0, color=C_TEXT)

    add_rect(s3, 0.45, 5.05, 12.43, 1.88, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(
        s3,
        0.70,
        5.18,
        11.9,
        0.35,
        "Bảng chữ cái Unicode động Σ(U), Phép bù ~(~A) = A và Giới hạn kích thước AST",
        size=14,
        bold=True,
        color=C_UEH,
    )
    add_bullets(
        s3,
        0.70,
        5.56,
        11.9,
        1.28,
        [
            (
                "Σ(U) = 128 ASCII (0x00..0x7F) ∪ U ∪ {NON_ASCII (U+FDD0)}: ",
                "Tách riêng ký tự Unicode tường minh U (như nếu, €, [^€]) khỏi phần còn lại NON_ASCII, giữ đúng tính đối hợp ~(~A) = A.",
            ),
            (
                "Giới hạn số nút AST lồng nhau (MAX_AST_NODES = 4096): ",
                "Dừng sớm (<0.1 ms) các biểu thức định lượng lồng nhau như (((a{64}){64}){64}) (528.483 nút) trước khi cấp phát bộ nhớ.",
            ),
            (
                "STRING_LIT xử lý đúng CRLF & Nullable Guard: ",
                "Loại trừ cả \\r và \\n trên Windows CRLF; kiểm soát ε ∈ L(Rᵢ) đảm bảo con trỏ quét luôn tiến.",
            ),
        ],
        size=11.4,
        space_after=4,
    )

    # =========================================================================
    # SLIDE 4: KIẾN TRÚC TỔNG THỂ
    # =========================================================================
    s4 = prs.slides.add_slide(blank)
    add_header(s4, "03 · KIẾN TRÚC HỆ THỐNG", "Quy trình Biên dịch Automata theo Định lý Kleene và Sinh mã Lexer", 4, TOTAL)

    add_rect(s4, 0.45, 1.12, 12.43, 4.55, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s4, FIG_DIR / "fig1_architecture_pipeline.png", 0.58, 1.20, 12.17, 4.38)

    chips = [
        (
            0.45,
            C_BLUE,
            "Chuỗi biến đổi Chương 3.1",
            "Thompson ε-NFA → NFA khử ε (ĐL 2) → Subset DFA (44 lớp Σ) → Moore & Hopcroft Min-DFA.",
        ),
        (
            4.65,
            C_PURPLE,
            "Direct DFA & GNFA (DFA → RE)",
            "Cây cú pháp r·# (followpos) + Khử trạng thái GNFA (Min-DFA → R_sinh, kiểm tra R₀ ≡ R_sinh).",
        ),
        (
            8.85,
            C_GREEN,
            "Ma trận L(Rᵢ)∩L(Rⱼ) & Sinh mã Lexer",
            "Phân tích giao nhau từng cặp kèm chứng nhân + Xuất tệp Lexer Python độc lập (.py) tốc độ O(n).",
        ),
    ]
    for x, col, t, d in chips:
        add_rect(s4, x, 5.82, 4.03, 1.15, C_WHITE, border_color=col, border_pt=1.3, rounded=True)
        add_text(s4, x + 0.14, 5.88, 3.76, 0.30, t, size=12.4, bold=True, color=col)
        add_text(s4, x + 0.14, 6.18, 3.76, 0.72, d, size=10.9, color=C_MUTED)

    # =========================================================================
    # SLIDE 5: ĐƯỜNG ỐNG CHUẨN (SLIDE 38 VERIFICATION + GNFA)
    # =========================================================================
    s5 = prs.slides.add_slide(blank)
    add_header(s5, "04 · THUẬT TOÁN CỐT LÕI (1/2)", "RE → Thompson → Khử ε → Subset → Min-DFA → GNFA RE (Slide 38 UEH)", 5, TOTAL)

    add_rect(s5, 0.45, 1.14, 8.25, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s5, FIG_DIR / "fig2_slide38_pipeline.png", 0.55, 1.22, 8.05, 5.65)

    add_rect(s5, 8.90, 1.14, 3.98, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s5, 9.10, 1.30, 3.6, 0.4, "Đối chiếu trên mẫu (a|b)*abb", size=14.5, bold=True, color=C_UEH)
    add_bullets(
        s5,
        9.10,
        1.78,
        3.6,
        4.9,
        [
            ("Thompson ε-NFA (11 TT): ", "in-deg(start)=0, out-deg(end)=0 → tạo ra q0..q10 khớp Slide 38."),
            ("Khử ε — Định lý 2 (6 TT): ", "Loại bỏ toàn bộ cung ε theo Slide 21–22, giảm từ 11 xuống 6 TT."),
            ("Subset → Min-DFA (5→4 TT): ", "Gộp D0 ≡ D2 còn 4 TT tối giản; đủ 6/6 cặp có chuỗi phân biệt Myhill–Nerode."),
            ("GNFA (DFA → RE): ", "Khử lần lượt D2, D0, D3, D1 sinh b*a(a|ba|bb(a|b+a))*bb ≡ (a|b)*abb."),
        ],
        size=11.7,
        space_after=8,
    )

    # =========================================================================
    # SLIDE 6: NHÁNH ĐỐI CHỨNG DIRECT RE -> DFA
    # =========================================================================
    s6 = prs.slides.add_slide(blank)
    add_header(s6, "04 · THUẬT TOÁN CỐT LÕI (2/2)", "Nhánh đối chứng: Direct RE → DFA đơn lẻ và Đa-Token (Slide 46–57)", 6, TOTAL)

    add_rect(s6, 0.45, 1.14, 7.15, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(
        s6,
        0.62,
        1.22,
        6.8,
        0.30,
        "Giao diện Web Tab 3: Cây cú pháp r·#, Bảng followpos, Kiểm tra Kleene & 6 Giai đoạn",
        size=11.4,
        bold=True,
        color=C_UEH,
    )
    add_picture_fit(s6, FIG_DIR / "fig7_web_direct_re_lab.png", 0.55, 1.56, 6.95, 5.30)

    add_rect(s6, 7.80, 1.14, 5.08, 3.15, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s6, FIG_DIR / "fig5_direct_dfa_slide46.png", 7.90, 1.22, 4.88, 3.0)

    add_rect(s6, 7.80, 4.46, 5.08, 2.50, C_GREEN_BG, border_color=C_GREEN, border_pt=1.3, rounded=True)
    add_text(s6, 7.98, 4.58, 4.75, 0.34, "Kết quả trên r = (a|ba)(a|b)*ba# & Đa-Token", size=12.8, bold=True, color=C_GREEN)
    add_bullets(
        s6,
        7.98,
        4.96,
        4.75,
        1.9,
        [
            ("Đối chiếu Slide 54: ", "8 lá; followpos(1)=3=4=5={4,5,6}, (2)={3}, (6)={7}, (7)={8}."),
            ("Direct DFA (5 TT A..E): ", "Dựng trực tiếp 5 trạng thái tối giản không qua ε-NFA."),
            ("Mở rộng Đa-Token (Rᵢ·#ᵢ): ", "Combined Direct DFA tương đương Min-DFA (MiniLang: 79 TT, CalcLang: 20, MiniSQL: 52)."),
        ],
        size=11.3,
        space_after=5,
        lead_color=C_GREEN,
    )

    # =========================================================================
    # SLIDE 7: COMBINED MULTI-TOKEN DFA (CALCLANG 20 STATES)
    # =========================================================================
    s7 = prs.slides.add_slide(blank)
    add_header(s7, "05 · TRỰC QUAN HÓA AUTOMATA", "Đồ thị Combined Minimized DFA — Ngôn ngữ CalcLang (20 trạng thái)", 7, TOTAL)

    add_rect(s7, 0.45, 1.14, 7.75, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s7, FIG_DIR / "fig3_calclang_combined_dfa.png", 0.55, 1.20, 7.55, 5.70)

    add_rect(s7, 8.40, 1.14, 4.48, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s7, 8.62, 1.32, 4.1, 0.4, "Phân tích quy tắc trên đồ thị DFA", size=14.5, bold=True, color=C_UEH)
    add_bullets(
        s7,
        8.62,
        1.82,
        4.08,
        3.7,
        [
            ("Giảm số trạng thái: ", "ε-NFA (57) → NFA khử ε (26) → Subset DFA (24) → Moore & Hopcroft Min-DFA (20, giảm -16.7%)."),
            ("Kiểm tra Myhill–Nerode: ", "Toàn bộ C(20, 2) = 190/190 cặp trạng thái đều có chuỗi phân biệt ngắn nhất w."),
            ("Từ khóa & Định danh: ", "KW_LET ⊂ ID (giao nhau trên 'let') nhưng được chọn nhờ Priority; đọc thêm chữ/số → rẽ về ID (Maximal Munch)."),
            ("Số thực & Quay lui: ", "D0 --[0-9]--> INT --'.'--> trung gian --[0-9]--> FLOAT. Gặp '3.' quay lui về INT('3')."),
        ],
        size=11.7,
        space_after=7,
    )
    add_rect(s7, 8.62, 5.70, 4.05, 1.05, C_PURPLE_BG, border_color=C_PURPLE, border_pt=1.1, rounded=True)
    add_text(
        s7,
        8.75,
        5.78,
        3.8,
        0.9,
        "Xuất & Đọc ngược JFLAP (.jff):\nBảo toàn cả ký tự điều khiển ASCII (\\v, \\f, \\0)\nvà Unicode động Σ(U) khi chuyển đổi XML.",
        size=11.0,
        bold=True,
        color=C_PURPLE,
        valign=MSO_ANCHOR.MIDDLE,
    )

    # =========================================================================
    # SLIDE 8: SCANNER MAXIMAL MUNCH O(n) & CODEGEN
    # =========================================================================
    s8 = prs.slides.add_slide(blank)
    add_header(s8, "06 · BỘ QUÉT O(n) & SINH MÃ", "Maximal Munch O(n) (Reps, 1998), Phục hồi lỗi và Sinh mã Lexer độc lập", 8, TOTAL)

    steps8 = [
        (
            0.45,
            C_BLUE,
            "1 · Maximal Munch + Bảng nhớ Reps",
            "Tra δ(cur, class[ch]) trong O(1); lưu mốc last_accept. Nếu (cur, cursor) ∈ failed_states thì cắt nhánh O(1) ngay → tránh quay lui bậc hai O(n²).",
        ),
        (
            4.65,
            C_AMBER,
            "2 · Phục hồi lỗi & Dòng CRLF",
            "STRING_LIT loại trừ cả \\r và \\n trên Windows CRLF; tùy chọn giữa Panic-mode (tiến 1 ký tự) và Smart-Sync (gom chuỗi/bình luận lỗi).",
        ),
        (
            8.85,
            C_GREEN,
            "3 · Sinh Lexer độc lập (.py) kiểu Flex",
            "cli.py codegen xuất ASCII_CLASS_MAP[128], UNICODE_CLASS_MAP, TRANSITIONS[78][44] thành 1 tệp .py độc lập (không dùng re, khớp bộ quét gốc).",
        ),
    ]
    for x, col, st_t, st_d in steps8:
        add_rect(s8, x, 1.18, 4.03, 1.95, C_WHITE, border_color=col, border_pt=1.6, rounded=True)
        add_text(s8, x + 0.16, 1.28, 3.72, 0.35, st_t, size=12.8, bold=True, color=col)
        add_text(s8, x + 0.16, 1.66, 3.72, 1.38, st_d, size=11.4, color=C_TEXT)

    add_text(
        s8,
        0.45,
        3.32,
        12.4,
        0.35,
        "Minh họa xử lý các tình huống biên và dữ liệu lỗi dài trên MiniLang (39 token):",
        size=13.8,
        bold=True,
        color=C_UEH,
    )
    add_styled_table(
        s8,
        0.45,
        3.72,
        12.43,
        3.20,
        ["Đầu vào ví dụ", "Hành vi của Bộ quét Minimized DFA O(n)", "Kết quả Token / Lỗi đầu ra", "Cơ chế xử lý"],
        [
            ["ifx / a===b", "Khớp trọn 'ifx' (3 ký tự); tách '===' thành '==' + '='", "ID('ifx') / ID('a'), EQ('=='), ASSIGN('='), ID('b')", "Maximal Munch > Priority"],
            ["1.5e + 2", "D0→'1.5'(FLOAT, lưu)→'e'→' '(DEAD)→quay lui 1; lưu failed_states", "FLOAT_LIT('1.5'), ID('e'), OP_PLUS, INT('2')", "Quay lui + Bảng nhớ"],
            ['"Xin chào" / nếu_1€', "Xử lý đồng thời chuỗi UTF-8 & từ khóa Unicode động Σ(U)", "STRING_LIT('\"Xin chào\"') / TOKEN('nếu_1€')", "Phân hoạch động Σ(U)"],
            ['"Quên đóng\\r\\nlet x=1;', "STRING_LIT dừng ngay trước \\r\\n; Smart-Sync giữ nguyên dòng 2", "1 lỗi '\"Quên đóng' + giữ đúng let x = 1; (dòng 2:1)", "CRLF + Smart-Sync"],
            ['"' + '\\"' * 5000, "Chuỗi 10.000 ký tự lỗi: thực hiện 5.000 lần cắt nhánh failed_states", "Thời gian tuyến tính O(n) trên cả bộ gốc & tệp .py", "Reps (1998) + Codegen"],
        ],
        [2.05, 4.55, 3.63, 2.2],
        font_size=10.9,
    )

    # =========================================================================
    # SLIDE 9: LIVE WEB DEMO SHOWCASE
    # =========================================================================
    s9 = prs.slides.add_slide(blank)
    add_header(s9, "07 · GIAO DIỆN & DEMO", "Giao diện Web 5 Tab và Kịch bản Demo trực tiếp", 9, TOTAL)

    add_rect(s9, 0.45, 1.14, 8.45, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s9, FIG_DIR / "fig6_web_scanner_demo.png", 0.55, 1.20, 8.25, 5.70)

    add_rect(s9, 9.10, 1.14, 3.78, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s9, 9.28, 1.30, 3.45, 0.40, "Kịch bản Demo trực tiếp (4 bước)", size=14.2, bold=True, color=C_UEH)
    add_bullets(
        s9,
        9.28,
        1.78,
        3.45,
        4.0,
        [
            ("Tab 1 & Xuất Lexer (.py): ", "Quét mã UTF-8/CRLF, đổi chế độ Panic/Smart-Sync, nút Dark/Light và tải bộ quét Python độc lập."),
            ("Tab 2 (Ma trận L(Rᵢ)∩L(Rⱼ)): ", "Xem bảng giao nhau 39×39 (9/741 cặp giao nhau) & bảng chứng nhân Myhill–Nerode 3003/3003 cặp."),
            ("Tab 3 (Định lý Kleene & Slide 54): ", "Đối chiếu cây r·# Slide 54 & các bước khử trạng thái GNFA (DFA → R_sinh ≡ R_gốc)."),
            ("Tab 4 (Unicode động & Che khuất): ", "Thêm quy tắc mẫu Unicode (nếu / €) & thử tình huống quy tắc bị che khuất."),
        ],
        size=11.1,
        space_after=7,
    )
    add_rect(s9, 9.28, 5.88, 3.42, 0.88, C_BLUE_BG, border_color=C_BLUE, border_pt=1.2, rounded=True)
    add_text(
        s9,
        9.38,
        5.95,
        3.22,
        0.74,
        "Chạy bằng thư viện chuẩn Python:\npython3 app.py  |  cli.py codegen\n(Không cần cài gói phụ thuộc ngoài)",
        size=11.0,
        bold=True,
        color=C_UEH,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )

    # =========================================================================
    # SLIDE 10: KIỂM THỬ TỰ ĐỘNG & ĐỐI CHỨNG
    # =========================================================================
    s10 = prs.slides.add_slide(blank)
    add_header(s10, "08 · KIỂM THỬ & BẤT BIẾN", "Kết quả Kiểm thử tự động (72/72 PASS · 22 Suites) và Đối chứng mã sinh", 10, TOTAL)

    kpis10 = [
        (0.45, C_GREEN, "72 / 72 PASS", "Ca kiểm thử JSON (20 RE · 24 Lỗi · 28 Scan)"),
        (3.62, C_BLUE, "22 / 22 OK", "Nhóm Unittest + GNFA + ~(~A)=A"),
        (6.79, C_PURPLE, "4.519 / 4.519", "Cặp trạng thái phân biệt Myhill–Nerode"),
        (9.96, C_AMBER, "100% Khớp", "Đối chứng bộ quét gốc ≡ Standalone .py"),
    ]
    for x, col, big, sub in kpis10:
        add_rect(s10, x, 1.16, 2.92, 1.15, C_WHITE, border_color=col, border_pt=1.6, rounded=True)
        add_text(s10, x + 0.1, 1.24, 2.72, 0.52, big, size=20.5, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_text(s10, x + 0.1, 1.78, 2.72, 0.42, sub, size=10.0, color=C_MUTED, align=PP_ALIGN.CENTER)

    add_styled_table(
        s10,
        0.45,
        2.52,
        12.43,
        4.40,
        ["Nhóm kiểm thử / Bất biến", "Số lượng", "Các kịch bản & Tính chất toán học kiểm tra tự động", "Kết quả"],
        [
            ["1. Single RE, Σ(U) & GNFA", "20 cases", "(a|b)*abb, Slide 54, (nếu|lặp)_[0-9]+€, [^€\\n]+, [\\f\\v]+; đối chiếu L(R_0) ≡ L(R_sinh)", "20/20 PASS"],
            ["2. Lỗi cú pháp RE & Giới hạn AST", "24 cases", "(((a{64}){64}){64}), (a{64}){64} (>4096 nút), \\u12G4, [a-\\uffff], a{5,2}, [z-a], '[]'", "24/24 PASS"],
            ["3. Scanner, CRLF & ASCII 0..127", "28 cases", "Maximal Munch, UTF-8 \"Xin chào UEH\", \"unclosed\\r\\nlet ok=1;, \\f, \\v, /*...*/", "28/28 PASS"],
            ["4. Đại số Boole ~(~A) = A", "Char & DFA", "Đối hợp phần bù trên 128 ASCII + U + NON_ASCII và L(D) ∩ L(~D) = ∅ trên DFA", "PASS"],
            ["5. Myhill–Nerode & Ma trận giao", "898 cặp", "3003/3003 (MiniLang), 190/190 (CalcLang), 1326/1326 (MiniSQL); 9/741 cặp giao nhau tĩnh", "PASS"],
            ["6. Reps O(n) & Sinh mã Lexer", "22 Suites", "5.000 lần cắt nhánh failed_states; tệp Lexer Python độc lập khớp đầu ra bộ gốc", "22/22 OK"],
        ],
        [2.75, 1.25, 6.93, 1.5],
        font_size=11.0,
    )

    # =========================================================================
    # SLIDE 11: THỰC NGHIỆM & BENCHMARK
    # =========================================================================
    s11 = prs.slides.add_slide(blank)
    add_header(s11, "09 · THỰC NGHIỆM & PHÂN TÍCH", "Đối sánh các mô hình Otomat, Ma trận giao nhau và Hiệu năng O(n)", 11, TOTAL)

    add_rect(s11, 0.45, 1.12, 12.43, 3.85, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s11, FIG_DIR / "fig4_benchmark_comparison.png", 0.58, 1.18, 12.17, 3.72)

    insights = [
        (
            0.45,
            C_BLUE,
            "MiniLang (39 token · 44 lớp Σ)",
            "ε-NFA (170) → Khử ε (96) → Subset (86) → Direct (79) → Moore/Hopcroft Min-DFA (78, -9.3%) · 9/741 cặp giao nhau.",
        ),
        (
            4.65,
            C_GREEN,
            "Moore ≡ Hopcroft & Myhill–Nerode",
            "CalcLang (57→26→24→20, 190/190 cặp, 2/66 giao); MiniSQL (128→67→64→52, 1326/1326 cặp, 5/91 giao).",
        ),
        (
            8.85,
            C_AMBER,
            "Reps O(n) & Standalone Lexer (.py)",
            "Bảng nhớ failed_states cắt 5.000 nhánh quay lui lặp lại; xuất tệp MiniLangLexer (~527 dòng, 0 phụ thuộc).",
        ),
    ]
    for x, col, it, idesc in insights:
        add_rect(s11, x, 5.14, 4.03, 1.82, C_WHITE, border_color=col, border_pt=1.4, rounded=True)
        add_text(s11, x + 0.15, 5.24, 3.74, 0.34, it, size=12.4, bold=True, color=col)
        add_text(s11, x + 0.15, 5.62, 3.74, 1.24, idesc, size=11.2, color=C_TEXT)

    # =========================================================================
    # SLIDE 12: GIỚI HẠN LÝ THUYẾT, HƯỚNG PHÁT TRIỂN & PHÂN CÔNG
    # =========================================================================
    s12 = prs.slides.add_slide(blank)
    add_header(s12, "10 · ĐÁNH GIÁ & TỔ CHỨC NHÓM", "Giới hạn Lý thuyết (Bổ đề Bơm), Hướng phát triển và Phân công", 12, TOTAL)

    add_rect(s12, 0.45, 1.16, 6.05, 5.80, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s12, 0.68, 1.30, 5.6, 0.36, "Các vấn đề đã giải quyết & Giới hạn lý thuyết DFA", size=13.6, bold=True, color=C_ROSE)
    add_bullets(
        s12,
        0.68,
        1.70,
        5.6,
        2.40,
        [
            ("Các vấn đề kỹ thuật đã xử lý: ", "Unicode động Σ(U), bù kép ~(~A)=A trên 128 ASCII, giới hạn AST ≤4096, CRLF, GNFA (DFA→RE), Ma trận giao & Sinh mã Lexer."),
            ("Giới hạn lý thuyết của DFA (Bổ đề Bơm Chương 3.2): ", "Bình luận lồng nhau tùy ý /* /* ... */ */ tương ứng ngôn ngữ L = {a^n b^n | n≥1} (Ngôn ngữ phi ngữ cảnh - CFL, vượt bộ nhớ hữu hạn DFA)."),
        ],
        size=11.2,
        space_after=5,
        lead_color=C_ROSE,
    )
    add_rect(s12, 0.68, 4.18, 5.6, 0.02, C_BORDER)
    add_text(s12, 0.68, 4.30, 5.6, 0.36, "Hướng phát triển tiếp theo", size=13.8, bold=True, color=C_GREEN)
    add_bullets(
        s12,
        0.68,
        4.70,
        5.6,
        2.15,
        [
            ("Trạng thái ngữ cảnh từ vựng: ", "Kết hợp Start Conditions (push_state / pop_state) và biến đếm độ sâu cho bình luận lồng nhau & chuỗi nội suy."),
            ("Kết nối Parser CFG/PDA (Chương 4–5): ", "Đưa luồng Token của Lexer độc lập (.py) vào bộ phân tích cú pháp LL(1) / LR(1)."),
        ],
        size=11.3,
        space_after=5,
        lead_color=C_GREEN,
    )

    add_rect(s12, 6.72, 1.16, 6.16, 5.80, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s12, 6.95, 1.30, 5.7, 0.36, "Phân công công việc nhóm (Nhóm 6)", size=14.2, bold=True, color=C_UEH)
    add_styled_table(
        s12,
        6.95,
        1.74,
        5.70,
        2.95,
        ["Thành viên", "Phần việc phụ trách chính", "Tỷ lệ"],
        [
            ["TV 1 [Điền tên]", "Cơ sở lý thuyết Kleene, ~(~A)=A, Myhill–Nerode/Bổ đề Bơm, báo cáo", "25%"],
            ["TV 2 [Điền tên]", "RE Parser (Σ(U), ≤4096 AST), Thompson, Khử ε (ĐL 2), Direct DFA", "25%"],
            ["TV 3 [Điền tên]", "Subset, Moore/Hopcroft, GNFA (DFA→RE), Ma trận L(Rᵢ)∩L(Rⱼ)", "25%"],
            ["TV 4 [Điền tên]", "Scanner O(n), Sinh mã Lexer (.py), Giao diện Web 5 Tab, 72 Tests", "25%"],
        ],
        [1.50, 3.40, 0.80],
        font_size=10.4,
    )
    add_rect(s12, 6.95, 4.92, 5.70, 1.82, C_AMBER_BG, border_color=C_AMBER, border_pt=1.2, rounded=True)
    add_text(s12, 7.12, 5.02, 5.38, 0.30, "Khai báo sử dụng công cụ AI (Mục 10.2 Báo cáo)", size=11.8, bold=True, color=C_AMBER)
    add_text(
        s12,
        7.12,
        5.34,
        5.38,
        1.32,
        "• Công cụ: Google Gemini / Antigravity hỗ trợ rà soát lý thuyết, kiểm tra các trường hợp biên, xây dựng hiển thị SVG 5 Tab và định dạng tài liệu.\n"
        "• Kiểm chứng: Các thành viên đọc hiểu từng hàm trong lexer_engine/, chạy 72/72 JSON + 22/22 Unittest và chịu trách nhiệm về nội dung trình bày.",
        size=10.5,
        color=C_TEXT,
    )

    # =========================================================================
    # SLIDE 13: KẾT LUẬN & Q&A
    # =========================================================================
    s13 = prs.slides.add_slide(blank)
    set_bg(s13, C_NAVY)
    add_rect(s13, 0, 0, 13.333, 0.14, C_SKY)
    add_rect(s13, 0, 7.36, 13.333, 0.14, C_BLUE)

    add_text(s13, 0.9, 1.25, 11.5, 0.5, "KẾT LUẬN ĐỒ ÁN T13", size=14, bold=True, color=C_SKY, align=PP_ALIGN.CENTER)
    add_text(
        s13,
        0.9,
        1.85,
        11.5,
        1.2,
        "Quy trình Biên dịch hai chiều theo Định lý Kleene &\nBộ phân tích từ vựng tuyến tính O(n)",
        size=30,
        bold=True,
        color=C_WHITE,
        align=PP_ALIGN.CENTER,
    )

    final_boxes = [
        (1.2, "Định lý Kleene (0 import re)", "Thompson · Khử ε · Subset · Direct r#\nMoore · Hopcroft · GNFA (DFA → RE)"),
        (5.1, "Đại số Σ(U) & Ma trận giao", "128 ASCII (~(~A)=A) · Giới hạn AST ≤4096\nMyhill–Nerode · Chứng nhân L(Rᵢ)∩L(Rⱼ)"),
        (9.0, "72/72 PASS & Sinh mã Lexer", "Reps (1998) O(n) · Xuất Lexer (.py)\n22 Unittest Suites · Giao diện Web 5 Tab"),
    ]
    for x, ft, fd in final_boxes:
        add_rect(s13, x, 3.45, 3.15, 1.45, RGBColor(0x16, 0x24, 0x47), border_color=C_SKY, border_pt=1.3, rounded=True)
        add_text(s13, x + 0.12, 3.58, 2.91, 0.40, ft, size=14.6, bold=True, color=C_SKY, align=PP_ALIGN.CENTER)
        add_text(s13, x + 0.12, 4.04, 2.91, 0.74, fd, size=11.1, color=RGBColor(0xE2, 0xE8, 0xF0), align=PP_ALIGN.CENTER)

    add_text(
        s13,
        0.9,
        5.45,
        11.5,
        0.65,
        "Cảm ơn Cô Hồ Thị Thanh Tuyến và các bạn đã lắng nghe.",
        size=22,
        bold=True,
        color=C_WHITE,
        align=PP_ALIGN.CENTER,
    )
    add_text(
        s13,
        0.9,
        6.18,
        11.5,
        0.45,
        "Nhóm rất mong nhận được câu hỏi góp ý và trao đổi trong phần hỏi đáp (Q&A)",
        size=14,
        italic=True,
        color=RGBColor(0x93, 0xC5, 0xFD),
        align=PP_ALIGN.CENTER,
    )

    speaker_notes = [
        (
            "[Thành viên 1 | 0:00 – 0:30 | Slide 1: Trang bìa]\n"
            "Em xin chào Cô và các bạn. Hôm nay Nhóm 6 xin trình bày báo cáo đồ án cuối kỳ môn Ngôn ngữ hình thức "
            "với đề tài T13: Automata-based Lexical Analyzer — Xây dựng Bộ phân tích từ vựng tổng quát theo quy trình khép kín của Định lý Kleene.\n"
            "Toàn bộ chương trình được cài đặt bằng thư viện chuẩn của Python (không dùng import re), "
            "phân hoạch bảng chữ cái Unicode động Σ(U) giữ đúng tính chất ~(~A)=A, cài đặt cả GNFA (DFA → RE), Ma trận giao nhau L(Rᵢ)∩L(Rⱼ), "
            "bộ sinh mã Lexer độc lập kiểu Flex và vượt qua 72/72 ca kiểm thử JSON cùng 22 nhóm Unittest."
        ),
        (
            "[Thành viên 1 | 0:30 – 1:15 | Slide 2: Đặt vấn đề và 4 mục tiêu chính]\n"
            "Trong trình biên dịch, Lexical Analyzer là giai đoạn đầu tiên chuyển dòng ký tự mã nguồn thành luồng Token, lọc bỏ khoảng trắng/bình luận "
            "và phát hiện lỗi từ vựng. Các lớp token thuộc Ngôn ngữ chính quy nên nhận diện được bằng DFA trong thời gian tuyến tính O(n).\n"
            "Nhóm đặt ra 4 mục tiêu chính: (1) Không dùng import re, đại số Boole Σ(U) trên 128 ASCII & giới hạn AST ≤ 4096 nút; "
            "(2) Cài đặt hai chiều Định lý Kleene với GNFA (DFA → RE), kiểm tra Myhill–Nerode & Ma trận giao nhau L(Rᵢ)∩L(Rⱼ); "
            "(3) Bộ quét O(n) Reps (1998), xử lý đúng dòng CRLF & xuất tệp Lexer Python độc lập kiểu Flex; "
            "(4) Giao diện Web 5 Tab cùng 72 test cases JSON và 22 nhóm unittest."
        ),
        (
            "[Thành viên 1 | 1:15 – 2:00 | Slide 3: Mô hình Đa-Token, Unicode động Σ(U) và Ma trận giao L(Rᵢ)∩L(Rⱼ)]\n"
            "Slide 3 trình bày 3 thành phần hình thức:\n"
            "1. Combined ε-NFA & Khử ε (Định lý 2, Slide 21–22): giảm MiniLang từ 170 xuống 96 trạng thái NFA không ε.\n"
            "2. Subset DFA (44 lớp tương đương) & Ma trận giao nhau L(Rᵢ)∩L(Rⱼ): phân tích tĩnh 741 cặp quy tắc của MiniLang, xác định 9 cặp từ khóa nằm trong IDENTIFIER kèm chứng nhân ngắn nhất.\n"
            "3. Moore/Hopcroft, Myhill–Nerode (3003/3003 cặp) & GNFA State Elimination (DFA → RE).\n"
            "Bảng chữ cái động Σ(U) = 128 ASCII ∪ U ∪ {NON_ASCII U+FDD0} đảm bảo ~(~A)=A, hỗ trợ từ khóa tiếng Việt 'nếu' và ký hiệu '€' không trùng NON_ASCII, đồng thời chặn biểu thức lồng nhau (((a{64}){64}){64}) bằng giới hạn MAX_AST_NODES = 4096."
        ),
        (
            "[Thành viên 2 | 2:00 – 2:40 | Slide 4: Quy trình biên dịch Automata theo Định lý Kleene và Sinh mã Lexer]\n"
            "Slide 4 mô tả kiến trúc tổng thể của chương trình:\n"
            "• Nhánh biên dịch đi qua các định lý Chương 3.1: RE Parser (≤4096 nút, Σ(U)) → Thompson ε-NFA → NFA khử ε → Subset DFA → Moore & Hopcroft Min-DFA.\n"
            "• Nhánh đối chứng và chiều ngược: cây cú pháp r·# (followpos) sinh Direct DFA, và thuật toán GNFA State Elimination chuyển ngược Min-DFA về biểu thức chính quy R_sinh.\n"
            "• Ở đầu ra, Min-DFA vừa điều khiển bộ quét O(n), vừa được mô-đun codegen xuất thành tệp Lexer Python độc lập."
        ),
        (
            "[Thành viên 2 | 2:40 – 3:25 | Slide 5: Đối chiếu Slide 38 UEH và GNFA trên (a|b)*abb]\n"
            "Đối chiếu trên biểu thức (a|b)*abb của Slide 38 Chương 3.1:\n"
            "• Hình (a) Thompson ε-NFA: tạo ra 11 trạng thái (q0..q10) khớp Slide 38.\n"
            "• Bước Khử ε (Định lý 2, Slide 21–22): giảm từ 11 xuống 6 trạng thái NFA.\n"
            "• Hình (b) & (c) Subset → Min-DFA: 5 tập con D0..D4 gộp D0 ≡ D2 còn 4 trạng thái tối giản (đủ 6/6 cặp Myhill–Nerode).\n"
            "• Bước GNFA (DFA → RE): khử lần lượt D2, D0, D3, D1 sinh biểu thức b*a(a|ba|bb(a|b+a))*bb tương đương L(R_gốc)."
        ),
        (
            "[Thành viên 2 | 3:25 – 4:15 | Slide 6: Nhánh đối chứng Direct RE → DFA (Slide 46–57)]\n"
            "Kiểm tra phương pháp trực tiếp trên r = (a|ba)(a|b)*ba# (Slide 54 Chương 3.1):\n"
            "• Cây cú pháp có 8 vị trí lá; bảng followpos trên giao diện Web Tab 3 khớp với Slide 54: "
            "followpos(1)=3=4=5={4,5,6}, (2)={3}, (6)={7}, (7)={8}.\n"
            "• Đồ thị Direct DFA sinh trực tiếp 5 trạng thái tối giản A..E khớp Slide 55–57.\n"
            "• Mở rộng Đa-Token (Rᵢ·#ᵢ) sinh Combined Direct DFA tương đương ngôn ngữ với Min-DFA trên cả MiniLang (79 TT), CalcLang (20), MiniSQL (52)."
        ),
        (
            "[Thành viên 3 | 4:15 – 4:55 | Slide 7: Đồ thị Combined Minimized DFA — Ngôn ngữ CalcLang]\n"
            "Đồ thị Combined Minimized DFA của CalcLang (12 token): giảm từ 57 ε-NFA → 26 NFA khử ε → 24 Subset DFA → 20 trạng thái tối giản (190/190 cặp Myhill–Nerode).\n"
            "• Từ khóa & Định danh: KW_LET ⊂ ID (giao nhau trên từ tố 'let') nhưng được chọn nhờ Priority; nếu đọc thêm chữ/số (như letx) thì rẽ sang ID nhờ Maximal Munch.\n"
            "• Số thực & Quay lui: đọc chữ số vào INT, gặp '.' sang trạng thái trung gian, đọc tiếp chữ số mới vào FLOAT. Gặp '3.' quay lui về INT('3')."
        ),
        (
            "[Thành viên 3 | 4:55 – 5:35 | Slide 8: Bộ quét O(n) (Reps, 1998) và Sinh mã Lexer độc lập]\n"
            "3 cơ chế ở tầng thực thi và sinh mã:\n"
            "1. Bảng nhớ failed_states (Reps, 1998): cắt nhánh O(1) tránh quay lui bậc hai O(n²); chuỗi lỗi 10.000 ký tự thực hiện 5.000 lần cắt nhánh.\n"
            "2. STRING_LIT loại trừ cả \\r và \\n trên Windows CRLF, kết hợp tùy chọn Panic-mode và Smart-Sync.\n"
            "3. Bộ sinh mã kiểu Flex (codegen.py): xuất các bảng tĩnh ASCII_CLASS_MAP[128], UNICODE_CLASS_MAP, TRANSITIONS[78][44] thành 1 tệp Python độc lập (~527 dòng, không dùng import re) khớp đầu ra với bộ phân tích gốc."
        ),
        (
            "[Thành viên 3 | 5:35 – 7:15 | Slide 9: Demo trực tiếp Giao diện Web 5 Tab]\n"
            "Chuyển sang trình duyệt thực hiện Demo trực tiếp qua 4 bước:\n"
            "• Tab 1 & Thanh công cụ: Quét mã UTF-8/CRLF, đổi Panic-mode / Smart-Sync, thử nút Dark / Light và bấm 'Xuất Lexer (.py)' tải tệp bộ quét độc lập.\n"
            "• Tab 2: Mở thẻ con 'Ma trận giao L(Rᵢ) ∩ L(Rⱼ)' xem bảng 39×39 (9/741 cặp giao nhau) & bảng Myhill–Nerode.\n"
            "• Tab 3: Xem cây r·# Slide 54 và mở thẻ con thứ 6 'GNFA khử trạng thái (DFA → RE)' xem từng bước khử đỉnh.\n"
            "• Tab 4: Bấm '+ Mẫu Unicode (nếu / €)' biên dịch lại, sau đó bấm 'Thử che khuất' để xem cảnh báo quy tắc bị che khuất."
        ),
        (
            "[Thành viên 4 | 7:15 – 7:50 | Slide 10: Kết quả Kiểm thử tự động (72/72 PASS · 22 Suites) và Đối chứng mã sinh]\n"
            "Kết quả kiểm thử tự động:\n"
            "• 72/72 ca kiểm thử JSON đạt: 20 mẫu RE đơn/Unicode/GNFA, 24 mẫu lỗi cú pháp RE & giới hạn AST (((a{64}){64}){64}), 28 ca quét CRLF & ký tự điều khiển ASCII.\n"
            "• 22/22 nhóm Unittest đạt: kiểm tra bảo toàn mã nguồn, đại số Boole ~(~A)=A trên cả CharSet & DFA, GNFA (DFA→RE), Ma trận giao nhau, Reps O(n) và đối chứng với tệp Standalone Lexer (.py)."
        ),
        (
            "[Thành viên 4 | 7:50 – 8:25 | Slide 11: Thực nghiệm và Phân tích hiệu năng trên 3 ngôn ngữ]\n"
            "Tổng hợp số liệu thực nghiệm:\n"
            "• MiniLang (39 token, 44 lớp Σ): 170 ε-NFA → 96 Khử ε → 86 Subset → 79 Direct → 78 Moore/Hopcroft Min-DFA (-9.3%, 3003/3003 cặp, 9/741 cặp giao nhau).\n"
            "• CalcLang (12 token): 57 → 26 → 24 → 20 → 20 Min-DFA (-16.7%, 190/190 cặp, 2/66 cặp giao).\n"
            "• MiniSQL (14 token): 128 → 67 → 64 → 52 → 52 Min-DFA (-18.8%, 1326/1326 cặp, 5/91 cặp giao)."
        ),
        (
            "[Thành viên 4 | 8:25 – 9:05 | Slide 12: Giới hạn Lý thuyết (Bổ đề Bơm), Hướng phát triển và Phân công]\n"
            "• Bên cạnh các vấn đề kỹ thuật đã xử lý trong cài đặt, nhóm phân tích giới hạn lý thuyết DFA theo Bổ đề Bơm Chương 3.2: "
            "bình luận lồng nhau tùy ý /* /* ... */ */ tương ứng với L = {a^n b^n | n ≥ 1} thuộc lớp Ngôn ngữ phi ngữ cảnh (CFL - Chương 4).\n"
            "• Hướng phát triển: Bổ sung ngăn xếp trạng thái ngữ cảnh từ vựng và nối luồng Token của Lexer độc lập (.py) vào Parser CFG LL(1)/LR(1).\n"
            "• Phân công 25% cho mỗi thành viên và khai báo việc sử dụng công cụ AI hỗ trợ rà soát, kiểm thử."
        ),
        (
            "[Thành viên 4 | 9:05 – 9:30 | Slide 13: Kết luận và Hỏi đáp Q&A]\n"
            "Tổng kết 3 kết quả chính của đồ án T13: (1) Quy trình hai chiều của Định lý Kleene với 7 biểu diễn tương đương (không dùng import re); "
            "(2) Đại số Boole trên Σ(U) (~(~A)=A), giới hạn AST ≤ 4096, kiểm chứng Myhill–Nerode & Ma trận giao nhau L(Rᵢ)∩L(Rⱼ); "
            "(3) 72/72 test case JSON + 22 nhóm Unittest + Bộ sinh mã Lexer Python độc lập kiểu Flex.\n"
            "Nhóm xin cảm ơn Cô Hồ Thị Thanh Tuyến và các bạn đã lắng nghe, rất mong nhận được câu hỏi góp ý từ Cô và các bạn."
        ),
    ]
    for s_obj, note_txt in zip(prs.slides, speaker_notes):
        s_obj.notes_slide.notes_text_frame.text = note_txt

    prs.save(str(PPTX_PATH))
    print(f"[OK] Saved PPTX presentation with embedded speaker notes -> {PPTX_PATH} ({TOTAL} slides)")


if __name__ == "__main__":
    build_slides()
