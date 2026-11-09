# CHƯƠNG 4. TRIỂN KHAI DASHBOARD BUSINESS INTELLIGENCE VÀ PHÂN TÍCH KỊCH BẢN

*Bản thảo phục vụ Task 10–12, cập nhật 09/11/2026. Chỉ mô tả những gì được mã nguồn và tài liệu đối soát chứng minh. Những hạng mục chưa có bằng chứng được nêu như giới hạn, không kết luận đã hoàn thành.*

## 4.1 Môi trường triển khai

Hệ thống sử dụng Python, DuckDB và Streamlit để xây dựng một dashboard phân tích vận hành đội xe. Cơ sở dữ liệu quan hệ đã được nạp qua pipeline ETL vào schema DDS, trong đó các bảng sự kiện và chiều được liên kết qua khóa định danh.

Ứng dụng được quản lý phiên bản tại repository `by-nhuanh/fleet-bi-dashboard` và triển khai qua Streamlit Community Cloud tại `https://fleet-bi-dashboard.streamlit.app/`. File phụ thuộc là `requirements.txt`. Cấu hình màu sắc được cố định ở `.streamlit/config.toml` nhằm giảm sự khác biệt hiển thị giữa chế độ giao diện sáng và tối của thiết bị.

Do sử dụng Streamlit thay cho Power BI, đầu ra dashboard là ứng dụng web, mã nguồn và file DuckDB thay vì `Project_Dashboard.pbix`. Đây là lựa chọn triển khai đã được nhóm cho phép trong bảng phân công Task 10; không nên mô tả như sản phẩm Power BI nếu không có file PBIX thực tế.

Hai bản database được sử dụng: `database/fleet_dw.duckdb` cho trang tổng quan; `database/fleet_analysis.duckdb` cho GIS và nhiên liệu. Bản triển khai phân tích là bản trích từ schema DDS gốc, không dùng dữ liệu KPI tự tạo.

## 4.2 Trang 1 — Tổng quan vận hành

Trang tổng quan cung cấp các nhóm chỉ số:
- **Số chuyến đi**: đếm bản ghi `dds.Fact_Trips`. Giá trị toàn kỳ đã đối soát là **85.410 chuyến**.
- **Tỷ lệ giao hàng trễ**: số chuyến đủ điều kiện KPI và `delay_minutes > 0` chia cho tổng số chuyến đủ điều kiện. Đối soát toàn kỳ: **51.970 / 77.959 = 66,66%**. Không sử dụng riêng cờ `is_late_delivery` để tính tỷ lệ này.
- **Tổng chi phí mua nhiên liệu**: cộng `total_cost_usd` của `dds.Fact_Fuel_Purchases` theo các `trip_id` liên kết. Giá trị toàn kỳ: **95.592.992,04 USD**, từ **196.442** giao dịch mua.

Trang hiển thị xu hướng theo tháng. Bộ lọc được tổ chức theo ngày bắt đầu chuyến, phương tiện, cơ sở xuất phát, loại cơ sở xuất phát và cơ sở đích. Khi lọc theo thời gian, chi phí mua nhiên liệu được phân bổ theo **ngày bắt đầu của chuyến liên kết**, không theo ngày phát sinh giao dịch mua.

**Lưu ý về chi nhánh**: DDS chưa xác thực được một bảng `Dim_Branch` độc lập. Vì vậy trường cơ sở xuất phát từ `Dim_Location` được dùng làm biến đại diện cho đơn vị/cơ sở vận hành; không đồng nhất khái niệm này với chi nhánh pháp lý hoặc tổ chức.

Dữ liệu nguồn xác nhận các quan hệ gồm `Fact_Trips` với `Dim_Date`, `Dim_Vehicle`, `Dim_Location`; `Fact_Fuel_Purchases` với `Fact_Trips` theo `trip_id`. Đối soát dữ liệu gốc ghi nhận **204** giao dịch mua nhiên liệu có mã xe không trùng xe liên kết của chuyến; khi phân tích chi phí theo xe cần giải thích rõ tiêu thức gán chi phí.

## 4.3 Trang 2 — Kịch bản phân tích tuyến đường và điểm nghẽn (GIS)

Trang GIS đọc `dds.Fact_GPS_Points` kết hợp bảng chuyến, thời gian và tuyến đường. Kho DDS có **1.435.571 điểm GPS từ 746 chuyến**; đây là phạm vi dữ liệu có GPS, không phải toàn bộ 85.410 chuyến.

Các thành phần giao diện:
1. Bộ lọc ngày GPS, tuyến đường và ngưỡng vận tốc thấp do người dùng lựa chọn.
2. Bản đồ nhiệt từ các điểm GPS có vận tốc dưới hoặc bằng ngưỡng đã chọn, tổng hợp theo ô tọa độ.
3. Bản đồ các điểm GPS quan sát được của một chuyến được chọn.
4. Bảng phân tích số chuyến, số chuyến trễ và tỷ lệ trễ theo tuyến; biểu đồ so sánh quy mô chuyến.

**Diễn giải**: vận tốc thấp là tín hiệu cần kiểm tra, không đủ để chứng minh ùn tắc giao thông. Hoạt động bốc dỡ và thời gian chờ tại cơ sở cũng có thể tạo ra các điểm chậm hoặc dừng. Việc phân biệt *dwell-time tại geofence* với *kẹt xe trên đường* cần kiểm tra kết hợp dữ liệu thời gian, geofence và/hoặc dữ liệu giao thông bên ngoài. Phần kết luận điểm nghẽn theo từng vị trí chưa được nghiệm thu nếu chưa có kiểm chứng này.

**Giới hạn**: Bản đồ thể hiện điểm GPS được ghi nhận, không thể coi là đường chạy chính xác trên mạng lưới đường bộ; các cảnh báo về tuyến đường không được suy rộng sang những chuyến không có GPS.

## 4.4 Trang 3 — Kịch bản chẩn đoán bất thường nhiên liệu

Trang nhiên liệu khai thác `dds.Fact_GPS_Points` để xem chuỗi thời gian theo chuyến: mức nhiên liệu (%), vận tốc (km/h), trạng thái động cơ và nhãn gốc đã ghi trong DDS. Người xem có thể chọn một chuyến và kiểm tra các điểm nghi vấn, đồng thời xem danh sách xe có nhãn cần xác minh trên toàn đội xe.

Từ báo cáo đối soát DDS, phân bố nhãn gồm:

| Nhãn ghi nhận | Số điểm |
|---|---:|
| NORMAL | 1.435.491 |
| IDLE_EXTENDED | 36 |
| GPS_JUMP_RECOVERY | 16 |
| FUEL_THEFT | 15 |
| FUEL_RECEIPT_MISMATCH | 13 |

Các nhãn là kết quả mô phỏng/ghi nhận từ pipeline dữ liệu. **Không được diễn giải `FUEL_THEFT` như một bằng chứng đã xảy ra hành vi gian lận thực tế**.

Logic chẩn đoán định hướng kiểm tra ba tình huống:
- Xe đứng yên, động cơ tắt, mức nhiên liệu giảm đột ngột: dấu hiệu cần kiểm tra thất thoát nhiên liệu và chất lượng cảm biến.
- Xe đứng yên, động cơ chạy, mức nhiên liệu giảm: dấu hiệu cần đánh giá tiêu hao do nổ máy chờ.
- Xe di chuyển, mức nhiên liệu giảm bất thường: cần đối chiếu điều kiện tải, quãng đường, giao dịch nhiên liệu và bảo dưỡng trước khi nghi ngờ lỗi kỹ thuật.

Đây mới là **quy tắc diễn giải hỗ trợ chuyên viên**, không phải bộ phân loại tự động đã được kiểm định. Để kết luận nguyên nhân một cách tự động cần có ngưỡng suy giảm nhiên liệu được phê duyệt, nhãn kiểm thử và bằng chứng xác minh.

## 4.5 Đối soát trong phạm vi Task 10–12

Các tập kiểm thử đã được lưu tại `tests/test_overview.py`, `tests/test_geo_fuel.py`, `tests/test_pages_smoke.py`, dự kiến thực thi qua GitHub Actions. Bộ đối soát DDS nguồn xác minh số chuyến, tính duy nhất khóa chuyến, số điểm GPS, tình trạng liên kết GPS và phân bố nhãn đã nêu.

Tại thời điểm soạn thảo, **chưa có bằng chứng độc lập cho thấy toàn bộ test đã chạy PASS trên GitHub Actions hoặc ba trang đã vận hành thành công trên Streamlit Cloud**. Vì vậy, bản thảo này không được dùng để tuyên bố nghiệm thu sản phẩm triển khai cuối cùng.

## 4.6 Tóm tắt mức hoàn thiện

- **Trang 1**: có mã nguồn và công thức nghiệp vụ đối soát; cần kiểm thử tích hợp sau triển khai, nghiệm thu giao diện.
- **Trang 2**: có mã nguồn heatmap, bản đồ chuyến và chỉ số tuyến; cần thẩm định geofence/điểm nghẽn trước khi đưa ra kết luận.
- **Trang 3**: có chuỗi dữ liệu cảm biến và danh sách cảnh báo; còn thiếu bộ phân loại nguyên nhân đã được chuẩn hóa và kiểm thử.

Nguồn dữ liệu: các bảng DDS trong dự án, file đối soát `overview_fact_baseline.json`, `dds_integrity_audit.json`, mã nguồn Dashboard và báo cáo nghiệm thu `QA_TASK10_12.md`. Không có chỉ số mô phỏng thêm trong bản thảo.
