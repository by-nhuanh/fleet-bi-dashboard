# Fleet BI Dashboard — Phân tích vận hành đội xe

Ứng dụng **Business Intelligence cho vận tải và quản lý đội xe** được xây dựng bằng **Python, Streamlit và DuckDB**, sử dụng dữ liệu từ tầng **Dimensional Data Store (DDS)** của đồ án.

**Dashboard trực tuyến:** https://fleet-bi-dashboard.streamlit.app/  
**Mã nguồn:** https://github.com/by-nhuanh/fleet-bi-dashboard

> Dashboard phục vụ phân tích dữ liệu lịch sử, **không phải hệ thống giám sát GPS thời gian thực**. Dữ liệu và biểu đồ được truy vấn từ các cơ sở dữ liệu DDS trong repository, không tự tạo số liệu minh họa.

## 1. Các trang phân tích

| Trang | Nội dung chính | File |
| --- | --- | --- |
| **Tổng quan vận hành** | KPI chuyến đi, tỷ lệ giao hàng trễ, chi phí mua nhiên liệu, xu hướng tháng; phân bổ chuyến theo cơ sở xuất phát và phương tiện | `app.py` |
| **Phân tích tuyến đường** | Bản đồ mật độ GPS vận tốc thấp, bản đồ GPS theo chuyến, các vị trí ưu tiên rà soát, so sánh số chuyến và tỷ lệ giao trễ theo tuyến | `pages/2_Route_GIS.py` |
| **Phân tích nhiên liệu** | Diễn biến mức nhiên liệu, vận tốc và trạng thái động cơ; biểu đồ tín hiệu đối chiếu; nhãn cảnh báo, giao dịch nhiên liệu liên kết và danh sách phương tiện cần kiểm tra | `pages/3_Fuel_Analytics.py` |

Ứng dụng có **thanh chuyển trang phía trên**, thiết kế sáng cố định; các lựa chọn lọc thay đổi phạm vi của biểu đồ và chỉ số tương ứng. Chi tiết các bộ lọc được trình bày trực tiếp trong từng trang.

## 2. Công nghệ và kiến trúc

- **Streamlit:** giao diện, điều hướng, bộ lọc và hiển thị bảng/biểu đồ.
- **DuckDB:** truy vấn dữ liệu DDS tại chỗ, ở chế độ `read_only`.
- **Altair:** trực quan hóa KPI, xu hướng, phân bổ và chuỗi cảm biến.
- **PyDeck:** bản đồ điểm GPS và bản đồ mật độ.
- **GitHub:** quản lý phiên bản; **Streamlit Community Cloud:** triển khai ứng dụng web.

Luồng xử lý: **DDS DuckDB → truy vấn SQL theo bộ lọc → tính chỉ số/tập dữ liệu → Streamlit/Altair/PyDeck → Dashboard**.

### Nguồn dữ liệu triển khai

| File | Công dụng |
| --- | --- |
| `database/fleet_dw.duckdb` | Trang Tổng quan vận hành |
| `database/fleet_analysis.duckdb` | Trang Tuyến đường và Nhiên liệu (bao gồm `Fact_GPS_Points`) |

Các database là **bản trích từ DDS** để triển khai, không thay thế kho dữ liệu gốc được xây dựng trong các pipeline ETL. Script `scripts/export_analysis_db.py` hỗ trợ tạo bản dữ liệu phân tích từ DDS gốc; không ghi đè file nguồn.

## 3. Công thức KPI và nguyên tắc đối soát

**Số chuyến đi** = `COUNT(*)` trên `dds.Fact_Trips` trong phạm vi lọc.

**Chuyến đủ điều kiện đánh giá** = số chuyến có `is_kpi_eligible = 1`.

**Tỷ lệ giao hàng trễ** =

```text
Số chuyến thỏa is_kpi_eligible = 1 AND delay_minutes > 0
---------------------------------------------------------------- × 100%
Số chuyến thỏa is_kpi_eligible = 1
```

**Chi phí mua nhiên liệu** = tổng `total_cost_usd` của các giao dịch `dds.Fact_Fuel_Purchases` liên kết với chuyến qua `trip_id`. Khi phân tích theo tháng, chi phí được quy về **tháng bắt đầu chuyến**, không phải tháng mua nhiên liệu.

Các giá trị tham chiếu đã được đối soát cho phạm vi chuyến toàn kỳ:

| Chỉ số | Giá trị |
| --- | ---: |
| Tổng số chuyến | 85.410 |
| Chuyến đủ điều kiện | 77.959 |
| Chuyến giao trễ đủ điều kiện | 51.970 |
| Tỷ lệ giao trễ | 66,66% |
| Tổng chi phí mua nhiên liệu | 95.592.992,04 USD |
| Giao dịch mua nhiên liệu | 196.442 |
| Điểm GPS | 1.435.571 |
| Chuyến có dữ liệu GPS | 746 |

**Lưu ý:** Các giá trị trên là mốc đối soát toàn kỳ, **không phải số cố định** khi người xem áp dụng bộ lọc. Trang GIS/Fuel chỉ phân tích các chuyến có dữ liệu GPS; không suy rộng kết luận cho toàn bộ chuyến.

### Quy ước nghiệp vụ và giới hạn

- **Cơ sở xuất phát:** sử dụng `Dim_Location` để phân nhóm hoạt động tại cơ sở; dữ liệu chưa chứng minh có một chiều **chi nhánh tổ chức** độc lập.
- **Vận tốc thấp:** ngưỡng do người xem chọn; nhiều điểm tốc độ thấp **không tự động chứng minh ùn tắc**. Ô tọa độ làm tròn là thống kê mật độ điểm ghi nhận, không phải số sự cố giao thông.
- **Cảnh báo nhiên liệu:** các nhãn `FUEL_THEFT`, `IDLE_EXTENDED`, `FUEL_RECEIPT_MISMATCH`… là tín hiệu có sẵn trong dữ liệu, **không phải kết luận gian lận/hỏng hóc đã được xác minh**. Việc phân loại nguyên nhân tự động cần ngưỡng được phê duyệt và kiểm định.
- **Dữ liệu GPS:** có 746 chuyến ghi nhận GPS trên 85.410 chuyến trong kho; diễn giải phải ghi rõ giới hạn bao phủ.

## 4. Cấu trúc repository

```text
fleet-bi-dashboard/
├── app.py                         # Trang Tổng quan
├── ui.py                          # Giao diện dùng chung và điều hướng
├── pages/
│   ├── 2_Route_GIS.py             # Phân tích tuyến đường
│   └── 3_Fuel_Analytics.py        # Phân tích nhiên liệu
├── database/
│   ├── fleet_dw.duckdb            # DDS triển khai Overview
│   └── fleet_analysis.duckdb      # DDS triển khai GIS/Fuel
├── .streamlit/config.toml         # Cấu hình màu sắc
├── scripts/export_analysis_db.py  # Script xuất DDS rút gọn
├── tests/                         # Kiểm thử KPI, quan hệ dữ liệu, giao diện
├── .github/workflows/validate.yml # GitHub Actions validation
├── requirements.txt
└── README.md
```

## 5. Chạy ứng dụng trên máy

Cần Python và hai file DuckDB trong thư mục `database/`.

```bash
git clone https://github.com/by-nhuanh/fleet-bi-dashboard.git
cd fleet-bi-dashboard
python -m pip install -r requirements.txt
streamlit run app.py
```

Mở địa chỉ localhost mà Streamlit hiển thị trong terminal. Để triển khai trên Streamlit Community Cloud, chọn repository này, nhánh `main`, file khởi chạy `app.py`. Website hiện tại: **https://fleet-bi-dashboard.streamlit.app/**.

## Đối soát chất lượng dữ liệu triển khai

Kết quả kiểm tra có thể tái lập bằng:

```bash
python scripts/audit_data_quality.py
```

Bản tổng hợp máy đọc được: [audit/data_quality_report.json](audit/data_quality_report.json). GitHub Actions chạy bộ kiểm tra trên **cơ sở dữ liệu DuckDB triển khai**, không thay thế kiểm toán toàn bộ dữ liệu gốc từ upstream ETL.

Kết quả ghi nhận:
- 8 bảng DDS đúng số lượng kỳ vọng; 85.410 chuyến, 77.959 chuyến hợp lệ, 51.970 chuyến giao trễ hợp lệ; 1.435.571 điểm GPS có mã bản tin duy nhất và liên kết đúng chuyến.
- **204/196.442 giao dịch nhiên liệu** có `vehicle_key` khác xe gắn với `trip_id`, tương ứng **97.440,92 USD**; đây là ngoại lệ **chưa được giải quyết ở nguồn**. Ứng dụng vẫn bảo toàn chúng trong tổng chi phí chính thức và gắn nhãn cần kiểm tra, không tự chuyển xe hoặc xóa chi phí.
- Chuyến `TRIP00078810` có 3.097 điểm GPS; chỉ 4 lần thay đổi vận tốc trên 0,01 km/h giữa các điểm liên tiếp. Mức nhiên liệu giảm trung bình khoảng 0,02326 điểm phần trăm mỗi điểm. Dạng đường thẳng phản ánh chuỗi DDS lưu trữ; **chưa đủ chứng cứ** xác nhận tín hiệu thực tế hay nguồn phát sinh đã nội suy/làm trơn.
- Sáu bản tin `IDLE_EXTENDED` của chuyến trên nằm ở 17:34–17:39 ngày 08/10/2024; nhãn không tự chứng minh toàn bộ thời gian nổ máy chờ hay nguyên nhân tiêu hao.

**Phân biệt rõ:** dữ liệu đạt quy tắc toàn vẹn khóa/kiểu/miền giá trị **không đồng nghĩa** tín hiệu cảm biến đã được kiểm định độ chính xác vật lý hoặc bất thường đã được xác minh thực địa.

## 6. Kiểm thử và lưu ý bàn giao

Chạy:

```bash
python -m compileall -q app.py ui.py pages tests
python -m unittest discover -s tests -v
```

Thư mục `tests/` chứa kiểm tra KPI, liên kết bảng DDS, GPS và kiểm thử mở các trang Streamlit. Workflow `.github/workflows/validate.yml` được cấu hình để kiểm tra khi cập nhật nhánh `main`. **Sự tồn tại của workflow không chứng minh các lần chạy đều thành công**; cần xem trạng thái thực tế trong GitHub Actions.

### Thông tin cần dùng khi viết báo cáo đồ án

- **Môi trường:** Streamlit + Python + DuckDB + Altair + PyDeck; mô hình truy vấn dữ liệu DDS.
- **Trang 1:** định nghĩa KPI, công thức giao trễ, các bộ lọc, xu hướng và phân tích theo cơ sở/phương tiện.
- **Trang 2:** luồng GPS–tuyến đường, bản đồ nhiệt, so sánh tuyến, điểm cần rà soát và giới hạn suy luận về ùn tắc.
- **Trang 3:** chuỗi nhiên liệu–vận tốc–trạng thái động cơ, cảnh báo và đối chiếu giao dịch, ranh giới giữa *dấu hiệu* và *kết luận nguyên nhân*.
- **Minh chứng:** dùng ảnh chụp trực tiếp từ Dashboard với bộ lọc được ghi rõ và kết quả kiểm thử thực tế; không thay ảnh/số bằng dữ liệu minh họa.

**Lưu ý về phạm vi công nghệ:** Sản phẩm hiện là **ứng dụng Streamlit**, không phải file Power BI `.pbix`. Báo cáo phải phản ánh đúng hình thức triển khai này.
