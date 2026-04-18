# TravelSDK Documentation

TravelSDK là thư viện Python cung cấp giao diện lập trình hợp nhất cho việc tìm kiếm thông tin vé tàu hỏa, xe khách và máy bay tại Việt Nam. Thư viện được tối ưu cho các hệ thống AI Agent, Chatbot và RAG nhờ vào việc chuẩn hóa dữ liệu đầu ra dưới dạng Pydantic models.

---

## 1. Khởi tạo và Cấu hình

Để bắt đầu, bạn cần khởi tạo `TravelClient` để quản lý việc xác thực token và kết nối HTTP.

### Tham số khởi tạo
```python
from travel import TravelClient

client = TravelClient(
    timeout=30.0,       # Thời gian chờ mặc định
    max_retries=2,      # Số lần thử lại khi lỗi mạng
    verbose=False       # Log debug chi tiết
)
```

Bạn nên sử dụng async context manager để đảm bảo tài nguyên được giải phóng đúng cách:
```python
async with TravelClient() as client:
    # Thực hiện các cuộc gọi API ở đây
    ...
```

---

## 2. Hướng dẫn Tìm kiếm

Tất cả các hàm tìm kiếm đều là async và hỗ trợ định dạng địa điểm linh hoạt như tên thành phố, mã IATA hoặc mã ga tàu.

### 2.1 Tìm kiếm Tàu hỏa
Sử dụng hàm `search_trains` để lấy thông tin từ Đường sắt Việt Nam:
```python
train_tickets = await client.search_trains(
    from_location="Hà Nội",
    to_location="Sài Gòn",
    date="2026-04-20",
    passengers=1,
    sort="fare:asc"
)
```

### 2.2 Tìm kiếm Xe khách
Sử dụng hàm `search_buses` để truy cập mạng lưới hàng trăm nhà xe:
```python
bus_tickets = await client.search_buses(
    from_location="Hà Nội",
    to_location="Đà Nẵng",
    date="2026-04-20"
)
```

### 2.3 Tìm kiếm Máy bay
Sử dụng hàm `search_flights` cho các hãng hàng không nội địa:
```python
flight_tickets = await client.search_flights(
    from_location="HAN",
    to_location="SGN",
    date="2026-04-20",
    fare_class="economy"
)
```

### 2.4 Tìm kiếm Tổng hợp
Hàm `search_all` thực hiện tìm kiếm đồng thời cả 3 phương tiện:
```python
result = await client.search_all("Hà Nội", "Sài Gòn", "2026-04-20")
```

---

## 3. Cấu trúc Dữ liệu

### 3.1 TrainTicket
- `train_number`: Mã tàu SE1, SE3...
- `min_price`: Giá vé thấp nhất hiện tại
- `cars`: Chi tiết từng toa, loại ghế và chỗ trống
- `utilities`: Tiện ích như Wifi, Điều hòa, Ổ cắm
- `images`: Link ảnh minh họa toa tàu

### 3.2 BusTicket
- `operator`: Tên và mã nhà xe
- `bus_type`: Loại xe Limousine, Giường nằm...
- `rating`: Điểm đánh giá trung bình
- `pickup_points`, `dropoff_points`: Danh sách các điểm dừng kèm tọa độ GPS

### 3.3 FlightTicket
- `airline_name`: Tên hãng hàng không
- `flight_number`: Số hiệu chuyến bay
- `airplane_name`: Loại máy bay Airbus, Boeing...
- `baggage_info`: Chi tiết hành lý xách tay và ký gửi
- `is_non_stop`: Trạng thái bay thẳng hoặc nối chuyến

---

## 4. Tiện ích và Tra cứu lịch

### 4.1 Tra cứu Lịch theo tháng
Lấy thông tin giá vé và số lượng chuyến trong một tháng để AI gợi ý ngày đi rẻ nhất:
```python
# Ví dụ lấy lịch tàu hỏa
calendar = await client.get_train_calendar("Hà Nội", "Sài Gòn", month=4, year=2026)
```

### 4.2 Xử lý địa điểm
SDK tự động chuyển đổi tên địa điểm sang mã code tương ứng:
```python
# Tìm sân bay theo tên hoặc mã IATA
airport = client.resolve_flight_airport("tân sơn nhất") 
# Tìm vùng xe khách
region = client.resolve_bus_region("hồ chí minh")
```

---

## 5. Mã mẫu đầy đủ

```python
import asyncio
from travel import TravelClient

async def main():
    async with TravelClient() as client:
        # 1. Tìm kiếm tổng hợp
        result = await client.search_all("Hà Nội", "Sài Gòn", "2026-04-20")
        
        # 2. Lấy thông tin tóm tắt
        summary = result.summary()
        print(f"Summary for AI: {summary}")
        
        # 3. Lấy vé rẻ nhất
        cheapest = result.cheapest()
        print(f"Rẻ nhất: {cheapest.min_price} VND")

        # 4. Tra cứu lịch bay
        calendar = await client.get_flight_calendar("HAN", "SGN", 5, 2026)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Mẫu Dữ liệu Phản hồi

### Train
```json
{
  "train_number": "SE9",
  "min_price": 1055000,
  "utilities": ["Điều hòa", "Ổ cắm điện"],
  "cars": [{"car_number": "1", "car_type": "Ngồi mềm"}]
}
```

### Bus
```json
{
  "operator": { "name": "FUTA HÀ SƠN" },
  "bus_type": "Limousine 34 chỗ",
  "rating": 4.8,
  "policies": ["Có thể hoàn hủy vé"]
}
```

### Flight
```json
{
  "airline_name": "Bamboo Airways",
  "airplane_name": "Airbus A320",
  "baggage_info": "7kg xách tay | 10kg ký gửi",
  "policies": ["Được phép hoàn vé", "Được phép đổi vé"]
}
```

---
*Bản quyền © 2026 TravelSDK Team. Tài liệu dành cho mục đích tích hợp kỹ thuật.*
