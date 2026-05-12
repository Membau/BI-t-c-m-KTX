# 🍱 Hệ thống BI Đặt Cơm KTX (Real-time Event-Driven Architecture)

> **Hệ thống Business Intelligence thời gian thực** cho dịch vụ đặt cơm ký túc xá đa chi nhánh. Hệ thống tiếp nhận đơn từ dữ liệu Stream đa cửa hàng, phân tích bằng AI cục bộ (Gemma 3 qua Ollama), streaming và tính toán bằng PySpark thông qua Apache Kafka 4.2, và hiển thị trên Dashboard Streamlit.

---

## ✨ Tính năng nổi bật

- **Kiến trúc Event-Driven hoàn chỉnh**: Dữ liệu luân chuyển liên tục qua Kafka từ lúc nhận đơn thô cho tới khi phân tích BI.
- **AI phân tích đơn hàng cục bộ**: Sử dụng mô hình Gemma 3 qua Ollama để trích xuất món ăn, số lượng, địa chỉ, SĐT từ các dòng comment tự nhiên của khách.
- **Few-shot learning tự động**: Mỗi lần admin sửa lỗi AI trên giao diện, hệ thống ghi nhớ và tự động cải thiện độ chính xác cho lần sau mà không cần huấn luyện lại model.
- **PySpark Real-time Analytics**: Lắng nghe sự kiện "Giao hàng thành công" từ Kafka để gom nhóm và tính toán doanh thu các chi nhánh theo thời gian thực.
- **Dashboard Streamlit 4 tab**: Báo cáo BI (PySpark), Quản lý Menu, Duyệt Comment Lỗi, Quản lý Giao hàng.
- **Tự động hóa hoàn toàn trên Windows**: Chạy 8 tiến trình ngầm chỉ với 1 cú click qua file `run_project.bat`.

---

## 🏗️ Kiến trúc hệ thống (Data Flow)

```text
       [1] Fake Stream / Facebook Crawler (Tạo Comment thô đa chi nhánh)
                             │
                             ▼
              Kafka Topic: facebook_orders_stream
                             │
                             ▼
       [2] AI Consumer (Gemma 3 parse text -> JSON)
                             │
                             ▼
                   [3] Streamlit Dashboard 
                      (Tab 4: Chờ Duyệt)
                             │
                      (User click "Đã giao")
                             │
                             ▼
              Kafka Topic: shipped_orders_stream
                             │
                             ▼
      [4] PySpark Streaming (Tính tổng doanh thu theo Store)
                             │
                             ▼
                      spark_summary.json
                             │
                             ▼
                   [5] Streamlit Dashboard 
                    (Tab 1: Báo Cáo BI Realtime)
```

---

## 📁 Cấu trúc thư mục

```
BI-t-c-m-KTX/
├── data/
│   ├── menu.xlsx              # Thực đơn (Tên Món, Giá, Trạng Thái)
│   └── few_shot_examples.json # Ví dụ dạy AI, tự cập nhật khi admin sửa lỗi hoặc hủy rác
├── hadoop/                    # (Windows only) Chứa winutils.exe và hadoop.dll cho PySpark
├── output/                    
│   ├── stream_orders.csv      # Đơn hàng đang chờ giao
│   ├── shipped_orders.csv     # Đơn đã giao (Lịch sử vĩnh viễn)
│   └── spark_summary.json     # Kết quả tính toán real-time của PySpark
├── AI_consumer.py             # Module gọi Gemma 3 để parse đơn hàng
├── app.py                     # Dashboard Streamlit chính (UI + Kafka Producer)
├── consumer_fb.py             # Kafka consumer xử lý comment và gọi AI
├── fake_stream.py             # Giả lập luồng comment từ nhiều KTX (A, B, C...)
├── spark_stream.py            # PySpark Structured Streaming lắng nghe đơn đã giao
├── requirements.txt           # Thư viện Python
└── run_project.bat            # Script khởi động toàn bộ hệ thống (Windows)
```

---

## ⚙️ Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|---|---|
| OS | Windows (khuyến nghị chạy `.bat`), Linux/macOS có thể tự dịch script bash |
| Java | JDK 17 (Bắt buộc cho PySpark) |
| Python | ≥ 3.10 |
| Apache Kafka | Bản 4.2+ (Hỗ trợ KRaft Mode) |
| Hadoop | Binaries (winutils) cho Windows đã được tích hợp sẵn |
| Ollama | Cài đặt Ollama cục bộ và pull model `gemma3` |

---

## 🚀 Cài đặt & Chạy hệ thống

### 1. Clone repository

```bash
git clone https://github.com/Membau/BI-t-c-m-KTX.git
cd BI-t-c-m-KTX
```

### 2. Cấu hình môi trường
Mở file `run_project.bat` bằng Notepad và sửa lại 2 đường dẫn sau cho phù hợp với máy của bạn:
- `JAVA_HOME`: Đường dẫn tới thư mục cài đặt JDK 17.
- `KAFKA_HOME`: Đường dẫn tới thư mục giải nén Apache Kafka.

### 3. Cài thư viện Python

```bash
pip install -r requirements.txt
```

### 4. Chuẩn bị AI (Ollama)
Cài đặt [Ollama](https://ollama.com/) và tải model:
```bash
ollama pull gemma3
```

### 5. Khởi động 1-Click (Dành cho Windows)
Chỉ cần nhấp đúp chuột vào file:
```
run_project.bat
```
Hệ thống sẽ tự động thực hiện 8 bước:
1. Bật Ollama ngầm.
2. Khởi động Kafka Server (KRaft mode).
3. Tạo 2 Kafka Topic (`facebook_orders_stream`, `shipped_orders_stream`).
4. Bật AI Consumer.
5. Bật Streamlit Dashboard.
6. Bật Fake Stream sinh dữ liệu đa chi nhánh.
7. Bật PySpark Analytics.

Truy cập Dashboard tại: **`http://localhost:8501`**

---

## 📊 Hướng dẫn sử dụng Dashboard

| Tab | Chức năng |
|---|---|
| 📊 Báo cáo BI | Xem doanh thu thực tế, biểu đồ PySpark Realtime theo chi nhánh KTX. |
| 🍴 Quản lý Menu | Thêm/sửa/xóa món ăn, cập nhật giá và trạng thái. AI sẽ tự động học Menu mới. |
| 🔎 Duyệt Comment Lỗi | Xử lý các lỗi NLP phức tạp, dạy lại AI thủ công (tùy chọn). |
| 🚚 Giao hàng | Nơi xác nhận đơn hàng. Bấm "Đã giao" để kích hoạt PySpark tính tiền. Bấm "Hủy đơn rác" để dạy AI tự động phớt lờ các comment nhiễu. |

---

## 🧠 Cơ chế học của AI (Few-Shot Learning)

Hệ thống sử dụng **dynamic few-shot prompting**:
1. Lần đầu tiên AI gặp một comment nhiễu (Ví dụ: "Up bài", "Có giao khu A không"), nó có thể nhận nhầm là đơn hàng.
2. Admin vào tab **Giao hàng**, bấm **🗑️ Hủy đơn rác**.
3. Hệ thống ngay lập tức lưu câu comment đó vào file `few_shot_examples.json` với nhãn là *Không phải đơn hàng*.
4. Ở các comment tiếp theo, AI sẽ đọc file này, nhận diện ra quy luật và **tự động phớt lờ** các câu tương tự mà không cần bạn phải can thiệp hay huấn luyện lại model.

---

## 📝 Giấy phép
Dự án học thuật bộ môn Big Data — tự do sử dụng và chỉnh sửa.
