import os
import requests
import json
import pandas as pd

MENU_FILE = "data/menu.xlsx"
EXAMPLES_FILE = "data/few_shot_examples.json"

def load_menu_from_excel():
    try:
        df = pd.read_excel(MENU_FILE)
        df_active = df[df["Trạng Thái"] != "Hết"]
        menu_dict = dict(zip(df_active["Tên Món"], df_active["Giá"]))
        menu_str = ", ".join(df_active["Tên Món"].tolist())
        print(f"📋 Menu hôm nay ({len(menu_dict)} món): {menu_str}")
        return menu_dict, menu_str
    except Exception as e:
        print(f"⚠️ Lỗi đọc menu Excel: {e}")
        return {}, ""

MENU_DICT, MENU_STR = load_menu_from_excel()

def load_examples():
    # Nếu chưa có file json, trả về ví dụ mặc định
    if not os.path.exists(EXAMPLES_FILE):
        default_examples = [
            {"comment": "dạ 2p Cơm chiên gà sốt me, rào A14, 0861418686", "is_order": True, "mon_an": "Cơm chiên gà sốt me", "so_luong": 2, "dia_chi": "rào A14", "sdt": "0861418686", "ghi_chu": ""},
            {"comment": "Có giao khu A không ạ", "is_order": False, "mon_an": "", "so_luong": 0, "dia_chi": "", "sdt": "", "ghi_chu": ""}
        ]
        return default_examples
    
    with open(EXAMPLES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_order_with_ollama(comment_text):
    # Lấy danh sách ví dụ từ file
    examples = load_examples()
    
    # Nối các ví dụ thành chuỗi cho Prompt
    few_shot_str = ""
    for i, ex in enumerate(examples):
        # Trích xuất phần comment ra khỏi JSON để in riêng
        comment_ex = ex.get("comment", "")
        # Tạo bản sao của dictionary và xóa key 'comment' để đưa vào kết quả JSON mẫu
        json_ex = ex.copy()
        if "comment" in json_ex:
            del json_ex["comment"]
        
        if "orders" in json_ex:
            json_str = json.dumps(json_ex, ensure_ascii=False)
        else:
            json_str = f"{{\"orders\": [{json.dumps(json_ex, ensure_ascii=False)}]}}"
            
        few_shot_str += f"Ví dụ {i+1}:\nComment: \"{comment_ex}\"\nJSON: {json_str}\n\n"

    prompt = f"""Bạn là AI trích xuất thông tin đặt hàng. CHỈ trả về một chuỗi JSON hợp lệ, bắt đầu bằng {{ và kết thúc bằng }}, tuyệt đối không giải thích.
Các món ăn phải có trong menu: [{MENU_DICT}]. Tên món ăn trích xuất BẮT BUỘC phải khớp chính xác với tên trong menu.

Cấu trúc JSON yêu cầu:
{{
    "orders": [
        {{
            "is_order": true hoặc false,
            "mon_an": "tên món ăn chuẩn",
            "so_luong": số lượng,
            "dia_chi": "địa chỉ",
            "sdt": "số điện thoại",
            "ghi_chu": "ghi chú"
        }}
    ]
}}

{few_shot_str}
Thực hiện với:
Comment: "{comment_text}"
JSON:"""

    try:
        res = requests.post(
            "http://localhost:11434/api/generate", 
            json={"model": "gemma3", "prompt": prompt, "stream": False, "format": "json"}
        )
        
        raw_response = res.json().get("response", "").strip()
        
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:-3].strip()
        elif raw_response.startswith("```"):
            raw_response = raw_response[3:-3].strip()
            
        parsed_json = json.loads(raw_response)
        orders = parsed_json.get("orders", [])
        
        if not orders:
            return [{"is_order": False}]
            
        return orders
        
    except Exception as e:
        print(f"⚠️ LỖI PARSE JSON: {e}")
        return [{"is_order": False}]