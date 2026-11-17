# Tài Liệu Kỹ Thuật: Kiến Trúc & Roadmap Phát Triển App Mobile - GastroWise

Tài liệu này tổng hợp toàn bộ Kiến trúc, Hướng dẫn Deploy/Test trên Máy Thật iPhone/Android và Bảng Task chi tiết về Giao diện (UI) & Nghiệp vụ cho ứng dụng di động **GastroWise Mobile**.

> [!NOTE]
> **Trọng tâm đề tài GastroWise**: Hệ thống thông tin trải nghiệm ẩm thực thông minh — tập trung vào **Gợi ý sản phẩm/quán ăn theo vị trí (Location-based Recommendation)**, **Phân tích khẩu vị AI (Taste DNA)** và **Tối ưu hóa lộ trình di chuyển Food Tour (AI Itinerary & Route Planner)**.

---

## 🏗️ 1. Tổng Quan Kiến Trúc Kỹ Thuật (Mobile Architecture)

* **Framework**: React Native kết hợp **Expo SDK 57** (TypeScript).
* **Routing / Navigation**: Expo Router (File-based Routing).
* **State Management**: Zustand (Đồng bộ với logic Zustand trên Web FE).
* **API Client**: Axios Interceptor (Tự động đính kèm `Authorization: Bearer <token>`, lưu Token vào `Expo SecureStore`).
* **UI Components**: Vanilla StyleSheet / Flexbox responsive + Lucide Icons (`lucide-react-native`).

---

## 📋 2. Bảng Chi Tiết Roadmap & Task Mobile App

### 📌 PHASE 1: Nền Tảng & Luồng Xác Thực (Authentication & Security)
- [x] **Task 1.1: Khởi tạo Repo `KLTN-123-GastroWise-Mobile`**
- [x] **Task 1.2: Màn hình Đăng Nhập (Login Screen UI & API)**
- [x] **Task 1.3: Màn hình Đăng Ký (Register Screen UI & API)**
- [x] **Task 1.4: Màn hình Khôi Phục Mật Khẩu & 2FA TOTP (Forgot Password UI)**
- [x] **Task 1.5: Tích hợp Secure Token Storage & Single Active Session**

---

### 📍 PHASE 2: Trang Chủ & Gợi Ý Sản Phẩm/Nhà Hàng Theo Vị Trí (Location-based Discovery)
- [x] **Task 2.1: Màn hình Trang Chủ (Home Screen UI)**
  - Header GPS Vị trí hiện tại của người dùng.
  - Banner AI Smart Recommendation.
  - Gợi ý món ăn theo Thời tiết thời gian thực (Mưa rào / Nắng nóng).
  - List Danh mục món ăn & Section "Nhà hàng/Món ăn Nổi bật".
- [x] **Task 2.2: Bộ Lọc & Tìm Kiếm Theo Ngân Sách & Khoảng Cách (Search & Filter UI)**
  - Filter Pills (Tất cả, Gần bạn 1-3km, Đánh giá cao 4.5+★, Giá tốt).

---

### 🗺️ PHASE 3: Tối Ưu Hóa Lộ Trình Food Tour AI & Chia Sẻ Chuyến Đi
- [x] **Task 3.1: Màn hình Quản Lý Lộ Trình Food Tour (`/(tabs)/itineraries.tsx`)**
  - Hiển thị danh sách các hành trình trải nghiệm ẩm thực đã được AI khởi tạo (`GET /itineraries`).
  - Hiển thị tổng số điểm dừng, ngân sách dự kiến, thời gian di chuyển và chỉ số tiết kiệm phát thải CO2.
- [x] **Task 3.2: Màn hình Lên Lộ Trình AI Smart Planner (`src/app/ai-planner.tsx`)**
  - Form nhập thông tin hành trình: Từ khóa mong muốn, Vị trí xuất phát, Ngân sách chi tiêu, Thời gian rảnh rỗi.
  - Gọi API Backend `POST /itineraries/generate` để Gemini AI phân tích, chọn 3 địa điểm tối ưu nhất và tính toán thứ tự chặng di chuyển (Stops).
- [x] **Task 3.3: Màn hình Chi Tiết Lộ Trình & Chỉ Đường Chặng (`src/app/itinerary/[id].tsx`)**
  - Hiển thị các điểm dừng theo thứ tự di chuyển 1 ➔ 2 ➔ 3.
  - Nút Mở Google Maps Chỉ Đường từng chặng.
- [ ] **Task 3.4: Modal Chia Sẻ Lộ Trình QR Code & Deep Linking**
  - Render QR Code mã lộ trình Food Tour cho bạn bè quét 1-Click để tham gia chuyến đi.
  - Nút Copy Link và Chia sẻ Native iOS/Android (`Share.share`).

---

### 📁 PHASE 4: Bộ Sưu Tập Yêu Thích Theo Chủ Đề (Smart Favorite Collections)
- [x] **Task 4.1: Hồ Sơ Khẩu Vị AI Taste DNA Profile (`src/app/favorites.tsx`)**
  - Biểu đồ phân tích tỷ lệ % khẩu vị cá nhân (Món Việt, Lẩu Nướng, Cafe, Hải Sản).
- [ ] **Task 4.2: Quản Lý Thư Mục Bộ Sưu Tập Theo Chủ Đề**
  - Cho phép người dùng phân loại nhà hàng yêu thích vào thư mục: *"Quán ăn khuya Gò Vấp"*, *"Hẹn hò 2 người"*, *"Góc chill cafe"*.
  - Modal tạo Bộ sưu tập mới.

---

### ⏰ PHASE 5: Hệ Thống Thông Báo Nhắc Nhở Chuyến Đi (Smart Itinerary Push Reminders)
- [ ] **Task 5.1: Bật Nhắc Nhở Lộ Trình Food Tour**
  - Modal chọn thời gian nhắc nhở (Trước 30 phút, 1 giờ, 2 giờ).
  - Tự động kích hoạt thông báo nhắc nhở khởi hành chuyến đi ăn uống.
