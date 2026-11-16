# BÀI TẬP LỚN: TRỰC QUAN HÓA VÀ PHÂN TÍCH DỮ LIỆU
**Nhóm thực hiện:** Nhóm 10  
**Đề tài số 7:** Phân tích dữ liệu bán lẻ trực tuyến (Online Retail Dataset)

## 1. Giới thiệu bài toán
Xây dựng hệ thống Dashboard tương tác bằng Python và Streamlit nhằm hỗ trợ doanh nghiệp theo dõi KPI kinh doanh, xu hướng doanh thu theo thời gian, hiệu quả theo khu vực, sản phẩm chủ lực và phân tích hành vi khách hàng (RFM).

## 2. Cấu trúc thư mục
- `data/data.csv`: Dữ liệu gốc (Online Retail).
- `data/cleaned_data.csv`: Dữ liệu đã qua làm sạch và trích xuất đặc trưng.
- `eda_processing.py`: Mã nguồn khám phá, làm sạch dữ liệu (EDA) và tạo biến mới.
- `app.py`: Mã nguồn ứng dụng Dashboard tương tác 6 trang (Streamlit + Plotly).
- `requirements.txt`: Danh sách thư viện Python cần thiết.

## 3. Hướng dẫn cài đặt và chạy ứng dụng
1. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt