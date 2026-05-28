from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

def scrape_facebook_comments(post_url, output_file="data/real_facebook_comments.txt"):
    try:
        # Mở bài viết
        driver.get(post_url)
        print("Đang tải trang... Vui lòng đăng nhập thủ công nếu bị yêu cầu (bạn có 60 giây).")
        time.sleep(60)
        print("Đang cuộn trang để tải thêm comment...")
        for _ in range(5): 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        comment_blocks = driver.find_elements(By.XPATH, "//div[contains(@dir, 'auto') and contains(@style, 'text-align: start;')]")
        os.makedirs("data", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for idx, block in enumerate(comment_blocks):
                text = block.text.strip()
                if text:
                    mock_uid = f"UID_{1000 + idx}"
                    current_time = time.strftime("%H:%M %p")
                    formatted_line = f"{mock_uid} | {current_time} | {text}\n"
                    f.write(formatted_line)
                    print(f"Đã cào: {formatted_line.strip()}")

        print(f"\n✅ Đã lưu dữ liệu vào {output_file}")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
    finally:
        driver.quit()
if __name__ == "__main__":
    POST_URL = "https://www.facebook.com/groups/hoiktxkhua/posts/1569401934550725/"
    scrape_facebook_comments(POST_URL)