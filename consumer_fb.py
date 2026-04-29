import os
import json
import pandas as pd
from kafka import KafkaConsumer
from AI_consumer import parse_order_with_ollama

OUTPUT_FILE = "output/stream_orders.csv"
MENU_FILE = "data/menu.xlsx"
PENDING_FILE = "output/pending_reviews.csv"
os.makedirs("output", exist_ok=True)

# BƯỚC KHÓA CỘT: Định nghĩa danh sách các cột chuẩn xác nhất
# BƯỚC KHÓA CỘT
STANDARD_COLUMNS = ["uid", "thoi_gian", "mon_an", "so_luong", "don_gia", "doanh_thu", "dia_chi", "sdt", "ghi_chu", "raw_comment"]

# ---------------------------------------------------------
# 1. LOAD MENU TỪ EXCEL (DYNAMIC MENU)
# ---------------------------------------------------------
def load_menu_from_excel():
    try:
        df = pd.read_excel(MENU_FILE)
        # Chỉ lấy những món trạng thái "Còn"
        df_active = df[df["Trạng Thái"] != "Hết"]
        
        # Tạo Dictionary để tính tiền { "Cơm chiên gà hấp hành": 30000 }
        menu_dict = dict(zip(df_active["Tên Món"], df_active["Giá"]))
        
        # Nối tên món thành 1 chuỗi để đưa vào Prompt cho AI
        menu_str = ", ".join(df_active["Tên Món"].tolist())
        
        print(f"📋 Menu hôm nay ({len(menu_dict)} món): {menu_str}")
        return menu_dict, menu_str
    except Exception as e:
        print(f"⚠️ Lỗi đọc menu Excel: {e}")
        return {}, ""

MENU_DICT, MENU_STR = load_menu_from_excel()

# ---------------------------------------------------------
# 2. XỬ LÝ LƯU TRỮ VÀ TÍNH DOANH THU (CÓ PHỤ THU TOPPING)
# ---------------------------------------------------------
def append_to_csv(order_data):
    mon_an = order_data.get("mon_an", "").strip()
    if mon_an not in MENU_DICT:
        return False  
    don_gia_co_ban = MENU_DICT[mon_an]
    
    # Quét Ghi chú để tính thêm tiền Topping
    ghi_chu = str(order_data.get("ghi_chu", "")).lower()
    phu_thu = 0
    if "đậu hũ" in ghi_chu or "đậu" in ghi_chu: phu_thu += 5000
    if "trứng" in ghi_chu: phu_thu += 5000
    if "cơm thêm" in ghi_chu or "thêm cơm" in ghi_chu: phu_thu += 2000
    
    tong_gia_1_phan = don_gia_co_ban + phu_thu
    
    # Đảm bảo số lượng hợp lệ
    try:
        qty = int(order_data.get("so_luong", 1))
        if qty <= 0: qty = 1
    except:
        qty = 1
        
    order_data["so_luong"] = qty
    order_data["don_gia"] = tong_gia_1_phan
    order_data["doanh_thu"] = qty * tong_gia_1_phan
    
    # LỌC DỮ LIỆU: Chỉ lấy các key nằm trong STANDARD_COLUMNS, nếu AI trả thiếu key thì gán bằng rỗng ("")
    clean_data = {col: order_data.get(col, "") for col in STANDARD_COLUMNS}
    
    df = pd.DataFrame([clean_data])
    if not os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, index=False)
    else:
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
        
    return True

# ---------------------------------------------------------
# 3. LUỒNG CHẠY CHÍNH (KAFKA CONSUMER)
# ---------------------------------------------------------
def main():
    if not MENU_DICT:
        print("❌ Hệ thống dừng vì không đọc được Menu. Hãy chạy file tao_menu.py trước!")
        return

    consumer = KafkaConsumer(
        "facebook_orders_stream",
        bootstrap_servers="localhost:9092",
        auto_offset_reset="latest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    
    print("\n🎧 Consumer đang lắng nghe...")
    for message in consumer:
        raw_text = message.value.get("raw_comment", "")
        parts = raw_text.split("|", 2)
        if len(parts) < 3: continue
        
        uid, time_str, comment = parts[0].strip(), parts[1].strip(), parts[2].strip()
        
        ai_results = parse_order_with_ollama(comment) 
        
        for ai_result in ai_results:
            ai_result["uid"] = uid
            ai_result["thoi_gian"] = time_str
            ai_result["raw_comment"] = comment 
            
            # Xử lý các comment không phải đơn hàng
            if not ai_result.get("is_order"):
                df_pending = pd.DataFrame([ai_result])
                if not os.path.exists(PENDING_FILE):
                    df_pending.to_csv(PENDING_FILE, index=False)
                else:
                    df_pending.to_csv(PENDING_FILE, mode="a", header=False, index=False)
                
                print(f"🟡 CẦN DUYỆT LẠI: {comment}")
                continue # Bỏ qua bước ghi vào file chính
                
            # Xử lý đơn hàng hợp lệ
            mon_an = ai_result.get("mon_an", "")
            success = append_to_csv(ai_result)
            
            if success:
                print(f"✅ ĐÃ CHỐT: {ai_result['so_luong']}x {mon_an} (Note: {ai_result.get('ghi_chu')})")
                print(f"   => Tiền: {ai_result.get('doanh_thu', 'N/A')}đ | Giao: {ai_result.get('dia_chi', 'N/A')} | ĐT: {ai_result.get('sdt', 'N/A')}")
        
        print("-" * 60)

if __name__ == "__main__":
    main()