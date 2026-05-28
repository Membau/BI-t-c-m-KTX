# 🍱 Dormitory Meal Ordering BI System

> **Real-time Business Intelligence system** for dormitory meal ordering — automatically receives orders from Facebook comments, analyzes with local AI (Gemma 3 via Ollama), streams data through Kafka 4.2, and displays on a Streamlit Dashboard.

---

## ✨ Key Features

- **Automated Facebook comment reading** via Selenium, pushing to Kafka topics in real time
- **AI-powered order analysis** using Gemma 3 running fully offline (via Ollama), extracting dish names, quantities, addresses, and phone numbers from natural customer text
- **Automatic few-shot learning**: every time an admin corrects an AI error, the system remembers and improves accuracy for next time
- **MapReduce revenue analysis** by dish and order status
- **4-tab Streamlit Dashboard**: BI Reports, Menu Management, Error Comment Review, Delivery Management
- **One-click launch** on Windows via `run_project.bat`

---

## 🏗️ System Architecture

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
                  (AI confirmed)           (AI uncertain)
                          │
                          ▼
                       app.py  (Streamlit Dashboard)
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         BI Reports   Delivery   AI Error Review
```

---

## 📁 Directory Structure

```
BI-t-c-m-KTX/
├── data/
│   ├── menu.xlsx              # Menu (Dish Name, Price, Status)
│   └── few_shot_examples.json # AI training examples, auto-updated on admin corrections
├── output/                    # Auto-created on run
│   ├── stream_orders.csv      # Orders awaiting delivery
│   ├── shipped_orders.csv     # Delivered orders
│   └── pending_reviews.csv    # Comments AI couldn't process
├── AI_consumer.py             # Module calling Gemma 3 to parse orders
├── app.py                     # Main Streamlit Dashboard
├── consumer_fb.py             # Kafka consumer processing comments
├── generate_sample_data.py    # Generate sample data for testing
├── getComment.py              # Facebook comment crawler using Selenium
├── mapreduce_analysis.py      # MapReduce analysis (revenue, dish quantities)
├── producer_fb.py             # Kafka producer pushing comments to topic
├── requirements.txt
└── run_project.bat            # Full system startup script (Windows)
```

---

## ⚙️ System Requirements

| Component | Version |
|---|---|
| Python | ≥ 3.10 |
| Apache Kafka | 4.2+ |
| Ollama | Latest |
| AI Model | `gemma3` (pull via Ollama) |
| OS | Windows (has `.bat`), Linux/macOS also supported |

---

## 🚀 Installation & Running

### 1. Clone repo

```bash
git clone https://github.com/Membau/BI-t-c-m-KTX.git
cd BI-t-c-m-KTX
```

### 2. Install Python libraries

```bash
pip install -r requirements.txt
pip install streamlit plotly openpyxl kafka-python
```

### 3. Install and start Ollama + Gemma 3

```bash
# Install Ollama at https://ollama.com
ollama pull gemma3
ollama serve
```

### 4. Start Kafka

Download Apache Kafka 4.2, extract, then run:

```bash
# KRaft mode (no Zookeeper needed)
bin/kafka-server-start.sh config/kraft/server.properties
```

### 5. Create Kafka topic

```bash
bin/kafka-topics.sh --create --topic fb_comments --bootstrap-server localhost:9092
```

### 6. Run the full system

**Windows (1 click):**
```
run_project.bat
```

**Manual (open 3 terminals):**
```bash
# Terminal 1: AI Consumer
python consumer_fb.py

# Terminal 2: Facebook Crawler
python getComment.py

# Terminal 3: Dashboard
streamlit run app.py
```

Access dashboard at: `http://localhost:8501`

---

## 📊 Dashboard Usage Guide

| Tab | Function |
|---|---|
| 📊 BI Reports | View actual/projected revenue, order composition charts, top-selling dishes (MapReduce) |
| 🍴 Menu Management | Add/edit/delete dishes, update prices and availability (Available / Out of stock) |
| 🔎 Error Comment Review | Review comments AI couldn't parse, manually correct and re-train AI |
| 🚚 Delivery | View pending orders, fix AI misreads, confirm delivery |

> 💡 **Tip:** After changing the Menu, restart `consumer_fb.py` so the AI loads the new menu.

---

## 🧠 AI Learning Mechanism

The system uses **dynamic few-shot prompting**:

1. AI reads `few_shot_examples.json` each time it processes a comment
2. When an admin fixes an error in the "Error Comment Review" or "Delivery" tab, the `(comment → correct order)` pair is written to this file
3. Next time, AI uses these examples to reason more accurately — **no model retraining needed**

---

## 🔧 Customization

- **Change Facebook Page/Post:** edit URL in `getComment.py`
- **Switch AI model:** replace `"gemma3"` with another model name in `AI_consumer.py` (model must be pulled via Ollama first)
- **Add new data sources:** create a new producer pushing to the same Kafka topic

---

## 📦 Main Dependencies

```
selenium       # Crawl Facebook comments
requests       # Call Ollama API
ollama         # (optional) Python client for Ollama
pandas         # Data processing
streamlit      # Dashboard UI
plotly         # Charts
openpyxl       # Read/write Excel files (menu.xlsx)
kafka-python   # Kafka producer/consumer
```

---

## 📝 License

Academic project — free to use and modify.

---
---

# 🍱 Hệ thống BI Đặt Cơm Ký Túc Xá

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
