# GastroWise AI Microservice 🤖🌧️☀️

> **Dịch vụ AI thông minh (Enterprise Modular Tree Architecture)**: Vector Search (TF-IDF), Nhận diện hình ảnh món ăn (YOLOv11m), Phân tích cảm xúc (ViSoBERT & Vietnamese Rule-Based), Chatbot tư vấn & Gợi ý thời tiết GPS Realtime.

---

## 📌 1. Các Tính Năng AI Đã Triển Khai

| Endpoint | Phương Thức | Mô Tả Chức Năng | Công Nghệ Sử Dụng |
| :--- | :--- | :--- | :--- |
| `GET /` | `GET` | Kiểm tra trạng thái hoạt động & cấu trúc AI Service | FastAPI (Lifespan Manager) |
| `POST /recommend` | `POST` | Gợi ý nhà hàng theo ngữ nghĩa từ khóa & tọa độ GPS | TF-IDF + Cosine Similarity |
| `POST /weather-recommend` | `POST` | Gợi ý món ăn theo thời tiết & GPS realtime | Open-Meteo Weather API + Weather-Food Matrix |
| `POST /predict-food` | `POST` | Nhận diện món ăn từ hình ảnh camera / thư viện | Computer Vision YOLOv11m (`best.pt`) |
| `POST /sentiment` | `POST` | Phân tích cảm xúc bài đánh giá (Tích cực / Tiêu cực) | HuggingFace ViSoBERT |
| `POST /analyze-sentiment` | `POST` | Phân tích cảm xúc & trích xuất Hashtag tự động | Vietnamese Rule-based NLP |
| `POST /chat` | `POST` | Chatbot tư vấn ẩm thực tự động | Conversational Vector Agent |

---

## 🏗️ 2. Cấu Trúc Cây Thư Mục Enterprise (Production Tree)

```
KLTN-123-GastroWise-AI/
├── main.py                        # Entrypoint chính khởi chạy FastAPI application
├── api.py                         # File wrapper tương thích ngược 100%
├── app/                           # Mã nguồn ứng dụng
│   ├── config.py                  # Cấu hình, biến môi trường, Từ điển EN-VI
│   ├── schemas/                   # Pydantic DTO (recommendation, weather, sentiment, vision)
│   ├── db/                        # Mongo DB Atlas Loader & TF-IDF Caching
│   ├── core/                      # Core ML algorithms & Services (recommender, weather, sentiment, vision)
│   └── api/v1/                    # API Controllers (Routers)
```

---

## 🛠️ 3. Hướng Dẫn Khởi Chạy AI Service

### Cách 1: Khởi chạy chuẩn Enterprise (Khuyên dùng)
```bash
python main.py
```
hoặc dùng uvicorn trực tiếp:
```bash
uvicorn main:app --host 127.0.0.1 --port 5000 --reload
```

### Cách 2: Khởi chạy theo lệnh cũ (Backward Compatible)
```bash
python api.py
```

👉 **Dịch vụ AI sẽ khởi chạy tại**: `http://127.0.0.1:5000`  
👉 **API Documentation (Swagger UI)**: `http://127.0.0.1:5000/docs`

---

## 🚀 4. Hướng Dẫn Khởi Chạy Toàn Bộ Hệ Thống GastroWise (Full-Stack)

Để chạy trọn vẹn toàn bộ hệ thống dự án cho nhóm:

1. **AI Microservice (Port 5000):**
   ```bash
   cd KLTN-123-GastroWise-AI
   python main.py
   ```

2. **Backend NestJS (Port 3001):**
   ```bash
   cd KLTN-123-GastroWise-BE
   npm run start:dev
   ```

3. **Frontend Next.js (Port 3000):**
   ```bash
   cd KLTN-123-GastroWise-FE
   npm run dev
   ```
