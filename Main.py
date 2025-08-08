import pandas as pd

df_population = pd.read_excel(r'Source/TinhThanhVietNam2025.xlsx',sheet_name='Population 2023')
df_Phuong2025 = pd.read_excel(r'Source/TinhThanhVietNam2025.xlsx',sheet_name='3321-2025')


colunms = df_Phuong2025.columns
colunms = colunms.drop(["Mã", "Tên", "Cấp", "Mã TP", "Tỉnh / Thành Phố","Lý do không thực hiện Random Sampling"])

df_sampling = df_Phuong2025.copy()
df_sampling.set_index(["Mã TP","Tỉnh / Thành Phố","Mã","Tên"], inplace=True)

#Get được danh sách các mã của phường xã theo City
Codelist = []
for i in list(df_sampling.index):
    Codelist.append(i)

df_sampling = df_sampling.reset_index()

# Lấy danh sách tỉnh/thành phố hợp lệ
valid_cities = df_sampling["Tỉnh / Thành Phố"].dropna().unique().tolist()

# Hiển thị danh sách city
df_city = df_sampling.copy()
print("Danh sách tỉnh/thành phố có trong dữ liệu:")
for city in valid_cities:
    df_city_filter = df_city[df_city["Tỉnh / Thành Phố"] == city]
    ma_tp_list = df_city_filter["Mã TP"].unique()
    print(ma_tp_list,"-", city)

Input_City = input("chọn Tỉnh/Thành phố theo Mã TP, ngăn cách các thành phố bằng dấu phẩy: ").replace(" ", "").strip().split(',')
df_sampled_final = pd.DataFrame() 
for i in Input_City:
    if int(i) in df_city["Mã TP"].tolist():
        df_sampling_city = df_sampling.loc[df_sampling["Mã TP"] == int(i)].copy()
        # 1 phường không quá 30 ID
        Input_Sample_Size = int(input("Nhập kích thước mẫu: "))
        Input_SoPhuong = int(input("Nhập số lượng phường xã: "))

        if Input_SoPhuong*30 < Input_Sample_Size:
            print("Số phường không đủ để thực hiện cho số mẫu, vui lòng nhập lại.")
            exit()

        Danhsach_Phuong_loaitru = input("Nhập danh sách phường xã loại trừ (cách nhau bằng dấu phẩy), nếu không có nhập 0: ").strip().split(',')
        Danhsach_Phuong_loaitru = [int(x) for x in Danhsach_Phuong_loaitru]
        Danhsach_select = []
        for i in df_sampling_city["Mã"].tolist():
            if int(i) not in Danhsach_Phuong_loaitru:
                Danhsach_select.append(i)
        df_sampling_city = df_sampling_city[df_sampling_city["Mã"].isin(Danhsach_select)]

        df_filter = df_sampling_city[df_sampling_city["Quận/Phường không thực hiện\n Random Sampling"].notnull()].copy()

        Input_filter = int(input("Nhập điều kiện lọc ('Phường' = '0' or 'Xã' = '1' or 'Phường và xã' = 2): "))
        if Input_filter == 0:
            df_filter = df_filter[df_filter["Cấp"] == "Phường"]
        elif Input_filter == 1:
            df_filter = df_filter[df_filter["Cấp"] == "Xã"]

    
        # Lựa chọn phương pháp sampling
        Input_Method = int(input("Chọn phương pháp sampling (1: Theo mật độ, 2: Theo tỷ lệ quận gần/xa, 3: Theo Urban/ Rural): "))

        # Sampling theo mật độ dân số
        if Input_Method == 1:
            # Chỉ thực hiện lọc các phường xã có dân số và diện tích
            df_filter = df_filter[df_filter[" POPULATION "].notna()]
            df_filter = df_filter[df_filter[" AREA (KM2) "].notna()]
            df_filter["MAT_DO"] = df_filter[" POPULATION "] / df_filter[" AREA (KM2) "]

            df_filter["MAT_DO_Group"] = pd.qcut(df_filter["MAT_DO"], q=3, labels=["Thấp", "Trung bình", "Cao"])

            Input_Cao = int(input("Tỷ lệ nhóm mật độ cao (%): "))

            Input_Trung = int(input("Tỷ lệ nhóm mật độ trung bình (%): "))
            if Input_Cao + Input_Trung > 100:
                print("Tỷ lệ nhóm mật độ phải nằm trong khoảng từ 0 đến 100.")
                exit()
            Input_Thap = 100 - Input_Cao - Input_Trung
            TyLe_MatDo = {"Cao": Input_Cao / 100, "Trung bình": Input_Trung / 100, "Thấp": Input_Thap / 100}

            samples = []
            for group, tyle in TyLe_MatDo.items():
                df_group = df_filter[df_filter["MAT_DO_Group"] == group]
                n = int(Input_SoPhuong * tyle)

                if n > len(df_group):
                    samples.append(df_group)
                else:
                    samples.append(df_group.sample(n=n, random_state=42))

            df_sampled = pd.concat(samples)

        # Sampling theo tỷ lệ quận gần/xa
        elif Input_Method == 2:
            Input_Urban_Gan = input("Nhập Tỷ lệ Gần (mặc định là 80 thì nhấn enter): ")
            Input_Urban_Xa = input("Nhập Tỷ lệ Xa (mặc định là 20 thì nhấn enter): ")
            if Input_Urban_Gan == "":
                Input_Urban_Gan = 80
            if Input_Urban_Xa == "":
                Input_Urban_Xa = 20            
            Soluong_Urban_Gan = int(int(Input_Urban_Gan)/100 * Input_SoPhuong)
            Soluong_Urban_Xa = int(int(Input_Urban_Xa)/100 * Input_SoPhuong)

            if int(Input_Urban_Gan) + int(Input_Urban_Xa) != 100:
                print("Tỷ lệ gần và xa phải nằm trong khoảng từ 0 đến 100.")
                exit()

            df_filter_Gan = df_filter[df_filter["URBAN\n1: gần\n2: xa"] == 1]
            if len(df_filter_Gan) <= 0:
                df_filter_Gan = df_filter[df_filter["Cấp"] == "Phường"]
            
            df_filter_Xa = df_filter[df_filter["URBAN\n1: gần\n2: xa"] == 2]
            if len(df_filter_Xa) <= 0:
                df_filter_Xa = df_filter[df_filter["Cấp"] == "Xã"]

            if len(df_filter_Gan) <= 0 and len(df_filter_Xa) <= 0:
                df_filter_Gan = df_filter[df_filter["Cấp"] == "Phường"]
                df_filter_Xa = df_filter[df_filter["Cấp"] == "Xã"]          

            if Soluong_Urban_Gan > len(df_filter_Gan):
                print("Số lượng phường xã gần không đủ để lấy mẫu, vui lòng nhập lại.")
                exit()
            else:
                urban_gan = df_filter_Gan.sample(n=Soluong_Urban_Gan, random_state=42)

            if Soluong_Urban_Xa > len(df_filter_Xa):
                print("Số lượng phường xã xa không đủ để lấy mẫu, vui lòng nhập lại.")
                exit()
            else:
                urban_xa = df_filter_Xa.sample(n=Soluong_Urban_Xa, random_state=42)

            df_sampled = pd.concat([urban_gan, urban_xa])
        # Sampling Theo Urban/ Rural => chỉ chạy Urban/ Sub-Urban/ Rural => Có thể chọn 1 hoặc nhiều
        elif Input_Method == 3:
            Selected = input("Chọn phường xã theo Urban = 1/ Sub-Urban =2/ Rural =3, nếu chọn nhiều loại thì ngăn cách bằng dấu / (ví dụ 1,3): ").strip().split(',')
            input_urban = 0
            input_suburban = 0  
            input_rural = 0
            df_filter_urban = pd.DataFrame()
            df_filter_suburban = pd.DataFrame() 
            df_filter_rural = pd.DataFrame()
            Selected = [int(x) for x in Selected]
            for x in Selected:
                if int(x) not in [1, 2, 3]:
                    print("Không có các giá trị 1/2/3. Vui lòng nhập lại.")
                    exit()
                else:
                    x = int(x)
                    if x == 1:
                        df_filter_urban = df_filter[df_filter["URBAN\n1: gần\n2: xa"].isin([1, 2])]
                        input_urban = int(input("Nhập tỷ lệ Urban (%): "))
                    elif x == 2:
                        df_filter_suburban = df_filter[df_filter["SUB-URBAN \n( < 40km)"] == 1]
                        input_suburban = int(input("Nhập tỷ lệ Sub-Urban (%): "))
                    elif x == 3:
                        df_filter_rural = df_filter[df_filter["RURAL \n(>= 40km)"] == 1]
                        input_rural = int(input("Nhập tỷ lệ Rural (%): "))

            if 1 in Selected and 2 in Selected and 3 in Selected:
                if len(df_filter_urban) <= 0 and len(df_filter_suburban) <= 0 and len(df_filter_rural) <= 0:
                    df_filter_urban = df_filter[df_filter["Cấp"] == "Phường"]
                    df_filter_suburban = df_filter[df_filter["Cấp"] == "Phường"]
                    df_filter_rural = df_filter[df_filter["Cấp"] == "Xã"]    
            elif 1 in Selected and 2 in Selected:
                if len(df_filter_urban) <= 0 and len(df_filter_suburban) <= 0:
                    df_filter_urban = df_filter[df_filter["Cấp"] == "Phường"]
                    df_filter_suburban = df_filter[df_filter["Cấp"] == "Phường"]
            elif 1 in Selected and 3 in Selected:
                if len(df_filter_urban) <= 0 and len(df_filter_rural) <= 0:
                    df_filter_urban = df_filter[df_filter["Cấp"] == "Phường"]
                    df_filter_rural = df_filter[df_filter["Cấp"] == "Xã"]
            elif 2 in Selected and 3 in Selected:
                if len(df_filter_suburban) <= 0 and len(df_filter_rural) <= 0:
                    df_filter_suburban = df_filter[df_filter["Cấp"] == "Phường"]
                    df_filter_rural = df_filter[df_filter["Cấp"] == "Xã"]
            elif 1 in Selected:
                if len(df_filter_urban) <= 0:
                    df_filter_urban = df_filter[df_filter["Cấp"] == "Phường"]
            elif 2 in Selected:
                if len(df_filter_suburban) <= 0:
                    df_filter_suburban = df_filter[df_filter["Cấp"] == "Phường"]
            elif 3 in Selected:
                if len(df_filter_rural) <= 0:
                    df_filter_rural = df_filter[df_filter["Cấp"] == "Xã"]

            if input_urban + input_suburban + input_rural != 100:
                print("Tỷ lệ Urban, Sub-Urban và Rural phải nằm trong khoảng từ 0 đến 100.")
                exit()
            else:
                urban_count = int(input_urban/100 * Input_SoPhuong)
                suburban_count = int(input_suburban/100 * Input_SoPhuong)
                rural_count = int(input_rural/100 * Input_SoPhuong)

                if urban_count > 0 and (urban_count > len(df_filter_urban)):
                    print("Số lượng phường xã Urban không đủ để lấy mẫu, vui lòng nhập lại.")
                    exit()
                else:
                    df_filter_urban = df_filter_urban.sample(n=urban_count, random_state=42)

                df_filter_suburban = df_filter_suburban[~df_filter_suburban["Mã"].isin(df_filter_urban["Mã"])]
                if suburban_count > 0 and (suburban_count > len(df_filter_suburban)):
                    print("Số lượng phường xã Sub-Urban không đủ để lấy mẫu, vui lòng nhập lại.")
                    exit()
                else:
                    df_filter_suburban = df_filter_suburban.sample(n=suburban_count, random_state=42)

                if rural_count > 0 and (rural_count > len(df_filter_rural)):
                    print("Số lượng phường xã Rural không đủ để lấy mẫu, vui lòng nhập lại.")
                    exit()
                else:
                    df_filter_rural = df_filter_rural.sample(n=rural_count, random_state=42)

            df_sampled = pd.concat([df_filter_urban, df_filter_suburban, df_filter_rural])

        df_sampled_final = pd.concat([df_sampled_final, df_sampled])    
    else:
        print("Không tìm thấy thành phố/tỉnh")

    
df_sampled_final.set_index(["Mã TP","Tỉnh / Thành Phố","Mã","Tên","Cấp"] + colunms.tolist(), inplace=True)  
    
df_sampled_final.to_excel("Sampling.xlsx", index=True)
print("DONE")
a=0

