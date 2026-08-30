import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import re
import os
import ast
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st
import base64
import json
from reportlab.platypus import (PageBreak,Paragraph,SimpleDocTemplate,Spacer,Table,TableStyle,)

#################################### SET DAU TRANG #####################################
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem; /* Thay đổi số rem này nhỏ hơn (ví dụ 1rem hoặc 2rem) */
        }
    </style>
""", unsafe_allow_html=True)
JSON_FILE_PATH = "info_tranh_tiet/info_school.json"
if os.path.exists(JSON_FILE_PATH):
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            school_info = json.load(f)
    except Exception as e:
        print(f"Cảnh báo: Không thể đọc tệp JSON do lỗi: {e}")

st.subheader('🏫 ' + school_info.get("ten_truong",""))
##########################################################################################

# 2. Định nghĩa hàm show_tkb_chung (truyền thêm tham số swap_mode)
def show_tkb_chung(dfc, swap_enabled=False):
    custom_css = {
        ".my-blue-header": {
            "background-color": "#0d47a1 !important",
            "color": "#ffffff !important",
            "font-weight": "bold !important"
        },
        ".my-blue-header .ag-header-cell-text": {
            "color": "#ffffff !important"
        }
    }

    # JS hoán vị ô: chỉ chạy logic hoán vị nếu swap_enabled == True
    swap_cells_js = JsCode(f"""
    function(params) {{
        let isSwapActive = {str(swap_enabled).lower()};
        if (!isSwapActive) return;

        if (!window.firstSelectedCell) {{
            window.firstSelectedCell = {{
                rowIndex: params.rowIndex,
                colId: params.column.colId,
                value: params.value,
                rowNode: params.node
            }};
            params.api.refreshCells({{force:true}});
        }} else {{
            let cell1 = window.firstSelectedCell;
            let cell2_value = params.value;

            cell1.rowNode.setDataValue(cell1.colId, cell2_value);
            params.node.setDataValue(params.column.colId, cell1.value);

            window.firstSelectedCell = null;
            params.api.refreshCells({{force:true}});
        }}
    }}
    """)

    # JS tô màu nền & kiểm tra trùng
    cell_style_js = JsCode("""
    function(params) {
        if (!params.data) return null;

        let thuVal = parseInt(params.data["Thứ"]);
        let tietVal = parseInt(params.data["Tiết"]);
        let style = {};

        if (!isNaN(thuVal) && !isNaN(tietVal)) {
            if (thuVal === 2) {
                style.backgroundColor = (tietVal <= 5) ? '#EBF3FF' : '#D6E4FF';
            }
            if (thuVal === 3) {
                style.backgroundColor = (tietVal <= 5) ? '#E8F8EC' : '#D1F2D9';
            }
            if (thuVal === 4) {
                style.backgroundColor = (tietVal <= 5) ? '#F0FCFD' : '#E0F7FA';
            }
            if (thuVal === 5) {
                style.backgroundColor = (tietVal <= 5) ? '#FFFDE7' : '#FFF9D9';
            }
            if (thuVal === 6) {
                style.backgroundColor = (tietVal <= 5) ? '#fae7cb' : '#f7deb8';
            }
            if (thuVal === 7) {
                style.backgroundColor = (tietVal <= 5) ? '#FAEDF9' : '#F3E5F5';
            }
        }

        if (params.column.colId === "Thứ" || params.column.colId === "Tiết") {
            style.color = "darkblue";
            style.fontWeight = "900";
        }

        if (window.firstSelectedCell && 
            window.firstSelectedCell.rowIndex === params.rowIndex && 
            window.firstSelectedCell.colId === params.column.colId) {
            style.backgroundColor = '#ffc107'; // Tô màu vàng nổi bật ô đang chọn hoán vị
            style.color = '#000000';
            style.fontWeight = 'bold';
        }

        let currentValue = params.value;
        if (currentValue !== "" && currentValue !== "nan") {
            let count = 0;
            for (let key in params.data) {
                if (key !== "Thứ" && key !== "Tiết") {
                    if (params.data[key] === currentValue) {
                        count++;
                    }
                }
            }
            if (count > 1) {
                style.color = '#b71c1c';
                style.fontWeight = 'bold';
            }
        }

        return style;
    }
    """)

    gob = GridOptionsBuilder.from_dataframe(dfc)
    gob.configure_grid_options(onCellClicked=swap_cells_js)  
    gob.configure_default_column(
        cellStyle=cell_style_js,
        headerClass="my-blue-header",
        suppressMovable=True,
        resizable=False,
        editable=True,
        width=90, minWidth=90, maxWidth=90
    )

    gob.configure_column("Thứ", pinned="left", width=60, minWidth=60, maxWidth=60, headerClass="my-blue-header")
    gob.configure_column("Tiết", pinned="left", width=60, minWidth=60, maxWidth=60, headerClass="my-blue-header")

    grid_response = AgGrid(
        dfc,
        gridOptions=gob.build(),
        allow_unsafe_jscode=True,
        key="grid_timetable_final",
        update_mode="MODEL_CHANGED"
    )

    if grid_response and "data" in grid_response:
        st.session_state.dftkbc = pd.DataFrame(grid_response["data"])



@st.dialog("🚀 Tổng Quát", width="large")
def tong_quat(dfc):
    with st.form("Dẫn Nhập"):
        st.subheader("💻 Đôi nét về Ứng dụng này:")
        st.markdown('<p style="color: blue;">Ứng dụng này được viết để hỗ trợ cho việc xếp thời khóa biểu trong các Trường học tại VN. Nó được viết bằng mã Python với các thuật toán có trong modul OR-TOOLS của Google.</p>', unsafe_allow_html=True)

        st.subheader("📋 Các bước làm việc với Ứng dụng:")
        st.write(":green[Bước 1:]")
        st.markdown('<p style="color: blue;">Nhập liệu vào file Excel (.xlsx), ví dụ như dưới đây. Chú ý rằng cột Thu và cột Tiet có các giá trị là số nguyên. Các cột còn lại có giá trị kiểu chuỗi. Các ô trống trong bàng hàm chứa ý nghĩa là không được xếp Gv nào vào. (Đó là ô cấm xếp). Tiêu đề các cột như Thu, Tiet, Lop_6A1, v.v...không có dấu. Lop_6A1,...phải viết theo mẫu đó. Các chuỗi trong các ô như Chính_TT hàm chứa Chính là tên Gv, TT là môn Toán, dấu _ ngăn cách. Môn có đúng 2 kí tự do ta đặt và sẽ ghi chú ý nghĩa trong tệp cấu hình. </p>', unsafe_allow_html=True)
        st.dataframe(dfc, hide_index=True)
        st.markdown('<p style="color: blue;">Tên Gv phải khác biệt (không có Gv nào trùng tên, nếu trùng thì lấy thêm tên đệm để khác biệt). Ví dụ T. An, M. An, K. An. Xếp ban đầu trùng hàng ngang vẫn được vì sau đó máy sẽ xếp lại. Nhớ rằng các ô để trống thì máy sẽ không xếp vào đó.</p>', unsafe_allow_html=True)

        st.write(":green[Bước 2:]")
        st.markdown('<p style="color: blue;">Ứng dụng này được viết để hỗ trợ cho việc xếp thời khóa biểu trong các Trường học tại VN. Nó được viết bằng mã Python với các thuật toán có trong modul OR-TOOLS của Google.</p>', unsafe_allow_html=True)

        st.write(":green[Bước 3:]")
        st.markdown('<p style="color: blue;">Ứng dụng này được viết để hỗ trợ cho việc xếp thời khóa biểu trong các Trường học tại VN. Nó được viết bằng mã Python với các thuật toán có trong modul OR-TOOLS của Google.</p>', unsafe_allow_html=True)

        st.write(":green[Bước 4:]")
        st.markdown('<p style="color: blue;">Ứng dụng này được viết để hỗ trợ cho việc xếp thời khóa biểu trong các Trường học tại VN. Nó được viết bằng mã Python với các thuật toán có trong modul OR-TOOLS của Google.</p>', unsafe_allow_html=True)

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()

@st.dialog("✔️ Kiểm tra File Excel", width="medium")
def kiemtra_excel():
    def tao_file_gv_yc_tranh(lgv):
        data = {
            "ten_gv": lgv,
            "yc_tranh_tiet_thu": [""]*len(lgv)
        }
        # 4. Xuất ra bảng DataFrame mới và lưu vào file Excel
        df_output = pd.DataFrame(data)
        df_output = df_output.fillna("").astype(str)
        df_output.to_excel("info_tranh_tiet/gv_yc_tranh.xlsx", index=False)

        return "Đã tạo file gv_yc_tranh.xlsx thành công!"

    def tao_file_lop_yc_tranh(df_tkb):
        # 2. Lấy danh sách tên lớp (các cột ngoại trừ 'Thứ' và 'Tiết')
        list_lop = [col for col in df_tkb.columns if col not in ["Thứ", "Tiết"]]

        result_data = []

        # 3. Duyệt qua từng lớp để tìm các ô trống
        for lop in list_lop:
            cac_cap_trong = []

            # Quét từng dòng trong thời khóa biểu
            for idx, row in df_tkb.iterrows():
                val = row[lop]

                # Kiểm tra nếu ô trống (NaN, None hoặc chuỗi rỗng/khoảng trắng)
                if pd.isna(val) or str(val).strip() == "":
                    thu = int(row["Thứ"])
                    tiet = int(row["Tiết"])
                    cac_cap_trong.append(f"({tiet},{thu})")

            # Nối các cặp thành chuỗi "(tiết, thứ), (tiết, thứ)"
            yc_str = ", ".join(cac_cap_trong)

            result_data.append({"ten_lop": lop, "yc_tranh_tiet_thu": yc_str})

        # 4. Xuất ra bảng DataFrame mới và lưu vào file Excel
        df_output = pd.DataFrame(result_data)
        df_output = df_output.fillna("").astype(str)
        df_output.to_excel("info_tranh_tiet/lop_yc_tranh.xlsx", index=False)

        return "Đã tạo file lop_yc_tranh.xlsx thành công!"

    file_path = "info_tranh_tiet/gv_yc_tranh.xlsx"
    # 1. Đọc dữ liệu từ tệp Excel
    df = pd.read_excel(file_path)
    # 2. Cắt khoảng trắng 2 bên của tên cột (nếu có)
    df.columns = df.columns.astype(str).str.strip()
    # 3. Cắt khoảng trắng 2 bên cho tất cả ô dữ liệu kiểu chuỗi
    #df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

    # 4. Lưu lại vào chính tệp Excel ban đầu (bỏ chỉ số dòng index)
    df.to_excel(file_path, index=False)

    file_path = "Tkb_luu_last/tkb_chung.xlsx"

    # 1. Đọc dữ liệu từ tệp Excel
    df = pd.read_excel(file_path)

    if not os.path.exists("info_tranh_tiet/lop_yc_tranh.xlsx"):

        kq_tao_lop_yc_tranh = tao_file_lop_yc_tranh(df)
    else:
        kq_tao_lop_yc_tranh = "Đã có file lop_yc_tranh.xlsx"    

    df.iloc[:, 2:] = df.iloc[:, 2:].fillna("").astype(str)

    # 2. Cắt khoảng trắng 2 bên của tên cột (nếu có)
    df.columns = df.columns.astype(str).str.strip()
    # 3. Cắt khoảng trắng 2 bên cho tất cả ô dữ liệu kiểu chuỗi
    #df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    # 4. Lưu lại vào chính tệp Excel ban đầu (bỏ chỉ số dòng index)
    df.to_excel(file_path, index=False)

    set_giao_vien = set()
    set_mon_day = set()
    cot_cac_lop = df.columns[2:].tolist()   # Danh sách cac lop (tieu de cua cac cot trong bang tu cot 2)

    so_lop = len(cot_cac_lop)
    so_o_no_ = 0
    so_o_nogv = 0
    so_o_nomon = 0
    so_gv = 0
    so_mon = 0

    # Duyệt qua từng dòng dữ liệu (bỏ qua hàng tiêu đề vì Pandas đã tự lấy làm df.columns)
    for index, row in df.iterrows():
        thu = row.iloc[0]   # goi thu la cot dau tien (cs 0) trong bang (khong phai la ten tieu de cot- Thứ)
        tiet = row.iloc[1]  # goi tiet la cot ke (cs ) trong bang, (khong phai la ten tieu de cot- Tiết)
        #print(index,thu,tiet) # in ra cs, gia tri cua thu, tiet trong trong moi row
        # Duyệt qua từng cột lớp trong dòng đó
        for lop in cot_cac_lop:
            gia_tri_o = row[lop]
            # Kiểm tra ô trống (NaN hoặc chuỗi trống)
            if not (pd.isna(gia_tri_o) or str(gia_tri_o).strip() == "" or str(gia_tri_o).lower() == "nan"):
                if "_" in gia_tri_o:
                    chuoi_o = str(gia_tri_o).strip()    #cat cac khoang trang 2 ben
                    gv = chuoi_o.split('_')[0].strip()
                    if  gv == "":
                        so_o_nogv = so_o_nogv + 1
                    mon = chuoi_o.split('_')[1].strip()
                    if  mon == "":
                        so_o_nomon = so_o_nomon + 1
                    set_giao_vien.add(gv)
                    set_mon_day.add(mon)
    so_gv = len(set_giao_vien)
    so_mon = len(set_mon_day)                
    list_giao_vien = sorted(list(set_giao_vien))

    if not os.path.exists("info_tranh_tiet/gv_yc_tranh.xlsx"):
        kq_tao_gv_yc_tranh = tao_file_gv_yc_tranh(list_giao_vien)
    else:
        kq_tao_gv_yc_tranh = "Đã có file gv_yc_tranh.xlsx"    

    list_mon_day = sorted(list(set_mon_day))
    st.write('Số ô không có _ giữa tên gv và môn: ', so_o_no_)
    st.write('Số ô không có tên gv: ', so_o_nogv)
    st.write('Số ô không có môn: ', so_o_nomon)
    st.write('Số giáo viên: ', so_gv, list_giao_vien)
    st.write('Số môn: ', so_mon , list_mon_day)
    st.write('Số lớp: ', so_lop , cot_cac_lop)
    st.write(':red[Nếu các số chưa khớp thực tế, cần chỉnh lại việc nhập dữ liệu.]')
    st.write(kq_tao_lop_yc_tranh)
    st.write(kq_tao_gv_yc_tranh)

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()

@st.dialog("✏️ Xem/Chỉnh các thông số cấu hình dưới đây và nhấn 'Lưu thay đổi' để cập nhật hệ thống.", width="")
def xem_chinh_info():
    # Định nghĩa đường dẫn tới tệp JSON trên server
    JSON_FILE_PATH = "info_tranh_tiet/info_school.json"

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
    #st.title("⚙️ Cấu Hình Thông Tin & Khung Giờ Học")
    #st.write("Chỉnh sửa các thông số cấu hình dưới đây và nhấn 'Lưu thay đổi' để cập nhật hệ thống.")

    # Tải dữ liệu từ file
    current_info = doc_du_lieu_json(JSON_FILE_PATH)

    # Tạo Form chỉnh sửa
    with st.form("form_edit_school_info"):
        st.subheader("📝 Thông tin chung")
        ten_truong = st.text_input(":blue[Tên trường:]", value=current_info.get("ten_truong", ""))
        dia_chi = st.text_input(":blue[Địa chỉ:]", value=current_info.get("dia_chi", ""))
        so_dien_thoai = st.text_input(":blue[Số điện thoại:]", value=current_info.get("so_dien_thoai", ""))

        st.subheader("🔎 Tra cứu các môn")
        st.write(current_info["cac_mon"])

        #st.subheader("🏫 Tham số cấu hình xếp thời khóa biểu")
        #tong_so_lop = st.number_input(":blue[Tổng số lớp học:]", value=int(current_info.get("tong_so_lop", 50)), min_value=1)
        #so_tiet_toi_da = st.number_input(":blue[Số tiết dạy tối đa của GV / ngày:]", value=int(current_info.get("so_tiet_toi_da_mot_ngay", 5)), min_value=1, max_value=10)
        
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
                gio_tiet = st.text_input(f":blue[Tiết {i+1}:] ", value=list_gio_hoc_hien_tai[i], key=f"tiet_{i+1}")
                updated_gio_hoc.append(gio_tiet)
                
        with col2:
            st.markdown("**🌇 Ca Chiều**")
            for i in range(5, 10):
                # Tạo ô nhập liệu cho từng tiết từ 6 đến 10
                gio_tiet = st.text_input(f":blue[Tiết {i+1}:] ", value=list_gio_hoc_hien_tai[i], key=f"tiet_{i+1}")
                updated_gio_hoc.append(gio_tiet)

        # Nút bấm submit form
        nut_luu = st.form_submit_button("💾 :red[Lưu thay đổi vào Server]")

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
        
        with st.expander("👀 :red[Xem cấu trúc tệp JSON thực tế trên Server]"):
            st.json(updated_info)

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()

@st.dialog("Xeptkb_auto đang chạy...", width="medium")
def chay_trinh_xeptkb(dfc):
    st.write("Đang viết...")
    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()


@st.dialog("In Tkb Lớp", width="medium")
def in_tkb_lop(dfc):
    gio_hoc = [
        "07:00 - 07:45", "07:50 - 08:35", "08:50 - 09:35", "09:40 - 10:25", "10:30 - 11:15",
        "13:00 - 13:45", "13:50 - 14:35", "14:50 - 15:35", "15:40 - 16:25", "16:30 - 17:15"
    ]

    font_path = "fonts/NotoSans-Regular.ttf"
    font_bold_path = "fonts/NotoSans-Bold.ttf"

    if os.path.exists(font_path) and os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont("NotoSans", font_path))
        pdfmetrics.registerFont(TTFont("NotoSans-Bold", font_bold_path))
        f_normal, f_bold = "NotoSans", "NotoSans-Bold"
    else:
        # Dự phòng nếu không tìm thấy font trên hệ thống
        f_normal, f_bold = "Helvetica", "Helvetica-Bold"

    # 1. Đọc dữ liệu ban đầu từ file Excel của bạn
    #df_tkbc = pd.read_excel("Tkb_luu_last/tkb_chung.xlsx")

    # 2. Chuyển bảng từ dạng rộng sang dọc để tạo ra biến df_long
    df_long = dfc.melt(id_vars=['Thứ', 'Tiết'], var_name='Lop', value_name='GiaoVien_Goc')

    # Lọc bỏ các dòng trống
    df_long = df_long.dropna(subset=['GiaoVien_Goc'])


    # Bước 2: Tạo nội dung hiển thị trong ô của học sinh (Tên môn + Tên GV)
    def tao_noi_dung_o_lop(row):
        parts_gv = str(row['GiaoVien_Goc']).split('_')
        ten_gv_short = parts_gv[0].strip()
        ten_mon = parts_gv[1].strip() if len(parts_gv) > 1 else ""
        return f"{ten_mon}\n({ten_gv_short})" if ten_mon else ten_gv_short

    df_long['Noi_Dung_O_Lop'] = df_long.apply(tao_noi_dung_o_lop, axis=1)

    # Bước 3: Duyệt qua danh sách lớp để tạo dict TKB 
    danh_sach_lop = sorted(df_long['Lop'].unique())
    tkb_cac_lop = {}

    for lop in danh_sach_lop:
        df_lop = df_long[df_long['Lop'] == lop]
        
        # Pivot dữ liệu theo Tiết và Thứ cho Lớp
        pivot_lop = df_lop.pivot_table(
            index='Tiết',
            columns='Thứ',
            values='Noi_Dung_O_Lop',
            aggfunc=lambda x: ', '.join(x.unique())
        )
        
        # Định hình khung cố định: Tiết 1-10, Thứ 2-7
        pivot_lop = pivot_lop.reindex(index=range(1, 11), columns=range(2, 8)).fillna('')
        
        # Định dạng lại tiêu đề cột và chỉ mục
        pivot_lop.columns = [f'Thứ {c}' for c in pivot_lop.columns]
        pivot_lop.index.name = 'Tiết'
        pivot_lop = pivot_lop.reset_index()
        
        tkb_cac_lop[lop] = pivot_lop
        #st.write(lop, tkb_cac_lop[lop])
    

    def xuat_pdf_lop_don_le(ten_lop, df_lop, filename="tkb_lop_don_le.pdf"):
        """Xuất file PDF xem riêng 1 lớp (Chữ to rõ ràng)"""
        styles = getSampleStyleSheet()
        style_school = ParagraphStyle("SchL", fontName=f_normal, fontSize=9, leading=11, alignment=0, textColor=colors.HexColor("#7F8C8D"))
        style_title = ParagraphStyle("TtlL", fontName=f_bold, fontSize=12, leading=15, alignment=1, textColor=colors.HexColor("#2C3E50"))
        style_header = ParagraphStyle("HdrL", fontName=f_bold, fontSize=9, leading=12, alignment=1, textColor=colors.whitesmoke)
        style_cell = ParagraphStyle("ClL", fontName=f_normal, fontSize=8.5, leading=11, alignment=1, textColor=colors.black)
        style_footer = ParagraphStyle("FtrL", fontName=f_bold, fontSize=10, leading=13, alignment=2, textColor=colors.HexColor("#2C3E50"))

        doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=30, bottomMargin=30)
        elements = []
        col_widths = [75, 50] + [68] * 6

        # Tính tổng số tiết học thực tế trong tuần của lớp
        tong_so_tiet = df_lop.iloc[:, 1:].map(lambda x: str(x).strip() != '').sum().sum()

        elements.append(Paragraph("TRƯỜNG THPT NGUYEN THI XXXXXX", style_school))
        elements.append(Paragraph(f"<b>THỜI KHÓA BIỂU LỚP: {ten_lop.upper()}</b>", style_title))
        elements.append(Spacer(1, 15))

        table_data = []
        header_row = [Paragraph("Giờ học", style_header), Paragraph("Tiết / Thứ", style_header)] + \
                    [Paragraph(str(col).replace("Thu", "Thứ"), style_header) for col in df_lop.columns[1:]]
        table_data.append(header_row)

        for i, row in df_lop.iterrows():
            row_data = [Paragraph(gio_hoc[i], style_cell), Paragraph(f"Tiết {row['Tiết']}", style_cell)]
            for cell_value in row[1:]:
                # Sử dụng thẻ <br/> để xuống dòng nếu ô có cả Tên môn và Tên giáo viên
                cell_text = str(cell_value).replace('\n', '<br/>')
                row_data.append(Paragraph(cell_text, style_cell))
            table_data.append(row_data)

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2E4053")), # Đổi sang tông màu xám xanh đầm cho học sinh
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (1, -1), colors.HexColor("#F2F4F4")),
            ('BACKGROUND', (2, 1), (-1, 5), colors.white),
            ('BACKGROUND', (2, 6), (-1, 10), colors.HexColor("#FBFCFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#2E4053"))
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Tổng số tiết học trong tuần: {tong_so_tiet} tiết", style_footer))
        
        doc.build(elements)
        return filename


    def xuat_pdf_lop_tong_hop(tkb_dict, filename="tkb_tat_ca_lop.pdf"):
        """Xuất file PDF tổng hợp gom tất cả các lớp (4 bảng/trang A4)"""
        styles = getSampleStyleSheet()
        style_school = ParagraphStyle("SchAllL", fontName=f_normal, fontSize=6, leading=7, alignment=0, textColor=colors.HexColor("#7F8C8D"))
        style_title = ParagraphStyle("TtlAllL", fontName=f_bold, fontSize=7.5, leading=9, alignment=1, textColor=colors.HexColor("#2C3E50"))
        style_header = ParagraphStyle("HdrAllL", fontName=f_bold, fontSize=6.5, leading=8, alignment=1, textColor=colors.whitesmoke)
        style_cell = ParagraphStyle("ClAllL", fontName=f_normal, fontSize=6, leading=7.5, alignment=1, textColor=colors.black)
        style_footer = ParagraphStyle("FtrAllL", fontName=f_bold, fontSize=6, leading=8, alignment=2, textColor=colors.HexColor("#2C3E50"))

        doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=10, bottomMargin=10)
        elements = []
        col_widths = [75, 50] + [68] * 6

        for idx, (ten_lop, df_lop) in enumerate(tkb_dict.items()):
            tong_so_tiet = df_lop.iloc[:, 1:].map(lambda x: str(x).strip() != '').sum().sum()

            elements.append(Paragraph("TRƯỜNG THPT NGUYEN THI XXXXXX", style_school))
            elements.append(Paragraph(f"<b>THỜI KHÓA BIỂU LỚP: {ten_lop.upper()}</b>", style_title))
            elements.append(Spacer(1, 2))

            table_data = []
            header_row = [Paragraph("Giờ học", style_header), Paragraph("Tiết / Thứ", style_header)] + \
                        [Paragraph(str(col).replace("Thu", "Thứ"), style_header) for col in df_lop.columns[1:]]
            table_data.append(header_row)

            for i, row in df_lop.iterrows():
                row_data = [Paragraph(gio_hoc[i], style_cell), Paragraph(f"Tiết {row['Tiết']}", style_cell)]
                for cell_value in row[1:]:
                    cell_text = str(cell_value).replace('\n', '<br/>')
                    row_data.append(Paragraph(cell_text, style_cell))
                table_data.append(row_data)

            t = Table(table_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2E4053")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 0.2),   
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2),
                ('BACKGROUND', (0, 1), (1, -1), colors.HexColor("#F2F4F4")),
                ('BACKGROUND', (2, 1), (-1, 5), colors.white),
                ('BACKGROUND', (2, 6), (-1, 10), colors.HexColor("#FBFCFC")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor("#2E4053"))
            ]))

            elements.append(t)
            elements.append(Spacer(1, 1))
            from reportlab.lib.enums import TA_LEFT

            # Căn trái cho style_footer
            style_footer.alignment = TA_LEFT

            elements.append(
                Paragraph(f"Tổng số tiết học trong tuần: {tong_so_tiet} tiết.  Áp dụng từ ngày 05/09/2026", style_footer)
            )

            #elements.append(Paragraph(f"Tổng số tiết học trong tuần: {tong_so_tiet} tiết", style_footer))

            # Thuật toán ngắt trang: Cứ nhóm 4 lớp xếp chồng gọn vào 1 trang A4
            if (idx + 1) % 3 == 0:
                if idx < len(tkb_dict) - 1:
                    elements.append(PageBreak())
            else:
                elements.append(Spacer(1, 80)) # Khoảng cách 2 dòng chữ giữa các bảng

        doc.build(elements)
        return filename


    tab_lop1, tab_lop2, tab_lop3 = st.tabs(["🔍 In riêng từng Lớp", "📦 Xuất file in hàng loạt Lớp", "Chỉ in Tkb Lớp có thay đổi"])

    def hien_thi_pdf_tren_web(file_path, height=600):
        """Hàm nhúng PDF vào giao diện Streamlit bằng iframe"""
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)


    #--- TAB 1: XEM RIÊNG TỪNG LỚP ---
    with tab_lop1:
        st.subheader("Chọn Lớp học để xem trước thời khóa biểu")
        lop_duoc_chon = st.selectbox("Chọn tên Lớp từ danh sách:", options=sorted(list(tkb_cac_lop.keys())))
        if lop_duoc_chon:
            df_lop_chon = tkb_cac_lop[lop_duoc_chon]
            file_lop_don = xuat_pdf_lop_don_le(lop_duoc_chon, df_lop_chon)
            
        with open(file_lop_don, "rb") as f:
            st.download_button(label=f"📥 Tải file PDF của Lớp {lop_duoc_chon}",
                data=f,
                file_name=f"TKB_Lop_{lop_duoc_chon}.pdf",
                mime="application/pdf",
                key="btn_lop_single")
                
            hien_thi_pdf_tren_web(file_lop_don, height=500)

    #--- TAB 2: XUẤT FILE TỔNG HỢP CHO TẤT CẢ CÁC LỚP ---
    with tab_lop2:
        st.subheader("Đóng gói thời khóa biểu của mọi lớp vào 1 file PDF tổng")
        st.write("Bố cục tối ưu tự động: xếp chồng 4 lớp trên một trang A4.")
        if st.button("🚀 Bắt đầu tạo file PDF tổng các lớp", key="btn_lop_all"):
            with st.spinner("Hệ thống đang tổng hợp dữ liệu các lớp học..."):
                pdf_file_lop_tong = xuat_pdf_lop_tong_hop(tkb_cac_lop)
                st.success("🎉 Đã tạo thành công file PDF chung cho toàn bộ các lớp học!")
            with open(pdf_file_lop_tong, "rb") as f:
                st.download_button(label="📥 Tải file PDF tổng hợp (Tất cả các Lớp)",
                    data=f,
                    file_name="TKB_Tong_Hop_Cac_Lop.pdf",
                    mime="application/pdf",
                    key="btn_download_lop_all")
                hien_thi_pdf_tren_web(pdf_file_lop_tong, height=800)

    #--- TAB 3: XUẤT FILE TỔNG HỢP CHO TẤT CẢ CÁC LỚP ---
    with tab_lop3:
        st.subheader("Chua viet ma")

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()

@st.dialog("In Tkb Toàn Trường ", width="large")
def  in_tkb_truong(dfc):
    # Đọc file gốc từ Excel của bạn (Cột là Lớp, Dòng là Tiết)

    # Điền mốc giờ học tương ứng với 10 tiết dạy để hiển thị thêm
    map_gio_hoc = {
        1: "09:00-07:45",
        2: "07:50-08:35",
        3: "08:50-09:35",
        4: "09:40-10:25",
        5: "10:30-11:15",
        6: "13:00-13:45",
        7: "13:50-14:35",
        8: "14:50-15:35",
        9: "15:40-16:25",
        10: "16:30-17:15",
    }
    # Đường dẫn tới tệp cấu hình JSON trên server
    JSON_FILE_PATH = "info_tranh_tiet/info_school.json"
    # Tiến hành đọc cấu hình giờ học thực tế từ tệp JSON
    if os.path.exists(JSON_FILE_PATH):
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                school_info = json.load(f)
                # Lấy dữ liệu của khóa "Gio_hoc", nếu không tìm thấy key này thì giữ nguyên mảng mặc định
                if "Gio_hoc" in school_info:
                    map_gio_hoc = {key: new_val for (key, old_val), new_val in zip(map_gio_hoc.items(), school_info["Gio_hoc"])}
        except Exception as e:
            # Nếu tệp JSON bị lỗi cú pháp khi người dùng sửa, in ra cảnh báo và dùng giờ mặc định
            print(f"Cảnh báo: Không thể đọc tệp JSON do lỗi: {e}")
    # thay khung gio hoc xong        

    dfc["Giờ học"] = dfc["Tiết"].map(map_gio_hoc)

    # Sắp xếp lại thứ tự cột để đưa "Thu", "Tiet", "Giờ học" lên đầu bảng đối chiếu
    cac_cot_co_dinh = ["Thứ", "Tiết", "Giờ học"]
    cac_cot_lop = [col for col in dfc.columns if col not in cac_cot_co_dinh]

    # Đảm bảo dữ liệu trống được điền chuỗi rỗng
    dfc = dfc.fillna("")

    # ==============================================================================
    # PHẦN 2: HÀM KẾT XUẤT FILE PDF KHỔ A4 DỌC (GIỮ NGUYÊN DẠNG LƯỚI EXCEL)
    # ==============================================================================


    def xuat_pdf_tkb_chung_a4_luoi_excel(df_data, filename="tkb_toan_truong_a4_luoi.pdf"):
        # 1. Cấu hình Font chữ tiếng Việt chuẩn văn giáo dục Times New Roman
        # Khởi tạo Font Noto Sans (Unicode đầy đủ, hỗ trợ tiếng Việt)
        font_path = "fonts/NotoSans-Regular.ttf"
        font_bold_path = "fonts/NotoSans-Bold.ttf"

        if os.path.exists(font_path) and os.path.exists(font_bold_path):
            pdfmetrics.registerFont(TTFont("NotoSans", font_path))
            pdfmetrics.registerFont(TTFont("NotoSans-Bold", font_bold_path))
            f_normal, f_bold = "NotoSans", "NotoSans-Bold"
        else:
            # Dự phòng nếu không tìm thấy font trên hệ thống
            f_normal, f_bold = "Helvetica", "Helvetica-Bold"

        # 2. Tạo Styles chữ cho khổ A4 dọc dạng lưới (Đã thu nhỏ cỡ chữ để giảm độ cao dòng)
        styles = getSampleStyleSheet()
        style_school = ParagraphStyle('SchA4L', fontName=f_normal, fontSize=8, leading=10, alignment=0, textColor=colors.HexColor("#7F8C8D"))
        style_title = ParagraphStyle('TtlA4L', fontName=f_bold, fontSize=12, leading=15, alignment=1, textColor=colors.HexColor("#1A5276"))
        
        style_header = ParagraphStyle('HdrA4L', fontName=f_bold, fontSize=7, leading=8.5, alignment=1, textColor=colors.whitesmoke)
        style_cell = ParagraphStyle('ClA4L', fontName=f_normal, fontSize=6.5, leading=8, alignment=1, textColor=colors.black)
        style_time_cell = ParagraphStyle('TimeA4L', fontName=f_bold, fontSize=6.5, leading=8, alignment=1, textColor=colors.HexColor("#1A5276"))

        # 3. Cấu hình file PDF khổ A4 đứng (Portrait), đặt lề hẹp 20 points để tối ưu không gian chiều ngang
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=20,
            rightMargin=20,
            topMargin=20,
            bottomMargin=20,
        )
        elements = []

        # CẤU HÌNH SỐ LỚP TRÊN MỖI TRANG A4 DỌC:
        # Tổng chiều ngang khả dụng sau khi trừ lề là ~555 points.
        # 3 cột cố định chiếm: Thứ (35pt) + Tiết (30pt) + Giờ học (60pt) = 125 points.
        # Còn lại 430 points dành cho các cột lớp. 
        # => Để chữ to rõ ràng, mỗi trang chứa đẹp nhất là 6 lớp (mỗi cột lớp rộng ~71 points).
        SO_LOP_MOI_TRANG_A4 = 6

        # Vòng lặp chia cắt các lớp thành từng cụm trang dọc
        for idx, i in enumerate(range(0, len(cac_cot_lop), SO_LOP_MOI_TRANG_A4)):
            nhom_lop_hien_tai = cac_cot_lop[i : i + SO_LOP_MOI_TRANG_A4]

            # Lọc ra các cột cần in cho cụm trang này
            cac_cot_can_in = cac_cot_co_dinh + list(nhom_lop_hien_tai)
            df_trang_a4 = df_data[cac_cot_can_in]

            # Thêm tiêu đề trang
            elements.append(Paragraph("TRƯỜNG THPT NGUYEN THI XXXXXX", style_school))
            nhom_lop_hien_tai = [pt.replace("Lop_", "") for pt in nhom_lop_hien_tai]
            strnhom=''
            for pt in nhom_lop_hien_tai:
                strnhom = strnhom+pt+", "
            strnhom = strnhom[0: -2]    
            elements.append(
                Paragraph(
                    #f"<b>THỜI KHÓA BIỂU TOÀN TRƯỜNG - CÁC LỚP: {strnhom} ĐẾN {nhom_lop_hien_tai[-1]}</b>",
                    f"<b>THỜI KHÓA BIỂU TOÀN TRƯỜNG - CÁC LỚP: {strnhom}</b>",
                    style_title,
                )
            )
            elements.append(Spacer(1, 12))

            # Đổ dữ liệu vào cấu trúc bảng của ReportLab
            table_data = []

            # Tạo hàng tiêu đề cột (Header) giống y hệt Excel
            header_row = []
            for col in df_trang_a4.columns:
                text_col = str(col)
                header_row.append(Paragraph(text_col, style_header))
            table_data.append(header_row)

            # Đổ dữ liệu 60 dòng (10 tiết x 6 ngày) chạy dọc xuống dưới
            for _, row in df_trang_a4.iterrows():
                row_data = []
                # Các ô tiêu đề trái ít chữ vẫn giữ Paragraph để định dạng font Bold đẹp
                row_data.append(Paragraph(f"Thứ {row['Thứ']}", style_time_cell))
                row_data.append(Paragraph(f"T.{row['Tiết']}", style_time_cell))
                row_data.append(Paragraph(str(row['Giờ học']), style_cell))
                
                # GIẢI PHÁP ÉP DÒNG: Loại bỏ lớp Paragraph ở các ô môn học, chỉ truyền chuỗi string thuần
                for cell_value in row[3:]:
                    cell_text = str(cell_value).replace('_', '-')
                    row_data.append(cell_text) # Truyền chữ thuần giúp ReportLab nén dòng cực nhỏ
                    
                table_data.append(row_data)

            # CẤU HÌNH ĐỘ RỘNG CỘT (Đã fix lỗi cú pháp hiển thị):
            do_rong_cac_cot_lop = [430 / len(nhom_lop_hien_tai)] * len(nhom_lop_hien_tai)
            col_widths = [35, 30, 60] + do_rong_cac_cot_lop

            # --- CẤU HÌNH CHIỀU CAO DÒNG SIÊU MỎNG ---
            # Hàng tiêu đề 0 rộng 14 points, 60 hàng tiếp theo gán cố định chỉ 10.5 points (siêu mỏng)
            heights = [14] + [10.5] * 60

            # Khởi tạo bảng và truyền thêm tham số rowHeights vào
            t = Table(table_data, colWidths=col_widths, rowHeights=heights)
            
            # Thiết kế TableStyle tối giản đệm ô (Padding bằng 0)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A5276")), 
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Ép phông chữ và cỡ chữ trực tiếp trong TableStyle cho các ô dữ liệu thuần string
                ('FONTNAME', (3, 1), (-1, -1), f_normal),
                ('FONTSIZE', (3, 1), (-1, -1), 6),
                ('TEXTCOLOR', (3, 1), (-1, -1), colors.black),
                
                # --- ĐẶT PADDING BẰNG 0 ĐỂ DÒNG CO LẠI TỐI ĐA ---
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('LEFTPADDING', (0, 0), (-1, -1), 0.5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0.5),
                
                ('BACKGROUND', (0, 1), (2, -1), colors.HexColor("#EBF5FB")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                
                # Tô màu nền phân biệt theo khối ngày học
                ('ROWBACKGROUNDS', (3, 1), (-1, 10), [colors.white]),                          
                ('ROWBACKGROUNDS', (3, 11), (-1, 20), [colors.HexColor("#F9F9F9")]),            
                ('ROWBACKGROUNDS', (3, 21), (-1, 30), [colors.white]),                          
                ('ROWBACKGROUNDS', (3, 31), (-1, 40), [colors.HexColor("#F9F9F9")]),            
                ('ROWBACKGROUNDS', (3, 41), (-1, 50), [colors.white]),                          
                ('ROWBACKGROUNDS', (3, 51), (-1, 60), [colors.HexColor("#F9F9F9")]),            
                ('BOX', (0, 0), (-1, -1), 1.8, colors.HexColor("#1A5276"))
            ]))


            elements.append(t)

            # Kích hoạt ngắt sang trang A4 đứng mới cho cụm lớp tiếp theo
            if i + SO_LOP_MOI_TRANG_A4 < len(cac_cot_lop):
                elements.append(PageBreak())

        doc.build(elements)
        return filename


    # ==============================================================================
    # PHẦN 3: GIAO DIỆN HIỂN THỊ TRÊN WEB STREAMLIT
    # ==============================================================================
    #st.subheader("📊 In TKB Tổng Hợp Toàn Trường Khổ A4 Dọc")


    def hien_thi_pdf_luoi_a4_web(file_path):
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)


    if st.button("🚀 Xuất file TKB dạng Lưới Excel (Khổ A4 dọc)"):
        with st.spinner("Đang chia cụm lớp và đóng gói PDF chuẩn lưới..."):
            file_luoi_out = xuat_pdf_tkb_chung_a4_luoi_excel(dfc)

        st.success("🎉 Đã xuất bản file PDF chuẩn lưới Excel thành công!")


        with open(file_luoi_out, "rb") as f:
            st.download_button(label="📥 Tải file PDF lưới Excel (Khổ A4)",
                data=f,
                file_name="TKB_Toan_Truong_Luoi_Excel_A4.pdf",
                mime="application/pdf",)
            #st.write("### 📄 Bản xem trước trang in (Dạng lưới Excel quen thuộc):")
        hien_thi_pdf_luoi_a4_web(file_luoi_out)

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()


@st.dialog("💾 Save to Excel and Download", width="medium")
def save_excel_download(dftkbc):
    file_path = "Tkb_luu_last/tkb_chung.xlsx"
    try:
        # 1. Lưu file vào thư mục
        st.session_state.dftkbc.to_excel(file_path, index=False)
        st.success(f"🎉 Đã lưu TKB cập nhật thành công vào tệp: {file_path}")
        
        # 2. Đọc file và tạo nút Download
        with open(file_path, "rb") as f:
            st.download_button(
                label="📥 Tải xuống file TKB Excel",
                data=f,
                file_name="tkb_truong_cap_nhat.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"Lỗi khi lưu file: {e}")

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()

@st.dialog("Xem/Chỉnh yêu cầu tránh tiết của Lớp", width="medium")
def dialog_lop_trt(ten_lop, yc_hien_tai=None):
    st.write(ten_lop)

    EXCEL_FILE = "info_tranh_tiet/lop_yc_tranh.xlsx"
    
    lop = ten_lop

    # --- 1. ĐỌC/KHỞI TẠO FILE EXCEL ---
    def load_data():
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            # Đảm bảo có đủ 2 cột bắt buộc
            for col in ["ten_lop", "yc_tranh_tiet_thu"]:
                if col not in df.columns:
                    df[col] = ""
        else:
            df = pd.DataFrame(columns=["ten_lop", "yc_tranh_tiet_thu"])
            df.to_excel(EXCEL_FILE, index=False)
        return df


    def save_data(df):
        df.to_excel(EXCEL_FILE, index=False)
        st.success(f"Đã lưu thành công tránh tiết cho lớp {ten_lop}!")



    # Lấy dữ liệu hiện tại
    df_excel = load_data()


    # --- 2. HÀM TẠO CHUỖI VÀ DỰNG MA TRẬN ---
    def create_empty_matrix():
        columns = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        df = pd.DataFrame(" ", index=range(1, 11), columns=columns)
        df.index.name = "Tiết"
        return df


    def parse_yc_to_matrix(yc_str):
        df_matrix = create_empty_matrix()
        if pd.notna(yc_str) and str(yc_str).strip():
            matches = re.findall(r"\((\d+)\s*,\s*(\d+)\)", str(yc_str))
            for tiet_str, thu_str in matches:
                tiet, thu = int(tiet_str), int(thu_str)
                if 1 <= tiet <= 10 and 2 <= thu <= 7:
                    df_matrix.loc[tiet, f"Thứ {thu}"] = "x"
        return df_matrix


    def matrix_to_yc_str(df_matrix):
        pairs = []
        for tiet in range(1, 11):
            for thu in range(2, 8):
                val = str(df_matrix.loc[tiet, f"Thứ {thu}"]).strip().lower()
                if val == "x":
                    pairs.append(f"({tiet},{thu})")
        return ", ".join(pairs)


    # --- 3. DIALOG NHẬP / CHỈNH SỬA CHO TỪNG LỚP ---
    #@st.dialog("Nhập yêu cầu tránh tiết - thứ", width="large")
    def open_input_dialog(ten_lop, yc_hien_tai=None):
        #st.subheader(f"Lớp: {ten_lop}")

        # Parse dữ liệu sẵn có (nếu có) vào ma trận
        df_matrix_init = parse_yc_to_matrix(yc_hien_tai)

        columns = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        column_config = {
            col: st.column_config.TextColumn(col, max_chars=1, default=" ")
            for col in columns
        }

        st.write("Đánh dấu **x** vào các tiết/thứ cần tránh:")
        edited_matrix = st.data_editor(df_matrix_init, column_config=column_config)

        if st.button("Lưu dữ liệu", type="primary"):
            # Chuyển bảng ma trận thành chuỗi dạng "(1,2), (1,3)"
            yc_str_new = matrix_to_yc_str(edited_matrix)

            # Cập nhật vào DataFrame Excel
            df = load_data()
            if ten_lop in df["ten_lop"].values:
                df.loc[df["ten_lop"] == ten_lop, "yc_tranh_tiet_thu"] = yc_str_new
            else:
                new_row = pd.DataFrame(
                    [{"ten_lop": ten_lop, "yc_tranh_tiet_thu": yc_str_new}]
                )
                df = pd.concat([df, new_row], ignore_index=True)

            save_data(df)


    # Kiểm tra lớp có trong Excel chưa
    row = df_excel[df_excel["ten_lop"] == lop]

    if not row.empty:
        yc_val = row["yc_tranh_tiet_thu"].values[0]
        open_input_dialog(lop, yc_val)
    else:
        st.warning("Chưa có trong Excel")
        open_input_dialog(lop, None)

    if st.button("Đóng"):
        # Reset active_dialog và đưa selectbox về trạng thái chưa chọn (None)
        st.session_state.active_dialog = None
        st.session_state.select_lop_trt = None
        st.rerun()

@st.dialog("Xem/Chỉnh yêu cầu tránh tiết của Gv", width="medium")
def dialog_gv_trt(ten_gv, yc_hien_tai=None):
    st.write(ten_gv)
    
    EXCEL_FILE = "info_tranh_tiet/gv_yc_tranh.xlsx"
    gv = ten_gv

    # --- 1. ĐỌC/KHỞI TẠO FILE EXCEL ---
    def load_data():
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            df = df.fillna("").astype(str)

            # Đảm bảo có đủ 2 cột bắt buộc
            for col in ["ten_gv", "yc_tranh_tiet_thu"]:
                if col not in df.columns:
                    df[col] = ""
        else:
            df = pd.DataFrame(columns=["ten_gv", "yc_tranh_tiet_thu"])
            df = df.fillna("").astype(str)
            df.to_excel(EXCEL_FILE, index=False)
        return df


    def save_data(df):
        df.to_excel(EXCEL_FILE, index=False)
        st.success(f"Đã lưu thành công tránh tiết cho Gv {ten_gv}!")




    # Lấy dữ liệu hiện tại
    df_excel = load_data()


    # --- 2. HÀM TẠO CHUỖI VÀ DỰNG MA TRẬN ---
    def create_empty_matrix():
        columns = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        df = pd.DataFrame(" ", index=range(1, 11), columns=columns)
        df.iloc[:, 1:] = df.iloc[:, 1:].fillna("").astype(str)

        df.index.name = "Tiết"
        return df


    def parse_yc_to_matrix(yc_str):
        df_matrix = create_empty_matrix()
        if pd.notna(yc_str) and str(yc_str).strip():
            matches = re.findall(r"\((\d+)\s*,\s*(\d+)\)", str(yc_str))
            for tiet_str, thu_str in matches:
                tiet, thu = int(tiet_str), int(thu_str)
                if 1 <= tiet <= 10 and 2 <= thu <= 7:
                    df_matrix.loc[tiet, f"Thứ {thu}"] = "x"
        return df_matrix


    def matrix_to_yc_str(df_matrix):
        pairs = []
        for tiet in range(1, 11):
            for thu in range(2, 8):
                val = str(df_matrix.loc[tiet, f"Thứ {thu}"]).strip().lower()
                if val == "x":
                    pairs.append(f"({tiet},{thu})")
        return ", ".join(pairs)


    # --- 3. DIALOG NHẬP / CHỈNH SỬA CHO TỪNG LỚP ---
    #@st.dialog("Nhập yêu cầu tránh tiết - thứ", width="large")
    def gv_input_dialog(ten_gv, yc_hien_tai=None):
        #st.subheader(f"Lớp: {ten_lop}")

        # Parse dữ liệu sẵn có (nếu có) vào ma trận
        df_matrix_init = parse_yc_to_matrix(yc_hien_tai)

        columns = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        column_config = {
            col: st.column_config.TextColumn(col, max_chars=1, default=" ")
            for col in columns
        }

        st.write("Đánh dấu **x** vào các tiết/thứ cần tránh:")
        edited_matrix = st.data_editor(df_matrix_init, column_config=column_config)

        if st.button("Lưu dữ liệu", type="primary"):
            # Chuyển bảng ma trận thành chuỗi dạng "(1,2), (1,3)"
            yc_str_new = matrix_to_yc_str(edited_matrix)

            # Cập nhật vào DataFrame Excel
            df = load_data()
            if ten_gv in df["ten_gv"].values:
                df.loc[df["ten_gv"] == ten_gv, "yc_tranh_tiet_thu"] = yc_str_new
            else:
                new_row = pd.DataFrame(
                    [{"ten_gv": ten_gv, "yc_tranh_tiet_thu": yc_str_new}]
                )
                df = pd.concat([df, new_row], ignore_index=True)

            save_data(df)


    # Kiểm tra lớp có trong Excel chưa
    row = df_excel[df_excel["ten_gv"] == gv]

    if not row.empty:
        yc_val = row["yc_tranh_tiet_thu"].values[0]
        gv_input_dialog(gv, yc_val)
    else:
        st.warning("Chưa có trong Excel")
        gv_input_dialog(gv, None)

    if st.button("Đóng"):
        # Reset active_dialog và đưa selectbox về trạng thái chưa chọn (None)
        st.session_state.active_dialog = None
        st.session_state.select_gv_trt = None
        st.rerun()

# 2. Khai báo các Dialog
@st.dialog("Xem TKB")
def dialog_gv_tkb(df, gv_name):
    st.write(f"của giáo viên: **{gv_name}**")
    # Đưa chỉ số index (1-10) thành 1 cột và đặt tên cột cũ đó là "Tiết"
    df = df.reset_index().rename(columns={'index': 'Tiết'})
    # Hàm tô màu cho cột Tiết
    def color_tiet(val):
        color = 'lightgreen' if val >= 6 else 'lightblue'
        return f'background-color: {color}'
    # Hàm tô màu cho cac cột khac dựa vào index
    def color_name(val, row_index):
        color = 'lightgreen' if row_index >= 5 else 'lightblue'
        return f'background-color: {color}'

    # Áp dụng style
    styled_df = df.style.map(color_tiet, subset=['Tiết'])
    # Áp dụng cho các cột còn lại theo index
    styled_df = styled_df.apply(
        lambda col: [
            color_name(val, i) for i, val in enumerate(col)
        ],
        subset=['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
    )
    st.dataframe(styled_df, hide_index=True)
    if st.button("Đóng"):
        # Reset active_dialog và đưa selectbox về trạng thái chưa chọn (None)
        st.session_state.active_dialog = None
        st.session_state.select_gv_tkb = None
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

    return df

@st.dialog("In Tkb Gv ", width="large")
def  in_tkb_gv(dfc):
    df = dfc
    # 2. Chuyển bảng từ dạng rộng sang dọc. GiaoVien_Goc co dang Tien_TT
    # 2 cột 'Thứ', 'Tiết' là của df , 2 cột 'Lop', 'GiaoVien_Goc' do ta đặt đẻ mang tiêu dề của column trong df
    # va value_name='GiaoVien_Goc' de mang gia tri cua var_name='Lop' cot tieu de cua df  
    df_long = df.melt(id_vars=['Thứ', 'Tiết'], var_name='Lop', value_name='GiaoVien_Mon')

    # Lọc bỏ dòng trống
    df_long = df_long.dropna(subset=['GiaoVien_Mon'])

    # 3a. Tách lấy tên GV đứng trước dấu "_" và loại bỏ khoảng trắng dư thừa
    df_long['GiaoVien'] = df_long['GiaoVien_Mon'].str.split('_').str[0].str.strip()

    # 3b. Tách lấy tên mon đứng sâu dấu "_" và loại bỏ khoảng trắng dư thừa
    df_long['Monday'] = df_long['GiaoVien_Mon'].str.split('_').str[1].str.strip()

    df_long['Lop_Mon'] = df_long['Lop']+"-"+df_long['Monday']


    #print(df_long['Mon'])
    khung_thu = [f"Thứ {i}" for i in range(2, 8)]

    # 4. Tạo thời khóa biểu cho từng giáo viên
    danh_sach_gv = df_long['GiaoVien'].unique()
    # chi lay cac pt co va sau khi cat bo trang 2 ben thi no van co
    danh_sach_gv = [x for x in danh_sach_gv if x and str(x).strip()]

    tkb_giao_vien = {}

    for gv in danh_sach_gv:
        df_gv = df_long[df_long['GiaoVien'] == gv]


        # Dùng pivot_table và nối các lớp bằng dấu phẩy nếu GV dạy nhiều lớp cùng tiết
        pivot_gv = df_gv.pivot_table(
            index='Tiết', 
            columns='Thứ', 
            values='Lop_Mon', 
            aggfunc=lambda x: ', '.join(x.unique())  # Dùng unique để tránh lặp lại tên lớp
        )
        
        
        # Định hình khung cố định: Tiết 1-10, Thứ 2-7
        pivot_gv = pivot_gv.reindex(index=range(1, 11), columns=range(2, 8)).fillna('')
        
        # Định dạng lại tiêu đề cột và chỉ mục
        pivot_gv.columns = [f'Thứ {c}' for c in pivot_gv.columns]
        pivot_gv.index.name = 'Tiết'
        pivot_gv = pivot_gv.reset_index()
        
        tkb_giao_vien[gv] = pivot_gv

        #st.write(gv, tkb_giao_vien[gv])
        
    # Khung giờ mặc định dự phòng (nếu không đọc được file JSON)
    gio_hoc = [
        "08:00 - 09:45", "07:50 - 08:35", "08:50 - 09:35", "09:40 - 10:25", "10:30 - 11:15",
        "13:00 - 13:45", "13:50 - 14:35", "14:50 - 15:35", "15:40 - 16:25", "16:30 - 17:15"
    ]
    # Đường dẫn tới tệp cấu hình JSON trên server
    JSON_FILE_PATH = "info_tranh_tiet/info_school.json"
    # Tiến hành đọc cấu hình giờ học thực tế từ tệp JSON
    if os.path.exists(JSON_FILE_PATH):
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                school_info = json.load(f)
                # Lấy dữ liệu của khóa "Gio_hoc", nếu không tìm thấy key này thì giữ nguyên mảng mặc định
                if "Gio_hoc" in school_info:
                    gio_hoc = school_info["Gio_hoc"]
        except Exception as e:
            # Nếu tệp JSON bị lỗi cú pháp khi người dùng sửa, in ra cảnh báo và dùng giờ mặc định
            print(f"Cảnh báo: Không thể đọc tệp JSON do lỗi: {e}")

    # thay khung gio hoc xong        
    font_path = "fonts/NotoSans-Regular.ttf"
    font_bold_path = "fonts/NotoSans-Bold.ttf"

    if os.path.exists(font_path) and os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont("NotoSans", font_path))
        pdfmetrics.registerFont(TTFont("NotoSans-Bold", font_bold_path))
        f_normal, f_bold = "NotoSans", "NotoSans-Bold"
    else:
        # Dự phòng nếu không tìm thấy font trên hệ thống
        f_normal, f_bold = "Helvetica", "Helvetica-Bold"

    def xuat_pdf_tong_hop(tkb_dict, filename="tkb_tat_ca_gv.pdf"):

        # Khởi tạo Font Noto Sans (Unicode đầy đủ, hỗ trợ tiếng Việt)
        font_path = "fonts/NotoSans-Regular.ttf"
        font_bold_path = "fonts/NotoSans-Bold.ttf"

        if os.path.exists(font_path) and os.path.exists(font_bold_path):
            pdfmetrics.registerFont(TTFont("NotoSans", font_path))
            pdfmetrics.registerFont(TTFont("NotoSans-Bold", font_bold_path))
            f_normal, f_bold = "NotoSans", "NotoSans-Bold"
        else:
            # Dự phòng nếu không tìm thấy font trên hệ thống
            f_normal, f_bold = "Helvetica", "Helvetica-Bold"



        # 2. Tạo Styles thiết kế văn bản
        styles = getSampleStyleSheet()
        style_school = ParagraphStyle(
            "Sch", fontName=f_normal, fontSize=6, leading=7, alignment=0, textColor=colors.HexColor("#7F8C8D")
        )
        style_title = ParagraphStyle(
            "Ttl", fontName=f_bold, fontSize=7.5, leading=9, alignment=1, textColor=colors.HexColor("#2C3E50")
        )
        style_header = ParagraphStyle(
            "Hdr", fontName=f_bold, fontSize=6.5, leading=8, alignment=1, textColor=colors.whitesmoke
        )
        style_cell = ParagraphStyle(
            "Cl", fontName=f_normal, fontSize=6.5, leading=8, alignment=1, textColor=colors.black
        )
        style_footer = ParagraphStyle(
            "Ftr", fontName=f_bold, fontSize=6.5, leading=8, alignment=2, textColor=colors.HexColor("#2C3E50")
        )

        # 3. Tạo mẫu layout tài liệu PDF (Khổ A4 đứng, lề 10 points)
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=30,
            rightMargin=30,
            topMargin=10,
            bottomMargin=10,
        )
        elements = []

        # Phân bổ độ rộng các cột: Giờ học (75pt) | Tiết (50pt) | 6 cột Thứ (mỗi cột 68pt) = Tổng 533pt vừa khít trang
        #col_widths = + * 6
        col_widths = [75, 50] + [68] * 6

        # 4. Duyệt qua từng Giáo viên trong dict dữ liệu thực tế của bạn
        for idx, (ten_gv, df_gv) in enumerate(tkb_dict.items()):

            # Tính tổng số tiết dạy: Đếm các ô có dữ liệu thực tế (loại bỏ ô rỗng hoặc chữ nghỉ)
            # Vì cấu trúc df_gv của bạn có cột 'Tiet' ở đầu, ta chỉ tính toán trên các cột Thứ (từ cột index 1 trở đi)
            df_chi_co_mon = df_gv.iloc[:, 1:]
            tong_so_tiet = (
                df_chi_co_mon.map(
                    lambda x: str(x).strip().lower() not in ["", "", ""]
                )
                .sum()
                .sum()
            )

            # Chèn tiêu đề tên trường và tên Giáo viên
            elements.append(Paragraph("TRƯỜNG THPT NGUYEN THI XXXXXX", style_school))
            elements.append(
                Paragraph(
                    f"<b>THỜI KHÓA BIỂU GIÁO VIÊN: {ten_gv.upper()}</b>", style_title
                )
            )
            elements.append(Spacer(1, 2))

            # Đọc dữ liệu từ DataFrame của bạn đổ vào Table ReportLab
            table_data = []

            # Tạo hàng tiêu đề: Giờ học | Tiết / Thứ | Thu 2 | Thu 3 | ... | Thu 7
            # Lấy tên các cột Thứ có sẵn trong df_gv của bạn chuyển sang dạng chữ đẹp
            header_row = [
                Paragraph("Giờ học", style_header),
                Paragraph("Tiết / Thứ", style_header),
            ] + [
                Paragraph(str(col).replace("Thu", "Thứ"), style_header)
                for col in df_gv.columns[1:]
            ]   # KHONG CO Thu ne khong quan tam 
            table_data.append(header_row)

            # Đổ dữ liệu 10 hàng tương ứng với 10 tiết
            for i, row in df_gv.iterrows():
                tiet_label = f"Tiết {row['Tiết']}"

                # Cột 1: Giờ học | Cột 2: Tiết học
                row_data = [
                    Paragraph(gio_hoc[i], style_cell),
                    Paragraph(tiet_label, style_cell),
                ]

                # Cột 3 -> 8: Các ô chứa lớp học ("12A3-NV")
                for cell_value in row[1:]:
                    row_data.append(Paragraph(str(cell_value), style_cell))

                table_data.append(row_data)

            # Định dạng giao diện màu sắc cho bảng
            t = Table(table_data, colWidths=col_widths)
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E8449")),  # Thanh tiêu đề màu xanh lá
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
                        # Màu nền xanh nhạt cố định cho 2 cột tiêu đề bên trái (Giờ & Tiết)
                        ("BACKGROUND", (0, 1), (1, -1), colors.HexColor("#EAFAF1")),
                        # Phân chia màu nền ca Sáng (trắng) và chiều (xám nhạt) từ cột index 2 trở đi
                        ("BACKGROUND", (2, 1), (-1, 5), colors.white),
                        (
                            "BACKGROUND",
                            (2, 6),
                            (-1, 10),
                            colors.HexColor("#F2F4F4"),
                        ),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#1E8449")),
                    ]
                )
            )

            elements.append(t)
            elements.append(Spacer(1, 1))

            # Hiển thị tổng số tiết tính toán bằng Pandas xuống cuối bảng
            elements.append(
                Paragraph(
                    f"Tổng số tiết dạy trong tuần là: {tong_so_tiet} tiết",
                    style_footer,
                )
            )

            # Thuật toán phân trang: Đủ 4 giáo viên ngắt trang một lần
            if (idx + 1) % 4 == 0:
                if idx < len(tkb_dict) - 1:
                    elements.append(PageBreak())
            else:
                # Khoảng cách trống tương đương 3 dòng chữ giữa các TKB
                elements.append(Spacer(1, 80))

        # Tiến hành biên dịch dữ liệu xuất thành file PDF hoàn chỉnh
        doc.build(elements)
        return filename

    def xuat_pdf_don_le(ten_gv, df_gv, filename="tkb_don_le.pdf"):
        styles = getSampleStyleSheet()
        style_school = ParagraphStyle(
            "SchSingle",
            fontName=f_normal,
            fontSize=9,
            leading=11,
            alignment=0,
            textColor=colors.HexColor("#7F8C8D"),
        )
        style_title = ParagraphStyle(
            "TtlSingle",
            fontName=f_bold,
            fontSize=12,
            leading=15,
            alignment=1,
            textColor=colors.HexColor("#2C3E50"),
        )
        style_header = ParagraphStyle(
            "HdrSingle",
            fontName=f_bold,
            fontSize=9,
            leading=12,
            alignment=1,
            textColor=colors.whitesmoke,
        )
        style_cell = ParagraphStyle(
            "ClSingle",
            fontName=f_normal,
            fontSize=9,
            leading=12,
            alignment=1,
            textColor=colors.black,
        )
        style_footer = ParagraphStyle(
            "FtrSingle",
            fontName=f_bold,
            fontSize=10,
            leading=13,
            alignment=2,
            textColor=colors.HexColor("#2C3E50"),
        )

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=30,
            bottomMargin=30,
        )
        elements = []
        #col_widths = + * 6
        col_widths = [75, 50] + [68] * 6

        # Tính tổng số tiết
        df_chi_co_mon = df_gv.iloc[:, 1:]
        tong_so_tiet = (
            df_chi_co_mon.map(
                lambda x: str(x).strip().lower() not in ["", "nan", "nghi"]
            )
            .sum()
            .sum()
        )

        elements.append(Paragraph("TRƯỜNG THPT NGUYEN THI XXXXXX", style_school))
        elements.append(
            Paragraph(
                f"<b>THỜI KHÓA BIỂU GIÁO VIÊN: {ten_gv.upper()}</b>", style_title
            )
        )
        elements.append(Spacer(1, 15))

        table_data = []
        header_row = [
            Paragraph("Giờ học", style_header),
            Paragraph("Tiết / Thứ", style_header),
        ] + [
            Paragraph(str(col).replace("Thu", "Thứ"), style_header)
            for col in df_gv.columns[1:]
        ]
        table_data.append(header_row)

        for i, row in df_gv.iterrows():
            row_data = [
                Paragraph(gio_hoc[i], style_cell),
                Paragraph(f"Tiết {row['Tiết']}", style_cell),
            ]
            for cell_value in row[1:]:
                row_data.append(Paragraph(str(cell_value), style_cell))
            table_data.append(row_data)

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E8449")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),  # Tăng padding cho rộng rãi
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND", (0, 1), (1, -1), colors.HexColor("#EAFAF1")),
                    ("BACKGROUND", (2, 1), (-1, 5), colors.white),
                    ("BACKGROUND", (2, 6), (-1, 10), colors.HexColor("#F2F4F4")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#1E8449")),
                ]
            )
        )

        elements.append(t)
        elements.append(Spacer(1, 10))
        elements.append(
            Paragraph(
                f"Tổng số tiết dạy trong tuần là: {tong_so_tiet} tiết", style_footer
            )
        )

        doc.build(elements)
        return filename


    def hien_thi_pdf_tren_web(file_path, height=600):
        """Hàm nhúng PDF vào giao diện Streamlit bằng iframe"""
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    #########################################################
    st.set_page_config(page_title="🖨️ IN TKB", layout="wide")
    #Tạo 3 Tab riêng biệt trên giao diện để tránh bị rối
    tab1, tab2, tab3 = st.tabs(["🧍 In Tkb riêng từng GV", "📦 In TKB mọi GV", "🔍 In Tkb chỉ các Gv có thay đổi"])

    #--- TAB 1: XEM RIÊNG TỪNG GIÁO VIÊN ---
    with tab1:
        st.subheader("Chọn GV để in")
        # Tạo Selectbox lấy danh sách key từ dict tkb_giao_vien của bạn
        gv_duoc_chon = st.selectbox("Chọn tên Giáo viên từ danh sách dưới đây:", options=sorted(list(tkb_giao_vien.keys())))
        if gv_duoc_chon:
            # Lấy DataFrame TKB của giáo viên được chọn từ dict của bạn
            df_gv_chon = tkb_giao_vien[gv_duoc_chon]
            # Tiến hành xuất file PDF đơn lẻ tạm thời
            file_don_le = xuat_pdf_don_le(gv_duoc_chon, df_gv_chon)
            # Tạo nút tải về riêng cho GV này
            with open(file_don_le, "rb") as f:
                st.download_button(label=f"📥 Tải file PDF của GV {gv_duoc_chon}",
                    data=f,
                    file_name=f"TKB_GV_{gv_duoc_chon.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key="btn_single",)
            # Hiển thị trực tiếp file PDF đơn lẻ lên web
            hien_thi_pdf_tren_web(file_don_le, height=500)

    #--- TAB 2: XUẤT FILE TỔNG HỢP IN ẤN HÀNG LOẠT ---
    with tab2:
        #st.subheader("Đóng gói tất cả thời khóa biểu vào 1 file PDF duy nhất")
        #st.write("Bố cục được tối ưu tự động: xếp chồng 4 bảng/trang A4.")
        if st.button("🚀 Bắt đầu tạo file PDF tổng hợp", key="btn_all"):
            with st.spinner("Hệ thống đang gộp dữ liệu và kết xuất file..."):
                pdf_file_tong = xuat_pdf_tong_hop(tkb_giao_vien)
                st.success("🎉 Đã tạo thành công file PDF chung!")
            with open(pdf_file_tong, "rb") as f:
                st.download_button(label="📥 Tải file PDF tổng hợp (Tất cả GV)",
                    data=f,
                    file_name="TKB_Tong_Hop_Giao_Vien.pdf",
                    mime="application/pdf",
                    key="btn_download_all",)
            # Hiển thị bản xem trước file tổng dài nhiều trang
            hien_thi_pdf_tren_web(pdf_file_tong, height=800)

    #--- TAB 3: XEM RIÊNG TỪNG GIÁO VIÊN ---
    with tab3:
        st.write("Chưa viết mã!")

    if st.button("Đóng"):
        st.session_state.active_dialog = None
        st.rerun()
    

# --- Main ----------------------------------------------------------------
if __name__ == "__main__":
    try:
        df_tkbc = pd.read_excel("Tkb_luu_last/tkb_chung.xlsx")
        df_tkbc.iloc[:, 2:] = df_tkbc.iloc[:, 2:].fillna("").astype(str)

        st.session_state.dftkbc = df_tkbc

        # 1. Đặt nút Toggle ở ngoài hàm, trước khi gọi bảng hiển thị
        swap_mode = st.toggle("🔄 ***:red[Tắt/Bật Hoán vị]***", value=False)

        #if swap_mode:
        #    st.info("Chế độ hoán vị đang BẬT: Hãy click chọn 2 ô để đổi chỗ.")
        #else:
        #    st.caption("Chế độ hoán vị đang TẮT: Bạn có thể lướt xem bảng thoải mái.")

        # 3. Gọi hàm hiển thị
        if "dftkbc" in st.session_state:
            show_tkb_chung(st.session_state.dftkbc, swap_enabled=swap_mode)

     
        #st.write("---")

        # tao 2 col1 o sidebar, col2 o trang chinh
        col1_tc, col2_tc, col3_tc = st.columns(3)

        ### 1. Khởi tạo session state #
        #-------------------------------------------
        if "active_dialog" not in st.session_state:
            st.session_state.active_dialog = None


        # Callback xử lý khi người dùng chọn GV
        def on_lop_change_trt():
            if st.session_state.select_lop_trt is not None:
                st.session_state.active_dialog = "lop_trt"

        def on_gv_change_trt():
            if st.session_state.select_gv_trt is not None:
                st.session_state.active_dialog = "gv_trt"



        def on_gv_change_tkb():
            if st.session_state.select_gv_tkb is not None:
                st.session_state.active_dialog = "gv_tkb"


        with col1_tc:
            list_cac_lop = [col for col in df_tkbc.columns[2:] if col not in ['index', 'Unnamed: 0', '::auto_unique_id::', ':auto_unique_id:']]
            st.selectbox(
                "✏️ ***:green[CHỈNH TRÁNH TIẾT CỦA LỚP]***", 
                options=list_cac_lop,
                index=None,
                placeholder="Chọn Lớp để chỉnh", 
                key="select_lop_trt", 
                on_change=on_lop_change_trt
            )


        with col2_tc:
            gv_list = rut_list_gv(df_tkbc)
            st.selectbox(
                "✏️ ***:blue[CHỈNH TRÁNH TIẾT CỦA GV]***", 
                options=gv_list,
                index=None,
                placeholder="Chọn GV để chỉnh", 
                key="select_gv_trt", 
                on_change=on_gv_change_trt
            )


        with col3_tc:
            gv_list = rut_list_gv(df_tkbc)
            st.selectbox(
                "👀 :red[XEM TKB GIÁO VIÊN]", 
                options=gv_list,
                index=None,
                placeholder="Chọn GV để xem", 
                key="select_gv_tkb", 
                on_change=on_gv_change_tkb
            )


        # Trong sidebar-----------------------
        
        st.sidebar.header('⚙️ Thời Khóa Biểu')

        if st.sidebar.button('🚀 Tổng Quát', type="primary", use_container_width=True, key="tong_quat"):
            st.session_state.active_dialog = "tong_quat"
            #tong_quat(st.session_state.dftkbc)
            # moi gan gia tri, cho dialog tong_quat thuc thi

        if st.sidebar.button('✔️ Kiểm tra File Excel', type="primary", use_container_width=True, key="kiemtra_excel"):
            st.session_state.active_dialog = "kiemtra_excel"

        if st.sidebar.button('✏️ Xem/Chỉnh Info', type="primary", use_container_width=True, key="xem_chinh_info"):
            st.session_state.active_dialog = "xem_chinh_info"

        if st.sidebar.button('⚙️ Chạy Trình Xếp TKB', type="primary", use_container_width=True, key="chay_trinh_xeptkb"):
            st.session_state.active_dialog = "chay_trinh_xeptkb"

        if st.sidebar.button('🖨️ In TKB Giáo viên', type="primary", use_container_width=True, key="in_tkb_gv"):
            st.session_state.active_dialog = "in_tkb_gv"

        if st.sidebar.button('🖨️ In TKB Lóp', type="primary", use_container_width=True, key="in_tkb_lop"):
            st.session_state.active_dialog = "in_tkb_lop"

        if st.sidebar.button('🖨️ In TKB TRƯỜNG', type="primary", use_container_width=True, key="in_tkb_truong"):
            st.session_state.active_dialog = "in_tkb_truong"

        if st.sidebar.button('💾 Save TKB to Excel and Download', type="primary", use_container_width=True, key="save_excel_download"):
            st.session_state.active_dialog = "save_excel_download"
    


        ### Điều hướng hiển thị DUY NHẤT 1 dialog ở cuối script de khong gay LOI
        #-----------------------------------------------------------------------

        if st.session_state.active_dialog == "lop_trt" and st.session_state.select_lop_trt is not None:
            #st.write(st.session_state.select_lop_trt)
            dialog_lop_trt(st.session_state.select_lop_trt)

        elif st.session_state.active_dialog == "gv_trt" and st.session_state.select_gv_trt is not None:
            #st.write(st.session_state.select_gv_trt)
            dialog_gv_trt(st.session_state.select_gv_trt) ### st.session_state.select_gv_trt la tengv da hon, select_gv_trt la key

        elif st.session_state.active_dialog == "gv_tkb" and st.session_state.select_gv_tkb is not None:
            #st.write(st.session_state.select_gv_tkb)
            ten_gv = st.session_state.select_gv_tkb
            df_tkb_gv = rut_df_tkb_gv(df_tkbc, ten_gv)
            dialog_gv_tkb(df_tkb_gv, ten_gv)    


        elif st.session_state.active_dialog == "tong_quat":
            tong_quat(st.session_state.dftkbc)

        elif st.session_state.active_dialog == "kiemtra_excel":
            kiemtra_excel()

        elif st.session_state.active_dialog == "xem_chinh_info":
            xem_chinh_info()

        elif st.session_state.active_dialog == "in_tkb_gv":
            in_tkb_gv(st.session_state.dftkbc)

        elif st.session_state.active_dialog == "in_tkb_lop":
            in_tkb_lop(st.session_state.dftkbc)

        elif st.session_state.active_dialog == "in_tkb_truong":
            in_tkb_truong(st.session_state.dftkbc)

        elif st.session_state.active_dialog == "save_excel_download":
            save_excel_download(st.session_state.dftkbc)

        elif st.session_state.active_dialog == "chay_trinh_xeptkb":
            chay_trinh_xeptkb(st.session_state.dftkbc)


    except FileNotFoundError: # neu chua co file ễcl thi yc upload file len
        uploaded_file = st.sidebar.file_uploader("📂 Chọn file Excel (.xlsx)", type=["xlsx"])
        if uploaded_file is not None:
            pass


#Cho ví dụ mã python 1 app có :
#2 dialog được gọi bởi 2 nút đặt ở sidebar
#2 dialog được gọi bởi 2 nút đặt ở main
#để làm rõ cách hoạt động vào mỗi thời điểm chỉ có có 1 dialog hoạt động.

