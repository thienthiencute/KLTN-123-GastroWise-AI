# Feature Breakdown & Implementation Guide
## Phân rã tính năng & Nhận diện tiến độ thực thi (Dành cho Dev Team & AI)

Tài liệu này theo dõi toàn bộ danh sách tính năng (Roadmap) của dự án GastroWise. Khi triển khai thành công một task, AI/Dev sẽ cập nhật dấu `[x]` và lưu nhật ký thực thi bên dưới.

---

### Module 1: Trang chủ & Xác thực (Home & Auth System) - ĐÃ HOÀN THÀNH
- [x] **Trang chủ (Landing Page):** Giới thiệu hệ thống, thanh tìm kiếm nhanh, danh sách quán ăn nổi bật/đánh giá cao (Top rated).
- [x] **Đăng nhập / Đăng ký (Email + Password):** Form validate với Zod + React Hook Form. Mã hóa mật khẩu bcrypt, lưu JWT Token an toàn và loại bỏ các trường nhạy cảm (`password`, `hashedRefreshToken`).
- [x] **Google Single Sign-On (OAuth 2.0):** Tích hợp Google OAuth 1-Click login với tự động redirect và lấy thông tin Profile.
- [x] **Tự động gia hạn Token & Bảo vệ Route:** Axios Interceptors tự động đính kèm `Bearer Token` và tự động bảo vệ các trang cá nhân (`/profile`, `/favorites`).

---

### Module 2: Hồ sơ Cá nhân & Quản lý User (User Profile & Preferences) - ĐÃ HOÀN THÀNH
- [x] **Trang Hồ sơ (`/profile`):** Hiển thị thông tin cá nhân (`firstName`, `lastName`, `phone`, `email`, `picture`), chỉnh sửa profile và đăng xuất.
- [x] **Upload Avatar (`POST /auth/avatar`):** Tải lên và thay đổi ảnh đại diện cá nhân lưu trữ tại máy chủ backend.
- [x] **Quản lý Danh sách Yêu thích (`/favorites` - `savedRestaurants`):** Thả tim/Lưu quán ăn yêu thích tại các thẻ `RestaurantCard` và đồng bộ mảng `savedRestaurants` trong MongoDB.
- [x] **Thiết lập Khẩu vị AI (`/preferences` - `preferences`):** Giao diện Wizard chọn sở thích ẩm thực, mức giá và tag vị trí để truyền vào AI Engine.

---

### Module 3: Khám phá & Gợi ý Lộ trình AI (Explore & AI Journey) - ĐÃ HOÀN THÀNH
- [x] **Trang Khám phá (`/explore`):** Giao diện hiển thị danh sách quán ăn theo dạng thẻ, tích hợp bộ lọc đa tiêu chí.
- [x] **Trang Chi tiết Quán ăn (`/restaurant/[id]`):** Hiển thị thông tin chi tiết (ảnh, địa chỉ, rating, menu, đánh giá cộng đồng).
- [x] **Lên Lộ trình AI (`/ai-planner`):** Chatbox tương tác kiểu AI, gợi ý nhà hàng và tự động tạo chuyến đi (`Itinerary`).

---

### Module 4: Các Tính năng Nghiệp vụ Nâng cao (Advanced Business Features) - ĐÃ HOÀN THÀNH
- [x] **AI Taste DNA Profile (Hồ sơ Khẩu vị Thông minh):** Component `AiTasteDnaCard` tự động phân tích mảng `preferences` và `savedRestaurants` để hiển thị tỷ lệ % sở thích ẩm thực (Món Việt, Món Cay, Cafe, Hải sản) cùng danh hiệu AI trên trang `/profile`.
- [x] **Smart Favorite Collections (Bộ sưu tập Yêu thích Theo chủ đề):** Thanh điều hướng bộ lọc danh mục (Món Việt, Lẩu & Nướng, Cafe, Đồ ăn nhanh) và ô tìm kiếm trực tiếp trong trang `/favorites`.
- [x] **Eco-Smart Travel Tracker:** Thống kê tổng số km di chuyển được tối ưu và lượng khí thải CO2 giảm thiểu tương đương (1.5kg CO2) hiển thị tại tab Thành tích Eco ở `/profile`.

---

### Module 5: Hệ Thống Quản Trị Admin & Investor Dashboard (Port 3002 - CMS & CRM System)
- [x] **Task 5.1: Overview Analytics Dashboard (`/` - Port 3002):** Biểu đồ Recharts (Line/AreaChart & PieChart) kết nối API thật lấy tổng số Nhà hàng (178+), Người dùng (CRM), Lượt tìm kiếm AI Itinerary & GMV.
- [x] **Task 5.2: CMS Quản Lý Nhà Hàng (`/restaurants`):** Bảng Data Table kết nối MongoDB Atlas Backend, hỗ trợ tìm kiếm trực tiếp, xem chi tiết Modal, Thêm nhà hàng mới (`POST`) và Xóa nhà hàng (`DELETE`).
- [x] **Task 5.3: CMS Quản Lý Thực Đơn (`/menu`):** Quản lý danh sách Món ăn theo từng Nhà hàng, thêm món mới, cập nhật giá & gán nhãn Hot/Món chay. Kết nối API Backend real-time & AI Smart Menu Generator.
- [x] **Task 5.4: CRM Quản Lý Người Dùng & Phân Quyền (`/users`):** Quản lý danh sách User, hiển thị Vai trò (User / Owner / Admin), Trạng thái tài khoản & Hồ sơ khẩu vị. Kết nối API Backend real-time & Hỗ trợ Đổi Role/Khóa tài khoản.
- [x] **Task 5.5: CRM Quản Lý Đánh Giá & Kiểm Duyệt (`/reviews`):** Quản lý Đánh giá cộng đồng, duyệt/ẩn đánh giá vi phạm, hiển thị nhãn phân tích cảm xúc AI Sentiment. Kết nối API Backend real-time & Chạy AI Sentiment Re-Scan.
- [x] **Task 5.6: AI Business Insights & Báo Cáo (`/ai-insights`):** AI phân tích xu hướng món ăn hot, thống kê lượng khách ghé quán, cảnh báo thời gian phục vụ & Xuất báo cáo CSV/PDF.

---

### Module 6: Hệ thống Thông báo (Notification System) - ĐÃ HOÀN THÀNH
- [x] **Notifications Bell:** Chuông thông báo góc phải Navbar hiển thị danh sách thông báo thời gian thực (`useGetNotifications`), tự động làm mới mỗi 30s và hỗ trợ đánh dấu đã đọc (`markAsRead`).

---

### Module 7: Đánh giá Cộng đồng & Phân tích Sentiment AI (Review & AI Sentiment System) - ĐÃ HOÀN THÀNH
- [x] **Form Viết Đánh Giá Chi Tiết (`/restaurant/[slug]`):** Cho phép người dùng gửi nhận xét, số sao (1-5★) và hình ảnh món ăn trực tiếp tại trang Chi tiết nhà hàng với Modal xịn xò.
- [x] **Tự động Phân tích Cảm xúc AI (AI Sentiment Analysis):** Tự động gửi nội dung nhận xét tới AI Sentiment Service để phân tích nhãn (POSITIVE/NEGATIVE/NEUTRAL) và trích xuất `hashtags`, sau đó lưu vào MongoDB.
  - **Mô hình AI (Model):** Google Gemini (cụ thể: `gemini-1.5-flash` / `gemini-2.5-flash`).
  - **Công cụ / SDK (Tool):** npm package `@google/generative-ai` tích hợp trực tiếp vào Node.js Backend.
- [x] **AI Review Summarizer (`AiReviewSummaryCard`):** Component AI tổng hợp tự động ưu điểm, hạn chế và tỷ lệ hài lòng % của cộng đồng hiển thị ở đầu danh sách đánh giá.

---

### Module 8: Các Tính năng AI Đột Phá & Tiện Ích Nâng Cao (Next-Gen AI Innovations) - ĐÃ HOÀN THÀNH
- [x] **AI Smart Food Camera & NutriAnalyzer (`/ai-nutri`):** Tải/chụp ảnh đĩa ăn ➔ AI quét thị giác nhận diện tên món, phân tích Calo (kcal), đạm (Protein), tinh bột (Carbs), béo (Fat) và đưa ra lời khuyên dinh dưỡng.
- [x] **AI Dynamic Weather & Health Recommender:** Component `AiWeatherRecommendationCard` tự động gợi ý món ăn chuẩn y khoa theo thời tiết thực tế (Mưa rào/Nắng nóng) & vị trí GPS.
- [x] **AI Budget & Route Food Tour Planner (`/ai-planner`):** Tự động phân bổ ngân sách theo từng mức chi tiêu (150k - 1M) và tối ưu hóa tuyến đường di chuyển giữa các quán.
- [x] **AI Menu Translator & Cultural Explainer:** Hỗ trợ phiên dịch thực đơn 4 ngôn ngữ (VI/EN/JA/KO) và Modal AI giải thích nguồn gốc, văn hóa ẩm thực các món ăn truyền thống.

---

## 📝 Nhật Ký Thực Thi Tasks (Task Completion Log)

| Ngày hoàn thành | Module / Task | Mô tả chi tiết & File đã chỉnh sửa |
| :--- | :--- | :--- |
| **08/09/2026** | **Tái cấu trúc Tài liệu (`docs/`)** | Gom tất cả 15+ file MD vào thư mục `docs/` phân loại theo 5 chủ đề. |
| **08/09/2026** | **Khắc phục Xung đột Port & Dependencies** | Đổi Port Admin FE sang 3002. Cài đặt bổ sung gói `sonner` tại FE. |
| **08/09/2026** | **Auth & Security Optimization** | Thêm hàm `_sanitizeUser` bảo mật `password` hash. Cấu hình Axios Interceptors. |
| **09/09/2026** | **MongoDB User Schema Alignment** | Ánh xạ mảng `savedRestaurants` & `preferences` từ MongoDB vào `UpdateUserDto` và `favorites.service.ts`. |
| **09/09/2026** | **AI Taste DNA & Smart Collections** | Tạo `AiTasteDnaCard.tsx` tại `/profile` và thêm bộ lọc Collection Filter & Search tại `/favorites`. |
| **09/09/2026** | **Eco Tracker & Notification Bell** | Hoàn thiện Notification Bell dropdown trên Navbar và tab Thành tích Eco Tracker tại `/profile`. |
| **09/09/2026** | **Sửa lỗi 500 Slug Lookup** | Hỗ trợ tìm kiếm Nhà hàng, Menu và Review theo cả `slug` và `ObjectId` tại Backend. |
| **09/09/2026** | **AI Review Sentiment & Summary** | Hoàn thiện `ReviewModal.tsx`, `AiReviewSummaryCard.tsx` và tự động phân tích cảm xúc AI với `POST /reviews`. |
| **09/09/2026** | **Next-Gen AI Innovations (Module 8)** | Hoàn thành `/ai-nutri` (Food Camera & Calorie Tracker), `AiWeatherRecommendationCard.tsx` (Gợi ý món theo thời tiết), AI Budget & Route Planner tại `/ai-planner`, và AI Menu Translator 4 ngôn ngữ + Cultural Explainer tại `RestaurantMenu.tsx`. |
| **09/09/2026** | **Admin Analytics & CMS (Module 5)** | Kết nối Admin FE (Port 3002) với MongoDB Backend, nâng cấp Biểu đồ Recharts tại `/` và hoàn thiện CMS Quản lý Nhà hàng (`/restaurants`) với Thêm mới, Xóa & Tìm kiếm trực tiếp. |
| **09/09/2026** | **Admin CMS Menu (Task 5.3)** | Hoàn thiện CMS Quản lý Thực đơn (`/menu`) kết nối API `/restaurants/menu/all`, bổ sung AI Menu Generator, bộ lọc theo Nhà hàng, Thêm món thủ công & Xóa món. |
| **09/09/2026** | **Admin CRM Users (Task 5.4)** | Hoàn thiện CRM Quản lý Người dùng (`/users`) kết nối MongoDB API `/users`, hiển thị Avatar, Email, Role Badges, Hồ sơ khẩu vị AI, đổi vai trò (Role) và Khóa/Mở khóa tài khoản. |
| **09/09/2026** | **Admin CRM Reviews (Task 5.5)** | Hoàn thiện CRM Quản lý Đánh giá & AI Sentiment (`/reviews`) kết nối `/reviews`, hỗ trợ duyệt/ẩn bài viết vi phạm, phân loại cảm xúc POS/NEU/NEG và chạy AI Sentiment Re-Scan. |
| **09/09/2026** | **Admin AI Insights (Task 5.6)** | Hoàn thiện AI Business Insights & Báo cáo (`/ai-insights`), thống kê tổng quan hệ thống, phân tích phản hồi tiêu cực/tích cực, gợi ý Smart Promo và Xuất báo cáo CSV & In PDF. |
| **09/09/2026** | **Biên dịch & Type Check System** | Biên dịch thành công `npx nest build` và `tsc --noEmit` với **0 lỗi**. |
