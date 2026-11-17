# Hướng dẫn: Dùng AI đọc project & viết báo cáo KLTN đúng chuẩn IUH

> Rút ra từ file mẫu `Mau_Noi_dung_cuon_bao_cao.docx` (đã kiểm tra cả nội dung lẫn style XML thật bên trong file, không suy đoán) và đối chiếu với báo cáo hiện có `ThanHoangThienThien_NguyenPhanMinhMan_BaoCaoKLTN.docx` (đề tài **GastroWise**).

---

## 1. Quy trình tổng thể (4 bước)

1. **AI đọc project** (source code, README, tài liệu API, sơ đồ ERD/usecase nếu có) → hiểu đúng project đang làm gì, dùng công nghệ/thuật toán gì thật sự — không bịa.
2. **AI đọc báo cáo hiện có** (file `.docx` bạn đang viết) → biết đã viết tới đâu, không viết đè/viết lại từ đầu.
3. **AI viết nội dung ra file `.md`**, bám đúng khung 5 chương bắt buộc, dùng `#`/`##`/`###` cho đúng 3 cấp heading để sau này convert sang Word không lệch mục lục.
4. **Convert `.md` → `.docx`** áp đúng style file mẫu (dùng Style Heading có sẵn, không bôi đen chỉnh tay) để Mục lục / Danh mục hình / Danh mục bảng vẫn **Update Field** tự động được như thiết kế gốc.

---

## 2. Bảng quy định trình bày (trích từ XML thật của file mẫu)

| Mục | Quy định |
|---|---|
| Khổ giấy | A4 |
| Lề | Trên 3cm · Dưới 3cm · **Trái 3.5cm** (chừa gáy đóng bìa) · Phải 2cm |
| Font | Times New Roman — bắt buộc toàn bộ tài liệu, không đổi font |
| Style **Normal** (nội dung) | Cỡ 13pt, giãn dòng ~1.3 lines, thụt đầu dòng đoạn ~1cm, canh đều 2 bên (justify). Phím tắt: `Ctrl+Shift+N` |
| **Heading 1** (tên Chương) | 16pt, **đậm**, canh giữa, tự đánh số "CHƯƠNG n". Phím tắt: `Ctrl+1` |
| **Heading 2** (mục n.n) | 13pt, đậm, canh trái. Phím tắt: `Ctrl+2` |
| **Heading 3** (mục n.n.n) | 13pt, đậm nghiêng, canh trái. Phím tắt: `Ctrl+3` |
| Xuống dòng trong cùng 1 heading (không muốn tạo mục mới) | `Shift+Enter`, tuyệt đối không dùng `Enter` |
| Bảng / Hình | Chèn caption qua *References → Insert Caption* (không gõ tay), số tự sinh theo chương: `Bảng n-n`, `Hình n-n` |
| Công thức | Trình bày dạng bảng 2 cột: cột 1 là công thức, cột 2 là số thứ tự `(n.n)` |
| Mục lục / Danh mục hình / Danh mục bảng | Không sửa tay — chuột phải vào mục lục → **Update Field** → **Update entire table** |
| Header | Đổi đúng tên chuyên ngành (VD: Kỹ Thuật Phần Mềm) |
| Footer | 3 ô: Họ và tên (trái) – Số trang (giữa) – Lớp (phải). Vùng tô vàng là ô **cần điền**, không xoá format |

## 3. Cấu trúc chương bắt buộc (không đổi tên / không thêm bớt mục lớn)

```
LỜI MỞ ĐẦU (không đánh số)
  1. Tổng quan tình hình nghiên cứu thuộc lĩnh vực đề tài
  2. Ý nghĩa khoa học và thực tiễn của đề tài

CHƯƠNG 1: GIỚI THIỆU
  1.1 Tổng quan
  1.2 Mục tiêu đề tài
  1.3 Phạm vi đề tài
  1.4 Mô tả yêu cầu

CHƯƠNG 2: CƠ SỞ LÝ THUYẾT
  (các lý thuyết/công nghệ/thuật toán đã tìm hiểu và áp dụng)

CHƯƠNG 3: PHÂN TÍCH – THIẾT KẾ
  (thu thập yêu cầu, phân tích, sơ đồ UML/ERD...)

CHƯƠNG 4: HIỆN THỰC – KIỂM THỬ
  (quá trình hiện thực, kịch bản test, kết quả)

CHƯƠNG 5: KẾT LUẬN
  5.1 Kết quả đạt được
  5.2 Hạn chế của đồ án
  5.3 Hướng phát triển

TÀI LIỆU THAM KHẢO (không đánh số)

PHỤ LỤC (không đánh số)
  A. Kế hoạch thực hiện đề tài
  B. Nhật ký thực hiện
  C. Kế hoạch khởi nghiệp
  D. Kiểm tra đạo văn
```

---

## 4. Prompt mẫu — Bước 1: AI đọc project + viết nội dung ra `.md`

Copy nguyên khối dưới, điền vào các chỗ `<...>`, đưa cho AI (Claude Code / Claude trong terminal có quyền đọc thư mục project là tốt nhất, vì cần đọc source code thật):

```
Bạn là trợ lý viết khóa luận tốt nghiệp (KLTN) chuyên ngành Kỹ Thuật Phần Mềm, Trường ĐH Công nghiệp TP.HCM.

BỐI CẢNH:
- Đề tài: "GastroWise – Hệ thống thông tin trải nghiệm ẩm thực thông minh tích hợp tối ưu hóa lộ trình phục vụ du lịch ẩm thực tại TP.HCM"
- Công nghệ đã dùng: Next.js 14 (App Router), TypeScript, TailwindCSS, React Query, <thuật toán routing bạn dùng, VD: TSP heuristic / Google Maps Directions API>
- Thư mục source code / tài liệu project: <đường dẫn thư mục hoặc repo>
- File báo cáo hiện có (nếu có, để không viết lại từ đầu): <đường dẫn file .docx/.md>

NHIỆM VỤ:
1. Đọc toàn bộ source code, README, tài liệu API, sơ đồ (nếu có) trong thư mục project để hiểu đúng: chức năng, kiến trúc hệ thống, luồng dữ liệu, các thuật toán/module đã cài đặt thật sự.
2. Đọc nội dung báo cáo hiện có (nếu có) để biết đã viết tới đâu, chỉ bổ sung phần còn thiếu, không viết đè lại từ đầu.
3. Viết nội dung báo cáo ra file Markdown (report_draft.md), bám ĐÚNG cấu trúc chương sau, không đổi tên, không thêm/bớt mục lớn:

   [dán nguyên khối "Cấu trúc chương bắt buộc" ở mục 3 phía trên vào đây]

4. Nội dung từng phần phải mô tả CHÍNH XÁC những gì có thật trong project (tên công nghệ, API endpoint, class/module, thuật toán, sơ đồ ERD/use-case nếu có trong code) — tuyệt đối không bịa số liệu, kết quả kiểm thử, hay chi tiết không tồn tại trong project.
5. Đánh dấu heading bằng cú pháp Markdown chuẩn để tiện convert sang Word sau này:
   - "# " cho tên Chương (tương ứng Heading 1)
   - "## " cho mục cấp 2, dạng "2.1 ..." (tương ứng Heading 2)
   - "### " cho mục cấp 3, dạng "2.1.1 ..." (tương ứng Heading 3)
6. Khi cần chèn bảng/hình, ghi chú dạng:
   - `[BẢNG: mô tả nội dung + dữ liệu bảng]`
   - `[HÌNH: mô tả hình + đường dẫn file ảnh nếu có]`
   để sau này chèn caption tự động, không đánh số tay.
7. Nếu thiếu thông tin (VD: tên hội đồng phản biện, kết quả test cụ thể, ngày tháng), để rõ `[CẦN BỔ SUNG: ...]` thay vì tự bịa.
8. Lưu kết quả vào file: report_draft.md
```

---

## 5. Prompt mẫu — Bước 2: Convert `.md` → `.docx` đúng format file mẫu

```
Dựa trên file report_draft.md vừa tạo, hãy tạo file Word (.docx) đúng theo định dạng của file mẫu Mau_Noi_dung_cuon_bao_cao.docx:

- Khổ A4; lề trên 3cm, dưới 3cm, trái 3.5cm, phải 2cm
- Font Times New Roman, cỡ 13pt cho toàn bộ nội dung, giãn dòng ~1.3, thụt đầu dòng đoạn ~1cm, canh đều 2 bên
- Heading 1: 16pt, đậm, canh giữa, tự đánh số "CHƯƠNG n"
- Heading 2: 13pt đậm, canh trái, số dạng n.n
- Heading 3: 13pt đậm nghiêng, canh trái, số dạng n.n.n
- Dùng đúng Style Heading có sẵn của Word (không bôi đen chỉnh tay) để Mục lục cập nhật tự động được
- Bảng/Hình dùng Insert Caption, đánh số theo chương (Bảng n-n / Hình n-n)
- Giữ nguyên trang bìa, Header, Footer, Lời cảm ơn, Nhận xét GVHD, khung Mục lục/Danh mục bảng/Danh mục hình như file mẫu — chỉ thay nội dung thân bài
- Xuất file: BaoCao_KLTN_<TenNhom>.docx
```

---

## 7. Prompt bổ sung — dùng khi báo cáo đã viết dở, chỉ muốn AI rà soát & viết tiếp

Dùng prompt này thay cho Bước 1 khi bạn **đã có sẵn nội dung** (như báo cáo GastroWise hiện tại đang viết dở Chương 1) và chỉ muốn AI kiểm tra + viết tiếp phần còn thiếu, **không viết đè** phần đã có:

```
Bạn là trợ lý viết khóa luận tốt nghiệp (KLTN) chuyên ngành Kỹ Thuật Phần Mềm, Trường ĐH Công nghiệp TP.HCM.

BỐI CẢNH:
- Đề tài: "GastroWise – Hệ thống thông tin trải nghiệm ẩm thực thông minh tích hợp tối ưu hóa lộ trình phục vụ du lịch ẩm thực tại TP.HCM"
- File báo cáo hiện có: <đường dẫn file .docx/.md đang viết dở>
- Thư mục source code / tài liệu project: <đường dẫn thư mục hoặc repo>
- Cấu trúc chương bắt buộc: <dán nguyên khối "Cấu trúc chương bắt buộc" ở mục 3>

NHIỆM VỤ:
1. Đọc file báo cáo hiện có, đối chiếu với cấu trúc chương bắt buộc ở trên.
2. Liệt kê rõ: phần nào đã viết xong, phần nào viết dở, phần nào chưa có — trình bày dưới dạng checklist trước khi viết tiếp.
3. Đọc source code / tài liệu project để lấy thông tin chính xác cho các phần còn thiếu (không bịa).
4. Viết tiếp NHỮNG PHẦN CÒN THIẾU vào file report_draft.md:
   - Giữ nguyên 100% nội dung đã có (copy nguyên văn, không diễn đạt lại, không rút gọn).
   - Chỉ thêm nội dung mới vào đúng vị trí mục/chương tương ứng.
   - Dùng đúng cú pháp "#", "##", "###" cho 3 cấp heading như đã thống nhất.
5. Với bảng/hình cần chèn, ghi chú dạng [BẢNG: ...] / [HÌNH: ...] như quy định.
6. Nếu thiếu thông tin để viết tiếp (số liệu, kết quả test, tên hội đồng...), để [CẦN BỔ SUNG: ...] thay vì tự bịa.
7. Lưu kết quả vào file: report_draft.md
```

## 8. Prompt gộp — làm 1 lần từ project đến file .docx hoàn chỉnh

Nếu muốn AI tự làm hết từ đầu đến cuối trong 1 lượt (đọc project → viết .md → convert .docx đúng chuẩn), dùng prompt gộp này:

```
Hãy thực hiện tuần tự 3 bước sau cho đề tài KLTN "GastroWise":

BƯỚC 1 — Đọc & tổng hợp:
- Đọc source code/tài liệu project tại: <đường dẫn>
- Đọc báo cáo hiện có (nếu có) tại: <đường dẫn>
- Đọc quy định trình bày tại file: HUONG_DAN_DUNG_AI_VIET_KLTN.md (mục 2 và mục 3)

BƯỚC 2 — Viết nội dung:
- Viết/viết tiếp nội dung vào report_draft.md, bám đúng cấu trúc chương bắt buộc, giữ nguyên phần đã có, chỉ bổ sung phần thiếu, dùng đúng cú pháp #/##/### cho heading, không bịa thông tin không có trong project.

BƯỚC 3 — Xuất file Word:
- Dựa trên file mẫu Mau_Noi_dung_cuon_bao_cao.docx, tạo file BaoCao_KLTN_<TenNhom>.docx với đúng font/size/lề/heading/caption như quy định ở mục 2, giữ nguyên bìa, header, footer, mục lục, danh mục hình/bảng của file mẫu.

Sau mỗi bước, tóm tắt ngắn gọn đã làm gì, còn thiếu gì, trước khi làm bước tiếp theo.
```

## 9. Lưu ý thực tế

- Nếu AI của bạn **có thể đọc trực tiếp file `.docx` mẫu** (như phiên hiện tại), cách an toàn nhất là **dùng chính file mẫu làm file gốc**, chỉ thay nội dung bên trong (giữ nguyên style/section breaks có sẵn) — tránh việc tự tạo file Word mới rồi style bị lệch so với mẫu gốc.
- Chương 1 trong báo cáo GastroWise hiện tại đang viết dở phần "1.2 Mục tiêu nghiên cứu" — có thể đưa thẳng cho AI ở Bước 1 để nó tiếp tục đúng mạch, không viết lại từ đầu.
- Nếu muốn, mình có thể trực tiếp thực hiện Bước 1 + Bước 2 luôn trong phiên này (đọc project của bạn, sinh `report_draft.md`, rồi convert ra `.docx` đúng style file mẫu) — chỉ cần bạn cung cấp source code/tài liệu project.

---

## 10. Nhật ký Thực hiện AI (Ghi chú tự động)

- **[03/09/2026] Cập nhật Báo cáo KLTN GastroWise**: Đã tiến hành soạn thảo hoàn chỉnh mã nguồn Markdown cho 3 phần cốt lõi của Chương 1:
  - **1.2 Mục tiêu đề tài**: Phân tích mục tiêu công nghệ (Microservices), mục tiêu tính năng và giá trị AI mang lại.
  - **1.3 Phạm vi đề tài**: Khoanh vùng không gian thực hiện tại TP.HCM, đối tượng (Admin, Merchant, User) và nền tảng (Web App).
  - **1.4 Mô tả yêu cầu**: Liệt kê yêu cầu chức năng (User FE, Admin FE, Tính năng AI Copilot, AI Menu Generator) và Yêu cầu phi chức năng (Bảo mật JWT, Hiệu năng <2s, Docker/Vercel).
- **Lưu ý**: Do không thể sửa trực tiếp cấu trúc XML của file `.docx`, nội dung đã được kết xuất ra file `report_draft_Chuong1.md`. Sinh viên cần Copy nguyên khối văn bản từ file `.md` và Paste đè vào vị trí mục 1.2, 1.3, 1.4 trong file Word `DecuongTTDN_NguyenPhanMinhMan.docx`, sau đó thiết lập Style "Heading 2" là hoàn tất.
