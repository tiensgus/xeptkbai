from st_aggrid import GridOptionsBuilder, JsCode
# ben streamlit_app.py có : from st_aggrid import AgGrid
import json

def ham_lay_gob(dfc, is_swap, is_view, cam_xep_keys):
    # bien custom_css se duoc return 
    custom_css = {
        # 1. Định dạng Tiêu đề cột
        ".my-blue-header": {
            "background-color": "#0d47a1 !important",
            "color": "#ffffff !important",
            "font-weight": "bold !important",
            "text-align": "center !important",
            "border-right": "2px solid #555555 !important",  # Đường kẻ đứng đậm cho Tiêu đề
        },
        ".my-blue-header .ag-header-cell-label": {
            "justify-content": "center !important",
        },
        ".my-blue-header .ag-header-cell-text": {
            "color": "#ffffff !important",
        },
        # 2. Đường kẻ đứng đậm cho TẤT CẢ CÁC Ô DỮ LIỆU
        ".ag-cell": {
            "border-right": "2px solid #0d47a1 !important",  # Độ dày 2px, màu xám đậm
        },
    }

    #### Cac dau {}: trong python van la {} nhung trong javascript xai chung python phai thanh {{}}

    cam_xep_json = json.dumps(cam_xep_keys)

    cell_click_js = JsCode(f"""
    function(params) {{
        let allowSwap = {str(is_swap).lower()};
        let allowView = {str(is_view).lower()};

        let colId = params.column.colId;
        // Bỏ qua nếu click vào cột Thứ hoặc Tiết
        if (colId === "Thứ" || colId === "Tiết") return;

        // --- TRƯỜNG HỢP 1: BẬT CHẾ ĐỘ XEM TKB LỚP ---
        if (allowView) {{
            let teacherValue = params.value;
            if (!teacherValue) return;

            let teacherPrefix = teacherValue.split("_")[0];
            let timetable = {{}};

            params.api.forEachNode(function(node) {{
                let row = node.data;
                let thu = row["Thứ"];
                let tiet = row["Tiết"];
                if (!timetable[tiet]) timetable[tiet] = {{}};

                let listLop = Object.keys(row).filter(k => k !== "Thứ" && k !== "Tiết");

                listLop.forEach(function(classCol) {{
                    let cellValue = row[classCol];
                    if (cellValue) {{
                        let parts = cellValue.split("_");
                        let prefix = parts[0];
                        let subject = parts[1] || "";
                        if (prefix === teacherPrefix) {{
                            timetable[tiet][thu] = classCol + "-" + subject;
                        }}
                    }}
                }});
            }});

            // Dựng bảng HTML Modal
            let tableHtml = "<table border='1' style='border-collapse:collapse;width:100%;text-align:center;'>";
            tableHtml += "<tr><th>Tiết</th><th>Thứ 2</th><th>Thứ 3</th><th>Thứ 4</th><th>Thứ 5</th><th>Thứ 6</th><th>Thứ 7</th></tr>";

            for (let tiet=1; tiet<=10; tiet++) {{
                let bgColor = (tiet <= 5) ? "#e0f7fa" : "#fff9c4";
                tableHtml += "<tr style='background-color:"+bgColor+"'><td>"+tiet+"</td>";
                for (let thu=2; thu<=7; thu++) {{
                    let val = timetable[tiet] && timetable[tiet][thu] ? timetable[tiet][thu] : "";
                    tableHtml += "<td>"+val+"</td>";
                }}
                tableHtml += "</tr>";
            }}
            tableHtml += "</table>";

            // Hiển thị Modal
            let modalDiv = document.createElement("div");
            modalDiv.style.position = "fixed";
            modalDiv.style.top = "0";
            modalDiv.style.left = "0";
            modalDiv.style.width = "100%";
            modalDiv.style.height = "100%";
            modalDiv.style.backgroundColor = "rgba(0,0,0,0.5)";
            modalDiv.style.display = "flex";
            modalDiv.style.alignItems = "center";
            modalDiv.style.justifyContent = "center";
            modalDiv.style.zIndex = "9999";

            let innerDiv = document.createElement("div");
            innerDiv.style.backgroundColor = "#fff";
            innerDiv.style.padding = "10px";
            innerDiv.style.borderRadius = "8px";
            innerDiv.style.maxHeight = "140%";
            innerDiv.style.maxWidth = "140%";
            innerDiv.style.fontSize = "12px";
            innerDiv.style.overflowY = "auto";
            innerDiv.innerHTML = "<h3>TKB của Gv: "+teacherPrefix+"</h3>" + tableHtml + "<br><button id='closeModal'>Đóng</button>";

            modalDiv.appendChild(innerDiv);
            document.body.appendChild(modalDiv);

            document.getElementById("closeModal").onclick = function() {{
                modalDiv.remove();
            }};
            return;
        }}

        // --- TRƯỜNG HỢP 2: BẬT CHẾ ĐỘ HOÁN VỊ Ô ---
        if (allowSwap) {{
            if (!window.firstSelectedCell) {{
                // Lưu lại thông tin ô thứ nhất (đảm bảo không bị undefined)
                window.firstSelectedCell = {{
                    rowIndex: params.rowIndex,
                    colId: params.column.colId,
                    value: (params.value !== undefined && params.value !== null) ? params.value : "",
                    rowNode: params.node
                }};
                params.api.refreshCells({{force:true}});
            }} else {{
                let cell1 = window.firstSelectedCell;
                let cell2_value = (params.value !== undefined && params.value !== null) ? params.value : "";
                let cell1_value = (cell1.value !== undefined && cell1.value !== null) ? cell1.value : "";

                // Hoán vị giá trị an toàn giữa 2 ô
                cell1.rowNode.setDataValue(cell1.colId, cell2_value);
                params.node.setDataValue(params.column.colId, cell1_value);

                // Reset trạng thái chọn
                window.firstSelectedCell = null;
                params.api.refreshCells({{force:true}});
            }}
            return;
        }}
    }}
    """)
    
    js_cell_template = """
    function(params) {
        if (!params.data) return null;
        let colId = params.column.colId;
        let thuVal = params.data["Thứ"];
        let tietVal = params.data["Tiết"];

        let camXepList = __CAM_XEP_DATA__; 
        let cellKey = thuVal + "_" + tietVal + "_" + colId;

        // 1. Kiểm tra xem TRONG DÒNG NÀY có giáo viên nào bị trùng lịch không
        let teacherCounts = {};
        for (let key in params.data) {
            if (key !== "Thứ" && key !== "Tiết" && key !== "Số TT") {
                let cellVal = params.data[key];
                if (cellVal && typeof cellVal === "string" && cellVal.trim() !== "") {
                    let prefix = cellVal.split("_")[0];
                    teacherCounts[prefix] = (teacherCounts[prefix] || 0) + 1;
                }
            }
        }

        let hasRowConflict = false;
        for (let prefix in teacherCounts) {
            if (teacherCounts[prefix] > 1) {
                hasRowConflict = true;
                break;
            }
        }

        // 2. Khởi tạo style cơ bản theo Thứ (màu nền phân chia theo thứ)
        let style = {'textAlign': 'center'};
        let t = parseInt(thuVal);
        let ti = parseInt(tietVal);

        if (!isNaN(t) && !isNaN(ti)) {
            if (t === 2) style.backgroundColor = (ti <= 5) ? '#EBF3FF' : '#D6E4FF';
            if (t === 3) style.backgroundColor = (ti <= 5) ? '#E8F8EC' : '#D1F2D9';
            if (t === 4) style.backgroundColor = (ti <= 5) ? '#F0FCFD' : '#E0F7FA';
            if (t === 5) style.backgroundColor = (ti <= 5) ? '#FFFDE7' : '#FFF9D9';
            if (t === 6) style.backgroundColor = (ti <= 5) ? '#fae7cb' : '#f7deb8';
            if (t === 7) style.backgroundColor = (ti <= 5) ? '#FAEDF9' : '#F3E5F5';
        }

        // 3. Xử lý màu cho Cột THỨ và TIẾT
        if (colId === "Thứ" || colId === "Tiết") {
            if (hasRowConflict) {
                style.color = '#b71c1c';       // Đỏ nếu dòng bị trùng GV
                style.fontWeight = '900';
            } else {
                style.color = "darkblue";     // Xanh đậm mặc định
                style.fontWeight = "900";
            }
        }

        // 4. Xử lý màu cho các CỘT LỚP (Ô nào chứa GV trùng thì chữ đỏ)
        if (colId !== "Thứ" && colId !== "Tiết") {
            let currentValue = params.value;
            if (currentValue && typeof currentValue === "string") {
                let currentPrefix = currentValue.split("_")[0];
                if (teacherCounts[currentPrefix] && teacherCounts[currentPrefix] > 1) {
                    style.color = '#b71c1c';
                    style.fontWeight = 'bold';
                }
            }
        }

        // 5. Nếu là ô cấm xếp (ghi đè màu xám)
        if (camXepList.includes(cellKey)) {
            return {'backgroundColor': '#D3D3D3', 'color': '#555555', 'textAlign': 'center'};
        }

        // 6. Hiệu ứng ô đang chọn để hoán vị (nếu có)
        if (window.firstSelectedCell && 
            window.firstSelectedCell.rowIndex === params.rowIndex && 
            window.firstSelectedCell.colId === colId) {
            style.backgroundColor = '#ffc107';
            style.color = '#000000';
            style.fontWeight = 'bold';
        }

        return style;
    }
    """
    cell_style_js = JsCode(
        js_cell_template.replace("__CAM_XEP_DATA__", cam_xep_json)
    )

    # 3- Hàm Javascript kiểm tra nếu là Tiết 5 hoặc Tiết 10 thì kẻ đường viền ngang bên dưới đậm hơn
    row_style_js = JsCode(f"""
    function(params) {{
        if (!params.data) return null;
        
        let tietVal = parseInt(params.data["Tiết"]);
        
        // Nếu là tiết 5 (cuối buổi sáng) hoặc tiết 10 (cuối buổi chiều/cuối ngày)
        if (tietVal === 5) {{
            return {{
                'borderBottom': '1px solid #333333'  
            }};
        }}
        if (tietVal === 10) {{
            return {{
                'borderBottom': '2px solid #333333'  
            }};
        }}
        return null;
    }}
    """)


    gob = GridOptionsBuilder.from_dataframe(dfc)
    gob.configure_selection("multiple", use_checkbox=True)
    gob.configure_grid_options(
        onCellClicked=cell_click_js,
        getRowStyle=row_style_js,  # <--- Bổ sung dòng này để kẻ vạch đậm ngang các T
    )

    gob.configure_default_column(
        cellStyle=cell_style_js,
        headerClass="my-blue-header",
        suppressMovable=True,
        sortable=False,
        resizable=False,
        editable=True,
        width=90,
        minWidth=90,
        maxWidth=90,
    )

    gob.configure_column(
        "Thứ",
        pinned="left",
        width=60,
        minWidth=60,
        maxWidth=60,
        headerClass="my-blue-header",
    )
    gob.configure_column(
        "Tiết",
        pinned="left",
        width=60,
        minWidth=60,
        maxWidth=60,
        headerClass="my-blue-header",
    )

    return gob.build(), custom_css
