import streamlit as st
import json, os
import pandas as pd
from xhtml2pdf import pisa


# --------------------------------------------------
@st.dialog("Định lại ràng buộc xếp", width="medium")
def resetrangbuoc():
    with st.form(key='scheduling_form'):
        quy_dinh_bat_buoc =[
            "✅ 1- Cấm xếp vào các vị trí tương ứng các ô trống trong bảng Excel ",
            "✅ 2- Buộc xếp vào vị trí đã định cho các ô có đánh dấu x",
            "✅ 3- Xếp không trùng tiết cho các ô không đánh dấu x"
        ]
        ophide = st.selectbox(":red[Quy định bắt buộc:]", index=None, placeholder="Nhấp vào nếu muốn xem", options=quy_dinh_bat_buoc,key="QDBB")

        #st.write(":red[**QUY ĐỊNH BẮT BUỘC:**]")
        #st.write("✅ 1- Cấm xếp vào các vị trí tương ứng các ô trống trong bảng Excel ")
        #st.write("✅ 2- Buộc xếp vào vị trí đã định cho các ô có đánh dấu x")
        #st.write("✅ 3- Xếp không trùng tiết cho các ô không đánh dấu x")
        st.write(":red[**CÁC RÀNG BUỘC TÙY CHỌN :**]")
        # 6 tùy chọn

        JSON_FILE_PATH = "info_school/rang_buoc_xep.json"
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        options = list(data[0].keys()) # la list trong json
        listV = [st.checkbox(opt,value=data[0][opt]) for opt in options]

        submit_button = st.form_submit_button(label='💾 **Cập nhât lại**')

    if submit_button:
        # Luu cac chon , Gom dữ liệu thành dict với tên checkbox và giá trị
        data[0] = {opt: val for opt, val in zip(options, listV)}
        # Lưu vào file JSON
        with open("info_school/rang_buoc_xep.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.success('Đã cập nhật thành công!')
        

    if st.button("Close"):
        # Reset active_dialog và đưa selectbox về trạng thái chưa chọn (None)
        #st.session_state.active_dialog = None
        #st.session_state.select_lop_tkb = None
        st.rerun()

#---------------------------------------------------
@st.dialog("✏️ Chỉnh thông tin TKB", width="medium")
def chinhinfo():
    # Định nghĩa đường dẫn tới tệp JSON trên server
    JSON_FILE_PATH = "info_school/info_school.json"

    # Cấu hình danh sách 10 tiết mặc định ban đầu
    GIO_HOC_MAC_DINH = [
        "07:00 - 07:45", "07:50 - 08:35", "08:50 - 09:35", "09:40 - 10:25", "10:30 - 11:15",
        "13:00 - 13:45", "13:50 - 14:35", "14:50 - 15:35", "15:40 - 16:25", "16:30 - 17:15"
    ]
    cac_mon =  {
        "NV":   "Ngữ văn",
        "TT":   "Toán",
        "NN":   "Ngoại ngữ",
        "EN":   "Tiếng Anh",
        "TC":   "Giáo dục thể chất",
        "QP":   "Giáo dục quốc phòng và an ninh",
        "LS":   "Lịch sử",
        "ĐL":   "Địa lí",
        "KP":   "Giáo dục kinh tế và pháp luật",
        "VL":   "Vật lí",
        "HH":   "Hoá học",
        "SH":   "Sinh học",
        "CN":   "Công nghệ",
        "TH":   "Tin học",
        "AN":   "Âm nhạc",
        "MT":   "Mĩ thuật",
        "CD":   "Giáo dục công dân",
        "LĐ":   "Lịch sử và Địa lí",
        "TN":   "Khoa học tự nhiên",
        "NT":   "Nghệ thuật",
        "HN":   "Hoạt động trải nghiệm, hướng nghiệp",
        "ĐĐ":   "Đạo đức",
        "TX":   "Tự nhiên và Xã hội ",
        "KH":   "Khoa học",
        "TI":   "Tin học và Công nghệ",
        "HĐ":   "Hoạt động trải nghiệm"
    }
    so_tiet_moi_tuan = {
        "cap_tieuhoc_35p1t":   [25, 25, 28, 30, 30],
        "cap_thcs_45p1t":   29,
        "cap_thpt_45p1t":   29
    }        


    # Hàm đọc dữ liệu từ tệp JSON
    def doc_du_lieu_json(file_path):
        if not os.path.exists(file_path): # neu khong co file info_school.json thi dl mac dinh la
            du_lieu_mac_dinh = {
                "ten_truong": "Trường THPT Châu Á Thái Bình Dương",
                "dia_chi": "33 Nguyen Binh Khiem",
                "so_tiet_max_cuagv_1ngay": 8,
                "ngay_apdung_tkb": "05/09/2026",
                "gio_hoc": GIO_HOC_MAC_DINH  # Thêm khóa mặc định vào đây
            }
            # roi tao ra file_path va ghi dl mac dinh vao file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(du_lieu_mac_dinh, f, ensure_ascii=False, indent=4)
            return du_lieu_mac_dinh

        # neu co file_path thi mo va doc
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Nếu file đã tồn tại nhưng chưa có key gio_hoc thì tự động bổ sung
            if "gio_hoc" not in data:
                data["gio_hoc"] = GIO_HOC_MAC_DINH
            return data

    # Hàm lưu dữ liệu
    def luu_du_lieu_json(file_path, du_lieu_moi):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(du_lieu_moi, f, ensure_ascii=False, indent=4)

    # --- GIAO DIỆN STREAMLIT ---
    #st.title("⚙️ Cấu Hình Thông Tin & Khung Giờ Học")
    #st.write("Chỉnh sửa các thông số cấu hình dưới đây và nhấn 'Lưu thay đổi' để cập nhật hệ thống.")

    # Tải dữ liệu từ file
    current_info = doc_du_lieu_json(JSON_FILE_PATH)

    # Tạo Form chỉnh sửa
    with st.form("form_edit_school_info"):
        st.subheader("📝 Thông tin chung")
        ten_truong = st.text_input(":blue[Tên trường:]", value=current_info.get("ten_truong", ""))
        dia_chi = st.text_input(":blue[Địa chỉ:]", value=current_info.get("dia_chi", ""))
        so_tiet_max_cuagv_1ngay = st.text_input(":red[Số tiết max của gv/ngày :]", value=current_info.get("so_tiet_max_cuagv_1ngay", 7))
        ngay_apdung_tkb = st.text_input(":red[Ngày áp dụng TKB :]", value=current_info.get("ngay_apdung_tkb", "05/09/2026"))


        
        # --- PHẦN CHỈNH SỬA KHUNG GIỜ HỌC CỦA 10 TIẾT ---
        st.subheader("⏰ Cấu hình giờ học (10 tiết)")
        list_gio_hoc_hien_tai = current_info.get("gio_hoc", GIO_HOC_MAC_DINH)
        
        # Tạo giao diện chia làm 2 cột: Ca sáng (Tiết 1-5) và Ca chiều (Tiết 6-10) cho gọn gàng
        col1, col2 = st.columns(2)
        updated_gio_hoc = []
        
        with col1:
            st.markdown("**🌅 Ca Sáng**")
            for i in range(5):
                # Tạo ô nhập liệu cho từng tiết từ 1 đến 5
                gio_tiet = st.text_input(f":blue[Tiết {i+1}:] ", value=list_gio_hoc_hien_tai[i], key=f"tiet_{i+1}")
                updated_gio_hoc.append(gio_tiet)
                
        with col2:
            st.markdown("**🌇 Ca Chiều**")
            for i in range(5, 10):
                # Tạo ô nhập liệu cho từng tiết từ 6 đến 10
                gio_tiet = st.text_input(f":blue[Tiết {i+1}:] ", value=list_gio_hoc_hien_tai[i], key=f"tiet_{i+1}")
                updated_gio_hoc.append(gio_tiet)

        st.subheader("🔎 Tra cứu các môn")
        st.write(current_info["cac_mon"])


        # Nút bấm submit form
        nut_luu = st.form_submit_button("💾 :red[Lưu thay đổi vào Server]")

    # Xử lý sự kiện lưu
    if nut_luu:
        updated_info = {
            "ten_truong": ten_truong,
            "dia_chi": dia_chi,
            "so_tiet_max_cuagv_1ngay": so_tiet_max_cuagv_1ngay,
            "ngay_apdung_tkb": ngay_apdung_tkb,
            "gio_hoc": updated_gio_hoc,
            "cac_mon": cac_mon,
            "so_tiet_moi_tuan" : so_tiet_moi_tuan
        }
        
        luu_du_lieu_json(JSON_FILE_PATH, updated_info)
        st.success("🎉 Đã cập nhật tệp info_school.json bao gồm cấu hình 'Gio_hoc' thành công!")
        
        with st.expander("👀 :red[Xem cấu trúc tệp JSON thực tế trên Server]"):
            st.json(updated_info)

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()


def rut_list_gv(df):
    set_giao_vien = set()
    cot_cac_lop = df.columns[2:].tolist()   # Danh sách cac lop (tieu de cua cac cot trong bang tu cot 2)

    # Duyệt qua từng dòng dữ liệu (bỏ qua hàng tiêu đề vì Pandas đã tự lấy làm df.columns)
    for index, row in df.iterrows():
        thu = row.iloc[0]   # goi thu la cot dau tien (cs 0) trong bang (khong phai la ten tieu de cot- Thứ)
        tiet = row.iloc[1]  # goi tiet la cot ke (cs ) trong bang, (khong phai la ten tieu de cot- Tiết)
        # Duyệt qua từng cột lớp trong dòng đó
        for lop in cot_cac_lop:
            gia_tri_o = row[lop]
            # Kiểm tra ô trống (NaN hoặc chuỗi trống)
            if not (pd.isna(gia_tri_o) or str(gia_tri_o).strip() == "" or str(gia_tri_o).lower() == "nan"):
                if "_" in gia_tri_o:
                    chuoi_o = str(gia_tri_o).strip()    #cat cac khoang trang 2 ben
                    gv = chuoi_o.split('_')[0].strip()
                    if gv != "":
                        set_giao_vien.add(gv)
    list_giao_vien = sorted(list(set_giao_vien))
    return list_giao_vien


def lay_tt_tu_info_school():
    # Đường dẫn tới tệp cấu hình JSON trên server
    JSON_FILE_PATH = "info_school/info_school.json"
    if os.path.exists(JSON_FILE_PATH):
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                school_info = json.load(f)
            return school_info
        except Exception as e:
            # Nếu tệp JSON bị lỗi cú pháp khi người dùng sửa, in ra cảnh báo và dùng giờ mặc định
            print(f"Cảnh báo: Không thể đọc tệp JSON do lỗi: {e}")


def rut_df_tkb_gv(df_tkbc, gvunique):
    vals = df_tkbc.iloc[:, 2:].values
    thutietij_dic = {}
    thutietij_set = set()
    for i, hang in enumerate(vals):
        for j, ocell in enumerate(hang):
            if isinstance(ocell, str) and '_' in ocell:
                tengv,mon = ocell.strip().split("_")
                if gvunique == tengv:
                    # gia tri cua cot ten "Thu" ở hàng index i
                    thu = df_tkbc.at[i, "Thứ"]
                    # gia tri cua cot ten "Tiet" ở hàng index i
                    tiet = df_tkbc.at[i, "Tiết"]
                    # ten lop tuong ung:
                    lop = df_tkbc.columns[j+2] # vì đã bỏ ra 2 cột 
                    #st.write('Thứ '+thu , "Tiết "+tiet, lop + "-" + mon)

                    valofij = lop + "-" + mon
                    x, y = thu, tiet
                    string_key = f"{x},{y}"

                    if string_key not in thutietij_dic :
                        thutietij_dic[string_key] = valofij 
                    else:
                        thutietij_dic[string_key] = thutietij_dic[string_key] + ", " + valofij

    #data = thutietij_dic
    # Các cột đại diện cho Thứ
    columns = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
    # Tạo DataFrame rỗng với 10 tiết
    df = pd.DataFrame('', index=range(1, 11), columns=columns)
    df.index.name = 'Tiết'
    # Điền dữ liệu từ dict vào bảng
    for key, value in thutietij_dic.items():
        thu, tiet = map(int, key.split(','))
        col_name = f'Thứ {thu}'
        if col_name in df.columns and 1 <= tiet <= 10:
            df.loc[tiet, col_name] = value.replace("Lop_","")

    df2 = df.reset_index()

    info_dict = lay_tt_tu_info_school()
    lgiobatdau = info_dict['gio_hoc']
    lgiobatdau = [pt.split('-')[0].strip() for pt in lgiobatdau]
    #print(lgiobatdau)
  
    map_gio = {}
    for cs, pt in enumerate(lgiobatdau):
        map_gio[cs+1] = f"{cs+1} ({pt})" 
    # sua lai nd cot tiet thanh dang: "1 (07:00)",...
    df2['Tiết'] = df2['Tiết'].astype(int).map(map_gio).fillna(df2['Tiết'])

    return df2


