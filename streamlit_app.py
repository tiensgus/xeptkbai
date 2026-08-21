import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

import os
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

#################################### SET DAU TRANG #####################################
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem; /* Thay đổi số rem này nhỏ hơn (ví dụ 1rem hoặc 2rem) */
        }
    </style>
""", unsafe_allow_html=True)

st.subheader("TKB THPT APC")
##########################################################################################

@st.dialog("In Tkb Gv ", width="large")
def  in_tkb_gv(dfc):
    df = dfc

    # 2. Chuyển bảng từ dạng rộng sang dọc
    df_long = df.melt(id_vars=['Thu', 'Tiet'], var_name='Lop', value_name='GiaoVien_Goc')

    # Lọc bỏ dòng trống
    df_long = df_long.dropna(subset=['GiaoVien_Goc'])

    # 3a. Tách lấy tên GV đứng trước dấu "_" và loại bỏ khoảng trắng dư thừa
    df_long['GiaoVien'] = df_long['GiaoVien_Goc'].str.split('_').str[0].str.strip()
    # 3b. Tách lấy tên mon đứng sâu dấu "_" và loại bỏ khoảng trắng dư thừa
    #df_long['Mon'] = df_long['GiaoVien_Goc'].str.split('_').str[1].str.strip()

    #print(df_long['GiaoVien'])

    #print(df_long['Mon'])
    khung_thu = [f"Thu {i}" for i in range(2, 8)]

    # 4. Tạo thời khóa biểu cho từng giáo viên
    danh_sach_gv = df_long['GiaoVien'].unique()

    tkb_giao_vien = {}

    for gv in danh_sach_gv:
        df_gv = df_long[df_long['GiaoVien'] == gv]
        # =========================================================================
        # MÃ XỬ LÝ CHÍNH: TẠO GIÁ TRỊ MỚI "12A3-NV" VÀ GÁN NGƯỢC LẠI VÀO CỘT LOP
        # =========================================================================
        # Bước 1: Lấy phần sau dấu "_" của cột Lop (ví dụ: 'Lop_12A3' -> '12A3')
        phan_duoi_lop = df_gv['Lop'].astype(str).str.split('_').str[1].str.strip()
        # Bước 2: Lấy phần sau dấu "_" của cột GiaoVien_Goc (ví dụ: 'Hương_NV' -> 'NV')
        phan_sau_gv = df_gv['GiaoVien_Goc'].astype(str).str.split('_').str[1].str.strip()
        # Bước 3: Nối hai phần lại với nhau bằng dấu "-" và ghi đè vào cột 'Lop'
        df_gv['Lop'] = phan_duoi_lop + '-' + phan_sau_gv

        # In kết quả kiểm tra bảng df_gv sau khi sửa
        #print(df_gv)
        # Dùng pivot_table và nối các lớp bằng dấu phẩy nếu GV dạy nhiều lớp cùng tiết
        pivot_gv = df_gv.pivot_table(
            index='Tiet', 
            columns='Thu', 
            values='Lop', 
            aggfunc=lambda x: ', '.join(x.unique())  # Dùng unique để tránh lặp lại tên lớp
        )
        
        # Định hình khung cố định: Tiết 1-10, Thứ 2-7
        pivot_gv = pivot_gv.reindex(index=range(1, 11), columns=range(2, 8)).fillna('')
        
        # Định dạng lại tiêu đề cột và chỉ mục
        pivot_gv.columns = [f'Thu {c}' for c in pivot_gv.columns]
        pivot_gv.index.name = 'Tiet'
        pivot_gv = pivot_gv.reset_index()
        
        tkb_giao_vien[gv] = pivot_gv
        #print(gv,tkb_giao_vien[gv])

    # ==============================================================================
    # PHẦN 2: VIẾT TIẾP MÃ XUẤT PDF CHUNG VÀ HIỂN THỊ LÊN STREAMLIT
    # ==============================================================================

    #st.set_page_config(page_title="Xuất TKB PDF", layout="wide")
    #st.title("🖨️ Hệ Thống Xuất Thời Khóa Biểu Giáo Viên Ra PDF")

    # Khai báo khung giờ học tương ứng từ Tiết 1 đến Tiết 10
    # ==============================================================================
    # PHẦN CẤU HÌNH CHUNG CHO CẢ 2 HÀM XUẤT PDF (Đã sửa lỗi khai báo biến)
    # ==============================================================================
    # Khung giờ mặc định dự phòng (nếu không đọc được file JSON)
    gio_hoc = [
        "08:00 - 09:45", "07:50 - 08:35", "08:50 - 09:35", "09:40 - 10:25", "10:30 - 11:15",
        "13:00 - 13:45", "13:50 - 14:35", "14:50 - 15:35", "15:40 - 16:25", "16:30 - 17:15"
    ]
    # Đường dẫn tới tệp cấu hình JSON trên server
    JSON_FILE_PATH = "info_school.json"
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

    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"

    # ĐỊNH NGHĨA RÕ RÀNG BIẾN TOÀN CỤC ĐỂ CÁC HÀM PHÍA DƯỚI ĐỀU ĐỌC ĐƯỢC
    f_normal = "Helvetica"
    f_bold = "Helvetica-Bold"

    if os.path.exists(font_path) and os.path.exists(font_bold_path):
        try:
            pdfmetrics.registerFont(TTFont('Arial', font_path))
            pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
            f_normal = "Arial"
            f_bold = "Arial-Bold"
        except Exception:
            pass



    def xuat_pdf_tong_hop(tkb_dict, filename="tkb_tat_ca_gv.pdf"):
        # 1. Khởi tạo Font chữ tiếng Việt Arial
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"

        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            pdfmetrics.registerFont(TTFont("Arial-Bold", font_bold_path))
            f_normal, f_bold = "Arial", "Arial-Bold"
        else:
            # Dự phòng nếu chạy trên Linux/Streamlit Cloud không có sẵn Arial
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
            ]
            table_data.append(header_row)

            # Đổ dữ liệu 10 hàng tương ứng với 10 tiết
            for i, row in df_gv.iterrows():
                tiet_label = f"Tiết {row['Tiet']}"

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
                Paragraph(f"Tiết {row['Tiet']}", style_cell),
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
        #st.subheader("Chọn GV để in")
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

@st.dialog("In Tkb Lớp", width="large")
def  in_tkb_lop(dfc):
    gio_hoc = [
        "09:00 - 07:45", "07:50 - 08:35", "08:50 - 09:35", "09:40 - 10:25", "10:30 - 11:15",
        "13:00 - 13:45", "13:50 - 14:35", "14:50 - 15:35", "15:40 - 16:25", "16:30 - 17:15"
    ]
    # Đường dẫn tới tệp cấu hình JSON trên server
    JSON_FILE_PATH = "info_school.json"
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

    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"

    f_normal = "Helvetica"
    f_bold = "Helvetica-Bold"

    if os.path.exists(font_path) and os.path.exists(font_bold_path):
        try:
            pdfmetrics.registerFont(TTFont('Arial', font_path))
            pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
            f_normal = "Arial"
            f_bold = "Arial-Bold"
        except Exception:
            pass


    # 2. Chuyển bảng từ dạng rộng sang dọc để tạo ra biến df_long
    df_long = dfc.melt(id_vars=['Thu', 'Tiet'], var_name='Lop', value_name='GiaoVien_Goc')

    # Lọc bỏ các dòng trống
    df_long = df_long.dropna(subset=['GiaoVien_Goc'])


    # ==============================================================================
    # TIẾP TỤC CÁC BƯỚC XỬ LÝ LỚP HỌC (ĐOẠN CODE TRƯỚC ĐÓ)
    # ==============================================================================
    # Bước 1: Làm sạch tên lớp hiển thị (Ví dụ: 'Lop_12A3' -> '12A3')
    df_long['Ten_Lop_Sạch'] = df_long['Lop'].astype(str).str.split('_').str[-1].str.strip()

    # Bước 2: Tạo nội dung hiển thị trong ô của học sinh (Tên môn + Tên GV)
    def tao_noi_dung_o_lop(row):
        parts_gv = str(row['GiaoVien_Goc']).split('_')
        ten_gv_short = parts_gv[0].strip()
        ten_mon = parts_gv[1].strip() if len(parts_gv) > 1 else ""
        return f"{ten_mon}\n({ten_gv_short})" if ten_mon else ten_gv_short

    df_long['Noi_Dung_O_Lop'] = df_long.apply(tao_noi_dung_o_lop, axis=1)

    # Bước 3: Duyệt qua danh sách lớp để tạo dict TKB 
    danh_sach_lop = sorted(df_long['Ten_Lop_Sạch'].unique())
    tkb_cac_lop = {}

    for lop in danh_sach_lop:
        df_lop = df_long[df_long['Ten_Lop_Sạch'] == lop]
        
        # Pivot dữ liệu theo Tiết và Thứ cho Lớp
        pivot_lop = df_lop.pivot_table(
            index='Tiet',
            columns='Thu',
            values='Noi_Dung_O_Lop',
            aggfunc=lambda x: ', '.join(x.unique())
        )
        
        # Định hình khung cố định: Tiết 1-10, Thứ 2-7
        pivot_lop = pivot_lop.reindex(index=range(1, 11), columns=range(2, 8)).fillna('')
        
        # Định dạng lại tiêu đề cột và chỉ mục
        pivot_lop.columns = [f'Thu {c}' for c in pivot_lop.columns]
        pivot_lop.index.name = 'Tiet'
        pivot_lop = pivot_lop.reset_index()
        
        tkb_cac_lop[lop] = pivot_lop

    # ==============================================================================
    # PHẦN 2: HÀM XUẤT PDF TKB LỚP ĐƠN LẺ VÀ LỚP TỔNG HỢP
    # ==============================================================================

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
            row_data = [Paragraph(gio_hoc[i], style_cell), Paragraph(f"Tiết {row['Tiet']}", style_cell)]
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
                row_data = [Paragraph(gio_hoc[i], style_cell), Paragraph(f"Tiết {row['Tiet']}", style_cell)]
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

    # ==============================================================================
    # PHẦN 3: GIAO DIỆN BỔ SUNG TRÊN STREAMLIT (NẰM DƯỚI PHẦN TKB GIÁO VIÊN CỦA BẠN)
    # ==============================================================================
    #st.markdown("---")
    #st.title("🏫 Hệ Thống Xuất Thời Khóa Biểu Học Sinh Theo Lớp")

    tab_lop1, tab_lop2, tab_lop3 = st.tabs(["🔍 In riêng từng Lớp", "📦 Xuất file in hàng loạt Lớp", "Chỉ in Tkb Lớp có thay đổi"])

    def hien_thi_pdf_tren_web(file_path, height=600):
        """Hàm nhúng PDF vào giao diện Streamlit bằng iframe"""
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)


    #--- TAB 1: XEM RIÊNG TỪNG LỚP ---
    with tab_lop1:
        #st.subheader("Chọn Lớp học để xem trước thời khóa biểu")
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
        #st.subheader("Đóng gói thời khóa biểu của mọi lớp vào 1 file PDF tổng")
        #st.write("Bố cục tối ưu tự động: xếp chồng 4 lớp trên một trang A4.")
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



def in_tkb_gv_button(dfc):
    # neu click nut nay 
    if st.sidebar.button("🖨️ In TKB Giáo viên", type="primary", use_container_width=True, key="F3"):
        # thi :
        try:
            #st.write("🎉 Vua click nut xep lai TKB. Xin cho mot lat... ")
            in_tkb_gv(dfc)
            #st.success("🎉 Da xep xong. ")
        except Exception as e:
            st.error(f"Lỗi khi xep: {e}")

def in_tkb_lop_button(dfc):
    # neu click nut nay 
    if st.sidebar.button("🖨️ In TKB Lớp", type="primary", use_container_width=True, key="TKBLOP"):
        # thi :
        try:
            #st.write("🎉 Vua click nut xep lai TKB. Xin cho mot lat... ")
            in_tkb_lop(dfc)
            #st.success("🎉 Da xep xong. ")
        except Exception as e:
            st.error(f"Lỗi khi xep: {e}")

@st.dialog("In Tkb Toàn Trường ", width="large")
def  in_tkb_truong(dfc):
    # Đọc file gốc từ Excel của bạn (Cột là Lớp, Dòng là Tiết)
    df_tkbc = dfc

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
    JSON_FILE_PATH = "info_school.json"
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

    df_tkbc["Giờ học"] = df_tkbc["Tiet"].map(map_gio_hoc)

    # Sắp xếp lại thứ tự cột để đưa "Thu", "Tiet", "Giờ học" lên đầu bảng đối chiếu
    cac_cot_co_dinh = ["Thu", "Tiet", "Giờ học"]
    cac_cot_lop = [col for col in df_tkbc.columns if col not in cac_cot_co_dinh]

    # Đảm bảo dữ liệu trống được điền chuỗi rỗng
    df_tkbc = df_tkbc.fillna("")

    # ==============================================================================
    # PHẦN 2: HÀM KẾT XUẤT FILE PDF KHỔ A4 DỌC (GIỮ NGUYÊN DẠNG LƯỚI EXCEL)
    # ==============================================================================


    def xuat_pdf_tkb_chung_a4_luoi_excel(df_data, filename="tkb_toan_truong_a4_luoi.pdf"):
        # 1. Cấu hình Font chữ tiếng Việt chuẩn văn giáo dục Times New Roman
        font_path = "C:\\Windows\\Fonts\\times.ttf"
        font_bold_path = "C:\\Windows\\Fonts\\timesbd.ttf"

        f_normal = "Times-New-Roman" if os.path.exists(font_path) else "Helvetica"
        f_bold = (
            "Times-New-Roman-Bold"
            if os.path.exists(font_bold_path)
            else "Helvetica-Bold"
        )

        if os.path.exists(font_path) and os.path.exists(font_bold_path):
            try:
                pdfmetrics.registerFont(TTFont("Times-New-Roman", font_path))
                pdfmetrics.registerFont(
                    TTFont("Times-New-Roman-Bold", font_bold_path)
                )
                from reportlab.pdfbase.pdfmetrics import registerFontDescription

                registerFontDescription(
                    "Times-New-Roman", italic=0, bold=0, name="Times-New-Roman"
                )
                registerFontDescription(
                    "Times-New-Roman",
                    italic=0,
                    bold=1,
                    name="Times-New-Roman-Bold",
                )
            except Exception:
                pass

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
                if text_col == "Thu":
                    text_col = "Thứ"
                elif text_col == "Tiet":
                    text_col = "Tiết"
                elif text_col.startswith("Lop_"):
                    text_col = text_col.replace("Lop_", "")

                header_row.append(Paragraph(text_col, style_header))
            table_data.append(header_row)

            # Đổ dữ liệu 60 dòng (10 tiết x 6 ngày) chạy dọc xuống dưới
            for _, row in df_trang_a4.iterrows():
                row_data = []
                # Các ô tiêu đề trái ít chữ vẫn giữ Paragraph để định dạng font Bold đẹp
                row_data.append(Paragraph(f"Thứ {row['Thu']}", style_time_cell))
                row_data.append(Paragraph(f"T.{row['Tiet']}", style_time_cell))
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
            file_luoi_out = xuat_pdf_tkb_chung_a4_luoi_excel(df_tkbc)

        st.success("🎉 Đã xuất bản file PDF chuẩn lưới Excel thành công!")


        with open(file_luoi_out, "rb") as f:
            st.download_button(label="📥 Tải file PDF lưới Excel (Khổ A4)",
                data=f,
                file_name="TKB_Toan_Truong_Luoi_Excel_A4.pdf",
                mime="application/pdf",)
            #st.write("### 📄 Bản xem trước trang in (Dạng lưới Excel quen thuộc):")
        hien_thi_pdf_luoi_a4_web(file_luoi_out)
        
    
def  in_tkb_truong_button(dfc):
    # neu click nut nay 
    if st.sidebar.button("🖨️ In TKB Trường", type="primary", use_container_width=True, key="F4"):
        # thi :
        try:
            #st.write("🎉 Vua click nut xep lai TKB. Xin cho mot lat... ")
            in_tkb_truong(dfc)
            #st.success("🎉 Da xep xong. ")
        except Exception as e:
            st.error(f"Lỗi khi xep: {e}")


@st.dialog("✏️ Chỉnh sửa các thông số cấu hình dưới đây và nhấn 'Lưu thay đổi' để cập nhật hệ thống.", width="")
def xem_chinh_tt():
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
        
        st.subheader("🏫 Tham số cấu hình xếp thời khóa biểu")
        tong_so_lop = st.number_input(":blue[Tổng số lớp học:]", value=int(current_info.get("tong_so_lop", 50)), min_value=1)
        so_tiet_toi_da = st.number_input(":blue[Số tiết dạy tối đa của GV / ngày:]", value=int(current_info.get("so_tiet_toi_da_mot_ngay", 5)), min_value=1, max_value=10)
        
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



def xem_chinh_tt_button():
    if st.sidebar.button("✏️ :blue[Chỉnh Thông Tin]",  use_container_width=True, key="XCTT"):
        # thi :
        try:
            #st.write("🎉 Vua click nut xep lai TKB. Xin cho mot lat... ")
            xem_chinh_tt()
            #st.success("🎉 Da xep xong. ")
        except Exception as e:
            st.error(f"Lỗi khi xep: {e}")

@st.dialog("✔️ Kiểm tra File Excel", width="medium")
def kiemtra_excel(dfc):
    st.write('KT Thu Tiet type dl')
    st.write('Tên GV')
    st.write('Tên Lop')



def kiemtra_excel_button(dfc):
    if st.sidebar.button("✔️ :blue[Kiểm tra file Excel]",  use_container_width=True, key="KTEX"):
        try:
            kiemtra_excel(dfc)
        except Exception as e:
            st.error(f"Lỗi khi xep: {e}")



@st.dialog("🚀 Dẫn Nhập", width="large")
def dan_nhap(dfc):
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


def dan_nhap_button(dfc):
    if st.sidebar.button("🚀 :blue[Dẫn nhập]",  use_container_width=True, key="DN"):
        try:
            dan_nhap(dfc)
        except Exception as e:
            st.error(f"Lỗi khi xep: {e}")


def xep_lai_tkb(dfc):
    st.write("Da xep xong!")


# f6 --- Hàm popup dictionary ---
@st.dialog("Tkb Gv.", width="medium")
def show_dict_popup(thutietij_dic, teacher_name):
    st.write(teacher_name)
    #print(thutietij_dic)


    # 2. Tạo DataFrame trống với các dòng (Tiết) từ 1 đến 10
    # Các cột từ Thứ 2 đến Thứ 7 (định dạng số: 2, 3, 4, 5, 6, 7)
    columns = [2, 3, 4, 5, 6, 7]
    index = range(1, 11)
    df = pd.DataFrame(index=index, columns=columns).fillna("")

    # 3. Duyệt qua dictionary và điền vào bảng (Theo logic hoán đổi của bạn)
    for key, value in thutietij_dic.items():
        row_str, col_str = key.split(",")
        col = int(row_str)  # Số đầu tiên là Thứ (Cột)
        row = int(col_str)  # Số thứ hai là Tiết (Hàng)
        
        # Kiểm tra xem hàng và cột có nằm trong phạm vi của bảng không
        if row in df.index and col in df.columns:
            df.at[row, col] = value.replace("Lop_","")

    # 4. Đổi tên cột từ số sang chữ "Thu X"
    df.columns = [f"Thu {c}" for c in df.columns]

    # --- PHẦN SỬA ĐỔI ĐỂ THÊM CỘT "Tiet" ---
    # Đưa chỉ số index (1-10) thành 1 cột và đặt tên cột cũ đó là "Tiet"
    df = df.reset_index().rename(columns={'index': 'Tiet'})

    # Hiển thị kết quả
    #st.write(df)

    # 2. Xây dựng cấu hình cho bảng AG Grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, resizable=True, sortable=False)

    # 3. Viết mã JavaScript để định dạng màu sắc cho cột 'Tiet'
    # - Tiết 1-5: Tô nền xanh lá nhạt (#d4edda) kèm chữ xanh đậm (#155724)
    # - Tiết 6-10: Tô nền vàng nhạt (#fff3cd) kèm chữ vàng đậm (#856404)
    rowstyle_jscode = JsCode("""
    function(params) {
        if (params.data && params.data.Tiet) {
            var val = parseInt(params.data.Tiet);
            if (val >= 1 && val <= 5) {
                return {
                    'backgroundColor': 'lightblue',
                    'color': '#155724'
                };
            } else if (val >= 6 && val <= 10) {
                return {
                    'backgroundColor': 'lightgreen',
                    'color': '#856404'
                };
            }
        }
        return null;
    }
    """)

    # Áp dụng màu sắc vào cột "Tiet"
    gb.configure_column(
        "Tiet", 
        header_name="Tiết", 
        cellStyle=rowstyle_jscode
    )
    gb.configure_column(
        "Thu 2", 
        header_name="Thứ Hai", 
        cellStyle=rowstyle_jscode
    )
    gb.configure_column(
        "Thu 3", 
        header_name="Thứ Ba", 
        cellStyle=rowstyle_jscode
    )
    gb.configure_column(
        "Thu 4", 
        header_name="Thứ Tư", 
        cellStyle=rowstyle_jscode
    )
    gb.configure_column(
        "Thu 5", 
        header_name="Thứ Năm", 
        cellStyle=rowstyle_jscode
    )
    gb.configure_column(
        "Thu 6", 
        header_name="Thứ Sáu", 
        cellStyle=rowstyle_jscode
    )
    gb.configure_column(
        "Thu 7", 
        header_name="Thứ Bảy", 
        cellStyle=rowstyle_jscode
    )
    gb.configure_grid_options(rowHeight=25)

    gridOptions = gb.build()

    # 4. Hiển thị bảng
    AgGrid(
        df,
        gridOptions=gridOptions,
        theme="balham",
        height=320,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True, # BẮT BUỘC phải bật thuộc tính này để chạy mã JsCode
        update_on="MODEL_CHANGED"
    )


# f5---Hàm tạo lịch cho một giáo viên---------
def build_teacher_schedule(dfc, teacher_name):
    vals = dfc.iloc[:, 2:].values
    thutietij_dic = {}
    thutietij_set = set()
    for i, hang in enumerate(vals):
        for j, ocell in enumerate(hang):
            if isinstance(ocell, str) and '_' in ocell:
                tengv,mon = ocell.strip().split("_")
                if teacher_name==tengv:
                    # gia tri cua cot ten "Thu" ở hàng index i
                    thu = dfc.at[i, "Thu"]
                    # gia tri cua cot ten "Tiet" ở hàng index i
                    tiet = dfc.at[i, "Tiet"]
                    # ten lop tuong ung:
                    lop = dfc.columns[j+2] # vì đã bỏ ra 2 cột 
                    #st.write('Thứ '+thu , "Tiết "+tiet, lop + "-" + mon)

                    valofij = lop + "-" + mon
                    x, y = thu, tiet
                    string_key = f"{x},{y}"

                    if string_key not in thutietij_dic :
                        thutietij_dic[string_key] = valofij 
                    else:
                        thutietij_dic[string_key] = thutietij_dic[string_key] + ", " + valofij

    #st.write(thutietij_dic)
    show_dict_popup(thutietij_dic, teacher_name)

    #show_dict_popup(schedule, teacher_name)
    ##return schedule

# f4--- Hàm menu chọn giáo viên ---
def show_teacher_menu(dfc):
    #df_chung = pd.read_excel("tkb_chung.xlsx", dtype=str)
    #df_all   = pd.read_excel("thoikhoabieu_all.xlsx", dtype=str)

    # Lấy tất cả tên GV từ các cột lớp (bỏ qua cột Thu, Tiet)
    gv_set = set()
    for col in dfc.columns:
        if col not in ["Thu","Tiet"]:
            # loại bỏ NaN, bỏ hậu tố "_TT"
            values = dfc[col].dropna().astype(str)
            clean_names = values.apply(lambda x: x.split("_")[0] if "_" in x else x)
            gv_set.update(clean_names.unique())
    gv_set.discard("")
    #print(gv_set)

    list_gvs_sorted = sorted(list(gv_set))

    selected_option = st.selectbox("👀 :red[XEM TKB TỪNG GIÁO VIÊN]", options=["-- Chọn Gv --"] + list_gvs_sorted, index=0)
    if selected_option != "-- Chọn Gv --":
        #st.write('TKB cua gv '+selected_option)
        build_teacher_schedule(dfc, selected_option)
        #show_dict_popup(dftkbgv)

# f3--- Hàm nút lưu vao excel bat ky luc nao tu luoi ---
def save_button(): # dinh nghia ham save_button() co viec tao nut trong sidebar
    if st.sidebar.button("💾 Lưu file tkb cập nhật", type="primary", use_container_width=True, key='H1'):
        try:
            st.session_state.dftkbc.to_excel("Tkb_luu_last/tkb_chung.xlsx", index=False)
            st.success("🎉 Đã lưu tkb cập nhật thành công vào tệp: Tkb_luu_last/tkb_chung.xlsx")
        except Exception as e:
            st.error(f"Lỗi khi lưu file: {e}")

# f2--- Hàm nút Xep lai TKB ---
def xeplai_tkb_button(dfc):
    # neu click nut nay 
    if st.sidebar.button("⚙️ Chạy Trình Xếp TKB", type="primary", use_container_width=True, key="H2"):
        # thi :
        try:
            #st.write("🎉 Vua click nut xep lai TKB. Xin cho mot lat... ")
            xep_lai_tkb(dfc)
            #st.success("🎉 Da xep xong. ")
        except Exception as e:
            st.error(f"Lỗi khi xep: {e}")

# f1----Hien thi grid tkbc---
def show_timetable(dfc):
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

    # JS: chọn ô đầu tiên, click ô thứ hai để hoán vị
    swap_cells_js = JsCode("""
    function(params) {
        if (!window.firstSelectedCell) {
            window.firstSelectedCell = {
                rowIndex: params.rowIndex,
                colId: params.column.colId,
                value: params.value,
                rowNode: params.node
            };
            params.api.refreshCells({force:true});
        } else {
            let cell1 = window.firstSelectedCell;
            let cell2_value = params.value;

            cell1.rowNode.setDataValue(cell1.colId, cell2_value);
            params.node.setDataValue(params.column.colId, cell1.value);

            window.firstSelectedCell = null;
            params.api.refreshCells({force:true});
        }
    }
    """)

    # JS: tô màu nền theo Thu/Tiet, chữ đỏ nếu trùng
    cell_style_js = JsCode("""
    function(params) {
        if (!params.data) return null;

        let thuVal = parseInt(params.data["Thu"]);
        let tietVal = parseInt(params.data["Tiet"]);
        let style = {};

        // nền theo Thu/Tiet
        if (!isNaN(thuVal) && !isNaN(tietVal)) {
            if (thuVal % 2 === 0) {
                style.backgroundColor = (tietVal <= 5) ? '#eeeeee' : '#cccccc';
            } else {
                style.backgroundColor = (tietVal <= 5) ? '#bbdefb' : '#90caf9';
            }
        }

        // nếu là cột Thu hoặc Tiet → chữ dark green
        if (params.column.colId === "Thu" || params.column.colId === "Tiet") {
            style.color = "darkblue";
            style.fontWeight = "900";
        }

        if (params.column.colId === "Tiet") {
            style.color = "darkblue";
            style.fontWeight = "700";
        }

        // highlight ô đang chọn để hoán vị
        if (window.firstSelectedCell && 
            window.firstSelectedCell.rowIndex === params.rowIndex && 
            window.firstSelectedCell.colId === params.column.colId) {
            style.backgroundColor = '#bbdefb';
            style.color = '#0d47a1';
            style.fontWeight = 'bold';
        }

        // kiểm tra trùng giá trị trong hàng
        let currentValue = params.value;
        if (currentValue !== "" && currentValue !== "nan") {
            let count = 0;
            for (let key in params.data) {
                if (key !== "Thu" && key !== "Tiet") {
                    if (params.data[key] === currentValue) {
                        count++;
                    }
                }
            }
            if (count > 1) {
                style.color = '#b71c1c'; // chữ đỏ cho ô trùng
                style.fontWeight = 'bold';
            }
        }

        return style;
    }
    """)

    gob = GridOptionsBuilder.from_dataframe(dfc)
    gob.configure_grid_options(onCellDoubleClicked=swap_cells_js)  
    gob.configure_default_column(
        cellStyle=cell_style_js,
        headerClass="my-blue-header",
        suppressMovable=True,
        resizable=False,
        editable=True,   # <-- Cho phép chỉnh sửa
        width=80, minWidth=80, maxWidth=80
    )

    # cố định cột Thu và Tiet
    gob.configure_column("Thu", pinned="left", width=60, minWidth=60, maxWidth=60, headerClass="my-blue-header")
    gob.configure_column("Tiet", pinned="left", width=60, minWidth=60, maxWidth=60, headerClass="my-blue-header")

    grid_response = AgGrid(
        dfc,
        gridOptions=gob.build(),
        allow_unsafe_jscode=True,
        key="grid_timetable_final",
        update_mode="MODEL_CHANGED"   # dùng đúng tham số
    )

    # cập nhật lại session_state với dữ liệu mới
    if grid_response and "data" in grid_response:
        st.session_state.dftkbc = pd.DataFrame(grid_response["data"])
        # hiển thị preview để kiểm tra
        #st.dataframe(st.session_state.dftkbc)



# --- Main ---------------
if __name__ == "__main__":

    try:
        df_tkbc = pd.read_excel("Tkb_luu_last/tkb_chung.xlsx")
        # Chọn tất cả các hàng (:), và các cột từ chỉ mục 2 đến hết (2:)
        df_tkbc.iloc[:, 2:] = df_tkbc.iloc[:, 2:].fillna("").astype(str)

        # khai bao trong st.session_state mot key co ten dftkbc thi gia tri cua no la df_tkbc
        st.session_state.dftkbc = df_tkbc
        #st.write(st.session_state.dftkbc)      
    
        # Hiển thị bảng và các chức năng
        show_timetable(st.session_state.dftkbc)

        # tao 2 col1 o sidebar, col2 o trang chinh
        col1, col2 = st.columns(2)
        with col1:
            # huong dan xep tkb
            dan_nhap_button(st.session_state.dftkbc)

            # kiem tra file excel
            kiemtra_excel_button(st.session_state.dftkbc)

            # Chinh thong tin cau hinh in an
            xem_chinh_tt_button()

            # Hien nut ham nhap de xep lai TKB
            xeplai_tkb_button(st.session_state.dftkbc)

            # Hien nut ham save dl luoi vao excel
            save_button()

            in_tkb_gv_button(st.session_state.dftkbc)

            in_tkb_lop_button(st.session_state.dftkbc)

            in_tkb_truong_button(st.session_state.dftkbc)

        with col2: # trang chinh
            # Hien thi menu chon  xem tkb tung gv
            show_teacher_menu(st.session_state.dftkbc)

  

    except FileNotFoundError: # neu chua co file ễcl thi yc upload file len
        uploaded_file = st.sidebar.file_uploader("📂 Chọn file Excel (.xlsx)", type=["xlsx"])
        if uploaded_file is not None:
            df_tkbc = pd.read_excel(uploaded_file)
            df_tkbc = df_tkbc.astype(str).fillna("")
            
            # khai bao trong st.session_state mot key co ten dftkbc thi gia tri cua no la df_tkbc
            st.session_state.dftkbc = df_tkbc
            #st.write(st.session_state.dftkbc)        

            # Hiển thị bảng và các chức năng
            show_timetable(st.session_state.dftkbc)

            # tao 2 col1 o sidebar, col2 o trang chinh
            col1, col2 = st.columns(2)
            with col1:
                save_button()
                st.write("xeplai_tkb_button(st.session_state.dftkbc")
            with col2:
                st.write("show_teacher_menu(st.session_state.dftkbc")
