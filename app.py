import os
import pandas as pd
import streamlit as st
import plotly.express as px
import json
from mapreduce_analysis import map_reduce_so_luong_theo_mon, map_reduce_doanh_thu_theo_mon

# ================= CẤU HÌNH FILE & HẰNG SỐ =================
MENU_FILE = "data/menu.xlsx"
PENDING_FILE = "output/pending_reviews.csv"
ORDER_FILE = "output/stream_orders.csv"      
SHIPPED_FILE = "output/shipped_orders.csv"  
EXAMPLES_FILE = "data/few_shot_examples.json"

# ĐÃ THÊM raw_comment VÀ THÊM store_name VÀO CHUẨN CỘT
STANDARD_COLUMNS = ["store_name", "uid", "thoi_gian", "mon_an", "so_luong", "don_gia", "doanh_thu", "dia_chi", "sdt", "ghi_chu", "raw_comment"]

from kafka import KafkaProducer
try:
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
except Exception:
    producer = None

st.set_page_config(page_title="Hệ thống BI Đặt Cơm KTX", layout="wide")
st.title("📊 BI Dashboard & Quản lý Đơn hàng KTX")

# Chia 4 Tab
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Báo cáo BI", 
    "🍴 Quản lý Menu", 
    "🔎 Duyệt Comment Lỗi", 
    "🚚 Giao hàng (Duyệt đơn)"
])

# ================= TAB 1: BÁO CÁO BI =================
with tab1:
    col_refresh, _ = st.columns([2, 8])
    if col_refresh.button("🔄 Làm mới dữ liệu"):
        st.rerun()
        
    df_pending = pd.read_csv(ORDER_FILE) if os.path.exists(ORDER_FILE) else pd.DataFrame(columns=STANDARD_COLUMNS)
    df_shipped = pd.read_csv(SHIPPED_FILE) if os.path.exists(SHIPPED_FILE) else pd.DataFrame(columns=STANDARD_COLUMNS)
    
    df_pending['Trạng thái'] = 'Chờ giao'
    df_shipped['Trạng thái'] = 'Đã ship'
    df_all = pd.concat([df_pending, df_shipped], ignore_index=True)

    if not df_all.empty:
        rev_shipped = df_shipped["doanh_thu"].sum() if not df_shipped.empty else 0
        rev_pending = df_pending["doanh_thu"].sum() if not df_pending.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Doanh thu thực tế (Đã ship)", f"{rev_shipped:,.0f} VNĐ")
        c2.metric("Doanh thu dự kiến (Chờ giao)", f"{rev_pending:,.0f} VNĐ", delta=f"{len(df_pending)} đơn")
        c3.metric("Tổng đơn hàng hệ thống", len(df_all))
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.subheader("Cơ cấu doanh thu theo trạng thái")
            fig_status = px.pie(df_all, names="Trạng thái", values="doanh_thu", hole=0.4)
            st.plotly_chart(fig_status, use_container_width=True)
            
        with col_chart2:
            st.subheader("Top món ăn đã giao (Xử lý bằng MapReduce)")
            if not df_shipped.empty:
                # Gọi hàm MapReduce thay cho groupby
                item_summary = map_reduce_so_luong_theo_mon(df_shipped)
                # Sắp xếp lại để biểu đồ đẹp hơn
                item_summary = item_summary.sort_values("so_luong", ascending=False)
                
                fig_item = px.bar(item_summary, x="mon_an", y="so_luong", color="mon_an")
                st.plotly_chart(fig_item, use_container_width=True)
            else:
                st.info("Chưa có món nào được giao thành công.")
                
        # THÊM BIỂU ĐỒ DOANH THU THEO CHI NHÁNH TỪ PYSPARK
        st.subheader("Doanh thu theo Chi nhánh (Real-time PySpark Analytics)")
        spark_summary_file = "output/spark_summary.json"
        if os.path.exists(spark_summary_file):
            try:
                with open(spark_summary_file, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
                df_spark = pd.DataFrame(summary_data)
                if not df_spark.empty:
                    fig_spark = px.bar(df_spark, x="store_name", y="total_revenue", color="store_name", title="Tổng doanh thu từng chi nhánh")
                    st.plotly_chart(fig_spark, use_container_width=True)
                else:
                    st.info("PySpark chưa tổng hợp được doanh thu chi nhánh nào.")
            except Exception as e:
                st.warning(f"Lỗi đọc kết quả PySpark: {e}")
        else:
            st.info("Đang chờ PySpark tổng hợp dữ liệu...")
    else:
        st.warning("Hệ thống chưa có dữ liệu kinh doanh.")

# ================= TAB 2: QUẢN LÝ MENU =================
with tab2:
    st.header("Thiết lập thực đơn")
    st.markdown("💡 *Nếu bạn thay đổi Menu, hãy khởi động lại `consumer_fb.py` ở terminal để hệ thống nạp lại Menu mới cho AI.*")
    
    if os.path.exists(MENU_FILE):
        df_menu = pd.read_excel(MENU_FILE)
        
        # DÙNG FORM ĐỂ NGĂN STREAMLIT F5 KHI ĐANG GÕ
        with st.form("menu_management_form"):
            edited_menu = st.data_editor(df_menu, num_rows="dynamic", use_container_width=True)
            submitted_menu = st.form_submit_button("💾 Lưu thay đổi Menu")
            
            if submitted_menu:
                edited_menu.to_excel(MENU_FILE, index=False)
                st.success("Đã cập nhật Menu thành công!")
                st.rerun()

# ================= TAB 3: DUYỆT COMMENT LỖI =================
with tab3:
    st.header("Xử lý comment AI không tự chốt được")
    if os.path.exists(PENDING_FILE):
        try:
            # Đọc file và dọn dẹp dữ liệu lỗi rỗng (NaN)
            df_rev = pd.read_csv(PENDING_FILE)
            df_rev["raw_comment"] = df_rev["raw_comment"].fillna("").astype(str)
            df_rev = df_rev[df_rev["raw_comment"].str.strip() != ""] # Bỏ các dòng trống
            
            if not df_rev.empty:
                # Lấy danh sách comment để đưa vào Selectbox
                unique_comments = df_rev["raw_comment"].unique()
                sel_comment = st.selectbox("Chọn comment:", unique_comments)
                
                # Lọc data theo comment đã chọn
                filtered_df = df_rev[df_rev["raw_comment"] == sel_comment]
                
                # KIỂM TRA AN TOÀN TRƯỚC KHI TRÍCH XUẤT (Fix lỗi iloc[0])
                if not filtered_df.empty:
                    curr_row = filtered_df.iloc[0]
                    st.info(f"Khách viết: {sel_comment}")
                    
                    with st.form("fix_ai_form"):
                        st.write("**1. Thông tin giao hàng chung:**")
                        col_info1, col_info2 = st.columns(2)
                        
                        # Dùng .get() để tránh lỗi nếu thiếu cột
                        f_addr = col_info1.text_input("Địa chỉ:", value=str(curr_row.get('dia_chi', '')))
                        f_sdt = col_info2.text_input("SĐT:", value=str(curr_row.get('sdt', '')))
                        
                        st.write("**2. Danh sách món ăn (Bấm dấu + ở dưới bảng để thêm món):**")
                        menu_list = pd.read_excel(MENU_FILE)["Tên Món"].tolist() if os.path.exists(MENU_FILE) else []
                        
                        df_items_input = pd.DataFrame([{"mon_an": "", "so_luong": 1, "ghi_chu": ""}])
                        
                        edited_items = st.data_editor(
                            df_items_input,
                            num_rows="dynamic",
                            column_config={
                                "mon_an": st.column_config.SelectboxColumn("🍲 Tên món", options=menu_list, width="medium"),
                                "so_luong": st.column_config.NumberColumn("🔢 SL", min_value=1),
                                "ghi_chu": st.column_config.TextColumn("📝 Ghi chú (Ít cay, thêm cơm...)", width="large")
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        c_btn1, c_btn2 = st.columns(2)
                        btn_chot_don = c_btn1.form_submit_button("✅ Chốt đơn & Dạy AI")
                        btn_xoa_rac = c_btn2.form_submit_button("🗑️ Xóa rác")
                        
                        # XỬ LÝ LƯU ĐƠN HÀNG
                        if btn_chot_don:
                            valid_items = edited_items[edited_items["mon_an"].str.strip() != ""]
                            
                            if valid_items.empty:
                                st.error("Vui lòng chọn ít nhất 1 món ăn!")
                            else:
                                orders_for_ai = []
                                for _, item in valid_items.iterrows():
                                    f_mon = item["mon_an"]
                                    f_qty = int(item["so_luong"])
                                    f_note = str(item.get("ghi_chu", ""))
                                    
                                    new_order = {
                                        "store_name": curr_row.get("store_name", "KTX_Chính"),
                                        "uid": curr_row.get("uid", ""), 
                                        "thoi_gian": curr_row.get("thoi_gian", ""), 
                                        "mon_an": f_mon, 
                                        "so_luong": f_qty, 
                                        "don_gia": 30000, 
                                        "doanh_thu": 30000 * f_qty, 
                                        "dia_chi": f_addr, 
                                        "sdt": f_sdt, 
                                        "ghi_chu": f_note, 
                                        "raw_comment": sel_comment
                                    } 
                                    clean_d = {col: new_order.get(col, "") for col in STANDARD_COLUMNS}
                                    pd.DataFrame([clean_d]).to_csv(ORDER_FILE, mode='a', header=not os.path.exists(ORDER_FILE), index=False)
                                    
                                    orders_for_ai.append({
                                        "is_order": True, "mon_an": f_mon, "so_luong": f_qty,
                                        "dia_chi": f_addr, "sdt": f_sdt, "ghi_chu": f_note
                                    })
                                
                                # Dạy AI
                                if os.path.exists(EXAMPLES_FILE):
                                    with open(EXAMPLES_FILE, "r", encoding="utf-8") as f:
                                        curr_examples = json.load(f)
                                else: 
                                    curr_examples = []
                                    
                                new_ex = {"comment": sel_comment, "orders": orders_for_ai}
                                curr_examples = [ex for ex in curr_examples if ex.get("comment") != sel_comment]
                                curr_examples.append(new_ex)
                                
                                with open(EXAMPLES_FILE, "w", encoding="utf-8") as f:
                                    json.dump(curr_examples, f, ensure_ascii=False, indent=4)
                                
                                # Xóa comment đã xử lý khỏi Pending file
                                df_rev = df_rev[df_rev["raw_comment"] != sel_comment]
                                df_rev.to_csv(PENDING_FILE, index=False)
                                st.success(f"Đã chốt {len(valid_items)} món!")
                                st.rerun()
                                
                        # XỬ LÝ XÓA RÁC
                        if btn_xoa_rac:
                            df_rev = df_rev[df_rev["raw_comment"] != sel_comment]
                            df_rev.to_csv(PENDING_FILE, index=False)
                            st.success("Đã dọn dẹp bình luận rác!")
                            st.rerun()
                            
                else:
                    st.warning("🔄 Giao diện đang cập nhật, vui lòng đợi 1 giây hoặc chọn comment khác.")
                    
            else:
                st.success("Tất cả comment đã được xử lý xong!")
        except pd.errors.EmptyDataError:
            st.success("File chờ duyệt trống.")
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {str(e)}")
    else:
        st.info("Không có dữ liệu chờ duyệt.")

# ================= TAB 4: GIAO HÀNG (DUYỆT ĐƠN) =================
with tab4:
    st.header("🚚 Quản lý giao hàng & Sửa lỗi AI (Real-time Sync)")
    
    # Load Menu để có danh sách món và giá
    df_menu = pd.read_excel(MENU_FILE) if os.path.exists(MENU_FILE) else pd.DataFrame()
    menu_list = df_menu["Tên Món"].tolist() if not df_menu.empty else []
    menu_dict = dict(zip(df_menu["Tên Món"], df_menu["Giá"])) if not df_menu.empty else {}

    if "df_shipping_view" not in st.session_state:
        st.session_state.df_shipping_view = pd.DataFrame(columns=STANDARD_COLUMNS)

    def refresh_shipping_data():
        if os.path.exists(ORDER_FILE):
            try:
                df = pd.read_csv(ORDER_FILE)
                # Tự động dọn rác do stream bị lặp
                df = df.drop_duplicates(subset=["uid", "sdt", "mon_an", "so_luong"], keep="last")
                df.to_csv(ORDER_FILE, index=False)
                st.session_state.df_shipping_view = df
            except Exception:
                st.session_state.df_shipping_view = pd.DataFrame(columns=STANDARD_COLUMNS)

    col_btn_1, _ = st.columns([2, 8])
    if col_btn_1.button("🔄 Đồng bộ đơn mới"):
        refresh_shipping_data()
        st.rerun()

    if st.session_state.df_shipping_view.empty:
        refresh_shipping_data()

    df_display = st.session_state.df_shipping_view.copy()
    
    if not df_display.empty:
        df_display["sdt"] = df_display["sdt"].fillna("Khách vãng lai")
        unique_sdts = df_display["sdt"].unique()
        
        st.info("💡 **Mẹo:** Bạn có thể sửa trực tiếp Món ăn, Số lượng, Ghi chú, **Địa chỉ và SĐT** ngay trong bảng. Nhớ bấm 'Lưu chỉnh sửa & Dạy AI' sau khi sửa nhé!")
        st.divider()
        
        for sdt in unique_sdts:
            df_sdt = df_display[df_display["sdt"] == sdt].copy()
            
            store_name_chung = df_sdt["store_name"].iloc[0] if "store_name" in df_sdt.columns else "KTX_Chính"
            uid_chung = df_sdt["uid"].iloc[0]
            thoi_gian_chung = df_sdt["thoi_gian"].iloc[0]
            
            comments = df_sdt["raw_comment"].dropna().unique()
            comments_str = " | ".join(comments) if len(comments) > 0 else "Không có comment"
            tong_tien = pd.to_numeric(df_sdt["doanh_thu"], errors="coerce").sum()
            
            with st.form(key=f"form_ship_{sdt}"):
                # UI Đầu mục (Chỉ hiển thị UID và Tổng tiền)
                st.markdown(f"**📞 SĐT Nhóm: {sdt}** | 💰 **{tong_tien:,.0f} VNĐ**")
                st.caption(f"💬 *{comments_str}*")
                
                # BẢNG QUẢN LÝ (Đã thêm Địa chỉ và SĐT vào đây)
                df_items = df_sdt[["mon_an", "so_luong", "ghi_chu", "dia_chi", "sdt"]].copy()
                
                # Ép kiểu để tránh lỗi Streamlit
                df_items["ghi_chu"] = df_items["ghi_chu"].fillna("").astype(str)
                df_items["mon_an"] = df_items["mon_an"].fillna("").astype(str)
                df_items["dia_chi"] = df_items["dia_chi"].fillna("").astype(str)
                df_items["sdt"] = df_items["sdt"].fillna("").astype(str)
                
                edited_items = st.data_editor(
                    df_items,
                    key=f"editor_{sdt}",
                    num_rows="dynamic",
                    column_config={
                        "mon_an": st.column_config.SelectboxColumn("🍲 Tên món", options=menu_list),
                        "so_luong": st.column_config.NumberColumn("🔢 SL", min_value=1),
                        "dia_chi": st.column_config.TextColumn("📍 Địa chỉ (Sửa nếu AI sai)"),
                        "sdt": st.column_config.TextColumn("📞 SĐT (Sửa nếu AI sai)"),
                        "ghi_chu": st.column_config.TextColumn("📝 Ghi chú")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                c1, c2, c3 = st.columns(3)
                btn_ship = c1.form_submit_button("🚚 Đã giao đơn này")
                btn_save_ai = c2.form_submit_button("💾 Lưu chỉnh sửa & Dạy AI")
                btn_delete = c3.form_submit_button("🗑️ Hủy đơn rác")
                
                if btn_delete:
                    # Dạy AI đây là đơn rác
                    if len(comments) > 0:
                        new_ex = {"comment": comments[0], "orders": [{"is_order": False}]}
                        curr_examples = json.load(open(EXAMPLES_FILE, "r", encoding="utf-8")) if os.path.exists(EXAMPLES_FILE) else []
                        curr_examples = [ex for ex in curr_examples if ex.get("comment") != new_ex["comment"]]
                        curr_examples.append(new_ex)
                        with open(EXAMPLES_FILE, "w", encoding="utf-8") as f:
                            json.dump(curr_examples, f, ensure_ascii=False, indent=4)
                    
                    df_display = df_display[df_display["sdt"] != sdt]
                    df_display.to_csv(ORDER_FILE, index=False)
                    if "df_shipping_view" in st.session_state:
                        del st.session_state.df_shipping_view
                    st.success("🗑️ Đã xóa đơn rác và nạp dữ liệu cho AI!")
                    st.rerun()
                    
                elif btn_ship or btn_save_ai:
                    valid_items = edited_items[edited_items["mon_an"].astype(str).str.strip() != ""]
                    
                    if valid_items.empty:
                        st.warning("Đơn hàng không có món nào hợp lệ!")
                        continue
                        
                    processed_orders = []
                    orders_for_ai = []
                    
                    for _, row in valid_items.iterrows():
                        mon = row["mon_an"]
                        qty = int(pd.to_numeric(row["so_luong"], errors="coerce")) if pd.notna(row["so_luong"]) else 1
                        don_gia = menu_dict.get(mon, 30000) 
                        doanh_thu = qty * don_gia
                        ghi_chu_val = str(row.get("ghi_chu", ""))
                        
                        # Lấy Địa chỉ và SĐT TỪ BẢNG (có thể đã bị sửa)
                        dia_chi_val = str(row.get("dia_chi", ""))
                        sdt_val = str(row.get("sdt", ""))
                        
                        processed_orders.append({
                            "store_name": store_name_chung,
                            "uid": uid_chung, "thoi_gian": thoi_gian_chung,
                            "mon_an": mon, "so_luong": qty, "don_gia": don_gia, "doanh_thu": doanh_thu,
                            "dia_chi": dia_chi_val, "sdt": sdt_val, "ghi_chu": ghi_chu_val,
                            "raw_comment": comments[0] if len(comments)>0 else ""
                        })
                        
                        orders_for_ai.append({
                            "is_order": True, "mon_an": mon, "so_luong": qty,
                            "dia_chi": dia_chi_val, "sdt": sdt_val, "ghi_chu": ghi_chu_val
                        })
                        
                    editor_state = st.session_state.get(f"editor_{sdt}", {})
                    is_changed = bool(editor_state.get("edited_rows") or editor_state.get("added_rows") or editor_state.get("deleted_rows"))
                    
                    if (btn_save_ai or (btn_ship and is_changed)) and len(comments) > 0:
                        new_ex = {"comment": comments[0], "orders": orders_for_ai}
                        curr_examples = json.load(open(EXAMPLES_FILE, "r", encoding="utf-8")) if os.path.exists(EXAMPLES_FILE) else []
                        curr_examples = [ex for ex in curr_examples if ex.get("comment") != new_ex["comment"]]
                        curr_examples.append(new_ex)
                        with open(EXAMPLES_FILE, "w", encoding="utf-8") as f:
                            json.dump(curr_examples, f, ensure_ascii=False, indent=4)
                        if btn_save_ai:
                            st.toast("🧠 Đã nạp dữ liệu gom đơn mới cho AI!")
                            if "df_shipping_view" in st.session_state:
                                del st.session_state.df_shipping_view
                            st.rerun()
                    
                    if btn_ship:
                        df_ship = pd.DataFrame(processed_orders).reindex(columns=STANDARD_COLUMNS)
                        df_ship.to_csv(SHIPPED_FILE, mode='a', header=not os.path.exists(SHIPPED_FILE), index=False)
                        
                        # Bắn lên Kafka cho PySpark đọc
                        if producer:
                            for order in processed_orders:
                                producer.send("shipped_orders_stream", value=order)
                            producer.flush()
                        
                        df_display = df_display[df_display["sdt"] != sdt]
                        df_display.to_csv(ORDER_FILE, index=False)
                        
                        del st.session_state.df_shipping_view
                        st.success(f"🚚 Đã chuyển đơn sang danh sách Đã giao!")
                        st.rerun()
                        
                    if btn_save_ai:
                        df_display = df_display[df_display["sdt"] != sdt] 
                        df_updated_sdt = pd.DataFrame(processed_orders).reindex(columns=STANDARD_COLUMNS)
                        df_display = pd.concat([df_display, df_updated_sdt], ignore_index=True)
                        
                        df_display.to_csv(ORDER_FILE, index=False)
                        del st.session_state.df_shipping_view
                        st.success("💾 Đã lưu chỉnh sửa và cập nhật lại thông tin!")
                        st.rerun()
                        
    else:
        st.info("Hiện không có đơn hàng nào cần giao. Hãy bấm 'Đồng bộ đơn mới' để kiểm tra.")