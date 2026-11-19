# LỜI THOẠI THUYẾT TRÌNH TỪNG SLIDE (13 SLIDES — 9 PHÚT 30 GIÂY) & FLASHCARD ÔN TẬP NHANH LÝ THUYẾT CHƯƠNG 1–3

> **Tài liệu này gồm 2 phần:**
> - **PHẦN A:** Lời thoại chi tiết từng câu cho **13 Slide** trong file `deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx` (chia đều cho 4 thành viên, khớp chuẩn **9 phút 30 giây**, kèm kịch bản chuyển sang **Live Demo Web Studio**).
> - **PHẦN B:** **15 Flashcard Ôn tập Cốt lõi Chương 1 – Chương 3** (Ngôn ngữ hình thức UEH) giải thích từ gốc cho cả thành viên không chuyên code cũng trả lời lưu loát khi giảng viên hỏi bất kỳ thành viên nào.

---

## PHẦN A: PHÂN CÔNG & LỜI THOẠI CHI TIẾT 13 SLIDES (9 PHÚT 30 GIÂY)

### Bảng phân công 4 thành viên (Ai cũng nắm vững phần mình + hiểu toàn bài)

| Thành viên | Phụ trách Slide | Thời lượng | Nội dung chính |
| :--- | :--- | :---: | :--- |
| **Thành viên 1** | **Slide 1, 2, 3** | **2 phút 00 giây** | Mở đầu, bài toán Lexical Analysis, kiến trúc 6 nhánh & cơ sở lý thuyết Chương 1–3 + UTF-8 `NON_ASCII` |
| **Thành viên 2** | **Slide 4, 5, 6** | **2 phút 15 giây** | Thompson $\varepsilon$-NFA (ĐL 3) $\to$ Khử $\varepsilon$ (ĐL 2) $\to$ Subset DFA (ĐL 1) $\to$ Direct DFA (`followpos` Slide 54) |
| **Thành viên 3** | **Slide 7, 8 + Live Demo** | **3 phút 00 giây** | Tối thiểu hóa Moore vs. Hopcroft, Myhill–Nerode, Reps (1998) $O(n)$, phát hiện luật bị che khuất & **Demo Web Studio** |
| **Thành viên 4** | **Slide 9, 10, 11, 12, 13** | **2 phút 15 giây** | Kiểm chứng Product Automaton, 62 test cases + 5 bất biến, Benchmark 3 ngôn ngữ, tổng kết & mời hỏi đáp |

---

### LỜI THOẠI TỪNG SLIDE (Cầm đọc tự nhiên, chỉ tay vào bảng/hình trên slide)

#### SLIDE 1 — Trang bìa (Thành viên 1 — 0:00 đến 0:30)
> *"Em xin kính chào Cô và các bạn. Hôm nay Nhóm 6 chúng em xin trình bày báo cáo đồ án cuối kỳ môn Ngôn ngữ hình thức với đề tài **T13: Automata-based Lexical Analyzer — Thiết kế và Hiện thực Bộ phân tích từ vựng tổng quát dựa trên Lý thuyết Ô-tô-mát hữu hạn**.*
>
> *Điểm cốt lõi nhất trong đồ án của nhóm là toàn bộ hệ thống được xây dựng **100% từ gốc bằng Python Standard Library**, tuyệt đối **không sử dụng thư viện `import re`** hay bất kỳ công cụ sinh lexer có sẵn nào, đồng thời cài đặt trọn vẹn **6 nhánh thuật toán Chương 3.1** và kiểm chứng tương đương toán học tự động."*

---

#### SLIDE 2 — Đặt vấn đề & Mục tiêu đề tài (Thành viên 1 — 0:30 đến 1:15)
> *"Bước sang Slide 2: Trong mọi trình biên dịch hay bộ thông dịch, **Phân tích từ vựng (Lexical Analysis)** là pha đầu tiên, có nhiệm vụ đọc dòng ký tự mã nguồn thô và nhóm chúng thành chuỗi các **Token** có nghĩa, đồng thời lọc bỏ khoảng trắng, chú thích và phát hiện lỗi từ vựng.*
>
> *Thay vì viết các câu lệnh `if-else` thủ công hay gọi hàm `re` hộp đen, đồ án của nhóm giải quyết bài toán tổng quát: Nhận vào một bảng đặc tả gồm $k$ biểu thức chính quy ưu tiên $\mathcal{S} = \{(R_1, T_1, \pi_1), \dots, (R_k, T_k, \pi_k)\}$, hệ thống tự động biên dịch qua 6 nhánh ô-tô-mát về một **Minimized DFA** duy nhất và quét mã nguồn với độ phức tạp **tuyến tính chặt $O(n)$**."*

---

#### SLIDE 3 — Kiến trúc 6 nhánh & Không gian ký tự UTF-8 `NON_ASCII` (Thành viên 1 — 1:15 đến 2:00)
> *"Trên Slide 3 là sơ đồ kiến trúc tổng thể gồm 10 mô-đun độc lập và 6 nhánh biên dịch song song của hệ thống:*
> 1. *Từ Regex qua Parser đệ quy xuống có hỗ trợ định lượng đếm `{m,n}`.*
> 2. *Nhánh 1 xây dựng **Thompson $\varepsilon$-NFA** (Định lý 3).*
> 3. *Nhánh 2 thực hiện **Khử $\varepsilon$-transition** sang NFA chuẩn không $\varepsilon$ (Định lý 2).*
> 4. *Nhánh 3 tập hợp con **Subset Construction** sang DFA (Định lý 1).*
> 5. *Nhánh 4 & 5 tối thiểu hóa song song bằng cả **Moore** lẫn **Hopcroft**.*
> 6. *Nhánh 6 đi thẳng từ **RE sang Direct DFA** không qua NFA, bao gồm cả **Combined Multi-token Direct DFA**.*
>
> *Đặc biệt, để xử lý tiếng Việt UTF-8 mà vẫn giữ bảng chữ cái hữu hạn $|\Sigma| = 99$, nhóm thiết kế lớp ký tự đại diện `NON_ASCII` (`\x80`) cho mọi ký tự `ord(c) >= 128`. Nhờ đó chuỗi `"Xin chào UEH"` hay chú thích tiếng Việt được khớp tự nhiên, nhưng ký tự lạ ngoài chuỗi như `100€` vẫn bị bắt lỗi `LEXICAL_ERROR (U+20AC)` chính xác. Em xin nhường lời cho bạn tiếp theo."*

---

#### SLIDE 4 — Pipeline 1: Thompson $\varepsilon$-NFA (ĐL 3) & Khử $\varepsilon$ (ĐL 2) (Thành viên 2 — 2:00 đến 2:45)
> *"Em xin tiếp tục ở Slide 4 với hai định lý đầu tiên của Chương 3.1.*
>
> *Thứ nhất, theo **Định lý 3 (Thompson Construction, Slide 26–29)**, mọi biểu thức chính quy $R$ đều chuyển được thành một $\varepsilon$-NFA mà mỗi nút cấu trúc có đúng 1 trạng thái vào, 1 trạng thái ra, và tối đa 2 cung $\varepsilon$ đi ra. Ví dụ với mẫu kinh điển `(a|b)*abb`, hệ thống sinh ra đúng **11 trạng thái ($q_0 \dots q_{10}$)** như hình bên phải.*
>
> *Thứ hai, nhóm cài đặt đầy đủ **Định lý 2 (Khử $\varepsilon$-chuyển tiếp, Slide 21–22)** trong hàm `eliminate_epsilon(nfa)`: với mỗi trạng thái $q$ và ký tự $a$, ta tính $\delta'(q, a) = \varepsilon\text{-closure}(\text{move}(\varepsilon\text{-closure}(q), a))$ và đánh dấu $q \in F'$ nếu $\varepsilon\text{-closure}(q) \cap F \neq \emptyset$. Trên mẫu `(a|b)*abb`, bước khử $\varepsilon$ thu gọn từ **11 trạng thái xuống còn 6 trạng thái** có hiệu lực, hoàn toàn không còn cung $\varepsilon$ nào."*

---

#### SLIDE 5 — Subset Construction (ĐL 1) & Tối ưu phân hoạch bảng chữ cái (Thành viên 2 — 2:45 đến 3:30)
> *"Sang Slide 5 là bước **Subset Construction (Định lý 1, Slide 18–20)**: mỗi trạng thái của DFA là một tập con $S = \varepsilon\text{-closure}(T) \subseteq Q_{\text{NFA}}$.*
>
> *Khi ghép $k$ quy tắc token của một ngôn ngữ thông qua một trạng thái khởi đầu chung $q_{\text{start}}$, một trạng thái DFA $S$ có thể chứa đồng thời nhiều trạng thái kết thúc của cả `KW_IF` lẫn `IDENTIFIER`. Hệ thống giải quyết xung đột theo quy tắc chuẩn của Lex/Flex:*
> $$\tau(S) = \arg\min_{(q, T_i, \pi_i) \in S \cap F_{\text{NFA}}} \pi_i$$
> *tức là quy tắc nào được khai báo trước (có $\pi_i$ nhỏ nhất) sẽ chiến thắng.*
>
> *Đồng thời, thay vì duyệt mù quáng cả 99 ký tự ở mỗi bước, mô-đun `subset_construction.py` phân hoạch bảng chữ cái thành các **lớp tương đương ký tự (Alphabet Equivalence Classes)** có cùng tập đích NFA, giúp rút gọn từ 99 ký tự xuống chỉ còn **43 lớp** trên MiniLang, tăng tốc biên dịch hơn 2,3 lần."*

---

#### SLIDE 6 — Pipeline 2: Direct RE $\to$ DFA & Combined Multi-token Direct DFA (Thành viên 2 — 3:30 đến 4:15)
> *"Ở Slide 6 là nhánh thứ hai: chuyển trực tiếp **RE sang DFA** theo thuật toán Aho–Lam–Sethi–Ullman và Slide 37–54 bài giảng.*
>
> *Ta nối biểu thức với ký hiệu kết thúc `#`: $(R) \cdot \#$, đánh số các lá ký tự $1 \dots n$, và tính đệ quy từ dưới lên 3 hàm `nullable(u)`, `firstpos(u)`, `lastpos(u)`, từ đó suy ra bảng `followpos(i)`.*
>
> *Như Cô và các bạn thấy trên bảng kiểm chứng đối chiếu **Slide 54 bài giảng UEH** với biểu thức `(a|ba)(a|b)*ba#` (8 vị trí lá): tập `followpos` của từng vị trí từ 1 đến 8 và 5 trạng thái Direct DFA $A=\{1,2\}$, $B=\{4,5,6\}$, $C=\{3\}$, $D=\{4,5,6,7\}$, $E=\{4,5,6,8\}$ do phần mềm sinh ra **khớp 100% từng con số với bài giảng**.*
>
> *Hơn nữa, nhóm đã mở rộng thành công sang **Combined Multi-token Direct DFA** trực tiếp từ cây hợp $(R_1 \cdot \#_1) \mid \dots \mid (R_k \cdot \#_k)$ cho cả bộ 39 quy tắc MiniLang. Em xin chuyển cho bạn thứ 3."*

---

#### SLIDE 7 — Tối thiểu hóa DFA (Moore vs. Hopcroft) & Chứng minh Myhill–Nerode (Thành viên 3 — 4:15 đến 5:00)
> *"Em xin trình bày Slide 7 về Tối thiểu hóa DFA và Chứng minh tính tối giản tuyệt đối.*
>
> *Điểm đặc biệt lưu ý trong bộ phân tích từ vựng đa-token là phân hoạch khởi đầu $\Pi_0$ **không thể** chỉ chia làm 2 nhóm $\{F, Q \setminus F\}$, vì nếu gộp trạng thái kết thúc của `KW_IF` với `IDENTIFIER` thì DFA sẽ trả về sai loại token! Do đó $\Pi_0$ phải chia theo **nhãn token chiến thắng**:*
> $$\Pi_0 = \{Q_{\text{non-accept}}\} \cup \{Q_{T_1}, Q_{T_2}, \dots, Q_{T_k}\}$$
>
> *Nhóm cài đặt song song cả 2 thuật toán:*
> - ***Moore Partition Refinement*** ($O(|Q|^2 \cdot |\Sigma|)$) để xuất vết trực quan từng bước $\Pi_0 \to \Pi_1 \to \dots \to \Pi_m$ phục vụ giảng dạy.
> - ***Hopcroft Worklist Algorithm*** ($O(|\Sigma| \cdot |Q| \log |Q|)$) dùng đồ thị chuyển tiếp ngược $\delta^{-1}(A, c)$ và luôn đẩy tập con nhỏ hơn vào hàng đợi $W$.
>
> *Cuối cùng, hàm `verify_dfa_is_minimal(dfa)` chứng minh theo **Định lý Myhill–Nerode**: mọi cặp trạng thái $\binom{78}{2} = 3.003$ cặp trên MiniLang đều tồn tại chuỗi phân tách ngắn nhất $w$, chứng minh DFA đã tối giản tuyệt đối 100%."*

---

#### SLIDE 8 — Bộ quét Từ vựng Tuyến tính $O(n)$ (Reps 1998), Luật Che Khuất & Phục hồi Lỗi (Thành viên 3 — 5:00 đến 7:15, gồm 1 phút 30 giây Live Demo)
> *"Ở Slide 8 là những nâng cấp chiều sâu cho bộ quét `scanner.py` và bộ kiểm tra `LexicalAnalyzer`:*
> 1. ***Chống tấn công quay lui bậc hai $O(n^2)$ theo thuật toán Reps (1998)***: Khi gặp chuỗi bệnh lý như `"` theo sau bởi 10.000 ký tự `\"` nhưng không đóng ngoặc kép ở cuối, Maximal Munch cổ điển sẽ quay lui lặp lại gây tốn thời gian $O(n^2)$. Nhóm trang bị bảng băm `failed_states` ghi nhớ các cặp `(state, pos)` đã biết chắc không dẫn tới trạng thái kết thúc nào. Nhờ đó 10.000 ký tự chỉ mất **24 ms** với đúng **5.000 lần cắt nhánh tức thì**.*
> 2. ***Tự động phát hiện quy tắc bị che khuất (Shadowed Rules)***: Nếu người dùng đặt `IDENTIFIER` lên trước `KW_IF`, hệ thống lập tức phát hiện `KW_IF` không xuất hiện ở bất kỳ trạng thái kết thúc nào của Minimized DFA và cảnh báo rõ quy tắc nào đã che khuất nó.*
> 3. ***Hỗ trợ 2 chế độ phục hồi lỗi (`panic_char` vs `smart_sync`)*** và bình luận nhiều dòng `/* ... */` bằng biểu thức chính quy chuẩn `/\*([^*]|\*+[^*/])*\*+/`.*
>
> *Bây giờ em xin chuyển sang **Live Demo 90 giây trên giao diện Web Studio** đang chạy trực tiếp:*
> *(Mở trình duyệt Web Studio)*
> - ***(0:00–0:25) Tab 1 — Bộ quét Từ vựng***: *Em bấm quét trên MiniLang (39 quy tắc). Hệ thống nhận diện chính xác chuỗi tiếng Việt UTF-8 `"Xin chào UEH"`, bình luận nhiều dòng `/* ... */`, và bắt lỗi ký tự `@` ở dòng 11 kèm vết chạy DFA từng bước. Khi chuyển giữa `panic_char` và `smart_sync`, chuỗi chưa đóng được gom gọn thành 1 lỗi duy nhất.*
> - ***(0:25–0:55) Tab 2 & Tab 3 — Sơ đồ 6 Nhánh Ô-tô-mát & Direct RE Lab***: *Ở Tab 2, chọn `(a|b)*abb` hiện rõ 11 trạng thái Thompson $\to$ 6 trạng thái Khử $\varepsilon$ $\to$ 5 Subset DFA $\to$ 4 Min-DFA (Moore = Hopcroft = 4, Myhill–Nerode 6/6 cặp phân biệt). Sang Tab 3 chọn `(a|ba)(a|b)*ba` hiện đúng 8 vị trí lá, bảng `followpos` khớp Slide 54 và 5 trạng thái A..E.*
> - ***(0:55–1:30) Tab 4 & Tab 5 — Kiểm chứng & Benchmark***: *Ở Tab 4 hiện toàn bộ chứng minh tương đương 6 nhánh (0 phản ví dụ) và 100% 3.003 cặp trạng thái Myhill–Nerode phân biệt. Ở Tab 5 cho thấy 3 ngôn ngữ MiniLang, CalcLang, MiniSQL đều khớp tuyệt đối. Em xin nhường lời cho bạn thứ 4."*

---

#### SLIDE 9 — Kiểm chứng Tương đương Toán học (Product Automaton BFS) (Thành viên 4 — 7:15 đến 7:45)
> *"Em xin tiếp tục ở Slide 9: Làm sao chứng minh được các nhánh cài đặt độc lập hoàn toàn tương đương nhau?*
>
> *Trong mô-đun `verifier.py`, nhóm cài đặt thuật toán **Product Automaton BFS** kiểm tra hiệu đối xứng $L(\mathcal{D}_1) \Delta L(\mathcal{D}_2) = \emptyset$. Hệ thống duyệt BFS trên không gian tích $(q_1, q_2) \in Q_1 \times Q_2$. Nếu phát hiện bất kỳ cặp trạng thái nào có nhãn kết thúc khác nhau ($\tau_1(q_1) \neq \tau_2(q_2)$), thuật toán sẽ truy vết ngược để trả về **phản ví dụ ngắn nhất** $w$.*
>
> *Nhờ cơ chế này, hệ thống chứng minh tự động 3 đẳng thức lớn:*
> 1. *Thompson $\varepsilon$-NFA $\equiv$ NFA đã khử $\varepsilon$ $\equiv$ Subset DFA $\equiv$ Direct DFA.*
> 2. *Moore Min-DFA $\equiv$ Hopcroft Min-DFA (đẳng cấu 1–1).*
> 3. *Thompson+Subset Combined Min-DFA $\equiv$ Combined Multi-token Direct DFA trên toàn bộ các ngôn ngữ.*"

---

#### SLIDE 10 — Bộ kiểm thử 62 Test Cases & 5 Bất biến Toán học (Thành viên 4 — 7:45 đến 8:15)
> *"Sang Slide 10 là kết quả kiểm thử chất lượng phần mềm:*
> - *Bộ `tests/test_cases.json` gồm **62 test cases cấu trúc** (16 mẫu RE đơn, 20 mẫu bắt lỗi cú pháp RE biên, 26 kịch bản quét từ vựng biên) kết hợp với **16 bộ unittest chuyên sâu** trong `tests/test_suite.py` — tất cả đều đạt **100% PASS**.*
> - *Nhóm kiểm chứng tự động **5 Bất biến Toán học (Mathematical Invariants)** trên hàng trăm chuỗi fuzzing ngẫu nhiên, nổi bật là:*
>   - ***Invariant 1 (Zero-Loss Reconstruction)***: *Ghép mọi `lexeme` của token giữ lại, token bị bỏ qua và token lỗi luôn tái tạo khớp 100% từng byte chuỗi đầu vào gốc.*
>   - ***Invariant 5 (JFLAP 7.x Lossless Round-Trip)***: *Xuất automaton ra file XML `.jff` chuẩn JFLAP 7.x và đọc ngược lại vẫn tương đương 100% với automaton ban đầu.*"

---

#### SLIDE 11 — Thực nghiệm & Đánh giá Hiệu năng trên 3 Ngôn ngữ (Thành viên 4 — 8:15 đến 8:45)
> *"Slide 11 tổng hợp kết quả thực nghiệm trên 3 ngôn ngữ đặc tả có độ phức tạp khác nhau:*
> - ***MiniLang (39 quy tắc)***: *Từ 170 trạng thái $\varepsilon$-NFA $\to$ 96 trạng thái NFA khử $\varepsilon$ $\to$ 86 Subset DFA $\to$ 79 Combined Direct DFA $\to$ **78 trạng thái Min-DFA** (cả Moore và Hopcroft đều ra 78, giảm 9,3%, kiểm chứng 3.003/3.003 cặp Myhill–Nerode).*
> - ***CalcLang (12 quy tắc)***: *57 $\varepsilon$-NFA $\to$ 26 NFA khử $\varepsilon$ $\to$ 24 Subset DFA $\to$ **20 trạng thái Min-DFA** (giảm 16,67%).*
> - ***MiniSQL (14 quy tắc)***: *128 $\varepsilon$-NFA $\to$ 67 NFA khử $\varepsilon$ $\to$ 64 Subset DFA $\to$ **52 trạng thái Min-DFA** (giảm 18,75%).*
> - *Tốc độ quét thực tế đạt trên **26.000 đến 51.000 tokens/giây** chỉ với Python thuần."*

---

#### SLIDE 12 — Tổng kết Đóng góp & Hướng phát triển (Thành viên 4 — 8:45 đến 9:15)
> *"Ở Slide 12, nhóm xin tóm tắt 5 đóng góp nổi bật nhất của đồ án:*
> 1. *Hiện thực từ gốc 100% bằng Python Standard Library (0 `import re`) trọn vẹn **6 nhánh thuật toán Chương 3.1**.*
> 2. *Mở rộng thành công **Combined Multi-token Direct DFA** và chứng minh tương đương với nhánh Thompson+Subset.*
> 3. *Cài đặt song song **Moore & Hopcroft**, chứng minh tối giản tuyệt đối bằng **Myhill–Nerode**.*
> 4. *Bộ quét **Maximal Munch tuyến tính $O(n)$ (Reps 1998)** chống quay lui bậc hai, hỗ trợ UTF-8 `NON_ASCII`, bình luận `/*...*/`, phát hiện luật bị che khuất và xuất/nhập khứ hồi **JFLAP `.jff`**.*
> 5. *Xây dựng **Web Studio 5 Tab** trực quan kèm CLI và bộ 62 test cases đạt 100% PASS.*
>
> *Hướng phát triển tiếp theo là kết nối đầu ra Token Stream của bộ phân tích từ vựng này với Bộ phân tích cú pháp CFG (`LL(1)` / `LR(1)`) ở Chương 4."*

---

#### SLIDE 13 — Lời cảm ơn & Hỏi đáp Q&A (Thành viên 4 — 9:15 đến 9:30)
> *"Bài thuyết trình của Nhóm 6 đến đây là kết thúc. Nhóm chúng em xin chân thành cảm ơn Cô Hồ Thị Thanh Tuyến đã tận tình giảng dạy và hướng dẫn bộ môn Ngôn ngữ hình thức. Nhóm rất mong nhận được các câu hỏi và góp ý từ Cô và các bạn!"*

---
---

## PHẦN B: 15 FLASHCARD ÔN TẬP LÝ THUYẾT CHƯƠNG 1 – CHƯƠNG 3 (DỄ HIỂU 100% CHO MỌI THÀNH VIÊN)

> **Cách học nhanh:** Mỗi thành viên chỉ cần đọc qua 15 thẻ ngắn gọn dưới đây trong 15 phút là hiểu bản chất từng khái niệm từ Chương 1 đến Chương 3, sẵn sàng trả lời bất kỳ câu hỏi lý thuyết nào của Giảng viên.

---

### Thẻ 1 — Bảng chữ cái ($\Sigma$), Chuỗi ($w$) và Ngôn ngữ ($L$) [Chương 1]
- **Bảng chữ cái $\Sigma$**: Tập hợp **hữu hạn, khác rỗng** các ký hiệu. Trong đồ án: $|\Sigma| = 99$ gồm 98 ký tự ASCII + 1 ký hiệu đại diện `NON_ASCII` (`\x80`) cho mọi ký tự UTF-8 `ord(c) >= 128`.
- **Chuỗi (String / Word) $w$**: Dãy hữu hạn các ký hiệu lấy từ $\Sigma$. Chuỗi rỗng ký hiệu là $\varepsilon$ có độ dài $|\varepsilon| = 0$.
- **Bao đóng Kleene $\Sigma^*$**: Tập tất cả các chuỗi hữu hạn trên $\Sigma$ (kể cả $\varepsilon$). $\Sigma^+ = \Sigma^* \setminus \{\varepsilon\}$.
- **Ngôn ngữ (Language) $L$**: Bất kỳ tập con nào của $\Sigma^*$ ($L \subseteq \Sigma^*$).

---

### Thẻ 2 — Biểu thức chính quy (Regular Expression — RE) và Thứ tự ưu tiên [Chương 2]
- **3 phép toán cơ bản của RE**:
  1. **Hợp (Union)** $R_1 \mid R_2$:$L(R_1 \mid R_2) = L(R_1) \cup L(R_2)$ — ưu tiên **thấp nhất**.
  2. **Nối kết (Concatenation)** $R_1 \cdot R_2$: $L(R_1 R_2) = \{xy \mid x \in L(R_1), y \in L(R_2)\}$ — ưu tiên **trung bình**.
  3. **Bao đóng Kleene (Star)** $R^*$: $L(R^*) = \bigcup_{i \ge 0} L(R)^i$ — ưu tiên **cao nhất** (cùng với `+`, `?`, `{m,n}`).
- **Các phép toán mở rộng đều quy về 3 phép toán gốc**:
  - $R^+ \equiv R \cdot R^*$
  - $R? \equiv R \mid \varepsilon$
  - $R\{2,4\} \equiv R \cdot R \cdot (R \mid \varepsilon) \cdot (R \mid \varepsilon)$

---

### Thẻ 3 — Phân biệt DFA, NFA và $\varepsilon$-NFA (Bộ 5 thành phần) [Chương 3.1]
Cả 3 đều được định nghĩa bởi bộ 5 thành phần $M = (Q, \Sigma, \delta, q_0, F)$, chỉ khác nhau ở **hàm chuyển trạng thái $\delta$**:
1. **DFA (Đơn định)**: $\delta: Q \times \Sigma \to Q$ (mỗi cặp $(q, a)$ đi tới **tối đa 1** trạng thái duy nhất, **không** có cung $\varepsilon$).
2. **NFA (Không đơn định, không $\varepsilon$)**: $\delta: Q \times \Sigma \to \mathcal{P}(Q)$ (mỗi cặp $(q, a)$ có thể đi tới **nhiều** trạng thái, nhưng **không** có cung $\varepsilon$).
3. **$\varepsilon$-NFA (Không đơn định có $\varepsilon$)**: $\delta: Q \times (\Sigma \cup \{\varepsilon\}) \to \mathcal{P}(Q)$ (cho phép chuyển trạng thái tự do qua cung $\varepsilon$ mà không cần đọc ký tự đầu vào).
- **Khả năng biểu diễn**: Ba mô hình này **tương đương hoàn toàn** — cùng nhận diện đúng lớp **Ngôn ngữ chính quy (Regular Languages)**.

---

### Thẻ 4 — Định lý 3: Thuật toán Thompson ($\text{RE} \to \varepsilon\text{-NFA}$, Slide 26–29)
- **Ý tưởng**: Dựng $\varepsilon$-NFA từ dưới lên theo cây cú pháp AST của biểu thức chính quy.
- **Đặc trưng**: Mỗi mảnh $\varepsilon$-NFA con $N(s, f)$ luôn có đúng **1 trạng thái bắt đầu $s$** (không có cung đi vào), **1 trạng thái kết thúc $f$** (không có cung đi ra), và mỗi trạng thái có **tối đa 2 cung $\varepsilon$ đi ra**.
- **Số trạng thái**: Tuyến tính theo kích thước biểu thức $|R|$, cụ thể $|Q| \le 2|R|$.
- **Ví dụ bài giảng**: `(a|b)*abb` sinh ra đúng **11 trạng thái ($q_0 \dots q_{10}$)**.

---

### Thẻ 5 — Định lý 2: Khử chuyển tiếp $\varepsilon$ ($\varepsilon\text{-NFA} \to \text{NFA}$, Slide 21–22)
- **Mục tiêu**: Xóa toàn bộ các cung $\varepsilon$ từ $\varepsilon$-NFA để thu được NFA chuẩn không có $\varepsilon$ trên cùng tập trạng thái.
- **Công thức**:
  1. Tính $\varepsilon\text{-closure}(q)$ cho mọi trạng thái $q$.
  2. Với mỗi trạng thái $q$ và ký tự $a \in \Sigma$:
     $$\delta'(q, a) = \varepsilon\text{-closure}\big(\text{move}(\varepsilon\text{-closure}(q), a)\big)$$
  3. Tập trạng thái kết thúc mới:
     $$F' = \{q \in Q \mid \varepsilon\text{-closure}(q) \cap F \neq \emptyset\}$$
- **Ví dụ bài giảng**: Trên `(a|b)*abb`, sau khi khử $\varepsilon$ và bỏ các trạng thái cô lập không có cung đi vào, số trạng thái giảm từ **11 xuống còn 6 trạng thái**.

---

### Thẻ 6 — Định lý 1: Thuật toán Tập con — Subset Construction ($\text{NFA} \to \text{DFA}$, Slide 18–20)
- **Ý tưởng**: Mỗi trạng thái của DFA là một **tập hợp các trạng thái NFA** có thể đạt tới đồng thời.
- **Công thức**:
  - Trạng thái bắt đầu DFA: $S_0 = \varepsilon\text{-closure}(\{q_0\})$.
  - Chuyển tiếp DFA: $\delta_{\text{DFA}}(S, a) = \varepsilon\text{-closure}(\text{move}(S, a))$.
- **Độ phức tạp**: Trường hợp xấu nhất theo lý thuyết là $2^{|Q|}$ trạng thái, nhưng với các quy tắc từ vựng thực tế, các tập con đạt được rất thưa: trên MiniLang (170 trạng thái $\varepsilon$-NFA), Subset DFA chỉ sinh ra **86 trạng thái**!

---

### Thẻ 7 — Phương pháp Trực tiếp $\text{RE} \to \text{DFA}$ (`nullable`, `firstpos`, `lastpos`, `followpos`, Slide 37–54)
- **Tại sao cần?**: Tránh sinh các trạng thái $\varepsilon$ trung gian của Thompson bằng cách chỉ tính toán trên các **lá ký tự thực sự** của biểu thức $(R) \cdot \#$.
- **Ý nghĩa 4 hàm**:
  - `nullable(u)`: Cây con $u$ có sinh được chuỗi rỗng $\varepsilon$ hay không? (`True`/`False`).
  - `firstpos(u)`: Tập vị trí lá có thể xuất hiện ở **ký tự đầu tiên** của chuỗi thuộc $L(u)$.
  - `lastpos(u)`: Tập vị trí lá có thể xuất hiện ở **ký tự cuối cùng** của chuỗi thuộc $L(u)$.
  - `followpos(i)`: Tập vị trí lá có thể xuất hiện **ngay liền sau** vị trí $i$.
- **Chỉ có 2 nơi sinh ra `followpos`**:
  1. Tại nút nối $c_1 \cdot c_2$: Với mọi $i \in \text{lastpos}(c_1)$, thêm $\text{firstpos}(c_2)$ vào $\text{followpos}(i)$.
  2. Tại nút lặp $c^*$ (hoặc $c^+$): Với mọi $i \in \text{lastpos}(c)$, thêm $\text{firstpos}(c)$ vào $\text{followpos}(i)$.

---

### Thẻ 8 — Tối thiểu hóa DFA: Moore vs. Hopcroft [Chương 3.1]
- **Tại sao phân hoạch đầu $\Pi_0$ của Lexer không phải là $\{F, Q \setminus F\}$?**
  - Vì nếu gộp chung trạng thái chấp nhận của `KW_IF` và `IDENTIFIER`, DFA sau khi tối thiểu hóa sẽ không biết trả về token nào! Do đó phải khởi tạo $\Pi_0 = \{Q_{\text{non-accept}}\} \cup \{Q_{T_1}, Q_{T_2}, \dots, Q_{T_k}\}$.
- **So sánh Moore và Hopcroft**:
  - **Moore**: Mỗi vòng lặp duyệt lại toàn bộ các nhóm để tách $\Pi_k \to \Pi_{k+1}$. Độ phức tạp $O(|Q|^2 \cdot |\Sigma|)$, rất trực quan để in bảng quá trình chia nhóm.
  - **Hopcroft**: Dùng tập chuyển tiếp ngược $\delta^{-1}(A, c)$ và hàng đợi $W$, mỗi lần chia đôi nhóm $Y \to (Y_1, Y_2)$ chỉ cần đẩy **nhóm nhỏ hơn** vào $W$, nhờ đó đạt độ phức tạp $O(|\Sigma| \cdot |Q| \log |Q|)$.
  - **Kết quả**: Cả hai luôn cho ra hai Min-DFA **đẳng cấu 1–1** (cùng 78 trạng thái trên MiniLang).

---

### Thẻ 9 — Định lý Myhill–Nerode & Cách chứng minh DFA đã tối giản tuyệt đối
- **Nội dung định lý**: Hai trạng thái $p, q$ là **phân biệt được (distinguishable)** nếu tồn tại ít nhất một chuỗi hậu tố $w \in \Sigma^*$ sao cho khi đọc tiếp $w$ từ $p$ và từ $q$, hai đường đi dẫn tới hai kết quả chấp nhận token khác nhau:
  $$\tau(\hat{\delta}(p, w)) \neq \tau(\hat{\delta}(q, w))$$
- **Ứng dụng trong đồ án (`verify_dfa_is_minimal`)**: Hệ thống kiểm tra tất cả $\binom{|Q|}{2}$ cặp trạng thái của Min-DFA (ví dụ $\binom{78}{2} = 3.003$ cặp trên MiniLang) và tìm ra chuỗi phân tách ngắn nhất $w$ cho đủ **100% (3.003/3.003 cặp)** — đây là bằng chứng toán học không thể chối cãi rằng không còn bất kỳ 2 trạng thái nào có thể gộp thêm được nữa!

---

### Thẻ 10 — Hai nguyên tắc vàng của Bộ quét Từ vựng: Maximal Munch & Priority Rule
1. **Maximal Munch (Khớp dài nhất)**: Luôn ăn chuỗi tiền tố dài nhất có thể mà vẫn thuộc một trạng thái kết thúc của DFA.
   - *Ví dụ*: Gặp `ifelse` phải nhận là 1 `IDENTIFIER("ifelse")` (dài 6) chứ không cắt ở `KW_IF("if")` (dài 2); gặp `==` phải nhận là `OP_EQ("==")` chứ không phải hai dấu `=`.
2. **Priority Rule (Ưu tiên quy tắc khai báo trước)**: Khi cùng khớp độ dài tối đa như nhau, quy tắc nào có số thứ tự ưu tiên $\pi$ nhỏ hơn (đứng trên trong bảng đặc tả) sẽ thắng.
   - *Ví dụ*: Chuỗi `"if"` vừa khớp `KW_IF` (dài 2, $\pi=0$) vừa khớp `IDENTIFIER` (dài 2, $\pi=36$) $\to$ Chọn `KW_IF`.

---

### Thẻ 11 — Thuật toán Reps (1998): Tại sao Maximal Munch ngây thơ bị $O(n^2)$ và cách sửa thành $O(n)$?
- **Vấn đề $O(n^2)$ của Maximal Munch ngây thơ**:
  - Giả sử quy tắc chuỗi là `"([^"\\\n]|\\.)*"` và đầu vào là `"` theo sau bởi 10.000 ký tự `a` nhưng **thiếu dấu `"` đóng ở cuối**.
  - Ở vị trí 0, DFA đọc ký tự `"` (chưa phải trạng thái kết thúc), rồi đọc hết 10.000 chữ `a` tới EOF vẫn chưa gặp `"` đóng $\to$ quay lui về vị trí 0 báo lỗi `"`, rồi tiến lên vị trí 1. Nếu có nhiều quy tắc tiền tố dài nhưng thất bại ở cuối (như `12345...e+` thiếu số mũ), bộ quét ngây thơ sẽ đọc đi đọc lại đoạn đuôi tốn $O(n^2)$ bước.
- **Giải pháp Reps (1998) trong `scanner.py`**:
  - Lưu bảng nhớ `failed_states`: nếu một lần chạy DFA đi qua cặp `(state, cursor)` mà từ thời điểm đó đến lúc kẹt không gặp thêm bất kỳ trạng thái kết thúc nào, ta đánh dấu `(state, cursor) \in \text{failed\_states}`.
  - Ở các token kế tiếp, hễ DFA chạm lại một cặp `(state, cursor)` đã có trong `failed_states`, nó **dừng ngay lập tức** không đi tiếp nữa! Nhờ đó mỗi cặp `(state, cursor)` chỉ bị duyệt thất bại tối đa 1 lần $\to$ thời gian quét luôn là **tuyến tính chặt $O(|Q| \cdot n) = O(n)$**.

---

### Thẻ 12 — Phát hiện Quy tắc bị Che Khuất (Shadowed / Dead Token Rules)
- **Khi nào một quy tắc bị che khuất?**
  - Khi ngôn ngữ của quy tắc $R_j$ nằm hoàn toàn trong ngôn ngữ của một quy tắc $R_i$ có độ ưu tiên cao hơn ($L(R_j) \subseteq L(R_i)$ với $\pi_i < \pi_j$).
  - *Ví dụ kinh điển*: Đặt `IDENTIFIER` (`[a-zA-Z_][a-zA-Z0-9_]*`, $\pi=1$) lên **trên** `KW_IF` (`if`, $\pi=2$). Vì mọi chuỗi `"if"` đều nằm trong tập hợp của `IDENTIFIER`, tại trạng thái kết thúc nhận chuỗi `"if"`, quy tắc `IDENTIFIER` luôn có $\pi$ nhỏ hơn và giành chiến thắng!
- **Cách hệ thống phát hiện tự động**:
  - Sau khi sinh `Minimized DFA`, hệ thống quét toàn bộ các trạng thái kết thúc $q \in F_{\text{min}}$. Nếu một quy tắc $T_j$ có xuất hiện trong các trạng thái NFA thành phần nhưng **không bao giờ là nhãn chiến thắng $\tau(q)$ ở bất kỳ trạng thái kết thúc nào**, hệ thống kết luận $T_j$ bị che khuất hoàn toàn và chỉ ra chính xác quy tắc $T_i$ đã đè lên nó!

---

### Thẻ 13 — Biểu thức chính quy cho Bình luận nhiều dòng `/* ... */` và Chứng minh Bổ đề Bơm (Pumping Lemma) cho bình luận lồng nhau
- **Tại sao không được viết `/\*.*\*/` cho bình luận nhiều dòng?**
  - Vì `.` khớp mọi ký tự (trừ `\n`), và do tính chất **Maximal Munch (tham lam)**, trên dòng `/* c1 */ x = 1; /* c2 */`, biểu thức `/\*.*\*/` sẽ nuốt trọn từ `/*` đầu tiên đến `*/` cuối cùng, ăn mất luôn cả câu lệnh `x = 1;` ở giữa!
- **Biểu thức chính quy chuẩn trong đồ án**:
  $$R_{\text{block}} = \texttt{/\*([\^{}*]|\\*+[\^{}*/])*\*+/}$$
  *(Giải thích: Sau `/*`, ở bên trong chỉ cho phép hoặc ký tự không phải `*`, hoặc một dãy dấu `*+` nhưng ký tự ngay sau nó không được là `*` hay `/`, cho tới khi gặp dãy `*+/` đóng đầu tiên).*
- **Tại sao bình luận nhiều dòng LỒNG NHAU (`/* /* ... */ */` độ sâu tùy ý) KHÔNG phải ngôn ngữ chính quy?**
  - Áp dụng **Bổ đề Bơm (Pumping Lemma)**: Giả sử ngôn ngữ bình luận lồng nhau $L = \{ \texttt{/*}^m \texttt{*/}^m \mid m \ge 1 \}$ là chính quy với hằng số bơm $p$. Chọn chuỗi $w = \texttt{/*}^p \texttt{*/}^p \in L$. Theo bổ đề bơm, $w = xyz$ với $|xy| \le p$ và $|y| \ge 1$, nên $y$ chỉ nằm trong phần mở `/*`. Khi bơm $xy^2z$, số dấu mở `/*` nhiều hơn số dấu đóng `*/` $\to$ chuỗi không còn cân bằng ($xy^2z \notin L$), mâu thuẫn! Vậy bình luận lồng nhau thuộc **Ngôn ngữ phi ngữ cảnh (CFG — Chương 4)** chứ không phải Ngôn ngữ chính quy.

---

### Thẻ 14 — Kiểm chứng Tương đương 2 DFA bằng Product Automaton BFS
- **Bài toán**: Cho 2 DFA $\mathcal{D}_1 = (Q_1, \Sigma, \delta_1, q_{01}, F_1, \tau_1)$ và $\mathcal{D}_2 = (Q_2, \Sigma, \delta_2, q_{02}, F_2, \tau_2)$, làm sao kiểm tra $\mathcal{D}_1 \equiv \mathcal{D}_2$ trên mọi chuỗi $w \in \Sigma^*$ (vô hạn chuỗi)?
- **Giải pháp**: Dựng ô-tô-mát tích $\mathcal{D}_1 \times \mathcal{D}_2$ và duyệt **BFS** từ cặp trạng thái gốc $(q_{01}, q_{02})$:
  - Với mỗi ký tự $a \in \Sigma$, đi tới cặp trạng thái đích $(p_1, p_2) = (\delta_1(q_1, a), \delta_2(q_2, a))$.
  - Nếu tại bất kỳ cặp $(p_1, p_2)$ nào mà $\tau_1(p_1) \neq \tau_2(p_2)$ (một bên chấp nhận, một bên từ chối, hoặc trả về 2 tên token khác nhau), thuật toán dừng ngay và trả về đường đi BFS làm **phản ví dụ ngắn nhất** $w$.
  - Vì $Q_1 \times Q_2$ là hữu hạn (tối đa $|Q_1| \cdot |Q_2|$ cặp), nếu BFS duyệt hết mà không có cặp nào lệch nhãn thì $\mathcal{D}_1 \equiv \mathcal{D}_2$ trên **toàn bộ vô hạn chuỗi** $w \in \Sigma^*$.

---

### Thẻ 15 — Bảng Tóm tắt Con số Thực nghiệm "Thuộc lòng 10 giây" khi Bảo vệ
- **Mẫu bài giảng 1 `(a|b)*abb`**: Thompson $\varepsilon$-NFA = **11** $\to$ Khử $\varepsilon$ = **6** $\to$ Subset DFA = **5** $\to$ Min-DFA = **4** trạng thái.
- **Mẫu bài giảng 2 `(a|ba)(a|b)*ba#` (Slide 54)**: **8** vị trí lá, bảng `followpos` khớp từng số Slide 54, Direct DFA = **5** trạng thái (**A..E**).
- **MiniLang (39 quy tắc)**: $\varepsilon$-NFA = **170** $\to$ Khử $\varepsilon$ = **96** $\to$ Subset DFA = **86** $\to$ Combined Direct DFA = **79** $\to$ Moore & Hopcroft Min-DFA = **78** trạng thái (giảm **9,3%**, **43** lớp ký tự tương đương, **3.003/3.003** cặp Myhill–Nerode phân biệt).
- **Kiểm thử**: **62** test cases JSON + **16** bộ unittest + **5** bất biến toán học = **100% PASS**, **0** `import re`.
