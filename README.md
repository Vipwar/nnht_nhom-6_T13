# Đề tài T13: Automata-based Lexical Analyzer (`LexAutomata Studio`)

> **Học phần:** Ngôn ngữ hình thức (*Introduction to Formal Languages*) — Mã lớp: `26C1INF50915301`  
> **Trường:** Đại học Kinh tế TP.HCM (UEH) — Khoa Công nghệ Thông tin Kinh doanh (CTD)  
> **Giảng viên hướng dẫn:** ThS. Hồ Thị Thanh Tuyến  
> **Nhóm thực hiện:** Nhóm 6  

---

## 1. Giới thiệu tổng quan

**LexAutomata Studio** là bộ sinh và thực thi **Bộ phân tích từ vựng dựa trên Automata (Automata-based Lexical Analyzer)** được cài đặt **100% từ con số 0 bằng Python thuần** (tuyệt đối **Zero `import re`** hay bất kỳ thư viện regex/lexer ngoài nào trong toàn bộ lõi `lexer_engine/`, `app.py` và `cli.py`).

Chương trình thể hiện trực tiếp, tường minh mối liên hệ giữa **Lý thuyết Ngôn ngữ hình thức & Automata (Chương 1, 2, 3)** với **Kỹ thuật trình biên dịch (Compiler Construction)** thông qua toàn bộ đường ống **6 phương pháp Automata tương đương** và **5 bất biến toán học**:

```
Tập Token Specs (RE + Thứ tự ưu tiên + Cờ Skip)
   │
   ├─► [1] Hand-written Recursive-Descent Regex Parser (AST + Postfix + Định lượng {m,n} + Lớp NON_ASCII UTF-8)
   ├─► [2] Thompson's Construction (Định lý 3 Slide 24-30) ──► Combined Multi-token ε-NFA
   ├─► [3] Epsilon Elimination (Định lý 2 Slide 21-22) ──► Combined NFA không có ε-chuyển tiếp
   ├─► [4] Subset Construction (Định lý 1 + Alphabet Partitioning + Rule Priority) ──► Combined Subset DFA
   ├─► [5] Multi-token DFA Minimization (Song song 2 thuật toán):
   │        ├─► Moore Partition Refinement O(p·|Q|²) (Xuất vết Π₀ → Π₁ → ... → Π_k)
   │        └─► Hopcroft Worklist Algorithm O(p·|Q|log|Q|) (Đồ thị ngược δ⁻¹ & chia nhỏ khối)
   ├─► [6] Direct RE → DFA (Chương 3.1 Mục 2.5 — Cây cú pháp r·# & Đa-Token (R₁·#₁)|...|(R_k·#_k), followpos)
   ├─► [7] Bộ Kiểm Chứng Toán Học (Formal Verifier):
   │        ├─► Product Automaton BFS 6-Chiều (ε-NFA ≡ NFA Khử ε ≡ Subset DFA ≡ Direct DFA ≡ Moore ≡ Hopcroft)
   │        ├─► Myhill–Nerode Minimality Verifier (Tìm chuỗi phân biệt ngắn nhất w cho 100% cặp trạng thái)
   │        ├─► Shadowed / Dead Token Rule Detector (Cảnh báo luật bị che khuất bởi luật ưu tiên cao hơn)
   │        └─► JFLAP 7.x XML (.jff) Round-Trip Exporter & Importer (Xuất & đọc ngược bảo toàn 100% ngôn ngữ)
   └─► [8] Linear-Time Maximal Munch Scanner O(n) (Reps 1998 failed_states Memoization + Panic-mode / Smart-Sync)
```

---

## 2. Yêu cầu môi trường & Cài đặt

- **Python 3.10+** (đã kiểm thử trên Python 3.11 / 3.12).
- **Không cần `pip install` bất kỳ thư viện nào** để chạy ứng dụng Web Studio, CLI và toàn bộ bộ kiểm thử tự động (`lexer_engine/`, `app.py`, `cli.py`, `tests/` chỉ dùng 100% Python Standard Library).
- Hỗ trợ chạy ngay trên **GitHub Codespaces** (`.devcontainer/devcontainer.json`) và **Render Cloud** (`render.yaml`).

---

## 3. Hướng dẫn chạy nhanh (Quick Start)

### 3.1. Chạy Giao diện Web Demo Trực Quan 5 Tab (`LexAutomata Studio`)
```bash
python3 app.py
```
- Chương trình tự khởi động máy chủ tại **`http://127.0.0.1:8000`** (hoặc đổi cổng: `python3 app.py --port 8765 --no-browser`).

**Các tính năng nổi bật trên 5 Tab của Web Studio:**
1. **Tab 1 — Bộ Quét & Mô Phỏng Từng Bước:** Nhập mã nguồn (hỗ trợ cả chuỗi tiếng Việt UTF-8 `"Xin chào UEH"` và bình luận nhiều dòng `/* ... */`), chuyển đổi trực tiếp giữa 2 chế độ phục hồi lỗi **`Panic-mode (1 ký tự)`** và **`Smart-Sync (Gom chuỗi/comment chưa đóng)`**, xem số lần cắt nhánh `memoized_cutoffs` (Reps, 1998) và chạy hoạt ảnh DFA từng bước.
2. **Tab 2 — 6 Phương pháp Automata Tổng Hợp & Chứng minh Myhill–Nerode:** Trực quan hóa đồ thị SVG có kéo-thả/zoom cho cả 6 mô hình (`Moore Min-DFA`, `Hopcroft Min-DFA`, `Subset DFA`, `Combined Direct DFA`, `NFA Khử ε`, `Combined ε-NFA`), xem bảng chuyển trạng thái, các bước phân hoạch `Π₀ → Π_k`, bảng chuỗi phân biệt **Myhill–Nerode** cho từng cặp trạng thái, cảnh báo **Shadowed Rules** và xuất file `.jff` chuẩn JFLAP.
3. **Tab 3 — Phòng Thí Nghiệm RE Đơn Lẻ & Kiểm Chứng 2 RE (`R₁ ≡ R₂?`):** Kiểm chứng trực tiếp các ví dụ trong Slide Chương 3.1 (`(a|b)*abb`, `(a|ba)(a|b)*ba`, `BLOCK_COMMENT`, định lượng `{m,n}`) kèm **Cây phân tích `r·#`** (`nullable`, `FP`, `LP`), **Bảng `followpos`**, và công cụ nhập 2 biểu thức chính quy bất kỳ để máy chứng minh tương đương hoặc sinh phản ví dụ ngắn nhất.
4. **Tab 4 — Đặc Tả Token (Live RE Editor & Shadowed Rule Trap):** Thêm/xóa/sửa biểu thức chính quy, thêm nhanh `HEX_LIT`, hoặc thử đẩy `IDENTIFIER` lên trên `KW_IF` để xem hệ thống phát hiện tự động **Quy tắc bị che khuất (Shadowed Token Rule)**.
5. **Tab 5 — Kiểm Thử Tự Động (62/62 PASS) & Benchmark Chống Quay Lui O(n²):** Chạy trực tiếp 62 ca kiểm thử JSON, bảng đối sánh 6 phương pháp Automata trên 3 ngôn ngữ và biểu đồ Stress Test 10.000 ký tự lỗi (`"aaaa...`, `/*xxxx...`, `"\"\"...`).

### 3.2. Chạy Giao diện Dòng Lệnh (CLI) & Kiểm thử Tự động
```bash
# 1. Chạy toàn bộ 62/62 ca kiểm thử có cấu trúc từ tests/test_cases.json
python3 cli.py test

# 2. Chạy 16/16 bộ Unittest kiểm chứng 5 bất biến toán học, Fuzzing & JFLAP Round-Trip
python3 tests/test_suite.py

# 3. Chạy Benchmark đối sánh 6 phương pháp Automata & Stress Test O(n) trên 3 ngôn ngữ
python3 cli.py benchmark

# 4. Quét mã nguồn với chế độ phục hồi lỗi Panic-mode hoặc Smart-Sync
python3 cli.py scan --preset minilang --file data/samples/demo_minilang_valid.mini
python3 cli.py scan --preset minilang --file data/samples/demo_minilang_errors.mini --recovery smart_sync

# 5. Phân tích chi tiết 1 Biểu thức chính quy qua chuỗi 6 Otomat + Myhill-Nerode (Slide 38 & Slide 54)
python3 cli.py inspect "(a|b)*abb" --name SLIDE38 --test abb aabb babb ab ba
python3 cli.py inspect "(a|ba)(a|b)*ba" --name SLIDE54 --test aba baba aabba ba a abb

# 6. Xuất DFA sang định dạng JFLAP (.jff)
python3 cli.py export-jff --pattern "(a|b)*abb" --stage min_dfa --expand --out data/jflap_exports/custom_abb.jff
```

---

## 4. Kết quả Thực nghiệm Tổng hợp trên 3 Ngôn ngữ

| Ngôn ngữ (Số quy tắc) | Thompson ε-NFA | NFA Khử ε (ĐL 2) | Subset DFA | Combined Direct DFA | Moore Min-DFA | Hopcroft Min-DFA | Cặp phân biệt Myhill–Nerode | Tương đương 6-Way |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **`MiniLang`** (39 token) | 170 TT | 96 TT | 86 TT | 79 TT | **78 TT** (-9.3%) | **78 TT** (-9.3%) | **3.003 / 3.003** (100%) | ✓ 0 phản ví dụ |
| **`CalcLang`** (12 token) | 57 TT | 26 TT | 24 TT | 20 TT | **20 TT** (-16.7%) | **20 TT** (-16.7%) | **190 / 190** (100%) | ✓ 0 phản ví dụ |
| **`MiniSQL`** (14 token) | 128 TT | 67 TT | 64 TT | 52 TT | **52 TT** (-18.8%) | **52 TT** (-18.8%) | **1.326 / 1.326** (100%) | ✓ 0 phản ví dụ |

---

## 5. Cấu trúc thư mục dự án

```
nnht_nhom-6_T13/
├── README.md                          # Tài liệu hướng dẫn cài đặt, kiến trúc & sử dụng
├── HUONG_DAN_BAO_VE.md                # Kịch bản thuyết trình 9.5 phút & 32 câu Q&A phản biện chuyên sâu
├── LOI_THOAI_13_SLIDE_VA_ON_TAP.md    # Lời thoại chi tiết từng slide & Flashcard ôn tập Chương 1-3
├── app.py                             # Máy chủ Web Studio + REST API (100% Python Standard Library)
├── cli.py                             # Công cụ dòng lệnh (scan, inspect, benchmark, export-jff, test)
├── .devcontainer/devcontainer.json    # Cấu hình chạy 1-Click trên GitHub Codespaces
├── render.yaml                        # Cấu hình triển khai Cloud trực tuyến trên Render
├── lexer_engine/                      # LÕI THUẬT TOÁN TỰ CÀI ĐẶT (100% Zero `import re`)
│   ├── __init__.py                    # Facade LexicalAnalyzer, phát hiện Shadowed Rules & inspect_single_regex
│   ├── models.py                      # Định nghĩa ASCII_SIGMA (98), NON_ASCII (0x80 UTF-8), NFA, DFA, Token, Error
│   ├── regex_parser.py                # Bộ phân tích RE đệ quy (AST, {m,n} n≤64, [-a], [a-], [^^], nullable)
│   ├── thompson.py                    # Thompson (RE → ε-NFA), Combined ε-NFA & Định lý 2 Khử ε (eliminate_epsilon)
│   ├── subset_construction.py         # Subset Construction (ε-closure, Move), Alphabet Partitioning & Priority
│   ├── direct_dfa.py                  # Direct RE → DFA cho RE đơn lẻ (r·#) & Đa-Token ((R₁·#₁)|...|(R_k·#_k))
│   ├── dfa_minimizer.py               # Tối thiểu hóa Multi-token DFA: Moore (Π₀→Π_k) & Hopcroft O(p·|Q|log|Q|)
│   ├── scanner.py                     # Bộ quét Maximal Munch O(n) (Reps 1998 failed_states, panic_char & smart_sync)
│   ├── verifier.py                    # Product Automaton 6-Way, Myhill–Nerode Minimality Proof & Compare 2 REs
│   ├── jflap_export.py                # Xuất & Đọc ngược (Round-Trip) XML .jff tương thích JFLAP 7.x
│   └── presets.py                     # 3 bộ đặc tả ngôn ngữ (MiniLang 39, CalcLang 12, MiniSQL 14) & mẫu thử
├── web/                               # Giao diện Web SPA 5 Tab (HTML5 + CSS3 + SVG/JS thuần)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   ├── specs/                         # File JSON đặc tả token cho MiniLang (39 token), CalcLang, MiniSQL
│   ├── samples/                       # File mã nguồn mẫu (hợp lệ, trường hợp biên, lỗi từ vựng)
│   └── jflap_exports/                 # File .jff sinh sẵn để đối chứng trực tiếp trên JFLAP 7.x
├── tests/
│   ├── test_cases.json                # 62 test cases có cấu trúc (16 RE đơn, 20 bẫy lỗi RE, 26 ca quét)
│   └── test_suite.py                  # 16 bộ Unittest kiểm chứng 5 bất biến toán học, Fuzzing & JFLAP Round-Trip
├── scripts/                           # Script tái tạo biểu đồ, báo cáo DOCX/PDF (14 trang) và slide PPTX (13 slide)
│   ├── generate_figures.py
│   ├── generate_report.py
│   └── generate_slides.py
└── deliverables/                      # Sản phẩm báo cáo & thuyết trình nộp cuối kỳ
    ├── Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.docx
    ├── Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.pdf
    └── Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx
```
