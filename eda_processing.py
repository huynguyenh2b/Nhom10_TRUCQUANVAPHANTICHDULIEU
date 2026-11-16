import pandas as pd
import numpy as np

def process_data():
    print("1. Đang đọc dữ liệu gốc từ data/data.csv...")
    df = pd.read_csv('data/data.csv', encoding='ISO-8859-1')
    
    initial_rows, initial_cols = df.shape
    print(f"-> Kích thước ban đầu: {initial_rows:,} dòng, {initial_cols} cột")
    
    print("\n2. Đang kiểm tra và làm sạch dữ liệu (EDA)...")
    # Loại bỏ dòng thiếu CustomerID hoặc Description
    df = df.dropna(subset=['CustomerID', 'Description'])
    
    # Loại bỏ các giao dịch hủy (InvoiceNo bắt đầu bằng 'C') và giá trị âm/bằng 0
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    
    # Xử lý kiểu dữ liệu
    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
    df['Description'] = df['Description'].str.strip()
    
    print("3. Đang tạo các biến đặc trưng mới (Feature Engineering)...")
    # Tính Doanh thu
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    
    # Xử lý thời gian chuyên sâu
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Date'] = df['InvoiceDate'].dt.date
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
    df['Month'] = df['InvoiceDate'].dt.month
    df['Year'] = df['InvoiceDate'].dt.year
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()
    
    # Phân nhóm thị trường (UK chiếm tỷ trọng lớn nên tách riêng để dễ so sánh Stacked/Grouped)
    df['Market_Group'] = np.where(df['Country'] == 'United Kingdom', 'United Kingdom', 'International')
    
    # Lưu dữ liệu sạch
    output_path = 'data/cleaned_data.csv'
    df.to_csv(output_path, index=False)
    
    print(f"\n=> HOÀN TẤT! Đã lưu tại: {output_path}")
    print(f"-> Kích thước sau làm sạch: {df.shape[0]:,} dòng (Đã lọc bỏ {initial_rows - df.shape[0]:,} dòng nhiễu/thiếu)")

if __name__ == "__main__":
    process_data()
  #python eda_processing.py   