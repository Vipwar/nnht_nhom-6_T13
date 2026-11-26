# Đề tài T13: Xây dựng Bộ phân tích từ vựng dựa trên Automata (Automata-based Lexical Analyzer)

[![T13 Automata Lexical Analyzer CI](https://github.com/Vipwar/nnht_nhom-6_T13/actions/workflows/ci.yml/badge.svg)](https://github.com/Vipwar/nnht_nhom-6_T13/actions/workflows/ci.yml)

- **Học phần:** Ngôn ngữ hình thức (*Introduction to Formal Languages*) — Mã lớp: `26C1INF50915301`
- **Trường:** Đại học Kinh tế TP.HCM (UEH) — Khoa Công nghệ Thông tin Kinh doanh (CTD)
- **Giảng viên hướng dẫn:** ThS. Hồ Thị Thanh Tuyến
- **Nhóm thực hiện:** Nhóm 6

---

## 1. Giới thiệu đồ án

Đồ án cài đặt **Bộ phân tích từ vựng dựa trên Automata (Automata-based Lexical Analyzer)** bằng ngôn ngữ Python chỉ sử dụng thư viện chuẩn (không sử dụng `import re` hay bất kỳ thư viện phân tích từ vựng bên thứ ba nào trong `lexer_engine/`, `app.py`, `cli.py` và mã bộ quét độc lập sinh tự động).

Chương trình minh họa mối liên hệ giữa lý thuyết Ngôn ngữ hình thức và Automata (Chương 1, 2, 3) với bài toán xây dựng bộ quét từ vựng trong trình biên dịch thông qua quy trình biên dịch khép kín hai chiều của Định lý Kleene:

```
Tập đặc tả Token (Biểu thức chính quy + Độ ưu tiên + Cờ bỏ qua)
  |
  +-- [1] Bộ phân tích cú pháp RE đệ quy (giới hạn MAX_AST_NODES = 4096, hỗ trợ {m,n})
  |        +-- Bảng chữ cái động Σ(U) = 128 ASCII (0x00..0x7F) ∪ U ∪ {NON_ASCII U+FDD0} (~(~A) = A)
  +-- [2] Cấu trúc Thompson (Định lý 3, Slide 24-30) -> Combined ε-NFA
  +-- [3] Khử chuyển tiếp ε (Định lý 2, Slide 21-22) -> Combined NFA không có ε
  +-- [4] Đơn định hóa tập con (Định lý 1 + phân hoạch bảng chữ cái + độ ưu tiên) -> Subset DFA
  +-- [5] Tối thiểu hóa DFA đa-token và lấy phần bù:
  |        +-- Thuật toán Moore O(p·|Q|²) (xuất bảng phân hoạch Π₀ -> Π₁ -> ... -> Π_k)
  |        +-- Thuật toán Hopcroft O(p·|Q|log|Q|) và hàm complement_dfa (~(~L) = L)
  +-- [6] Phương pháp trực tiếp RE -> DFA (cây cú pháp r·# và đa-token (R₁·#₁)|...|(R_k·#_k), followpos)
  +-- [7] Khử trạng thái GNFA (chiều ngược Định lý Kleene: Min-DFA -> R_sinh, kiểm tra L(R_gốc) ≡ L(R_sinh))
  +-- [8] Kiểm chứng hình thức và phân tích tĩnh:
  |        +-- Đối chiếu tương đương bằng Product Automaton BFS giữa các mô hình
  |        +-- Ma trận giao nhau tĩnh L(Rᵢ) ∩ L(Rⱼ) kèm chuỗi chứng nhân ngắn nhất và cảnh báo luật che khuất
  |        +-- Kiểm tra tính tối giản Myhill-Nerode (chuỗi phân biệt ngắn nhất cho từng cặp trạng thái)
  |        +-- Xuất và đọc ngược định dạng XML (.jff) tương thích JFLAP 7.x
  +-- [9] Thực thi quét từ vựng và sinh mã:
           +-- Bộ quét Maximal Munch tuyến tính O(n) (bảng nhớ failed_states theo Reps 1998, Panic-mode / Smart-Sync)
           +-- Bộ sinh mã Lexer Python độc lập kiểu Flex (codegen.py -> file .py chạy độc lập)
```

---

## 2. Yêu cầu môi trường

- **Python 3.10 trở lên** (đã kiểm thử trên Python 3.10, 3.11, 3.12 qua GitHub Actions).
- Không cần cài đặt thêm gói thư viện ngoài để chạy giao diện Web, giao diện dòng lệnh CLI, bộ quét độc lập sinh ra hay bộ kiểm thử tự động.

---

## 3. Hướng dẫn chạy chương trình

### 3.1. Chạy giao diện Web (5 tab)
```bash
python3 app.py
```
Máy chủ mặc định chạy tại địa chỉ `http://127.0.0.1:8000` (có thể đổi cổng bằng `python3 app.py --port 8765 --no-browser`). Trên góc phải thanh công cụ có nút chuyển chế độ nền `Dark` / `Light`, nút `Xuất Lexer (.py)` và `Xuất .jff`.

Nội dung 5 tab chính:
1. **Tab 1 — Bộ quét từ vựng:** Nhập mã nguồn (hỗ trợ tiếng Việt UTF-8, xuống dòng CRLF `\r\n`, bình luận nhiều dòng `/* ... */`), chọn chế độ phục hồi lỗi `Panic-mode (1 ký tự)` hoặc `Smart-Sync`, theo dõi quá trình chạy từng bước trên DFA và xem số lần cắt nhánh `memoized_cutoffs`.
2. **Tab 2 — Đồ thị Automata và Tối thiểu hóa:** Quan sát đồ thị SVG của 4 giai đoạn ô-tô-mát đa-token, bảng chuyển trạng thái, các bước phân hoạch Moore / Hopcroft kèm chứng nhân Myhill-Nerode, và ma trận giao nhau tĩnh `L(Rᵢ) ∩ L(Rⱼ)`.
3. **Tab 3 — Phân tích Biểu thức chính quy đơn lẻ:** Thử nghiệm các biểu thức bài giảng Chương 3.1 (`(a|b)*abb`, `(a|ba)(a|b)*ba`), biểu thức chứa ký tự Unicode tường minh `(nếu|lặp)_[0-9]+€`, xem cây cú pháp `r·#`, bảng `followpos`, từng bước khử đỉnh GNFA (`DFA -> RE`) và kiểm tra tương đương hai biểu thức `R₁ ≡ R₂`.
4. **Tab 4 — Đặc tả Token:** Chỉnh sửa danh sách quy tắc từ vựng trực tiếp, thêm quy tắc mẫu Unicode (`nếu`, `€`) hoặc số thập lục phân (`0xFF`), thử tình huống quy tắc bị che khuất (`IDENTIFIER` đặt trước `KW_IF`) và xuất file bộ quét `.py` độc lập.
5. **Tab 5 — Kiểm thử và Hiệu năng:** Chạy 72 test case JSON có cấu trúc, xem thống kê trạng thái trên 3 bộ ngôn ngữ và kết quả kiểm tra độ phức tạp tuyến tính $O(n)$ trên dữ liệu lỗi 10.000 ký tự.

### 3.2. Các lệnh trên giao diện dòng lệnh (CLI)
```bash
# 1. Chạy 72 ca kiểm thử từ tests/test_cases.json
python3 cli.py test

# 2. Chạy 22 nhóm unittest kiểm tra bất biến toán học và đối chứng mã sinh
python3 tests/test_suite.py -v

# 3. Chuyển Min-DFA ngược về biểu thức chính quy bằng GNFA (chiều ngược Định lý Kleene)
python3 cli.py gnfa "(a|b)*abb"
python3 cli.py gnfa "(nếu|lặp)_[0-9]+€"

# 4. Phân tích tĩnh ma trận giao nhau L(R_i) ∩ L(R_j) và chuỗi chứng nhân ngắn nhất
python3 cli.py intersections --preset minilang

# 5. Sinh file bộ quét từ vựng Python độc lập kiểu Flex (không phụ thuộc lexer_engine)
python3 cli.py codegen --preset minilang -o minilang_lexer.py
python3 minilang_lexer.py --code 'let x = 42; if (x >= 10) { print("Xin chào UEH"); }'

# 6. Chạy benchmark thời gian biên dịch và quét 10 KB trên 3 ngôn ngữ
python3 cli.py benchmark

# 7. Quét mã nguồn từ file với chế độ Panic-mode hoặc Smart-Sync
python3 cli.py scan --preset minilang --file data/samples/demo_minilang_valid.mini
python3 cli.py scan --preset minilang --file data/samples/demo_minilang_errors.mini --error-recovery smart_sync

# 8. Phân tích chi tiết 1 biểu thức chính quy (ví dụ Slide 38 và Slide 54 Chương 3.1)
python3 cli.py inspect "(a|b)*abb" --name SLIDE38 --test abb aabb babb ab ba
python3 cli.py inspect "(a|ba)(a|b)*ba" --name SLIDE54 --test aba baba aabba ba a abb

# 9. Kiểm tra tương đương 2 biểu thức chính quy và xuất file JFLAP 7.x (.jff)
python3 cli.py equiv "(a|b)*" "(a*b*)*"
python3 cli.py export-jff --pattern "(a|b)*abb" --stage min_dfa --expand -o data/jflap_exports/custom_abb.jff
```

---

## 4. Tóm tắt kết quả thực nghiệm trên 3 ngôn ngữ mẫu

| Ngôn ngữ (số quy tắc) | Thompson ε-NFA | NFA khử ε (ĐL 2) | Subset DFA | Combined Direct DFA | Moore / Hopcroft Min-DFA | Lớp Σ(U)/≡ | Myhill-Nerode | Giao nhau L(Rᵢ)∩L(Rⱼ) | Đối chiếu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `MiniLang` (39 token) | 170 TT | 96 TT | 86 TT | 79 TT | 78 / 78 TT (-9.3%) | 44 lớp | 3.003 / 3.003 | 9 / 741 (0 che khuất) | Khớp |
| `CalcLang` (12 token) | 57 TT | 26 TT | 24 TT | 20 TT | 20 / 20 TT (-16.7%) | 19 lớp | 190 / 190 | 2 / 66 (0 che khuất) | Khớp |
| `MiniSQL` (14 token) | 128 TT | 67 TT | 64 TT | 52 TT | 52 / 52 TT (-18.8%) | 44 lớp | 1.326 / 1.326 | 5 / 91 (0 che khuất) | Khớp |

---

## 5. Cấu trúc thư mục

```
nnht_nhom-6_T13/
|-- README.md                          # Hướng dẫn cài đặt và sử dụng chương trình
|-- HUONG_DAN_BAO_VE.md                # Kịch bản trình bày demo và 38 câu hỏi ôn tập phản biện
|-- LOI_THOAI_13_SLIDE_VA_ON_TAP.md    # Lời thoại theo từng slide và tóm tắt kiến thức Chương 1-3
|-- app.py                             # Máy chủ Web và REST API (thư viện chuẩn http.server)
|-- cli.py                             # Giao diện dòng lệnh CLI (9 lệnh)
|-- .devcontainer/devcontainer.json    # Cấu hình môi trường GitHub Codespaces
|-- render.yaml                        # Cấu hình triển khai trên Render
|-- lexer_engine/                      # Lõi thuật toán tự cài đặt (không dùng import re)
|   |-- __init__.py                    # Lớp điều phối LexicalAnalyzer
|   |-- models.py                      # Bảng chữ cái 128 ASCII, NON_ASCII (U+FDD0), Σ(U), NFA, DFA
|   |-- regex_parser.py                # Bộ phân tích RE đệ quy (MAX_AST_NODES=4096, {m,n}, \xHH, \uHHHH)
|   |-- thompson.py                    # Cấu trúc Thompson (RE -> ε-NFA) và khử ε (eliminate_epsilon)
|   |-- subset_construction.py         # Đơn định hóa tập con, phân hoạch bảng chữ cái và độ ưu tiên
|   |-- direct_dfa.py                  # Phương pháp trực tiếp RE -> DFA (followpos) đơn lẻ và đa-token
|   |-- dfa_minimizer.py               # Tối thiểu hóa Moore, Hopcroft và lấy phần bù DFA
|   |-- gnfa.py                        # Khử trạng thái GNFA (DFA -> RE) theo Định lý Kleene
|   |-- scanner.py                     # Bộ quét Maximal Munch O(n) (Reps 1998, panic_char, smart_sync)
|   |-- codegen.py                     # Bộ sinh mã Lexer Python độc lập điều khiển bằng bảng
|   |-- verifier.py                    # Kiểm chứng Product Automaton, Myhill-Nerode và ma trận giao nhau
|   |-- jflap_export.py                # Xuất và đọc ngược file XML .jff cho JFLAP 7.x
|   +-- presets.py                     # 3 bộ đặc tả ngôn ngữ (MiniLang, CalcLang, MiniSQL)
|-- web/                               # Giao diện Web 5 tab (HTML, CSS, JavaScript thuần)
|   |-- index.html
|   |-- styles.css
|   +-- app.js
|-- data/
|   |-- specs/                         # Đặc tả JSON cho MiniLang, CalcLang, MiniSQL
|   |-- samples/                       # Các tệp mã nguồn mẫu
|   +-- jflap_exports/                 # Các tệp .jff xuất sẵn để mở trên JFLAP 7.x
|-- tests/
|   |-- test_cases.json                # 72 test case JSON có cấu trúc
|   +-- test_suite.py                  # 22 nhóm unittest tự động
|-- scripts/                           # Script tạo hình minh họa, báo cáo DOCX/PDF và slide PPTX
|   |-- generate_figures.py
|   |-- generate_report.py
|   +-- generate_slides.py
+-- deliverables/                      # Tài liệu nộp cuối kỳ (Báo cáo DOCX, PDF và Slide PPTX)
    |-- Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.docx
    |-- Bao_Cao_Do_An_T13_Automata_Lexical_Analyzer.pdf
    +-- Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx
```
