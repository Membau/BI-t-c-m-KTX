# 🍱 Hệ thống BI Đặt Cơm KTX

> **Hệ thống Business Intelligence thời gian thực** cho dịch vụ đặt cơm ký túc xá — tự động nhận đơn từ bình luận Facebook, phân tích bằng AI cục bộ (Gemma 3 qua Ollama), streaming dữ liệu qua Kafka 4.2, và hiển thị trên Dashboard Streamlit.

---

## ✨ Tính năng nổi bật

- **Tự động đọc bình luận Facebook** bằng Selenium, đẩy vào Kafka topic theo thời gian thực
- **AI phân tích đơn hàng** bằng mô hình Gemma 3 chạy hoàn toàn offline (qua Ollama), trích xuất món ăn, số lượng, địa chỉ, SĐT từ văn bản tự nhiên của khách
- **Few-shot learning tự động**: mỗi lần admin sửa lỗi AI, hệ thống ghi nhớ và cải thiện độ chính xác cho lần sau
- **MapReduce phân tích doanh thu** theo món, theo trạng thái đơn
- **Dashboard Streamlit 4 tab**: Báo cáo BI, Quản lý Menu, Duyệt Comment Lỗi, Quản lý Giao hàng
- **Chạy 1 click** trên Windows với file `run_project.bat`

---

## 🏗️ Kiến trúc hệ thống

```
Facebook Comments
      │
      ▼
 getComment.py  ──(Selenium)──►  producer_fb.py
                                       │
                                  Kafka Topic
                                       │
                              consumer_fb.py / AI_consumer.py
                                       │
                          ┌────────────┴────────────┐
                          ▼                         ▼
                  stream_orders.csv        pending_reviews.csv
                  (AI chốt được)           (AI không chắc)
                          │
                          ▼
                       app.py  (Streamlit Dashboard)
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         Báo cáo BI   Giao hàng   Duyệt lỗi AI
```

---

## 📁 Cấu trúc thư mục

```
BI-t-c-m-KTX/
├── data/
│   ├── menu.xlsx              # Thực đơn (Tên Món, Giá, Trạng Thái)
│   └── few_shot_examples.json # Ví dụ dạy AI, tự cập nhật khi admin sửa lỗi
├── output/                    # Tự tạo khi chạy
│   ├── stream_orders.csv      # Đơn hàng đang chờ giao
│   ├── shipped_orders.csv     # Đơn đã giao
│   └── pending_reviews.csv    # Comment AI chưa xử lý được
├── AI_consumer.py             # Module gọi Gemma 3 để parse đơn hàng
├── app.py                     # Dashboard Streamlit chính
├── consumer_fb.py             # Kafka consumer xử lý comment
├── generate_sample_data.py    # Tạo dữ liệu mẫu để test
├── getComment.py              # Crawler bình luận Facebook bằng Selenium
├── mapreduce_analysis.py      # Phân tích MapReduce (doanh thu, số lượng món)
├── producer_fb.py             # Kafka producer đẩy comment vào topic
├── requirements.txt
└── run_project.bat            # Script khởi động toàn bộ hệ thống (Windows)
```

---

## ⚙️ Yêu cầu hệ thống

| Thành phần | Phiên bản |
|---|---|
| Python | ≥ 3.10 |
| Apache Kafka | 4.2+ |
| Ollama | Mới nhất |
| Model AI | `gemma3` (kéo qua Ollama) |
| Hệ điều hành | Windows (có `.bat`), Linux/macOS cũng chạy được |

---

## 🚀 Cài đặt & Chạy

### 1. Clone repo

```bash
git clone https://github.com/Membau/BI-t-c-m-KTX.git
cd BI-t-c-m-KTX
```

### 2. Cài thư viện Python

```bash
pip install -r requirements.txt
pip install streamlit plotly openpyxl kafka-python
```

### 3. Cài và khởi động Ollama + Gemma 3

```bash
# Cài Ollama tại https://ollama.com
ollama pull gemma3
ollama serve
```

### 4. Khởi động Kafka

Tải Apache Kafka 4.2, giải nén, rồi chạy:

```bash
# KRaft mode (không cần Zookeeper)
bin/kafka-server-start.sh config/kraft/server.properties
```

### 5. Tạo Kafka topic

```bash
bin/kafka-topics.sh --create --topic fb_comments --bootstrap-server localhost:9092
```

### 6. Chạy toàn bộ hệ thống

**Windows (1 click):**
```
run_project.bat
```

**Thủ công (mở 3 terminal):**
```bash
# Terminal 1: Consumer AI
python consumer_fb.py

# Terminal 2: Crawler Facebook
python getComment.py

# Terminal 3: Dashboard
streamlit run app.py
```

Truy cập dashboard tại: `http://localhost:8501`

---

## 📊 Hướng dẫn sử dụng Dashboard

| Tab | Chức năng |
|---|---|
| 📊 Báo cáo BI | Xem doanh thu thực tế / dự kiến, biểu đồ cơ cấu đơn, top món bán chạy (MapReduce) |
| 🍴 Quản lý Menu | Thêm/sửa/xóa món ăn, cập nhật giá và trạng thái (Có / Hết) |
| 🔎 Duyệt Comment Lỗi | Xem lại các comment AI không tự phân tích được, admin sửa tay và "dạy" lại AI |
| 🚚 Giao hàng | Xem danh sách đơn chờ giao, sửa thông tin nếu AI nhận sai, xác nhận đã giao |

> 💡 **Mẹo:** Sau khi thay đổi Menu, khởi động lại `consumer_fb.py` để AI nạp thực đơn mới.

---

## 🧠 Cơ chế học của AI

Hệ thống sử dụng **few-shot prompting động**:

1. AI đọc file `few_shot_examples.json` mỗi lần xử lý comment
2. Khi admin sửa lỗi trong tab "Duyệt Comment Lỗi" hoặc "Giao hàng", cặp `(comment → đơn hàng đúng)` được ghi vào file này
3. Lần sau AI sẽ dùng ví dụ đó để suy luận chính xác hơn — **không cần train lại model**

---

## 🔧 Tùy chỉnh

- **Thay đổi Facebook Page/Post:** sửa URL trong `getComment.py`
- **Đổi model AI:** thay `"gemma3"` thành tên model khác trong `AI_consumer.py` (yêu cầu model đó đã được pull qua Ollama)
- **Thêm nguồn dữ liệu mới:** tạo producer mới đẩy vào cùng Kafka topic

---

## 📦 Dependencies chính

```
selenium       # Crawl bình luận Facebook
requests       # Gọi Ollama API
ollama         # (tùy chọn) Python client cho Ollama
pandas         # Xử lý dữ liệu
streamlit      # Dashboard UI
plotly         # Biểu đồ
openpyxl       # Đọc/ghi file Excel (menu.xlsx)
kafka-python   # Kafka producer/consumer
```

---

## 📝 Giấy phép

Dự án học thuật — tự do sử dụng và chỉnh sửa.
