import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CẤU HÌNH TRANG & CACHE (Đáp ứng UX Page 5) ---
st.set_page_config(page_title="Hệ Thống Phân Tích Online Retail - Nhóm 10", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('data/cleaned_data.csv')
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df['CustomerID'] = df['CustomerID'].astype(str)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ Không tìm thấy file 'data/cleaned_data.csv'. Vui lòng chạy lệnh `python eda_processing.py` trong Terminal trước!")
    st.stop()

# ==========================================
# SIDEBAR: ĐIỀU HƯỚNG LINH HOẠT & BỘ LỌC CHUNG
# ==========================================
st.sidebar.title("🧭 ĐIỀU HƯỚNG & BỘ LỌC")

# 1. Bộ lọc Thời gian (Slider / Date Input)
min_date = df['Date'].min()
max_date = df['Date'].max()
date_range = st.sidebar.date_input(
    "1. Khoảng thời gian:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0] if isinstance(date_range, tuple) else date_range

# 2. Bộ lọc Khu vực (Multiselect) với tùy chọn Chọn tất cả
all_countries = sorted(df['Country'].unique().tolist())
select_all_countries = st.sidebar.checkbox("Chọn tất cả quốc gia", value=True)

if select_all_countries:
    selected_countries = st.sidebar.multiselect("2. Quốc gia:", all_countries, default=all_countries)
else:
    default_top3 = df.groupby('Country')['Revenue'].sum().nlargest(3).index.tolist()
    selected_countries = st.sidebar.multiselect("2. Quốc gia:", all_countries, default=default_top3)

# 3. Bộ lọc Giá trị đơn giá
max_price = float(df['UnitPrice'].quantile(0.99))
price_limit = st.sidebar.slider("3. Lọc theo Đơn giá tối đa ($):", 0.0, float(df['UnitPrice'].max()), max_price)

# Áp dụng bộ lọc toàn cục
filtered_df = df[
    (df['Date'] >= start_date) & 
    (df['Date'] <= end_date) & 
    (df['Country'].isin(selected_countries)) &
    (df['UnitPrice'] <= price_limit)
]

if filtered_df.empty:
    st.warning("⚠️ Không có dữ liệu khớp với bộ lọc hiện tại. Vui lòng mở rộng điều kiện lọc bên thanh công cụ!")
    st.stop()


# ==========================================
# ĐỊNH NGHĨA CÁC GIAO DIỆN PHÂN TÍCH (PAGES)
# ==========================================

def page_overview(data):
    st.header("📌 1. Tổng Quan Tình Hình Kinh Doanh & EDA")
    
    col1, col2, col3, col4 = st.columns(4)
    total_rev = data['Revenue'].sum()
    total_orders = data['InvoiceNo'].nunique()
    total_customers = data['CustomerID'].nunique()
    total_products = data['StockCode'].nunique()
    
    col1.metric("💰 Tổng Doanh Thu ($)", f"${total_rev:,.2f}")
    col2.metric("🧾 Tổng Số Đơn Hàng", f"{total_orders:,}")
    col3.metric("👥 Số Khách Hàng", f"{total_customers:,}")
    col4.metric("📦 Số Mã Sản Phẩm", f"{total_products:,}")
    
    st.markdown("---")
    
    tab_summary, tab_stat, tab_raw = st.tabs([
        "📊 Tổng hợp theo Nhóm Thị Trường (GroupBy)", 
        "📈 Thống kê mô tả (EDA)", 
        "🗃️ Dữ liệu chi tiết & Kiểu dữ liệu"
    ])
    
    with tab_summary:
        col_left, col_right = st.columns([1.2, 1])
        with col_left:
            st.subheader("Bảng tổng hợp theo Thị trường")
            market_grp = data.groupby('Market_Group').agg(
                Tong_Doanh_Thu=('Revenue', 'sum'),
                So_Don_Hang=('InvoiceNo', 'nunique'),
                So_Khach_Hang=('CustomerID', 'nunique'),
                San_Pham_Ban_Ra=('Quantity', 'sum')
            ).reset_index()
            
            st.dataframe(
                market_grp,
                column_config={
                    "Market_Group": "Nhóm Thị Trường",
                    "Tong_Doanh_Thu": st.column_config.NumberColumn("Tổng Doanh Thu ($)", format="$%.2f"),
                    "So_Don_Hang": st.column_config.NumberColumn("Số Đơn Hàng", format="%d"),
                    "So_Khach_Hang": st.column_config.NumberColumn("Số Khách Hàng", format="%d"),
                    "San_Pham_Ban_Ra": st.column_config.NumberColumn("Sản Phẩm Bán Ra", format="%d"),
                },
                width="stretch",
                hide_index=True
            )
            
        with col_right:
            fig_pie = px.pie(
                market_grp, values='Tong_Doanh_Thu', names='Market_Group', 
                hole=0.4, title="Tỷ trọng doanh thu: Nội địa (UK) vs Quốc tế"
            )
            st.plotly_chart(fig_pie, width="stretch")
            
    with tab_stat:
        st.subheader("Thống kê mô tả các biến định lượng (Quantity, UnitPrice, Revenue)")
        stat_df = data[['Quantity', 'UnitPrice', 'Revenue']].describe().T.round(2)
        st.dataframe(stat_df, width="stretch")
        
    with tab_raw:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("**Thông tin biến & Kiểu dữ liệu:**")
            dtype_df = pd.DataFrame({'Tên Cột': data.columns, 'Kiểu Dữ Liệu': data.dtypes.astype(str).values})
            st.dataframe(dtype_df, width="stretch", hide_index=True)
        with c2:
            st.write("**100 dòng dữ liệu mẫu sau khi lọc:**")
            st.dataframe(data.head(100), width="stretch")


def page_time_trends(data):
    st.header("📈 2. Phân Tích Xu Hướng & Biểu Đồ Tổng Hợp Theo Thời Gian")
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        time_unit = st.selectbox("Chọn chu kỳ thời gian:", ["Theo Tháng (Year-Month)", "Theo Ngày (Date)"])
    with col_opt2:
        chart_mode = st.radio("Kiểu biểu đồ tổng hợp:", ["Đường xu hướng (Line)", "Cột chồng (Stacked Bar)", "Cột nhóm (Grouped Bar)"], horizontal=True)
    
    time_col = 'YearMonth' if "Tháng" in time_unit else 'Date'
    
    if chart_mode == "Đường xu hướng (Line)":
        trend_df = data.groupby(time_col)['Revenue'].sum().reset_index()
        fig_time = px.line(trend_df, x=time_col, y='Revenue', markers=True, title=f"Xu hướng tổng doanh thu ({time_unit})")
    else:
        trend_grp = data.groupby([time_col, 'Market_Group'])['Revenue'].sum().reset_index()
        barmode = 'stack' if "Stacked" in chart_mode else 'group'
        fig_time = px.bar(
            trend_grp, x=time_col, y='Revenue', color='Market_Group', 
            barmode=barmode, title=f"Biểu đồ tổng hợp doanh thu theo thị trường ({chart_mode})"
        )
    st.plotly_chart(fig_time, width="stretch")
    
    st.subheader("🔥 Tần suất mua sắm theo Khung giờ và Thứ trong tuần")
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = data.pivot_table(index='DayOfWeek', columns='Hour', values='InvoiceNo', aggfunc='nunique').reindex(days_order).fillna(0)
    
    fig_heat = px.imshow(
        heatmap_data, aspect="auto", color_continuous_scale="YlGnBu",
        labels=dict(x="Giờ trong ngày (h)", y="Thứ trong tuần", color="Số đơn hàng"),
        title="Mật độ đơn hàng theo Giờ và Thứ"
    )
    st.plotly_chart(fig_heat, width="stretch")


def page_distribution(data):
    st.header("📊 3. Phân Tích Phân Phối & Ngoại Lệ (Histogram & Boxplot)")
    st.caption("Trang này đáp ứng yêu cầu bắt buộc về Biểu đồ phân phối (Histogram / Boxplot) tại Phần 3 của Bài tập lớn.")
    
    # Tính giá trị từng đơn hàng
    order_df = data.groupby(['InvoiceNo', 'Country', 'Market_Group'], as_index=False).agg(
        Order_Value=('Revenue', 'sum'),
        Total_Items=('Quantity', 'sum')
    )
    
    quantile_cutoff = st.slider("Chọn ngưỡng phần trăm dữ liệu hiển thị (Lọc bớt cực trị để nhìn rõ phân phối):", 80, 100, 95)
    val_limit = order_df['Order_Value'].quantile(quantile_cutoff / 100.0)
    filtered_orders = order_df[order_df['Order_Value'] <= val_limit]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Biểu đồ Histogram")
        # Đã bỏ marginal="rug" để tránh treo trình duyệt khi vẽ 20.000 đơn hàng
        fig_hist = px.histogram(
            filtered_orders, x='Order_Value', nbins=40, color='Market_Group',
            barmode='overlay', opacity=0.75,
            title=f"Phân phối Giá trị đơn hàng (Dưới mức ${val_limit:,.0f})"
        )
        st.plotly_chart(fig_hist, width="stretch")
        
    with col2:
        st.subheader("2. Biểu đồ Boxplot")
        top_c = filtered_orders['Country'].value_counts().nlargest(8).index
        box_data = filtered_orders[filtered_orders['Country'].isin(top_c)]
        # Chỉ hiển thị các điểm ngoại lệ (outliers) thay vì toàn bộ điểm để tải tức thì
        fig_box = px.box(
            box_data, x='Country', y='Order_Value', color='Country',
            points="outliers",
            title="Phân phối và Ngoại lệ (Outliers) Giá trị đơn hàng tại Top Quốc gia"
        )
        st.plotly_chart(fig_box, width="stretch")


def page_regional(data):
    st.header("🌍 4. Phân Tích Hiệu Quả Theo Khu Vực (Quốc Gia)")
    
    include_uk = st.checkbox("Bao gồm Vương quốc Anh (United Kingdom) trong biểu đồ so sánh", value=False)
    reg_data = data if include_uk else data[data['Country'] != 'United Kingdom']
    
    if reg_data.empty:
        st.info("Dữ liệu hiện tại chỉ có United Kingdom. Hãy tích vào ô bên trên để xem.")
        reg_data = data
        
    country_summary = reg_data.groupby('Country').agg(
        Revenue=('Revenue', 'sum'),
        Orders=('InvoiceNo', 'nunique'),
        Customers=('CustomerID', 'nunique')
    ).reset_index().sort_values(by='Revenue', ascending=False)
    
    col1, col2 = st.columns([1.5, 1])
    with col1:
        fig_bar = px.bar(
            country_summary.head(15), x='Country', y='Revenue', color='Revenue',
            color_continuous_scale='Viridis', title="Top 15 Quốc gia dẫn đầu doanh thu"
        )
        st.plotly_chart(fig_bar, width="stretch")
        
    with col2:
        st.subheader("Bảng xếp hạng Khu vực")
        st.dataframe(
            country_summary,
            column_config={
                "Country": "Quốc gia",
                "Revenue": st.column_config.NumberColumn("Doanh thu ($)", format="$%.2f"),
                "Orders": st.column_config.NumberColumn("Số đơn hàng", format="%d"),
                "Customers": st.column_config.NumberColumn("Khách hàng", format="%d"),
            },
            width="stretch",
            hide_index=True
        )


def page_products(data):
    st.header("🛍️ 5. Phân Tích Sản Phẩm & Bảng Chéo (Pivot Table)")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        top_n = st.slider("Chọn số lượng Top sản phẩm hiển thị:", 5, 30, 10)
    with col2:
        metric_choice = st.selectbox("Tiêu chí xếp hạng:", ["Doanh thu cao nhất ($)", "Số lượng bán nhiều nhất (Cái)"])
        
    sort_col = 'Revenue' if "Doanh thu" in metric_choice else 'Quantity'
    
    prod_df = data.groupby(['StockCode', 'Description']).agg(
        Revenue=('Revenue', 'sum'),
        Quantity=('Quantity', 'sum'),
        Orders=('InvoiceNo', 'nunique')
    ).reset_index().sort_values(by=sort_col, ascending=False).head(top_n)
    
    fig_prod = px.bar(
        prod_df, x=sort_col, y='Description', orientation='h', color=sort_col,
        color_continuous_scale='Blues', title=f"Top {top_n} Sản phẩm theo {metric_choice}"
    )
    fig_prod.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_prod, width="stretch")
    
    st.markdown("---")
    st.subheader("📋 Bảng Pivot Table: Doanh thu ($) của Top 10 Sản phẩm qua các Tháng")
    top10_names = prod_df.head(10)['Description'].tolist()
    pivot_source = data[data['Description'].isin(top10_names)]
    
    pivot_tbl = pd.pivot_table(
        pivot_source, values='Revenue', index='Description', 
        columns='YearMonth', aggfunc='sum', fill_value=0
    ).round(0)
    
    st.dataframe(pivot_tbl, width="stretch")
    
    fig_pivot = px.imshow(
        pivot_tbl, aspect="auto", color_continuous_scale="Blues",
        labels=dict(x="Tháng - Năm", y="Sản phẩm", color="Doanh thu ($)"),
        title="Biểu đồ nhiệt (Heatmap) từ Pivot Table Doanh thu Sản phẩm theo Tháng"
    )
    st.plotly_chart(fig_pivot, width="stretch")


def page_customers_insights(data):
    st.header("🎯 6. Phân Tích Hành Vi Khách Hàng (RFM) & Đề Xuất (Insights)")
    st.caption("Trang này giải quyết trọng tâm Đề tài 7 (Hành vi mua sắm, Doanh thu theo khách hàng) và Phần 5 (Nhận xét & Insight).")
    
    snapshot_date = data['Date'].max()
    rfm = data.groupby('CustomerID').agg(
        Recency=('Date', lambda x: (snapshot_date - x.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('Revenue', 'sum')
    ).reset_index()
    
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.subheader("Top 15 Khách hàng VIP (Đóng góp doanh thu lớn nhất)")
        top_cust = rfm.sort_values(by='Monetary', ascending=False).head(15)
        fig_cust = px.bar(
            top_cust, x='CustomerID', y='Monetary', color='Frequency',
            labels={'Monetary': 'Tổng chi tiêu ($)', 'Frequency': 'Số lần mua'},
            title="Top 15 Khách hàng chi tiêu cao nhất và Tần suất mua hàng"
        )
        st.plotly_chart(fig_cust, width="stretch")
        
    with col2:
        st.subheader("Tương quan Tần suất mua & Tổng chi tiêu")
        rfm_clean = rfm[rfm['Monetary'] < rfm['Monetary'].quantile(0.99)]
        fig_scatter = px.scatter(
            rfm_clean, x='Frequency', y='Monetary', color='Recency',
            size='Monetary', hover_data=['CustomerID'],
            title="Phân bố RFM của Khách hàng"
        )
        st.plotly_chart(fig_scatter, width="stretch")
        
    st.markdown("---")
    st.subheader("💡 Nhận Xét Tự Động & Gợi Ý Ra Quyết Định (Business Insights)")
    
    top1_country = data.groupby('Country')['Revenue'].sum().idxmax()
    top1_country_rev = data.groupby('Country')['Revenue'].sum().max()
    top1_prod = data.groupby('Description')['Revenue'].sum().idxmax()
    peak_hour = data.groupby('Hour')['InvoiceNo'].nunique().idxmax()
    avg_order_val = data['Revenue'].sum() / data['InvoiceNo'].nunique()
    
    st.success(f"""
    **1. Phát hiện chính từ dữ liệu đang lọc:**
    * **Thị trường trọng điểm:** Quốc gia mang lại doanh thu số 1 là **{top1_country}** với **${top1_country_rev:,.2f}** (chiếm **{top1_country_rev/data['Revenue'].sum()*100:.1f}%** tổng doanh thu).
    * **Sản phẩm ngôi sao (Best-seller):** Mặt hàng mang lại doanh thu cao nhất là **"{top1_prod}"**.
    * **Hành vi thời gian:** Khung giờ vàng có lượng đơn đặt hàng cao nhất trong ngày là **{peak_hour}:00 giờ**. Giá trị trung bình mỗi đơn hàng (AOV) đạt **${avg_order_val:,.2f}**.
    
    **2. Gợi ý ra quyết định cho Doanh nghiệp bán lẻ (Recommendations):**
    * **Chiến dịch Marketing & Khuyến mãi:** Tập trung gửi email/thông báo đẩy và tung flash-sale vào khung giờ **trước {peak_hour}:00 giờ** để đón đầu lưu lượng truy cập mua sắm lớn nhất.
    * **Quản trị tồn kho & Bán chéo (Cross-selling):** Đảm bảo nguồn cung tồn kho cho nhóm mặt hàng chủ lực như **{top1_prod}** không bị đứt gãy; đồng thời tạo các combo ghép mặt hàng này với các sản phẩm bán chậm hơn để đẩy giá trị đơn hàng trung bình (AOV) vượt mức **${avg_order_val:,.2f}**.
    * **Chăm sóc khách hàng VIP:** Triển khai chính sách chiết khấu riêng cho nhóm Top 15 khách hàng có tần suất mua (Frequency) và tổng chi tiêu (Monetary) cao nhất để giữ chân nhóm khách sỉ này.
    """)


# ==========================================
# BỘ ĐIỀU KHIỂN TRANG LINH HOẠT (DYNAMIC ROUTER)
# ==========================================
PAGES = {
    "1. Tổng quan & Thống kê (EDA)": page_overview,
    "2. Xu hướng & Tổng hợp thời gian": page_time_trends,
    "3. Phân phối & Ngoại lệ (Hist/Box)": page_distribution,
    "4. Phân tích Khu vực (Quốc gia)": page_regional,
    "5. Phân tích Sản phẩm & Pivot Table": page_products,
    "6. Khách hàng (RFM) & Insights": page_customers_insights
}

st.sidebar.markdown("---")
selected_page = st.sidebar.radio("📂 Chọn Giao Diện Phân Tích:", list(PAGES.keys()))

PAGES[selected_page](filtered_df)
#python -m streamlit run app.py