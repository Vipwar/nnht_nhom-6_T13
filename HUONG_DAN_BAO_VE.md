# TÀI LIỆU HƯỚNG DẪN TRÌNH BÀY, DEMO VÀ CÂU HỎI ÔN TẬP — ĐỀ TÀI T13

- **Học phần:** Ngôn ngữ hình thức (*Introduction to Formal Languages*) — UEH
- **Giảng viên hướng dẫn:** ThS. Hồ Thị Thanh Tuyến
- **Đề tài T13:** Xây dựng Bộ phân tích từ vựng dựa trên Automata (*Automata-based Lexical Analyzer*)
- **Thời lượng bảo vệ dự kiến:** 15 phút (8–10 phút trình bày kết hợp demo, 5–7 phút hỏi đáp).

---

## PHẦN 1: KỊCH BẢN TRÌNH BÀY VÀ DEMO TRỰC TIẾP (9 PHÚT 30 GIÂY)

| Thời lượng | Thành viên | Nội dung trình bày và thao tác Demo | Nội dung trọng tâm cần làm rõ |
|---|---|---|---|
| **0:00 – 1:30** | **TV 1** (Mở đầu và Mô hình) | **Slide 1–3:** Vai trò của Lexical Analyzer; quy trình chuyển đổi khép kín hai chiều theo Định lý Kleene (`RE ⇄ Thompson ε-NFA ⇄ NFA khử ε ⇄ Subset/Direct DFA ⇄ Moore/Hopcroft Min-DFA ⇄ GNFA RE`); phân hoạch bảng chữ cái Unicode động $\Sigma(U) = 128\text{ ASCII} \cup U \cup \{\text{NON\_ASCII}\}$ bảo toàn phép bù kép $\sim(\sim A) = A$. | Nêu rõ toàn bộ lõi không dùng `import re`, có giới hạn `MAX_AST_NODES = 4096` chặn nhân bản cây cú pháp quá mức, hỗ trợ từ khóa tiếng Việt `nếu`, ký hiệu `€` và chuỗi UTF-8. |
| **1:30 – 3:45** | **TV 2** (Thompson, Khử ε, Direct DFA và GNFA) | **Slide 4–6 + Mở Tab 3 trên giao diện Web:**<br>1. Chọn `(a\|b)*abb (Slide 38)` -> đối chiếu số trạng thái: Thompson ε-NFA = 11, NFA khử ε (ĐL 2) = 6, Subset DFA = 5, Min-DFA = 4; sau đó mở thẻ `6. GNFA (DFA -> RE)` xem các bước khử đỉnh sinh biểu thức `b*a(a\|ba\|bb(a\|b+a))*bb` tương đương $R_0$.<br>2. Chọn `(a\|ba)(a\|b)*ba (Slide 54)` -> đối chiếu cây `r·#` 8 nút lá và bảng `followpos` với Slide 54.<br>3. Chọn ví dụ `(nếu\|lặp)_[0-9]+€` để minh họa bảng chữ cái động $\Sigma(U)$. | Thể hiện cả chiều xuôi và chiều ngược của Định lý Kleene cùng 2 ví dụ trong bài giảng Chương 3.1. |
| **3:45 – 5:45** | **TV 3** (Subset, Moore/Hopcroft, Myhill-Nerode và Ma trận giao) | **Slide 7 + Mở Tab 2 và Tab 4 trên giao diện Web:**<br>1. Trên **Tab 2 (`MiniLang`)**: mở thẻ `Ma trận giao L(Rᵢ) ∩ L(Rⱼ)` xem bảng $39 \times 39$ chỉ ra 9/741 cặp giao nhau (`KW_IF..BOOL_LIT` $\subset$ `IDENTIFIER`) kèm chuỗi chứng nhân ngắn nhất (`'if'..'true'`), và xem bảng chứng nhân Myhill-Nerode (`3003/3003` cặp).<br>2. Chuyển sang **Tab 4**: bấm `+ Mẫu Unicode (nếu / €)`, sau đó bấm `Thử che khuất` để đưa `IDENTIFIER` lên trước `KW_IF` và quan sát cảnh báo quy tắc bị che khuất. | Giải thích cách dùng Product Automaton phân tích giao nhau $L(R_i) \cap L(R_j)$ và kiểm tra tính tối giản Myhill-Nerode. |
| **5:45 – 8:00** | **TV 4** (Bộ quét O(n), Phục hồi lỗi và Sinh mã Lexer) | **Slide 8–9 + Mở Tab 1 trên giao diện Web:**<br>1. Quét mã nguồn mẫu chứa chuỗi UTF-8/CRLF, chạy từng bước trên token quay lui `1.5e + 2`, đổi giữa hai chế độ `Panic-mode (1 ký tự)` và `Smart-Sync` trên mã có chuỗi chưa đóng, thử nút đổi giao diện `Dark` / `Light`.<br>2. Bấm nút `Xuất Lexer (.py)` trên thanh công cụ để tải file `minilang_standalone_lexer.py` (~527 dòng, hoạt động độc lập theo bảng chuyển trạng thái như công cụ `flex`). | Minh họa cách đóng gói bảng chuyển trạng thái Min-DFA thành bộ quét độc lập và cơ chế bảng nhớ `failed_states` (Reps, 1998). |
| **8:00 – 9:30** | **TV 1 / TV 4** (Kiểm thử, Bổ đề Bơm và Kết luận) | **Slide 10–13 + Mở Tab 5 trên giao diện Web:**<br>1. Bấm `Chạy kiểm thử` xem kết quả 72/72 test case đạt cùng bảng kiểm tra chuỗi lỗi 10.000 ký tự (`memoized_cutoffs = 5000`).<br>2. Trình bày giới hạn lý thuyết của DFA theo Bổ đề Bơm (Chương 3.2): bình luận lồng nhau tùy ý `/* /* ... */ */` tương ứng ngôn ngữ $L = \{a^n b^n \mid n \ge 1\}$ thuộc lớp phi ngữ cảnh (CFL). | Liên hệ giới hạn của ngôn ngữ chính quy ở Chương 3.2 với hướng mở rộng sang Chương 4 (CFG/PDA). |

---

## PHẦN 2: SƠ ĐỒ MÃ NGUỒN (`lexer_engine/`) ĐỂ TRA CỨU KHI VẤN ĐÁP

1. **Bảng chữ cái 128 ASCII (`0x00..0x7F`), phân hoạch Unicode động $\Sigma(U)$ và phép bù tập hợp**: [`lexer_engine/models.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/models.py) — bao phủ đủ 128 mã ASCII (kể cả `\0`, `\f`, `\v`, `\x7f`), hằng phi ký tự nội bộ `NON_ASCII = "\ufdd0"` (Unicode Standard Section 23.7), hàm `build_dynamic_sigma(U)` và `complement_charset()` đảm bảo $\sim(\sim A) = A$.
2. **Bộ phân tích cú pháp RE tự viết (giới hạn `MAX_AST_NODES = 4096`, `{m,n}`, `\xHH`, `\uHHHH`, không dùng `import re`)**: [`lexer_engine/regex_parser.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/regex_parser.py) — lớp `RegexParser` đệ quy 4 mức ưu tiên; ước lượng trước số nút AST trong $O(1)$ để chặn biểu thức lồng nhau kiểu `(((a{64}){64}){64})`; trích tập `explicit_unicode_chars()`.
3. **Cấu trúc Thompson và Định lý 2 khử chuyển tiếp $\varepsilon$ (`ε-NFA -> NFA không ε`)**: [`lexer_engine/thompson.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/thompson.py) — lớp `_ThompsonBuilder` dựng mảnh ε-NFA theo Định lý 3; hàm `eliminate_epsilon(nfa)` cài đặt Định lý 2 (Slide 21–22 Chương 3.1).
4. **Đơn định hóa tập con (Subset Construction) và phân hoạch bảng chữ cái**: [`lexer_engine/subset_construction.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/subset_construction.py) — gom $\Sigma(U)$ thành các lớp tương đương (`MiniLang`: 44 lớp) và phân giải xung đột theo `priority`.
5. **Phương pháp trực tiếp RE -> DFA cho biểu thức đơn lẻ (`r·#`) và đa-token (`(R₁·#₁)|...|(R_k·#_k)`)**: [`lexer_engine/direct_dfa.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/direct_dfa.py) — hàm `build_direct_dfa()` và `build_combined_direct_dfa()` tính `nullable`, `firstpos`, `lastpos`, `followpos`.
6. **Tối thiểu hóa Moore và Hopcroft $O(p \cdot |Q| \log |Q|)$ kèm lấy phần bù DFA**: [`lexer_engine/dfa_minimizer.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/dfa_minimizer.py) — `minimize_dfa()` (Moore), `minimize_dfa_hopcroft()` (Hopcroft) và `complement_dfa()` kiểm tra $\sim(\sim D) \equiv D$.
7. **Khử trạng thái GNFA (`DFA -> Regular Expression`) theo chiều ngược Định lý Kleene**: [`lexer_engine/gnfa.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/gnfa.py) — hàm `dfa_to_regex()` chọn đỉnh khử có tích $\text{in\_deg} \times \text{out\_deg}$ nhỏ nhất, rút gọn đại số và đối chiếu $L(R_0) \equiv L(R_{\text{sinh}})$.
8. **Kiểm chứng tương đương, Myhill-Nerode và ma trận giao nhau tĩnh $L(R_i) \cap L(R_j)$**: [`lexer_engine/verifier.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/verifier.py) — `check_dfa_equivalence()`, `verify_dfa_is_minimal()`, `check_dfa_intersection()` và `analyze_token_intersections()`.
9. **Bộ quét Maximal Munch tuyến tính $O(n)$ (Reps, 1998) và bộ sinh mã Lexer độc lập**: [`lexer_engine/scanner.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/scanner.py) và [`lexer_engine/codegen.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/codegen.py) (`generate_standalone_lexer()`).
10. **Xuất và đọc ngược định dạng JFLAP 7.x (`.jff`)**: [`lexer_engine/jflap_export.py`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/lexer_engine/jflap_export.py) — xử lý cả các ký tự điều khiển XML 1.0 (`\v`, `\f`, `\0`) và tập Unicode $\Sigma(U)$.

---

## PHẦN 3: 38 CÂU HỎI PHẢN BIỆN VÀ GỢI Ý TRẢ LỜI

### Nhóm A — Nền tảng Lý thuyết Chương 1, 2, 3 và Mô hình Toán học

**Câu 1. Tại sao bộ phân tích từ vựng lại dùng Otomat hữu hạn (DFA/NFA) và Biểu thức chính quy mà không dùng Văn phạm phi ngữ cảnh (CFG) hay Otomat đẩy xuống (PDA)?**
> **Trả lời:** Hầu hết cấu trúc từ vựng của ngôn ngữ lập trình (từ khóa, định danh, số nguyên, số thực, chuỗi ký tự, bình luận không lồng nhau) không có cấu trúc đệ quy tự lồng sâu tùy ý nên thuộc lớp Ngôn ngữ chính quy (*Regular Languages*). Theo Định lý Kleene, mọi ngôn ngữ chính quy đều nhận diện được bằng DFA trong thời gian tuyến tính $O(n)$ với không gian nhớ $O(1)$ (mỗi ký tự tra bảng chuyển trạng thái một lần), nhanh và gọn hơn đáng kể so với các thuật toán phân tích CFG như CYK $O(n^3)$ hay LR.

**Câu 2. Trong bài giảng Chương 3.1 có các định lý chuyển đổi hai chiều giữa FA và RE (Định lý Kleene). Nhóm đã cài đặt những định lý nào?**
> **Trả lời:** Nhóm đã cài đặt đầy đủ cả hai chiều chuyển đổi của Định lý Kleene trong Chương 3.1:
> - **Định lý 3 (Slide 24–30):** Chuyển Biểu thức chính quy sang $\varepsilon$-NFA bằng cấu trúc Thompson (`thompson.py`).
> - **Định lý 2 (Slide 21–22):** Khử chuyển tiếp $\varepsilon$ để chuyển $\varepsilon$-NFA sang NFA không có $\varepsilon$ (`eliminate_epsilon` trong `thompson.py`).
> - **Định lý 1 (Slide 18):** Đơn định hóa tập con chuyển NFA/$\varepsilon$-NFA sang Subset DFA (`subset_construction.py`).
> - **Mục 2.5 (Slide 43–57):** Phương pháp trực tiếp chuyển RE sang Direct DFA qua cây cú pháp $r\cdot \#$ và bảng `followpos` (`direct_dfa.py`).
> - **Giải thuật 3.6 (Slide 58):** Tối thiểu hóa DFA bằng cả hai thuật toán Moore và Hopcroft (`dfa_minimizer.py`).
> - **Chiều ngược Định lý Kleene (Hopcroft Mục 3.2.1):** Khử trạng thái trên GNFA (`DFA -> Regular Expression`) trong `gnfa.py`, sau đó biên dịch ngược $R_{\text{sinh}}$ để kiểm tra $L(R_{\text{gốc}}) \equiv L(R_{\text{sinh}})$.

**Câu 3. Làm thế nào hệ thống vừa quét được chuỗi tiếng Việt UTF-8 (`"Xin chào UEH"`), vừa cho phép khai báo trực tiếp từ khóa/ký hiệu Unicode trong Regex (như `nếu`, `€`, `[^€]`) mà bảng chữ cái $\Sigma$ của DFA vẫn hữu hạn nhỏ gọn và bảo toàn luật bù kép $\sim(\sim A) = A$?**
> **Trả lời:** Hệ thống áp dụng kỹ thuật phân hoạch bảng chữ cái Unicode động $\Sigma(U)$ trong `models.py` và `regex_parser.py`:
> - `ASCII_SIGMA` bao phủ đủ 128 mã ASCII `0x00..0x7F` (kể cả `\0`, `\f`, `\v`, `\x7f`) để không sót ký tự nào khi lấy phần bù.
> - Hằng phi ký tự nội bộ `NON_ASCII = U+FDD0` (theo chuẩn Unicode Section 23.7, không xuất hiện như ký tự văn bản thông thường) đại diện cho tất cả điểm mã Unicode ngoài tập tường minh.
> - Khi biên dịch biểu thức hoặc bộ đặc tả, parser duyệt AST để thu thập tập hữu hạn $U$ các ký tự Unicode xuất hiện tường minh (ví dụ $U = \{\text{'ế'}, \text{'€'}\}$) và tạo bảng chữ cái:
>   $$\Sigma(U) = \text{ASCII\_SIGMA} \cup U \cup \{\text{NON\_ASCII}\}$$
> - Khi đọc ký tự đầu vào $c \ge 128$: nếu $c \in U$ thì tra theo đúng ký tự $c$; nếu $c \notin U$ thì ánh xạ về `NON_ASCII`. Nhờ vậy lớp phủ định `[^€]` loại trừ đúng `'€'` nhưng vẫn khớp `'ế'`, đồng thời $\sim(\sim A) = A$ luôn được giữ đúng.

**Câu 4. Tại sao khi tối thiểu hóa Multi-token DFA cho bộ phân tích từ vựng, ta không khởi tạo $\Pi_0 = \{Q \setminus F, F\}$ như trong DFA nhận diện ngôn ngữ đơn lẻ?**
> **Trả lời:** Ở DFA đơn lẻ, đầu ra chỉ mang giá trị nhị phân ($\text{Accept}$ hoặc $\text{Reject}$), nên mọi trạng thái kết thúc $q \in F$ cùng thuộc một nhóm ban đầu. Trong khi đó, bộ phân tích từ vựng hoạt động như máy trạng thái kiểu Moore có hàm gán nhãn $\tau: F \to \{T_1, T_2, \dots, T_k\}$: trạng thái kết thúc của `KW_IF` trả về `KW_IF`, còn trạng thái của `INT_LIT` trả về `INT_LIT`. Nếu gộp chung toàn bộ $F$ vào một khối trong $\Pi_0$, thuật toán sẽ gộp nhầm các trạng thái kết thúc của các loại token khác nhau. Do đó phân hoạch ban đầu phải tách theo từng nhãn token:
> $$\Pi_0 = \{ Q \setminus F \} \cup \{ F_{T_1}, F_{T_2}, \dots, F_{T_m} \}$$

**Câu 5. Giải thích sự khác biệt giữa thuật toán tối thiểu hóa Moore và thuật toán Hopcroft trong `dfa_minimizer.py`?**
> **Trả lời:**
> - **Thuật toán Moore (Partition Refinement — Giải thuật 3.6):** Mỗi vòng lặp duyệt qua toàn bộ các khối trong $\Pi_k$ và tính chữ ký chuyển tiếp $(\text{block}(\delta(q, E_1)), \dots, \text{block}(\delta(q, E_p)))$ cho mọi trạng thái $q$ cho đến khi hội tụ $\Pi_{k+1} = \Pi_k$. Độ phức tạp xấu nhất là $O(p \cdot |Q|^2)$, ưu điểm là cho bảng vết từng vòng $\Pi_0 \to \Pi_1 \to \dots \to \Pi_k$ dễ theo dõi.
> - **Thuật toán Hopcroft (1971):** Dựng bảng tiền ảnh ngược $\delta^{-1}(A, c)$ và duy trì danh sách chờ (worklist) $W$. Mỗi bước lấy $(A, c)$ từ $W$, xét các khối $Y$ bị tập tiền ảnh $X = \delta^{-1}(A, c)$ chia thành hai phần khác rỗng $Y_1$ và $Y_2$; nếu $Y \notin W$ thì chỉ đưa khối nhỏ hơn ($\min(|Y_1|, |Y_2|)$) vào $W$. Vì mỗi trạng thái rơi vào nửa nhỏ hơn tối đa $\log_2 |Q|$ lần, độ phức tạp đạt $O(p \cdot |Q| \log |Q|)$.
> - Cả hai thuật toán được chạy song song và kiểm tra tương đương bằng Product Automaton (cùng ra 78 trạng thái trên `MiniLang`, 20 trên `CalcLang`, 52 trên `MiniSQL`).

**Câu 6. Làm thế nào nhóm kiểm chứng rằng DFA sau khi tối thiểu hóa đã thực sự tối giản (không thể gộp thêm cặp trạng thái nào nữa)?**
> **Trả lời:** Hàm `verify_dfa_is_minimal(dfa)` trong `verifier.py` dựa trên Định lý Myhill-Nerode: hai trạng thái $p \neq q$ phân biệt được khi và chỉ khi tồn tại chuỗi hậu tố $w \in \Sigma^*$ sao cho $\tau(\hat{\delta}(p, w)) \neq \tau(\hat{\delta}(q, w))$.
> Thuật toán đánh dấu các cặp cơ sở có $\tau(p) \neq \tau(q)$ với $w = \varepsilon$, rồi lan truyền ngược để tìm chuỗi phân biệt ngắn nhất cho mọi cặp còn lại:
> - Trên `(a|b)*abb` (4 trạng thái `M0..M3`): đủ $\binom{4}{2} = 6/6$ cặp có chuỗi phân biệt (`(M0,M1): "bb"`, `(M0,M2): "b"`, `(M0,M3): ""`, ...).
> - Trên `MiniLang` (78 trạng thái): đủ $\binom{78}{2} = 3.003 / 3.003$ cặp.
> - Trên `CalcLang` (20 trạng thái): đủ $\binom{20}{2} = 190 / 190$ cặp.
> - Trên `MiniSQL` (52 trạng thái): đủ $\binom{52}{2} = 1.326 / 1.326$ cặp.

**Câu 7. Tại sao cần thêm trạng thái chết `DEAD = -1` trước khi chạy tối thiểu hóa Moore/Hopcroft rồi loại bỏ `DEAD` ở cuối?**
> **Trả lời:** DFA sinh từ Subset Construction hoặc Direct DFA có hàm chuyển tiếp thưa (các cung đi vào $\varnothing$ không được lưu). Nếu không bổ sung trạng thái `DEAD = -1` để đưa $\delta$ về hàm toàn phần, phép lấy tiền ảnh ngược $\delta^{-1}$ trong Hopcroft có thể bỏ sót sự khác biệt giữa một trạng thái không có cung trên ký tự $a$ (rơi vào `DEAD`) và một trạng thái đi sang $r \notin F$ nhưng từ $r$ vẫn có đường đi tiếp tới $F$. Sau khi phân hoạch xong, khối chứa `DEAD` được lược bỏ để đồ thị gọn nhẹ.

**Câu 8. Giải thích cách mở rộng phương pháp trực tiếp (`Direct RE -> DFA`) sang bài toán Đa-Token (`build_combined_direct_dfa`)?**
> **Trả lời:** Với $k$ quy tắc token $\{(T_1, R_1, p_1), \dots, (T_k, R_k, p_k)\}$, chương trình tạo cây cú pháp kết hợp:
> $$R_{\text{comb}} = (R_1 \cdot \#_1) \mid (R_2 \cdot \#_2) \mid \dots \mid (R_k \cdot \#_k)$$
> Mỗi nút đánh dấu kết thúc $\#_r$ mang một chỉ số vị trí lá riêng $i_r$ kèm thông tin `AcceptInfo(T_r, p_r, skip_r)`. Các hàm `nullable`, `firstpos`, `lastpos`, `followpos` giữ nguyên công thức chuẩn; khi một tập vị trí $S$ chứa nhiều dấu kết thúc $\#_r$, nhãn chấp nhận được gán theo quy tắc có `priority` nhỏ nhất: $\tau(S) = \arg\min_{\#_r \in S} p_r$.

---

### Nhóm B — Thuật toán Cài đặt, Trường hợp Biên và Độ phức tạp

**Câu 9. Định lượng đếm `{m}`, `{m,}`, `{m,n}` được xử lý như thế nào mà không cần sửa cấu trúc Thompson hay `followpos`?**
> **Trả lời:** Parser khai triển đại số trực tiếp ở tầng cây cú pháp AST trong `regex_parser.py` (`_apply_counted_quantifier`):
> - $R\{m\} \equiv R \cdot R \cdots R$ ($m$ lần; nếu $m = 0$ trả về `EpsilonNode()`).
> - $R\{m,\} \equiv R \cdot R \cdots R \cdot R^*$.
> - $R\{m,n\} \equiv R \cdot R \cdots R \cdot (R?) \cdots (R?)$ ($m$ bản bắt buộc nối với $n - m$ bản tùy chọn).
> Mỗi bản sao được nhân bản sâu (`_clone_ast`) để có vị trí lá độc lập, đồng thời kiểm tra $0 \le m \le n \le 64$ và tổng nút cây không vượt `MAX_AST_NODES = 4096`.

**Câu 10. Bộ phân tích cú pháp RE xử lý các trường hợp biên của lớp ký tự như `[-a]`, `[a-]`, `[-]`, `[^-]`, `[^^]`, `[\[\]\\]` như thế nào?**
> **Trả lời:** Trong `_parse_char_class()` của `regex_parser.py`:
> - Dấu `-` đứng ngay đầu lớp ký tự (sau `[` hoặc `[^`) hay đứng ngay cuối lớp trước `]` được hiểu là ký tự gạch ngang thông thường `'-'`.
> - Dấu `-` nằm giữa hai ký tự $c_1 - c_2$ được kiểm tra điều kiện $\text{ord}(c_1) \le \text{ord}(c_2)$; nếu ngược thứ tự như `[z-a]` sẽ báo `RegexSyntaxError`.
> - Với `[^^]`, dấu `^` đầu tiên bật cờ phủ định, dấu `^` thứ hai là ký tự `'^'`, cho kết quả $\Sigma \setminus \{\text{'\^'}\}$.
> - Các lớp rỗng `[]`, `[^]` đều được bắt lỗi cú pháp rõ ràng.

**Câu 11. Quy tắc bị che khuất (Shadowed Rule) là gì và được phát hiện tự động bằng cách nào?**
> **Trả lời:** Quy tắc $(T_i, R_i, p_i)$ bị che khuất hoàn toàn nếu mọi chuỗi thuộc $L(R_i)$ đều đã thuộc hợp ngôn ngữ của các quy tắc có độ ưu tiên cao hơn đứng trước nó:
> $$L(R_i) \subseteq \bigcup_{j < i} L(R_j)$$
> Ví dụ đặt `IDENTIFIER` lên trước `KW_IF`. Trên Minimized DFA $D_{\min}$, điều này tương đương với việc không tồn tại trạng thái kết thúc đạt tới được nào mang nhãn chiến thắng $T_i$. Phương thức `LexicalAnalyzer.compile()` kiểm tra tập nhãn kết thúc trên $D_{\min}$, đối chiếu `all_matched_tokens` và ma trận giao nhau để chỉ rõ quy tắc nào đã che khuất $T_i$.

**Câu 12. Tại sao bộ quét Maximal Munch thông thường có thể suy biến thành $O(n^2)$, và kỹ thuật `failed_states` (Reps, 1998) trong `scanner.py` khắc phục như thế nào?**
> **Trả lời:**
> - Với chuỗi mở đầu bằng `"` theo sau là 5.000 cặp `\"` nhưng thiếu dấu `"` đóng ở cuối (dài 10.001 ký tự), bộ quét thông thường đọc đến cuối chuỗi mới biết thất bại, báo lỗi 1 ký tự rồi lại dò lại cùng hậu tố dài ở lượt tiếp theo, dẫn đến $\Theta(n^2)$ bước chuyển.
> - Giải pháp của Reps (1998) lưu tập `failed_states: Set[Tuple[str, int]]` gồm các cặp `(trạng_thái, vị_trí)` nằm sau `last_accept_pos` đã chứng minh không thể đi tới trạng thái kết thúc nào. Do DFA đơn định, nếu lượt quét sau gặp lại `(curr_state, scan_pos) in failed_states` thì dừng nhánh ngay trong $O(1)$.
> - Vì chỉ có $|Q|$ trạng thái và $n$ vị trí văn bản, tổng số bước dò thất bại trên toàn văn bản bị chặn bởi $|Q| \cdot n = O(n)$. Trên mẫu 10.001 ký tự nói trên, bộ quét cắt nhánh đúng 5.000 lần và chạy khoảng 20–25 ms.

**Câu 13. So sánh hai chế độ phục hồi lỗi `panic_char` và `smart_sync` trong `scanner.py`?**
> **Trả lời:**
> - `panic_char` (Panic-mode theo từng ký tự): khi không khớp được token nào tại `pos`, ghi nhận lỗi cho ký tự `source[pos]` và tăng `pos += 1`. Phù hợp khi mã nguồn có các ký tự lạ đơn lẻ như `$`, `@`.
> - `smart_sync` (đồng bộ theo ngữ cảnh chuỗi/bình luận): khi thất bại tại dấu `"` mở chuỗi chưa đóng hoặc `/*` mở bình luận khối chưa đóng, bộ quét gom toàn bộ đoạn chuỗi lỗi tới cuối dòng `\n` (hoặc bình luận khối tới `EOF`) thành 1 lỗi duy nhất, tránh sinh hàng loạt token giả ở phần nội dung bên trong.

**Câu 14. Tại sao biểu thức chính quy cho bình luận nhiều dòng `/* ... */` trong `MiniLang` phải viết là `/\*([^*]|\*+[^*/])*\*+/` thay vì `/\*.*\*/`?**
> **Trả lời:** Vì bộ quét dùng nguyên tắc Maximal Munch và dấu `.` khớp cả `*` lẫn `/`, nên nếu viết `/\*.*\*/` thì dòng mã `/* c1 */ let x = 10; /* c2 */` sẽ bị gộp từ `/*` đầu tiên tới tận `*/` cuối cùng, làm mất câu lệnh `let x = 10;` ở giữa. Biểu thức `/\*([^*]|\*+[^*/])*\*+/` bắt buộc chuỗi dấu `*` bên trong không được đi liền trước `/`, nhờ đó dừng đúng tại cặp `*/` đóng đầu tiên.

**Câu 15. Tại sao bình luận nhiều dòng lồng nhau `/* ... /* ... */ ... */` không thể nhận diện bằng DFA? Chứng minh bằng Bổ đề Bơm (Chương 3.2).**
> **Trả lời:**
> - Giả sử ngôn ngữ bình luận lồng nhau cân bằng là chính quy. Đặt $a = \text{"/*"}$ và $b = \text{"*/"}$, xét giao với $(/\*)^*(\*/)^*$ rồi đồng cấu nghịch đảo ta suy ra $L = \{a^n b^n \mid n \ge 1\}$ cũng phải chính quy.
> - Gọi $p \ge 1$ là hằng số bơm trong Bổ đề Bơm (Chương 3.2). Chọn $w = a^p b^p \in L$ ($|w| = 2p \ge p$). Mọi cách tách $w = xyz$ với $|xy| \le p, |y| \ge 1$ đều có $y = a^k$ ($1 \le k \le p$).
> - Bơm với $i = 2$ được $xy^2z = a^{p+k} b^p \notin L$ do $p + k \neq p$ (mâu thuẫn). Vậy cấu trúc lồng nhau sâu tùy ý thuộc Ngôn ngữ phi ngữ cảnh (CFL — Chương 4) và cần ngăn xếp (PDA) hoặc biến đếm độ sâu.

---

### Nhóm C — Kiểm chứng Bất biến, JFLAP Round-Trip và Chi tiết Thực nghiệm

**Câu 16. Năm bất biến (invariants) được kiểm tra tự động trong `tests/test_suite.py` là gì?**
> **Trả lời:**
> 1. **Bảo toàn mã nguồn (Zero-Loss Reconstruction):** Hợp rời nhau của các token giữ lại, token bị skip và mảnh lỗi `LexicalError` ghép lại trùng khớp chuỗi nguồn ban đầu từng ký tự.
> 2. **Tương đương đa mô hình:** `Thompson ε-NFA`, `NFA khử ε`, `Subset DFA`, `Moore Min-DFA`, `Hopcroft Min-DFA`, `Direct DFA` và `GNFA RE` chấp nhận cùng một ngôn ngữ.
> 3. **Tính tối giản Myhill-Nerode:** Mọi cặp trạng thái khác nhau của Min-DFA đều có chuỗi hậu tố phân biệt.
> 4. **Độ phức tạp quét tuyến tính $O(n)$:** Các chuỗi bệnh lý 10.000 ký tự đều hoàn tất dưới 200 ms nhờ `failed_states`.
> 5. **Không dùng `import re`:** Phân tích cây AST Python của toàn bộ `lexer_engine/`, `app.py`, `cli.py` và mã sinh `codegen.py` xác nhận không có lệnh nạp module `re`.

**Câu 17. Kiểm chứng khứ hồi JFLAP (Round-Trip Verification) trong `jflap_export.py` hoạt động như thế nào?**
> **Trả lời:** Ngoài hàm xuất sang XML `.jff` (`export_nfa_to_jflap`, `export_dfa_to_jflap`), module còn có hàm đọc ngược (`import_jflap_to_nfa`, `import_jflap_to_dfa`) dựng lại đối tượng `NFA` / `DFA` từ file XML `.jff` rồi dùng `check_dfa_equivalence` đối chiếu tương đương với ô-tô-mát gốc trên cả 3 ngôn ngữ mẫu.

**Câu 18. Giải thích số lượng trạng thái trên ví dụ `(a|b)*abb` (Slide 38 Chương 3.1): Thompson 11, Khử $\varepsilon$ 6, Subset DFA 5, Min-DFA 4?**
> **Trả lời:**
> - **Thompson $\varepsilon$-NFA (11 trạng thái `q0..q10`):** `a` (2 TT) và `b` (2 TT) ghép hợp `a|b` thêm 2 đỉnh đầu/cuối thành 6 TT; bao đóng `(a|b)*` thêm 2 đỉnh thành 8 TT; nối tiếp `.a.b.b` gộp đỉnh nối nên thêm 3 đỉnh thành $8 + 3 = 11$ trạng thái.
> - **NFA khử $\varepsilon$ (6 trạng thái):** Sau khi tính $\varepsilon$-closure và tạo cung trực tiếp chỉ còn 6 đỉnh có đường đi tới từ `q0`.
> - **Subset DFA (5 trạng thái `D0..D4`):** Gồm `D0` (khởi đầu), `D1` (đọc `a`), `D2` (đọc `b`), `D3` (đọc `ab`), `D4` (đọc `abb` — kết thúc).
> - **Min-DFA (4 trạng thái `M0..M3`):** Hai trạng thái `D0` và `D2` cùng không kết thúc và có cùng đích chuyển tiếp trên `a`, `b` nên gộp thành `M0`, còn 4 trạng thái.

**Câu 19. Giải thích ví dụ `(a|ba)(a|b)*ba` (Slide 48–56 Chương 3.1): 8 nút lá và bảng `followpos`?**
> **Trả lời:** Sau khi nối `#` thành `(a|ba)(a|b)*ba#`, đánh số 8 lá: `1:a, 2:b, 3:a, 4:a, 5:b, 6:b, 7:a, 8:#`.
> - Tiền tố `(a|ba)` có `lastpos = {1, 3}` nối với `(a|b)*ba#` có `firstpos = {4, 5, 6}` -> `followpos(1) = followpos(3) = {4, 5, 6}`; lá `2:b` nối `3:a` -> `followpos(2) = {3}`.
> - Vòng lặp `(a|b)*` cho `followpos(4) = followpos(5) = {4, 5, 6}`.
> - Hậu tố `ba#` cho `followpos(6) = {7}`, `followpos(7) = {8}`, `followpos(8) = ∅`.
> - Từ `firstpos(root) = {1, 2}` sinh ra 5 trạng thái Direct DFA khớp Slide 55–57.

**Câu 20. Tại sao trên `MiniLang`, `Combined Direct DFA` có 79 trạng thái trong khi `Minimized DFA` có 78 trạng thái?**
> **Trả lời:** Phương pháp trực tiếp `followpos` tạo DFA rất gọn (79 trạng thái so với 86 của Subset DFA), nhưng theo lý thuyết (Dragon Book Mục 3.9.5), Direct DFA chưa chắc tối giản trong mọi trường hợp vì hai tập vị trí lá khác nhau vẫn có thể có cùng hành vi tương lai (trên `MiniLang` xuất hiện ở quy tắc `BLOCK_COMMENT`). Khi tối thiểu hóa bằng Moore hoặc Hopcroft, cặp trạng thái tương đương đó được gộp lại còn đúng 78 trạng thái.

**Câu 21. Nếu biểu thức chính quy khớp được chuỗi rỗng $\varepsilon$ (ví dụ `a*`), bộ quét tránh lặp vô hạn bằng cách nào?**
> **Trả lời:** Khi biên dịch, `ast.is_nullable()` phát cảnh báo cho các quy tắc khớp chuỗi rỗng. Khi quét trong `scanner.py`, một token chỉ được phát ra nếu `last_accept_pos > pos` (độ dài lexeme $\ge 1$); nếu không tiến thêm được ký tự nào thì chuyển sang bước xử lý lỗi và tăng `pos += 1`, đảm bảo con trỏ luôn tiến về phía trước.

**Câu 22. Bộ quét tính tọa độ `(line, col)` trên các kiểu xuống dòng `\n`, `\r\n` (Windows CRLF) và `\r` như thế nào?**
> **Trả lời:** Hàm `_advance_position()` trong `scanner.py` tăng `line += 1, col = 1` khi gặp `\r`, và khi gặp `\n` đi ngay sau `\r` (cặp `\r\n`) thì chỉ giữ `col = 1` mà không tăng `line` lần thứ hai; nếu `\n` đứng độc lập thì tăng `line += 1, col = 1`.

**Câu 23. Ba chuỗi `"1.5e+2"`, `"1.5e"` và `"1.5e+"` được quét khác nhau như thế nào trong `MiniLang`?**
> **Trả lời:** Với `FLOAT_LIT = [0-9]+\.[0-9]+([eE][+-]?[0-9]+)?`:
> - `"1.5e+2"` khớp trọn vẹn 1 token `FLOAT_LIT("1.5e+2")`.
> - `"1.5e"` đọc qua `1.5` (lưu `last_accept_pos = 3`), đọc thêm `e` rồi gặp DEAD nên quay lui 1 ký tự xuất `FLOAT_LIT("1.5")`, sau đó quét `e` thành `IDENTIFIER("e")`.
> - `"1.5e+"` đọc `1.5`, thử tiếp `e+` rồi gặp DEAD nên quay lui 2 ký tự xuất `FLOAT_LIT("1.5")`, tiếp theo xuất `IDENTIFIER("e")` và `OP_PLUS("+")`.

**Câu 24. Tại sao chuỗi `"123abc"` được bộ quét tách thành `INT_LIT("123")` và `IDENTIFIER("abc")` thay vì báo lỗi từ vựng?**
> **Trả lời:** Theo chuẩn phân tầng của trình biên dịch (C, Java, Python, Dragon Book Chương 3), bộ quét từ vựng áp dụng Maximal Munch tách tiền tố hợp lệ dài nhất `"123"` (`INT_LIT`) rồi tới `"abc"` (`IDENTIFIER`). Việc hai token này đứng cạnh nhau không có toán tử sẽ bị bắt lỗi ở pha Phân tích cú pháp (Parser). Nếu muốn bắt ngay ở tầng từ vựng, có thể thêm quy tắc bẫy lỗi `[0-9]+[a-zA-Z_]+` phía trên `INT_LIT` trong Tab 4.

**Câu 25. Chuỗi `"0.0.0"` được tách thành những token nào?**
> **Trả lời:** Tiền tố dài nhất `"0.0"` khớp `FLOAT_LIT("0.0")`; tiếp theo dấu `.` đứng riêng không thuộc quy tắc nào nên báo `LEXICAL_ERROR(".")`, sau đó ký tự `"0"` cuối được quét thành `INT_LIT("0")`.

**Câu 26. Tại sao phép nối `ConcatNode(left, right)` trong `thompson.py` gộp trực tiếp đỉnh cuối của `left` với đỉnh đầu của `right`?**
> **Trả lời:** Theo cấu trúc Thompson chuẩn (Dragon Book Hình 3.41), mỗi mảnh $\varepsilon$-NFA con luôn có đỉnh đầu bậc vào bằng 0 và đỉnh cuối bậc ra bằng 0. Việc gộp hai đỉnh này không tạo chu trình phụ, giảm bớt trạng thái/cung $\varepsilon$ dư thừa, và cho ra đúng 11 trạng thái (`q0..q10`) trên ví dụ `(a|b)*abb` khớp với Slide 38 bài giảng.

**Câu 27. Hàm `compare_regex_equivalence(R1, R2)` trên Tab 3 kiểm tra hai biểu thức chính quy tương đương bằng cách nào?**
> **Trả lời:** Biên dịch $R_1, R_2$ sang Min-DFA $D_1, D_2$ trên bảng chữ cái chung rồi duyệt BFS trên ô-tô-mát tích $D_1 \times D_2$. Nếu gặp cặp trạng thái lệch tính chất kết thúc thì truy vết cây BFS trả về chuỗi phản ví dụ ngắn nhất $w \in L(R_1) \triangle L(R_2)$; nếu duyệt hết không có mâu thuẫn thì kết luận $L(R_1) = L(R_2)$.

**Câu 28. Tại sao số trạng thái Subset DFA của `MiniLang` (86), `CalcLang` (24), `MiniSQL` (64) nhỏ hơn số trạng thái $\varepsilon$-NFA ban đầu (170, 57, 128)?**
> **Trả lời:** Hiện tượng bùng nổ $2^{|Q_N|}$ chỉ xảy ra trên các mẫu biểu thức nhập nhằng vị trí như $(a\mid b)^*a(a\mid b)^{k-1}$. Các quy tắc token của ngôn ngữ lập trình thực tế phân nhánh gần giống cây tiền tố theo từng nhóm ký tự (chữ cái, chữ số, toán tử), nên phép $\varepsilon$-closure gom nhiều đỉnh trung gian của Thompson lại thành ít tập con đạt tới được hơn.

**Câu 29. Nếu người dùng nhập biểu thức gây bùng nổ trạng thái hoặc nhân bản cây cú pháp lồng nhau `(((a{64}){64}){64})`, hệ thống bảo vệ như thế nào?**
> **Trả lời:** Hệ thống có 3 mức giới hạn an toàn:
> 1. Giới hạn biên lặp đơn lẻ `MAX_QUANTIFIER_BOUND = 64`.
> 2. Giới hạn tổng kích thước cây cú pháp `MAX_AST_NODES = 4096` trong `regex_parser.py` (ước lượng trước số nút trong $O(1)$ để từ chối ngay `(((a{64}){64}){64})` trước khi cấp phát bộ nhớ).
> 3. Ngưỡng trạng thái `max_states = 5000` trong `subset_construction.py`.

**Câu 30. Làm sao đảm bảo toàn bộ mã lõi và mã sinh ra không sử dụng `import re`?**
> **Trả lời:** Hai bài kiểm thử `test_zero_re_in_engine()` và `test_v2_5_standalone_table_driven_lexer_generator_differential()` trong `tests/test_suite.py` dùng module `ast` của Python phân tích cú pháp toàn bộ file `.py` trong `lexer_engine/`, `app.py`, `cli.py` và file độc lập do `codegen.py` sinh ra để kiểm tra mọi câu lệnh `import`, `from ... import`, `__import__` và `importlib`.

**Câu 31. Tại sao tỷ lệ giảm trạng thái khi tối thiểu hóa DFA của `MiniSQL` (`-18.8%`, từ 64 xuống 52) cao hơn `MiniLang` (`-9.3%`, từ 86 xuống 78)?**
> **Trả lời:** Các từ khóa trong `MiniSQL` khai báo song song hai nhánh HOA và thường (`SELECT|select`, `FROM|from`, ...). Subset DFA tách riêng đường đi HOA và thường, nhưng phần hậu tố cuối hoặc nhánh rẽ sang `IDENT` có hành vi chuyển tiếp giống hệt nhau nên được Moore/Hopcroft gộp lại nhiều hơn. Trong khi đó `MiniLang` có 39 nhãn token kết thúc khác nhau ngay từ $\Pi_0$ nên số trạng thái có thể gộp ít hơn.

**Câu 32. Đồ án kết nối với Chương 4 (CFG) và Chương 5 (PDA) của môn học như thế nào nếu phát triển tiếp thành trình biên dịch?**
> **Trả lời:** Dãy đối tượng `Token` đầu ra của `LexicalAnalyzer.scan()` (hoặc `MiniLangLexer` độc lập) đóng vai trò là chuỗi ký hiệu kết thúc (*terminals*) cho Văn phạm phi ngữ cảnh $G = (V, \Sigma_{\text{tok}}, R, S)$ ở Chương 4, được đưa trực tiếp vào bộ phân tích cú pháp `LL(1)` hoặc `LR(1)` (cài đặt PDA đơn định ở Chương 5) để dựng cây cú pháp chương trình.

---

### Nhóm D — Khử trạng thái GNFA, Đại số Boole, Ma trận Giao nhau và Sinh mã Lexer

**Câu 33. Thuật toán GNFA State Elimination (`dfa_to_regex` trong `gnfa.py`) chuyển DFA ngược về Biểu thức chính quy như thế nào?**
> **Trả lời:** Theo chứng minh chiều ngược của Định lý Kleene (Hopcroft, Motwani & Ullman, Mục 3.2.1):
> 1. Lọc bỏ các trạng thái không đạt tới được hoặc không có đường đi tới $F$; thêm đỉnh đầu mới $q_{\text{start}} \xrightarrow{\varepsilon} D_0$ và đỉnh cuối mới $q_{\text{accept}}$ nhận cung $\varepsilon$ từ mọi $f \in F$.
> 2. Ở mỗi bước, chọn đỉnh trung gian $q_{\text{rip}}$ có tích bậc vào nhân bậc ra $\text{in\_deg}(q) \times \text{out\_deg}(q)$ nhỏ nhất để giữ biểu thức kết quả gọn.
> 3. Cập nhật nhãn biểu thức cho mọi cặp $(q_i, q_j)$ đi qua $q_{\text{rip}}$:
>    $$R'(q_i, q_j) = R(q_i, q_j) \;\cup\; R(q_i, q_{\text{rip}}) \cdot \big(R(q_{\text{rip}}, q_{\text{rip}})\big)^* \cdot R(q_{\text{rip}}, q_j)$$
>    kèm các phép rút gọn đại số cơ bản ($\varnothing \cdot X = \varnothing$, $\varepsilon \cdot X = X$, $\varnothing^* = \varepsilon$).
> 4. Sau khi khử hết đỉnh trung gian, biên dịch lại $R(q_{\text{start}}, q_{\text{accept}})$ sang DFA để đối chiếu tương đương với DFA ban đầu.

**Câu 34. Vì sao việc bao phủ đủ 128 mã ASCII `0x00..0x7F` (gồm cả `\0`, `\f`, `\v`, `\x7f`) lại cần thiết cho tính chất đối hợp $\sim(\sim A) = A$?**
> **Trả lời:** Phép lấy phần bù $\sim A = \Sigma \setminus A$ chỉ thỏa mãn $\sim(\sim A) = A$ khi tập vũ trụ $\Sigma$ chứa đầy đủ mọi ký tự có thể xuất hiện trong $A$. Nếu $\Sigma$ thiếu `\f` hay `\v`, thì với $A = \{\text{'\textbackslash f'}, \text{'\textbackslash v'}\}$, lần lấy bù thứ nhất cho $\Sigma \setminus A = \Sigma$, và lần thứ hai cho $\Sigma \setminus \Sigma = \varnothing \neq A$. Việc định nghĩa `ASCII_SIGMA` đủ 128 mã `0x00..0x7F` kết hợp $\Sigma(U)$ đảm bảo $\sim(\sim A) = A$ ở cả mức tập ký tự lẫn mức `complement_dfa`.

**Câu 35. Tại sao quy tắc `STRING_LIT` trong `MiniLang` cần viết `"([^"\\\n\r]|\\.)*"` (loại trừ cả `\r` và `\n`)?**
> **Trả lời:** Trên tệp văn bản kiểu Windows CRLF (`\r\n`), nếu chỉ loại trừ `\n` mà không loại trừ `\r`, DFA sẽ đọc luôn ký tự `\r` ở cuối dòng vào nhánh chuỗi chưa đóng trước khi dừng ở `\n`, làm lệch ranh giới thu hồi lỗi của chế độ `smart_sync` và cho phép ký tự `\r` trần nằm trong chuỗi đơn dòng. Loại trừ cả `\r` và `\n` giúp tách riêng lớp ký tự của chúng (44 lớp tương đương trên `MiniLang`) và giữ chính xác ranh giới dòng.

**Câu 36. Ma trận giao nhau tĩnh $L(R_i) \cap L(R_j)$ trên Tab 2 khác gì với kiểm tra `Shadowed Rules`?**
> **Trả lời:** Kiểm tra `Shadowed Rules` chỉ báo khi một quy tắc bị che khuất toàn bộ ($L(R_j) \subseteq \bigcup_{i < j} L(R_i)$). Trong khi đó `analyze_token_intersections(specs)` xét từng cặp $D_i \times D_j$ ($i < j$) bằng BFS để kiểm tra cả $L(D_i) \cap L(D_j)$, $L(D_i) \setminus L(D_j)$ và $L(D_j) \setminus L(D_i)$, qua đó phân loại đủ các quan hệ ($\varnothing$, $\subset$, $\equiv$, $\supset$, giao một phần $\cap$) và tìm chuỗi chứng nhân ngắn nhất $w \in L(R_i) \cap L(R_j)$. Trên `MiniLang`, trong 741 cặp có 732 cặp rời nhau và 9 cặp từ khóa nằm trong `IDENTIFIER`.

**Câu 37. Bộ sinh mã Lexer độc lập (`codegen.py` / `cli.py codegen`) tổ chức dữ liệu như thế nào?**
> **Trả lời:** Tương tự cách công cụ `flex` sinh bảng chuyển trạng thái tĩnh trong C, `codegen.py` xuất `Minimized DFA` ra một tệp `.py` độc lập (~527 dòng cho `MiniLang`, không phụ thuộc `lexer_engine/`, không dùng `import re`) gồm 4 cấu trúc hằng: `ASCII_CLASS_MAP` (mảng 128 phần tử), `UNICODE_CLASS_MAP` kèm `NON_ASCII_CLASS`, ma trận hai chiều `TRANSITIONS` kích thước `|Q_min| × |Σ/≡|` và bảng `ACCEPT_TABLE`, đi cùng vòng lặp quét Maximal Munch $O(n)$ có `failed_states`. Bộ kiểm thử vi sai xác nhận đầu ra của tệp sinh ra khớp với `LexicalAnalyzer` gốc trên từng token và từng lỗi từ vựng.

**Câu 38. Tại sao hằng nội bộ `NON_ASCII` dùng điểm mã `"\ufdd0"` thay vì `"\x80"`?**
> **Trả lời:** Điểm mã `U+0080` (`"\x80"`) là ký tự điều khiển có thực trong khối Latin-1 Supplement nên có thể xuất hiện trong dữ liệu đầu vào hoặc qua chuỗi escape `\x80` / `\u0080`, dễ gây trùng ký hiệu với hằng đại diện. Ngược lại, dải `U+FDD0..U+FDEF` được chuẩn Unicode (Section 23.7) quy định cố định là *noncharacters* dùng nội bộ trong chương trình, nhờ đó tránh xung đột với các ký tự văn bản thông thường.
