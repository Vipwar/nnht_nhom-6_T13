# Đề tài T13: Automata-based Lexical Analyzer (`LexAutomata Studio`)

[![T13 Automata Lexical Analyzer CI](https://github.com/Vipwar/nnht_nhom-6_T13/actions/workflows/ci.yml/badge.svg)](https://github.com/Vipwar/nnht_nhom-6_T13/actions/workflows/ci.yml)

> **Học phần:** Ngôn ngữ hình thức (*Introduction to Formal Languages*) — Mã lớp: `26C1INF50915301`  
> **Trường:** Đại học Kinh tế TP.HCM (UEH) — Khoa Công nghệ Thông tin Kinh doanh (CTD)  
> **Giảng viên hướng dẫn:** ThS. Hồ Thị Thanh Tuyến  
> **Nhóm thực hiện:** Nhóm 6  

---

## 1. Giới thiệu tổng quan

**LexAutomata Studio (Version 2.0 Ultimate)** là bộ sinh và thực thi **Bộ phân tích từ vựng dựa trên Automata (Automata-based Lexical Analyzer)** được cài đặt **100% từ con số 0 bằng Python thuần** (tuyệt đối **Zero `import re`** hay bất kỳ thư viện regex/lexer ngoài nào trong toàn bộ lõi `lexer_engine/`, `app.py`, `cli.py` và các file bộ quét độc lập sinh tự động).

Chương trình thể hiện trực tiếp, tường minh mối liên hệ giữa **Lý thuyết Ngôn ngữ hình thức & Automata (Chương 1, 2, 3)** với **Kỹ thuật trình biên dịch (Compiler Construction)** thông qua **Vòng tròn Định lý Kleene 360°** và các bộ kiểm chứng hình thức:

```
Tập Token Specs (RE + Thứ tự ưu tiên + Cờ Skip)
   │
   ├─► [1] Recursive-Descent Regex Parser (Zero `re` · Chống bom AST MAX_AST_NODES=4096 · Định lượng {m,n})
   │        └─► Bảng chữ cái Unicode Động Σ(U) = 128 ASCII (0x00..0x7F) ∪ U ∪ {NON_ASCII U+FDD0} (~(~A) = A)
   ├─► [2] Thompson's Construction (Định lý 3 Slide 24-30) ──► Combined Multi-token ε-NFA
   ├─► [3] Epsilon Elimination (Định lý 2 Slide 21-22) ──► Combined NFA không có ε-chuyển tiếp
   ├─► [4] Subset Construction (Định lý 1 + Alphabet Partitioning + Rule Priority) ──► Combined Subset DFA
   ├─► [5] Multi-token DFA Minimization & Complement (Song song 2 thuật toán):
   │        ├─► Moore Partition Refinement O(p·|Q|²) (Xuất vết Π₀ → Π₁ → ... → Π_k)
   │        └─► Hopcroft Worklist Algorithm O(p·|Q|log|Q|) + complement_dfa bảo toàn ~(~L) = L
   ├─► [6] Direct RE → DFA (Chương 3.1 Mục 2.5 — Cây cú pháp r·# & Đa-Token (R₁·#₁)|...|(R_k·#_k), followpos)
   ├─► [7] GNFA State Elimination (Chiều ngược Kleene 360°: Min-DFA ──► R_sinh, chứng minh L(R_gốc) ≡ L(R_sinh))
   ├─► [8] Bộ Kiểm Chứng Toán Học & Phân Tích Tĩnh (Formal Verifier):
   │        ├─► Product Automaton BFS Đa-Chiều (ε-NFA ≡ NFA Khử ε ≡ Subset ≡ Direct ≡ Moore ≡ Hopcroft ≡ GNFA RE)
   │        ├─► Ma trận Giao nhau Tĩnh L(Rᵢ) ∩ L(Rⱼ) kèm chuỗi chứng nhân ngắn nhất & Phát hiện Shadowed Rules
   │        ├─► Myhill–Nerode Minimality Verifier (Tìm chuỗi phân biệt ngắn nhất w cho 100% cặp trạng thái)
   │        └─► JFLAP 7.x XML (.jff) Round-Trip Exporter & Importer (Bảo toàn cả ký tự điều khiển & Σ(U))
   └─► [9] Tầng Thực Thi & Sinh Mã:
            ├─► Linear-Time Maximal Munch Scanner O(n) (Reps 1998 failed_states + CRLF-Safe + Panic / Smart-Sync)
            └─► Flex-style Standalone Python Lexer Generator (codegen.py ──► file .py độc lập 0 phụ thuộc)
```

---

## 2. Yêu cầu môi trường & Cài đặt

- **Python 3.10+** (đã kiểm thử trên Python 3.10 / 3.11 / 3.12 qua GitHub Actions CI).
- **Không cần `pip install` bất kỳ thư viện nào** để chạy ứng dụng Web Studio, CLI, file Lexer độc lập sinh ra và toàn bộ bộ kiểm thử tự động (`lexer_engine/`, `app.py`, `cli.py`, `tests/` chỉ dùng 100% Python Standard Library).
- Hỗ trợ chạy ngay trên **GitHub Codespaces** (`.devcontainer/devcontainer.json`) và **Render Cloud** (`render.yaml`).

---

## 3. Hướng dẫn chạy nhanh (Quick Start)

### 3.1. Chạy Giao diện Web Demo Trực Quan 5 Tab (`LexAutomata Studio`)
```bash
python3 app.py
```
- Chương trình tự khởi động máy chủ tại **`http://127.0.0.1:8000`** (hoặc đổi cổng: `python3 app.py --port 8765 --no-browser`).

**Các tính năng nổi bật trên 5 Tab của Web Studio:**
1. **Tab 1 & Thanh công cụ — Bộ Quét O(n), Hoạt ảnh DFA & Nút `⬇ Sinh Lexer (.py)`:** Nhập mã nguồn (hỗ trợ tiếng Việt UTF-8 `"Xin chào UEH"`, CRLF `\r\n`, bình luận `/* ... */`), chuyển đổi trực tiếp giữa **`Panic-mode (1 ký tự)`** và **`Smart-Sync`**, xem số lần cắt nhánh `memoized_cutoffs` (Reps, 1998), chạy hoạt ảnh DFA từng bước và tải ngay file bộ quét Python độc lập kiểu Flex (`.py`).
2. **Tab 2 — Đồ thị Automata Đa-Token, Myhill–Nerode & Ma trận Giao nhau `L(Rᵢ) ∩ L(Rⱼ)`:** Trực quan hóa đồ thị SVG kéo-thả/zoom cho cả 6 mô hình đa-token, xem bảng chuỗi phân biệt **Myhill–Nerode**, thẻ con **Ma trận Giao nhau `L(Rᵢ) ∩ L(Rⱼ)`** (bản đồ nhiệt tương tác `39 × 39` + bảng từ tố chứng nhân ngắn nhất) và xuất file `.jff` chuẩn JFLAP.
3. **Tab 3 — Phòng Thí Nghiệm RE Đơn Lẻ & Vòng Tròn Định Lý Kleene 360° (`GNFA DFA → RE`):** Kiểm chứng trực tiếp các ví dụ Slide Chương 3.1 (`(a|b)*abb`, `(a|ba)(a|b)*ba`), biểu thức Unicode động `(nếu|lặp)_[0-9]+€`, xem **Cây `r·#`** (`nullable`, `FP`, `LP`), **Bảng `followpos`**, mở thẻ con thứ 6 **GNFA Khử Trạng Thái (`DFA → RE · Kleene 360°`)** xem từng bước khử đỉnh `q_rip` và kiểm chứng `R₁ ≡ R₂`.
4. **Tab 4 — Đặc Tả Token (Live RE Editor, Unicode Động & Flex Codegen):** Bấm **`+ Thêm Unicode (nếu / €)`** để thêm từ khóa tiếng Việt/ký hiệu tiền tệ vào ngôn ngữ, thử bẫy **Shadowed Rule** (`IDENTIFIER > KW_IF`), xem bảng chứng nhân giao nhau trực tiếp và tải **`Standalone Lexer (.py)`** tùy chỉnh.
5. **Tab 5 — Kiểm Thử Tự Động (72/72 PASS) & Benchmark Chống Quay Lui O(n²):** Chạy trực tiếp 72 ca kiểm thử JSON, bảng đối sánh trên 3 ngôn ngữ và biểu đồ Stress Test 10.000 ký tự lỗi (`"aaaa...`, `/*xxxx...`, `"\"\"...`).

### 3.2. Chạy Giao diện Dòng Lệnh (CLI) & Kiểm thử Tự động
```bash
# 1. Chạy toàn bộ 72/72 ca kiểm thử có cấu trúc từ tests/test_cases.json
python3 cli.py test

# 2. Chạy 22/22 bộ Unittest kiểm chứng các bất biến toán học, Kleene 360°, ~(~A)=A & Differential Codegen
python3 tests/test_suite.py -v

# 3. Khép kín vòng tròn Định lý Kleene 360°: Chuyển Min-DFA ngược về RE bằng GNFA State Elimination
python3 cli.py gnfa "(a|b)*abb"
python3 cli.py gnfa "(nếu|lặp)_[0-9]+€"

# 4. Phân tích tĩnh Ma trận Giao nhau L(R_i) ∩ L(R_j) & tìm chuỗi chứng nhân ngắn nhất
python3 cli.py intersections --preset minilang

# 5. Sinh bộ quét từ vựng Python độc lập kiểu Flex (Standalone Table-Driven Lexer, Zero `import re`)
python3 cli.py codegen --preset minilang -o minilang_lexer.py
python3 minilang_lexer.py --code 'let x = 42; if (x >= 10) { print("Xin chào UEH"); }'

# 6. Chạy Benchmark đối sánh Đa-Otomat & Stress Test O(n) trên 3 ngôn ngữ
python3 cli.py benchmark

# 7. Quét mã nguồn với chế độ phục hồi lỗi Panic-mode hoặc Smart-Sync
python3 cli.py scan --preset minilang --file data/samples/demo_minilang_valid.mini
python3 cli.py scan --preset minilang --file data/samples/demo_minilang_errors.mini --error-recovery smart_sync

# 8. Phân tích chi tiết 1 Biểu thức chính quy qua chuỗi Otomat + GNFA + Myhill-Nerode (Slide 38 & Slide 54)
python3 cli.py inspect "(a|b)*abb" --name SLIDE38 --test abb aabb babb ab ba
python3 cli.py inspect "(a|ba)(a|b)*ba" --name SLIDE54 --test aba baba aabba ba a abb

# 9. Chứng minh tương đương 2 Biểu thức chính quy bất kỳ & Xuất JFLAP 7.x (.jff)
python3 cli.py equiv "(a|b)*" "(a*b*)*"
python3 cli.py export-jff --pattern "(a|b)*abb" --stage min_dfa --expand -o data/jflap_exports/custom_abb.jff
```

---

## 4. Kết quả Thực nghiệm Tổng hợp trên 3 Ngôn ngữ

| Ngôn ngữ (Số quy tắc) | Thompson ε-NFA | NFA Khử ε (ĐL 2) | Subset DFA | Combined Direct DFA | Moore / Hopcroft Min-DFA | Lớp Σ(U)/≡ | Myhill–Nerode | Giao nhau L(Rᵢ)∩L(Rⱼ) | Kiểm chứng |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **`MiniLang`** (39 token) | 170 TT | 96 TT | 86 TT | 79 TT | **78 / 78 TT** (-9.3%) | 44 lớp | **3.003 / 3.003** | **9 / 741** (0 che khuất) | ✓ 100% Eq |
| **`CalcLang`** (12 token) | 57 TT | 26 TT | 24 TT | 20 TT | **20 / 20 TT** (-16.7%) | 19 lớp | **190 / 190** | **2 / 66** (0 che khuất) | ✓ 100% Eq |
| **`MiniSQL`** (14 token) | 128 TT | 67 TT | 64 TT | 52 TT | **52 / 52 TT** (-18.8%) | 44 lớp | **1.326 / 1.326** | **5 / 91** (0 che khuất) | ✓ 100% Eq |

---

## 5. Cấu trúc thư mục dự án

```
nnht_nhom-6_T13/
├── README.md                          # Tài liệu hướng dẫn cài đặt, kiến trúc v2.0 & sử dụng
├── HUONG_DAN_BAO_VE.md                # Kịch bản thuyết trình 9.5 phút & 38 câu Q&A phản biện chuyên sâu
├── LOI_THOAI_13_SLIDE_VA_ON_TAP.md    # Lời thoại chi tiết 13 slide & 18 Flashcard ôn tập Chương 1-3
├── app.py                             # Máy chủ Web Studio + REST API (100% Python Standard Library)
├── cli.py                             # Công cụ CLI 9 lệnh (scan, inspect, gnfa, codegen, intersections, ...)
├── .devcontainer/devcontainer.json    # Cấu hình chạy 1-Click trên GitHub Codespaces
├── render.yaml                        # Cấu hình triển khai Cloud trực tuyến trên Render
├── lexer_engine/                      # LÕI THUẬT TOÁN TỰ CÀI ĐẶT (11 module, 100% Zero `import re`)
│   ├── __init__.py                    # Facade LexicalAnalyzer, Shadowed Rules, Intersections, Codegen & GNFA
│   ├── models.py                      # ASCII_SIGMA (128 mã 0x00..0x7F), NON_ASCII (U+FDD0), Σ(U) động, NFA, DFA
│   ├── regex_parser.py                # Bộ phân tích RE đệ quy (MAX_AST_NODES=4096, {m,n}, \xHH, \uHHHH, Σ(U))
│   ├── thompson.py                    # Thompson (RE → ε-NFA), Combined ε-NFA & Định lý 2 Khử ε (eliminate_epsilon)
│   ├── subset_construction.py         # Subset Construction (ε-closure, Move), Alphabet Partitioning & Priority
│   ├── direct_dfa.py                  # Direct RE → DFA cho RE đơn lẻ (r·#) & Đa-Token ((R₁·#₁)|...|(R_k·#_k))
│   ├── dfa_minimizer.py               # Moore (Π₀→Π_k), Hopcroft O(p·|Q|log|Q|) & complement_dfa (~(~D) ≡ D)
│   ├── gnfa.py                        # GNFA State Elimination (DFA → RE) khép kín Định lý Kleene 360°
│   ├── scanner.py                     # Bộ quét Maximal Munch O(n) (Reps 1998 failed_states, panic_char & smart_sync)
│   ├── codegen.py                     # Bộ sinh mã Standalone Table-Driven Python Lexer kiểu Flex (Zero `import re`)
│   ├── verifier.py                    # Product Automaton, Myhill–Nerode & Ma trận Giao nhau Tĩnh L(Rᵢ) ∩ L(Rⱼ)
│   ├── jflap_export.py                # Xuất & Đọc ngược (Round-Trip) XML .jff tương thích JFLAP 7.x
│   └── presets.py                     # 3 bộ đặc tả ngôn ngữ (MiniLang 39, CalcLang 12, MiniSQL 14, CRLF-Safe)
├── web/                               # Giao diện Web SPA 5 Tab (HTML5 + CSS3 + SVG/JS thuần)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   ├── specs/                         # File JSON đặc tả token cho MiniLang (39 token), CalcLang, MiniSQL
│   ├── samples/                       # File mã nguồn mẫu (hợp lệ, trường hợp biên, lỗi từ vựng)
│   └── jflap_exports/                 # File .jff sinh sẵn để đối chứng trực tiếp trên JFLAP 7.x
├── tests/
│   ├── test_cases.json                # 72 test cases có cấu trúc (20 RE/Unicode/GNFA, 24 bẫy lỗi/AST Bomb, 28 Scan)
│   └── test_suite.py                  # 22 bộ Unittest kiểm chứng bất biến toán học, Kleene 360° & Differential Codegen
├── scripts/                           # Script tái tạo biểu đồ, báo cáo DOCX/PDF (13 trang) và slide PPTX (13 slide)
│   ├── generate_figures.py
│   ├── generate_report.py
│   └── generate_slides.py
└── deliverables/                      # Sản phẩm báo cáo & thuyết trình nộp cuối kỳ
    ├── Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.docx
    ├── Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.pdf
    └── Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx
```
