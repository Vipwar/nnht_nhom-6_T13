# LỜI THOẠI THUYẾT TRÌNH KHỚP TỪNG SLIDE (13 SLIDES — 9 PHÚT 30 GIÂY) & FLASHCARD ÔN TẬP CHƯƠNG 1–3

> **Tài liệu này gồm 2 phần:**
> - **PHẦN A:** Lời thoại chi tiết từng câu **khớp chính xác 100% với tiêu đề và bố cục của 13 Slide** trong file [`deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx) (đồng thời đã được nhúng sẵn vào **Speaker Notes** của từng slide trong file PowerPoint để xem trực tiếp ở chế độ *Presenter View* `Alt + F5`).
> - **PHẦN B:** **18 Flashcard Ôn tập Cốt lõi Chương 1 – Chương 3 & Nâng cấp v2.0** (Ngôn ngữ hình thức UEH) giải thích từ gốc giúp mọi thành viên trả lời tự tin bất kỳ câu hỏi lý thuyết hay thực nghiệm nào.

---

## PHẦN A: PHÂN CÔNG & LỜI THOẠI CHI TIẾT 13 SLIDES (9 PHÚT 30 GIÂY)

### Bảng phân công 4 thành viên (Chia đều thời lượng + Kết hợp Live Demo mượt mà)

| Thành viên | Phụ trách Slide | Thời lượng | Nội dung chính |
| :--- | :--- | :---: | :--- |
| **Thành viên 1** | **Slide 1, 2, 3** | **2 phút 00 giây** | Mở đầu, bài toán Lexical Analysis & 4 mục tiêu v2.0, mô hình Đa-Token + Unicode Động $\Sigma(U)$, bù kép $\sim(\sim A)=A$ & Ma trận giao nhau |
| **Thành viên 2** | **Slide 4, 5, 6** | **2 phút 15 giây** | Kiến trúc v2.0 Kleene 360°, kiểm chứng Slide 38 `(a|b)*abb` + GNFA (`DFA → RE`) và Slide 54 `(a|ba)(a|b)*ba#` (`followpos`) |
| **Thành viên 3** | **Slide 7, 8, 9 + Live Demo** | **3 phút 00 giây** | Đồ thị Combined Min-DFA CalcLang (20 TT), Bộ quét $O(n)$ Reps (1998) + Flex Codegen (`.py`), và **Live Demo Web Studio 5 Tab** |
| **Thành viên 4** | **Slide 10, 11, 12, 13** | **2 phút 15 giây** | Bộ kiểm thử 72/72 PASS + 22 Suites & đối chứng vi sai, Benchmark 3 ngôn ngữ, Bổ đề Bơm (Chương 3.2), phân công & kết luận |

---

### LỜI THOẠI TỪNG SLIDE (Khớp từng thẻ, bảng và sơ đồ trên Slide)

#### SLIDE 1 — Trang bìa: AUTOMATA-BASED LEXICAL ANALYZER (Thành viên 1 — 0:00 đến 0:30)
> *"Em xin kính chào Cô và các bạn. Hôm nay Nhóm 6 chúng em xin trình bày báo cáo đồ án cuối kỳ môn Ngôn ngữ hình thức với đề tài **T13: Automata-based Lexical Analyzer — Xây dựng Bộ phân tích từ vựng tổng quát khép kín vòng tròn Định lý Kleene 360°**.*
>
> *Như hiển thị ở khung Điểm nổi bật v2.0 bên phải slide, toàn bộ hệ thống của nhóm được lập trình **100% từ gốc bằng Python Standard Library**, tuyệt đối **không sử dụng thư viện `import re`**, phân hoạch bảng chữ cái Unicode động $\Sigma(U)$ bảo toàn đại số Boole $\sim(\sim A) = A$, tích hợp **GNFA (`DFA → RE`)**, **Ma trận Giao nhau $L(R_i) \cap L(R_j)$**, **Bộ sinh mã Lexer độc lập kiểu Flex** và vượt qua tuyệt đối **72/72 kịch bản kiểm thử** cùng **22 bộ Unittest**."*

---

#### SLIDE 2 — `01 · ĐẶT VẤN ĐỀ`: Bài toán Phân tích Từ vựng & Mục tiêu Đồ án T13 (v2.0) (Thành viên 1 — 0:30 đến 1:15)
> *"Bước sang Slide 2: Trong kiến trúc trình biên dịch, **Lexical Analyzer** là cầu nối đầu tiên chuyển dòng ký tự mã nguồn thô thành luồng **Token**, đồng thời lọc bỏ khoảng trắng, bình luận `//` và `/*...*/`, cũng như phát hiện lỗi từ vựng kèm tọa độ dòng, cột.*
>
> *Tại sao chúng ta dùng Ô-tô-mát hữu hạn? Bởi mọi lớp token từ vựng đều thuộc lớp **Ngôn ngữ chính quy** — đặc tả bằng Biểu thức chính quy và quét bằng DFA trong thời gian tuyến tính chặt $O(n)$, miễn nhiễm hoàn toàn với lỗi treo máy ReDoS $O(2^n)$.*
>
> *Từ đó, nhóm đặt ra **4 mục tiêu đột phá** ở cột bên phải:*
> 1. *Zero `import re`, đại số Boole $\Sigma(U)$ trên 128 ASCII & chống bom nhân bản AST `MAX_AST_NODES = 4096`.*
> 2. *Khép kín vòng tròn **Kleene 360°** với GNFA (`DFA → RE`), chứng minh **Myhill–Nerode** & **Ma trận Giao nhau $L(R_i) \cap L(R_j)$**.*
> 3. *Bộ quét tuyến tính $O(n)$ theo **Reps (1998)**, chuỗi `STRING_LIT` an toàn CRLF & sinh file **Lexer Python độc lập kiểu Flex**.*
> 4. *Xây dựng **Web Studio 5 Tab** trực quan cùng bộ **72 test cases JSON** và **22 bộ unittest**."*

---

#### SLIDE 3 — `02 · MÔ HÌNH HÌNH THỨC`: Mô hình Đa-Token, Phân hoạch Unicode Động $\Sigma(U)$ & Ma trận Giao $L(R_i) \cap L(R_j)$ (Thành viên 1 — 1:15 đến 2:00)
> *"Trên Slide 3 là 3 trụ cột hình thức mở rộng ô-tô-mát đơn lẻ sang bộ phân loại **Đa-Token**:*
> - ***Thẻ 1 (Combined $\varepsilon$-NFA & Khử $\varepsilon$)***: *Ghép $k$ mảnh $\varepsilon$-NFA con qua đỉnh khởi đầu chung $q_{\text{start}}$, đồng thời cài đặt **Định lý 2 (Slide 21–22)** khử toàn bộ cung $\varepsilon$, giúp MiniLang rút gọn từ 170 xuống 96 trạng thái NFA.*
> - ***Thẻ 2 (Subset DFA & Ma trận Giao nhau $L(R_i) \cap L(R_j)$)***: *Nén $\Sigma(U)$ thành 44 lớp tương đương trên MiniLang; đồng thời quét tĩnh toàn bộ $\binom{39}{2} = 741$ cặp quy tắc để chỉ ra đúng 9 cặp từ khóa bao hàm trong `IDENTIFIER` kèm từ tố chứng nhân ngắn nhất (`'if'..'true'`).*
> - ***Thẻ 3 (Moore/Hopcroft, Myhill–Nerode & GNFA 360°)***: *Phân hoạch $\Pi_0$ theo từng nhãn token chiến thắng, chứng minh Myhill–Nerode trên 3.003/3.003 cặp, và dùng GNFA khử trạng thái chuyển ngược DFA về RE.*
> - *Ở khung dưới cùng, bảng chữ cái động $\Sigma(U) = 128\text{ ASCII} \cup U \cup \{\text{NON\_ASCII } \text{U+FDD0}\}$ bảo toàn đối hợp $\sim(\sim A) = A$, cho phép dùng trực tiếp từ khóa tiếng Việt `nếu`, ký hiệu `€` mà không va chạm `NON_ASCII`, đồng thời chặn bom AST lồng nhau `(((a{64}){64}){64})` bằng ngưỡng `MAX_AST_NODES = 4096`. Em xin nhường lời cho bạn thứ 2."*

---

#### SLIDE 4 — `03 · KIẾN TRÚC HỆ THỐNG`: Đường ống Biên dịch v2.0 — Vòng tròn Kleene 360° & Bộ Sinh Mã Lexer (Thành viên 2 — 2:00 đến 2:40)
> *"Em xin tiếp tục ở Slide 4 với kiến trúc v2.0 khép kín vòng tròn Định lý Kleene 360°.*
>
> *Từ tập quy tắc biểu thức chính quy đầu vào:*
> - ***Nhánh chuẩn bên trên*** *đi qua chuỗi 4 định lý Chương 3.1: Bộ phân tích cú pháp RE ($\le 4096$ nút, $\Sigma(U)$) $\to$ **Thompson $\varepsilon$-NFA** (Định lý 3) $\to$ **NFA Khử $\varepsilon$** (Định lý 2) $\to$ **Subset DFA** (44 lớp $\Sigma$) $\to$ tối thiểu hóa song song bằng cả **Moore** và **Hopcroft**.*
> - ***Nhánh đối chứng & chiều ngược Kleene bên dưới*** *đi trực tiếp từ cây cú pháp gia tố $r\cdot\#$ qua bảng `followpos` để sinh **Direct DFA**, đồng thời dùng thuật toán **GNFA State Elimination** chuyển ngược Min-DFA về biểu thức chính quy $R_{\text{sinh}}$ và chứng minh $L(R_0) \equiv L(R_{\text{sinh}})$.*
> - *Ở đầu ra, Min-DFA vừa vận hành trực tiếp bộ quét $O(n)$, vừa được mô-đun `codegen.py` đóng gói thành một file **Lexer Python độc lập kiểu Flex**."*

---

#### SLIDE 5 — `04 · THUẬT TOÁN CỐT LÕI (1/2)`: RE $\to$ Thompson $\to$ Khử $\varepsilon$ $\to$ Subset $\to$ Min-DFA $\to$ GNFA RE (Slide 38 UEH) (Thành viên 2 — 2:40 đến 3:25)
> *"Sang Slide 5 là kết quả kiểm chứng vòng tròn Kleene 360° trên biểu thức kinh điển `(a|b)*abb` ở **Slide 38 Chương 3.1 bài giảng UEH**:*
> - ***Hình (a) Thompson $\varepsilon$-NFA***: *Nhờ bất biến $\text{in-deg}(\text{start})=0$ và $\text{out-deg}(\text{end})=0$, phép nối kết gộp trực tiếp đỉnh nối và sinh ra **đúng 11 trạng thái ($q_0 \dots q_{10}$)** khớp tuyệt đối Slide 38 của Cô.*
> - ***Bước Khử $\varepsilon$ theo Định lý 2 (Slide 21–22)***: *Loại bỏ hoàn toàn cung $\varepsilon$, rút gọn từ 11 xuống **6 trạng thái NFA**.*
> - ***Hình (b) & (c) Subset $\to$ Min-DFA***: *5 tập con $D_0 \dots D_4$ gộp $D_0 \equiv D_2$ còn **4 trạng thái tối giản** (đủ 6/6 cặp Myhill–Nerode).*
> - ***Bước GNFA (`DFA → RE`)***: *Khử lần lượt $D_2, D_0, D_3, D_1$ sinh biểu thức `b*a(a|ba|bb(a|b+a))*bb`, và Product Automaton chứng minh tự động $L(R_{\text{gốc}}) \equiv L(R_{\text{sinh}})$!"*

---

#### SLIDE 6 — `04 · THUẬT TOÁN CỐT LÕI (2/2)`: Nhánh đối chứng Direct RE $\to$ DFA Đơn lẻ & Đa-Token (Slide 46–57) (Thành viên 2 — 3:25 đến 4:15)
> *"Ở Slide 6 là nhánh đối chứng **Direct RE $\to$ DFA** theo Mục 2.5 (Slide 46–57 bài giảng).*
>
> *Khi kiểm chứng với biểu thức bài giảng `r = (a|ba)(a|b)*ba#`:*
> - *Hệ thống đánh số **8 nút lá** và xuất bảng `followpos` trên giao diện Web Tab 3 (hình bên trái): vị trí 1, 3, 4, 5 có `followpos = {4, 5, 6}`; vị trí 2 là `{3}`; vị trí 6 là `{7}`; vị trí 7 là `{8}` — **khớp 100% từng con số với Slide 54 bài giảng**, kèm huy hiệu xác nhận **Kleene 360°**!*
> - *Từ đó đồ thị Direct DFA ở hình góc trên bên phải sinh trực tiếp **5 trạng thái tối giản A, B, C, D, E** khớp Slide 55–57.*
> - *Đặc biệt, mở rộng Đa-Token $(R_1\cdot\#_1)\mid\dots\mid(R_k\cdot\#_k)$ sinh Combined Direct DFA tương đương 100% với Min-DFA trên cả 3 ngôn ngữ. Em xin chuyển cho bạn thứ 3."*

---

#### SLIDE 7 — `05 · TRỰC QUAN HÓA AUTOMATA`: Minh họa Combined Minimized DFA Hoàn chỉnh — Ngôn ngữ CalcLang (Thành viên 3 — 4:15 đến 4:55)
> *"Em xin trình bày Slide 7: Hình bên trái là đồ thị **Combined Minimized DFA** hoàn chỉnh của ngôn ngữ **CalcLang (12 quy tắc token)** sau khi nén từ 57 trạng thái $\varepsilon$-NFA $\to$ 26 NFA khử $\varepsilon$ $\to$ 24 Subset DFA $\to$ còn **20 trạng thái tối giản** (giảm 16,7%, đủ 190/190 cặp phân biệt Myhill–Nerode).*
>
> *Nhìn vào đồ thị này, ta thấy rõ 2 bài toán cốt lõi:*
> 1. ***Từ khóa vs Định danh***: *`KW_LET` $\subset$ `ID` (giao nhau trên từ tố chứng nhân `'let'`) nhưng thắng nhờ Priority; nếu sau `let` còn chữ/số (ví dụ `letx`), DFA rẽ ngay sang `ID` theo nguyên tắc **Maximal Munch**.*
> 2. ***Số thực & Quay lui***: *Đọc chữ số vào `INT`, gặp dấu chấm `.` sang trạng thái trung gian, đọc tiếp chữ số mới vào `FLOAT`. Gặp `3.` dừng ở trạng thái trung gian rồi quay lui 1 bước về `INT("3")`!"*

---

#### SLIDE 8 — `06 · BỘ QUÉT O(n) & CODEGEN`: Maximal Munch $O(n)$ (Reps, 1998), Phục hồi lỗi & Sinh Lexer Độc lập Kiểu Flex (Thành viên 3 — 4:55 đến 5:35)
> *"Sang Slide 8 là 3 cơ chế nổi bật ở tầng thực thi và sinh mã:*
> - ***Thứ nhất — Bảng nhớ `failed_states` (Reps, 1998)***: *Ghi nhớ các cấu hình `(state, cursor)` không dẫn tới trạng thái kết thúc để cắt nhánh $O(1)$ chống quay lui bậc hai $O(n^2)$. Chuỗi lỗi 10.000 ký tự `"` + `\"`*5000 kích hoạt đúng **5.000 lần cắt nhánh**!*
> - ***Thứ hai — An toàn Windows CRLF & Phục hồi lỗi kép***: *Quy tắc `STRING_LIT` loại trừ cả `\r` lẫn `\n`, kết hợp công tắc chuyển đổi trực tiếp giữa `Panic-mode` và `Smart-Sync`.*
> - ***Thứ ba — Bộ sinh mã Lexer Độc lập kiểu Flex (`codegen.py`)***: *Đóng gói các mảng tĩnh `ASCII_CLASS_MAP[128]`, `UNICODE_CLASS_MAP`, `TRANSITIONS[78][44]` và vòng lặp Reps $O(n)$ thành 1 file Python hoàn toàn độc lập (~527 dòng, Zero `import re`) khớp 100% luồng token với engine gốc!"*

---

#### SLIDE 9 — `07 · TRÌNH DIỄN SẢN PHẨM`: Giao diện Trực quan LexAutomata Studio 5 Tab & Live Demo (Thành viên 3 — 5:35 đến 7:15)
> *"Ở Slide 9 là giao diện **LexAutomata Studio 5 Tab**. Ngay bây giờ em xin thao tác **Live Demo trực tiếp trên trình duyệt** theo 4 bước:*
> *(Chuyển sang cửa sổ trình duyệt Web Studio)*
> 1. ***Tab 1 & Thanh công cụ***: *Quét mã UTF-8/CRLF, gạt công tắc `Panic-mode` vs `Smart-Sync`, chiếu hoạt ảnh quay lui `1.5e`, và bấm nút **`⬇ Sinh Lexer (.py)`** tải ngay file bộ quét Python độc lập.*
> 2. ***Tab 2 (Ma trận Giao nhau $L(R_i) \cap L(R_j)$ & Myhill–Nerode)***: *Mở thẻ con **Ma Trận Giao Nhau** xem bản đồ nhiệt $39 \times 39$ (chỉ ra đúng 9/741 cặp giao nhau kèm chứng nhân) và bảng Myhill–Nerode 3.003/3.003 cặp.*
> 3. ***Tab 3 (Vòng tròn Kleene 360° & Slide 54)***: *Xem cây `r#` Slide 54 và mở thẻ con thứ 6 **GNFA Khử Trạng Thái (`DFA → RE · Kleene 360°`)** xem từng bước khử đỉnh.*
> 4. ***Tab 4 (Unicode Động & Bẫy Luật Che Khuất)***: *Bấm **`+ Thêm Unicode (nếu / €)`** biên dịch tức thì, rồi bấm **`⚠ Thử Che Khuất`** để hệ thống bật ngay **Cảnh báo Đỏ Shadowed Rule**! Em xin nhường lời cho bạn thứ 4."*

---

#### SLIDE 10 — `08 · KIỂM THỬ & BẤT BIẾN`: Bộ Kiểm thử Không Lỗ Hổng (72/72 PASS · 22 Suites) & Đối chứng Vi sai (Thành viên 4 — 7:15 đến 7:50)
> *"Em xin tiếp tục ở Slide 10 về hệ thống kiểm thử tự động phiên bản v2.0:*
> - *4 chỉ số KPI hàng trên tóm tắt kết quả kiểm định: **72/72 kịch bản JSON PASS (100%)** (20 mẫu RE/Unicode/GNFA, 24 bẫy lỗi & bom AST, 28 ca quét CRLF & điều khiển ASCII), **22/22 bộ Unittest OK**, **4.519/4.519 cặp trạng thái** Myhill–Nerode phân biệt đôi một, và **100% trùng khớp vi sai** giữa Engine gốc với file Standalone Lexer `.py`.*
> - *Như bảng bên dưới, hệ thống kiểm chứng tự động cả luật đối hợp đại số Boole $\sim(\sim A) = A$ trên 128 ASCII + $\Sigma(U)$, vòng tròn Kleene 360° $L(R_0) \equiv L(R_{\text{sinh}})$, chống bom AST `(((a{64}){64}){64})` và khứ hồi JFLAP `.jff`."*

---

#### SLIDE 11 — `09 · THỰC NGHIỆM & PHÂN TÍCH`: Đánh giá Đa-Otomat, Ma trận Giao nhau & Hiệu năng Tuyến tính $O(n)$ (Thành viên 4 — 7:50 đến 8:25)
> *"Slide 11 trình bày kết quả thực nghiệm trên cả 3 ngôn ngữ đặc tả:*
> - ***MiniLang (39 token · 44 lớp $\Sigma$)***: *170 $\varepsilon$-NFA $\to$ 96 Khử $\varepsilon$ $\to$ 86 Subset $\to$ 79 Direct $\to$ **78 trạng thái Moore/Hopcroft Min-DFA** (-9,3%, 3.003/3.003 cặp, 9/741 cặp giao nhau hợp lệ).*
> - ***CalcLang (12 token)***: *57 $\to$ 26 $\to$ 24 $\to$ 20 $\to$ **20 trạng thái Min-DFA** (-16,7%, 190/190 cặp, 2/66 cặp giao).*
> - ***MiniSQL (14 token)***: *128 $\to$ 67 $\to$ 64 $\to$ 52 $\to$ **52 trạng thái Min-DFA** (-18,8%, 1.326/1.326 cặp, 5/91 cặp giao).*
> - *Bảng nhớ `failed_states` cắt đúng 5.000 nhánh quay lui dư thừa và xuất gọn gàng thành file `MiniLangLexer` độc lập chỉ ~527 dòng."*

---

#### SLIDE 12 — `10 · ĐÁNH GIÁ & TỔ CHỨC NHÓM`: Giới hạn Lý thuyết (Bổ đề Bơm), Hướng phát triển & Phân công (Thành viên 4 — 8:25 đến 9:05)
> *"Ở Slide 12, bên cạnh các lỗ hổng kỹ thuật tinh vi đã vá triệt để ở v2.0, nhóm phân tích rõ **giới hạn lý thuyết của DFA theo Bổ đề Bơm (Pumping Lemma — Chương 3.2)**:*
> - *Bình luận nhiều dòng **lồng nhau sâu tùy ý** `/* /* ... */ */` đẳng cấu với ngôn ngữ $L = \{a^n b^n \mid n \ge 1\}$. Theo Bổ đề Bơm, bộ nhớ hữu hạn trạng thái của DFA không thể đếm độ sâu lồng nhau tùy ý nên thuộc lớp **Ngôn ngữ phi ngữ cảnh (CFL — Chương 4)**.*
> - *Hướng phát triển tiếp theo là bổ sung ngăn xếp ngữ cảnh từ vựng và đưa luồng Token của file Lexer độc lập (`.py`) vào bộ phân tích cú pháp CFG `LL(1)` / `LR(1)`.*
> - *Khung bên phải trình bày bảng phân công đồng đều 25% cho 4 thành viên cùng khai báo minh bạch việc sử dụng công cụ AI hỗ trợ rà soát, kiểm định."*

---

#### SLIDE 13 — `KẾT LUẬN ĐỒ ÁN T13 — VERSION 2.0 ULTIMATE`: Tổng kết & Hỏi đáp Q&A (Thành viên 4 — 9:05 đến 9:30)
> *"Khép lại ở Slide 13, đồ án T13 v2.0 Ultimate của Nhóm 6 hội tụ 3 trụ cột: (1) **Khép kín vòng tròn Định lý Kleene 360°** với 7 biểu diễn tương đương (Zero `import re`); (2) **Đại số Boole $\Sigma(U)$ ($\sim(\sim A)=A$)**, chống bom AST $\le 4096$, Myhill–Nerode & **Ma trận Giao nhau $L(R_i) \cap L(R_j)$**; và (3) **72/72 PASS + 22 Unittest Suites + Bộ sinh mã Lexer Python độc lập kiểu Flex**.*
>
> *Nhóm chúng em xin chân thành cảm ơn Cô Hồ Thị Thanh Tuyến và các bạn đã lắng nghe. Nhóm rất hân hạnh được đón nhận các câu hỏi phản biện từ Cô và các bạn!"*

---
---

## PHẦN B: 18 FLASHCARD ÔN TẬP LÝ THUYẾT CHƯƠNG 1 – CHƯƠNG 3 & v2.0 (DỄ HIỂU 100% CHO MỌI THÀNH VIÊN)

> **Cách học nhanh:** Mỗi thành viên chỉ cần đọc qua 18 thẻ ngắn gọn dưới đây trong 15 phút là hiểu bản chất từng khái niệm từ Chương 1 đến Chương 3 và toàn bộ nâng cấp v2.0, sẵn sàng trả lời bất kỳ câu hỏi nào của Giảng viên.

---

### Thẻ 1 — Bảng chữ cái Động ($\Sigma(U)$), Đại số Boole $\sim(\sim A) = A$, Chuỗi ($w$) và Ngôn ngữ ($L$) [Chương 1 + v2.0]
- **Bảng chữ cái động $\Sigma(U)$**: Tập hợp **hữu hạn, khác rỗng** gồm:
  $$\Sigma(U) = \text{ASCII\_SIGMA (128 mã 0x00..0x7F)} \;\cup\; U \;\cup\; \{\text{NON\_ASCII (U+FDD0)}\}$$
  trong đó $U$ là tập ký tự Unicode tường minh xuất hiện trong Regex (như `'ế'`, `'€'`), và `U+FDD0` là mã noncharacter nội bộ đại diện cho mọi ký tự Unicode còn lại ngoài $U$.
- **Luật đối hợp đại số Boole**: Nhờ phủ kín toàn bộ 128 mã ASCII (gồm cả `\0`, `\f`, `\v`, `\x7f`), mọi tập con $A \subseteq \Sigma(U)$ đều thỏa mãn tuyệt đối $\sim(\sim A) = A$!
- **Chuỗi $w$ & Ngôn ngữ $L$**: Chuỗi rỗng $\varepsilon$ có $|\varepsilon| = 0$; $L \subseteq \Sigma^*$.

---

### Thẻ 2 — Biểu thức chính quy (Regular Expression — RE) và Thứ tự ưu tiên [Chương 2]
- **3 phép toán cơ bản của RE**:
  1. **Hợp (Union)** $R_1 \mid R_2$: $L(R_1 \mid R_2) = L(R_1) \cup L(R_2)$ — ưu tiên **thấp nhất**.
  2. **Nối kết (Concatenation)** $R_1 \cdot R_2$: $L(R_1 R_2) = \{xy \mid x \in L(R_1), y \in L(R_2)\}$ — ưu tiên **trung bình**.
  3. **Bao đóng Kleene (Star)** $R^*$: $L(R^*) = \bigcup_{i \ge 0} L(R)^i$ — ưu tiên **cao nhất** (cùng với `+`, `?`, `{m,n}`).
- **Các phép toán mở rộng đều quy về 3 phép toán gốc**:
  - $R^+ \equiv R \cdot R^*$, $R? \equiv R \mid \varepsilon$, $R\{2,4\} \equiv R \cdot R \cdot (R \mid \varepsilon) \cdot (R \mid \varepsilon)$.

---

### Thẻ 3 — Phân biệt DFA, NFA và $\varepsilon$-NFA (Bộ 5 thành phần) [Chương 3.1]
Cả 3 đều được định nghĩa bởi bộ 5 thành phần $M = (Q, \Sigma, \delta, q_0, F)$, chỉ khác nhau ở **hàm chuyển trạng thái $\delta$**:
1. **DFA (Đơn định)**: $\delta: Q \times \Sigma \to Q$ (mỗi cặp $(q, a)$ đi tới **tối đa 1** trạng thái duy nhất, **không** có cung $\varepsilon$).
2. **NFA (Không đơn định, không $\varepsilon$)**: $\delta: Q \times \Sigma \to \mathcal{P}(Q)$ (mỗi cặp $(q, a)$ có thể đi tới **nhiều** trạng thái, **không** có cung $\varepsilon$).
3. **$\varepsilon$-NFA (Không đơn định có $\varepsilon$)**: $\delta: Q \times (\Sigma \cup \{\varepsilon\}) \to \mathcal{P}(Q)$ (cho phép chuyển tự do qua cung $\varepsilon$).
- **Khả năng biểu diễn**: Tương đương hoàn toàn — cùng nhận diện đúng lớp **Ngôn ngữ chính quy**.

---

### Thẻ 4 — Định lý 3: Thuật toán Thompson ($\text{RE} \to \varepsilon\text{-NFA}$, Slide 26–29)
- **Đặc trưng**: Mỗi mảnh $\varepsilon$-NFA con $N(s, f)$ luôn có đúng **1 đỉnh bắt đầu $s$** (`in-deg = 0`), **1 đỉnh kết thúc $f$** (`out-deg = 0`), tối đa $2|R|$ trạng thái và bậc ra mỗi đỉnh $\le 2$.
- **Ví dụ bài giảng**: `(a|b)*abb` sinh ra đúng **11 trạng thái ($q_0 \dots q_{10}$)**.

---

### Thẻ 5 — Định lý 2: Khử chuyển tiếp $\varepsilon$ ($\varepsilon\text{-NFA} \to \text{NFA}$, Slide 21–22)
- **Công thức**: $\delta'(q, a) = \varepsilon\text{-closure}(\text{move}(\varepsilon\text{-closure}(q), a))$ và $F' = \{q \in Q \mid \varepsilon\text{-closure}(q) \cap F \neq \emptyset\}$.
- **Ví dụ bài giảng**: Trên `(a|b)*abb`, số trạng thái giảm từ **11 xuống 6 trạng thái**.

---

### Thẻ 6 — Định lý 1: Thuật toán Tập con — Subset Construction ($\text{NFA} \to \text{DFA}$, Slide 18–20)
- **Công thức**: $S_0 = \varepsilon\text{-closure}(\{q_0\})$ và $\delta_{\text{DFA}}(S, a) = \varepsilon\text{-closure}(\text{move}(S, a))$.
- **Thực tế**: Trên MiniLang (170 trạng thái $\varepsilon$-NFA), Subset DFA chỉ sinh ra **86 trạng thái**!

---

### Thẻ 7 — Phương pháp Trực tiếp $\text{RE} \to \text{DFA}$ (`nullable`, `firstpos`, `lastpos`, `followpos`, Slide 37–54)
- **Chỉ có 2 nơi sinh ra `followpos`**:
  1. Tại nút nối $c_1 \cdot c_2$: $\forall i \in \text{lastpos}(c_1)$, thêm $\text{firstpos}(c_2)$ vào $\text{followpos}(i)$.
  2. Tại nút lặp $c^*$ (hoặc $c^+$): $\forall i \in \text{lastpos}(c)$, thêm $\text{firstpos}(c)$ vào $\text{followpos}(i)$.

---

### Thẻ 8 — Tối thiểu hóa DFA: Moore vs. Hopcroft [Chương 3.1]
- **Phân hoạch đầu $\Pi_0$ của Lexer**: $\Pi_0 = \{Q_{\text{non-accept}}\} \cup \{Q_{T_1}, Q_{T_2}, \dots, Q_{T_k}\}$ (tách riêng từng loại token để không làm mất nhãn phân loại!).
- **Moore** $O(p \cdot |Q|^2)$ xuất vết trực quan $\Pi_0 \to \Pi_k$; **Hopcroft** $O(p \cdot |Q| \log |Q|)$ chỉ đẩy khối nhỏ hơn vào $W$. Cả hai hội tụ đẳng cấu 1–1 (`MiniLang`: 78 TT).

---

### Thẻ 9 — Định lý Myhill–Nerode & Cách chứng minh DFA đã tối giản tuyệt đối
- Hai trạng thái $p, q$ phân biệt được khi tồn tại chuỗi hậu tố $w \in \Sigma^*$ sao cho $\tau(\hat{\delta}(p, w)) \neq \tau(\hat{\delta}(q, w))$.
- Hệ thống tìm chuỗi phân tách ngắn nhất $w$ cho **100% cặp trạng thái** (`3.003/3.003` cặp trên MiniLang).

---

### Thẻ 10 — Hai nguyên tắc vàng của Bộ quét Từ vựng: Maximal Munch & Priority Rule
1. **Maximal Munch (Khớp dài nhất)**: Luôn ăn tiền tố dài nhất (`ifelse` $\to$ `IDENTIFIER`, `==` $\to$ `OP_EQ`).
2. **Priority Rule (Ưu tiên luật đứng trước)**: Cùng độ dài tối đa thì chọn quy tắc có chỉ số ưu tiên nhỏ hơn (`if` $\to$ `KW_IF` thắng `IDENTIFIER`).

---

### Thẻ 11 — Thuật toán Reps (1998): Chống suy biến $O(n^2)$ thành Tuyến tính chặt $O(n)$
- Lưu tập `failed_states` chứa các cấu hình `(state, cursor)` nằm sau `last_accept_pos` đã chứng minh không dẫn tới trạng thái kết thúc nào.
- Khi gặp lại `(state, cursor) in failed_states`, cắt nhánh `break` ngay trong $O(1)$ $\implies$ tổng số bước duyệt thất bại $\le |Q| \cdot n = O(n)$!

---

### Thẻ 12 — Phát hiện Quy tắc bị Che Khuất (Shadowed / Dead Token Rules) & Ma trận Giao nhau $L(R_i) \cap L(R_j)$
- **Shadowed Rule**: Quy tắc $T_j$ không xuất hiện ở bất kỳ trạng thái kết thúc nào của `Min-DFA` ($L(R_j) \subseteq \bigcup_{i < j} L(R_i)$).
- **Ma trận Giao nhau $L(R_i) \cap L(R_j)$**: Dùng Product Automaton BFS kiểm tra từng cặp $D_i \times D_j$, phân loại $\varnothing, \subset, \equiv, \supset, \cap$ và tìm từ tố chứng nhân ngắn nhất (`MiniLang`: 9/741 cặp giao nhau hợp lệ, 732 cặp rời nhau).

---

### Thẻ 13 — Bình luận `/* ... */` và Chứng minh Bổ đề Bơm (Pumping Lemma) cho bình luận lồng nhau
- Không viết `/\*.*\*/` vì Maximal Munch sẽ ăn xuyên qua 2 comment trên cùng dòng; phải viết `/\*([^*]|\*+[^*/])*\*+/`.
- Bình luận **lồng nhau sâu tùy ý** `/* /* ... */ */` đẳng cấu $L = \{a^n b^n \mid n \ge 1\}$: theo **Bổ đề Bơm Chương 3.2**, chọn $w = a^p b^p$, bơm $xy^2z = a^{p+k}b^p \notin L$ (mâu thuẫn!) $\implies$ thuộc CFL (Chương 4).

---

### Thẻ 14 — Kiểm chứng Tương đương 2 DFA bằng Product Automaton BFS
- Duyệt BFS trên $D_1 \times D_2$ từ $(q_{01}, q_{02})$ trên bảng chữ cái chung $\Sigma(U_1 \cup U_2)$. Nếu gặp cặp lệch nhãn chấp nhận thì trả về chuỗi phản ví dụ ngắn nhất; nếu duyệt hết không mâu thuẫn thì $L(D_1) \equiv L(D_2)$ trên toàn bộ $\Sigma^*$.

---

### Thẻ 15 — Chiều ngược Định lý Kleene 360°: Thuật toán GNFA State Elimination (`DFA → RE`) [v2.0]
- Thêm $q_{\text{start}} \xrightarrow{\varepsilon} D_0$ và $\forall f \in F: f \xrightarrow{\varepsilon} q_{\text{accept}}$.
- Lặp khử từng đỉnh trung gian $q_{\text{rip}}$ (chọn đỉnh tối thiểu hóa $\text{in\_deg} \times \text{out\_deg}$) theo công thức:
  $$R'(q_i, q_j) = R(q_i, q_j) \;\mid\; R(q_i, q_{\text{rip}}) \cdot \big(R(q_{\text{rip}}, q_{\text{rip}})\big)^* \cdot R(q_{\text{rip}}, q_j)$$
- Trên `(a|b)*abb` (4 TT): sinh ra `b*a(a|ba|bb(a|b+a))*bb` và chứng minh tự động $L(R_{\text{gốc}}) \equiv L(R_{\text{sinh}})$!

---

### Thẻ 16 — Chống Bom Nhân bản AST Lồng nhau (`MAX_AST_NODES = 4096`) [v2.0]
- Giới hạn đơn lẻ `MAX_QUANTIFIER_BOUND = 64` ngăn được `a{100}`, nhưng nếu viết lồng nhau `(((a{64}){64}){64})` thì số nút AST tăng mũ $64^3 \approx 528.483$ nút!
- `regex_parser.py` ước lượng trước kích thước cây kết quả trong $O(1)$ ngay trước khi nhân bản và ném `RegexSyntaxError` tức thì (`< 0.1 ms`) hễ vượt quá **`MAX_AST_NODES = 4096`**.

---

### Thẻ 17 — Bộ Sinh Mã Lexer Độc lập Kiểu Flex (`codegen.py` / `cli.py codegen`) [v2.0]
- Giống công cụ `flex` sinh `lex.yy.c`, lệnh `python3 cli.py codegen --preset minilang -o minilang_lexer.py` đóng gói trực tiếp `ASCII_CLASS_MAP[128]`, `UNICODE_CLASS_MAP`, `TRANSITIONS[78][44]`, `ACCEPT_TABLE` và thuật toán Reps $O(n)$ thành 1 file `.py` độc lập (~527 dòng, Zero `import re`), được unittest đối chứng vi sai khớp **100%** với engine gốc!

---

### Thẻ 18 — Bảng Tóm tắt Con số Thực nghiệm "Thuộc lòng 10 giây" khi Bảo vệ (v2.0 Ultimate)
- **Mẫu bài giảng 1 `(a|b)*abb` (Slide 38)**: Thompson = **11** $\to$ Khử $\varepsilon$ = **6** $\to$ Subset = **5** $\to$ Min-DFA = **4** TT $\to$ GNFA sinh `b*a(a|ba|bb(a|b+a))*bb` ($\equiv R_{\text{gốc}}$).
- **Mẫu bài giảng 2 `(a|ba)(a|b)*ba#` (Slide 54)**: **8** vị trí lá, bảng `followpos` khớp từng số Slide 54, Direct DFA = **5** TT (**A..E**).
- **MiniLang (39 quy tắc)**: $\varepsilon$-NFA = **170** $\to$ Khử $\varepsilon$ = **96** $\to$ Subset = **86** $\to$ Direct = **79** $\to$ Moore/Hopcroft Min-DFA = **78** TT (**44** lớp $\Sigma$, **3.003/3.003** cặp Myhill–Nerode, **9/741** cặp giao nhau hợp lệ).
- **CalcLang (12 quy tắc)**: **57** $\to$ **26** $\to$ **24** $\to$ **20** $\to$ **20** TT (**19** lớp $\Sigma$, **190/190** cặp, **2/66** cặp giao).
- **MiniSQL (14 quy tắc)**: **128** $\to$ **67** $\to$ **64** $\to$ **52** $\to$ **52** TT (**44** lớp $\Sigma$, **1.326/1.326** cặp, **5/91** cặp giao).
- **Kiểm thử**: **72/72** test cases JSON + **22/22** bộ unittest = **100% PASS**, **0** `import re`, Báo cáo PDF chuẩn **13 trang**.

