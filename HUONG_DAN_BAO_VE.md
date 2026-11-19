# CẨM NANG THUYẾT TRÌNH, DEMO & BẢO VỆ ĐẠT 10/10 — ĐỀ TÀI T13

> Tài liệu ôn tập nội bộ cho nhóm trước buổi bảo vệ (15 phút: **8–10 phút trình bày + demo**, **5–7 phút hỏi đáp**).  
> Mục tiêu: Mọi thành viên hiểu sâu từng thuật toán, giải thích trôi chảy phần code phụ trách và trả lời xuất sắc câu hỏi phản biện của Giảng viên (cô Hồ Thị Thanh Tuyến).

---

## PHẦN 1: KỊCH BẢN TRÌNH BÀY & DEMO 9.5 PHÚT (CHUẨN RUBRIC)

*(Điều chỉnh linh hoạt theo 4 hoặc 5 thành viên)*

| Thời lượng | Thành viên | Nội dung trình bày / Thao tác Demo | Điểm ăn điểm tối đa |
|---|---|---|---|
| **0:00 – 1:30** | **TV 1** (Trưởng nhóm & Lý thuyết) | Giới thiệu bài toán Lexical Analysis trong trình biên dịch; liên hệ môn Ngôn ngữ hình thức (Định lý Kleene: `RE ≡ ε-NFA ≡ DFA`); mô hình hình thức 5-bộ & giả định bảng chữ cái $\Sigma$ (98 ký tự ASCII). | Nêu rõ **không dùng `import re`** — toàn bộ cốt lõi 100% cài đặt từ lý thuyết Automata. |
| **1:30 – 3:30** | **TV 2** (Regex Parser & Thompson / Direct DFA) | Trình bày pipeline biến đổi `RE → AST → Thompson ε-NFA` và **mở Tab 3 Web Studio**: chạy trực tiếp 2 ví dụ trên slide Chương 3.1 của cô là `(a|b)*abb` (11 trạng thái NFA) và `(a|ba)(a|b)*ba` (Cây phân tích `r#`, `nullable`, `FP`, `LP`, bảng `followpos` y hệt Slide 52–54!). | Cô thấy ví dụ slide bài giảng chạy sống động ngay trên đồ thị SVG → ấn tượng cực mạnh! |
| **3:30 – 5:30** | **TV 3** (Subset Construction, Tối thiểu hóa & Equivalence) | Giải thích mở rộng **Multi-token Combined ε-NFA → Subset DFA** (giải quyết xung đột ưu tiên `KW_IF` vs `IDENTIFIER`) + **Tối thiểu hóa Multi-token DFA** (khởi tạo $\Pi_0$ tách riêng từng loại token!) + tối ưu **Alphabet Partitioning**. **Mở Tab 2 (chọn CalcLang)** để chiếu toàn bộ đồ thị Combined DFA 20 trạng thái, bảng chuyển, các bước $\Pi_0 \to \Pi_n$ và chứng minh tương đương bằng **Product Automaton**. | Nhấn mạnh khác biệt cốt lõi giữa tối giản 1-token ($\Pi_0 = \{Q\setminus F, F\}$) và tối giản đa-token ($\Pi_0 = \{Q\setminus F, F_{t_1}, \dots, F_{t_k}\}$). |
| **5:30 – 8:00** | **TV 4** (Scanner Maximal Munch & Live Demo) | **Mở Tab 1 (chọn MiniLang)**:<br>1. Quét mẫu **Hợp lệ** → chỉ bảng token & tô màu trực tiếp.<br>2. Chuyển sang mẫu **Biên (Maximal Munch)**: bấm vào token `ifx` hoặc `1.5` trong `1.5e` / `3.` → bấm nút **▶ Chạy** trên bộ mô phỏng từng bước để chiếu hoạt ảnh đọc ký tự, gặp `DEAD`, và **quay lui (backtrack)**!<br>3. Chuyển sang mẫu **Lỗi & Phục hồi** → chỉ 4 lỗi có tọa độ `(dòng:cột)` và chương trình vẫn quét tiếp được dòng cuối (`let okAfterError = 42;`).<br>4. **Mở Tab 4**: bấm `+ Thêm nhanh HEX_LIT` → `Biên Dịch Lại` → quay lại Tab 1 gõ `let c = 0xFF;` và quét ra `HEX_LIT` ngay lập tức! | Chứng minh chương trình là **Lexical Analyzer Generator tổng quát**, không hề hardcode từ khóa hay token! |
| **8:00 – 9:30** | **TV 5** (hoặc TV 1) (Kiểm thử, Đánh giá & Kết luận) | **Mở Tab 5**: chạy 29/29 test case PASS (100%) + bảng Benchmark 3 ngôn ngữ (`MiniLang`, `CalcLang`, `MiniSQL`) + giới thiệu file `.jff` xuất sang JFLAP đối chứng; nêu trung thực hạn chế (panic-mode 1 ký tự với chuỗi chưa đóng, chưa hỗ trợ bảng chữ cái Unicode đầy đủ, trạng thái bùng nổ mũ $2^n$ ở RE bệnh lý) và hướng phát triển. | Đạt trọn vẹn 100% tiêu chí **Kiểm thử & đánh giá (10%)**! |

---

## PHẦN 2: BẢN ĐỒ CODE ĐỂ TỪNG THÀNH VIÊN TỰ TIN GIẢI THÍCH

- **Parse RE không dùng `re`**: `lexer_engine/regex_parser.py` — lớp `RegexParser` dùng đệ quy đoán nhận trước (Recursive Descent) với 4 mức ưu tiên: `_parse_expr` (`|`) → `_parse_concat` (nối kết ẩn) → `_parse_repeat` (`*`, `+`, `?`) → `_parse_atom` (`(...)`, `[...]`, `.`, `\escape`, ký tự đơn).
- **Thompson ε-NFA & Hợp nhất đa-token**: `lexer_engine/thompson.py` — `_ThompsonBuilder.build_node()` đảm bảo bất biến Thompson (`in-degree(start)=0`, `out-degree(end)=0`) nên phép nối kết ghép trực tiếp `l_e` với `r_s` không sinh chu trình giả. `build_combined_nfa()` tạo trạng thái đầu `q0 = 0` nối ε tới từng NFA con và gắn `AcceptInfo(token_name, priority, skip)` lên đỉnh kết thúc.
- **Subset Construction + Alphabet Partitioning**: `lexer_engine/subset_construction.py` — `compute_alphabet_partition()` (trong `models.py`) phân hoạch 98 ký tự ASCII thành các lớp tương đương nhỏ nhất (VD: MiniLang còn 43 lớp). `_resolve_accept()` chọn token có `priority` nhỏ nhất (ưu tiên cao nhất) khi tập con NFA chứa nhiều trạng thái kết thúc.
- **Direct RE → DFA**: `lexer_engine/direct_dfa.py` — bổ sung nút kết thúc `#` (`r·#`), đánh số lá `1..n`, đệ quy hậu tố tính `nullable`, `firstpos`, `lastpos`, cập nhật `followpos` tại các nút `·`, `*`, `+`, rồi BFS tạo trạng thái DFA từ `firstpos(root)`.
- **Tối thiểu hóa Multi-token DFA**: `lexer_engine/dfa_minimizer.py` — loại trạng thái không đạt tới (BFS), thêm trạng thái chết ảo `DEAD = -1` để hàm chuyển đầy đủ, khởi tạo $\Pi_0$ tách riêng `Q \ F` và từng loại `token_name`, lặp chia nhóm theo chữ ký vector chuyển tiếp cho đến điểm bất động, cuối cùng loại khối `DEAD` (khớp Slide 58 Bước 5).
- **Bộ quét Maximal Munch**: `lexer_engine/scanner.py` — `scan_source()` giữ cặp `last_accept = (cursor, state, accept_info)`. Khi `dfa.step(cur, ch)` trả về `None` (DEAD) hoặc hết chuỗi, quay lui về `last_accept[0]`. Nếu `last_accept is None`, ghi nhận `LexicalError` và tiến `pos += 1` (Panic-mode recovery).
- **Chứng minh tương đương**: `lexer_engine/verifier.py` — `check_dfa_equivalence()` chạy BFS trên Product Automaton $A \times B$ với bảng chữ cái phân hoạch chung; nếu gặp cặp $(q_A, q_B)$ khác nhãn chấp nhận thì truy vết ngược cha để trả về **phản ví dụ ngắn nhất**.

---

## PHẦN 3: 20 CÂU HỎI BẢO VỆ CÁ NHÂN (Q&A) THƯỜNG GẶP NHẤT

### Nhóm A — Kiến thức lý thuyết Automata & Ngôn ngữ hình thức
1. **Tại sao phân tích từ vựng lại dùng Ngôn ngữ chính quy / Finite Automata mà không dùng CFG / PDA?**
   > Vì cấu trúc từ vựng (từ khóa, định danh, hằng số, toán tử) không đòi hỏi lồng ngoặc đệ quy không giới hạn (như $a^n b^n$). Ngôn ngữ chính quy đủ mạnh để mô tả mọi quy tắc từ vựng, và DFA quét đầu vào trong thời gian tuyến tính $O(|w|)$ với bộ nhớ hằng số $O(1)$ (mỗi ký tự chỉ tra bảng 1 lần).
2. **Mối liên hệ giữa RE, ε-NFA và DFA là gì?**
   > Theo Định lý Kleene, ba mô hình có sức mạnh biểu diễn tương đương (cùng mô tả lớp Ngôn ngữ chính quy). RE dễ cho con người viết đặc tả token; ε-NFA dễ xây dựng máy móc từ RE bằng cấu trúc Thompson; DFA loại bỏ tính không đơn định để thực thi cực nhanh $O(1)$ mỗi bước chuyển khi quét mã nguồn.
3. **Tại sao khi hợp nhất nhiều token lại có thể xảy ra xung đột ở trạng thái kết thúc của DFA? Nhóm giải quyết ra sao?**
   > Ví dụ chuỗi `"if"` vừa khớp `KW_IF` (`if`) vừa khớp `IDENTIFIER` (`[a-zA-Z_][a-zA-Z0-9_]*`). Khi chạy Subset Construction, tập con NFA của trạng thái nhận `"if"` chứa đồng thời trạng thái kết thúc của cả hai NFA con. Ta giải quyết bằng **Quy tắc ưu tiên (Rule Priority)**: chọn quy tắc xuất hiện trước (priority nhỏ hơn), tức là `KW_IF` thắng `IDENTIFIER`.
4. **Điểm khác biệt quan trọng nhất giữa tối thiểu hóa DFA đơn ngôn ngữ (trong bài giảng) và tối thiểu hóa Multi-token DFA của Lexical Analyzer là gì?**
   > Trong DFA đơn ngôn ngữ, phân hoạch khởi đầu chỉ có 2 nhóm $\Pi_0 = \{Q \setminus F, F\}$. Nhưng trong Lexical Analyzer, hai trạng thái kết thúc nhận hai loại token khác nhau (VD: `KW_IF` và `IDENTIFIER`) **không tương đương về đầu ra** nên tuyệt đối không được gộp chung. Vì vậy ta khởi tạo $\Pi_0 = \{Q \setminus F\} \cup \{F_{T_1}, F_{T_2}, \dots, F_{T_m}\}$, mỗi loại token một nhóm riêng (mở rộng Định lý Myhill–Nerode cho máy đầu ra Moore).
5. **Tại sao trước khi tối thiểu hóa DFA ta cần bổ sung trạng thái chết ảo `DEAD` (làm đầy đủ hàm chuyển)?**
   > Vì nếu bỏ qua các chuyển tiếp không xác định, hai trạng thái $s, t$ cùng nhóm nhưng $s$ có chuyển tiếp trên ký tự `a` sang trạng thái khác trong khi $t$ không có chuyển tiếp trên `a` (đi vào `DEAD`) phải bị tách riêng. Bổ sung trạng thái chết ảo `DEAD` làm hàm chuyển toàn phần giúp phép so sánh chữ ký phân hoạch chính xác 100%, sau đó ở bước cuối ta loại bỏ khối `DEAD` đi (đúng Bước 5 Giải thuật 3.6).
6. **Chứng minh tính tương đương trước và sau tối thiểu hóa hoạt động như thế nào?**
   > Dùng **Product Automaton** $A \times B$: duyệt BFS các cặp trạng thái đạt tới được từ $(q_{0,A}, q_{0,B})$ trên các lớp ký tự chung. Nếu tồn tại bất kỳ cặp $(q_A, q_B)$ nào mà nhãn token chấp nhận của $A$ khác $B$, BFS lập tức truy ngược ra **chuỗi phản ví dụ ngắn nhất**. Nếu duyệt hết không có sai khác → chứng minh toán học $A$ và $B$ cho đầu ra giống hệt nhau trên **vô hạn chuỗi** $w \in \Sigma^*$ (mạnh hơn kiểm thử bằng mẫu hữu hạn!).

### Nhóm B — Thuật toán cài đặt & Xử lý biên
7. **Maximal Munch (Longest Match) là gì? Cho ví dụ cụ thể cần quay lui (backtracking)?**
   > Maximal Munch luôn chọn tiền tố dài nhất có thể tạo thành một token hợp lệ. Ví dụ:
   > - `ifx` → đọc `i`, `f` (chấp nhận `KW_IF`), nhưng vẫn đọc tiếp `x` (chấp nhận `IDENTIFIER`) → xuất `IDENTIFIER("ifx")`.
   > - **Trường hợp phải quay lui**: `1.5e` trong `MiniLang`! DFA đọc `1` (`INT`), `.` (trung gian), `5` (`FLOAT`, lưu `last_accept = 3`), đọc tiếp `e` (trung gian vì mong chờ số mũ như `1.5e-2`), gặp hết chuỗi/khoảng trắng → DEAD! Lúc đó scanner phải **quay lui 1 ký tự** về `last_accept = 3`, xuất `FLOAT("1.5")`, rồi vòng lặp mới quét `e` thành `IDENTIFIER("e")`.
8. **Nếu người dùng định nghĩa một quy tắc token có thể khớp chuỗi rỗng $\varepsilon$ (như `a*`), điều gì xảy ra?**
   > Nếu bộ quét chấp nhận độ dài lexeme = 0, con trỏ `pos` sẽ không tăng và bộ quét rơi vào **vòng lặp vô hạn**! Chương trình xử lý bằng 2 lớp bảo vệ: (1) dùng `ast.is_nullable()` phát hiện & cảnh báo ngay lúc biên dịch; (2) điều kiện xuất token trong `scanner.py` bắt buộc `last_accept[0] > pos` (độ dài ≥ 1), nếu không sẽ kích hoạt báo lỗi và tiến 1 ký tự.
9. **Alphabet Partitioning (Lớp tương đương ký tự) là gì và tại sao nó không làm sai kết quả?**
   > Trong bảng chữ cái 98 ký tự ASCII, nhiều ký tự có hành vi giống hệt nhau trên mọi quy tắc (VD: các chữ số `'0'..'9'` đều thuộc `[0-9]` và không xuất hiện lẻ trong từ khóa nào). Ta phân hoạch $\Sigma$ thành các tập con rời nhau nhỏ nhất (min-terms) sao cho mọi ký tự trong cùng một lớp có tập chuyển tiếp NFA giống hệt nhau. Nhờ vậy MiniLang giảm từ 98 cột xuống 43 cột, biên dịch nhanh dưới 10 ms mà **chính xác toán học 100%**.
10. **So sánh phương pháp Thompson → Subset Construction và Direct RE → DFA (`r#`, `followpos`)?**
    > - Thompson → Subset dễ mở rộng cho **nhiều token cùng lúc** (chỉ cần thêm `q0` với ε-cạnh nối tất cả NFA con) và cấu trúc đơn giản.
    > - Direct RE → DFA bỏ qua bước NFA trung gian và thường tạo ra DFA có số trạng thái gần tối giản ngay (VD: với `(a|ba)(a|b)*ba`, Subset tạo 7 trạng thái còn Direct tạo ngay 5 trạng thái tối giản!). Tuy nhiên với đa-token cần nhiều ký hiệu kết thúc `#_1, #_2, ..., #_k`.
11. **Độ phức tạp thời gian & không gian của từng giai đoạn?**
    > - Parse RE + Thompson NFA: $O(|R|)$ thời gian và $O(|R|)$ trạng thái (mỗi toán tử thêm tối đa 2 trạng thái).
    > - Subset Construction: Trường hợp xấu nhất $O(2^{|Q_N|} \cdot |\mathcal{E}|)$ (bùng nổ lũy thừa lý thuyết), nhưng với đặc tả token thực tế chỉ tuyến tính $O(|Q_D| \cdot |\mathcal{E}|)$ (MiniLang: 153 NFA → 81 DFA!).
    > - Tối thiểu hóa (Partition Refinement): $O(|Q_D|^2 \cdot |\mathcal{E}|)$ (với số trạng thái vài chục–vài trăm chạy < 4 ms).
    > - Quét văn bản độ dài $n$: Trường hợp thông thường $O(n)$ (mỗi ký tự tra bảng `dict` $O(1)$); trường hợp xấu nhất khi phải quay lui liên tục (như `"aaaa...` chưa đóng lặp lại) có thể lên $O(n^2)$ nếu dùng panic-mode 1 ký tự — đây cũng là hạn chế nhóm đã phân tích rõ!
12. **Tại sao trong `scanner.py` khi gặp chuỗi chưa đóng `"chuoi chua dong;` lại sinh thêm các token `chuoi`, `chua`, `dong` sau lỗi?**
    > Vì hiện tại nhóm cài đặt phục hồi lỗi **Panic-mode đơn giản (tiến 1 ký tự)** khi gặp lỗi từ vựng tại dấu `"`. Sau khi bỏ qua `"`, phần còn lại `chuoi chua dong;` hợp lệ như các `IDENTIFIER`. Hướng cải tiến (như Flex/GCC): thêm quy tắc bắt lỗi chuyên biệt `UNTERMINATED_STRING = "[^"\n]*` đặt ở mức ưu tiên thấp hơn `STRING_LIT` để nuốt trọn cả chuỗi lỗi và báo 1 thông báo gọn gàng duy nhất!
13. **Trong Regex của nhóm, phép hợp dùng ký hiệu `|` thay vì `+` như trên slide lý thuyết, vì sao?**
    > Trong lý thuyết thuần túy (Slide 23), `r + s` là phép hợp, nhưng trong đặc tả từ vựng thực tế (POSIX/Flex) ký hiệu `+` là **bao đóng dương** ($r^+ = r r^*$, rất hay dùng như `[0-9]+`) và `|` là phép hợp (tuyển). Chương trình hỗ trợ chuẩn thực tế (`|`, `*`, `+`, `?`, `[a-z]`, `[^...]`, `\escape`, `ε`) và đã giải thích rõ quy ước ký hiệu trong báo cáo.
14. **Làm sao chứng minh chương trình KHÔNG gian lận bằng cách gọi thư viện `re` của Python?**
    > Có thể kiểm tra trực tiếp thư mục `lexer_engine/` (không một file nào `import re`), thậm chí có hẳn test tự động `test_zero_re_in_engine()` trong `tests/test_suite.py` quét mã nguồn mọi file trong `lexer_engine/` để khẳng định! Thư viện `re` chỉ được dùng duy nhất làm **đối chứng độc lập (oracle)** trong file kiểm thử `tests/test_suite.py`.
15. **JFLAP đóng vai trò gì trong dự án này?**
    > Đúng yêu cầu đề bài: nhóm tự cài đặt 100% thuật toán cốt lõi, còn JFLAP dùng làm công cụ **đối chứng độc lập**. Nhóm còn viết luôn module `jflap_export.py` để xuất thẳng NFA/DFA ra file `.jff` mở trực tiếp trên JFLAP 7.x kiểm tra chéo!
16. **Thứ tự các quy tắc trong Token Spec có quan trọng không? Điều gì xảy ra nếu đặt `IDENTIFIER` lên trên `KW_IF`?**
    > Cực kỳ quan trọng! Nếu đặt `IDENTIFIER` có ưu tiên cao hơn `KW_IF`, thì trạng thái DFA nhận chuỗi `"if"` sẽ chọn `IDENTIFIER` thay vì `KW_IF`, khiến mọi từ khóa bị nuốt thành định danh (trạng thái `KW_IF` thậm chí bị che khuất hoàn toàn — *shadowed rule*). Ta có thể minh họa trực tiếp ngay trên **Tab 4 (Live RE Editor)** bằng cách bấm mũi tên đổi thứ tự!
17. **Phép nối kết trong Thompson của nhóm gộp trạng thái kết thúc của $N(r)$ với trạng thái đầu của $N(s)$ (không thêm cạnh ε nối), liệu có bao giờ sinh ra ngôn ngữ sai không?**
    > Không bao giờ! Nhờ bất biến cấu trúc Thompson: mọi mảnh NFA con do `build_node()` sinh ra đều có **bậc vào của `start` bằng 0** và **bậc ra của `accept` bằng 0** (kể cả `StarNode` và `PlusNode`, vì vòng lặp quay về `c_s` nằm bên trong, còn `s` và `e` mới tạo ở ngoài). Do đó việc gộp `l_e` với `r_s` không thể tạo bất kỳ đường đi thừa nào.
18. **Tại sao `MiniSQL` tối thiểu hóa giảm tới 18.8% trạng thái trong khi `MiniLang` chỉ giảm 7.4%?**
    > Vì `MiniSQL` cho phép từ khóa cả chữ hoa lẫn chữ thường (`SELECT|select`, `WHERE|where`, `FROM|from`...), tạo ra hai nhánh song song dài trong Subset DFA (`S-E-L-E-C-T` và `s-e-l-e-c-t`). Tuy nhiên sau các tiền tố khác nhau, các phần đuôi hoặc các trạng thái chỉ còn nối tiếp thành `IDENT` có hành vi tương lai giống hệt nhau nên thuật toán phân hoạch gộp lại được nhiều hơn đáng kể!
19. **Nếu đầu vào có ký tự tiếng Việt có dấu (như `ă`, `đ`) hoặc `€` thì bộ quét xử lý thế nào?**
    > Do bảng chữ cái $\Sigma$ được giới hạn trong 98 ký tự ASCII (32..126 + `\t\n\r`), ký tự ngoài $\Sigma$ không thuộc lớp tương đương nào (`_char_to_class.get(ch)` trả về `None`), nên `dfa.step()` trả `None` (DEAD) ngay tại `D0` và scanner báo `LEXICAL_ERROR` kèm mã Unicode (VD: `U+20AC`) rồi phục hồi quét tiếp.
20. **Hướng mở rộng tiếp theo của đồ án nếu có thêm thời gian là gì?**
    > (1) Hỗ trợ bình luận nhiều dòng `/* ... */` bằng chính biểu thức chính quy hoặc chế độ Start Conditions (nhiều trạng thái ngữ cảnh như Flex); (2) Hỗ trợ UTF-8/Unicode bằng bảng phân hoạch theo khoảng mã điểm (range-based DFA transitions); (3) Thêm quy tắc bắt lỗi chuỗi chưa đóng riêng để phục hồi thông minh hơn; (4) Kết nối luồng token đầu ra vào một bộ phân tích cú pháp LL(1) / Recursive-Descent Parser hoàn chỉnh!
