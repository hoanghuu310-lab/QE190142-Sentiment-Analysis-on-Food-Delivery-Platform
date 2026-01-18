import requests
import json
import time
import random
import os
from schema_sentiment import ReviewItem

# --- CẤU HÌNH ---
DATA_FOLDER = "data_sentiment"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'x-foody-client-type': '1',
    'x-foody-client-version': '3.0.0',
    'x-foody-api-version': '1',
}

# BẢNG TỪ ĐIỂN MAP TỪ URL -> ID THÀNH PHỐ
CITY_MAPPING = {
    "ha-noi": {"id": 218, "name": "HaNoi"},
    "ho-chi-minh": {"id": 217, "name": "HCM"},
    "da-nang": {"id": 219, "name": "DaNang"},
    "hai-phong": {"id": 220, "name": "HaiPhong"},
    # Có thể thêm các tỉnh khác nếu cần
}

def analyze_url(url):
    """
    Phân tích URL để tách Slug và Thành phố
    Input: https://shopeefood.vn/ha-noi/pho-thin-lo-duc
    Output: slug='pho-thin-lo-duc', city_info={'id': 218, 'name': 'HaNoi'}
    """
    # Xóa phần https://shopeefood.vn/
    clean_url = url.replace("https://shopeefood.vn/", "").replace("http://shopeefood.vn/", "")
    parts = clean_url.split("/")
    
    # URL chuẩn thường là: [ten-thanh-pho]/[ten-quan]
    if len(parts) >= 2:
        city_slug = parts[0]
        restaurant_slug = parts[1].split("?")[0] # Bỏ tham số ? sau slug
        
        # Tra cứu trong từ điển
        city_info = CITY_MAPPING.get(city_slug)
        if city_info:
            return restaurant_slug, city_info
            
    return None, None

def get_restaurant_id_from_slug(slug):
    """Gọi API để đổi tên quán (slug) thành ID số"""
    url = f"https://gappapi.deliverynow.vn/api/delivery/get_detail?request_id={slug}&id_type=2"
    try:
        resp = requests.get(url, headers=HEADERS)
        data = resp.json()
        delivery_detail = data.get('reply', {}).get('delivery_detail', {})
        
        return {
            "id": delivery_detail.get('delivery_id'),
            "name": delivery_detail.get('name')
        }
    except:
        return None

def crawl_reviews_by_link(url_list, limit_per_shop=100):
    print(f"🚀 Đang xử lý danh sách {len(url_list)} quán ăn...")
    
    for url in url_list:
        print(f"\n🔗 Checking: {url}")
        
        # 1. Tự động phát hiện thành phố
        slug, city_info = analyze_url(url)
        
        if not city_info:
            print("   ⚠️ Không nhận diện được thành phố từ Link này. Bỏ qua.")
            continue
            
        print(f"   -> Phát hiện: {city_info['name']} (Slug: {slug})")
        
        # 2. Lấy ID quán
        shop_info = get_restaurant_id_from_slug(slug)
        if not shop_info or not shop_info['id']:
            print("   ❌ Không lấy được ID quán. Link có thể bị lỗi.")
            continue
            
        shop_id = shop_info['id']
        shop_name = shop_info['name']
        
        # 3. Tạo tên file tự động theo thành phố (TỰ ĐỘNG PHÂN LOẠI TỆP KHÁCH HÀNG)
        output_file = os.path.join(DATA_FOLDER, f"reviews_{city_info['name']}.jsonl")
        
        # 4. Crawl Review
        print(f"   -> Đang tải review cho quán: {shop_name}...")
        api_review = f"https://gappapi.deliverynow.vn/api/delivery/get_reply?id_type=1&request_id={shop_id}&sort_type=1&limit={limit_per_shop}"
        
        try:
            res = requests.get(api_review, headers=HEADERS)
            reviews = res.json().get('reply', {}).get('reply_list', [])
            
            if not reviews:
                print("   ⚠️ Quán này chưa có review nào.")
                continue

            with open(output_file, 'a', encoding='utf-8') as f:
                for rev in reviews:
                    item = ReviewItem(
                        review_id=rev.get('id'),
                        restaurant_id=shop_id,
                        restaurant_name=shop_name,
                        city=city_info['name'], # Lưu tên thành phố vào từng dòng
                        user_name=rev.get('name', 'Anonymous'),
                        comment=rev.get('comment', ''),
                        rating=rev.get('rating', 0),
                        review_date=rev.get('created_on', '')
                    )
                    f.write(item.to_json_line() + "\n")
            
            print(f"   ✅ Đã lưu {len(reviews)} reviews vào file: reviews_{city_info['name']}.jsonl")
            
        except Exception as e:
            print(f"   ❌ Lỗi crawl review: {e}")
            
        # Nghỉ nhẹ để không bị spam
        time.sleep(random.uniform(1, 3))

# --- MAIN RUN ---
if __name__ == "__main__":
    
    # BẠN CHỈ CẦN DÁN LIST LINK VÀO ĐÂY (LỘN XỘN CŨNG ĐƯỢC)
    # Code sẽ tự tách: Link nào Hà Nội -> Vào file HaNoi, Link nào HCM -> Vào file HCM
    
    MY_LINKS = [
        # Link Hà Nội
        "https://shopeefood.vn/ha-noi/pho-thin-lo-duc", 
        "https://shopeefood.vn/ha-noi/bun-cha-dac-kim-hang-manh",
        
        # Link Sài Gòn
        "https://shopeefood.vn/ho-chi-minh/com-tam-cali-nguyen-trai-q1",
        "https://shopeefood.vn/ho-chi-minh/phuc-long-lotte-mart-le-dai-hanh",
        
        # Link Đà Nẵng
        "https://shopeefood.vn/da-nang/my-quang-ba-mua-tran-binh-trong"
    ]
    
    crawl_reviews_by_link(MY_LINKS, limit_per_shop=50)
