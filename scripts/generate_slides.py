"""
Generate the 16:9 widescreen PowerPoint Presentation Deck (13 Slides)
for Topic T13: Automata-based Lexical Analyzer (UEH Formal Languages).

Output:
  deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx
Also exports a temporary QA PDF via PowerPoint COM so we can visually inspect every slide.
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
QA_PDF_PATH = OUT_DIR / "_qa_slides_preview.pdf"

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
    bullet_char: str = "▸ ",
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
    # Top navy bar
    add_rect(slide, 0, 0, 13.333, 0.88, C_UEH)
    add_rect(slide, 0, 0.88, 13.333, 0.05, C_SKY)
    # Pill tag (auto-sized so text never wraps onto 2 lines)
    pill_w = max(2.35, min(3.8, len(section_tag) * 0.105 + 0.55))
    add_rect(slide, 0.45, 0.14, pill_w, 0.28, C_BLUE, rounded=True)
    add_text(slide, 0.45, 0.14, pill_w, 0.28, section_tag, size=10, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    # Slide title
    add_text(slide, 0.45, 0.44, 11.8, 0.40, title, size=20, bold=True, color=C_WHITE)
    # Footer bar
    add_rect(slide, 0, 7.16, 13.333, 0.34, C_WHITE, border_color=C_BORDER, border_pt=0.5)
    add_text(
        slide, 0.45, 7.19, 9.5, 0.28,
        "UEH · Học phần Ngôn ngữ hình thức · Đề tài T13: Automata-based Lexical Analyzer",
        size=10, color=C_MUTED, valign=MSO_ANCHOR.MIDDLE,
    )
    add_text(
        slide, 11.4, 7.19, 1.5, 0.28,
        f"Trang {slide_num} / {total_slides}",
        size=10, bold=True, color=C_UEH, align=PP_ALIGN.RIGHT, valign=MSO_ANCHOR.MIDDLE,
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
    tbl_shape = slide.shapes.add_table(1 + len(rows), len(headers), Inches(left), Inches(top), Inches(width), Inches(height))
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
            r.font.color.rgb = C_GREEN if "PASS" in str(val) or "✓" in str(val) else C_TEXT
            if "PASS" in str(val) or "✓" in str(val):
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
    # Decorative left vertical accent bar & top accent strip
    add_rect(s1, 0, 0, 0.28, 7.5, C_SKY)
    add_rect(s1, 0.28, 0, 13.053, 0.10, C_BLUE)
    # Decorative translucent panel right
    add_rect(s1, 8.9, 0.6, 4.0, 6.3, RGBColor(0x16, 0x24, 0x47), border_color=RGBColor(0x2B, 0x45, 0x80), border_pt=1.2, rounded=True)

    add_text(s1, 0.85, 0.65, 7.8, 0.4, "TRƯỜNG ĐẠI HỌC KINH TẾ TP. HỒ CHÍ MINH (UEH)", size=13, bold=True, color=C_SKY)
    add_text(s1, 0.85, 1.02, 7.8, 0.35, "KHOA CÔNG NGHỆ THÔNG TIN KINH DOANH · HỌC PHẦN NGÔN NGỮ HÌNH THỨC", size=11.5, color=RGBColor(0xCB, 0xD5, 0xE1))

    add_rect(s1, 0.85, 1.70, 2.35, 0.40, C_SKY, rounded=True)
    add_text(s1, 0.85, 1.70, 2.35, 0.40, "ĐỀ TÀI T13 — TIỂU LUẬN CK", size=11.5, bold=True, color=C_NAVY, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

    add_text(s1, 0.85, 2.25, 7.9, 1.35, "AUTOMATA-BASED\nLEXICAL ANALYZER", size=38, bold=True, color=C_WHITE)
    add_text(
        s1, 0.85, 3.72, 7.7, 0.95,
        "Xây dựng Bộ Phân Tích Từ Vựng Tổng Quát từ Biểu Thức Chính Quy,\nThompson ε-NFA, Subset Construction, Direct DFA (r#) & Multi-Token Min-DFA",
        size=15, italic=True, color=RGBColor(0xBF, 0xDB, 0xFE),
    )

    add_rect(s1, 0.85, 4.92, 7.5, 0.03, C_SKY)
    add_text(s1, 0.85, 5.15, 7.5, 0.35, "Giảng viên hướng dẫn: ThS. Hồ Thị Thanh Tuyến", size=14, bold=True, color=C_WHITE)
    add_text(s1, 0.85, 5.52, 7.5, 0.35, "Mã lớp học phần: 26C1INF50915301  |  TP. Hồ Chí Minh, 11/2026", size=12.5, color=RGBColor(0x94, 0xA3, 0xB8))

    # Right summary card (Group & Highlights)
    add_text(s1, 9.15, 0.85, 3.5, 0.4, "ĐIỂM NỔI BẬT DỰ ÁN", size=13, bold=True, color=C_SKY)
    add_bullets(
        s1, 9.15, 1.35, 3.55, 3.0,
        [
            ("100% Tự cài đặt: ", "Không dùng 'import re' trong toàn bộ lõi thuật toán."),
            ("Hai nhánh RE → DFA: ", "Thompson + Subset & Direct r# (followpos)."),
            ("Multi-token Min-DFA: ", "Bảo toàn nhãn token + Product Automaton Proof."),
            ("Web Studio + JFLAP: ", "Hoạt ảnh từng bước & xuất file .jff đối chứng."),
        ],
        size=12, space_after=8, lead_color=C_SKY, text_color=C_WHITE,
    )
    add_rect(s1, 9.15, 4.55, 3.5, 0.02, RGBColor(0x38, 0x54, 0x94))
    add_text(s1, 9.15, 4.72, 3.5, 0.35, "NHÓM THỰC HIỆN (NHÓM ...)", size=12, bold=True, color=C_SKY)
    add_text(
        s1, 9.15, 5.10, 3.5, 1.65,
        "1. [Họ tên Thành viên 1] — [MSSV]\n"
        "2. [Họ tên Thành viên 2] — [MSSV]\n"
        "3. [Họ tên Thành viên 3] — [MSSV]\n"
        "4. [Họ tên Thành viên 4] — [MSSV]",
        size=11.5, color=RGBColor(0xE2, 0xE8, 0xF0),
    )

    # =========================================================================
    # SLIDE 2: BÀI TOÁN & MỤC TIÊU
    # =========================================================================
    s2 = prs.slides.add_slide(blank)
    add_header(s2, "01 · ĐẶT VẤN ĐỀ", "Bài toán Phân tích Từ vựng & Mục tiêu Đồ án T13", 2, TOTAL)

    # Left card: Why Automata for Lexical Analysis?
    add_rect(s2, 0.45, 1.18, 6.1, 5.72, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s2, 0.70, 1.35, 5.6, 0.4, "Cầu nối giữa Ngôn ngữ hình thức & Trình biên dịch", size=15.5, bold=True, color=C_UEH)
    add_bullets(
        s2, 0.70, 1.85, 5.6, 3.4,
        [
            ("Vai trò Lexical Analyzer: ", "Chuyển chuỗi ký tự thô thành luồng token (từ khóa, định danh, số, chuỗi, toán tử), lọc khoảng trắng/bình luận và báo lỗi ký tự kèm (dòng, cột)."),
            ("Tại sao dùng Automata hữu hạn? ", "Mọi lớp token đều là Ngôn ngữ chính quy — đặc tả cực gọn bằng Biểu thức chính quy (RE) và quét bằng DFA trong thời gian tuyến tính O(n)."),
            ("Vấn đề khi lập trình thủ công: ", "Viết if/else cứng nhắc khó mở rộng; còn gọi sẵn thư viện re không phản ánh bản chất toán học của Automata."),
        ],
        size=13, space_after=10,
    )
    add_rect(s2, 0.70, 5.45, 5.6, 1.18, C_BLUE_BG, border_color=C_BLUE, border_pt=1.2, rounded=True)
    add_text(
        s2, 0.85, 5.58, 5.3, 0.95,
        "Định lý Kleene — Nền tảng cốt lõi:\nRE (đặc tả dễ viết)  ≡  ε-NFA (dễ hợp nhất)  ≡  Minimized DFA (chạy O(1)/ký tự)",
        size=13, bold=True, color=C_UEH, valign=MSO_ANCHOR.MIDDLE,
    )

    # Right card: 4 Concrete Objectives
    add_rect(s2, 6.78, 1.18, 6.1, 5.72, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s2, 7.03, 1.35, 5.6, 0.4, "4 Mục tiêu Vượt Chuẩn Yêu cầu Tối thiểu", size=15.5, bold=True, color=C_GREEN)

    goals = [
        ("1", C_BLUE, C_BLUE_BG, "Cài đặt 100% thuần Python (Không dùng re)", "Tự lập trình trọn bộ: RE Parser → Thompson → Subset → Min-DFA → Maximal Munch Scanner."),
        ("2", C_PURPLE, C_PURPLE_BG, "Đối chứng song song & Chứng minh toán học", "Cài thêm Direct RE→DFA (cây r#, followpos), Product Automaton Equivalence & xuất JFLAP (.jff)."),
        ("3", C_AMBER, C_AMBER_BG, "Bộ sinh tổng quát đa ngôn ngữ", "Hỗ trợ MiniLang (38 token), CalcLang (12 token), MiniSQL (14 token) + sửa RE trực tiếp trên Web."),
        ("4", C_GREEN, C_GREEN_BG, "Trực quan hóa & Kiểm thử 100%", "LexAutomata Studio 5 tab, hoạt ảnh quay lui từng bước & 29/29 test cases PASS."),
    ]
    for i, (num, col, bgc, g_title, g_desc) in enumerate(goals):
        y = 1.92 + i * 1.18
        add_rect(s2, 7.03, y, 5.6, 1.03, bgc, border_color=col, border_pt=1.0, rounded=True)
        add_rect(s2, 7.18, y + 0.22, 0.52, 0.56, col, rounded=True)
        add_text(s2, 7.18, y + 0.22, 0.52, 0.56, num, size=16, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
        add_text(s2, 7.82, y + 0.08, 4.65, 0.32, g_title, size=13, bold=True, color=col)
        add_text(s2, 7.82, y + 0.40, 4.65, 0.55, g_desc, size=11.5, color=C_TEXT)

    # =========================================================================
    # SLIDE 3: MÔ HÌNH HÌNH THỨC & MỞ RỘNG ĐA-TOKEN
    # =========================================================================
    s3 = prs.slides.add_slide(blank)
    add_header(s3, "02 · MÔ HÌNH HÌNH THỨC", "Mở rộng Automata sang Bài toán Phân loại Đa-Token (Multi-token DFA)", 3, TOTAL)

    # Top 3 formal cards
    cards3 = [
        (0.45, C_BLUE, C_BLUE_BG, "1. Combined ε-NFA",
         "N_lex = (Q_N, Σ, δ_N, q_start, F_N, τ_N)\n\n"
         "• Dựng N(Rᵢ) rời nhau cho k luật token.\n"
         "• Thêm q_start nối ε → s₁, s₂, ..., sₖ.\n"
         "• Mỗi đỉnh kết thúc fᵢ mang nhãn\n  τ_N(fᵢ) = (Tokenᵢ, Priorityᵢ, Skipᵢ)."),
        (4.65, C_AMBER, C_AMBER_BG, "2. Multi-token Subset DFA",
         "D_lex = (Q_D, Σ/≡, δ_D, D₀, F_D, τ_D)\n\n"
         "• D₀ = ε-closure({q_start}).\n"
         "• Σ/≡ là lớp tương đương ký tự (43 lớp).\n"
         "• Nếu S chứa nhiều fᵢ ∈ F_N (xung đột):\n"
         "  τ_D(S) = argmin priority(fᵢ)\n"
         "  (VD: KW_IF thắng IDENTIFIER trên 'if')."),
        (8.85, C_GREEN, C_GREEN_BG, "3. Tối thiểu hóa Đa-Token ★",
         "Phân hoạch khởi đầu Π₀ (Moore-DFA)\n\n"
         "• DFA đơn: Π₀ = { Q\\F, F }\n"
         "• Lexer DFA: KHÔNG được gộp 2 trạng\n  thái khác loại token!\n"
         "• Π₀ = { Q\\F } ∪ { F_{T₁}, ..., F_{Tₘ} }\n"
         "• Bổ sung DEAD ảo khi chia nhóm,\n  sau đó loại bỏ DEAD ở bước cuối."),
    ]
    for x, col, bgc, heading, body in cards3:
        add_rect(s3, x, 1.18, 4.03, 3.65, C_WHITE, border_color=col, border_pt=1.5, rounded=True)
        add_rect(s3, x, 1.18, 4.03, 0.48, col, rounded=False)
        add_text(s3, x + 0.12, 1.21, 3.8, 0.42, heading, size=14, bold=True, color=C_WHITE, valign=MSO_ANCHOR.MIDDLE)
        add_text(s3, x + 0.16, 1.78, 3.72, 2.9, body, size=12.5, color=C_TEXT)

    # Bottom assumption & convention box
    add_rect(s3, 0.45, 5.05, 12.43, 1.88, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s3, 0.70, 5.18, 11.9, 0.35, "Giả định hình thức & Quy ước Biểu thức chính quy", size=14, bold=True, color=C_UEH)
    add_bullets(
        s3, 0.70, 5.56, 11.9, 1.28,
        [
            ("Bảng chữ cái Σ (|Σ| = 98): ", "95 ký tự ASCII in được (32..126) + {\\t, \\n, \\r}. Ký tự ngoài Σ (như €, chữ có dấu) rơi vào DEAD → báo LEXICAL_ERROR an toàn."),
            ("Quy ước RE: ", "Dùng '|' cho phép hợp, '*' (Kleene), '+' (bao đóng dương r+ = rr*), '?' (r|ε), '[a-z]', '[^\"\\n]', '\\escape', 'ε'."),
            ("An toàn chuỗi rỗng (Nullable Guard): ", "Tự động cảnh báo nếu ε ∈ L(Rᵢ) và bắt buộc lexeme dài ≥ 1 để ngăn vòng lặp vô hạn."),
        ],
        size=12, space_after=4,
    )

    # =========================================================================
    # SLIDE 4: KIẾN TRÚC TỔNG THỂ 6 GIAI ĐOẠN
    # =========================================================================
    s4 = prs.slides.add_slide(blank)
    add_header(s4, "03 · KIẾN TRÚC HỆ THỐNG", "Đường ống Biên dịch & Thực thi 6 Giai đoạn (Thuần Automata)", 4, TOTAL)

    add_rect(s4, 0.45, 1.12, 12.43, 4.55, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s4, FIG_DIR / "fig1_architecture_pipeline.png", 0.58, 1.20, 12.17, 4.38)

    # 3 Bottom highlight chips
    chips = [
        (0.45, C_BLUE, "Alphabet Partitioning (Min-terms)", "Nén 98 ký tự ASCII → 43 lớp tương đương; tăng tốc Subset & Minimization xuống < 10 ms."),
        (4.65, C_PURPLE, "Nhánh Đối Chứng Độc Lập", "Song song Direct RE→DFA (r#, followpos) và xuất XML .jff mở trực tiếp trên JFLAP 7.x."),
        (8.85, C_GREEN, "Product Automaton Verifier", "Chứng minh toán học Subset ≡ Min-DFA trên vô hạn chuỗi (0 phản ví dụ) sau mỗi lần biên dịch."),
    ]
    for x, col, t, d in chips:
        add_rect(s4, x, 5.82, 4.03, 1.15, C_WHITE, border_color=col, border_pt=1.3, rounded=True)
        add_text(s4, x + 0.14, 5.88, 3.76, 0.30, t, size=12.5, bold=True, color=col)
        add_text(s4, x + 0.14, 6.18, 3.76, 0.72, d, size=11, color=C_MUTED)

    # =========================================================================
    # SLIDE 5: ĐƯỜNG ỐNG CHUẨN (SLIDE 38 VERIFICATION)
    # =========================================================================
    s5 = prs.slides.add_slide(blank)
    add_header(s5, "04 · THUẬT TOÁN CỐT LÕI (1/2)", "RE → Thompson ε-NFA → Subset DFA → Min-DFA (Khớp Slide 38 UEH)", 5, TOTAL)

    add_rect(s5, 0.45, 1.14, 8.25, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s5, FIG_DIR / "fig2_slide38_pipeline.png", 0.55, 1.22, 8.05, 5.65)

    add_rect(s5, 8.90, 1.14, 3.98, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s5, 9.10, 1.30, 3.6, 0.4, "Chi tiết kỹ thuật tự cài đặt", size=14.5, bold=True, color=C_UEH)
    add_bullets(
        s5, 9.10, 1.78, 3.6, 4.9,
        [
            ("RE Parser (O(|R|)): ", "Đệ quy đoán nhận 4 mức ưu tiên; gom [a-z0-9] thành 1 nút CharSetNode gọn nhẹ."),
            ("Bất biến Thompson: ", "in-deg(start)=0, out-deg(end)=0 → phép nối gộp trực tiếp l_e với r_s, tạo đúng 11 trạng thái q0..q10 cho (a|b)*abb!"),
            ("Subset Construction: ", "BFS từ D0 = ε-closure({q0}) sinh đúng 5 trạng thái D0..D4 (khớp Slide 19–20)."),
            ("Minimized DFA: ", "Gộp hai trạng thái tương đương D0 ≡ D2 → còn đúng 4 trạng thái tối giản!"),
        ],
        size=12.2, space_after=9,
    )

    # =========================================================================
    # SLIDE 6: NHÁNH ĐỐI CHỨNG DIRECT RE -> DFA
    # =========================================================================
    s6 = prs.slides.add_slide(blank)
    add_header(s6, "04 · THUẬT TOÁN CỐT LÕI (2/2)", "Nhánh đối chứng: Direct RE → DFA (Cây r·# & Followpos — Slide 46–57)", 6, TOTAL)

    # Left: Real screenshot of Tab 3 Syntax Tree + Followpos table
    add_rect(s6, 0.45, 1.14, 7.15, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s6, 0.62, 1.22, 6.8, 0.30, "Giao diện Web Tab 3: Cây phân tích r·# (nullable, FP, LP) & Bảng followpos", size=12, bold=True, color=C_UEH)
    add_picture_fit(s6, FIG_DIR / "fig7_web_direct_re_lab.png", 0.55, 1.56, 6.95, 5.30)

    # Right: Direct DFA Graph + Comparison
    add_rect(s6, 7.80, 1.14, 5.08, 3.15, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s6, FIG_DIR / "fig5_direct_dfa_slide46.png", 7.90, 1.22, 4.88, 3.0)

    add_rect(s6, 7.80, 4.46, 5.08, 2.50, C_GREEN_BG, border_color=C_GREEN, border_pt=1.3, rounded=True)
    add_text(s6, 7.98, 4.58, 4.75, 0.34, "Kết quả đối chứng trên r = (a|ba)(a|b)*ba#", size=13, bold=True, color=C_GREEN)
    add_bullets(
        s6, 7.98, 4.96, 4.75, 1.9,
        [
            ("Khớp 100% Slide 54: ", "followpos(1)=3=4=5={4,5,6}, (2)={3}, (6)={7}, (7)={8}."),
            ("Số trạng thái tối ưu ngay: ", "Direct DFA sinh trực tiếp 5 trạng thái A..E (Subset cần 7 → tối giản còn 5)."),
            ("Chứng minh tương đương: ", "Product Automaton xác nhận Subset ≡ Direct ≡ Min (✓ 100%)."),
        ],
        size=11.5, space_after=5, lead_color=C_GREEN,
    )

    # =========================================================================
    # SLIDE 7: COMBINED MULTI-TOKEN DFA (CALCLANG 20 STATES)
    # =========================================================================
    s7 = prs.slides.add_slide(blank)
    add_header(s7, "05 · TRỰC QUAN HÓA AUTOMATA", "Minh họa Combined Minimized DFA Hoàn chỉnh — Ngôn ngữ CalcLang", 7, TOTAL)

    add_rect(s7, 0.45, 1.14, 7.75, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s7, FIG_DIR / "fig3_calclang_combined_dfa.png", 0.55, 1.20, 7.55, 5.70)

    add_rect(s7, 8.40, 1.14, 4.48, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s7, 8.62, 1.32, 4.1, 0.4, "Đọc trực tiếp quy tắc từ đồ thị DFA", size=14.5, bold=True, color=C_UEH)
    add_bullets(
        s7, 8.62, 1.82, 4.08, 3.6,
        [
            ("Nén từ 12 RE → 20 trạng thái: ", "Combined ε-NFA (57) → Subset DFA (24) → Min-DFA (20, giảm -16.7%)."),
            ("Ưu tiên Từ khóa vs Định danh: ", "Nhánh D0→D9→D13→D16[KW_LET] thắng ID nhờ Rule Priority; nhưng nếu đọc tiếp ký tự chữ/số → chuyển ngay về D8[ID] (Maximal Munch)!"),
            ("Số nguyên & Số thực: ", "D0 --[0-9]--> D5[INT] --'.'--> D11 --[0-9]--> D15[FLOAT]. Gặp '3.' dừng tại D11 → quay lui về D5!"),
            ("Toán tử 1 & 2 ký tự: ", "D0 --'='--> D7[ASSIGN] --'='--> D12[EQ]."),
        ],
        size=12.2, space_after=8,
    )
    add_rect(s7, 8.62, 5.70, 4.05, 1.05, C_PURPLE_BG, border_color=C_PURPLE, border_pt=1.1, rounded=True)
    add_text(
        s7, 8.75, 5.78, 3.8, 0.9,
        "Xuất JFLAP (.jff) trực tiếp:\ndata/jflap_exports/calclang_combined_min_dfa.jff\nMở kiểm chứng độc lập trên JFLAP 7.x!",
        size=11.3, bold=True, color=C_PURPLE, valign=MSO_ANCHOR.MIDDLE,
    )

    # =========================================================================
    # SLIDE 8: SCANNER MAXIMAL MUNCH, BACKTRACKING & ERROR RECOVERY
    # =========================================================================
    s8 = prs.slides.add_slide(blank)
    add_header(s8, "06 · BỘ QUÉT TỪ VỰNG", "Cơ chế Quét DFA: Maximal Munch, Backtracking & Panic-mode Recovery", 8, TOTAL)

    # 3 Step Flow Top
    steps8 = [
        (0.45, C_BLUE, "Bước 1 · Tiến tối đa (Greedy)", "Bắt đầu tại D0, mỗi ký tự tra δ(cur, class[ch]) trong O(1). Mỗi lần qua trạng thái kết thúc, lưu mốc last_accept."),
        (4.65, C_AMBER, "Bước 2 · Quay lui (Backtrack)", "Khi gặp chuyển tiếp DEAD hoặc EOF: quay lui về last_accept để xuất token dài nhất (VD: 1.5e → quay lui 1 ký tự xuất FLOAT('1.5'))."),
        (8.85, C_ROSE, "Bước 3 · Phục hồi lỗi (Panic-mode)", "Nếu chưa từng qua trạng thái kết thúc nào: ghi nhận LEXICAL_ERROR kèm (line, col) và tiến 1 ký tự để tiếp tục quét hết file."),
    ]
    for x, col, st_t, st_d in steps8:
        add_rect(s8, x, 1.18, 4.03, 1.95, C_WHITE, border_color=col, border_pt=1.6, rounded=True)
        add_text(s8, x + 0.16, 1.30, 3.72, 0.35, st_t, size=13.5, bold=True, color=col)
        add_text(s8, x + 0.16, 1.70, 3.72, 1.30, st_d, size=12, color=C_TEXT)

    # Bottom concrete walkthrough table
    add_text(s8, 0.45, 3.35, 12.4, 0.35, "Minh họa xử lý các tình huống kinh điển trên MiniLang:", size=14, bold=True, color=C_UEH)
    add_styled_table(
        s8, 0.45, 3.76, 12.43, 3.15,
        ["Đầu vào ví dụ", "Hành vi của Minimized DFA Scanner", "Kết quả Token / Lỗi đầu ra", "Cơ chế minh họa"],
        [
            ["ifx", "D0 → 'i'(ID) → 'f'(KW_IF) → 'x'(ID) → DEAD", "IDENTIFIER('ifx')", "Maximal Munch > Priority"],
            ["a===b", "Đọc '='(ASSIGN) → '='(EQ) → '='(DEAD) → dừng", "ID('a'), OP_EQ('=='), OP_ASSIGN('='), ID('b')", "Toán tử liền kề"],
            ["1.5e + 2", "D0→'1'(INT)→'.'→'5'(FLOAT, lưu)→'e'→' '(DEAD)→quay lui 1", "FLOAT_LIT('1.5'), ID('e'), OP_PLUS, INT('2')", "Backtracking (1 ký tự)"],
            ["3. + 4", "D0→'3'(INT, lưu)→'.'→' '(DEAD)→quay lui 1; sau đó '.' DEAD", "INT('3'), LEXICAL_ERROR('.'), '+', INT('4')", "Backtrack + Error Recovery"],
            ["100$ + @x", "'$' và '@' không có cung rời D0 → báo lỗi & tiến 1 ký tự", "INT('100'), ERR('$'), '+', ERR('@'), ID('x')", "Panic-mode Recovery"],
        ],
        [1.8, 4.65, 3.78, 2.2],
        font_size=11.5,
    )

    # =========================================================================
    # SLIDE 9: LIVE WEB DEMO SHOWCASE
    # =========================================================================
    s9 = prs.slides.add_slide(blank)
    add_header(s9, "07 · TRÌNH DIỄN SẢN PHẨM", "Giao diện Trực quan LexAutomata Studio & Kịch bản Live Demo", 9, TOTAL)

    add_rect(s9, 0.45, 1.14, 8.45, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s9, FIG_DIR / "fig6_web_scanner_demo.png", 0.55, 1.20, 8.25, 5.70)

    add_rect(s9, 9.10, 1.14, 3.78, 5.82, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s9, 9.28, 1.30, 3.45, 0.40, "Kịch bản Live Demo (4 phút)", size=14.5, bold=True, color=C_UEH)
    add_bullets(
        s9, 9.28, 1.80, 3.45, 3.9,
        [
            ("Demo 1 — Tab 1 (MiniLang): ", "Quét mã hợp lệ → chuyển mẫu Biên → chạy hoạt ảnh quay lui 1 ký tự trên '1.5e' & phục hồi lỗi trên '$', '@', '\"abc'."),
            ("Demo 2 — Tab 2 (CalcLang): ", "Zoom đồ thị 20 trạng thái, nhấp D16[KW_LET] xem xung đột ưu tiên, xem phân hoạch Π₀ → Π₄."),
            ("Demo 3 — Tab 3 (Slide UEH): ", "Chạy trực tiếp (a|ba)(a|b)*ba hiển thị cây r# & bảng followpos."),
            ("Demo 4 — Tab 4 (Live Edit): ", "Bấm '+ Thêm HEX_LIT' → Biên dịch lại trong 2 ms → quét ngay '0xFF0A'!"),
        ],
        size=11.8, space_after=8,
    )
    add_rect(s9, 9.28, 5.88, 3.42, 0.88, C_BLUE_BG, border_color=C_BLUE, border_pt=1.2, rounded=True)
    add_text(
        s9, 9.38, 5.95, 3.22, 0.74,
        "Khởi chạy chỉ bằng 1 lệnh:\npython app.py\n(Không cần cài thư viện ngoài!)",
        size=11.5, bold=True, color=C_UEH, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE,
    )

    # =========================================================================
    # SLIDE 10: KIỂM THỬ TỰ ĐỘNG & ĐỐI CHỨNG
    # =========================================================================
    s10 = prs.slides.add_slide(blank)
    add_header(s10, "08 · KIỂM THỬ & KIỂM CHỨNG", "Bộ Kiểm thử Toàn diện (29/29 PASS) & 4 Lớp Đối chứng Độc lập", 10, TOTAL)

    # 4 KPI Cards Top
    kpis10 = [
        (0.45, C_GREEN, "29 / 29 PASS", "100% Test Cases (Valid · Edge · Invalid)"),
        (3.62, C_BLUE, "11 / 11 OK", "Automated Unittest Suite (0.08 giây)"),
        (6.79, C_PURPLE, "0 Phản ví dụ", "Product Automaton Proof (Mọi Preset)"),
        (9.96, C_AMBER, "0 import re", "Xác minh tự động trong lexer_engine/"),
    ]
    for x, col, big, sub in kpis10:
        add_rect(s10, x, 1.16, 2.92, 1.15, C_WHITE, border_color=col, border_pt=1.6, rounded=True)
        add_text(s10, x + 0.1, 1.24, 2.72, 0.52, big, size=22, bold=True, color=col, align=PP_ALIGN.CENTER)
        add_text(s10, x + 0.1, 1.78, 2.72, 0.42, sub, size=10.5, color=C_MUTED, align=PP_ALIGN.CENTER)

    add_styled_table(
        s10, 0.45, 2.52, 12.43, 4.40,
        ["Nhóm kiểm thử", "Số lượng", "Các kịch bản tiêu biểu đã kiểm chứng", "Kết quả"],
        [
            ["Single RE Pipeline", "6 cases", "(a|b)*abb (11→5→4), (a|ba)(a|b)*ba (khớp Slide 54), FLOAT, ID, STRING escape, (a|ε)b*", "6/6 PASS ✓"],
            ["Bắt lỗi cú pháp RE", "9 cases", "RE rỗng '', ngoặc lệch '(a|b*', 'ab)', '()', '*abc', 'a|', '[a-z', '[z-a]', 'abc\\'", "9/9 PASS ✓"],
            ["Scanner — Hợp lệ", "3 cases", "MiniLang đầy đủ, CalcLang biểu thức ngoặc, MiniSQL SELECT/FROM/WHERE", "3/3 PASS ✓"],
            ["Scanner — Trường hợp biên", "6 cases", "ifx/while2, a===b!==c, 1.5e quay lui, // cuối file, chuỗi \"\", đầu vào rỗng", "6/6 PASS ✓"],
            ["Scanner — Lỗi & Phục hồi", "5 cases", "Ký tự lạ $, @, ~; số '3.'; chuỗi chưa đóng \"abc; đơn & |; ký tự ngoài Σ (€)", "5/5 PASS ✓"],
            ["Đối chứng độc lập (Unit)", "11 suites", "Product Automaton (cả phản ví dụ a+b ≠ a*b), Oracle Python re, JFLAP XML, HEX_LIT", "11/11 OK ✓"],
        ],
        [2.7, 1.25, 6.98, 1.5],
        font_size=11.5,
    )

    # =========================================================================
    # SLIDE 11: THỰC NGHIỆM & BENCHMARK
    # =========================================================================
    s11 = prs.slides.add_slide(blank)
    add_header(s11, "09 · THỰC NGHIỆM & PHÂN TÍCH", "Đánh giá Tối thiểu hóa Trạng thái & Hiệu năng trên 3 Ngôn ngữ", 11, TOTAL)

    add_rect(s11, 0.45, 1.12, 12.43, 3.85, C_WHITE, border_color=C_BORDER, rounded=True)
    add_picture_fit(s11, FIG_DIR / "fig4_benchmark_comparison.png", 0.58, 1.18, 12.17, 3.72)

    # 3 Analytical takeaway cards below chart
    insights = [
        (0.45, C_BLUE, "Không bùng nổ trạng thái",
         "MiniLang (153→81→75), CalcLang (57→24→20), MiniSQL (128→64→52). Cấu trúc tiền tố giúp |Q_DFA| luôn nhỏ hơn |Q_NFA|."),
        (4.65, C_GREEN, "Tại sao MiniSQL giảm tới 18.8%?",
         "Từ khóa hỗ trợ cả HOA/thường (SELECT|select) tạo nhánh song song → Minimization gộp hiệu quả hậu tố tương đương (64→52)."),
        (8.85, C_AMBER, "Biên dịch < 12 ms · Quét ~800 KB/s",
         "Phân hoạch 98 ký tự ASCII xuống 19–43 lớp giúp biên dịch + chứng minh tương đương tức thời ngay trên Python thuần."),
    ]
    for x, col, it, idesc in insights:
        add_rect(s11, x, 5.14, 4.03, 1.82, C_WHITE, border_color=col, border_pt=1.4, rounded=True)
        add_text(s11, x + 0.15, 5.24, 3.74, 0.34, it, size=13, bold=True, color=col)
        add_text(s11, x + 0.15, 5.62, 3.74, 1.24, idesc, size=11.5, color=C_TEXT)

    # =========================================================================
    # SLIDE 12: HẠN CHẾ, HƯỚNG PHÁT TRIỂN & PHÂN CÔNG
    # =========================================================================
    s12 = prs.slides.add_slide(blank)
    add_header(s12, "10 · ĐÁNH GIÁ & TỔ CHỨC NHÓM", "Hạn chế, Hướng phát triển & Phân công Công việc", 12, TOTAL)

    # Left: Limitations & Future work
    add_rect(s12, 0.45, 1.16, 6.05, 5.80, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s12, 0.68, 1.32, 5.6, 0.36, "Hạn chế còn tồn tại", size=14.5, bold=True, color=C_ROSE)
    add_bullets(
        s12, 0.68, 1.72, 5.6, 2.35,
        [
            ("Panic-mode 1 ký tự: ", "Chuỗi chưa đóng '\"abc' bỏ qua '\"' rồi quét tiếp 'abc' thành ID."),
            ("Phạm vi ASCII (98 ký tự): ", "Chưa hỗ trợ trực tiếp tiếng Việt/UTF-8 trong chuỗi."),
            ("RE bệnh lý & Bình luận lồng nhau: ", "RE lặp dài có thể chạm ngưỡng O(2^n); bình luận lồng /* /* */ */ thuộc lớp CFL (vượt DFA)."),
        ],
        size=11.8, space_after=5, lead_color=C_ROSE,
    )
    add_rect(s12, 0.68, 4.18, 5.6, 0.02, C_BORDER)
    add_text(s12, 0.68, 4.30, 5.6, 0.36, "Hướng phát triển tiếp theo", size=14.5, bold=True, color=C_GREEN)
    add_bullets(
        s12, 0.68, 4.70, 5.6, 2.15,
        [
            ("Error-token rules: ", "Thêm luật ưu tiên thấp bắt trọn UNTERMINATED_STRING."),
            ("UTF-8 & Start Conditions: ", "Phân hoạch theo khoảng mã Unicode & đa ngữ cảnh cho /* ... */."),
            ("Kết nối Parser: ", "Nối luồng token vào Recursive-Descent / LL(1) Parser (Chương 4)."),
        ],
        size=11.8, space_after=5, lead_color=C_GREEN,
    )

    # Right: Team allocation & AI transparency
    add_rect(s12, 6.72, 1.16, 6.16, 5.80, C_WHITE, border_color=C_BORDER, rounded=True)
    add_text(s12, 6.95, 1.32, 5.7, 0.36, "Phân công công việc nhóm", size=14.5, bold=True, color=C_UEH)
    add_styled_table(
        s12, 6.95, 1.76, 5.70, 2.95,
        ["Thành viên", "Phần việc phụ trách", "Tỷ lệ"],
        [
            ["TV 1 [Điền tên]", "Lý thuyết, mô hình hình thức, báo cáo & slide", "25%"],
            ["TV 2 [Điền tên]", "RE Parser, Thompson NFA, Direct DFA (r#), Presets", "25%"],
            ["TV 3 [Điền tên]", "Subset DFA, Min-DFA, Product Verifier, JFLAP", "25%"],
            ["TV 4 [Điền tên]", "Maximal Munch Scanner, Web Studio, 29 Test Cases", "25%"],
        ],
        [1.55, 3.35, 0.80],
        font_size=10.8,
    )
    add_rect(s12, 6.95, 4.92, 5.70, 1.82, C_AMBER_BG, border_color=C_AMBER, border_pt=1.2, rounded=True)
    add_text(s12, 7.12, 5.02, 5.38, 0.30, "Khai báo minh bạch việc sử dụng AI (Mục 8)", size=12, bold=True, color=C_AMBER)
    add_text(
        s12, 7.12, 5.34, 5.38, 1.32,
        "• Công cụ: Google Gemini / Antigravity hỗ trợ rà soát lý thuyết, gỡ lỗi biên, dựng khung giao diện SVG và trình bày tài liệu.\n"
        "• Kiểm chứng: Cả nhóm đọc hiểu toàn bộ thuật toán cốt lõi, đối chiếu 100% ví dụ bài giảng Chương 3.1 và chịu trách nhiệm hoàn toàn khi bảo vệ.",
        size=10.8, color=C_TEXT,
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
        s13, 0.9, 1.85, 11.5, 1.2,
        "Từ Lý thuyết Automata Hữu hạn đến\nBộ Phân Tích Từ Vựng Thực Tế Hoàn Chỉnh",
        size=32, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER,
    )

    # 3 summary metrics
    final_boxes = [
        (1.2, "100% Tự cài đặt", "Không dùng re · 6 thuật toán cốt lõi\n+ Direct r# + Product Proof"),
        (5.1, "3 Ngôn ngữ + Live RE", "MiniLang · CalcLang · MiniSQL\n+ Biên dịch nóng < 10 ms"),
        (9.0, "29/29 Test PASS", "Khớp Slide UEH · Đối chứng Oracle\n+ Xuất file JFLAP (.jff)"),
    ]
    for x, ft, fd in final_boxes:
        add_rect(s13, x, 3.45, 3.15, 1.45, RGBColor(0x16, 0x24, 0x47), border_color=C_SKY, border_pt=1.3, rounded=True)
        add_text(s13, x + 0.12, 3.60, 2.91, 0.40, ft, size=16, bold=True, color=C_SKY, align=PP_ALIGN.CENTER)
        add_text(s13, x + 0.12, 4.06, 2.91, 0.72, fd, size=11.8, color=RGBColor(0xE2, 0xE8, 0xF0), align=PP_ALIGN.CENTER)

    add_text(
        s13, 0.9, 5.45, 11.5, 0.65,
        "Cảm ơn Cô Hồ Thị Thanh Tuyến và các bạn đã lắng nghe!",
        size=22, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER,
    )
    add_text(
        s13, 0.9, 6.18, 11.5, 0.45,
        "Nhóm rất hân hạnh đón nhận câu hỏi & tiến hành Demo trực tiếp (Q&A)",
        size=14, italic=True, color=RGBColor(0x93, 0xC5, 0xFD), align=PP_ALIGN.CENTER,
    )

    prs.save(str(PPTX_PATH))
    print(f"[OK] Saved PPTX presentation -> {PPTX_PATH} ({TOTAL} slides)")

    # Export to PDF via PowerPoint COM for visual inspection!
    try:
        import win32com.client

        ppt = win32com.client.Dispatch("PowerPoint.Application")
        # Open without showing window if possible
        pres = ppt.Presentations.Open(str(PPTX_PATH.resolve()), WithWindow=False)
        # ppSaveAsPDF = 32
        pres.SaveAs(str(QA_PDF_PATH.resolve()), 32)
        pres.Close()
        ppt.Quit()
        print(f"[OK] Exported QA PDF preview -> {QA_PDF_PATH}")
    except Exception as exc:
        print(f"[WARN] PowerPoint COM PDF export failed: {exc}")


if __name__ == "__main__":
    build_slides()
