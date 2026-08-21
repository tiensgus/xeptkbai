import os
import json
import streamlit as st

# Định nghĩa đường dẫn tới tệp JSON trên server
JSON_FILE_PATH = "info_school.json"

# Cấu hình danh sách 10 tiết mặc định ban đầu
GIO_HOC_MAC_DINH = [
    "07:00 - 07:45", "07:50 - 08:35", "08:50 - 09:35", "09:40 - 10:25", "10:30 - 11:15",
    "13:00 - 13:45", "13:50 - 14:35", "14:50 - 15:35", "15:40 - 16:25", "16:30 - 17:15"
]

# Hàm đọc dữ liệu từ tệp JSON
def doc_du_lieu_json(file_path):
    if not os.path.exists(file_path):
        du_lieu_mac_dinh = {
            "ten_truong": "TRƯỜNG THPT NGUYEN THI XXXXXX",
            "dia_chi": "Số 123 Đường ABC, Thành phố XYZ",
            "so_dien_thoai": "024.1234.5678",
            "tong_so_lop": 50,
            "so_tiet_toi_da_mot_ngay": 5,
            "Gio_hoc": GIO_HOC_MAC_DINH  # Thêm khóa mặc định vào đây
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(du_lieu_mac_dinh, f, ensure_ascii=False, indent=4)
        return du_lieu_mac_dinh
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Nếu file đã tồn tại nhưng chưa có key Gio_hoc thì tự động bổ sung
        if "Gio_hoc" not in data:
            data["Gio_hoc"] = GIO_HOC_MAC_DINH
        return data

# Hàm lưu dữ liệu
def luu_du_lieu_json(file_path, du_lieu_moi):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(du_lieu_moi, f, ensure_ascii=False, indent=4)

# --- GIAO DIỆN STREAMLIT ---
st.title("⚙️ Cấu Hình Thông Tin & Khung Giờ Học")
st.write("Chỉnh sửa các thông số cấu hình dưới đây và nhấn 'Lưu thay đổi' để cập nhật hệ thống.")

# Tải dữ liệu từ file
current_info = doc_du_lieu_json(JSON_FILE_PATH)

# Tạo Form chỉnh sửa
with st.form("form_edit_school_info"):
    st.subheader("📝 Thông tin chung")
    ten_truong = st.text_input("Tên trường:", value=current_info.get("ten_truong", ""))
    dia_chi = st.text_input("Địa chỉ:", value=current_info.get("dia_chi", ""))
    so_dien_thoai = st.text_input("Số điện thoại:", value=current_info.get("so_dien_thoai", ""))
    
    st.subheader("🏫 Tham số cấu hình xếp thời khóa biểu")
    tong_so_lop = st.number_input("Tổng số lớp học:", value=int(current_info.get("tong_so_lop", 50)), min_value=1)
    so_tiet_toi_da = st.number_input("Số tiết dạy tối đa của GV / ngày:", value=int(current_info.get("so_tiet_toi_da_mot_ngay", 5)), min_value=1, max_value=10)
    
    # --- PHẦN CHỈNH SỬA KHUNG GIỜ HỌC CỦA 10 TIẾT ---
    st.subheader("⏰ Cấu hình giờ học (10 tiết)")
    list_gio_hoc_hien_tai = current_info.get("Gio_hoc", GIO_HOC_MAC_DINH)
    
    # Tạo giao diện chia làm 2 cột: Ca sáng (Tiết 1-5) và Ca chiều (Tiết 6-10) cho gọn gàng
    col1, col2 = st.columns(2)
    updated_gio_hoc = []
    
    with col1:
        st.markdown("**🌅 Ca Sáng**")
        for i in range(5):
            # Tạo ô nhập liệu cho từng tiết từ 1 đến 5
            gio_tiet = st.text_input(f"Tiết {i+1}: ", value=list_gio_hoc_hien_tai[i], key=f"tiet_{i+1}")
            updated_gio_hoc.append(gio_tiet)
            
    with col2:
        st.markdown("**🌇 Ca Chiều**")
        for i in range(5, 10):
            # Tạo ô nhập liệu cho từng tiết từ 6 đến 10
            gio_tiet = st.text_input(f"Tiết {i+1}: ", value=list_gio_hoc_hien_tai[i], key=f"tiet_{i+1}")
            updated_gio_hoc.append(gio_tiet)

    # Nút bấm submit form
    nut_luu = st.form_submit_button("💾 Lưu thay đổi vào Server")

# Xử lý sự kiện lưu
if nut_luu:
    updated_info = {
        "ten_truong": ten_truong,
        "dia_chi": dia_chi,
        "so_dien_thoai": so_dien_thoai,
        "tong_so_lop": tong_so_lop,
        "so_tiet_toi_da_mot_ngay": so_tiet_toi_da,
        "Gio_hoc": updated_gio_hoc  # Lưu danh sách 10 mốc giờ mới đã chỉnh sửa
    }
    
    luu_du_lieu_json(JSON_FILE_PATH, updated_info)
    st.success("🎉 Đã cập nhật tệp info_school.json bao gồm cấu hình 'Gio_hoc' thành công!")
    
    with st.expander("👀 Xem cấu trúc tệp JSON thực tế trên Server"):
        st.json(updated_info)
