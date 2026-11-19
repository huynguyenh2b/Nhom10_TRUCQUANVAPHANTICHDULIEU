import pandas as pd
import numpy as np

# Danh sách các mã không phải sản phẩm thực tế (phí vận chuyển, chiết khấu, phí ngân hàng...)
NON_PRODUCT_CODES = {
    'POST', 'DOT', 'M', 'BANK CHARGES', 'D', 'CRUK',
    'AMAZONFEE', 'S', 'PADS', 'C2', 'B', 'ADJUST', 'ADJUST2'
}

def process_data():
    print("1. Đang đọc dữ liệu gốc từ data/data.csv...")
    df = pd.read_csv('data/data.csv', encoding='ISO-8859-1')
    initial_rows = df.shape[0]
    print(f"-> Kích thước ban đầu: {initial_rows:,} dòng, {df.shape[1]} cột")

    print("\n2. Đang làm sạch dữ liệu (EDA)...")
    # 2.1. Xóa các dòng trùng lặp hoàn toàn
    dup_count = df.duplicated().sum()
    df = df.drop_duplicates()
    print(f"-> Đã loại bỏ {dup_count:,} dòng trùng lặp.")

    # 2.2. Loại bỏ giao dịch hủy (InvoiceNo bắt đầu bằng 'C') và giá trị Quantity/UnitPrice <= 0
    df['InvoiceNo'] = df['InvoiceNo'].astype(str).str.strip()
    df = df[~df['InvoiceNo'].str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]

    # 2.3. Chuẩn hóa StockCode và loại bỏ các mã phí dịch vụ không phải hàng hóa
    df['StockCode'] = df['StockCode'].astype(str).str.strip().str.upper()
    non_prod_mask = df['StockCode'].isin(NON_PRODUCT_CODES)
    print(f"-> Đã loại bỏ {non_prod_mask.sum():,} dòng phí dịch vụ (POST, DOT, M, BANK CHARGES...).")
    df = df[~non_prod_mask]

    # 2.4. Loại bỏ dòng thiếu tên sản phẩm
    df = df.dropna(subset=['Description'])
    df['Description'] = df['Description'].astype(str).str.strip().str.upper()

    # 2.5. Chuẩn hóa tên sản phẩm: mỗi StockCode chỉ gắn với 1 Description phổ biến nhất
    canonical_desc = (
        df.groupby('StockCode')['Description']
        .agg(lambda s: s.value_counts().index[0])
    )
    df['Description'] = df['StockCode'].map(canonical_desc)

    # 2.6. Giữ lại giao dịch khách vãng lai (Guest) để không làm hụt ~25% tổng doanh thu
    df['CustomerID'] = df['CustomerID'].apply(
        lambda x: str(int(x)) if pd.notna(x) else 'Guest'
    )
    df['Customer_Type'] = np.where(df['CustomerID'] == 'Guest', 'Khách vãng lai (Guest)', 'Khách có tài khoản')

    print("\n3. Đang tạo các biến đặc trưng mới (Feature Engineering)...")
    # Doanh thu (đơn vị chuẩn của bộ dữ liệu UK là Bảng Anh - £)
    df['Revenue'] = df['Quantity'] * df['UnitPrice']

    # Xử lý thời gian
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Date'] = df['InvoiceDate'].dt.date
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
    df['Month'] = df['InvoiceDate'].dt.month
    df['Year'] = df['InvoiceDate'].dt.year
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()

    # Phân nhóm thị trường
    df['Market_Group'] = np.where(df['Country'] == 'United Kingdom', 'United Kingdom', 'International')

    output_path = 'data/cleaned_data.csv'
    df.to_csv(output_path, index=False)

    print(f"\n=> HOÀN TẤT! Đã lưu dữ liệu sạch tại: {output_path}")
    print(f"-> Kích thước sau làm sạch: {df.shape[0]:,} dòng (Giữ lại {(df.shape[0]/initial_rows)*100:.1f}% dữ liệu gốc)")
    print(f"-> Tổng doanh thu chuẩn hóa: £{df['Revenue'].sum():,.2f}")

if __name__ == "__main__":
    process_data()
    #python eda_processing.py