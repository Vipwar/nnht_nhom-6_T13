# Đề tài T13: Automata-based Lexical Analyzer (`LexAutomata Studio`)

> **Học phần:** Ngôn ngữ hình thức (*Introduction to Formal Languages*) — Mã lớp: `26C1INF50915301`  
> **Trường:** Đại học Kinh tế TP.HCM (UEH) — Khoa Công nghệ Thông tin Kinh doanh  
> **Giảng viên hướng dẫn:** ThS. Hồ Thị Thanh Tuyến  

---

## 1. Giới thiệu tổng quan

**LexAutomata Studio** là bộ sinh và thực thi **Bộ phân tích từ vựng dựa trên Automata (Automata-based Lexical Analyzer)** được cài đặt **100% từ đầu bằng Python thuần** (hoàn toàn **không sử dụng** thư viện `re` của Python hay bất kỳ thư viện regex/lexer ngoài nào trong toàn bộ lõi `lexer_engine/`).

Chương trình thể hiện trực tiếp, tường minh mối liên hệ giữa **Lý thuyết Ngôn ngữ hình thức & Automata** với **Kỹ thuật trình biên dịch (Compiler Construction)** thông qua toàn bộ đường ống:

```
Tập Token Specs (RE)
   │
   ├─► [1] Hand-written Recursive-Descent Regex Parser (AST + Postfix)
   ├─► [2] Thompson's Construction ──► Combined Multi-token ε-NFA
   ├─► [3] Subset Construction (ε-closure, Move + Alphabet Partitioning + Rule Priority) ──► Combined DFA
   ├─► [4] Multi-token DFA Minimization (Partition Refinement Π₀ → Π_final) ──► Minimized Combined DFA
   ├─► [5] Product Automaton Equivalence Checker ──► Chứng minh toán học Subset DFA ≡ Min-DFA
   └─► [6] DFA-driven Lexical Scanner (Maximal Munch, Backtracking, Line/Col, Panic-mode Recovery)
```

Ngoài ra, dự án cài đặt song song phương pháp **Direct RE → DFA** (Cây phân tích biểu thức chính quy gia tố `r·#`, tính `nullable`, `firstpos`, `lastpos`, `followpos` — khớp chính xác Chương 3.1 bài giảng UEH) để đối chứng và chứng minh tương đương trên từng biểu thức chính quy đơn lẻ, đồng thời hỗ trợ **xuất định dạng `.jff` (JFLAP)** để kiểm chứng độc lập trên phần mềm JFLAP.

---

## 2. Yêu cầu môi trường & Cài đặt

- **Python 3.10+** (đã kiểm thử trên Python 3.12).
- **Không cần cài đặt thư viện bên thứ ba** để chạy ứng dụng Web Demo, CLI và bộ kiểm thử tự động (`lexer_engine/`, `app.py`, `cli.py`, `tests/` chỉ dùng hoàn toàn Thư viện Chuẩn Python).
- Trình duyệt web hiện đại (Chrome, Edge, Firefox) để sử dụng giao diện Web Studio trực quan.

---

## 3. Hướng dẫn chạy nhanh (Quick Start)

Mở Terminal / PowerShell tại thư mục gốc `T13_Automata_Lexical_Analyzer/`:

### 3.1. Chạy Giao diện Web Demo Trực Quan (Khuyến nghị cho buổi bảo vệ)
```bash
python app.py
```
- Chương trình tự khởi động máy chủ cục bộ tại **`http://127.0.0.1:8000`** và tự động mở trình duyệt.
- Tùy chọn đổi cổng hoặc tắt tự mở trình duyệt:
  ```bash
  python app.py --port 8080 --no-browser
  ```

**Các tính năng chính trên Web Studio (5 Tab):**
1. **Bộ Quét & Mô Phỏng Từng Bước:** Nhập mã nguồn hoặc chọn mẫu (`Hợp lệ`, `Trường hợp biên`, `Lỗi & Phục hồi`), xem tô màu trực tiếp theo token, bảng luồng token, và **mô phỏng chuyển động từng bước DFA** (băng ký tự + sơ đồ đường đi trạng thái + hiển thị quay lui Maximal Munch).
2. **Automata Tổng Hợp & Tối Thiểu Hóa:** Trực quan hóa SVG có kéo-thả/phóng to-thu nhỏ cho `Minimized DFA`, `Subset DFA`, `Combined ε-NFA`, **Bảng chuyển trạng thái**, **Các bước phân hoạch tối thiểu hóa (`Π₀ → Πₙ`)**, danh sách xung đột ưu tiên đã giải quyết, và nút xuất `.svg` / **JFLAP `.jff`**.
3. **Phòng Thí Nghiệm RE Đơn Lẻ:** Kiểm chứng song song 2 phương pháp trong Slide Chương 3.1 (`(a|b)*abb`, `(a|ba)(a|b)*ba`, `FLOAT_LIT`, `IDENTIFIER`, `STRING_LIT`) kèm **Cây phân tích `r·#`** (`nullable`, `FP`, `LP`), **Bảng `followpos`**, và kiểm tra chuỗi đồng thời trên `ε-NFA`, `Direct-DFA`, `Minimized-DFA`.
4. **Đặc Tả Token (Live RE Editor):** Thêm/xóa/sửa biểu thức chính quy hoặc đổi độ ưu tiên (có nút thêm nhanh `HEX_LIT: 0[xX][0-9a-fA-F]+`) và biên dịch lại toàn bộ Automata trực tiếp trong vài mili-giây.
5. **Kiểm Thử Tự Động & Benchmark:** Chạy toàn bộ 29 test case chuẩn (valid, edge, invalid) và bảng đo hiệu năng biên dịch + quét 10 KB mã nguồn trên cả 3 bộ ngôn ngữ (`MiniLang`, `CalcLang`, `MiniSQL`).

### 3.2. Chạy Giao diện Dòng Lệnh (CLI)
```bash
# Quét file mẫu MiniLang hợp lệ
python cli.py scan --preset minilang --file data/samples/demo_minilang_valid.mini

# Quét các trường hợp biên (Maximal Munch & Rule Priority)
python cli.py scan --preset minilang --file data/samples/demo_minilang_edge_cases.mini

# Quét các trường hợp lỗi & phục hồi Panic-mode
python cli.py scan --preset minilang --file data/samples/demo_minilang_errors.mini

# Phân tích chi tiết 1 Biểu thức chính quy (khớp Slide 46-57 Chương 3.1)
python cli.py inspect "(a|ba)(a|b)*ba" --name SLIDE46 --test aba baba aabba ba a abb

# Chạy benchmark so sánh trên cả 3 ngôn ngữ
python cli.py benchmark

# Xuất DFA sang định dạng JFLAP (.jff) để đối chứng
python cli.py export-jff --pattern "(a|b)*abb" --stage min_dfa --expand --out data/jflap_exports/custom_abb.jff

# Chạy toàn bộ test case từ data JSON
python cli.py test
```

### 3.3. Chạy Bộ Kiểm Thử Đơn Vị & Tích Hợp (`unittest`)
```bash
python tests/test_suite.py
```
Bộ kiểm thử tự động kiểm tra:
- Không tồn tại `import re` trong toàn bộ `lexer_engine/`.
- Khớp chính xác số trạng thái & bảng `followpos` với các ví dụ trên slide bài giảng Chương 3.1 UEH.
- Chứng minh tương đương toán học `Subset DFA ≡ Minimized DFA` bằng Product Automaton trên cả 3 ngôn ngữ.
- Kiểm chứng chéo độc lập với Python `re` (chỉ dùng làm oracle trong file test) và kiểm chứng NFA vs DFA.
- 29 test case phân loại đầy đủ: hợp lệ (`valid`), biên (`edge`), và không hợp lệ (`invalid`).

---

## 4. Cấu trúc thư mục dự án

```
T13_Automata_Lexical_Analyzer/
├── README.md                          # Tài liệu hướng dẫn cài đặt & sử dụng
├── HUONG_DAN_BAO_VE.md                # Kịch bản thuyết trình 10 phút & 20 câu Q&A bảo vệ cá nhân
├── app.py                             # Máy chủ Web Studio (chỉ dùng thư viện chuẩn Python)
├── cli.py                             # Công cụ dòng lệnh (scan, inspect, benchmark, export-jff, test)
├── lexer_engine/                      # LÕI THUẬT TOÁN TỰ CÀI ĐẶT (100% không dùng `re`)
│   ├── __init__.py                    # Facade LexicalAnalyzer & inspect_single_regex
│   ├── models.py                      # Định nghĩa hình thức Σ, NFA, DFA, Token, Error, Trace, Alphabet Partition
│   ├── regex_parser.py                # Bộ phân tích RE đệ quy (AST, explicit infix, postfix, nullable)
│   ├── thompson.py                    # Thuật toán Thompson (RE → ε-NFA) & Combined Multi-token ε-NFA
│   ├── subset_construction.py         # Thuật toán tập con (ε-closure, Move) & giải quyết xung đột ưu tiên
│   ├── direct_dfa.py                  # Xây dựng DFA trực tiếp từ RE qua r#, nullable, FP, LP, followpos
│   ├── dfa_minimizer.py               # Tối thiểu hóa Multi-token DFA bằng tinh chỉnh phân hoạch (Π₀ → Πₙ)
│   ├── scanner.py                     # Bộ quét DFA: Maximal Munch, Backtracking, Line/Col, Error Recovery
│   ├── verifier.py                    # Product Automaton Equivalence Checker (sinh phản ví dụ ngắn nhất)
│   ├── jflap_export.py                # Xuất NFA/DFA sang XML .jff tương thích JFLAP 7.x
│   └── presets.py                     # 3 bộ đặc tả ngôn ngữ (MiniLang, CalcLang, MiniSQL) & dữ liệu mẫu
├── web/                               # Giao diện Web SPA trực quan (HTML5 + CSS3 + SVG/JS thuần)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   ├── specs/                         # File JSON đặc tả token cho MiniLang, CalcLang, MiniSQL
│   ├── samples/                       # 5 file mã nguồn mẫu (hợp lệ, biên, lỗi)
│   └── jflap_exports/                 # 4 file .jff sinh sẵn để đối chứng trực tiếp trên JFLAP
├── tests/
│   ├── test_cases.json                # 29 test case có cấu trúc (valid / edge / invalid)
│   └── test_suite.py                  # Bộ unit test & integration test tự động
├── scripts/                           # Script tái tạo biểu đồ, báo cáo DOCX/PDF và slide PPTX
│   ├── generate_figures.py
│   ├── generate_report.py
│   └── generate_slides.py
└── deliverables/                      # Sản phẩm báo cáo & thuyết trình nộp cuối kỳ
    ├── Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.docx
    ├── Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.pdf
    └── Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx
```

---

## 5. Phân tách rõ phần tự cài đặt và thư viện

| Thành phần | Tự cài đặt bởi nhóm | Thư viện sử dụng |
|---|---|---|
| Bộ phân tích RE (AST, lớp ký tự, thoát ký tự, báo lỗi cú pháp) | **100%** (`regex_parser.py`) | Không |
| Cấu trúc Thompson (`RE → ε-NFA`, Combined Multi-token NFA) | **100%** (`thompson.py`) | Không |
| Subset Construction (`ε-closure`, `Move`, Alphabet Partitioning, Priority) | **100%** (`subset_construction.py`) | Không |
| Direct RE → DFA (`r#`, `nullable`, `firstpos`, `lastpos`, `followpos`) | **100%** (`direct_dfa.py`) | Không |
| Tối thiểu hóa Multi-token DFA (`Π₀ → Πₙ`, loại trạng thái chết) | **100%** (`dfa_minimizer.py`) | Không |
| Bộ quét từ vựng Maximal Munch + Error Recovery + Step Trace | **100%** (`scanner.py`) | Không |
| Kiểm chứng tương đương bằng Product Automaton | **100%** (`verifier.py`) | Không |
| Xuất JFLAP `.jff` & Web UI + SVG Graph Visualizer | **100%** (`jflap_export.py`, `web/`, `app.py`) | Chỉ dùng Python stdlib (`http.server`, `json`, `dataclasses`, `unittest`) |
| Kiểm thử đối chứng độc lập (chỉ trong file test) | Tự viết test case (`tests/`) | Python `re` **chỉ làm oracle kiểm chứng** trong `test_suite.py` |
| Sinh hình báo cáo & xuất tài liệu DOCX/PDF/PPTX (ngoài runtime) | Script tự động (`scripts/`) | `graphviz`, `matplotlib`, `python-docx`, `python-pptx` |
