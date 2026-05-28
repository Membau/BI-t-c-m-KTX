import time
import random
from datetime import datetime
import json
from kafka import KafkaProducer

# Khởi tạo Kafka Producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Danh sách chi nhánh
STORES = ["KTX_A", "KTX_B", "KTX_C"]

# Từ điển ánh xạ món
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
PREFIX_KEM_SL = ["1p ", "2p ", "3p ", "4p "]
PREFIX_KHONG_KEM_SL = ["Cho e ", "cho mình ", "lấy ", "ê m cho tao ", ""]

def generate_phone():
    return random.choice(SDT) + "".join([str(random.randint(0, 9)) for _ in range(8)])

def generate_random_comment():
    behavior = random.choices(["day_du", "nhieu_mon", "spam"], weights=[0.6, 0.3, 0.1])[0]
    
    if behavior == "spam":
        return random.choice(["Có giao khu A không ạ", "C còn nhận đơn nhé", "Up", "Mb: 039234857 (Nguyễn Văn A)"])

    sdt = generate_phone()
    dc = random.choice(DIA_CHI)
    
    dung_prefix_kem_sl = random.choice([True, False])
    if dung_prefix_kem_sl:
        chuoi_so_luong_va_prefix = random.choice(PREFIX_KEM_SL)
    else:
        qty = random.randint(1, 3)
        chuoi_so_luong_va_prefix = f"{random.choice(PREFIX_KHONG_KEM_SL)}{qty} "
        
    if behavior == "day_du":
        mon_chuan = random.choice(list(MENU_MAPPING.keys()))
        mon_goi = random.choice(MENU_MAPPING[mon_chuan])
        return f"{chuoi_so_luong_va_prefix}{mon_goi}, {dc}, {sdt}"
        
    elif behavior == "nhieu_mon":
        mon_chinh = random.choice(list(MENU_MAPPING.keys())[:-2]) 
        mon_phu = random.choice(["Cơm thêm", "Trứng thêm"])
        ten_chinh = random.choice(MENU_MAPPING[mon_chinh])
        ten_phu = random.choice(MENU_MAPPING[mon_phu])
        prefix = random.choice(["Cho e ", "lấy "])
        return f"{prefix}{ten_chinh} với {ten_phu}, giao {dc}, sdt {sdt}"

print("🚀 Bắt đầu giả lập luồng Comment từ nhiều chi nhánh (Fake Stream)...")
print("⚠️ Lưu ý: Tốc độ sinh 3s/đơn để AI xử lý kịp, tránh treo máy.")

current_uid_counter = 5000

while True:
    store_name = random.choice(STORES)
    uid = f"UID_{current_uid_counter}"
    current_uid_counter += 1
    
    current_time = datetime.now().strftime('%H:%M %p')
    comment = generate_random_comment()
    
    # Format: KTX_A | UID_5000 | 23:30 PM | 2p cơm gà...
    raw_text = f"{store_name} | {uid} | {current_time} | {comment}"
    
    payload = {"raw_comment": raw_text}
    producer.send("facebook_orders_stream", payload)
    print(f"[{store_name}] Sent: {raw_text}")
    
    # Delay 10s để AI kịp phân tích (Consumer chạy AI rất nặng)
    time.sleep(3)