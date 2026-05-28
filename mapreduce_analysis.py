import pandas as pd
from collections import defaultdict

def reduce_sum(mapped_data):
    """Hàm Reduce: Gom nhóm và tính tổng các Value theo cùng một Key"""
    result = defaultdict(float)
    for key, value in mapped_data:
        result[key] += value
    return dict(result)

def map_reduce_doanh_thu_theo_mon(df):
    """
    Tính tổng doanh thu cho từng món ăn
    - Map: Xuất ra cặp (mon_an, doanh_thu)
    - Reduce: Cộng tổng doanh thu theo tên món
    """
    mapped = [(row["mon_an"], float(row["doanh_thu"])) for _, row in df.iterrows() if pd.notna(row["mon_an"])]
    reduced_dict = reduce_sum(mapped)
    
    # Chuyển đổi lại thành DataFrame để Streamlit dễ vẽ biểu đồ
    return pd.DataFrame(list(reduced_dict.items()), columns=["mon_an", "doanh_thu"])

def map_reduce_so_luong_theo_mon(df):
    """
    Tính tổng số lượng đã bán cho từng món
    - Map: Xuất ra cặp (mon_an, so_luong)
    - Reduce: Cộng tổng số lượng theo tên món
    """
    mapped = [(row["mon_an"], int(row["so_luong"])) for _, row in df.iterrows() if pd.notna(row["mon_an"])]
    reduced_dict = reduce_sum(mapped)
    
    return pd.DataFrame(list(reduced_dict.items()), columns=["mon_an", "so_luong"])