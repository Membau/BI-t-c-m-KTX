import random
from datetime import datetime, timedelta
import os

# Từ điển ánh xạ món chuẩn và các cách gọi tên của khách
MENU_MAPPING = {
    "Cơm chiên gà hấp hành": ["gà hấp hành", "gà hấp", "cơm gà hấp hành"],
    "Cơm chiên gà chiên xả ớt": ["gà chiên xả ớt", "gà xả ớt", "cơm xả ớt"],
    "Cơm chiên gà sốt me": ["gà sốt me", "gà me", "cơm gà me", "gà viên sốt me"],
    "Cơm gà viên chiên giòn": ["gà viên dòn", "gà viên", "gà chiên dòn"],
    "Cơm heo chiên xù": ["heo xù", "cơm heo", "kơm heo xù"],
    "Cơm heo xù sốt me": ["heo xù sốt me", "heo me", "heo xù me"],
    "Cơm thêm": ["cơm thêm", "thêm cơm", "cơm trắng thêm"],
    "Trứng thêm": ["trứng thêm", "thêm trứng", "+ trứng"]
}

DIA_CHI = ["rào A9", "rào AH", "rào A14", "AG3", "toà BA4", "rào A17", "AH1", "H1 bk", "cổng BK"]
SDT = ["03", "05", "07", "08", "09"]

# TÁCH LÀM 2 LOẠI PREFIX ĐỂ KHÔNG BỊ TRÙNG SỐ LƯỢNG
PREFIX_KEM_SL = ["1p ", "2p ", "3p ", "4p "]
PREFIX_KHONG_KEM_SL = ["Cho e ", "cho mình ", "lấy ", "ê m cho tao ", ""]

def generate_phone():
    return random.choice(SDT) + "".join([str(random.randint(0, 9)) for _ in range(8)])

def generate_facebook_orders_v3(num_customers=30, output_file="data/facebook_comments.txt"):
    orders = []
    current_time = datetime.now().replace(hour=23, minute=30, second=0)
    current_uid_counter = 1000

    print("🚀 Đang tạo dữ liệu giả lập (Đã fix lỗi lặp số lượng)...")

    for _ in range(num_customers):
        uid = f"UID_{current_uid_counter}"
        current_uid_counter += 1
        
        current_time += timedelta(minutes=random.randint(0, 2))
        
        behavior = random.choices(
            ["day_du", "nhieu_mon", "spam"], 
            weights=[0.6, 0.3, 0.1]
        )[0]

        if behavior == "spam":
            noise = random.choice(["Có giao khu A không ạ", "C còn nhận đơn nhé", "Up", "Mb: 039234857 (Nguyễn Văn A)"])
            orders.append(f"{uid} | {current_time.strftime('%H:%M %p')} | {noise}")
            continue

        sdt = generate_phone()
        dc = random.choice(DIA_CHI)
        
        # --- LOGIC GỌI MỚI (CHỐNG LẶP SỐ LƯỢNG) ---
        # Random xem có dùng Prefix kèm số lượng sẵn hay không
        dung_prefix_kem_sl = random.choice([True, False])
        
        if dung_prefix_kem_sl:
            chuoi_so_luong_va_prefix = random.choice(PREFIX_KEM_SL)
        else:
            qty = random.randint(1, 3)
            chuoi_so_luong_va_prefix = f"{random.choice(PREFIX_KHONG_KEM_SL)}{qty} "
        # ----------------------------------------
            
        if behavior == "day_du":
            mon_chuan = random.choice(list(MENU_MAPPING.keys()))
            mon_goi = random.choice(MENU_MAPPING[mon_chuan])
            
            comment = f"{chuoi_so_luong_va_prefix}{mon_goi}, {dc}, {sdt}"
            orders.append(f"{uid} | {current_time.strftime('%H:%M %p')} | {comment}")
            
        elif behavior == "nhieu_mon":
            mon_chinh = random.choice(list(MENU_MAPPING.keys())[:-2]) 
            mon_phu = random.choice(["Cơm thêm", "Trứng thêm"])
            
            ten_chinh = random.choice(MENU_MAPPING[mon_chinh])
            ten_phu = random.choice(MENU_MAPPING[mon_phu])
            
            # Đối với đơn nhiều món, để dễ đọc mình sẽ fix cứng luôn cách gọi
            prefix = random.choice(["Cho e ", "lấy "])
            comment = f"{prefix}{ten_chinh} với {ten_phu}, giao {dc}, sdt {sdt}"
            orders.append(f"{uid} | {current_time.strftime('%H:%M %p')} | {comment}")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for order in orders:
            f.write(order + "\n")
            print(order)
            
    print(f"\n✅ Đã tạo thành công {len(orders)} dòng dữ liệu comment tại {output_file}")

if __name__ == "__main__":
    generate_facebook_orders_v3(30)