# 🍜 Foody Sentiment Analysis & Data Pipeline

**Đề tài:** Xây dựng hệ thống thu thập, lưu trữ và phân tích cảm xúc khách hàng F&B trên Foody.vn  
**Sinh viên:** Lê Hoàng Hữu 
**MSSV:** QE190142 
**Lớp/Môn học:** ADY201m


Dự án phân tích cảm xúc (Sentiment Analysis) từ các đánh giá trên nền tảng **Foody.vn**. Đây là đồ án môn học **ADY202 (AI, Data Science with Python & SQL)** được thiết kế mô phỏng mô hình doanh nghiệp với kiến trúc lưu trữ Data Lake, Database và Machine Learning.

---

## 🏗️ 1. TECH STACK VÀ KIẾN TRÚC HỆ THỐNG
Dự án được triển khai trên kiến trúc **Micro-architecture** thông qua **Docker Compose**, bao gồm:
1. **Data Lake (MinIO):** Lưu trữ dữ liệu thô (.txt, .jsonl, .csv) crawl từ website.
2. **Database (PostgreSQL 14):** Cấu trúc chuẩn hóa dữ liệu tinh (`fact_reviews`) dùng cho ML.
3. **App Workstation (Python 3.9):** Môi trường để chạy quy trình Crawl -> ETL -> ML.
4. **Machine Learning & Demo:** Mô hình học máy dựa trên **Logistic Regression & Random Forest**, được đưa lên giao diện tương tác thông qua **Streamlit**.

---

## 📂 2. CẤU TRÚC REPOSITORY (Theo chuẩn Syllabus)

```text
├── .gitignore               # Lọc file rác
├── README.md                # Hướng dẫn setup (Bạn đang đọc)
├── AI_Log.md                # Nhật ký quá trình sử dụng AI 
├── docker-compose.yml       # Cấu hình container toàn bộ hệ thống
├── requirements.txt         # File thư viện Python
│
├── data/                    
│   ├── raw/                 # Dữ liệu Data Lake ban đầu chứa logs và links
│   └── processed/           # Dữ liệu `foody_clean_master.csv` đã ETL (mẫu)
│
├── src/                     # Source Code toàn bộ quy trình
│   ├── ingestion/           # Python Scripts để Crawl dữ liệu Foody
│   ├── processing/          # Python Scripts thực hiện quá trình ETL
│   ├── modeling/            # Python Scripts để Train 2 Model ML
│   └── utils/               # Tiện ích chung
│
├── notebooks/               # Các Scripts R/Jupyter dùng để EDA và vẽ biểu đồ
├── models/                  # Nơi lưu 3 object (.pkl) sau khi Train xong
├── results/                 # Các kết quả đánh giá Model (.png, .json)
├── reports/                 # Các báo cáo tiến độ R2, R3, Final_Report
└── streamlit_app/           # Source code của ứng dụng Demo Streamlit
```

---

## 🚀 3. HƯỚNG DẪN TRIỂN KHAI VÀ SỬ DỤNG DỰ ÁN

Dưới đây là các bước để hệ thống (Pipeline) tự động chạy từ đầu đến cuối một cách dễ dàng.

### BƯỚC 1: KHỞI ĐỘNG HỆ THỐNG SERVICES (Docker)
Bạn cần cài đặt sẵn **Docker Desktop** (hoặc Docker Engine).
1. Mở Terminal (PowerShell/CMD) trỏ vào thư mục thư mục gốc của dự án.
2. Chạy lệnh:
   ```bash
   docker-compose up -d --build
   ```
3. Sau khi chạy thành công, bạn có thể kiểm tra các dịch vụ đang live:
   - **Streamlit Demo App:** `http://localhost:8501`
   - **MinIO Data Lake:** `http://localhost:9001` (User: `minioadmin` / Pass: `minioadmin`)
   - **PostgreSQL Database:** Database kết nối tại cổng `5432` dùng DBeaver hoặc pgAdmin.

---

### BƯỚC 2: QUY TRÌNH DATA ENGINEERING (R2)
Quy trình từ Crawl dữ liệu -> Lưu Data Lake -> ETL -> Đẩy vào Database. Bạn mở Terminal tại máy bạn (hoặc bên trong container `foody_app`):

1. **Chạy luồng Thu thập dữ liệu thô (Data Ingestion):**
   ```bash
   # Bước 2.1: Quét và lấy danh sách các đường link quán ăn trên Foody
   python src/ingestion/getlink.py
   
   # Bước 2.2: Từ danh sách link, tiến hành crawl nội dung Review
   python src/ingestion/crawler.py
   ```
   *(Dữ liệu thô thu thập được sẽ tự động lưu vào S3 bucket tên `foody-raw-data` trên Data Lake MinIO)*

2. **Chạy luồng Làm sạch & Biến đổi dữ liệu (Processing/ETL):**
   ```bash
   python src/processing/cleaner.py
   ```
   *(Kết quả sẽ tạo ra file `data/processed/foody_clean_master.csv` sẵn sàng huấn luyện mô hình)*

---

### BƯỚC 3: QUY TRÌNH PHÂN TÍCH KHÁM PHÁ EDA (R3)
Dự án cung cấp mã nguồn RStudio trong thư mục `notebooks/generate_charts.R`.  
Bạn có thể mở tệp này bằng RStudio và chạy lệnh để **trực quan hóa dữ liệu**, tạo các biểu đồ kết xuất ra thục mục `results/` bao gồm (Biểu đồ tròn theo tỉ lệ nhãn tích cực/tiêu cực).

---

### BƯỚC 4: QUY TRÌNH MACHINE LEARNING & EVALUATION (R4)
Xây dựng 2 mô hình Học Máy (Logistic Regression và Random Forest) để tiên đoán cảm xúc của các comments.

Chạy lệnh:
```bash
python src/modeling/model.py
```
**Luồng hoạt động:**
1. Text từ Clean Dataset sẽ chạy qua bộ mã hóa **TF-IDF**.
2. Mô hình tiến hành học tập và validation chéo để chọn mô hình tối ưu nhất.
3. Sau khi chạy, file **models `.pkl`** sẽ được thiết lập vào thư mục `models/` và file kết quả json sẽ bay vào `results/model_comparison.json`.

---

### BƯỚC 5: TƯƠNG TÁC GIAO DIỆN DEMO (R5)
Khi Docker Compose trên **BƯỚC 1** đã chạy xanh, một web app viết bằng Streamlit đã tự động được dựng qua port 8501. Web interface này sẽ sử dụng file `Logistic Regression.pkl` lúc nãy vừa train để phân tích real-time:

👉 Truy cập URL trên trình duyệt:  
`http://localhost:8501`

- Viết review bất kỳ và nhấn chạy.
- Giao diện có chức năng so sánh trực tiếp kết quả xử lý ngôn ngữ tự nhiên (NLP) giữa 2 mô hình Machine Learning.
