import json
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- PHẦN 1: ĐỊNH NGHĨA CLASS REVIEW (Gộp vào đây để xóa bỏ lỗi Import) ---
class ReviewItem:
    def __init__(self, review_id, restaurant_id, restaurant_name, city, user_name, comment, rating, review_date):
        self.review_id = review_id
        self.restaurant_id = restaurant_id
        self.restaurant_name = restaurant_name
        self.city = city
        self.user_name = user_name
        self.comment = comment
        self.rating = rating
        self.review_date = review_date

    def to_json_line(self):
        # Chuyển đối tượng thành chuỗi JSON để lưu file
        return json.dumps(self.__dict__, ensure_ascii=False)

# --- PHẦN 2: CẤU HÌNH ---
DATA_FOLDER = "data_foody_ok"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Bản đồ vùng miền (Dùng để đặt tên file kết quả)
REGION_MAPPING = {
    "MienBac": ["ha-noi", "hai-phong", "quang-ninh", "bac-ninh"],
    "MienTrung": ["da-nang", "hue", "khanh-hoa", "nha-trang", "quy-nhon", "vinh", "binh-dinh"],
    "MienNam": ["ho-chi-minh", "can-tho", "dong-nai", "binh-duong", "vung-tau"]
}

def setup_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Bỏ comment nếu muốn chạy ẩn
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    # Tắt dòng chữ "Chrome đang bị điều khiển bởi phần mềm tự động"
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def detect_region_from_url(url):
    # Xử lý link để tìm vùng miền
    clean_url = url.replace("https://www.foody.vn/", "").replace("http://www.foody.vn/", "")
    parts = clean_url.split("/")
    if len(parts) < 1: return "Khac", "unknown"
    
    city_slug = parts[0]
    found_region = "Khac"
    
    for region, cities in REGION_MAPPING.items():
        if city_slug in cities:
            found_region = region
            break
            
    return found_region, city_slug

def scroll_to_load_reviews(driver):
    """Hàm cuộn trang để Foody tải thêm bình luận"""
    print("   ⬇️ Đang cuộn trang...")
    for _ in range(3): # Cuộn 3 lần
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

def crawl_foody_ok(url_list):
    print("🚀 Đang khởi động Chrome...")
    driver = setup_driver()
    
    for url in url_list:
        region, city = detect_region_from_url(url)
        print(f"\n🌍 Đang truy cập: {url}")
        
        output_file = os.path.join(DATA_FOLDER, f"reviews_{region}.jsonl")
        
        try:
            driver.get(url)
            time.sleep(5) # Đợi web load
            
            # 1. Cuộn trang để hiện bình luận
            scroll_to_load_reviews(driver)
            
            # 2. Tìm các thẻ chứa review (Cập nhật Selector mới nhất)
            review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'review-item')] | //li[contains(@class, 'review-item')]")
            
            print(f"   👀 Tìm thấy {len(review_elements)} review trên màn hình.")
            
            count = 0
            with open(output_file, 'a', encoding='utf-8') as f:
                for idx, element in enumerate(review_elements):
                    try:
                        # Lấy Tên User
                        try: user = element.find_element(By.CSS_SELECTOR, ".ru-username").text.strip()
                        except: user = "Anonymous"
                        
                        # Lấy Nội dung
                        try: comment = element.find_element(By.CSS_SELECTOR, ".rd-des").text.strip()
                        except: comment = ""
                        
                        # Lấy Điểm số
                        try: 
                            rating_text = element.find_element(By.CSS_SELECTOR, ".review-points span").text
                            rating = float(rating_text)
                        except: rating = 0.0
                        
                        # Chỉ lưu nếu có nội dung bình luận
                        if comment:
                            item = ReviewItem(
                                review_id=f"foody_{idx}_{random.randint(100,999)}",
                                restaurant_id=0,
                                restaurant_name=url.split("/")[-1],
                                city=city,
                                user_name=user,
                                comment=comment,
                                rating=rating,
                                review_date=""
                            )
                            f.write(item.to_json_line() + "\n")
                            count += 1
                            
                    except Exception:
                        continue 
            
            print(f"   🎉 Đã lưu {count} reviews vào file: {output_file}")

        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            
        time.sleep(3) # Nghỉ giữa các quán

    print(f"\n🏁 Xong! Kiểm tra folder '{DATA_FOLDER}' nhé.")
    driver.quit()

if __name__ == "__main__":
    # --- DANH SÁCH LINK FOODY CHUẨN (Đã kiểm tra hoạt động tốt) ---
    MY_LINKS = [
        "https://www.foody.vn/ho-chi-minh/ech-xanh",
        "https://www.foody.vn/ho-chi-minh/boom-ca-phe-tra-sua-sua-tuoi-tran-chau-duong-den-duong-so-1",
        "https://www.foody.vn/ho-chi-minh/banh-xep-789-go-dau"
    ]
    
    crawl_foody_ok(MY_LINKS)
