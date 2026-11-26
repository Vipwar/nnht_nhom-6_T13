# LỜI THOẠI THUYẾT TRÌNH THEO TỪNG SLIDE (13 SLIDES — 9 PHÚT 30 GIÂY) VÀ THẺ ÔN TẬP CHƯƠNG 1–3

- **PHẦN A:** Lời thoại theo từng slide khớp với bố cục 13 slide trong tệp [`deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx) (đã được ghi vào phần **Speaker Notes** của từng slide trong PowerPoint để xem ở chế độ *Presenter View* `Alt + F5`).
- **PHẦN B:** 18 thẻ tóm tắt kiến thức Chương 1 – Chương 3 (Ngôn ngữ hình thức UEH) và các thành phần kỹ thuật của đồ án để ôn tập trước buổi bảo vệ.

---

## PHẦN A: PHÂN CÔNG VÀ LỜI THOẠI CHI TIẾT 13 SLIDES (9 PHÚT 30 GIÂY)

### Bảng phân công 4 thành viên

| Thành viên | Phụ trách Slide | Thời lượng | Nội dung chính |
| :--- | :--- | :---: | :--- |
| **Thành viên 1** | **Slide 1, 2, 3** | **2 phút 00 giây** | Mở đầu, bài toán Lexical Analysis và 4 mục tiêu đồ án, mô hình Đa-Token + Unicode động $\Sigma(U)$, bù kép $\sim(\sim A)=A$ và Ma trận giao nhau |
| **Thành viên 2** | **Slide 4, 5, 6** | **2 phút 15 giây** | Kiến trúc tổng thể theo Định lý Kleene, đối chiếu Slide 38 `(a|b)*abb` + GNFA (`DFA -> RE`) và Slide 54 `(a|ba)(a|b)*ba#` (`followpos`) |
| **Thành viên 3** | **Slide 7, 8, 9 + Demo** | **3 phút 00 giây** | Đồ thị Combined Min-DFA CalcLang (20 TT), Bộ quét $O(n)$ Reps (1998) + Sinh mã Lexer (`.py`), và Demo trực tiếp giao diện Web 5 tab |
| **Thành viên 4** | **Slide 10, 11, 12, 13** | **2 phút 15 giây** | Bộ kiểm thử 72/72 PASS + 22 nhóm Unittest và đối chứng mã sinh, Benchmark 3 ngôn ngữ, Bổ đề Bơm (Chương 3.2), phân công và kết luận |

---

### LỜI THOẠI THEO TỪNG SLIDE

#### SLIDE 1 — Trang bìa: AUTOMATA-BASED LEXICAL ANALYZER (Thành viên 1 — 0:00 đến 0:30)
> *"Em xin chào Cô và các bạn. Hôm nay Nhóm 6 xin trình bày báo cáo đồ án cuối kỳ môn Ngôn ngữ hình thức với đề tài **T13: Automata-based Lexical Analyzer — Xây dựng Bộ phân tích từ vựng tổng quát theo quy trình khép kín của Định lý Kleene**.*
>
> *Như tóm tắt ở khung bên phải slide, toàn bộ chương trình được cài đặt bằng thư viện chuẩn của Python, không sử dụng `import re`, phân hoạch bảng chữ cái Unicode động $\Sigma(U)$ giữ đúng tính chất bù kép $\sim(\sim A) = A$, cài đặt cả chiều xuôi và chiều ngược `GNFA (DFA -> RE)`, ma trận giao nhau tĩnh $L(R_i) \cap L(R_j)$, bộ sinh mã Lexer độc lập kiểu Flex và vượt qua 72/72 ca kiểm thử JSON cùng 22 nhóm Unittest."*

---

#### SLIDE 2 — `01 · ĐẶT VẤN ĐỀ`: Bài toán Phân tích từ vựng và Mục tiêu Đồ án T13 (Thành viên 1 — 0:30 đến 1:15)
> *"Ở Slide 2: Trong trình biên dịch, **Lexical Analyzer** là giai đoạn đầu tiên chuyển dòng ký tự mã nguồn thành luồng **Token**, lọc bỏ khoảng trắng, bình luận `//` và `/*...*/`, đồng thời phát hiện lỗi từ vựng kèm vị trí dòng, cột.*
>
> *Các lớp token từ vựng đều thuộc lớp **Ngôn ngữ chính quy**, có thể đặc tả bằng Biểu thức chính quy và nhận diện bằng DFA trong thời gian tuyến tính $O(n)$, tránh hiện tượng quay lui hàm mũ $O(2^n)$.*
>
> *Từ đó, nhóm đặt ra **4 mục tiêu chính** ở cột bên phải:*
> 1. *Không dùng `import re`, xây dựng đại số Boole trên $\Sigma(U)$ bao phủ 128 mã ASCII và giới hạn số nút AST `MAX_AST_NODES = 4096`.*
> 2. *Cài đặt hai chiều **Định lý Kleene** kèm GNFA (`DFA -> RE`), kiểm tra **Myhill-Nerode** và **Ma trận giao nhau $L(R_i) \cap L(R_j)$**.*
> 3. *Bộ quét tuyến tính $O(n)$ theo **Reps (1998)**, quy tắc `STRING_LIT` xử lý đúng dòng CRLF và sinh tệp **Lexer Python độc lập kiểu Flex**.*
> 4. *Xây dựng **Giao diện Web 5 tab** phục vụ minh họa cùng bộ **72 test cases JSON** và **22 nhóm unittest**."*

---

#### SLIDE 3 — `02 · MÔ HÌNH HÌNH THỨC`: Mô hình Đa-Token, Phân hoạch Unicode động $\Sigma(U)$ và Ma trận giao $L(R_i) \cap L(R_j)$ (Thành viên 1 — 1:15 đến 2:00)
> *"Slide 3 trình bày 3 thành phần mở rộng từ ô-tô-mát đơn lẻ sang bộ phân loại **Đa-Token**:*
> - ***Khung 1 (Combined $\varepsilon$-NFA và Khử $\varepsilon$)***: *Ghép $k$ mảnh $\varepsilon$-NFA con qua đỉnh đầu chung $q_{\text{start}}$, đồng thời cài đặt **Định lý 2 (Slide 21–22)** khử toàn bộ cung $\varepsilon$, giảm MiniLang từ 170 xuống 96 trạng thái NFA.*
> - ***Khung 2 (Subset DFA và Ma trận giao nhau $L(R_i) \cap L(R_j)$)***: *Gom $\Sigma(U)$ thành 44 lớp tương đương trên MiniLang; đồng thời phân tích tĩnh $\binom{39}{2} = 741$ cặp quy tắc để xác định 9 cặp từ khóa nằm trong `IDENTIFIER` kèm chuỗi chứng nhân ngắn nhất (`'if'..'true'`).*
> - ***Khung 3 (Moore/Hopcroft, Myhill-Nerode và GNFA)***: *Khởi tạo phân hoạch $\Pi_0$ tách riêng từng nhãn token kết thúc, kiểm tra Myhill-Nerode trên 3.003/3.003 cặp, và dùng GNFA khử trạng thái chuyển ngược DFA về RE.*
> - *Ở khung bên dưới, bảng chữ cái động $\Sigma(U) = 128\text{ ASCII} \cup U \cup \{\text{NON\_ASCII } \text{U+FDD0}\}$ đảm bảo $\sim(\sim A) = A$, hỗ trợ từ khóa tiếng Việt `nếu`, ký hiệu `€` không trùng với `NON_ASCII`, đồng thời chặn biểu thức lồng nhau `(((a{64}){64}){64})` bằng giới hạn `MAX_AST_NODES = 4096`. Em xin mời bạn tiếp theo trình bày."*

---

#### SLIDE 4 — `03 · KIẾN TRÚC HỆ THỐNG`: Quy trình Biên dịch Automata theo Định lý Kleene và Sinh mã Lexer (Thành viên 2 — 2:00 đến 2:40)
> *"Em xin tiếp tục ở Slide 4 với sơ đồ kiến trúc tổng thể của chương trình.*
>
> *Từ danh sách quy tắc biểu thức chính quy đầu vào:*
> - ***Nhánh biên dịch bên trên*** *đi qua các định lý Chương 3.1: Bộ phân tích cú pháp RE ($\le 4096$ nút, $\Sigma(U)$) $\to$ **Thompson $\varepsilon$-NFA** (Định lý 3) $\to$ **NFA khử $\varepsilon$** (Định lý 2) $\to$ **Subset DFA** (44 lớp $\Sigma$) $\to$ tối thiểu hóa song song bằng **Moore** và **Hopcroft**.*
> - ***Nhánh đối chứng và chiều ngược bên dưới*** *dựng trực tiếp từ cây cú pháp $r\cdot\#$ qua bảng `followpos` để sinh **Direct DFA**, đồng thời dùng thuật toán **GNFA State Elimination** chuyển ngược Min-DFA về biểu thức chính quy $R_{\text{sinh}}$ và kiểm tra $L(R_0) \equiv L(R_{\text{sinh}})$.*
> - *Ở đầu ra, Min-DFA vừa điều khiển trực tiếp bộ quét $O(n)$, vừa được mô-đun `codegen.py` xuất thành tệp **Lexer Python độc lập**."*

---

#### SLIDE 5 — `04 · THUẬT TOÁN CỐT LÕI (1/2)`: RE $\to$ Thompson $\to$ Khử $\varepsilon$ $\to$ Subset $\to$ Min-DFA $\to$ GNFA RE (Slide 38 UEH) (Thành viên 2 — 2:40 đến 3:25)
> *"Slide 5 đối chiếu kết quả thực thi trên biểu thức `(a|b)*abb` ở **Slide 38 Chương 3.1 bài giảng**:*
> - ***Hình (a) Thompson $\varepsilon$-NFA***: *Nhờ tính chất $\text{in-deg}(\text{start})=0$ và $\text{out-deg}(\text{end})=0$, phép nối kết gộp trực tiếp đỉnh nối và tạo ra **11 trạng thái ($q_0 \dots q_{10}$)** khớp với Slide 38.*
> - ***Bước Khử $\varepsilon$ theo Định lý 2 (Slide 21–22)***: *Loại bỏ các cung $\varepsilon$, giảm từ 11 xuống **6 trạng thái NFA**.*
> - ***Hình (b) và (c) Subset $\to$ Min-DFA***: *5 tập con $D_0 \dots D_4$ gộp $D_0 \equiv D_2$ còn **4 trạng thái tối giản** (đủ 6/6 cặp Myhill-Nerode).*
> - ***Bước GNFA (`DFA -> RE`)***: *Khử lần lượt $D_2, D_0, D_3, D_1$ thu được biểu thức `b*a(a|ba|bb(a|b+a))*bb`, và Product Automaton xác nhận $L(R_{\text{gốc}}) \equiv L(R_{\text{sinh}})$."*

---

#### SLIDE 6 — `04 · THUẬT TOÁN CỐT LÕI (2/2)`: Nhánh đối chứng Direct RE $\to$ DFA đơn lẻ và Đa-Token (Slide 46–57) (Thành viên 2 — 3:25 đến 4:15)
> *"Ở Slide 6 là nhánh đối chứng **Direct RE $\to$ DFA** theo Mục 2.5 (Slide 46–57 bài giảng).*
>
> *Khi chạy trên biểu thức bài giảng `r = (a|ba)(a|b)*ba#`:*
> - *Chương trình đánh số **8 nút lá** và tính bảng `followpos` trên giao diện Web Tab 3 (hình bên trái): vị trí 1, 3, 4, 5 có `followpos = {4, 5, 6}`; vị trí 2 là `{3}`; vị trí 6 là `{7}`; vị trí 7 là `{8}` — khớp với các giá trị trên Slide 54.*
> - *Đồ thị Direct DFA ở hình góc trên bên phải sinh trực tiếp **5 trạng thái tối giản A, B, C, D, E** khớp Slide 55–57.*
> - *Ngoài ra, cây mở rộng đa-token $(R_1\cdot\#_1)\mid\dots\mid(R_k\cdot\#_k)$ tạo Combined Direct DFA tương đương ngôn ngữ với Min-DFA trên cả 3 bộ đặc tả. Em xin nhường lời cho bạn thứ 3."*

---

#### SLIDE 7 — `05 · TRỰC QUAN HÓA AUTOMATA`: Đồ thị Combined Minimized DFA — Ngôn ngữ CalcLang (Thành viên 3 — 4:15 đến 4:55)
> *"Em xin trình bày Slide 7: Hình bên trái là đồ thị **Combined Minimized DFA** của ngôn ngữ **CalcLang (12 quy tắc token)** sau khi giảm từ 57 trạng thái $\varepsilon$-NFA $\to$ 26 NFA khử $\varepsilon$ $\to$ 24 Subset DFA $\to$ còn **20 trạng thái tối giản** (giảm 16,7%, đủ 190/190 cặp phân biệt Myhill-Nerode).*
>
> *Từ đồ thị này có thể quan sát hai cơ chế phân tích từ vựng:*
> 1. ***Từ khóa và Định danh***: *`KW_LET` $\subset$ `ID` (giao nhau trên từ tố `'let'`) nhưng được chọn nhờ độ ưu tiên; nếu sau `let` có thêm chữ hoặc số (như `letx`), DFA chuyển tiếp sang trạng thái `ID` theo nguyên tắc **Maximal Munch**.*
> 2. ***Số thực và Quay lui***: *Đọc chữ số vào `INT`, gặp dấu chấm `.` sang trạng thái trung gian, đọc tiếp chữ số mới vào `FLOAT`. Nếu gặp `3.` rồi kết thúc thì quay lui 1 bước về `INT("3")`."*

---

#### SLIDE 8 — `06 · BỘ QUÉT O(n) & SINH MÃ`: Maximal Munch $O(n)$ (Reps, 1998), Phục hồi lỗi và Sinh mã Lexer độc lập (Thành viên 3 — 4:55 đến 5:35)
> *"Slide 8 trình bày 3 cơ chế ở tầng thực thi và sinh mã:*
> - ***Thứ nhất — Bảng nhớ `failed_states` (Reps, 1998)***: *Lưu các cặp `(state, cursor)` đã biết không dẫn tới trạng thái kết thúc để dừng sớm trong $O(1)$, tránh quay lui bậc hai $O(n^2)$. Trên chuỗi chưa đóng dài 10.000 ký tự `"` + `\"`*5000, bộ quét thực hiện **5.000 lần cắt nhánh**.*
> - ***Thứ hai — Xử lý dòng CRLF và hai chế độ phục hồi lỗi***: *Quy tắc `STRING_LIT` loại trừ cả `\r` và `\n`, kết hợp tùy chọn giữa `Panic-mode` (tiến 1 ký tự) và `Smart-Sync` (gom chuỗi/bình luận chưa đóng).*
> - ***Thứ ba — Bộ sinh mã Lexer độc lập (`codegen.py`)***: *Xuất các mảng hằng `ASCII_CLASS_MAP[128]`, `UNICODE_CLASS_MAP`, `TRANSITIONS[78][44]` cùng vòng lặp Reps $O(n)$ ra một tệp Python độc lập (~527 dòng, không dùng `import re`), cho kết quả khớp với bộ phân tích gốc."*

---

#### SLIDE 9 — `07 · GIAO DIỆN & DEMO`: Giao diện Web 5 Tab và Kịch bản Demo trực tiếp (Thành viên 3 — 5:35 đến 7:15)
> *"Slide 9 giới thiệu giao diện Web 5 tab của chương trình. Tiếp theo em xin thao tác **Demo trực tiếp trên trình duyệt** qua 4 nội dung:*
> *(Chuyển sang cửa sổ trình duyệt)*
> 1. ***Tab 1 và Thanh công cụ***: *Quét mã nguồn UTF-8/CRLF, đổi giữa `Panic-mode` và `Smart-Sync`, xem mô phỏng quay lui trên `1.5e`, thử nút đổi chế độ `Dark` / `Light` và bấm `Xuất Lexer (.py)` để tải tệp bộ quét độc lập.*
> 2. ***Tab 2 (Ma trận giao nhau $L(R_i) \cap L(R_j)$ và Myhill-Nerode)***: *Mở thẻ con `Ma trận giao L(Rᵢ) ∩ L(Rⱼ)` xem bảng $39 \times 39$ (9/741 cặp giao nhau kèm chứng nhân) và bảng Myhill-Nerode 3.003/3.003 cặp.*
> 3. ***Tab 3 (Định lý Kleene và Slide 54)***: *Xem cây `r·#` của Slide 54 và mở thẻ con thứ 6 `GNFA khử trạng thái (DFA -> RE)` xem từng bước khử đỉnh.*
> 4. ***Tab 4 (Unicode động và Cảnh báo che khuất)***: *Bấm `+ Mẫu Unicode (nếu / €)` biên dịch lại, sau đó bấm `Thử che khuất` để quan sát cảnh báo quy tắc bị che khuất. Em xin mời bạn thứ 4 trình bày phần cuối."*

---

#### SLIDE 10 — `08 · KIỂM THỬ & BẤT BIẾN`: Kết quả Kiểm thử tự động (72/72 PASS · 22 Suites) và Đối chứng mã sinh (Thành viên 4 — 7:15 đến 7:50)
> *"Em xin tiếp tục ở Slide 10 về kết quả kiểm thử tự động:*
> - *4 ô thống kê phía trên tóm tắt kết quả: **72/72 ca kiểm thử JSON đạt** (20 mẫu RE/Unicode/GNFA, 24 mẫu lỗi cú pháp và giới hạn AST, 28 ca quét CRLF và ký tự điều khiển ASCII), **22/22 nhóm Unittest đạt**, **4.519/4.519 cặp trạng thái** phân biệt theo Myhill-Nerode, và kết quả **đối chứng khớp 100%** giữa bộ phân tích gốc với tệp Standalone Lexer `.py`.*
> - *Bảng bên dưới liệt kê các tính chất được kiểm tra tự động gồm đối hợp $\sim(\sim A) = A$ trên 128 ASCII + $\Sigma(U)$, đối chiếu $L(R_0) \equiv L(R_{\text{sinh}})$, chặn nhân bản AST `(((a{64}){64}){64})` và đọc/ghi khứ hồi JFLAP `.jff`."*

---

#### SLIDE 11 — `09 · THỰC NGHIỆM & PHÂN TÍCH`: Đối sánh các mô hình Otomat, Ma trận giao nhau và Hiệu năng $O(n)$ (Thành viên 4 — 7:50 đến 8:25)
> *"Slide 11 tổng hợp số liệu thực nghiệm trên 3 bộ đặc tả ngôn ngữ:*
> - ***MiniLang (39 token · 44 lớp $\Sigma$)***: *170 $\varepsilon$-NFA $\to$ 96 Khử $\varepsilon$ $\to$ 86 Subset $\to$ 79 Direct $\to$ **78 trạng thái Moore/Hopcroft Min-DFA** (-9,3%, 3.003/3.003 cặp, 9/741 cặp giao nhau có kiểm soát).*
> - ***CalcLang (12 token)***: *57 $\to$ 26 $\to$ 24 $\to$ 20 $\to$ **20 trạng thái Min-DFA** (-16,7%, 190/190 cặp, 2/66 cặp giao).*
> - ***MiniSQL (14 token)***: *128 $\to$ 67 $\to$ 64 $\to$ 52 $\to$ **52 trạng thái Min-DFA** (-18,8%, 1.326/1.326 cặp, 5/91 cặp giao).*
> - *Bảng nhớ `failed_states` cắt 5.000 nhánh quay lui lặp lại và xuất ra tệp `MiniLangLexer` độc lập dài khoảng 527 dòng."*

---

#### SLIDE 12 — `10 · ĐÁNH GIÁ & TỔ CHỨC NHÓM`: Giới hạn Lý thuyết (Bổ đề Bơm), Hướng phát triển và Phân công (Thành viên 4 — 8:25 đến 9:05)
> *"Ở Slide 12, bên cạnh các vấn đề kỹ thuật đã giải quyết trong cài đặt, nhóm phân tích **giới hạn lý thuyết của DFA theo Bổ đề Bơm (Pumping Lemma — Chương 3.2)**:*
> - *Bình luận nhiều dòng **lồng nhau tùy ý** `/* /* ... */ */` tương ứng với ngôn ngữ $L = \{a^n b^n \mid n \ge 1\}$. Theo Bổ đề Bơm, bộ nhớ hữu hạn trạng thái của DFA không đếm được độ sâu lồng nhau tùy ý nên cấu trúc này thuộc lớp **Ngôn ngữ phi ngữ cảnh (CFL — Chương 4)**.*
> - *Hướng phát triển tiếp theo là kết hợp ngăn xếp trạng thái ngữ cảnh từ vựng và nối luồng Token của tệp Lexer độc lập (`.py`) sang bộ phân tích cú pháp CFG `LL(1)` / `LR(1)`.*
> - *Khung bên phải là bảng phân công công việc của 4 thành viên cùng phần khai báo việc sử dụng công cụ AI hỗ trợ rà soát tài liệu và kiểm thử."*

---

#### SLIDE 13 — `KẾT LUẬN ĐỒ ÁN T13`: Tổng kết và Hỏi đáp Q&A (Thành viên 4 — 9:05 đến 9:30)
> *"Tổng kết ở Slide 13, đồ án T13 của Nhóm 6 tập trung vào 3 kết quả chính: (1) **Cài đặt quy trình hai chiều của Định lý Kleene** với 7 biểu diễn tương đương (không dùng `import re`); (2) **Đại số Boole trên $\Sigma(U)$ ($\sim(\sim A)=A$)**, giới hạn AST $\le 4096$, kiểm chứng Myhill-Nerode và **Ma trận giao nhau $L(R_i) \cap L(R_j)$**; (3) **72/72 test case JSON + 22 nhóm Unittest + Bộ sinh mã Lexer Python độc lập kiểu Flex**.*
>
> *Nhóm xin cảm ơn Cô Hồ Thị Thanh Tuyến và các bạn đã lắng nghe. Nhóm rất mong nhận được câu hỏi góp ý từ Cô và các bạn."*

---
---

## PHẦN B: 18 THẺ ÔN TẬP KIẾN THỨC CHƯƠNG 1 – CHƯƠNG 3

### Thẻ 1 — Bảng chữ cái động ($\Sigma(U)$), phép bù $\sim(\sim A) = A$, chuỗi ($w$) và ngôn ngữ ($L$) [Chương 1]
- **Bảng chữ cái động $\Sigma(U)$**: Tập hợp hữu hạn, khác rỗng gồm:
  $$\Sigma(U) = \text{ASCII\_SIGMA (128 mã 0x00..0x7F)} \;\cup\; U \;\cup\; \{\text{NON\_ASCII (U+FDD0)}\}$$
  trong đó $U$ là tập ký tự Unicode tường minh xuất hiện trong Regex (như `'ế'`, `'€'`), còn `U+FDD0` là điểm mã phi ký tự nội bộ đại diện cho các ký tự Unicode ngoài $U$.
- **Tính đối hợp của phép bù**: Nhờ bao phủ đủ 128 mã ASCII (kể cả `\0`, `\f`, `\v`, `\x7f`), mọi tập con $A \subseteq \Sigma(U)$ đều thỏa $\sim(\sim A) = A$.
- **Chuỗi $w$ và Ngôn ngữ $L$**: Chuỗi rỗng $\varepsilon$ có $|\varepsilon| = 0$; $L \subseteq \Sigma^*$.

---

### Thẻ 2 — Biểu thức chính quy (Regular Expression — RE) và thứ tự ưu tiên [Chương 2]
- **3 phép toán cơ sở**:
  1. **Hợp (Union)** $R_1 \mid R_2$: $L(R_1 \mid R_2) = L(R_1) \cup L(R_2)$ — ưu tiên thấp nhất.
  2. **Nối kết (Concatenation)** $R_1 \cdot R_2$: $L(R_1 R_2) = \{xy \mid x \in L(R_1), y \in L(R_2)\}$ — ưu tiên trung bình.
  3. **Bao đóng Kleene (Star)** $R^*$: $L(R^*) = \bigcup_{i \ge 0} L(R)^i$ — ưu tiên cao nhất (cùng với `+`, `?`, `{m,n}`).
- **Quy đổi toán tử mở rộng**: $R^+ \equiv R \cdot R^*$, $R? \equiv R \mid \varepsilon$, $R\{2,4\} \equiv R \cdot R \cdot (R \mid \varepsilon) \cdot (R \mid \varepsilon)$.

---

### Thẻ 3 — Phân biệt DFA, NFA và $\varepsilon$-NFA [Chương 3.1]
Cả 3 được xác định bởi bộ 5 thành phần $M = (Q, \Sigma, \delta, q_0, F)$, khác nhau ở hàm chuyển $\delta$:
1. **DFA**: $\delta: Q \times \Sigma \to Q$ (mỗi cặp $(q, a)$ có tối đa 1 trạng thái đích, không có cung $\varepsilon$).
2. **NFA**: $\delta: Q \times \Sigma \to \mathcal{P}(Q)$ (có thể đi tới nhiều trạng thái, không có cung $\varepsilon$).
3. **$\varepsilon$-NFA**: $\delta: Q \times (\Sigma \cup \{\varepsilon\}) \to \mathcal{P}(Q)$ (cho phép chuyển qua cung $\varepsilon$).
- Cả ba mô hình có khả năng biểu diễn tương đương, cùng nhận diện lớp Ngôn ngữ chính quy.

---

### Thẻ 4 — Định lý 3: Cấu trúc Thompson ($\text{RE} \to \varepsilon\text{-NFA}$, Slide 26–29)
- Mỗi mảnh $\varepsilon$-NFA con $N(s, f)$ có 1 đỉnh đầu $s$ (`in-deg = 0`), 1 đỉnh cuối $f$ (`out-deg = 0`), tối đa $2|R|$ trạng thái và bậc ra mỗi đỉnh $\le 2$.
- Ví dụ Slide 38: `(a|b)*abb` tạo ra **11 trạng thái ($q_0 \dots q_{10}$)**.

---

### Thẻ 5 — Định lý 2: Khử chuyển tiếp $\varepsilon$ ($\varepsilon\text{-NFA} \to \text{NFA}$, Slide 21–22)
- Công thức: $\delta'(q, a) = \varepsilon\text{-closure}(\text{move}(\varepsilon\text{-closure}(q), a))$ và $F' = \{q \in Q \mid \varepsilon\text{-closure}(q) \cap F \neq \emptyset\}$.
- Trên `(a|b)*abb`, số trạng thái giảm từ **11 xuống 6 trạng thái**.

---

### Thẻ 6 — Định lý 1: Đơn định hóa tập con — Subset Construction ($\text{NFA} \to \text{DFA}$, Slide 18–20)
- Công thức: $S_0 = \varepsilon\text{-closure}(\{q_0\})$ và $\delta_{\text{DFA}}(S, a) = \varepsilon\text{-closure}(\text{move}(S, a))$.
- Trên MiniLang (170 trạng thái $\varepsilon$-NFA), Subset DFA có **86 trạng thái**.

---

### Thẻ 7 — Phương pháp trực tiếp $\text{RE} \to \text{DFA}$ (`nullable`, `firstpos`, `lastpos`, `followpos`, Slide 37–54)
- Hai quy tắc cập nhật `followpos`:
  1. Tại nút nối $c_1 \cdot c_2$: với mọi $i \in \text{lastpos}(c_1)$, thêm $\text{firstpos}(c_2)$ vào $\text{followpos}(i)$.
  2. Tại nút lặp $c^*$ (hoặc $c^+$): với mọi $i \in \text{lastpos}(c)$, thêm $\text{firstpos}(c)$ vào $\text{followpos}(i)$.

---

### Thẻ 8 — Tối thiểu hóa DFA: Moore và Hopcroft [Chương 3.1]
- Phân hoạch đầu $\Pi_0$ của Lexer: $\Pi_0 = \{Q_{\text{non-accept}}\} \cup \{Q_{T_1}, Q_{T_2}, \dots, Q_{T_k}\}$ (tách riêng theo nhãn token).
- **Moore** $O(p \cdot |Q|^2)$ cho bảng vết từng vòng $\Pi_0 \to \Pi_k$; **Hopcroft** $O(p \cdot |Q| \log |Q|)$ chỉ đưa khối nhỏ hơn vào danh sách chờ $W$. Cả hai cho kết quả đẳng cấu (`MiniLang`: 78 TT).

---

### Thẻ 9 — Định lý Myhill-Nerode và kiểm tra tính tối giản
- Hai trạng thái $p, q$ phân biệt được khi tồn tại hậu tố $w \in \Sigma^*$ sao cho $\tau(\hat{\delta}(p, w)) \neq \tau(\hat{\delta}(q, w))$.
- Chương trình tìm chuỗi phân biệt ngắn nhất $w$ cho toàn bộ các cặp trạng thái (`3.003/3.003` cặp trên MiniLang).

---

### Thẻ 10 — Hai nguyên tắc của Bộ quét từ vựng: Maximal Munch và Priority Rule
1. **Maximal Munch (khớp dài nhất)**: Chọn tiền tố khớp dài nhất (`ifelse` $\to$ `IDENTIFIER`, `==` $\to$ `OP_EQ`).
2. **Priority Rule (ưu tiên luật đứng trước)**: Cùng độ dài tối đa thì chọn quy tắc có chỉ số ưu tiên nhỏ hơn (`if` $\to$ `KW_IF` ưu tiên hơn `IDENTIFIER`).

---

### Thẻ 11 — Thuật toán Reps (1998): Giữ độ phức tạp tuyến tính $O(n)$
- Lưu tập `failed_states` gồm các cặp `(state, cursor)` sau `last_accept_pos` đã chứng minh không đi tới trạng thái kết thúc.
- Khi gặp lại `(state, cursor) in failed_states`, dừng nhánh ngay trong $O(1)$ nên tổng số bước dò thất bại không vượt quá $|Q| \cdot n = O(n)$.

---

### Thẻ 12 — Quy tắc bị che khuất (Shadowed Rules) và Ma trận giao nhau $L(R_i) \cap L(R_j)$
- **Shadowed Rule**: Quy tắc $T_j$ không xuất hiện ở bất kỳ trạng thái kết thúc nào của `Min-DFA` ($L(R_j) \subseteq \bigcup_{i < j} L(R_i)$).
- **Ma trận giao nhau $L(R_i) \cap L(R_j)$**: Dùng Product Automaton BFS xét từng cặp $D_i \times D_j$, phân loại $\varnothing, \subset, \equiv, \supset, \cap$ và tìm chuỗi chứng nhân ngắn nhất (`MiniLang`: 9/741 cặp giao nhau có kiểm soát, 732 cặp rời nhau).

---

### Thẻ 13 — Bình luận `/* ... */` và Bổ đề Bơm cho bình luận lồng nhau
- Viết `/\*([^*]|\*+[^*/])*\*+/` thay vì `/\*.*\*/` để Maximal Munch dừng đúng ở dấu `*/` đầu tiên.
- Bình luận lồng nhau tùy ý `/* /* ... */ */` tương ứng $L = \{a^n b^n \mid n \ge 1\}$: theo Bổ đề Bơm Chương 3.2, với $w = a^p b^p$, chuỗi bơm $xy^2z = a^{p+k}b^p \notin L$ nên thuộc lớp CFL (Chương 4).

---

### Thẻ 14 — Kiểm tra tương đương 2 DFA bằng Product Automaton BFS
- Duyệt BFS trên $D_1 \times D_2$ từ $(q_{01}, q_{02})$ theo bảng chữ cái chung $\Sigma(U_1 \cup U_2)$. Nếu gặp cặp lệch nhãn chấp nhận thì trả về chuỗi phản ví dụ ngắn nhất; nếu duyệt hết không có mâu thuẫn thì $L(D_1) \equiv L(D_2)$.

---

### Thẻ 15 — Chiều ngược Định lý Kleene: Khử trạng thái GNFA (`DFA -> RE`)
- Thêm $q_{\text{start}} \xrightarrow{\varepsilon} D_0$ và $\forall f \in F: f \xrightarrow{\varepsilon} q_{\text{accept}}$.
- Lần lượt khử từng đỉnh trung gian $q_{\text{rip}}$ (ưu tiên $\text{in\_deg} \times \text{out\_deg}$ nhỏ nhất) theo công thức:
  $$R'(q_i, q_j) = R(q_i, q_j) \;\mid\; R(q_i, q_{\text{rip}}) \cdot \big(R(q_{\text{rip}}, q_{\text{rip}})\big)^* \cdot R(q_{\text{rip}}, q_j)$$
- Trên `(a|b)*abb` (4 TT): sinh biểu thức `b*a(a|ba|bb(a|b+a))*bb` tương đương $R_{\text{gốc}}$.

---

### Thẻ 16 — Giới hạn kích thước cây cú pháp AST (`MAX_AST_NODES = 4096`)
- Biểu thức định lượng lồng nhau `(((a{64}){64}){64})` có thể nhân bản cây cú pháp lên $64^3 \approx 528.483$ nút dù mỗi bậc đơn lẻ không vượt 64.
- `regex_parser.py` ước lượng kích thước cây con trong $O(1)$ trước khi nhân bản và dừng ngay khi vượt `MAX_AST_NODES = 4096`.

---

### Thẻ 17 — Bộ sinh mã Lexer độc lập kiểu Flex (`codegen.py` / `cli.py codegen`)
- Lệnh `python3 cli.py codegen --preset minilang -o minilang_lexer.py` xuất các bảng tĩnh `ASCII_CLASS_MAP[128]`, `UNICODE_CLASS_MAP`, `TRANSITIONS[78][44]`, `ACCEPT_TABLE` và vòng lặp Reps $O(n)$ thành 1 tệp `.py` độc lập (~527 dòng, không dùng `import re`), khớp đầu ra với bộ phân tích gốc.

---

### Thẻ 18 — Bảng tóm tắt số liệu thực nghiệm chính
- **Mẫu bài giảng 1 `(a|b)*abb` (Slide 38)**: Thompson = **11** $\to$ Khử $\varepsilon$ = **6** $\to$ Subset = **5** $\to$ Min-DFA = **4** TT $\to$ GNFA sinh `b*a(a|ba|bb(a|b+a))*bb` ($\equiv R_{\text{gốc}}$).
- **Mẫu bài giảng 2 `(a|ba)(a|b)*ba#` (Slide 54)**: **8** vị trí lá, bảng `followpos` khớp Slide 54, Direct DFA = **5** TT (**A..E**).
- **MiniLang (39 quy tắc)**: $\varepsilon$-NFA = **170** $\to$ Khử $\varepsilon$ = **96** $\to$ Subset = **86** $\to$ Direct = **79** $\to$ Moore/Hopcroft Min-DFA = **78** TT (**44** lớp $\Sigma$, **3.003/3.003** cặp Myhill-Nerode, **9/741** cặp giao nhau).
- **CalcLang (12 quy tắc)**: **57** $\to$ **26** $\to$ **24** $\to$ **20** $\to$ **20** TT (**19** lớp $\Sigma$, **190/190** cặp, **2/66** cặp giao).
- **MiniSQL (14 quy tắc)**: **128** $\to$ **67** $\to$ **64** $\to$ **52** $\to$ **52** TT (**44** lớp $\Sigma$, **1.326/1.326** cặp, **5/91** cặp giao).
- **Kiểm thử**: **72/72** test cases JSON + **22/22** nhóm unittest đạt, **0** `import re`, Báo cáo PDF **13 trang**.
