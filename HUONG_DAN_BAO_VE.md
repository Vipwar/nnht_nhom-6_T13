# CẨM NANG THUYẾT TRÌNH, DEMO & PHẢN BIỆN ĐẠT 10/10 TUYỆT ĐỐI — ĐỀ TÀI T13

> **Học phần:** Ngôn ngữ hình thức (*Introduction to Formal Languages*) — UEH  
> **Giảng viên hướng dẫn:** ThS. Hồ Thị Thanh Tuyến  
> **Đề tài T13:** Automata-based Lexical Analyzer (`LexAutomata Studio`)  
> **Mục tiêu:** Mọi thành viên trong nhóm nắm chắc lý thuyết Chương 1–3, chỉ đúng từng hàm trong mã nguồn và trả lời sắc bén mọi câu hỏi xoáy của Giảng viên trong buổi bảo vệ (15 phút: **8–10 phút trình bày + demo**, **5–7 phút hỏi đáp**).

---

## PHẦN 1: KỊCH BẢN TRÌNH BÀY & LIVE DEMO 9.5 PHÚT (ĂN TRỌN 100% RUBRIC)

| Thời lượng | Thành viên | Nội dung trình bày & Thao tác Live Demo | Điểm nhấn ăn điểm tuyệt đối với Cô Tuyến |
|---|---|---|---|
| **0:00 – 1:30** | **TV 1** (Trưởng nhóm & Lý thuyết) | **Slide 1–3:** Giới thiệu vai trò Lexical Analyzer; khép kín **Vòng tròn Định lý Kleene 360°** (`RE ⇄ Thompson ε-NFA ⇄ NFA Khử ε ⇄ Subset/Direct DFA ⇄ Moore/Hopcroft Min-DFA ⇄ GNFA RE`); giải thích bảng chữ cái Unicode động $\Sigma(U) = 128\text{ ASCII} \cup U \cup \{\text{NON\_ASCII}\}$ bảo toàn đại số Boole $\sim(\sim A) = A$. | Nhấn mạnh **Zero `import re`** trong lõi, chống bom AST `MAX_AST_NODES = 4096`, và hỗ trợ đồng thời cả từ khóa tiếng Việt `nếu`, ký hiệu `€` lẫn chuỗi UTF-8! |
| **1:30 – 3:45** | **TV 2** (Regex Parser, Thompson, Khử ε, Direct DFA & GNFA) | **Slide 4–6 + Mở Tab 3 Web Studio:**<br>1. Chọn `(a\|b)*abb (Slide 38)` → chỉ rõ: Thompson ε-NFA = **11 TT**, NFA Khử ε (ĐL 2) = **6 TT**, Subset DFA = **5 TT**, Min-DFA = **4 TT**, rồi bấm thẻ **6. GNFA Khử Trạng Thái** chỉ quá trình khử đỉnh sinh `b*a(a\|ba\|bb(a\|b+a))*bb` chứng minh $L(R_0) \equiv L(R_{\text{sinh}})$!<br>2. Chọn `(a\|ba)(a\|b)*ba (Slide 54)` → chỉ cây `r·#` 8 lá & bảng `followpos` khớp Slide 54.<br>3. Bấm chip `Unicode Động: (nếu\|lặp)_[0-9]+€` để minh họa $\Sigma(U)$. | Cô thấy trọn vẹn cả chiều xuôi lẫn chiều ngược của Định lý Kleene 360° + 2 ví dụ Slide Chương 3.1 chạy trực tiếp! |
| **3:45 – 5:45** | **TV 3** (Subset, Moore/Hopcroft, Myhill–Nerode & Ma trận Giao) | **Slide 7 + Mở Tab 2 & Tab 4 Web Studio:**<br>1. Trên **Tab 2 (`MiniLang`)**: mở thẻ **Ma Trận Giao Nhau $L(R_i) \cap L(R_j)$** → chỉ bản đồ nhiệt $39 \times 39$ phát hiện đúng **9/741 cặp giao nhau** (`KW_IF..BOOL_LIT` $\subset$ `IDENTIFIER`) kèm chứng nhân ngắn nhất (`'if'..'true'`) và xem bảng **Myhill–Nerode** (`3003/3003` cặp).<br>2. Qua **Tab 4**: bấm **`+ Thêm Unicode (nếu / €)`**, sau đó bấm **`⚠ Thử Che Khuất`** đưa `IDENTIFIER` lên trên `KW_IF` → bật **Biểu ngữ Đỏ Shadowed Rule** tức thì! | Phân tích tĩnh giao nhau ngôn ngữ $L(R_i) \cap L(R_j)$ bằng Product Automaton và chứng minh tối giản Myhill–Nerode! |
| **5:45 – 8:00** | **TV 4** (Scanner O(n), Smart-Sync & Flex Codegen) | **Slide 8–9 + Mở Tab 1 Web Studio:**<br>1. Quét mã UTF-8/CRLF, chiếu hoạt ảnh quay lui `1.5e + 2`, gạt công tắc **`Panic-mode`** vs **`Smart-Sync`** trên chuỗi chưa đóng.<br>2. Bấm nút **`⬇ Sinh Lexer (.py)`** trên thanh công cụ tải ngay file `minilang_lexer.py` (~527 dòng, kiểu Flex, 0 phụ thuộc ngoài, đối chứng vi sai 100%). | Trình diễn khả năng sinh mã trình biên dịch thực thụ (*Standalone Table-Driven Lexer Generator*) như công cụ `flex`/`lex`! |
| **8:00 – 9:30** | **TV 1 / TV 4** (Kiểm thử 72 Cases, Bổ đề Bơm & Kết luận) | **Slide 10–13 + Mở Tab 5 Web Studio:**<br>1. Bấm chạy **72/72 Test Cases PASS (100%)** + **22/22 Unittest Suites** và chỉ bảng **Stress Test 10.000 ký tự lỗi** (`memoized_cutoffs = 5000`).<br>2. Nêu rõ giới hạn lý thuyết DFA theo **Bổ đề Bơm (Chương 3.2)**: bình luận lồng nhau sâu tùy ý `/* /* ... */ */` đẳng cấu $L = \{a^n b^n \mid n \ge 1\}$ thuộc CFL. | Khép lại bằng kiến thức Bổ đề Bơm Chương 3.2 và bộ kiểm định 72 kịch bản không lỗ hổng! |

---

## PHẦN 2: BẢN ĐỒ MÃ NGUỒN (`lexer_engine/`) ĐỂ CHỈ TRỰC TIẾP KHI CÔ HỎI

1. **Bảng chữ cái 128 ASCII (`0x00..0x7F`) + Phân hoạch Unicode Động $\Sigma(U)$ & Đại số Boole**: [`lexer_engine/models.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/models.py) — phủ kín 128 mã ASCII (gồm cả `\0`, `\f`, `\v`, `\x7f`), sentinel noncharacter `NON_ASCII = "\ufdd0"` (Unicode §23.7), hàm `build_dynamic_sigma(U)` và `complement_charset()` bảo toàn $\sim(\sim A) = A$.
2. **Bộ phân tích cú pháp RE tự viết (Chống bom AST `MAX_AST_NODES = 4096`, `{m,n}`, `\xHH`, `\uHHHH`, Zero `import re`)**: [`lexer_engine/regex_parser.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/regex_parser.py) — lớp `RegexParser` đệ quy 4 mức ưu tiên; ước lượng kích thước cây con trong $O(1)$ chặn bom nhân bản `(((a{64}){64}){64})` trước khi cấp phát bộ nhớ; trích tự động tập `explicit_unicode_chars()`.
3. **Cấu trúc Thompson & Định lý 2 Khử chuyển tiếp $\varepsilon$ (`ε-NFA → NFA không ε`)**: [`lexer_engine/thompson.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/thompson.py) — lớp `_ThompsonBuilder` dựng mảnh ε-NFA theo Định lý 3; hàm `eliminate_epsilon(nfa)` cài đặt Định lý 2 (Slide 21–22 Chương 3.1).
4. **Đơn định hóa Tập con (Subset Construction) & Alphabet Partitioning**: [`lexer_engine/subset_construction.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/subset_construction.py) — nén $\Sigma(U)$ thành các lớp tương đương nhỏ nhất (`MiniLang`: 44 lớp) và giải quyết xung đột theo `priority`.
5. **Direct RE → DFA cho Biểu thức Đơn lẻ (`r·#`) & Đa-Token Kết hợp (`(R₁·#₁)|...|(R_k·#_k)`)**: [`lexer_engine/direct_dfa.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/direct_dfa.py) — hàm `build_direct_dfa()` và `build_combined_direct_dfa()` tính `nullable`, `firstpos`, `lastpos`, `followpos`.
6. **Tối thiểu hóa Song song Moore & Hopcroft $O(p \cdot |Q| \log |Q|)$ + Phần bù DFA**: [`lexer_engine/dfa_minimizer.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/dfa_minimizer.py) — `minimize_dfa()` (Moore), `minimize_dfa_hopcroft()` (Hopcroft) và `complement_dfa()` kiểm chứng $\sim(\sim D) \equiv D$.
7. **Khử Trạng Thái GNFA (`DFA → Regular Expression`) — Khép kín Định lý Kleene 360°**: [`lexer_engine/gnfa.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/gnfa.py) — hàm `dfa_to_regex()` chọn đỉnh khử tối thiểu hóa $\text{in\_deg} \times \text{out\_deg}$, rút gọn đại số Kleene và tự động chứng minh $L(R_0) \equiv L(R_{\text{sinh}})$.
8. **Kiểm chứng Tương đương, Myhill–Nerode & Ma trận Giao nhau Tĩnh $L(R_i) \cap L(R_j)$**: [`lexer_engine/verifier.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/verifier.py) — `check_dfa_equivalence()`, `verify_dfa_is_minimal()`, `check_dfa_intersection()` và `analyze_token_intersections()`.
9. **Bộ quét Maximal Munch Tuyến tính $O(n)$ (Reps, 1998) & Bộ sinh mã Lexer Độc lập Kiểu Flex**: [`lexer_engine/scanner.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/scanner.py) và [`lexer_engine/codegen.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/codegen.py) (`generate_standalone_lexer()`).
10. **Xuất & Đọc ngược Khứ hồi JFLAP 7.x (`.jff`)**: [`lexer_engine/jflap_export.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/jflap_export.py) — bảo toàn cả ký tự điều khiển XML 1.0 (`\v`, `\f`, `\0`) và Unicode động $\Sigma(U)$.

---

## PHẦN 3: 38 CÂU HỎI PHẢN BIỆN CHUYÊN SÂU & ĐÁP ÁN MẪU (CHỐNG MỌI CÂU HỎI XOÁY)

### Nhóm A — Nền tảng Lý thuyết Chương 1, 2, 3 & Mô hình Toán học

**Câu 1. Tại sao bộ phân tích từ vựng lại dùng Otomat hữu hạn (DFA/NFA) và Biểu thức chính quy mà không dùng Văn phạm phi ngữ cảnh (CFG) hay Otomat đẩy xuống (PDA)?**
> **Trả lời:** Vì hầu hết các cấu trúc từ vựng của ngôn ngữ lập trình (từ khóa, định danh, số nguyên, số thực, chuỗi ký tự, bình luận không lồng nhau) không có cấu trúc đệ quy tự lồng sâu tùy ý nên đều thuộc lớp **Ngôn ngữ chính quy (Regular Languages)**. Theo Định lý Kleene, mọi ngôn ngữ chính quy đều nhận diện được bằng một DFA trong thời gian tuyến tính chặt $O(n)$ với chi phí bộ nhớ $O(1)$ (mỗi ký tự chỉ tra bảng chuyển trạng thái 1 lần), nhanh hơn và đơn giản hơn rất nhiều so với các thuật toán phân tích CFG như CYK $O(n^3)$ hay Earley/LR.

**Câu 2. Trong bài giảng Chương 3.1 của cô có các định lý chuyển đổi hai chiều giữa FA và RE (Định lý Kleene). Nhóm đã cài đặt những định lý nào?**
> **Trả lời:** Nhóm đã cài đặt **trọn vẹn vòng tròn tương đương 360° của Định lý Kleene** trong Chương 3.1:
> - **Định lý 3 (Slide 24–30):** Chuyển Biểu thức chính quy sang $\varepsilon$-NFA bằng cấu trúc Thompson (`thompson.py`).
> - **Định lý 2 (Slide 21–22):** Khử chuyển tiếp $\varepsilon$ chuyển $\varepsilon$-NFA sang NFA không có $\varepsilon$ (`eliminate_epsilon` trong `thompson.py`).
> - **Định lý 1 (Slide 18):** Đơn định hóa Tập con chuyển NFA/$\varepsilon$-NFA sang Subset DFA (`subset_construction.py`).
> - **Mục 2.5 (Slide 43–57):** Phương pháp trực tiếp chuyển RE sang Direct DFA qua cây cú pháp gia tố $r\cdot \#$ và bảng `followpos` (`direct_dfa.py`).
> - **Giải thuật 3.6 (Slide 58):** Tối thiểu hóa DFA bằng cả hai thuật toán Moore và Hopcroft (`dfa_minimizer.py`).
> - **Chiều ngược Định lý Kleene (Hopcroft §3.2.1):** Khử trạng thái trên Ô-tô-mát hữu hạn tổng quát **GNFA (`DFA → Regular Expression`)** trong `gnfa.py`, sau đó tự động biên dịch ngược $R_{\text{sinh}}$ để chứng minh $L(R_{\text{gốc}}) \equiv L(R_{\text{sinh}})$!

**Câu 3. Làm thế nào hệ thống vừa quét được chuỗi tiếng Việt UTF-8 (`"Xin chào UEH"`), vừa cho phép khai báo trực tiếp từ khóa/ký hiệu Unicode trong Regex (như `nếu`, `€`, `[^€]`) mà bảng chữ cái $\Sigma$ của DFA vẫn hữu hạn nhỏ gọn và bảo toàn luật bù kép $\sim(\sim A) = A$?**
> **Trả lời:** Đây là kỹ thuật **Phân hoạch Bảng chữ cái Unicode Động $\Sigma(U)$** trong `models.py` và `regex_parser.py`:
> - Thứ nhất, `ASCII_SIGMA` phủ kín toàn bộ **128 mã ASCII `0x00..0x7F`** (kể cả `\0`, `\f`, `\v`, `\x7f`) để không có ký tự ASCII nào lọt ra ngoài khi lấy phần bù.
> - Thứ hai, hệ thống dùng điểm mã noncharacter nội bộ **`NON_ASCII = U+FDD0`** (theo chuẩn Unicode §23.7, được bảo đảm không bao giờ xuất hiện như ký tự văn bản hợp lệ) làm đại diện cho lớp "mọi ký tự Unicode không được nhắc tên tường minh".
> - Thứ ba, khi biên dịch một biểu thức hay bộ đặc tả, parser quét cây AST để trích tập hữu hạn $U$ gồm các ký tự Unicode xuất hiện tường minh (ví dụ $U = \{\text{'ế'}, \text{'€'}\}$) và xây dựng bảng chữ cái động:
>   $$\Sigma(U) = \text{ASCII\_SIGMA} \cup U \cup \{\text{NON\_ASCII}\}$$
> - Khi gặp ký tự đầu vào $c \ge 128$: nếu $c \in U$ thì tra đúng lớp của $c$; nếu $c \notin U$ thì mới ánh xạ về `NON_ASCII`! Nhờ vậy `[^€]` loại trừ đúng `'€'` nhưng vẫn nhận `'ế'`, và phép bù luôn thỏa mãn $\sim(\sim A) = A$!

**Câu 4. Tại sao khi tối thiểu hóa Multi-token DFA cho bộ phân tích từ vựng, ta không được khởi tạo $\Pi_0 = \{Q \setminus F, F\}$ như trong bài toán DFA đơn lẻ?**
> **Trả lời:** Trong DFA nhận diện một ngôn ngữ đơn lẻ $L$, hàm đầu ra ở mỗi trạng thái chỉ là nhị phân ($\text{Accept}$ hoặc $\text{Reject}$), nên mọi trạng thái kết thúc $q \in F$ đều tương đương nhau ở bước 0. Ngược lại, bộ phân tích từ vựng là một **Otomat hữu hạn có nhãn đầu ra kiểu Moore** $\tau: F \to \{T_1, T_2, \dots, T_k\}$: trạng thái kết thúc của `KW_IF` phát ra token `KW_IF`, còn trạng thái kết thúc của `INT_LIT` phát ra token `INT_LIT`. Nếu gộp chung tất cả $F$ vào một khối trong $\Pi_0$, thuật toán tối thiểu hóa sẽ gộp nhầm các trạng thái kết thúc của các loại token khác nhau làm mất khả năng phân loại token! Do đó, phân hoạch ban đầu bắt buộc phải tách riêng từng loại token:
> $$\Pi_0 = \{ Q \setminus F \} \cup \{ F_{T_1}, F_{T_2}, \dots, F_{T_m} \}$$

**Câu 5. Giải thích sự khác biệt giữa thuật toán tối thiểu hóa Moore và thuật toán Hopcroft mà nhóm cài đặt trong `dfa_minimizer.py`?**
> **Trả lời:**
> - **Thuật toán Moore (Partition Refinement — Giải thuật 3.6):** Ở mỗi vòng lặp $k$, duyệt qua toàn bộ các khối trong phân hoạch $\Pi_k$ và tính vector chữ ký chuyển tiếp $(\text{block}(\delta(q, E_1)), \dots, \text{block}(\delta(q, E_p)))$ cho mọi trạng thái $q$ để tách khối cho tới khi $\Pi_{k+1} = \Pi_k$. Độ phức tạp thời gian trường hợp xấu nhất là $O(p \cdot |Q|^2)$. Ưu điểm lớn nhất là xuất được bảng vết $\Pi_0 \to \Pi_1 \to \dots \to \Pi_k$ rất trực quan cho sinh viên theo dõi.
> - **Thuật toán Hopcroft (1971):** Thay vì quét lại toàn bộ các khối ở mỗi vòng, Hopcroft dựng đồ thị chuyển tiếp ngược $\delta^{-1}(A, c)$ và duy trì một hàng đợi phân tách (worklist) $W$. Mỗi bước lấy một cặp $(A, c)$ từ $W$, tìm tập tiền ảnh $X = \delta^{-1}(A, c)$, và chỉ kiểm tra các khối $Y$ có giao với $X$. Nếu $Y$ bị $X$ cắt thành hai phần khác rỗng $Y_1 = Y \cap X$ và $Y_2 = Y \setminus X$: nếu $Y$ đang ở trong $W$ thì thay $Y$ bằng cả $Y_1, Y_2$; ngược lại **chỉ đẩy khối nhỏ hơn** ($\min(|Y_1|, |Y_2|)$) vào $W$. Vì mỗi trạng thái chỉ có thể rơi vào "nửa nhỏ hơn" tối đa $\log_2 |Q|$ lần, tổng độ phức tạp đạt cận tối ưu $O(p \cdot |Q| \log |Q|)$.
> - Hệ thống của nhóm chạy song song cả hai thuật toán và dùng Product Automaton chứng minh `Moore Min-DFA ≡ Hopcroft Min-DFA` (cùng đúng 78 trạng thái trên `MiniLang`, 20 trên `CalcLang`, 52 trên `MiniSQL`).

**Câu 6. Làm thế nào nhóm chứng minh toán học rằng DFA sau khi tối thiểu hóa đã thực sự tối giản tuyệt đối (không thể gộp thêm bất kỳ 2 trạng thái nào nữa)?**
> **Trả lời:** Nhóm cài đặt hàm `verify_dfa_is_minimal(dfa)` trong `verifier.py` dựa trực tiếp trên **Định lý Myhill–Nerode**: hai trạng thái $p \neq q$ là phân biệt được (distinguishable) khi và chỉ khi tồn tại một chuỗi hậu tố phân biệt (witness string) $w \in \Sigma^*$ sao cho $\tau(\hat{\delta}(p, w)) \neq \tau(\hat{\delta}(q, w))$.
> Thuật toán đánh dấu các cặp cơ sở $(p, q)$ có $\tau(p) \neq \tau(q)$ với chuỗi phân biệt $w = \varepsilon$, sau đó lan truyền ngược qua các cung chuyển tiếp để tìm chuỗi phân biệt ngắn nhất $w$ cho mọi cặp còn lại. Kết quả thực nghiệm:
> - Trên `(a|b)*abb` (4 trạng thái `M0..M3`): cả $\binom{4}{2} = 6/6$ cặp đều có chuỗi phân biệt (`(M0,M1): "bb"`, `(M0,M2): "b"`, `(M0,M3): ""`, `(M1,M2): "b"`, `(M1,M3): ""`, `(M2,M3): ""`).
> - Trên `MiniLang` (78 trạng thái): toàn bộ $\binom{78}{2} = 3.003 / 3.003$ cặp trạng thái đều có chuỗi phân biệt (100%).
> - Trên `CalcLang` (20 trạng thái): toàn bộ $\binom{20}{2} = 190 / 190$ cặp (100%).
> - Trên `MiniSQL` (52 trạng thái): toàn bộ $\binom{52}{2} = 1.326 / 1.326$ cặp (100%).

**Câu 7. Tại sao cần thêm trạng thái chết ảo `DEAD = -1` trước khi chạy tối thiểu hóa Moore/Hopcroft rồi lại xóa `DEAD` ở bước cuối?**
> **Trả lời:** Vì DFA sinh ra từ Subset Construction hoặc Direct DFA thường có hàm chuyển tiếp không đầy đủ (sparse transitions — những cung đi vào tập rỗng $\varnothing$ bị lược bỏ). Nếu không thêm trạng thái `DEAD = -1`, một trạng thái $p$ không có cung trên ký tự $a$ (tức đi vào $\varnothing \notin F$) và trạng thái $q$ có cung trên ký tự $a$ đi tới một trạng thái không kết thúc $r \notin F$ nhưng $r$ lại đi tiếp được tới trạng thái kết thúc qua ký tự $b$ sẽ bị xử lý sai khi tính tiền ảnh ngược $\delta^{-1}$ trong Hopcroft. Việc bổ sung `DEAD` làm hàm chuyển thành **hàm toàn phần (total function)** giúp thuật toán phân hoạch chính xác tuyệt đối, sau đó Bước 5 loại bỏ khối chứa `DEAD` để đồ thị DFA gọn sạch.

**Câu 8. Giải thích cách nhóm mở rộng phương pháp Trực tiếp (`Direct RE → DFA`) từ một biểu thức đơn lẻ sang bài toán Đa-Token (`build_combined_direct_dfa`)?**
> **Trả lời:** Trong bài giảng Chương 3.1 Mục 2.5, một biểu thức đơn $R$ được nối với một dấu kết thúc duy nhất: $R \cdot \#$. Để mở rộng cho $k$ quy tắc token $\{(T_1, R_1, p_1), \dots, (T_k, R_k, p_k)\}$, nhóm xây dựng một cây cú pháp kết hợp duy nhất:
> $$R_{\text{comb}} = (R_1 \cdot \#_1) \mid (R_2 \cdot \#_2) \mid \dots \mid (R_k \cdot \#_k)$$
> Trong đó mỗi nút lá đặc biệt $\#_r$ được cấp một mã vị trí lá riêng $i_r$ và lưu thông tin `AcceptInfo(T_r, p_r, skip_r)`. Các hàm `nullable`, `firstpos`, `lastpos` và `followpos` vẫn tính theo đúng công thức chuẩn. Khi dựng các trạng thái DFA từ tập vị trí $S \subseteq \{1, \dots, n\}$:
> - Chỉ các vị trí lá $i \in S$ mang ký hiệu thật $c \in \Sigma$ mới sinh cung chuyển tiếp $\delta(S, c) = \bigcup_{i \in S, \text{sym}(i)=c} \text{followpos}(i)$.
> - Nếu $S$ chứa một hoặc nhiều vị trí kết thúc $\#_r$, trạng thái $S$ trở thành trạng thái kết thúc và nhận nhãn của token có độ ưu tiên cao nhất: $\tau(S) = \arg\min_{\#_r \in S} p_r$.

---

### Nhóm B — Thuật toán Cài đặt, Trường hợp Biên & Độ phức tạp

**Câu 9. Định lượng đếm `{m}`, `{m,}`, `{m,n}` được nhóm xử lý như thế nào mà không cần thay đổi cấu trúc Thompson hay `followpos`?**
> **Trả lời:** Nhóm áp dụng phép khai triển đại số ngay tại tầng cây cú pháp trừu tượng (AST) trong `regex_parser.py` (hàm `_apply_counted_quantifier`):
> - $R\{m\} \equiv \underbrace{R \cdot R \cdots R}_{m \text{ lần}}$ (nếu $m = 0$ thì trả về `EpsilonNode()`).
> - $R\{m,\} \equiv \underbrace{R \cdot R \cdots R}_{m \text{ lần}} \cdot R^*$.
> - $R\{m,n\} \equiv \underbrace{R \cdot R \cdots R}_{m \text{ lần}} \cdot \underbrace{(R?) \cdot (R?) \cdots (R?)}_{n-m \text{ lần}}$.
> Mỗi bản sao của cây con $R$ được nhân bản sâu (`_clone_ast`) để các nút lá trong Direct DFA có chỉ số vị trí độc lập. Đồng thời parser kiểm tra chặt điều kiện $0 \le m \le n \le 64$ (`MAX_QUANTIFIER_BOUND = 64`), nếu $m > n$ (như `a{5,2}`) hoặc vượt ngưỡng (`a{100}`) sẽ ném `RegexSyntaxError` rõ ràng.

**Câu 10. Làm thế nào bộ phân tích cú pháp RE xử lý các trường hợp biên hiểm hóc của lớp ký tự như `[-a]`, `[a-]`, `[-]`, `[^-]`, `[^^]`, `[\[\]\\]`?**
> **Trả lời:** Trong hàm `_parse_char_class()` của `regex_parser.py`:
> - Ngay sau dấu `[` (và sau dấu phủ định `^` nếu có), dấu `-` đứng ở **đầu lớp ký tự** (như `[-a]`, `[-]`, `[^-]`) hoặc đứng ở **cuối lớp ký tự** ngay trước `]` (như `[a-]`) không có đủ 2 đầu mút nên được nhận diện là **ký tự gạch ngang literal `'-'`** chứ không phải toán tử khoảng!
> - Khi dấu `-` nằm giữa hai ký tự $c_1 - c_2$: chương trình kiểm tra $\text{ord}(c_1) \le \text{ord}(c_2)$; nếu $\text{ord}(c_1) > \text{ord}(c_2)$ (như `[z-a]`) lập tức báo `RegexSyntaxError("Khoảng ký tự ngược")`.
> - Với `[^^]`, dấu `^` thứ nhất bật cờ phủ định `negated = True`, còn dấu `^` thứ hai nằm ở vị trí phần tử nên là ký tự literal `'^'`, kết quả là tập $\Sigma \setminus \{\text{'\^'}\}$.
> - Với lớp rỗng `[]`, `[^]` hoặc lớp phủ định loại trừ toàn bộ ASCII, hệ thống đều bắt lỗi `RegexSyntaxError`.

**Câu 11. Quy tắc bị che khuất (Shadowed / Dead Token Rule) là gì? Hệ thống phát hiện tự động bằng thuật toán nào?**
> **Trả lời:** Một quy tắc token $(T_i, R_i, p_i)$ bị gọi là **che khuất hoàn toàn (shadowed)** nếu mọi chuỗi $w \in L(R_i)$ cũng đồng thời thuộc hợp các ngôn ngữ của các quy tắc có độ ưu tiên cao hơn đứng trước nó:
> $$L(R_i) \subseteq \bigcup_{j < i} L(R_j)$$
> Ví dụ điển hình: nếu người dùng đặt `IDENTIFIER` (`[a-zA-Z_][a-zA-Z0-9_]*`, ưu tiên 1) lên trước `KW_IF` (`if`, ưu tiên 2), thì tại trạng thái DFA nhận chuỗi `"if"`, hàm giải quyết xung đột $\arg\min \text{priority}$ luôn chọn `IDENTIFIER`.
> Nhờ tính chất đầy đủ của Minimized DFA $D_{\min}$, điều kiện $L(R_i) \subseteq \bigcup_{j < i} L(R_j)$ tương đương chính xác với việc **không tồn tại bất kỳ trạng thái kết thúc có thể đạt tới nào $q \in F_{\min}$ mang nhãn chiến thắng $\tau_{\min}(q) = T_i$**! Hệ thống kiểm tra điều kiện này ngay trong `LexicalAnalyzer.compile()`, tìm luôn quy tắc đứng trước đã đè lên $T_i$ (tại các trạng thái xung đột `all_matched_tokens`) và phát cảnh báo chi tiết trên cả CLI lẫn Web UI Tab 2 & Tab 4!

**Câu 12. Tại sao bộ quét Maximal Munch thông thường có thể bị tấn công suy biến thành thời gian bậc hai $O(n^2)$, và kỹ thuật `failed_states` (Reps, 1998) trong `scanner.py` giải quyết triệt để vấn đề này như thế nào?**
> **Trả lời:**
> - **Nguyên nhân gây $O(n^2)$ ở bộ quét thông thường:** Xét quy tắc chuỗi hoặc bình luận nhiều dòng, hoặc mẫu bệnh lý như đầu vào gồm 1 dấu `"` theo sau là 5.000 cặp `\"` nhưng thiếu dấu `"` đóng ở cuối (`"` + `\"` * 5000, dài 10.001 ký tự). Tại vị trí 0, DFA đọc từ đầu đến tận ký tự 10.001 mới phát hiện không có dấu `"` đóng, nên quay lui về điểm chấp nhận gần nhất (hoặc báo lỗi tại vị trí 0 rồi tiến lên vị trí 1, 2...). Ở mỗi lần thử sau, bộ quét thông thường lại đọc đi đọc lại cùng một hậu tố dài đến cuối chuỗi nhưng cuối cùng vẫn thất bại, dẫn tới $\sum_{i=1}^n (n - i) = \Theta(n^2)$ bước chuyển trạng thái!
> - **Giải pháp Memoization của Reps (1998) trong `scanner.py`:** Nhóm duy trì tập `failed_states: Set[Tuple[str, int]]`. Trong một lượt dò Maximal Munch từ vị trí `pos`, giả sử DFA đi qua dãy cấu hình $(q_1, i_1), (q_2, i_2), \dots, (q_m, i_m)$ và vị trí kết thúc hợp lệ cuối cùng là `last_accept_pos`. Khi đó, mọi cấu hình $(q_r, i_r)$ nằm **sau** `last_accept_pos` ($i_r > \text{last\_accept\_pos}$) đều đã được chứng minh chắc chắn rằng: *"Nếu xuất phát từ trạng thái $q_r$ tại chỉ số văn bản $i_r$, DFA không bao giờ đi tới được bất kỳ trạng thái kết thúc nào trước khi gặp DEAD/EOF"*.
> - Do tính chất đơn định của DFA, kết quả từ $(q_r, i_r)$ chỉ phụ thuộc vào $q_r$ và hậu tố `source[i_r:]`, hoàn toàn không phụ thuộc vào đường đi trước đó! Vì vậy ta đưa tất cả $(q_r, i_r)$ với $i_r > \text{last\_accept\_pos}$ vào `failed_states`. Ở các lượt quét tiếp theo, hễ gặp `(curr_state, scan_pos) in failed_states`, bộ quét cắt nhánh `break` ngay trong $O(1)$!
> - **Độ phức tạp chặt:** Vì chỉ có $|Q|$ trạng thái và $n$ vị trí văn bản, mỗi cặp $(q, i)$ bị đánh dấu thất bại tối đa 1 lần $\implies$ tổng số bước chuyển thất bại trên toàn bộ quá trình quét toàn file không vượt quá $|Q| \cdot n = O(n)$! Thực nghiệm trên chuỗi 10.001 ký tự `"` + `\"`*5000: hệ thống cắt nhánh đúng 5.000 lần (`memoized_cutoffs = 5000`) và quét xong trong **~24 ms**!

**Câu 13. So sánh hai chế độ phục hồi lỗi `panic_char` và `smart_sync` mà nhóm cài đặt trong `scanner.py`?**
> **Trả lời:**
> - **`panic_char` (Panic-mode cổ điển theo từng ký tự):** Khi không khớp được token nào tại `pos`, bộ quét ghi nhận lỗi cho ký tự `source[pos]` và dịch con trỏ `pos += 1`. Chế độ này rất chuẩn xác khi gặp các ký tự lạ rời rạc (như `let a = 5$ + @b;` $\to$ bắt đúng lỗi `$`, `@` và giữ nguyên `5`, `+`, `b`). Tuy nhiên, nếu gặp **chuỗi chưa đóng** như `"Chuỗi quên đóng\nlet x = 1;`, việc chỉ bỏ qua dấu `"` ở đầu khiến phần văn bản bên trong `Chuỗi quên đóng` bị quét tiếp thành các `IDENTIFIER` và lỗi lẻ tẻ.
> - **`smart_sync` (Phục hồi đồng bộ theo ngữ cảnh chuỗi / bình luận):** Khi thất bại tại dấu mở chuỗi `"` hoặc dấu mở bình luận nhiều dòng `/*`, bộ quét nhận diện đây là cấu trúc chuỗi/bình luận chưa đóng (`_is_unclosed_block_comment` / unclosed string) nên tự động gom toàn bộ chuỗi chưa đóng cho tới dấu xuống dòng `\n` (hoặc gom toàn bộ bình luận `/*...` chưa đóng tới `EOF`) thành **đúng 1 `LexicalError` duy nhất**, giúp dòng lệnh `let x = 1;` phía sau được quét sạch sẽ 100% không có bất kỳ token rác nào!
> - Hệ thống cho phép người dùng bật/tắt cả 2 chế độ ngay trên giao diện Web Tab 1 để đối sánh trực quan.

**Câu 14. Giải thích biểu thức chính quy nhận diện bình luận nhiều dòng `/* ... */` trong `MiniLang`: tại sao không viết đơn giản là `/\*.*\*/` mà phải viết `/\*([^*]|\*+[^*/])*\*+/`?**
> **Trả lời:** Nếu viết `/\*.*\*/`, vì bộ quét áp dụng nguyên lý **Maximal Munch (khớp dài nhất)** và dấu `.` khớp cả dấu `*` lẫn `/`, nên khi gặp đoạn mã có hai bình luận trên cùng một dòng như:
> `/* comment 1 */ let x = 10; /* comment 2 */`
> biểu thức `/\*.*\*/` sẽ nuốt trọn từ `/*` đầu tiên đến tận `*/` cuối cùng, ăn mất luôn câu lệnh `let x = 10;` ở giữa!
> Ngược lại, biểu thức chính tắc chuẩn C/Flex:
> `/\*([^*]|\*+[^*/])*\*+/`
> quy định chặt chẽ phần ruột bên trong: sau `/*`, hoặc là ký tự không phải `*` (`[^*]`), hoặc là một chuỗi một hay nhiều dấu `*` nhưng ký tự ngay sau chuỗi `*` đó **không được là `*` và không được là `/`** (`\*+[^*/]`), và kết thúc bằng một hoặc nhiều dấu `*` liền trước dấu `/` (`\*+/`). Nhờ vậy DFA dừng chính xác ngay tại cặp `*/` đóng đầu tiên và xử lý đúng mọi trường hợp hiểm như `/**/`, `/*** a * b ***/`, `/* a */ let x = 1; /* b */`!

**Câu 15. Tại sao bình luận nhiều dòng không lồng nhau `/* ... */` thì nhận diện được bằng DFA, nhưng bình luận nhiều dòng LỒNG NHAU `/* ... /* ... */ ... */` lại không thể nhận diện bằng bất kỳ DFA nào? Hãy chứng minh bằng Bổ đề Bơm (Pumping Lemma Chương 3.2)!**
> **Trả lời:**
> - Giả sử phản chứng rằng ngôn ngữ $L_{\text{nested}}$ gồm các bình luận lồng nhau cân bằng `/* ... /* ... */ ... */` là ngôn ngữ chính quy.
> - Vì lớp ngôn ngữ chính quy đóng với phép đồng cấu nghịch đảo (hoặc xét tập con giao với $(/\*)^* (\*/)^*$), nếu đặt $a = \text{"/*"}$ và $b = \text{"*/"}$, thì ngôn ngữ $L = \{ a^n b^n \mid n \ge 1 \}$ cũng phải là ngôn ngữ chính quy.
> - Áp dụng **Bổ đề Bơm (Pumping Lemma — Chương 3.2)** cho $L$: Gọi $p \ge 1$ là hằng số bơm (tương ứng số trạng thái $|Q|$ của DFA). Chọn chuỗi $w = a^p b^p \in L$ có $|w| = 2p \ge p$.
> - Theo Bổ đề Bơm, mọi cách phân tách $w = xyz$ thỏa mãn $|xy| \le p$ và $|y| \ge 1$ đều buộc chuỗi con $y$ chỉ nằm trong đoạn $a^p$ đầu tiên, tức $y = a^k$ với $1 \le k \le p$.
> - Khi bơm lên với $i = 2$ (hoặc $i = 0$), ta thu được chuỗi $xy^2z = a^{p+k} b^p$. Vì $k \ge 1$ nên số dấu mở $p + k \neq p$ (số dấu đóng), suy ra $xy^2z \notin L$ — **mâu thuẫn với Bổ đề Bơm**!
> - Vậy ngôn ngữ bình luận lồng nhau sâu tùy ý không phải là ngôn ngữ chính quy mà thuộc lớp **Ngôn ngữ phi ngữ cảnh (CFL — Chương 4)** và cần Otomat đẩy xuống (PDA) hoặc bộ đếm độ sâu lồng nhau.

---

### Nhóm C — Kiểm chứng Bất biến, JFLAP Round-Trip & Chi tiết Thực nghiệm

**Câu 16. Năm bất biến toán học (Mathematical Invariants) mà nhóm kiểm chứng tự động trong `tests/test_suite.py` là gì?**
> **Trả lời:**
> 1. **Invariant 1 (Zero-Loss Source Reconstruction):** Với mọi chuỗi đầu vào $S$ bất kỳ (kể cả chứa lỗi liên tiếp, tiếng Việt UTF-8, CRLF), nếu lấy tất cả các token giữ lại + các token bị skip (khoảng trắng, comment) + các mảnh lỗi `LexicalError` sắp xếp theo `start_pos`, chúng tạo thành một phân hoạch rời nhau phủ kín $[0, |S|)$ và ghép lại bằng đúng $S$ 100% không mất và không trùng dù chỉ 1 byte!
> 2. **Invariant 2 (6-Way Automaton Equivalence):** Với mọi biểu thức chính quy hợp lệ, cả 6 mô hình (`Thompson ε-NFA`, `NFA Khử ε`, `Subset DFA`, `Moore Min-DFA`, `Hopcroft Min-DFA`, `Direct DFA`) đều chấp nhận/từ chối cùng một tập ngôn ngữ trên hàng trăm chuỗi Fuzz và trên Product Automaton BFS (0 phản ví dụ).
> 3. **Invariant 3 (Myhill–Nerode Absolute Minimality):** Với mọi DFA tối giản sinh ra, 100% các cặp trạng thái phân biệt $(p, q)$ đều tồn tại chuỗi phân biệt ngắn nhất $w$.
> 4. **Invariant 4 (Reps 1998 Linear-Time Bound):** Mọi đầu vào bệnh lý dài 10.000 ký tự (`"aaaa...`, `/*xxxx...`, `"\"\"...`) đều quét hoàn tất dưới 200 ms (thực tế chỉ 3–24 ms).
> 5. **Invariant 5 (AST Zero-`import re` Guard):** Duyệt cây cú pháp Python (`ast.parse`) của toàn bộ các file trong `lexer_engine/`, `app.py`, `cli.py` xác nhận tuyệt đối không có bất kỳ lệnh `import re` hay `from re import ...` nào.

**Câu 17. Kiểm chứng Khứ hồi JFLAP (Round-Trip Verification) trong `jflap_export.py` hoạt động như thế nào?**
> **Trả lời:** Không chỉ xuất một chiều từ NFA/DFA sang file XML `.jff` chuẩn JFLAP 7.x (`export_nfa_to_jflap`, `export_dfa_to_jflap`), nhóm còn viết bộ đọc ngược (`import_jflap_to_nfa`, `import_jflap_to_dfa`) bằng `xml.etree.ElementTree` để tái tạo lại đối tượng `NFA` / `DFA` từ chính chuỗi XML `.jff` vừa xuất ra, sau đó dùng Product Automaton (`check_dfa_equivalence`) chứng minh DFA đọc ngược từ `.jff` tương đương 100% với DFA gốc trên tất cả các ngôn ngữ `MiniLang`, `CalcLang`, `MiniSQL`!

**Câu 18. Giải thích từng con số trên ví dụ `(a|b)*abb` (Slide 38 Chương 3.1): tại sao Thompson có 11 trạng thái, Khử $\varepsilon$ còn 6 trạng thái, Subset DFA có 5 trạng thái, và Min-DFA có 4 trạng thái?**
> **Trả lời:**
> - **Thompson $\varepsilon$-NFA (11 trạng thái `q0..q10`):** Nhánh `a` là `q2 -> q3` (2 TT); nhánh `b` là `q4 -> q5` (2 TT); phép hợp `a|b` thêm đầu `q1` và cuối `q6` (2 TT $\to$ tổng 6 TT); bao đóng Kleene `(a|b)*` thêm đầu `q0` và cuối `q7` (2 TT $\to$ tổng 8 TT); nối tiếp `.a`, `.b`, `.b` gộp đỉnh đầu nên chỉ thêm 3 trạng thái `q8`, `q9`, `q10` $\to$ tổng đúng $8 + 3 = 11$ trạng thái!
> - **NFA Khử $\varepsilon$ theo Định lý 2 (6 trạng thái):** Sau khi tính $\varepsilon$-closure và dựng cung trực tiếp $\delta'(p, c)$, chỉ còn 6 trạng thái có cung đi tới (trạng thái đầu `q0` cùng các trạng thái sau khi đọc `a` hoặc `b`).
> - **Subset DFA (5 trạng thái `D0..D4`):** `D0 = {0,1,2,4,7}`, `D1 = {1,2,3,4,6,7,8}` (đọc `a`), `D2 = {1,2,4,5,6,7}` (đọc `b`), `D3 = {1,2,4,5,6,7,9}` (đọc `ab`), `D4 = {1,2,4,5,6,7,10}` (đọc `abb` — kết thúc).
> - **Moore & Hopcroft Min-DFA (4 trạng thái `M0..M3`):** Hai trạng thái `D0` và `D2` đều không kết thúc và đều chuyển tới `D1` qua `a`, chuyển tới `D2` qua `b`, nên chúng tương đương Myhill–Nerode (`D0 ≡ D2`) và được gộp thành `M0`, giảm từ 5 xuống 4 trạng thái tối giản!

**Câu 19. Giải thích từng con số trên ví dụ `(a|ba)(a|b)*ba` (Slide 48–56 Chương 3.1): tại sao có 8 lá và bảng `followpos` tính ra sao?**
> **Trả lời:** Gia tố hóa thành `(a|ba)(a|b)*ba#`, đánh số 8 nút lá từ trái sang phải:
> - Tiền tố `(a|ba)`: lá `1:a`, lá `2:b`, lá `3:a`. Vì `lastpos(a|ba) = {1, 3}` nối với `(a|b)*ba#` có `firstpos = {4, 5, 6}`, nên `followpos(1) = followpos(3) = {4, 5, 6}`, còn `2:b` nối với `3:a` nên `followpos(2) = {3}`.
> - Vòng lặp `(a|b)*`: lá `4:a`, lá `5:b`. Do nút sao `*` nối `lastpos = {4, 5}` quay lại `firstpos = {4, 5}` và nối tiếp sang `6:b`, nên `followpos(4) = followpos(5) = {4, 5, 6}`.
> - Hậu tố `ba#`: lá `6:b` nối với `7:a` $\implies$ `followpos(6) = {7}`; lá `7:a` nối với `8:#` $\implies$ `followpos(7) = {8}`; và `followpos(8) = ∅`.
> - Từ `firstpos(root) = {1, 2}` (trạng thái `A`), dựng trực tiếp ra đúng 5 trạng thái: `A={1,2}`, `B={3}` (hoặc `{4,5,6}` tùy thứ tự duyệt `a`/`b`), `{3}`, `{4,5,6,7}`, `{4,5,6,8}` (chứa `#8` là trạng thái kết thúc).

**Câu 20. Tại sao trên `MiniLang` (39 token), `Combined Direct DFA` sinh ra 79 trạng thái trong khi `Minimized DFA` có 78 trạng thái (chênh nhau 1 trạng thái), còn trên `CalcLang` (20) và `MiniSQL` (52) thì `Combined Direct DFA` bằng đúng `Minimized DFA`?**
> **Trả lời:** Phương pháp Direct RE → DFA (`followpos`) luôn tạo ra một DFA nhỏ gọn hơn rất nhiều so với Subset Construction (79 trạng thái so với 86 trạng thái của Subset DFA trên `MiniLang`), nhưng về mặt lý thuyết (Berry & Sethi, 1986; Dragon Book Mục 3.9.5), Direct DFA **không phải lúc nào cũng tối giản tuyệt đối**, bởi hai tập vị trí lá khác nhau $S_1 \neq S_2$ trong cây cú pháp vẫn có thể có cùng hành vi chuyển tiếp tương lai (trong `MiniLang`, biểu thức `BLOCK_COMMENT` `/\*([^*]|\*+[^*/])*\*+/` có hai tập vị trí lá sau khi đọc dấu `*` mang hành vi tương đương nhau). Khi đưa `Combined Direct DFA` (79 trạng thái) qua thuật toán Moore hoặc Hopcroft, cặp trạng thái tương đương đó được gộp lại thành đúng **78 trạng thái** bằng y hệt nhánh Thompson+Subset!

**Câu 21. Nếu một biểu thức chính quy có thể khớp chuỗi rỗng $\varepsilon$ (nullable, ví dụ `a*` hoặc `(a|ε)*`), bộ quét xử lý thế nào để không bao giờ bị treo trong vòng lặp vô hạn?**
> **Trả lời:** Hệ thống có 2 chốt chặn an toàn:
> 1. Lúc biên dịch (`LexicalAnalyzer.compile`), hàm `ast.is_nullable()` phát hiện mọi quy tắc có $\varepsilon \in L(R_i)$ và ghi vào danh sách `warnings`.
> 2. Lúc quét (`scanner.py`), điều kiện phát token bắt buộc `last_accept_pos > pos` (tức độ dài lexeme phải $\ge 1$). Nếu tại vị trí `pos`, DFA chỉ chấp nhận chuỗi rỗng độ dài 0 và không tiến thêm được ký tự nào, bộ quét coi đó là không khớp được token tiến triển và chuyển sang bước phục hồi lỗi (dịch `pos += 1`), đảm bảo con trỏ `pos` **luôn tăng nghiêm ngặt** sau mỗi bước lặp!

**Câu 22. Bộ quét xử lý các chuẩn xuống dòng khác nhau (`\n` của Linux/macOS, `\r\n` của Windows CRLF, `\r` của Mac cổ) như thế nào để tọa độ `(line, col)` luôn chính xác?**
> **Trả lời:** Trong hàm `_advance_position(text, start, end, line, col)` của `scanner.py`:
> - Khi gặp `\n`: nếu ký tự ngay trước đó là `\r` (tức cặp `\r\n` của Windows CRLF mà `\r` vừa được xử lý ở bước trước), hàm chỉ đặt lại `col = 1` chứ **không cộng dòng lần thứ hai**; ngược lại (Unix `\n`) thì tăng `line += 1, col = 1`.
> - Khi gặp `\r`: tăng `line += 1, col = 1`.
> - Nhờ vậy cả `\n`, `\r\n` và `\r` (kể cả nằm bên trong bình luận nhiều dòng `/* dòng 1\r\ndòng 2 */`) đều tính tọa độ `(line, col)` của các token phía sau chính xác tuyệt đối (được kiểm chứng tự động trong `test_mixed_newlines_crlf_line_col_tracking`).

**Câu 23. Trong `MiniLang`, chuỗi `"1.5e"` và `"1.5e+2"` và `"1.5e+"` được quét khác nhau như thế nào?**
> **Trả lời:** Quy tắc `FLOAT_LIT` có RE là `[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?`:
> - Với `"1.5e+2"`: DFA đọc hết 6 ký tự vào trạng thái kết thúc của `FLOAT_LIT` $\to$ xuất 1 token `FLOAT_LIT("1.5e+2")`.
> - Với `"1.5e"`: DFA đọc `1.5` (vào trạng thái kết thúc `FLOAT_LIT`, lưu `last_accept_pos = 3`), đọc tiếp `e` (vào trạng thái trung gian chờ chữ số mũ), rồi gặp EOF/khoảng trắng (DEAD). Bộ quét **quay lui 1 ký tự** về vị trí 3 để xuất `FLOAT_LIT("1.5")`, sau đó quét tiếp `e` thành `IDENTIFIER("e")`.
> - Với `"1.5e+"`: DFA đọc `1.5` (lưu `last_accept_pos = 3`), đọc tiếp `e` và `+` (trạng thái trung gian chờ chữ số mũ), gặp EOF/khoảng trắng (DEAD) $\to$ **quay lui 2 ký tự** về vị trí 3 để xuất `FLOAT_LIT("1.5")`, sau đó quét tiếp `e` thành `IDENTIFIER("e")` và `+` thành `OP_PLUS("+")`!

**Câu 24. Với chuỗi `"123abc"`, nhiều bạn nghĩ bộ phân tích từ vựng phải báo lỗi "tên biến bắt đầu bằng số". Tại sao bộ quét DFA chuẩn lại tách thành `INT_LIT("123")` và `IDENTIFIER("abc")`?**
> **Trả lời:** Trong kiến trúc trình biên dịch chuẩn (C, Java, Python, Dragon Book Chương 3), ở tầng **Phân tích từ vựng (Lexical Analysis)**, quy tắc Maximal Munch đọc từ đầu chuỗi `"123abc"`: tiền tố dài nhất khớp một quy tắc hợp lệ là `"123"` (`INT_LIT`), tiếp theo là `"abc"` (`IDENTIFIER`). Việc hai token `INT_LIT` và `IDENTIFIER` đứng cạnh nhau không có toán tử ở giữa là một **Lỗi cú pháp (Syntax Error)** sẽ bị bắt ngay lập tức ở pha kế tiếp là **Bộ phân tích cú pháp (Parser - Chương 4)**! (Nếu muốn bắt ngay ở tầng từ vựng, người thiết kế ngôn ngữ có thể thêm một quy tắc bẫy lỗi `INVALID_ID = [0-9]+[a-zA-Z_]+` ngay trên `INT_LIT` trong Tab 4 Live Editor).

**Câu 25. Với chuỗi `"0.0.0"`, bộ quét DFA của nhóm tách thành những token nào?**
> **Trả lời:** Khi quét `"0.0.0"`:
> 1. Từ đầu chuỗi, DFA khớp tiền tố dài nhất `"0.0"` thành `FLOAT_LIT("0.0")`.
> 2. Phần còn lại là `".0"`: trong `MiniLang`, dấu `.` đứng một mình không bắt đầu bất kỳ token hợp lệ nào, nên tại dấu `.` thứ hai, bộ quét báo `LEXICAL_ERROR(".")`, tiến 1 ký tự và quét nốt `"0"` thành `INT_LIT("0")`!

**Câu 26. Tại sao trong `Thompson's Construction` của nhóm (`thompson.py`), phép nối kết `ConcatNode(left, right)` lại gộp trực tiếp đỉnh kết thúc của `left` với đỉnh bắt đầu của `right` thay vì thêm một cung $\varepsilon$ nối giữa chúng?**
> **Trả lời:** Trong bài báo gốc của Thompson (1968) và giáo trình Dragon Book (Hình 3.41 trang 160), mọi mảnh $\varepsilon$-NFA con $N(s)$ được xây dựng quy nạp luôn thỏa mãn 2 bất biến cấu trúc:
> 1. Trạng thái khởi đầu không có bất kỳ cung nào đi vào ($\text{in-degree}(q_{\text{start}}) = 0$).
> 2. Trạng thái kết thúc không có bất kỳ cung nào đi ra ($\text{out-degree}(q_{\text{accept}}) = 0$).
> Nhờ hai bất biến này, khi nối $N(r)$ với $N(s)$, việc đồng nhất (gộp) đỉnh kết thúc của $N(r)$ với đỉnh khởi đầu của $N(s)$ không bao giờ tạo ra chu trình ngược hay đường đi tắt sai lệch, đồng thời tiết kiệm được 1 trạng thái và 1 cung $\varepsilon$ cho mỗi phép nối. Quan trọng hơn cả, chính cách gộp đỉnh này trong phép nối giúp biểu thức `(a|b)*abb` sinh ra **đúng 11 trạng thái (`q0..q10`)** khớp 100% với Slide 38 Chương 3.1 của cô!

**Câu 27. Làm sao thuật toán `compare_regex_equivalence(R1, R2)` trên Tab 3 biết được hai biểu thức chính quy bất kỳ có tương đương nhau hay không ($L(R_1) = L(R_2)$)?**
> **Trả lời:** Bài toán kiểm tra tương đương hai biểu thức chính quy $L(R_1) \stackrel{?}{=} L(R_2)$ là bài toán quyết định được (decidable) đối với ngôn ngữ chính quy:
> 1. Biên dịch $R_1 \to \text{Min-DFA } D_1$ và $R_2 \to \text{Min-DFA } D_2$.
> 2. Chạy BFS trên **Otomat tích (Product Automaton)** $D_1 \times D_2$ xuất phát từ cặp trạng thái đầu $(q_{0,1}, q_{0,2})$ trên bảng chữ cái phân hoạch chung.
> 3. Nếu gặp bất kỳ cặp trạng thái $(q_1, q_2)$ nào mà một bên thuộc $F$ còn bên kia không thuộc $F$ (tức $(q_1 \in F_1) \neq (q_2 \in F_2)$), thuật toán dừng ngay và truy vết ngược cây BFS để trả về **chuỗi phản ví dụ ngắn nhất** $w \in L(R_1) \triangle L(R_2)$!
> 4. Nếu BFS duyệt hết mọi cặp trạng thái đạt tới được mà không có mâu thuẫn, thuật toán kết luận $L(R_1) = L(R_2)$ trên toàn bộ $\Sigma^*$.

**Câu 28. Tại sao số trạng thái Subset DFA thực tế của `MiniLang` (86 trạng thái), `CalcLang` (24 trạng thái), `MiniSQL` (64 trạng thái) lại NHỎ HƠN cả số trạng thái của Thompson $\varepsilon$-NFA (170, 57, 128), trong khi lý thuyết nói Subset Construction có thể bùng nổ lên $2^{|Q_N|}$ trạng thái?**
> **Trả lời:** Cận trên $2^{|Q_N|}$ chỉ xảy ra với các biểu thức chính quy bệnh lý có tính nhập nhằng vị trí sâu như $(a \mid b)^* a (a \mid b)^{k-1}$ (cần nhớ đủ $k$ bit lịch sử gần nhất nên DFA cần $2^k$ trạng thái). Ngược lại, các quy tắc từ vựng của ngôn ngữ lập trình thực tế có cấu trúc dạng **cây tiền tố (trie-like)** và phân tách rõ theo các lớp ký tự rời nhau (chữ cái, chữ số, toán tử, dấu ngoặc kép). Khi chạy $\varepsilon$-closure và `Move`, phần lớn các trạng thái $\varepsilon$ trung gian của Thompson được gom chung vào một vài tập con hoạt động, khiến số tập con đạt tới được từ $D_0$ chỉ tăng tuyến tính và thậm chí nhỏ hơn số đỉnh $\varepsilon$-NFA ban đầu!

**Câu 29. Nếu cô nhập một biểu thức bệnh lý như `(a|b)*a(a|b){15}` (bùng nổ trạng thái $2^{16}$) hoặc bom nhân bản AST lồng nhau `(((a{64}){64}){64})` vào hệ thống, hệ thống xử lý ra sao?**
> **Trả lời:** Nhóm đã thiết kế **ba tầng bảo vệ chống từ chối dịch vụ (DoS)**:
> 1. Ở tầng định lượng đơn lẻ (`regex_parser.py`): giới hạn `MAX_QUANTIFIER_BOUND = 64` cho `{m,n}`.
> 2. Ở tầng cây cú pháp toàn cục (`regex_parser.py`): giới hạn **`MAX_AST_NODES = 4096`**! Trước khi nhân bản cây con cho `{m,n}`, parser ước lượng kích thước cây kết quả trong $O(1)$ (`m * sub_size + (n - m) * (sub_size + 1) + ...`). Do đó bom lồng nhau `(((a{64}){64}){64})` (vốn sẽ sinh tới `528.483` nút AST nếu nhân bản ngây thơ) bị chặn đứng ngay lập tức trong `< 0.1 ms` mà không cấp phát bộ nhớ!
> 3. Ở tầng đơn định hóa (`subset_construction.py`): tham số bảo vệ `max_states = 5000` chủ động ngắt an toàn nếu số tập con DFA vượt quá 5.000 trạng thái.

**Câu 30. Làm thế nào nhóm kiểm chứng được rằng trong toàn bộ lõi `lexer_engine/`, `app.py`, `cli.py` và cả file Lexer độc lập sinh ra hoàn toàn không có bất kỳ chỗ nào lén dùng `import re`?**
> **Trả lời:** Trong `tests/test_suite.py`, phương thức `test_zero_re_in_engine()` và `test_v2_5_standalone_table_driven_lexer_generator_differential()` sử dụng trực tiếp module `ast` của Python để phân tích cây cú pháp (`ast.parse`) của tất cả 11 file `.py` trong `lexer_engine/`, `app.py`, `cli.py` cũng như mã nguồn `.py` do `codegen.py` sinh ra, kiểm tra mọi nút `ast.Import`, `ast.ImportFrom`, `importlib.import_module("re")` và `__import__("re")` để khẳng định 100% Zero `re`!

**Câu 31. Tại sao trong `MiniSQL`, tỷ lệ giảm trạng thái khi tối thiểu hóa DFA đạt tới `-18.75%` (từ 64 xuống 52 trạng thái), cao hơn hẳn `MiniLang` (`-9.3%`, từ 86 xuống 78 trạng thái)?**
> **Trả lời:**
> - Trong `MiniSQL`, mỗi từ khóa được viết ở dạng hỗ trợ cả chữ HOA và chữ thường như `SELECT|select`, `FROM|from`, `WHERE|where`, `INSERT|insert`... Khi chạy Subset Construction, hai nhánh chữ HOA (`S-E-L-E-C-T`) và chữ thường (`s-e-l-e-c-t`) đi qua các tập trạng thái NFA khác nhau nên sinh ra các trạng thái Subset DFA riêng biệt. Tuy nhiên, khi đi vào các vị trí hậu tố cuối hoặc rẽ nhánh sang `IDENT`, hành vi chuyển tiếp tương lai của nhánh HOA và nhánh thường là **đồng nhất 100%**, nên thuật toán Moore & Hopcroft gộp được tới 12/64 trạng thái (`-18.75%`).
> - Trong khi đó, `MiniLang` có tới 39 loại token phân biệt (nhiều toán tử và dấu câu 1–2 ký tự), nên ngay từ phân hoạch khởi đầu $\Pi_0$ các trạng thái kết thúc đã thuộc về các lớp token khác nhau và chỉ gộp được 8/86 trạng thái dư thừa (`-9.3%`).

**Câu 32. Nếu muốn nâng cấp đồ án này thành một trình biên dịch hoàn chỉnh cho `MiniLang` trong học phần tiếp theo, các bước kết nối cụ thể với kiến thức Chương 4 (CFG) và Chương 5 (PDA) của môn Ngôn ngữ hình thức là gì?**
> **Trả lời:**
> 1. **Đầu ra của Đề tài T13 (Chương 2 & 3 — FA/RE):** Phương thức `LexicalAnalyzer.scan(source)` (hoặc lớp `MiniLangLexer` độc lập sinh bởi `cli.py codegen`) trả về dãy token $T_1 T_2 \dots T_m$ (đã loại bỏ `WHITESPACE`, `COMMENT`, `BLOCK_COMMENT`), trong đó mỗi `Token.token_name` chính là một **ký hiệu kết thúc (terminal symbol)** của Văn phạm phi ngữ cảnh $G = (V, \Sigma_{\text{tok}}, R, S)$ ở Chương 4.
> 2. **Tầng Phân tích cú pháp (Chương 4 & 5 — CFG/PDA):** Xây dựng văn phạm phi ngữ cảnh $G$ cho các câu lệnh của `MiniLang` (`stmt -> if_stmt | while_stmt | let_stmt | block`, `expr -> term ((+|-) term)*`...) và cài đặt Otomat đẩy xuống đơn định (Deterministic PDA) dưới dạng bộ phân tích `LL(1)` hoặc `LR(1)` để dựng Cây cú pháp trừu tượng (AST) của chương trình!

---

### Nhóm D — Nâng cấp Chuyên sâu Version 2.0 Ultimate (Kleene 360°, Đại số Boole, Ma trận Giao & Flex Codegen)

**Câu 33. Thuật toán GNFA State Elimination (`dfa_to_regex` trong `gnfa.py`) hoạt động như thế nào để chuyển một DFA ngược trở lại thành Biểu thức chính quy?**
> **Trả lời:** Đây là chứng minh chiều ngược kinh điển của **Định lý Kleene** (Hopcroft, Motwani & Ullman, Mục 3.2.1):
> 1. **Làm sạch & Chuẩn hóa GNFA:** Đầu tiên loại bỏ các trạng thái không đạt tới được từ $D_0$ và các trạng thái không có đường đi tới $F$ (nếu $F$ không đạt tới được thì trả về ngay $\varnothing$). Sau đó thêm 1 đỉnh khởi đầu mới $q_{\text{start}}$ nối $\varepsilon$ vào $D_0$, và 1 đỉnh kết thúc duy nhất $q_{\text{accept}}$ nhận cung $\varepsilon$ từ mọi $f \in F$. Các cung song song giữa cùng cặp đỉnh $(p, q)$ được gộp lại bằng phép hợp ký tự tối giản `charset_to_regex_pattern()`.
> 2. **Chiến lược chọn đỉnh khử thông minh:** Ở mỗi bước, trong các đỉnh trung gian còn lại, thuật toán chọn đỉnh $q_{\text{rip}}$ có tích bậc vào $\times$ bậc ra ($\text{in\_deg}(q) \times \text{out\_deg}(q)$) nhỏ nhất (ưu tiên đỉnh không có khuyên tự lặp) để giữ biểu thức trung gian ngắn gọn nhất có thể!
> 3. **Công thức cập nhật cung Kleene:** Với mọi cặp đỉnh đứng trước $q_i$ (có cung đi vào $q_{\text{rip}}$) và đỉnh đứng sau $q_j$ (có cung đi ra từ $q_{\text{rip}}$), biểu thức trên cung $(q_i, q_j)$ được cập nhật thành:
>    $$R'(q_i, q_j) = R(q_i, q_j) \;\cup\; R(q_i, q_{\text{rip}}) \cdot \big(R(q_{\text{rip}}, q_{\text{rip}})\big)^* \cdot R(q_{\text{rip}}, q_j)$$
>    kết hợp các luật rút gọn đại số ($\varnothing \cdot X = \varnothing$, $\varepsilon \cdot X = X$, $\varnothing^* = \varepsilon$, $r \cdot r^* = r^+$).
> 4. **Kiểm chứng khép kín 360°:** Khi khử hết mọi đỉnh trung gian, nhãn duy nhất còn lại $R(q_{\text{start}}, q_{\text{accept}})$ chính là $R_{\text{sinh}}$. Hệ thống tự động biên dịch ngược $R_{\text{sinh}}$ sang DFA và chạy Product Automaton đối chiếu với DFA gốc để chứng minh $L(R_{\text{gốc}}) \equiv L(R_{\text{sinh}})$!

**Câu 34. Tại sao việc bỏ sót các ký tự điều khiển ASCII như `\0`, `\f`, `\v`, `\x7f` trong bảng chữ cái lại làm gãy luật đối hợp đại số Boole $\sim(\sim A) = A$, và nhóm đã khắc phục ra sao?**
> **Trả lời:** Trong đại số Boole trên tập vũ trụ $\Sigma$, phép lấy phần bù $\sim A = \Sigma \setminus A$ chỉ thỏa mãn luật đối hợp $\sim(\sim A) = A$ khi mọi phần tử hợp lệ đều nằm trong $\Sigma$. Nếu `ASCII_SIGMA` chỉ chứa 98 ký tự in được + `\t, \n, \r` mà thiếu `\f` (`0x0C`) hoặc `\v` (`0x0B`), thì khi viết lớp ký tự `[\f\v]` ($A = \{\text{'\textbackslash f'}, \text{'\textbackslash v'}\} \not\subseteq \Sigma$), phép lấy bù lần 1 cho $\sim A = \Sigma \setminus A = \Sigma$, và lấy bù lần 2 cho $\sim(\sim A) = \Sigma \setminus \Sigma = \varnothing \neq A$!
> Phiên bản v2.0 sửa triệt để bằng cách định nghĩa `ASCII_SIGMA = tuple(chr(i) for i in range(128))` phủ kín toàn bộ **128 mã ASCII `0x00..0x7F`**, kết hợp với tập Unicode động $U$ và `NON_ASCII`, đồng thời kiểm chứng tự động cả ở mức tập ký tự (`complement_charset`) lẫn mức ô-tô-mát (`complement_dfa(complement_dfa(D)) ≡ D` và $L(D) \cap L(\sim D) = \varnothing$) trong `test_v2_2`!

**Câu 35. Tại sao quy tắc `STRING_LIT` trong `MiniLang` phải viết là `"([^"\\\n\r]|\\.)*"` (loại trừ cả `\r` lẫn `\n`) thay vì chỉ loại trừ `\n`?**
> **Trả lời:** Trên hệ điều hành Windows, ký tự xuống dòng là cặp CRLF `\r\n` (`0x0D 0x0A`). Nếu `STRING_LIT` chỉ viết `"([^"\\\n]|\\.)*"` (chỉ cấm `\n` mà quên cấm `\r`), thì:
> 1. Một chuỗi chứa ký tự `\r` trần (carriage return Mac/Windows lỗi) sẽ vô tình được nhận là chuỗi đơn dòng hợp lệ.
> 2. Khi gặp chuỗi quên đóng dấu ngoặc kép trên file CRLF như `"unclosed\r\nlet ok = 1;`, DFA sẽ ăn luôn ký tự `\r` ở cuối dòng 1 vào đường đi thất bại trước khi va vào `\n`, làm lệch ranh giới lỗi của chế độ `smart_sync`!
> Khi loại trừ cả `\r` và `\n` (`[^"\\\n\r]`), DFA dừng chính xác ngay trước `\r\n` (đồng thời tách `\r` và `\n` thành lớp tương đương riêng, nâng số lớp tương đương của `MiniLang` từ 43 lên **44 lớp**), giữ sạch hoàn toàn dòng 2!

**Câu 36. Ma trận Giao nhau Tĩnh $L(R_i) \cap L(R_j)$ trên Tab 2 hoạt động như thế nào và khác gì với kiểm tra `Shadowed Rules`?**
> **Trả lời:**
> - Kiểm tra `Shadowed Rules` phát hiện trường hợp **nghiêm trọng nhất**: một quy tắc $R_j$ bị nuốt trọn 100% bởi các quy tắc đứng trước ($L(R_j) \subseteq \bigcup_{i < j} L(R_i)$) nên không bao giờ khớp được bất kỳ chuỗi nào.
> - Tuy nhiên, người thiết kế ngôn ngữ còn cần biết **tất cả các cặp quy tắc có giao nhau** ($L(R_i) \cap L(R_j) \neq \varnothing$), kể cả giao một phần (*partial overlap*) hay bao hàm an toàn (*safe subset*).
> - Hàm `analyze_token_intersections(specs)` trong `verifier.py` biên dịch từng quy tắc $R_i$ sang Min-DFA riêng $D_i$ trên bảng chữ cái chung $\Sigma(U_{\text{all}})$, sau đó chạy BFS trên từng cặp tích $D_i \times D_j$ ($i < j$) để kiểm tra đồng thời 3 tính chất rỗng: $L(D_i) \cap L(D_j)$ (giao), $L(D_i) \setminus L(D_j)$ và $L(D_j) \setminus L(D_i)$. Nhờ đó hệ thống phân loại chính xác 5 quan hệ tập hợp ($\varnothing$, $R_i \subset R_j$, $R_i \equiv R_j$, $R_i \supset R_j$, giao một phần $R_i \cap R_j$) và trích xuất **chuỗi chứng nhân ngắn nhất** $w \in L(R_i) \cap L(R_j)$! Trên `MiniLang`, trong $\binom{39}{2} = 741$ cặp, hệ thống chứng minh 732 cặp rời nhau hoàn toàn và chỉ ra đúng 9 cặp giao nhau (`KW_IF..BOOL_LIT` $\subset$ `IDENTIFIER` với chứng nhân `'if'`, `'else'`, ..., `'true'`).

**Câu 37. Bộ sinh mã Lexer Độc lập kiểu Flex (`codegen.py` / `cli.py codegen`) sinh ra cấu trúc mã nguồn như thế nào?**
> **Trả lời:** Giống như công cụ kinh điển `lex`/`flex` trong C biên dịch đặc tả `.l` thành bảng số nguyên `yy_nxt[][]` trong `lex.yy.c`, module `codegen.py` đóng gói toàn bộ `Minimized DFA` của bất kỳ bộ đặc tả nào thành một file `.py` hoàn toàn độc lập (~527 dòng cho `MiniLang`, **0 phụ thuộc ngoài, không cần thư mục `lexer_engine/`, Zero `import re`**) gồm 4 bảng hằng số tĩnh:
> 1. `ASCII_CLASS_MAP` (mảng 128 số nguyên ánh xạ `ord(ch)` sang chỉ số lớp tương đương trong $O(1)$).
> 2. `UNICODE_CLASS_MAP` (từ điển ánh xạ các ký tự Unicode tường minh $c \in U$) và hằng `NON_ASCII_CLASS`.
> 3. `TRANSITIONS` (ma trận 2 chiều `|Q_min| × |Σ/≡|` chứa trạng thái đích hoặc `-1` nếu là `DEAD`).
> 4. `ACCEPT_TABLE` (mảng chứa tuple `(token_name, priority, skip)` cho từng trạng thái kết thúc).
> Đi kèm bên dưới là vòng lặp quét Maximal Munch tuyến tính $O(n)$ có sẵn bảng nhớ `failed_states` (Reps, 1998), hỗ trợ cả `panic_char` và `smart_sync` cùng giao diện CLI riêng. Trong `test_v2_5`, bộ kiểm thử chạy đối chứng vi sai (*differential testing*) khẳng định file `.py` sinh ra cho kết quả trùng khớp **100% từng Token, từng tọa độ `(line, col)` và từng `LexicalError`** với `LexicalAnalyzer` gốc!

**Câu 38. Tại sao hằng số nội bộ `NON_ASCII` được chọn là `"\ufdd0"` thay vì `"\x80"` như ở bản đầu tiên?**
> **Trả lời:** Ở bản 1.0, `"\x80"` (`U+0080`, ký tự điều khiển C1 PAD trong Latin-1 Supplement) là một điểm mã Unicode có thực có thể xuất hiện trong chuỗi đầu vào hoặc trong biểu thức escape `\x80` / `\u0080` của người dùng! Nếu người dùng viết regex khớp `\u0080`, nó sẽ bị đụng độ trực tiếp với hằng sentinel `NON_ASCII`. Ngược lại, dải `U+FDD0..U+FDEF` được **Chuẩn Unicode (Mục 23.7 — Noncharacters)** quy định vĩnh viễn là *mã phi ký tự nội bộ (internal-use noncharacters)* không bao giờ được gán cho bất kỳ ký tự văn bản nào. Việc chọn `NON_ASCII = "\ufdd0"` (và từ chối nếu người dùng cố tình nhập trực tiếp noncharacter nội bộ này) đảm bảo không bao giờ xảy ra va chạm ký hiệu (symbol collision) trên toàn bộ không gian Unicode!

