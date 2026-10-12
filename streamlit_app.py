import json
import pandas as pd
import streamlit as st
#from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_aggrid import AgGrid
import io, os, re, zipfile
from xhtml2pdf import pisa


from utils.grid_helper import ham_lay_gob
from utils.scheduler import chay_trinh_xeptkb
from utils.dial_logs import resetrangbuoc

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

def rut_df_tkb_lop(df1, lopx):
    # lay index cua cot co ten lopx cua df1
    index_cua_cotlopx = df1.columns.get_loc(lopx)
    # tao dflopx la cac cot cs 0,1 va index_cua_cotlopx cua df1
    dflopx = df1.iloc[:, [0,1,index_cua_cotlopx]]
    df2 = dflopx.pivot(index="Tiết", columns="Thứ", values=lopx)
    # 3. Đổi tên các cột từ [2, 3] thành ['Thứ 2', 'Thứ 3']
    df2.columns = [f"Thứ {col}" for col in df2.columns]
    # 4. Đưa 'Tiết' từ chỉ mục (index) trở lại thành một cột bình thường
    df2 = df2.reset_index()
    return df2 

# cac ham dialog
@st.dialog("📊", width="normal")
def dialog_gv_tkb(df, gv_name):
    #st.write(f"của giáo viên: **{gv_name}**")
    # Đưa chỉ số index (1-10) thành 1 cột và đặt tên cột cũ đó là "Tiết"
    df = df.reset_index().rename(columns={'index': 'Tiết'})

    # 2. Tạo Styled DataFrame (Ẩn index, tô màu cột 1, vạch đôi dòng 5)
    styled_df = df.style.hide().set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-size', '12px'), ('border', '2px solid #555555'), ('padding', '4px')]},
        {'selector': 'td', 'props': [('border', '1px solid #555555'),('font-size', '12px'), ('padding', '4px')]},
        {'selector': 'td:first-child', 'props': [('background-color', '#E8F5E9'), ('font-weight', 'bold'), ('color', '#2E7D32')]},
        {'selector': 'tr:nth-child(5) td', 'props': [('border-bottom', '2px double #555555 !important')]}
    ])

    # Chuyển thành chuỗi HTML
    html_table = styled_df.to_html()
    tieude_pdf = f"TKB của Gv. {gv_name}"
    html_table = f"<h3>{tieude_pdf}</h3>" + html_table
    # 3. Chuẩn bị cấu trúc HTML đầy đủ kèm Font chữ cho PDF
    font_path = os.path.join("fonts", "NotoSans-Regular.ttf").replace('\\', '/')

    html_content = f"""
    
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <style>
        @font-face {{ font-family: 'LocalFont'; src: url('{font_path}'); }}
        body, table, th, td {{ font-family: 'LocalFont'; }}
        table {{ width: 100%;}}
    </style>
    </head>
    <body>
    <div>
        {html_table}
    """
    # do trong html_table da co cac </div> , </body>, </html?
    st.markdown(html_content, unsafe_allow_html=True)

    #st.divider()

    # Hàm này CHỈ CHẠY khi người dùng bấm nút Download
    def generate_pdf_callback():
        pdf_buffer = io.BytesIO()  # Tạo file ảo trong bộ nhớ RAM
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        if not pisa_status.err:
            pdf_buffer.seek(0)  # Đưa con trỏ file về đầu để đọc dữ liệu
            return pdf_buffer
        return None

    # Nút bấm thông minh: Nó nhận vào một hàm (data=generate_pdf_callback) 
    # và sẽ không thực thi hàm đó cho tới khi có người click chuột!
    st.download_button(
        label="📥 Tải file PDF về máy",
        data=generate_pdf_callback(),
        file_name=f"tkb_{gv_name}.pdf",
        mime="application/pdf"
    )
    if st.button("Đóng"):
        # Reset active_dialog và đưa selectbox về trạng thái chưa chọn (None)
        st.session_state.active_dialog = None
        st.session_state.select_gv_tkb = None
        st.rerun()

@st.dialog("Xem/Chỉnh yêu cầu tránh tiết của Gv", width="medium")
def dialog_gv_trt(ten_gv, yc_hien_tai=None):
    st.write(ten_gv)
    EXCEL_FILE = "info_school/gv_yc_tranh.xlsx"
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

    def gv_input_dialog(ten_gv, yc_hien_tai=None):
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
@st.dialog("📊", width="normal")
def dialog_lop_tkb(df, ten_lop):
    # 2. Tạo Styled DataFrame (Ẩn index, tô màu cột 1, vạch đôi dòng 5)
    styled_df = df.style.hide().set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-size', '12px'), ('border', '2px solid #555555'), ('padding', '4px')]},
        {'selector': 'td', 'props': [('border', '1px solid #555555'),('font-size', '12px'), ('padding', '4px')]},
        {'selector': 'td:first-child', 'props': [('background-color', '#E8F5E9'), ('font-weight', 'bold'), ('color', '#2E7D32')]},
        {'selector': 'tr:nth-child(5) td', 'props': [('border-bottom', '2px double #555555 !important')]}
    ])

    # Chuyển thành chuỗi HTML
    html_table = styled_df.to_html()
    tieude_pdf = f"TKB của Lớp: {ten_lop}"
    html_table = f"<h3>{tieude_pdf}</h3>" + html_table

    # 3. Chuẩn bị cấu trúc HTML đầy đủ kèm Font chữ cho PDF
    font_path = os.path.join("fonts", "NotoSans-Regular.ttf").replace('\\', '/')

    html_content = f"""
    
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <style>
        @font-face {{ font-family: 'LocalFont'; src: url('{font_path}'); }}
        body, table, th, td {{ font-family: 'LocalFont'; }}
        table {{ width: 100%;}}
    </style>
    </head>
    <body>
    <div>
        {html_table}
    """
    # do trong html_table da co cac </div> , </body>, </html?
    st.markdown(html_content, unsafe_allow_html=True)

    #st.divider()

    # Hàm này CHỈ CHẠY khi người dùng bấm nút Download
    def generate_pdf_callback():
        pdf_buffer = io.BytesIO()  # Tạo file ảo trong bộ nhớ RAM
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        if not pisa_status.err:
            pdf_buffer.seek(0)  # Đưa con trỏ file về đầu để đọc dữ liệu
            return pdf_buffer
        return None

    # Nút bấm thông minh: Nó nhận vào một hàm (data=generate_pdf_callback) 
    # và sẽ không thực thi hàm đó cho tới khi có người click chuột!
    st.download_button(
        label="📥 Tải file PDF về máy",
        data=generate_pdf_callback(),
        file_name=f"tkb_{ten_lop}.pdf",
        mime="application/pdf"
    )
    if st.button("Đóng"):
        # Reset active_dialog và đưa selectbox về trạng thái chưa chọn (None)
        st.session_state.active_dialog = None
        st.session_state.select_lop_tkb = None
        st.rerun()

#-----------------------------------
def rut_list_gv(df):
    classes = list(df.columns[2:])
    available_slots = []
    set_gv = set()
    for idx, row in df.iterrows():
        thu = int(row["Thứ"])
        tiet = int(row["Tiết"])
        for c in classes:
            val = row[c]
            if pd.notna(val) and val != "" and "_" in val: 
                available_slots.append((thu, tiet, c))
                gv = val.split("_")[0]
                set_gv.add(gv)
    list_gv = list(set_gv)
    return sorted(list_gv)

#################################### SET DAU TRANG #####################################
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 4rem; /* Thay đổi số rem này nhỏ hơn (ví dụ 1rem hoặc 2rem) */
        }
    </style>
""", unsafe_allow_html=True)
TEN_TRUONG="Trường Học với tiensg89@"
#########################################################################################

# Cấu hình giao diện trang web (phải đặt ở dòng đầu tiên của Streamlit)
st.set_page_config(page_title="Quản Lý & Xếp TKB",layout="wide",initial_sidebar_state="expanded",)
st.subheader(f"⚙️ ***Xếp & QL TKB Trường học với tiensg89@***")
time_select = st.select_slider(".", options=[30, 60, 120, 180, 240, 300, 360, 420, 480,540, 600,900,1800],label_visibility="hidden")
thongbao = st.empty()
#thongbao.write("---")
# ==========================================
# 1. KHỞI TẠO SESSION STATE BAN ĐẦU
# ==========================================

if "current_df" not in st.session_state:
    st.session_state.current_df = None

if "cam_xep_keys" not in st.session_state:
    st.session_state.cam_xep_keys = []  # Danh sách ô cấm xếp (nếu có)

if "swap_mode" not in st.session_state:
    st.session_state.swap_mode = False

if "swap_mode2" not in st.session_state:
    st.session_state.swap_mode2 = False

if "active_dialog" not in st.session_state:
    st.session_state.active_dialog = None


# ==========================================
# 2. HÀM CALLBACK LOẠI TRỪ LẪN NHAU CHO 2 TOGGLE
# ==========================================
def on_change_swap_mode():
    if st.session_state.swap_mode:
        st.session_state.swap_mode2 = False  # Bật hoán vị thì tắt xem TKB


def on_change_swap_mode2():
    if st.session_state.swap_mode2:
        st.session_state.swap_mode = False  # Bật xem TKB thì tắt hoán vị

@st.dialog("Thông Báo:", width="normal")
def hien_thi_tb(lkq):
    st.success(f'Đã xếp TKB với tỉ lệ hoàn thành: {lkq[3]:.1f} %')
    st.write(f":blue[Số tiết đã xếp được: {lkq[1]} / {lkq[0]}]")
    st.write(f":red[Số tiết chưa xếp được là : {lkq[2]} / {lkq[0]}]")

    if st.button("Đóng và cập nhật lưới"):
        st.session_state.active_dialog = None
        st.rerun()

# ==========================================
# 3. SIDEBAR: CHỌN VÀ NẠP DỮ LIỆU EXCEL
# ==========================================

st.sidebar.header("📁 Cấu hình Dữ liệu")

danh_sach_file = {
    "TKB hiện hành": "tkb_dang_dung/tkb_chung.xlsx",
    "TKB để xếp": "tkb_xlsx_for_xep/tkb_dang_xep.xlsx",
    "Tải lên tệp excel khác": None,
}

# Đã gán key="select_file_excel" để tránh trùng lặp
chon_file = st.sidebar.selectbox(
    ":red[Chọn nguồn dữ liệu TKB:]",
    options=list(danh_sach_file.keys()),
    key="select_file_excel",
)
if danh_sach_file[chon_file]==None:
    uploaded_file = st.sidebar.file_uploader("📂 Chọn file Excel (.xlsx) dạng TKB", type=["xlsx"])
    if uploaded_file:
        file_path = uploaded_file
    else: # neu chua upload
        file_path = None    
else:   #neu khac None
    file_path = danh_sach_file[chon_file]   # None

thongbaodl = st.sidebar.empty()

# Đã gán key="btn_load_excel" để tránh trùng lặp
if st.sidebar.button("📥 Nạp dữ liệu Excel", key="btn_load_excel") and not (file_path==None):
    try:
        if file_path:
            df_loaded = pd.read_excel(file_path)
            df_loaded = df_loaded.rename(columns=lambda c: str(c).strip()) 
            df_loaded.iloc[:, 2:] = df_loaded.iloc[:, 2:].fillna("").astype(str)
            st.session_state.current_df = df_loaded
            thongbaodl.success(f"Đã nạp thành công dữ liệu từ **{chon_file}**!")
            
    except Exception:
        thongbaodl.warning(
            f"Không tìm thấy file '{file_path}' trên ổ đĩa. Đang tạo dữ liệu mẫu để minh họa."
        )
        # Dữ liệu mẫu test giao diện
        data_mau = {
            "Thứ": [2, 2, 2, 3, 3, 3],
            "Tiết": [1, 2, 3, 1, 2, 3],
            "6A1": ["GV1_Toán", "", "GV2_Lý", "", "GV3_Hóa", ""],
            "6A2": ["", "GV4_Văn", "", "GV1_Toán", "", "GV5_Anh"],
        }
        df_loaded = pd.DataFrame(data_mau)
        df_loaded = df_loaded.rename(columns=lambda c: str(c).strip()) 
        df_loaded.iloc[:, 2:] = df_loaded.iloc[:, 2:].fillna("").astype(str)
        st.session_state.current_df = df_loaded

    # tao cam_xep ngay luc dau
    cam_xep_keys = []
    ds_lop = [col for col in df_loaded.columns if col not in ["Thứ", "Tiết"]]
    for _, row in df_loaded.iterrows():
        thu = row["Thứ"]
        tiet = row["Tiết"]
        for lop in ds_lop:
            val = row[lop]
            # Nếu ô trống/null ngay từ file Excel gốc
            if pd.isna(val) or str(val).strip() == "":
                cam_xep_keys.append(f"{thu}_{tiet}_{lop}")
    # Truyền danh sách này vào hàm JS dưới dạng mảng JSON
    #cam_xep_json = json.dumps(cam_xep_keys)
    st.session_state.cam_xep_keys = json.dumps(cam_xep_keys)

# Kiểm tra nếu chưa nạp dữ liệu
if st.session_state.current_df is None:
    thongbao.info("👈 Vui lòng chọn file Excel ở Sidebar và bấm 'Nạp dữ liệu Excel' để bắt đầu.")
    st.stop()

# ==========================================
# 4. GIAO DIỆN CHÍNH & ĐIỀU KHIỂN XẾP LỊCH
# ==========================================
col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 2, 3, 3])

with col_ctrl1:
    # Đã gán key="toggle_swap_mode"
    swap_mode = st.toggle(
        "🔄 ***:red[Tắt/Bật Hoán vị]***",
        key="swap_mode",
        on_change=on_change_swap_mode,
    )

with col_ctrl2:
    # Đã gán key="toggle_view_mode"
    swap_mode2 = st.toggle(
        "🔄 ***:yellow[Tắt/Bật Xem TKB GV]***",
        key="swap_mode2",
        on_change=on_change_swap_mode2,
    )

with col_ctrl3:
    # Đã gán key="btn_run_algorithm" để tránh trùng lặp
    if st.button("🚀 **Xếp TKB với thời gian chọn**", use_container_width=True, key="btn_run_algorithm"):
        with st.spinner(f":red[Max {time_select} giây :]",  show_time=True):
            # ==========================================
            # 📌 GỌI HÀM XẾP TKB CỦA BẠN TẠI ĐÂY
            df_tkb_new, df_chua_xep, kq = chay_trinh_xeptkb(st.session_state.current_df.copy(), time_select)
            st.balloons()
            #st.write(df_chua_xep)
            # ==========================================
            
            # Cập nhật dữ liệu mới vào session
            st.session_state.current_df = df_tkb_new
            st.session_state.chuaxep_df = df_chua_xep

        #st.rerun()
        st.session_state.active_dialog = "hien_thi_tb"
        hien_thi_tb(kq)

with col_ctrl4:
    # Đã gán key="btn_run_algorithm" để tránh trùng lặp
    if st.button(f"🧩 :blue[Đưa chưa xếp vào đã xếp]", use_container_width=True, key="gop_dfdx_dfcx"):
        def gop_tkb(df_da_xep, df_chua_xep, cam_xep_keys):
            # Duyệt qua tất cả các cột lớp học
            for col in [c for c in df_da_xep.columns if c not in ["Thứ", "Tiết"]]:
                # Lấy các giá trị hợp lệ từ data_2 giống như trước
                available_values = [val for val in df_chua_xep[col] if val != ""]

                if available_values:    #len(available_values)>0
                    # TÌM CÁC Ô TRỐNG NHƯNG PHẢI ĐỦ ĐIỀU KIỆN (KHÔNG NẰM TRONG DANH SÁCH CẤM)
                    empty_indices = []
                    for idx in df_da_xep[df_da_xep[col] == ""].index:
                        thu = df_da_xep.loc[idx, "Thứ"]
                        tiet = df_da_xep.loc[idx, "Tiết"]

                        # Tạo khóa theo định dạng "Thứ_Tiết_Lớp" (Ví dụ: "2_2_6A1")
                        check_key = f"{thu}_{tiet}_{col}"

                        # Nếu khóa này KHÔNG nằm trong danh sách cấm, ta mới thêm vào để xếp lịch
                        if check_key not in cam_xep_keys:
                            empty_indices.append(idx)

                    # Điền tuần tự dữ liệu vào các ô trống hợp lệ đã lọc được
                    for idx, new_val in zip(empty_indices, available_values):
                        df_da_xep.loc[idx, col] = new_val

            return df_da_xep

        df_ket_qua_tong = gop_tkb(st.session_state.current_df, 
                                  st.session_state.chuaxep_df, 
                                  st.session_state.cam_xep_keys)

        
        st.session_state.current_df = df_ket_qua_tong
        
        @st.dialog("Thông Báo:", width="normal")
        def hthi_tb_duavao():
            st.success("✅ Đã đưa các tiết chưa xếp được vào TKB đã xếp để sau đó chỉnh bằng tay.")
        hthi_tb_duavao()

# ==========================================
# 5. CẤU HÌNH AGGRID & HÀM HIỂN THỊ LƯỚI
# ==========================================
# thuc thi ham_lay_gob dat tai utils de no tra ve gob.build() gan vao cho grid_options
grid_options, custom_css = ham_lay_gob(st.session_state.current_df, st.session_state.swap_mode, st.session_state.swap_mode2, st.session_state.cam_xep_keys)

grid_response = AgGrid(
    st.session_state.current_df,
    gridOptions=grid_options,
    custom_css=custom_css,
    allow_unsafe_jscode=True,
    #height=520,
    key="aggrid_tkb_main_instance",  # Khóa định danh độc lập cho AgGrid
    #update_on="GridUpdateMode.MODEL_CHANGED"
    update_on=['cellValueChanged', 'modelChanged']
)

st.session_state.current_df = grid_response["data"]

#st.write('---')
# 3 menu
col1_tc, col2_tc, col3_tc = st.columns([3, 3, 3])

# kich hoat
if st.session_state.active_dialog == "gv_tkb" and st.session_state.select_gv_tkb is not None:
    #st.write(st.session_state.select_gv_tkb)
    ten_gv = st.session_state.select_gv_tkb
    df_tkb_gv = rut_df_tkb_gv(st.session_state.current_df, ten_gv)
    dialog_gv_tkb(df_tkb_gv, ten_gv)    

elif st.session_state.active_dialog == "gv_trt" and st.session_state.select_gv_trt is not None:
    #st.write(st.session_state.select_gv_trt)
    dialog_gv_trt(st.session_state.select_gv_trt) ### st.session_state.select_gv_trt la tengv da hon, select_gv_trt la key

elif st.session_state.active_dialog == "lop_tkb" and st.session_state.select_lop_tkb is not None:
    #st.write(st.session_state.select_lop_tkb)
    ten_lop = st.session_state.select_lop_tkb
    df_tkb_lop = rut_df_tkb_lop(st.session_state.current_df, ten_lop)
    dialog_lop_tkb(df_tkb_lop, ten_lop)


with col1_tc:
    def on_gv_change_tkb():
        if st.session_state.select_gv_tkb is not None:
            st.session_state.active_dialog = "gv_tkb"
    gv_list = rut_list_gv(st.session_state.current_df)
    st.selectbox(
        "👀 :blue[Xem TKB GV:]", 
        options=gv_list,
        index=None,
        placeholder="Chọn GV", 
        key="select_gv_tkb", 
        on_change=on_gv_change_tkb
    )

with col2_tc:
    def on_gv_change_trt():
        if st.session_state.select_gv_trt is not None:
            st.session_state.active_dialog = "gv_trt"
    gv_list = rut_list_gv(st.session_state.current_df)
    st.selectbox(
        "✏️ ***:green[Yc tránh của gv:]***", 
        options=gv_list,
        index=None,
        placeholder="Chọn gv để chỉnh", 
        key="select_gv_trt", 
        on_change=on_gv_change_trt
    )

with col3_tc:
    def on_lop_change_tkb():
        if st.session_state.select_lop_tkb is not None:
            st.session_state.active_dialog = "lop_tkb"
    list_cac_lop = [col for col in st.session_state.current_df.columns[2:] if col not in ['index', 'Unnamed: 0', '::auto_unique_id::', ':auto_unique_id:']]
    st.selectbox(
        "👀 ***:red[Xem TKB của lớp:]***", 
        options=list_cac_lop,
        index=None,
        placeholder="Chọn lớp để xem", 
        key="select_lop_tkb", 
        on_change=on_lop_change_tkb
    )

###########################################
st.sidebar.header("👇 Bổ sung điều chỉnh:")


if st.sidebar.button("Định lại ràng buộc xếp", type="primary", use_container_width=True, key="set_rb_xep"):
    resetrangbuoc()

if st.sidebar.button("Bổ sung thông tin", type="primary",use_container_width=True, key="bo_sung_tt"):
    thongbao.write('Bổ sung thông tin')

if st.sidebar.button("Save/Download", type="primary", use_container_width=True, key="save_download"):
    thongbao.write('Save')

#st.sidebar.header("🖨️ Xuất file PDF:")
ldanhmuc = {
    "TKB của các Giáo Viên" : "fintkb_gvs",
    "TKB của các Lớp" : "fintkb_lops",
    "TKB toàn Trường" : "fintkb_truong",
    "TKB của các Giáo Viên có thay đổi so vói tkb trước" : "fintkbtd_gvs",
    "TKB của các Lớp có thay đổi so vói tkb trước" : "fintkbtd_lops",
    "Bảng phân công giảng dạy": "bang_pcgd",
    "Mã tên giáo viên": "ma_tengv",
    "Tờ ghi yêu cầu xếp tránh tiết ": "yc_tranht"
}

chon_in = st.sidebar.selectbox(
    ":red[🖨️ **Xuất file PDF**]",
    options=list(ldanhmuc.keys()),
    index=None,
    placeholder="Chọn:",
    #label_visibility="hidden",
    key="chon_in"
)
if chon_in :
    st.sidebar.write(chon_in)

###########################################
