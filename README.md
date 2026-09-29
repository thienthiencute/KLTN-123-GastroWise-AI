# GastroWise AI Microservice 🤖🌧️☀️

> **Dịch vụ AI thông minh**: Vector Search (TF-IDF), Nhận diện hình ảnh món ăn (YOLOv11m), Phân tích cảm xúc (VisoBERT), Chatbot tư vấn & Gợi ý thời tiết GPS Realtime.

---

## 📌 1. Các Tính Năng AI Đã Triển Khai

| Endpoint | Phương Thức | Mô Tả Chức Năng | Công Nghệ Sử Dụng |
| :--- | :--- | :--- | :--- |
| `GET /` | `GET` | Kiểm tra trạng thái hoạt động của AI Service | FastAPI |
| `POST /recommend` | `POST` | Gợi ý nhà hàng theo ngữ nghĩa từ khóa & tọa độ GPS | TF-IDF + Cosine Similarity |
| `POST /weather-recommend` | `POST` | **[MỚI] Gợi ý món ăn theo thời tiết & GPS realtime** | Open-Meteo Weather API + Weather-Food Matrix |
| `POST /predict-food` | `POST` | Nhận diện món ăn từ hình ảnh camera / thư viện | Computer Vision YOLOv11m (`best.pt`) |
| `POST /sentiment` | `POST` | Phân tích cảm xúc bài đánh giá (Tích cực / Tiêu cực) | HuggingFace VisoBERT |
| `POST /chat` | `POST` | Chatbot tư vấn ẩm thực tự động | Conversational Vector Agent |

---

## 🛠️ 2. Hướng Dẫn Cài Đặt & Khởi Chạy

### Yêu cầu môi trường:
* Python 3.9 - 3.11
* MongoDB Atlas hoặc Local MongoDB running on port 27017

### Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

### Khởi chạy AI Service:
```bash
python api.py
```
*Dịch vụ AI sẽ khởi chạy tại*: `http://127.0.0.1:5000`

---

## 🌦️ 3. Chi Tiết Endpoint Gợi Ý Theo Thời Tiết (`POST /weather-recommend`)

### Request Body:
```json
{
  "user_gps": [10.7769, 106.7009],
  "temperature": null,
  "weather_condition": null
}
```

### Response Body:
```json
{
  "weather": {
    "temperature": 23.5,
    "condition_text": "Mưa rào",
    "condition_code": 61,
    "banner_title": "🌧️ Trời đang mưa lạnh (23.5°C)",
    "banner_desc": "Thời tiết lý tưởng để thưởng thức Lẩu thái, Phở nóng & Đồ nướng BBQ!"
  },
  "scores": [
    {
      "id": "6a7d8da3c8148b897824b16a",
      "name": "Lẩu Bò Ba Toa - Sài Gòn",
      "tags": "MÓN LẨU, lẩu bò, nướng",
      "S_taste": 0.95,
      "distance_km": 1.4,
      "price": 150000
    }
  ]
}
```
