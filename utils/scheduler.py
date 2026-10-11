import pandas as pd
#import streamlit as st
import json
import time
from ortools.sat.python import cp_model
import ast
import io
#import zipfile



def chay_trinh_xeptkb(df, max_time):
    # ham nay de dua cac cell co 'x' vao lai df
    def dua_mon_db_vao_l(thu_tiet_lop, lop_gv_mon, df):
        # thu_tiet_lop la : available_slots_db  # dang [(6, 10, '10A4'), (6, 10, '11A1'), (6, 10, '11A2')]
        # lop_gv_mon la   :   assignments_db)   # dang [('12A2', 'Linh', 'DL'), ..., ('12A3', 'Hoàng', 'SV')]
        # df la df_ketqua
        # --- BẮT ĐẦU XỬ LÝ NÂNG CAO de dat toc do nhanh hon---
        # Bước 1: Tạo một DataFrame phụ từ 2 lists
        df_updates = pd.DataFrame({
            'Thứ': [t[0] for t in thu_tiet_lop],
            'Tiết': [t[1] for t in thu_tiet_lop],
            'Lớp': [t[2] for t in thu_tiet_lop],
            'Giá_trị': [f"{g[1]}_{g[2].replace('x','')}" for g in lop_gv_mon]
        })
        # Bước 2: Dùng pivot để biến đổi DataFrame phụ về cấu trúc giống hệt DataFrame gốc
        df_pivot = df_updates.pivot(index=['Thứ', 'Tiết'], columns='Lớp', values='Giá_trị')
        # Bước 3: Đặt tạm index cho DataFrame gốc theo ['Thứ', 'Tiết'] để đồng bộ chỉ mục với bảng pivot
        df.set_index(['Thứ', 'Tiết'], inplace=True)
        # Bước 4: Thực hiện hàm update (Hàm này chạy song song luồng, cực kỳ nhanh)
        df.update(df_pivot)
        # Bước 5: Đưa 'Thứ' và 'Tiết' quay trở lại làm cột bình thường
        df.reset_index(inplace=True)
        return df


    # ------------------------------------------------------------------
    # Buoc 1 : lay ra list cac rang buoc da danh dau True/False
    # ------------------------------------------------------------------
    start_time = time.time()

    JSON_FILE_PATH = "info_school/rang_buoc_xep.json"
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    options = list(data[0].keys()) # la list trong json
    listV = [data[0][opt] for opt in options]

    # --------------------------------------------------------------------------------------------------
    # BƯỚC 2: NHAP NUT BAT DAU KHỞI TẠO CP-MODEL & BIẾN QUYẾT ĐỊNH # (ĐẶT Ở ĐÂY - TRƯỚC KHI CHẠY SOLVER)
    # --------------------------------------------------------------------------------------------------
    # tao cac bien cho viec xep
    #columns = list(df.columns)
    classes = list(df.columns[2:])

    assignments = []
    assignments_db = []

    available_slots = []
    available_slots_db = []

    for idx, row in df.iterrows():
        thu = int(row["Thứ"])
        tiet = int(row["Tiết"])
        for c in classes:
            val = row[c]
            # vì MO có thêm x thành MOx được cố định không cần may xếp nên
            # những cái sau chỉ tính cho cac MO bình thường, cc se bo di chũ x
            if pd.notna(val) and val != "" and val[-1] != 'x' and "_" in val: 
                available_slots.append((thu, tiet, c))
                gv, mon = val.split("_")
                assignments.append((c, gv, mon))

            if pd.notna(val) and val != "" and val[-1] == 'x' and "_" in val : 
                available_slots_db.append((thu, tiet, c))
                gvdb, mondb = val.split("_")
                assignments_db.append((c, gvdb, mondb))

    pc_df = pd.DataFrame(assignments, columns=["LOP", "GIAOVIEN", "MON"])
    pc_summary = pc_df.groupby(["LOP", "GIAOVIEN", "MON"]).size().reset_index(name="SOTIET")
    # tao pc_df tu list du lieu assignments voi ten cac cot la "LOP", "GIAOVIEN", "MON" ,
    # cac gia tri la cac pt trong assignments
    pc_df = pd.DataFrame(assignments, columns=["LOP", "GIAOVIEN", "MON"])
    pc_summary = pc_df.groupby(["LOP", "GIAOVIEN", "MON"]).size().reset_index(name="SOTIET")
    #print(pc_summary) # pc_summary la bang co dang :
    #LOP     GIAOVIEN    MON     SOTIET
    #10A1    Nguyễn      TT      4
    # tao cac bien global sau de neu bo 1 rang buoc nao do thi khong gay loi
    all_days = sorted(list(set(thu for thu, tiet, c in available_slots)))
    all_days_slots = set((thu, tiet) for (thu, tiet, c) in available_slots)
    all_subjects = pc_summary["MON"].unique()
    all_gvs = pc_summary["GIAOVIEN"].unique()
    sessions = {"Sang": [1, 2, 3, 4, 5], "Chieu": [6, 7, 8, 9, 10]}
    all_gv_gap_vars = []

    # ---------------------------------------------------------
    model = cp_model.CpModel()

    # [Code khởi tạo biến x[(lop, gv, mon, thu, tiet)]...]
    # tao bang phan cong tung tiet se xep vao cac slot, moi phan tu cua list task la mot bo (lop,gv,mon,csoiet day)
    tasks = []
    for idx, row in pc_summary.iterrows():
        for i in range(row["SOTIET"]):
            tasks.append((row["LOP"], row["GIAOVIEN"], row["MON"], i))
    # task co dang [('9A3','Phúc','TT', 0),('9A3','Phúc','TT',1),('9A3','Phúc','TT', 2),('9A3','Phúc','TT',3), ...]
    
    # Tổng số tiết cần phải xếp theo phân công chuyên môn
    total_required_slots = len(tasks) 

    x = {}
    is_scheduled = []  # Biến đánh dấu task có được xếp thành công hay không

    for t_idx, (lop, gv, mon, _) in enumerate(tasks):
        for thu, tiet, c in available_slots:
            if c == lop:
                x[t_idx, thu, tiet] = model.NewBoolVar(f"x_{t_idx}_{thu}_{tiet}")
                
        scheduled_var = model.NewBoolVar(f"scheduled_{t_idx}")
        model.Add(sum(x[t_idx, thu, tiet] for (thu, tiet, c) in available_slots if c == lop) == scheduled_var)
        is_scheduled.append(scheduled_var)

    total_required_slots = len(is_scheduled) 

    # ----------------------------------------------------------------------------------------
    # RANG BUOC CO BAN I : XEP CO DINH CHO CAC O DA GAN CHU x SAU MON
    # ----------------------------------------------------------------------------------------
    # Đặt trước các Gv_MOx vào các vị trí cần xếp, available_slots sẽ không chứa các slots nay
    # Sau khi xếp xong sẽ xóa x và đưa các cell này vào df đã xếp by 
    # def dua_mon_db_vao_l(thu_tiet_lop, lop_gv_mon, df)

    # ----------------------------------------------------------------------------------------
    # RANG BUOC CO BAN II : CAC O CO DU LIEU Gv_MO (khong co x) MOI XEP, CON LAI CAM XEP
    # ----------------------------------------------------------------------------------------
    for thu, tiet, c in available_slots:
        model.Add(sum(x[t_idx, thu, tiet] for t_idx, task in enumerate(tasks) if task[0] == c and (t_idx, thu, tiet) in x) <= 1)

    # ----------------------------------------------------------------------
    # RANG BUOC CO BAN III: GV KHONG TRUNG TIET DAY
    # ----------------------------------------------------------------------
    #all_days_slots = set((thu, tiet) for (thu, tiet, c) in available_slots)
    #all_gvs = pc_summary["GIAOVIEN"].unique()
    for gv in all_gvs:
        for thu, tiet in all_days_slots:
            gv_vars = [x[t_idx, thu, tiet] for t_idx, task in enumerate(tasks) if task[1] == gv and (t_idx, thu, tiet) in x]
            if gv_vars:
                model.Add(sum(gv_vars) <= 1)

    # -----------------------------------------------------------------------------------------
    # RÀNG BUỘC LUA CHON 1 : SỐ TIẾT DẠY CỦA GV (TỐI THIỂU 2 TIẾT/BUỔI, TỐI ĐA 6 TIẾT/NGÀY) 
    # -----------------------------------------------------------------------------------------
    if listV[0]:
        #st.write(1, options[0])

        for gv in all_gvs:
            for thu in all_days:
                daily_vars = []  # Lưu toàn bộ biến dạy của GV trong 1 ngày (10 tiết)
                
                for session_name, slots in sessions.items():
                    session_vars = []  # Lưu các biến dạy của GV trong 1 buổi (5 tiết)
                    
                    for tiet in slots:
                        # Lấy danh sách các biến phân công của GV này tại (thu, tiet) ở tất cả các lớp
                        vars_in_tiet = [
                            x[t_idx, thu, tiet] 
                            for t_idx, task in enumerate(tasks) 
                            if task[1] == gv and (thu, tiet, task[0]) in available_slots and (t_idx, thu, tiet) in x
                        ]
                        if vars_in_tiet:
                            session_vars.extend(vars_in_tiet)
                            daily_vars.extend(vars_in_tiet)

                    # 1. RÀNG BUỘC BUỔI: Nếu có dạy thì tối thiểu 2 tiết (Số tiết trong buổi thuộc {0, 2, 3, 4, 5})
                    if session_vars:
                        # Biến has_teach = 1 nếu GV có ít nhất 1 tiết dạy trong buổi, = 0 nếu không dạy tiết nào
                        has_teach = model.NewBoolVar(f"has_teach_{gv}_{thu}_{session_name}")
                        
                        # Liên kết biến has_teach với tổng số tiết dạy trong buổi
                        model.Add(sum(session_vars) >= 1).OnlyEnforceIf(has_teach)
                        model.Add(sum(session_vars) == 0).OnlyEnforceIf(has_teach.Not())
                        
                        # Nếu has_teach = 1 thì tổng số tiết dạy phải >= 2 (Cấm trường hợp dạy đúng 1 tiết)
                        model.Add(sum(session_vars) >= 2).OnlyEnforceIf(has_teach)

                # 2. RÀNG BUỘC NGÀY: Tối đa 6 tiết/ngày (cho cả Sáng + Chiều)
                if daily_vars:
                    model.Add(sum(daily_vars) <= 6)

    # ----------------------------------------------------------------------------------------------------
    # RÀNG BUỘC LUA CHON 2 : Kiểm soát lủng tiết của Giáo viên (Tối đa 1 tiết/buổi, không quá 2 buổi/tuần)
    # ----------------------------------------------------------------------------------------------------
    if listV[1]:
        #st.write(2,options[1])
        # Ràng buộc: Kiểm soát lủng tiết của Giáo viên
        sessions = {"Sang": [1, 2, 3, 4, 5], "Chieu": [6, 7, 8, 9, 10]}

        # 1. BỔ SUNG: Khởi tạo danh sách tổng trước khi vào vòng lặp
        all_gv_gap_vars = []

        for gv in pc_summary["GIAOVIEN"].unique():
            gv_gaps_in_week = []
            for thu in all_days:
                for session_name, slots in sessions.items():
                    gv_busy = {}
                    for tiet in slots:
                        vars_in_tiet = [
                            x[t_idx, thu, tiet]
                            for t_idx, task in enumerate(tasks)
                            if task[1] == gv
                            and (thu, tiet, task[0]) in available_slots
                            and (t_idx, thu, tiet) in x
                        ]
                        if vars_in_tiet:
                            b = model.NewBoolVar(
                                f"gv_busy_{gv}_{thu}_{session_name}_{tiet}"
                            )
                            model.Add(sum(vars_in_tiet) == 1).OnlyEnforceIf(b)
                            model.Add(sum(vars_in_tiet) == 0).OnlyEnforceIf(b.Not())
                            gv_busy[tiet] = b
                        else:
                            gv_busy[tiet] = 0

                    gap_vars_in_session = []
                    for k in slots:
                        before_k = [
                            v
                            for v in [gv_busy[i] for i in slots if i < k]
                            if not (isinstance(v, int) and v == 0)
                        ]
                        after_k = [
                            v
                            for v in [gv_busy[j] for j in slots if j > k]
                            if not (isinstance(v, int) and v == 0)
                        ]

                        if before_k and after_k:
                            has_before = model.NewBoolVar(
                                f"has_before_{gv}_{thu}_{session_name}_{k}"
                            )
                            has_after = model.NewBoolVar(
                                f"has_after_{gv}_{thu}_{session_name}_{k}"
                            )
                            is_empty_k = model.NewBoolVar(
                                f"is_empty_{gv}_{thu}_{session_name}_{k}"
                            )

                            model.Add(sum(before_k) >= 1).OnlyEnforceIf(has_before)
                            model.Add(sum(before_k) == 0).OnlyEnforceIf(
                                has_before.Not()
                            )
                            model.Add(sum(after_k) >= 1).OnlyEnforceIf(has_after)
                            model.Add(sum(after_k) == 0).OnlyEnforceIf(
                                has_after.Not()
                            )

                            curr_val = gv_busy[k]
                            if isinstance(curr_val, int):
                                model.Add(is_empty_k == (1 if curr_val == 0 else 0))
                            else:
                                model.Add(curr_val == 0).OnlyEnforceIf(is_empty_k)
                                model.Add(curr_val == 1).OnlyEnforceIf(is_empty_k.Not())

                            gap_at_k = model.NewBoolVar(
                                f"gap_at_{gv}_{thu}_{session_name}_{k}"
                            )
                            model.AddBoolAnd(
                                [has_before, has_after, is_empty_k]
                            ).OnlyEnforceIf(gap_at_k)
                            model.AddBoolOr(
                                [has_before.Not(), has_after.Not(), is_empty_k.Not()]
                            ).OnlyEnforceIf(gap_at_k.Not())
                            gap_vars_in_session.append(gap_at_k)

                    if gap_vars_in_session:
                        model.Add(sum(gap_vars_in_session) <= 1)
                        session_has_gap = model.NewBoolVar(
                            f"session_has_gap_{gv}_{thu}_{session_name}"
                        )
                        model.Add(sum(gap_vars_in_session) == 1).OnlyEnforceIf(
                            session_has_gap
                        )
                        model.Add(sum(gap_vars_in_session) == 0).OnlyEnforceIf(
                            session_has_gap.Not()
                        )
                        gv_gaps_in_week.append(session_has_gap)

                        # 2. BỔ SUNG: Thêm biến lủng tiết buổi này vào danh sách tổng
                        all_gv_gap_vars.append(session_has_gap)

            if gv_gaps_in_week:
                model.Add(sum(gv_gaps_in_week) <= 2)
    # ----------------------------------------------------------------------------------------------------
    # RÀNG BUỘC LUA CHON 3 : MON TT NV PHAI CO IT NHAT 1 LAN TIET DOI TRONG tUAN
    # ----------------------------------------------------------------------------------------------------
    if listV[2]:
        #st.write(3, options[2])

        for lop in classes:
            for mon_target in ["NV", "TT"]:
                target_tasks = [
                    t_idx
                    for t_idx, task in enumerate(tasks)
                    if task[0] == lop and task[2] == mon_target
                ]
                if len(target_tasks) >= 2:
                    pair_vars = []
                    for thu, tiet, c in available_slots:
                        # Kiểm tra slot liền kề (thu, tiet) và (thu, tiet + 1)
                        if c == lop and (thu, tiet + 1, lop) in available_slots:
                            s1 = sum(
                                x[t_idx, thu, tiet]
                                for t_idx in target_tasks
                                if (t_idx, thu, tiet) in x
                            )
                            s2 = sum(
                                x[t_idx, thu, tiet + 1]
                                for t_idx in target_tasks
                                if (t_idx, thu, tiet + 1) in x
                            )

                            is_pair = model.NewBoolVar(
                                f"pair_{lop}_{mon_target}_{thu}_{tiet}"
                            )
                            # Ép logic: is_pair = 1 <=> (s1 == 1 và s2 == 1)
                            model.Add(s1 + s2 == 2).OnlyEnforceIf(is_pair)
                            model.Add(s1 + s2 < 2).OnlyEnforceIf(is_pair.Not())
                            pair_vars.append(is_pair)

                    # Ép buộc phải có ít nhất 1 cặp tiết đôi cho môn đó trong tuần
                    if pair_vars:
                        model.Add(sum(pair_vars) >= 1)

    # ----------------------------------------------------------------------------------------------------
    # RÀNG BUỘC LUA CHON 4 : KHONG HOC QUA 2 TIET/MON/NGAY/LOP
    # ----------------------------------------------------------------------------------------------------
    if listV[3]:
        #st.write(4, options[3])
        #all_days = sorted(list(set(thu for thu, tiet, c in available_slots)))
        #all_subjects = pc_summary["MON"].unique()
        for lop in classes:
            for mon_target in all_subjects:
                target_tasks = [t_idx for t_idx, task in enumerate(tasks) if task[0] == lop and task[2] == mon_target]
                if len(target_tasks) > 2:
                    for thu in all_days:
                        tasks_in_day = [
                            x[t_idx, thu, tiet]
                            for t_idx in target_tasks
                            for (th, tiet, c) in available_slots
                            if th == thu and c == lop and (t_idx, thu, tiet) in x
                        ]
                        if tasks_in_day:
                            model.Add(sum(tasks_in_day) <= 2)

    # ----------------------------------------------------------------------------------------------------
    # RÀNG BUỘC LUA CHON 5 : GIÁO VIÊN TRÁNH TIẾT THEO BANG EXCEL gv_yc_tranh.xlsx
    # ----------------------------------------------------------------------------------------------------
    if listV[4]:
        #st.write(5, options[4])

        df_off = pd.read_excel("gv_yc_tranh.xlsx")

        def parse_off_slots(cell_value):
            """Hàm chuyển đổi chuỗi '(2,1), (2,2)' thành danh sách các tuple [(2, 1), (2, 2)]"""
            if pd.isna(cell_value) or not str(cell_value).strip():
                return []

            val_str = str(cell_value).strip()
            # Nếu chuỗi không có dấu ngoặc vuông bên ngoài, bọc lại để ast parse thành list các tuple
            if not val_str.startswith("["):
                val_str = f"[{val_str}]"
            try:
                return ast.literal_eval(val_str)
            except Exception:
                return []

        for _, row in df_off.iterrows():
            # Lấy tên GV và loại bỏ hoàn toàn khoảng trắng thừa
            gv_name = str(row["ten_gv"]).strip()
            off_slots = parse_off_slots(row["yc_tranh_thu_tiet"])

            for off_thu, off_tiet in off_slots:
                for t_idx, (lop, gv, mon, _) in enumerate(tasks):
                    # Tách lấy phần tên GV trước dấu '_' (Ví dụ: "Khiêm_AV" -> "Khiêm")
                    gv_clean = gv.split("_")[0].strip() if "_" in gv else gv.strip()

                    # So sánh chính xác tên giáo viên
                    if gv_clean.lower() == gv_name.lower():
                        if (off_thu, off_tiet, lop) in available_slots and (
                            t_idx,
                            off_thu,
                            off_tiet,
                        ) in x:
                            # Bắt buộc biến này = 0 (Không cho phép xếp)
                            model.Add(x[t_idx, off_thu, off_tiet] == 0)


    # ----------------------------------------------------------------------------------------------------
    # RÀNG BUỘC LUA CHON 6 : GIÁO VIÊN TRÁNH TIẾT THEO BANG EXCEL gv_yc_tranh.xlsx
    # ----------------------------------------------------------------------------------------------------
    if listV[5]:
        #st.write(6, options[5])

        # Ràng buộc: Môn "CC" phải xếp vào Thứ 2, Tiết 1
        for t_idx, (lop, gv, mon, _) in enumerate(tasks):
            if mon == "CC" and (2, 1, lop) in available_slots:
                model.Add(x[t_idx, 2, 1] == 1)

    # ---------------------------------------------------------
    # BƯỚC 4: HÀM MỤC TIÊU (OBJECTIVE FUNCTION)
    # (ĐẶT Ở ĐÂY - TRƯỚC KHI CHẠY SOLVER)
    # ---------------------------------------------------------
    # model.Maximize(...) hoặc model.Minimize(...)
    penalties = []
    all_gv_gap_vars = []

    # (1) Ưu tiên cao nhất: Số tiết xếp thành công (+10,000 điểm/tiết)
    for scheduled_var in is_scheduled:
        penalties.append(scheduled_var * 10000)

    # (2) Phạt GV bị lủng tiết (-100 điểm/buổi lủng)
    for gv_gap_var in all_gv_gap_vars:
        penalties.append(gv_gap_var * -100)

    # (3) Phạt Lớp bị lủng tiết giữa buổi (-200 điểm/tiết lủng)
    for thu in all_days:
        for session_name, slots in sessions.items():
            for c in classes:
                class_busy = {}
                for tiet in slots:
                    vars_in_tiet = [x[t_idx, thu, tiet] for t_idx, task in enumerate(tasks) if task[0] == c and (t_idx, thu, tiet) in x]
                    if vars_in_tiet:
                        b = model.NewBoolVar(f"class_busy_{c}_{thu}_{session_name}_{tiet}")
                        model.Add(sum(vars_in_tiet) == 1).OnlyEnforceIf(b)
                        model.Add(sum(vars_in_tiet) == 0).OnlyEnforceIf(b.Not())
                        class_busy[tiet] = b
                    else:
                        class_busy[tiet] = 0

                for k in slots:
                    before_k = [v for v in [class_busy[i] for i in slots if i < k] if not (isinstance(v, int) and v == 0)]
                    after_k = [v for v in [class_busy[j] for j in slots if j > k] if not (isinstance(v, int) and v == 0)]

                    if before_k and after_k:
                        has_before = model.NewBoolVar(f"c_before_{c}_{thu}_{k}")
                        has_after = model.NewBoolVar(f"c_after_{c}_{thu}_{k}")
                        is_empty = model.NewBoolVar(f"c_empty_{c}_{thu}_{k}")

                        model.Add(sum(before_k) >= 1).OnlyEnforceIf(has_before)
                        model.Add(sum(before_k) == 0).OnlyEnforceIf(has_before.Not())
                        model.Add(sum(after_k) >= 1).OnlyEnforceIf(has_after)
                        model.Add(sum(after_k) == 0).OnlyEnforceIf(has_after.Not())

                        curr_val = class_busy[k]
                        if isinstance(curr_val, int):
                            model.Add(is_empty == (1 if curr_val == 0 else 0))
                        else:
                            model.Add(curr_val == 0).OnlyEnforceIf(is_empty)
                            model.Add(curr_val == 1).OnlyEnforceIf(is_empty.Not())

                        gap_class_k = model.NewBoolVar(f"gap_class_{c}_{thu}_{k}")
                        model.AddBoolAnd([has_before, has_after, is_empty]).OnlyEnforceIf(gap_class_k)
                        penalties.append(gap_class_k * -200)

    model.Maximize(sum(penalties))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time
    solver.parameters.num_search_workers = 2
    
    #-- Giải bài toán------------
    status = solver.Solve(model)
    #----------------------------

    # Toi day thi da giai xong nen cham dut with, bat dau khau xu li kq giai    
    elapsed_time = time.time() - start_time
    #st.info(f"⏱️ **Đã hoàn thành sau:** {elapsed_time:.1f} giây")

    # ---------------------------------------------------------
    # BƯỚC 6: XỬ LÝ VÀ XUẤT KẾT QUẢ (NẰM Ở ĐÂY)
    # ---------------------------------------------------------
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # tổng số tiết phải xếp
        total_required_slots = len(tasks) 

        # Số tiết đã gán thành công vào thời khóa biểu
        assigned_slots = sum(solver.Value(scheduled_var) for scheduled_var in is_scheduled)

        # so tiet chua xep duoc
        sotietchuax = total_required_slots - assigned_slots

        # Tính tỷ lệ %
        percent = (assigned_slots / total_required_slots) * 100 if total_required_slots > 0 else 0

        #st.success(f"✅ TKB đã xếp được : {percent} %")
        #st.balloons()  # Hiển thị bong bóng bay

        # Số tiết đã gán thành công vào thời khóa biểu
        #assigned_slots = sum(solver.Value(scheduled_var) for scheduled_var in is_scheduled)

        # Khởi tạo 2 mảng de luu du lieu da xep va chua xep 
        result_tkb = {(thu, tiet, c): "" for thu, tiet, c in available_slots}
        unassigned_tasks = []

        # Lay dl dua vao 2 mang tren
        for t_idx, (lop, gv, mon, i) in enumerate(tasks):
            if solver.Value(is_scheduled[t_idx]) == 1:
                for (thu, tiet, c) in available_slots:
                    if c == lop and (t_idx, thu, tiet) in x and solver.Value(x[t_idx, thu, tiet]) == 1:
                        # dua vao mang da xep result_tkb
                        result_tkb[(thu, tiet, lop)] = f"{gv}_{mon}"
            else:
                # dua vao mang chua xep
                unassigned_tasks.append((lop, f"{gv}_{mon}"))

        # Tao df tkb da xep duoc
        out_data = []
        all_time_slots = sorted(list(set((r[0], r[1]) for r in df[["Thứ", "Tiết"]].values)))
        for thu, tiet in all_time_slots:
            row = {"Thứ": thu, "Tiết": tiet}
            for c in classes:
                row[c] = result_tkb.get((thu, tiet, c), "")
            out_data.append(row)

        #percent = (assigned_slots / total_required_slots) * 100 if total_required_slots > 0 else 0
        df_ketqua = pd.DataFrame(out_data)

        #Dua TD da bi xoa vao out_data nhu cu---------------------------------------------
        if len(available_slots_db) > 0 and len(available_slots_db) == len(assignments_db):
            df_ketqua = dua_mon_db_vao_l(available_slots_db, assignments_db, df_ketqua)
        #---------------------------------------------------------------------------------
        #st.info(f"**TKB đã xếp với tiến độ hoàn thành: **:red[{percent:.1f}%] ({assigned_slots} / {assigned_slots+len(unassigned_tasks)} tiết)")
        kq_so = [total_required_slots, assigned_slots, sotietchuax, percent]


        if len(unassigned_tasks) > 0 :
            # B. Tạo df_chua_xep: Đặt liên tục theo cột Lớp
            unassigned_by_class = {c: [] for c in classes}
            for lop_un, gv_mon_un in unassigned_tasks:
                unassigned_by_class[lop_un].append(gv_mon_un)

        #    max_rows = max([len(v) for v in unassigned_by_class.values()], default=0)

        #    out_chua_xep = []
        #    for i in range(max_rows):
        #        row = {"STT": i + 1}
        #        for c in classes:
        #            if i < len(unassigned_by_class[c]):
        #                row[c] = unassigned_by_class[c][i]
        #            else:
        #                row[c] = ""
        #        out_chua_xep.append(row)

        #    df_chua_xep = pd.DataFrame(out_chua_xep)
            #st.info(f"**:red[Và phần còn lại chưa xếp được:]** ({100-percent:.1f}%) :red[({len(unassigned_tasks)} / {assigned_slots+len(unassigned_tasks)} tiết)]")
            #st.dataframe(df_chua_xep, hide_index=True)
        out_chua_xep = []
        if len(unassigned_tasks) > 0:
            # 1. Gom các tiết chưa xếp theo từng lớp
            unassigned_by_class = {c: [] for c in classes}
            for lop_un, gv_mon_un in unassigned_tasks:
                unassigned_by_class[lop_un].append(gv_mon_un)

            # 2. Xây dựng df_chua_xep có cấu trúc y hệt df_da_xep (lấy Thứ và Tiết chuẩn từ bảng mẫu)
            num_rows = len(df_ketqua)
            for i in range(num_rows):
                # Lấy trực tiếp Thứ và Tiết từ dòng tương ứng của df_da_xep để đồng bộ cấu trúc
                row = {
                    "Thứ": df_ketqua.iloc[i]["Thứ"],
                    "Tiết": df_ketqua.iloc[i]["Tiết"],
                }

                # Đưa các tiết chưa xếp của từng lớp vào các dòng từ trên xuống
                for c in classes:
                    tasks_of_class = unassigned_by_class.get(c, [])
                    if i < len(tasks_of_class):
                        row[c] = tasks_of_class[i]
                    else:
                        row[c] = ""  # Ô trống nếu lớp đó hết tiết dư

                out_chua_xep.append(row)

            # Chuyển thành DataFrame
            df_chua_xep = pd.DataFrame(out_chua_xep)
        else:
            # Nếu không có tiết nào chưa xếp, tạo một bảng rỗng cấu trúc y hệt df_da_xep
            df_chua_xep = df_ketqua.copy()
            for c in classes:
                if c in df_chua_xep.columns:
                    df_chua_xep[c] = ""

        #print(df_chua_xep)
        # Xuat ra excel 2 file tkb da va chua xep
        # Xuất ra buffer Excel
        #buffer1 = io.BytesIO()
        #df_ketqua.to_excel(buffer1, index=False)
        #if len(unassigned_tasks) > 0 :
        #    buffer2 = io.BytesIO()
        #    df_chua_xep.to_excel(buffer2, index=False)

        # Tạo file zip chứa cả 2 Excel
        #zip_buffer = io.BytesIO()
        #with zipfile.ZipFile(zip_buffer, "w") as zf:
        #    zf.writestr("tkb_da_xep.xlsx", buffer1.getvalue())
        #    if len(unassigned_tasks) > 0 :
        #        zf.writestr("tkb_chua_xep.xlsx", buffer2.getvalue())

        # Nút tải zip
        #st.download_button(
        #    label="📥 Download 2 Excel files tkb đã xếp và chưa xếp",
        #    data=zip_buffer.getvalue(),
        #    file_name="tkb_da_va_chua_xep.zip",
        #    mime="application/zip"
        #)
        return df_ketqua, df_chua_xep, kq_so

    else:
        #st.error("❌ Không tìm được lời giải khả thi! Hãy kiểm tra lại các ràng buộc.")
        print("❌ Không tìm được lời giải khả thi! Hãy kiểm tra lại các ràng buộc.")

