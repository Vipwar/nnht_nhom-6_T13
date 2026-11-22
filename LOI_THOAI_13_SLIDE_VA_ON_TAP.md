# LỜI THOẠI THUYẾT TRÌNH KHỚP TỪNG SLIDE (13 SLIDES — 9 PHÚT 30 GIÂY) & FLASHCARD ÔN TẬP CHƯƠNG 1–3

> **Tài liệu này gồm 2 phần:**
> - **PHẦN A:** Lời thoại chi tiết từng câu **khớp chính xác 100% với tiêu đề và bố cục của 13 Slide** trong file [`deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx`](file:///home/antigravity/Vipwar/nnht_nhom-6_T13/deliverables/Slide_Thuyet_Trinh_T13_Automata_Lexical_Analyzer.pptx) (đồng thời đã được nhúng sẵn vào **Speaker Notes** của từng slide trong file PowerPoint để xem trực tiếp ở chế độ *Presenter View* `Alt + F5`).
> - **PHẦN B:** **15 Flashcard Ôn tập Cốt lõi Chương 1 – Chương 3** (Ngôn ngữ hình thức UEH) giải thích từ gốc giúp mọi thành viên trả lời tự tin bất kỳ câu hỏi lý thuyết hay thực nghiệm nào.

---

## PHẦN A: PHÂN CÔNG & LỜI THOẠI CHI TIẾT 13 SLIDES (9 PHÚT 30 GIÂY)

### Bảng phân công 4 thành viên (Chia đều thời lượng + Kết hợp Live Demo mượt mà)

| Thành viên | Phụ trách Slide | Thời lượng | Nội dung chính |
| :--- | :--- | :---: | :--- |
| **Thành viên 1** | **Slide 1, 2, 3** | **2 phút 00 giây** | Mở đầu, bài toán Lexical Analysis & 4 mục tiêu đột phá, mô hình hình thức Đa-Token + bảng chữ cái UTF-8 `NON_ASCII` ($|\Sigma|=99$) |
| **Thành viên 2** | **Slide 4, 5, 6** | **2 phút 15 giây** | Kiến trúc đường ống 6 nhánh, kiểm chứng Slide 38 `(a|b)*abb` (11 $\to$ 6 $\to$ 5 $\to$ 4) và Slide 54 `(a|ba)(a|b)*ba#` (8 lá, `followpos`, 5 TT) |
| **Thành viên 3** | **Slide 7, 8, 9 + Live Demo** | **3 phút 00 giây** | Đồ thị Combined Min-DFA CalcLang (20 TT), Bộ quét $O(n)$ Reps (1998) & Smart-Sync, và **Trình diễn trực tiếp LexAutomata Studio 5 Tab** |
| **Thành viên 4** | **Slide 10, 11, 12, 13** | **2 phút 15 giây** | Bộ kiểm thử 62/62 PASS & 5 bất biến, thực nghiệm Benchmark 3 ngôn ngữ, giới hạn Bổ đề Bơm (Chương 3.2), phân công & kết luận |

---

### LỜI THOẠI TỪNG SLIDE (Khớp từng thẻ, bảng và sơ đồ trên Slide)

#### SLIDE 1 — Trang bìa: AUTOMATA-BASED LEXICAL ANALYZER (Thành viên 1 — 0:00 đến 0:30)
> *"Em xin kính chào Cô và các bạn. Hôm nay Nhóm 6 chúng em xin trình bày báo cáo đồ án cuối kỳ môn Ngôn ngữ hình thức với đề tài **T13: Automata-based Lexical Analyzer — Xây dựng Bộ phân tích từ vựng tổng quát từ Biểu thức chính quy và Ô-tô-mát hữu hạn**.*
>
> *Như hiển thị ở khung Điểm nổi bật bên phải slide, toàn bộ hệ thống của nhóm được lập trình **100% từ gốc bằng Python Standard Library**, tuyệt đối **không sử dụng thư viện `import re`** trong lõi, hiện thực trọn vẹn **6 phương pháp Automata Chương 3.1**, chứng minh tương đương toán học 6 chiều và vượt qua tuyệt đối **62 trên 62 kịch bản kiểm thử**."*

---

#### SLIDE 2 — `01 · ĐẶT VẤN ĐỀ`: Bài toán Phân tích Từ vựng & Mục tiêu Đồ án T13 (Thành viên 1 — 0:30 đến 1:15)
> *"Bước sang Slide 2: Trong kiến trúc trình biên dịch, **Lexical Analyzer** là cầu nối đầu tiên chuyển dòng ký tự mã nguồn thô thành luồng **Token**, đồng thời lọc bỏ khoảng trắng, bình luận `//` và `/*...*/`, cũng như phát hiện lỗi từ vựng kèm tọa độ dòng, cột.*
>
> *Tại sao chúng ta dùng Ô-tô-mát hữu hạn? Bởi mọi lớp token từ vựng đều thuộc lớp **Ngôn ngữ chính quy** — đặc tả bằng Biểu thức chính quy và quét bằng DFA trong thời gian tuyến tính chặt $O(n)$, miễn nhiễm hoàn toàn với lỗi treo máy ReDoS $O(2^n)$.*
>
> *Từ đó, nhóm đặt ra **4 mục tiêu đột phá** ở cột bên phải:*
> 1. *100% thuần Python (`Zero import re`), hỗ trợ định lượng đếm `{m,n}` và UTF-8 `NON_ASCII`.*
> 2. *Kiểm chứng tương đương 6 chiều và chứng minh tối giản tuyệt đối bằng **Định lý Myhill–Nerode**.*
> 3. *Bộ quét tuyến tính $O(n)$ theo thuật toán **Reps (1998)** chống quay lui bậc hai $O(n^2)$ và tự động phát hiện quy tắc bị che khuất (**Shadowed Rules**).*
> 4. *Xây dựng **Web Studio 5 Tab** trực quan cùng bộ 62 test cases và 16 bộ unittest."*

---

#### SLIDE 3 — `02 · MÔ HÌNH HÌNH THỨC`: Mở rộng Automata sang Phân loại Đa-Token, Khử $\varepsilon$ & Hopcroft/Moore (Thành viên 1 — 1:15 đến 2:00)
> *"Trên Slide 3 là cách nhóm mở rộng mô hình ô-tô-mát đơn lẻ trong giáo trình sang bộ phân loại **Đa-Token** qua 3 thẻ ở nửa trên:*
> - ***Thẻ 1 (Combined $\varepsilon$-NFA & Khử $\varepsilon$)***: *Ghép $k$ mảnh $\varepsilon$-NFA con qua đỉnh khởi đầu chung $q_{\text{start}}$, đồng thời cài đặt **Định lý 2 (Slide 21–22)** khử toàn bộ cung $\varepsilon$, giúp MiniLang rút gọn từ 170 xuống 96 trạng thái NFA.*
> - ***Thẻ 2 (Subset DFA & Giải quyết xung đột)***: *Khi một tập con DFA chứa nhiều trạng thái kết thúc, hệ thống chọn quy tắc có độ ưu tiên cao nhất ($\tau_D(S) = \arg\min \text{priority}$). Từ đó tự động phát hiện **Shadowed Rule** nếu có quy tắc không bao giờ thắng ở bất kỳ trạng thái kết thúc nào của Min-DFA.*
> - ***Thẻ 3 (Moore, Hopcroft & Myhill–Nerode)***: *Khởi tạo phân hoạch $\Pi_0$ tách riêng theo từng nhãn token chiến thắng, chạy song song cả **Moore** $O(p\cdot|Q|^2)$ và **Hopcroft** $O(p\cdot|Q|\log|Q|)$, rồi tìm chuỗi phân biệt Myhill–Nerode cho 100% cặp trạng thái.*
> - *Ở khung dưới cùng, nhóm thiết kế bảng chữ cái hữu hạn $|\Sigma| = 99$ gồm 98 ký tự ASCII và lớp đại diện `NON_ASCII` (`0x80`) cho mọi ký tự `ord(c) >= 128`, giúp quét mượt chuỗi tiếng Việt `"Xin chào UEH"` nhưng vẫn bắt chính xác lỗi `100€` (`U+20AC`) ngoài chuỗi. Em xin nhường lời cho bạn thứ 2."*

---

#### SLIDE 4 — `03 · KIẾN TRÚC HỆ THỐNG`: Đường ống Biên dịch 6 Phương pháp Automata & Kiểm chứng Hình thức (Thành viên 2 — 2:00 đến 2:40)
> *"Em xin tiếp tục ở Slide 4 với sơ đồ kiến trúc đường ống biên dịch 6 phương pháp Automata và kiểm chứng hình thức.*
>
> *Từ tập quy tắc biểu thức chính quy đầu vào:*
> - ***Nhánh chuẩn bên trên*** *đi qua chuỗi 4 định lý Chương 3.1: Bộ phân tích cú pháp RE $\to$ **Thompson $\varepsilon$-NFA** (Định lý 3) $\to$ **NFA Khử $\varepsilon$** (Định lý 2) $\to$ **Subset DFA** với bộ phân hoạch 43 lớp ký tự tương đương (Định lý 1) $\to$ tối thiểu hóa song song bằng cả **Moore** và **Hopcroft**.*
> - ***Nhánh đối chứng bên dưới*** *đi trực tiếp từ cây cú pháp gia tố $r\cdot\#$ và $(R_1\cdot\#_1)\mid\dots\mid(R_k\cdot\#_k)$ qua bảng `followpos` để sinh **Direct DFA** đơn lẻ và Đa-Token.*
> - *Toàn bộ 6 ô-tô-mát này đều được đưa vào mô-đun **Product Automaton Verifier** để chứng minh tương đương ngôn ngữ 100%, kiểm chứng tối giản Myhill–Nerode và kiểm chứng xuất/nhập khứ hồi chuẩn XML **JFLAP 7.x**."*

---

#### SLIDE 5 — `04 · THUẬT TOÁN CỐT LÕI (1/2)`: RE $\to$ Thompson $\varepsilon$-NFA $\to$ Khử $\varepsilon$ $\to$ Subset DFA $\to$ Min-DFA (Slide 38 UEH) (Thành viên 2 — 2:40 đến 3:25)
> *"Sang Slide 5 là kết quả kiểm chứng nhánh thuật toán chuẩn trên biểu thức kinh điển `(a|b)*abb` ở **Slide 38 Chương 3.1 bài giảng UEH**:*
> - ***Hình (a) Thompson $\varepsilon$-NFA***: *Nhờ bất biến $\text{in-deg}(\text{start})=0$ và $\text{out-deg}(\text{end})=0$, phép nối kết gộp trực tiếp đỉnh nối và sinh ra **đúng 11 trạng thái ($q_0 \dots q_{10}$)** khớp từng đỉnh, từng cung với Slide 38 của Cô.*
> - ***Bước Khử $\varepsilon$ theo Định lý 2 (Slide 21–22)***: *Loại bỏ hoàn toàn các cung $\varepsilon$, rút gọn từ 11 xuống **6 trạng thái NFA**.*
> - ***Hình (b) Subset Construction DFA***: *Thuật toán tập con sinh ra **đúng 5 trạng thái ($D_0 \dots D_4$)** khớp hoàn toàn với Slide 35 bài giảng.*
> - ***Hình (c) Minimized DFA***: *Cả thuật toán Moore và Hopcroft đều phát hiện $D_0 \equiv D_2$ và gộp lại còn **4 trạng thái tối giản**, trong đó toàn bộ $\binom{4}{2} = 6/6$ cặp trạng thái đều có chuỗi phân biệt Myhill–Nerode ngắn nhất là `bb`, `b` và $\varepsilon$."*

---

#### SLIDE 6 — `04 · THUẬT TOÁN CỐT LÕI (2/2)`: Nhánh đối chứng Direct RE $\to$ DFA Đơn lẻ & Đa-Token (Slide 46–57) (Thành viên 2 — 3:25 đến 4:15)
> *"Ở Slide 6 là nhánh đối chứng **Direct RE $\to$ DFA** theo Mục 2.5 (Slide 46–57 bài giảng).*
>
> *Thay vì đi qua $\varepsilon$-NFA, hệ thống gắn ký hiệu kết thúc `#` để tạo cây cú pháp gia tố $r\cdot\#$, đánh số các lá ký tự và tính đệ quy `nullable`, `firstpos`, `lastpos` cùng bảng `followpos`.*
>
> *Khi kiểm chứng với biểu thức bài giảng `r = (a|ba)(a|b)*ba#`:*
> - *Hệ thống đánh số **8 nút lá** và xuất bảng `followpos` trên giao diện Web Tab 3 (hình bên trái): vị trí 1, 3, 4, 5 có `followpos = {4, 5, 6}`; vị trí 2 là `{3}`; vị trí 6 là `{7}`; vị trí 7 là `{8}` — **khớp 100% từng con số với Slide 54 bài giảng**!*
> - *Từ đó đồ thị Direct DFA ở hình góc trên bên phải sinh trực tiếp **5 trạng thái tối giản A, B, C, D, E** khớp Slide 55–57.*
> - *Đặc biệt, nhóm đã mở rộng thành công phương pháp này sang **Combined Multi-token Direct DFA** $(R_1\cdot\#_1)\mid\dots\mid(R_k\cdot\#_k)$ và chứng minh tương đương 100% với Min-DFA trên cả 3 ngôn ngữ. Em xin chuyển cho bạn thứ 3."*

---

#### SLIDE 7 — `05 · TRỰC QUAN HÓA AUTOMATA`: Minh họa Combined Minimized DFA Hoàn chỉnh — Ngôn ngữ CalcLang (Thành viên 3 — 4:15 đến 4:55)
> *"Em xin trình bày Slide 7: Hình bên trái là đồ thị **Combined Minimized DFA** hoàn chỉnh của ngôn ngữ **CalcLang (12 quy tắc token)** sau khi nén từ 57 trạng thái $\varepsilon$-NFA $\to$ 26 NFA khử $\varepsilon$ $\to$ 24 Subset DFA $\to$ còn **20 trạng thái tối giản** (giảm 16,7%, đủ 190/190 cặp phân biệt Myhill–Nerode).*
>
> *Nhìn vào đồ thị này, ta thấy rõ cách DFA giải quyết 2 bài toán cốt lõi của bộ phân tích từ vựng:*
> 1. ***Từ khóa vs Định danh***: *Đi từ $D_0$ đọc `l` $\to D_9$, `e` $\to D_{13}$, `t` $\to D_{16}$ nhận `KW_LET` (nhờ độ ưu tiên cao hơn `ID`). Nhưng nếu sau `let` còn chữ cái hoặc số (ví dụ `letx`), DFA rẽ ngay sang $D_8$ để nhận `ID` theo đúng nguyên tắc **Maximal Munch**.*
> 2. ***Số thực & Quay lui***: *Từ $D_0$ đọc chữ số vào $D_5$ (`INT`), gặp dấu chấm `.` sang trạng thái trung gian $D_{11}$ (không kết thúc), đọc tiếp chữ số mới vào $D_{15}$ (`FLOAT`). Nếu đầu vào là `3.`, DFA dừng ở $D_{11}$ rồi quay lui 1 bước về $D_5$ để phát `INT("3")`!"*

---

#### SLIDE 8 — `06 · BỘ QUÉT TỪ VỰNG O(n)`: Maximal Munch Tuyến tính $O(n)$ (Reps, 1998) & Phục hồi lỗi Kép (Thành viên 3 — 4:55 đến 5:35)
> *"Sang Slide 8 là cơ chế hoạt động của bộ quét từ vựng `scanner.py` với 3 cải tiến đột phá:*
> - ***Thứ nhất — Chống quay lui bậc hai $O(n^2)$ theo thuật toán Reps (1998)***: *Trong quá trình dò Maximal Munch, nếu một nhánh đi qua `(state, cursor)` không dẫn tới bất kỳ trạng thái kết thúc nào, hệ thống ghi vào bảng băm `failed_states`. Ở các lượt sau, hễ chạm lại cấu hình này là cắt nhánh trong $O(1)$. Như dòng cuối bảng thực nghiệm: chuỗi lỗi 10.000 ký tự `"` + `\"`*5000 kích hoạt đúng **5.000 lần cắt nhánh** và quét xong chỉ trong **24 ms**!*
> - ***Thứ hai — Hỗ trợ UTF-8 an toàn & Bình luận nhiều dòng `/*...*/`***: *Nhận diện trọn vẹn chuỗi tiếng Việt `"Xin chào"`, bỏ qua `/*a*/`, và bắt lỗi ngay ký tự `€` ngoài chuỗi với mã `U+20AC`.*
> - ***Thứ ba — Phục hồi lỗi kép (`Panic-mode` vs `Smart-Sync`)***: *Cho phép chuyển đổi trực tiếp giữa dịch 1 ký tự cổ điển và gom trọn chuỗi/bình luận chưa đóng thành 1 lỗi duy nhất."*

---

#### SLIDE 9 — `07 · TRÌNH DIỄN SẢN PHẨM`: Giao diện Trực quan LexAutomata Studio 5 Tab & Live Demo (Thành viên 3 — 5:35 đến 7:15)
> *"Ở Slide 9 là giao diện **LexAutomata Studio 5 Tab** chạy hoàn toàn độc lập bằng `python3 app.py`. Ngay bây giờ em xin thao tác **Live Demo trực tiếp trên trình duyệt** theo 4 bước:*
> *(Chuyển sang cửa sổ trình duyệt Web Studio)*
> 1. ***Tab 1 (Quét Từ vựng & Phục hồi lỗi)***: *Em bấm quét trên MiniLang (39 token) có chuỗi tiếng Việt `"Xin chào UEH"` và bình luận `/*...*/`. Khi chọn mẫu **Biên Maximal Munch** và bấm vào token `1.5` trong `1.5e + 2`, hoạt ảnh DFA chiếu rõ bước đọc `e` rồi quay lui 1 ký tự. Khi chọn mẫu **Lỗi & Phục hồi** và gạt giữa `Panic-mode` với `Smart-Sync`, chuỗi quên đóng được gom sạch thành 1 lỗi duy nhất.*
> 2. ***Tab 2 (6 Ô-tô-mát & Myhill–Nerode)***: *Em chuyển đổi trực tiếp giữa 6 mô hình (`Moore Min-DFA`, `Hopcroft Min-DFA`, `Subset DFA`, `Combined Direct DFA`, `NFA Khử ε`, `Thompson ε-NFA`) và mở bảng chứng minh Myhill–Nerode 3.003/3.003 cặp phân biệt.*
> 3. ***Tab 3 (Direct RE Lab & Kiểm chứng $R_1 \equiv R_2$)***: *Bấm chip `(a|b)*abb` (11 $\to$ 6 $\to$ 5 $\to$ 4) và `(a|ba)(a|b)*ba` hiện cây `r#` cùng bảng `followpos` khớp 100% Slide 54, đồng thời kiểm chứng 2 biểu thức `(a|b)*` $\equiv$ `(a*b*)*`.*
> 4. ***Tab 4 (Bắt bẫy Luật bị Che Khuất)***: *Khi em đẩy `IDENTIFIER` lên trên `KW_IF` và bấm Biên dịch, hệ thống bật ngay **Cảnh báo Đỏ Shadowed Rule** báo `KW_IF` bị che khuất hoàn toàn! Em xin nhường lời cho bạn thứ 4."*

---

#### SLIDE 10 — `08 · KIỂM THỬ & BẤT BIẾN`: Bộ Kiểm thử Không Lỗ Hổng (62/62 PASS) & 5 Bất biến Toán học (Thành viên 4 — 7:15 đến 7:50)
> *"Em xin tiếp tục ở Slide 10 về hệ thống kiểm thử tự động:*
> - *4 chỉ số KPI ở hàng trên tóm tắt kết quả kiểm định: **62/62 kịch bản JSON PASS (100%)**, **16/16 bộ Unittest OK** trên hơn 400 chuỗi Fuzzing, tổng cộng **4.519/4.519 cặp trạng thái** trên 3 ngôn ngữ đều có chuỗi phân biệt Myhill–Nerode, và thời gian Stress Test 10.000 ký tự lỗi luôn **dưới 25 ms**.*
> - *Như bảng chi tiết bên dưới, hệ thống kiểm chứng tự động cả **5 bất biến toán học**, nổi bật là **Bất biến Zero-Loss Reconstruction** (ghép toàn bộ token giữ lại, token skip và mảnh lỗi luôn tái tạo khớp 100% từng byte mã nguồn gốc) và **Khứ hồi JFLAP `.jff`** (xuất ra XML JFLAP 7.x và đọc ngược lại vẫn đẳng cấu 100% với ô-tô-mát ban đầu)."*

---

#### SLIDE 11 — `09 · THỰC NGHIỆM & PHÂN TÍCH`: Đánh giá 6 Phương pháp Automata & Hiệu năng Tuyến tính $O(n)$ (Thành viên 4 — 7:50 đến 8:25)
> *"Slide 11 trình bày biểu đồ thực nghiệm so sánh cả 6 phương pháp xây dựng Automata trên 3 ngôn ngữ đặc tả:*
> - ***MiniLang (39 token)***: *Từ 170 trạng thái $\varepsilon$-NFA $\to$ 96 trạng thái NFA Khử $\varepsilon$ $\to$ 86 Subset DFA $\to$ 79 Combined Direct DFA $\to$ **78 trạng thái Moore & Hopcroft Min-DFA** (giảm 9,3%, 3.003/3.003 cặp phân biệt).*
> - ***CalcLang (12 token)***: *57 $\varepsilon$-NFA $\to$ 26 NFA Khử $\varepsilon$ $\to$ 24 Subset DFA $\to$ **20 trạng thái Min-DFA** (giảm 16,7%, 190/190 cặp).*
> - ***MiniSQL (14 token)***: *128 $\varepsilon$-NFA $\to$ 67 NFA Khử $\varepsilon$ $\to$ 64 Subset DFA $\to$ **52 trạng thái Min-DFA** (giảm 18,8%, 1.326/1.326 cặp).*
> - *Biểu đồ bên phải xác nhận tốc độ quét thực tế đạt từ **26.000 đến hơn 51.000 tokens/giây** và giữ độ phức tạp tuyến tính chặt $O(n)$ nhờ bảng nhớ `failed_states`."*

---

#### SLIDE 12 — `10 · ĐÁNH GIÁ & TỔ CHỨC NHÓM`: Giới hạn Lý thuyết (Bổ đề Bơm), Hướng phát triển & Phân công (Thành viên 4 — 8:25 đến 9:05)
> *"Ở Slide 12, bên cạnh các thách thức kỹ thuật đã giải quyết triệt để, nhóm cũng phân tích rõ **giới hạn lý thuyết của DFA theo Bổ đề Bơm (Pumping Lemma — Chương 3.2)**:*
> - *Trong khi bình luận nhiều dòng không lồng nhau `/*...*/` là ngôn ngữ chính quy, thì bình luận nhiều dòng **lồng nhau sâu tùy ý** `/* /* ... */ */` lại đẳng cấu với ngôn ngữ $L = \{a^n b^n \mid n \ge 1\}$. Theo Bổ đề Bơm, bộ nhớ hữu hạn trạng thái của DFA không thể đếm độ sâu lồng nhau tùy ý nên cấu trúc này thuộc lớp **Ngôn ngữ phi ngữ cảnh (CFL — Chương 4)**.*
> - *Hướng phát triển tiếp theo của nhóm là bổ sung ngăn xếp ngữ cảnh từ vựng và kết nối luồng Token đầu ra với bộ phân tích cú pháp CFG `LL(1)` / `LR(1)`.*
> - *Khung bên phải trình bày bảng phân công đồng đều 25% cho 4 thành viên cùng khai báo minh bạch việc sử dụng công cụ AI hỗ trợ rà soát và kiểm định."*

---

#### SLIDE 13 — `KẾT LUẬN ĐỒ ÁN T13`: Tổng kết & Hỏi đáp Q&A (Thành viên 4 — 9:05 đến 9:30)
> *"Khép lại ở Slide 13, đồ án T13 của Nhóm 6 đã hiện thực hoàn chỉnh hành trình từ lý thuyết Ô-tô-mát hữu hạn Chương 1–3 đến một bộ phân tích từ vựng tổng quát tuyến tính $O(n)$: **6 phương pháp Automata không dùng `import re`**, **chứng minh toán học Product Automaton & Myhill–Nerode**, và **62/62 test cases đạt 100% PASS**.*
>
> *Nhóm chúng em xin chân thành cảm ơn Cô Hồ Thị Thanh Tuyến và các bạn đã lắng nghe. Nhóm rất hân hạnh được đón nhận các câu hỏi phản biện từ Cô và các bạn!"*

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
  1. **Hợp (Union)** $R_1 \mid R_2$: $L(R_1 \mid R_2) = L(R_1) \cup L(R_2)$ — ưu tiên **thấp nhất**.
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
- **Mục tiêu**: Xóa toàn bộ các cung $\varepsilon$ từ $\varepsilon$-NFA để thu được NFA chuẩn không có $\varepsilon$.
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
   - *Ví dụ*: Chuỗi `"if"` vừa khớp `KW_IF` (dài 2, $\pi=4$) vừa khớp `IDENTIFIER` (dài 2, $\pi=16$) $\to$ Chọn `KW_IF`.

---

### Thẻ 11 — Thuật toán Reps (1998): Tại sao Maximal Munch ngây thơ bị $O(n^2)$ và cách sửa thành $O(n)$?
- **Vấn đề $O(n^2)$ của Maximal Munch ngây thơ**:
  - Giả sử quy tắc chuỗi là `"([^"\\\n]|\\.)*"` và đầu vào là `"` theo sau bởi 5.000 cặp `\"` (10.000 ký tự) nhưng **thiếu dấu `"` đóng ở cuối**.
  - Ở vị trí 0, DFA đọc từ đầu đến hết 10.000 ký tự tới EOF vẫn chưa gặp `"` đóng $\to$ quay lui về điểm chấp nhận gần nhất hoặc báo lỗi rồi tiến lên. Nếu bộ quét ngây thơ không ghi nhớ, ở mỗi vị trí tiếp theo nó lại đọc đi đọc lại đoạn đuôi dài tốn $O(n^2)$ bước.
- **Giải pháp Reps (1998) trong `scanner.py`**:
  - Lưu bảng nhớ `failed_states`: nếu một lần chạy DFA đi qua cặp `(state, cursor)` sau vị trí chấp nhận cuối cùng mà đến lúc kẹt không gặp thêm bất kỳ trạng thái kết thúc nào, ta đánh dấu `(state, cursor) \in \text{failed\_states}`.
  - Ở các token kế tiếp, hễ DFA chạm lại một cặp `(state, cursor)` đã có trong `failed_states`, nó **cắt nhánh `break` ngay lập tức trong $O(1)$**! Nhờ đó mỗi cặp `(state, cursor)` chỉ bị duyệt thất bại tối đa 1 lần $\to$ thời gian quét luôn là **tuyến tính chặt $O(|Q| \cdot n) = O(n)$**.

---

### Thẻ 12 — Phát hiện Quy tắc bị Che Khuất (Shadowed / Dead Token Rules)
- **Khi nào một quy tắc bị che khuất?**
  - Khi ngôn ngữ của quy tắc $R_j$ nằm hoàn toàn trong hợp ngôn ngữ của các quy tắc $R_i$ có độ ưu tiên cao hơn ($L(R_j) \subseteq \bigcup_{i < j} L(R_i)$).
  - *Ví dụ kinh điển*: Đặt `IDENTIFIER` (`[a-zA-Z_][a-zA-Z0-9_]*`, $\pi=1$) lên **trên** `KW_IF` (`if`, $\pi=2$). Vì mọi chuỗi `"if"` đều thuộc `IDENTIFIER`, tại trạng thái kết thúc nhận chuỗi `"if"`, quy tắc `IDENTIFIER` luôn có $\pi$ nhỏ hơn và giành chiến thắng!
- **Cách hệ thống phát hiện tự động**:
  - Sau khi sinh `Minimized DFA`, hệ thống quét toàn bộ các trạng thái kết thúc đạt tới được $q \in F_{\min}$. Nếu một quy tắc $T_j$ **không bao giờ là nhãn chiến thắng $\tau(q)$ ở bất kỳ trạng thái kết thúc nào**, hệ thống kết luận $T_j$ bị che khuất hoàn toàn và chỉ ra chính xác quy tắc $T_i$ đã đè lên nó!

---

### Thẻ 13 — Biểu thức chính quy cho Bình luận nhiều dòng `/* ... */` và Chứng minh Bổ đề Bơm (Pumping Lemma) cho bình luận lồng nhau
- **Tại sao không được viết `/\*.*\*/` cho bình luận nhiều dòng?**
  - Vì `.` khớp mọi ký tự (trừ `\n`), và do tính chất **Maximal Munch (tham lam)**, trên dòng `/* c1 */ x = 1; /* c2 */`, biểu thức `/\*.*\*/` sẽ nuốt trọn từ `/*` đầu tiên đến `*/` cuối cùng, ăn mất luôn cả câu lệnh `x = 1;` ở giữa!
- **Biểu thức chính quy chuẩn trong đồ án**:
  $$R_{\text{block}} = \texttt{/\*([\^{}*]|\\*+[\^{}*/])*\*+/}$$
  *(Giải thích: Sau `/*`, ở bên trong chỉ cho phép hoặc ký tự không phải `*`, hoặc một dãy dấu `*+` nhưng ký tự ngay sau nó không được là `*` hay `/`, cho tới khi gặp dãy `*+/` đóng đầu tiên).*
- **Tại sao bình luận nhiều dòng LỒNG NHAU (`/* /* ... */ */` độ sâu tùy ý) KHÔNG phải ngôn ngữ chính quy?**
  - Áp dụng **Bổ đề Bơm (Pumping Lemma — Chương 3.2)**: Giả sử ngôn ngữ bình luận lồng nhau $L = \{ \texttt{/*}^m \texttt{*/}^m \mid m \ge 1 \}$ là chính quy với hằng số bơm $p$. Chọn chuỗi $w = \texttt{/*}^p \texttt{*/}^p \in L$. Theo bổ đề bơm, $w = xyz$ với $|xy| \le p$ và $|y| \ge 1$, nên $y$ chỉ nằm trong phần mở `/*`. Khi bơm $xy^2z$, số dấu mở `/*` nhiều hơn số dấu đóng `*/` $\to$ chuỗi không còn cân bằng ($xy^2z \notin L$), mâu thuẫn! Vậy bình luận lồng nhau thuộc **Ngôn ngữ phi ngữ cảnh (CFG — Chương 4)** chứ không phải Ngôn ngữ chính quy.

---

### Thẻ 14 — Kiểm chứng Tương đương 2 DFA bằng Product Automaton BFS
- **Bài toán**: Cho 2 DFA $\mathcal{D}_1 = (Q_1, \Sigma, \delta_1, q_{01}, F_1, \tau_1)$ và $\mathcal{D}_2 = (Q_2, \Sigma, \delta_2, q_{02}, F_2, \tau_2)$, làm sao kiểm tra $\mathcal{D}_1 \equiv \mathcal{D}_2$ trên mọi chuỗi $w \in \Sigma^*$ (vô hạn chuỗi)?
- **Giải pháp**: Dựng ô-tô-mát tích $\mathcal{D}_1 \times \mathcal{D}_2$ và duyệt **BFS** từ cặp trạng thái gốc $(q_{01}, q_{02})$:
  - Với mỗi ký tự $a \in \Sigma$, đi tới cặp trạng thái đích $(p_1, p_2) = (\delta_1(q_1, a), \delta_2(q_2, a))$.
  - Nếu tại bất kỳ cặp $(p_1, p_2)$ nào mà $\tau_1(p_1) \neq \tau_2(p_2)$ (một bên chấp nhận, một bên từ chối, hoặc trả về 2 tên token khác nhau), thuật toán dừng ngay và trả về đường đi BFS làm **phản ví dụ ngắn nhất** $w$.
  - Vì $Q_1 \times Q_2$ là hữu hạn (tối đa $|Q_1| \cdot |Q_2|$ cặp), nếu BFS duyệt hết mà không có cặp nào lệch nhãn thì $\mathcal{D}_1 \equiv \mathcal{D}_2$ trên **toàn bộ vô hạn chuỗi** $w \in \Sigma^*$.

---

### Thẻ 15 — Bảng Tóm tắt Con số Thực nghiệm "Thuộc lòng 10 giây" khi Bảo vệ
- **Mẫu bài giảng 1 `(a|b)*abb` (Slide 38)**: Thompson $\varepsilon$-NFA = **11** $\to$ Khử $\varepsilon$ (ĐL 2) = **6** $\to$ Subset DFA (ĐL 1) = **5** $\to$ Moore & Hopcroft Min-DFA = **4** trạng thái (6/6 cặp Myhill–Nerode).
- **Mẫu bài giảng 2 `(a|ba)(a|b)*ba#` (Slide 54)**: **8** vị trí lá, bảng `followpos` khớp từng số Slide 54, Direct DFA = **5** trạng thái (**A..E**).
- **MiniLang (39 quy tắc)**: $\varepsilon$-NFA = **170** $\to$ Khử $\varepsilon$ = **96** $\to$ Subset DFA = **86** $\to$ Combined Direct DFA = **79** $\to$ Moore & Hopcroft Min-DFA = **78** trạng thái (giảm **9,3%**, **43** lớp ký tự tương đương, **3.003/3.003** cặp Myhill–Nerode phân biệt).
- **CalcLang (12 quy tắc)**: $\varepsilon$-NFA = **57** $\to$ Khử $\varepsilon$ = **26** $\to$ Subset DFA = **24** $\to$ Combined Direct DFA = **20** $\to$ Min-DFA = **20** trạng thái (giảm **16,7%**, **190/190** cặp Myhill–Nerode).
- **MiniSQL (14 quy tắc)**: $\varepsilon$-NFA = **128** $\to$ Khử $\varepsilon$ = **67** $\to$ Subset DFA = **64** $\to$ Combined Direct DFA = **52** $\to$ Min-DFA = **52** trạng thái (giảm **18,8%**, **1.326/1.326** cặp Myhill–Nerode).
- **Kiểm thử**: **62/62** test cases JSON + **16/16** bộ unittest + **5** bất biến toán học = **100% PASS**, **0** `import re`.
