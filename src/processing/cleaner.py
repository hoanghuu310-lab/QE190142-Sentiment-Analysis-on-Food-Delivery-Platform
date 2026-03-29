import pandas as pd
import json
import os
import glob
import re
import csv

# 1. Cấu hình đường dẫn
# Dùng os.path.abspath để tự tìm đúng thư mục data dù bạn chạy code ở đâu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Tạo folder processed nếu chưa có
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

# 2. HÀM QUAN TRỌNG NHẤT: Làm sạch text (Sát thủ diệt dấu xuống dòng)
def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Chém đẹp tất cả dấu xuống dòng (\n), dấu về đầu dòng (\r), và tab (\t)
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Gom nhiều khoảng trắng liền nhau thành 1 khoảng trắng duy nhất
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# 3. Hàm gán nhãn cảm xúc
def get_sentiment(rating):
    try:
        r = float(rating)
        if r >= 8.0: return "Positive"
        elif r < 5.0: return "Negative"
        else: return "Neutral"
    except:
        return "Unknown"

def process_and_export():
    all_data = []
    
    # Quét toàn bộ file .jsonl trong folder data/raw
    file_paths = glob.glob(os.path.join(RAW_DIR, "*.jsonl"))
    
    if not file_paths:
        print(f"❌ Không tìm thấy file JSONL nào trong {RAW_DIR}")
        return

    print("🚀 BẮT ĐẦU ĐỌC VÀ GỘP 3 FILE DATA RAW...")
    
    for path in file_paths:
        # Tách lấy chữ MienBac, MienNam... từ tên file
        filename = os.path.basename(path)
        region = filename.replace("reviews_", "").replace(".jsonl", "")
        
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        row = json.loads(line)
                        row['region'] = region # Gán vùng miền làm Metadata
                        all_data.append(row)
                    except json.JSONDecodeError:
                        continue

    if not all_data:
        print("⚠️ Không đọc được dữ liệu nào.")
        return

    # Chuyển thành DataFrame Pandas
    df = pd.DataFrame(all_data)
    print(f"✅ Đã gộp thành công {len(df)} dòng dữ liệu.")

    # Xóa dòng bị trùng lặp (Dựa vào review_id)
    if 'review_id' in df.columns:
        df = df.drop_duplicates(subset=['review_id'], keep='first')
        print(f"🧹 Đã lọc trùng lặp. Còn lại: {len(df)} dòng chuẩn.")

    print("🔧 Đang dọn dẹp dấu xuống dòng và gán nhãn Sentiment...")
    
    # Áp dụng hàm dọn rác cho cả comment và tên user (nhiều user để tên có dấu cách lạ)
    df['comment_clean'] = df['comment'].apply(clean_text)
    if 'user_name' in df.columns:
        df['user_name'] = df['user_name'].apply(clean_text)
        
    df['sentiment_label'] = df['rating'].apply(get_sentiment)
    
    # Sắp xếp lại thứ tự cột cho đẹp mắt
    cols_order = ['review_id', 'restaurant_name', 'city', 'region', 'user_name', 'rating', 'sentiment_label', 'comment_clean']
    # Chỉ giữ lại các cột có tồn tại
    existing_cols = [c for c in cols_order if c in df.columns]
    df = df[existing_cols]

    # 4. XUẤT FILE CSV
    output_file = os.path.join(PROCESSED_DIR, "foody_clean_master.csv")
    
    # Giải thích tham số:
    # utf-8-sig: Giúp mở bằng Excel không bị lỗi font Tiếng Việt
    # quoting=csv.QUOTE_ALL: Bắt buộc nhốt toàn bộ text vào trong dấu ngoặc kép "..." để chống vỡ cột
    df.to_csv(output_file, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    
    print(f"\n🎉 THÀNH CÔNG RỰC RỠ! File CSV siêu sạch đã nằm tại:\n👉 {output_file}")

if __name__ == "__main__":
    process_and_export()