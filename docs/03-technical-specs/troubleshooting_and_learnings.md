# GastroWise - Nhật Ký Lỗi & Kiến Thức Kỹ Thuật (Troubleshooting & Learnings)

Tài liệu này ghi chép lại các sự cố kỹ thuật, nguyên nhân gốc rễ (Root Cause), giải pháp xử lý và bài học kinh nghiệm trong quá trình phát triển dự án **GastroWise**.

---

## 1. Lỗi Xung đột Port giữa Backend và Admin Frontend
- **Thời gian:** 08/09/2026
- **Triệu chứng:** Cả Backend (`KLTN-123-GastroWise-BE`) và Admin Frontend (`KLTN-123-GastroWise-Admin-FE`) đều sử dụng chung Port `3001`. Khi chạy đồng thời 2 dịch vụ sẽ gây ra lỗi `EADDRINUSE`.
- **Nguyên nhân:** File `package.json` của Admin-FE đặt mặc định script `"dev": "next dev -p 3001"`.
- **Khắc phục:** 
  - Đổi Port của Admin-FE sang **Port 3002** trong `KLTN-123-GastroWise-Admin-FE/package.json`: `"dev": "next dev -p 3002"`.
  - Cập nhật file `KLTN-123-GastroWise-Admin-FE/.env.local` trỏ API về Backend port `3001`.

---

## 2. Lỗi `Module not found: Can't resolve 'sonner'` tại Customer FE
- **Thời gian:** 08/09/2026
- **Triệu chứng:** Khi khởi chạy Next.js tại `KLTN-123-GastroWise-FE`, trang báo lỗi 500: `Can't resolve 'sonner'`.
- **Nguyên nhân:** Gói `sonner` chưa được cài đặt đầy đủ trong `node_modules` ở repo `KLTN-123-GastroWise-FE`.
- **Khắc phục:** Chạy `npm install` tại thư mục `KLTN-123-GastroWise-FE`.

---

## 3. Lỗi `:3001/auth/register Failed to load resource: net::ERR_CONNECTION_REFUSED`
- **Thời gian:** 08/09/2026
- **Triệu chứng:** Người dùng bấm Đăng ký/Đăng nhập từ Web UI bị báo lỗi trình duyệt: `net::ERR_CONNECTION_REFUSED` khi kết nối tới `http://localhost:3001`.
- **Nguyên nhân Gốc rễ (Root Cause):** 
  - Backend NestJS chưa khởi chạy được hoàn tất trên Port `3001` vì **MongoDB Atlas đang chặn địa chỉ IP mạng hiện tại** (`MongooseServerSelectionError: Could not connect to any servers in your MongoDB Atlas cluster. IP isn't whitelisted`).
  - Mongoose cố kết nối lại liên tục làm Server NestJS bị treo (hang) ở giai đoạn Bootstrap.
- **Khắc phục:**
  1. Thêm `serverSelectionTimeoutMS: 5000` vào `MongooseModule.forRootAsync` trong `app.module.ts` để tránh treo tiến trình NestJS.
  2. **Thêm IP Mạng vào Whitelist của MongoDB Atlas:**
     - Truy cập MongoDB Atlas Console ➔ **Network Access** ➔ Thêm IP hiện tại hoặc thêm `0.0.0.0/0` (Allow Access From Anywhere) để cho phép kết nối từ mọi mạng Wifi/IP.

---

## 4. Bài Học & Quy Trình Khởi Chạy Chuẩn (Tech Lead Checklist)

1. **Kiểm tra MongoDB Atlas IP Whitelist:**
   - Khi đổi mạng Wifi, IP động của nhà mạng sẽ bị thay đổi. Cần đảm bảo MongoDB Atlas Network Access cấu hình `0.0.0.0/0`.
2. **Quy hoạch Port chuẩn cho hệ thống:**
   - **Port 3000:** Customer Frontend (`KLTN-123-GastroWise-FE`)
   - **Port 3001:** Backend NestJS (`KLTN-123-GastroWise-BE`)
   - **Port 3002:** Admin Frontend (`KLTN-123-GastroWise-Admin-FE`)
