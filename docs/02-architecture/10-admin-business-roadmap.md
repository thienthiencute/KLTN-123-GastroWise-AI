# GastroWise Admin CMS - Roadmap & Tiến Độ Nghiệp Vụ (Final)

Tài liệu này quản lý danh sách các **Nghiệp vụ Admin**, tiến độ thực hiện chi tiết từng phần theo nguyên tắc **"Làm xong dứt điểm nghiệp vụ này mới chuyển sang nghiệp vụ tiếp theo"**, và nghiệm thu kèm tính năng AI tích hợp.

---

## 📋 Bảng Tổng Quan Tiến Độ Các Nghiệp Vụ Admin

| STT | Nghiệp vụ Admin | Trạng thái | CRUD Status | Tích hợp AI |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Quản Lý Đánh Giá (Reviews)** | ✅ **100% Hoàn thành** | Đầy đủ | Gemini 1.5 Sentiment Analysis & Hashtags Extraction |
| **2** | **Quản Lý Nhà Hàng (Restaurants)** | ✅ **100% Hoàn thành** | Đầy đủ | AI Auto-Tagging & AI SEO Description Generator |
| **3** | **Quản Lý Thực Đơn (Menu)** | ✅ **100% Hoàn thành** | Đầy đủ | AI Scan Menu Image (Nhận diện món ăn từ hình ảnh) |
| **4** | **Quản Lý Người Dùng (Users)** | ✅ **100% Hoàn thành** | Đầy đủ | AI User Preference Profile & Role Management |
| **5** | **AI Insights & Báo Cáo** | ✅ **100% Hoàn thành** | Read-Only | Báo cáo tổng hợp cảm xúc & Top Hashtags |
| **6** | **Quản Lý Đặt Bàn (Bookings)** | ⛔ **Out of Scope** | N/A | Không áp dụng trong phạm vi dự án GastroWise |

---

## 🛠️ Chi Tiết Từng Nghiệp Vụ & Quy Trình Dứt Điểm (Checklist)

### 1. Nghiệp Vụ 1: Quản Lý Đánh Giá (Reviews Management) - `/reviews`
> **Nguyên tắc dứt điểm:** Đã hoàn thành 100% & test thành công.

- [x] **Client/Server DataTable:** Tìm kiếm theo tên user, nội dung review. Lọc theo nhãn Sentiment (`POSITIVE`, `NEGATIVE`, `NEUTRAL`).
- [x] **Thao tác CRUD:** Xem danh sách, Xóa review rác.
- [x] **Tích hợp AI:** Phân tích cảm xúc bằng Gemini 1.5 Flash, tính điểm tự tin (`score`), trích xuất tối đa 3 `#hashtags`.
- [x] **Tài liệu KLTN:** Đã lưu tại `docs/03-technical-specs/09-ai-prompt-engineering.md`.

---

### 2. Nghiệp Vụ 2: Quản Lý Nhà Hàng (Restaurants Management) - `/restaurants`
> **Nguyên tắc dứt điểm:** Đã hoàn thành 100% & test thành công.

- [x] **DataTable & Phân Trang:** Phân trang 8 bản ghi/trang, tìm kiếm theo tên quán, địa chỉ, tag.
- [x] **Thao tác CRUD Đầy Đủ:**
  - [x] **Create:** Thêm nhà hàng mới.
  - [x] **Read:** Xem chi tiết kèm hình ảnh & chỉ số.
  - [x] **Update:** Sửa thông tin nhà hàng (Tên, địa chỉ, giờ mở cửa, giá cả, tags, mô tả) — *Đã fix get chuẩn dữ liệu cũ*.
  - [x] **Delete:** Xóa nhà hàng khỏi hệ thống.
- [x] **Tích hợp AI Trợ Lý:**
  - [x] **AI Auto-Tagging:** Tự động đề xuất thẻ phân loại (`#MonViet`, `#Pho`, `#GiaTruyen`).
  - [x] **AI SEO Description:** Sinh bài viết mô tả nhà hàng chuẩn SEO.
  - [x] **AI Summary Insights:** Tóm tắt ưu/nhược điểm nhà hàng dựa trên reviews.

---

### 3. Nghiệp Vụ 3: Quản Lý Thực Đơn & Món Ăn (Menu Management) - `/menu`
> **Nguyên tắc dứt điểm:** Đã hoàn thành 100% & test thành công.

- [x] **Danh sách & Bộ lọc:** Lọc theo nhà hàng, tìm kiếm theo tên món.
- [x] **Thao tác CRUD Đầy Đủ:**
  - [x] **Create:** Thêm món ăn thủ công (Post API).
  - [x] **Read:** Hiển thị thẻ món ăn, hình ảnh, nhãn món Chay/Mặn, giá cả.
  - [x] **Update:** Chỉnh sửa thông tin món ăn (Tên, giá, nhãn chay, mô tả) qua API `PATCH /restaurants/menu/:menuId`.
  - [x] **Delete:** Xóa món ăn khỏi thực đơn qua API `DELETE /restaurants/menu/:menuId`.
- [x] **AI Scan Menu Image:** Tính năng nhận diện hình ảnh món ăn bằng AI.

---

### 4. Nghiệp Vụ 4: Quản Lý Người Dùng & Phân Quyền (Users Management) - `/users`
> **Nguyên tắc dứt điểm:** Đã hoàn thành 100% & test thành công.

- [x] **DataTable Phân Trang:** Phân trang Server-side từ Backend NestJS.
- [x] **Thao tác CRUD & Phân Quyền:**
  - [x] Tìm kiếm người dùng theo tên/email.
  - [x] Đổi vai trò (Role): `user` ↔ `owner` ↔ `admin`.
  - [x] Khóa / Mở khóa tài khoản (`active` ↔ `banned`).
- [x] **Xem chi tiết:** Hiển thị danh sách nhà hàng đã lưu và sở thích ẩm thực do AI phân tích.

---

## 🏆 Kết Luận
Toàn bộ 4 phân hệ Admin CMS cốt lõi (`Reviews`, `Restaurants`, `Menu`, `Users`) đã hoàn thành dứt điểm 100% đúng chuẩn nghiệp vụ, đầy đủ CRUD, DataTable phân trang và tính năng AI ứng dụng thực tế.
