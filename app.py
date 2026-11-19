from datetime import timedelta
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- CẤU HÌNH TRANG & CACHE (Đáp ứng UX Page 5) ---
st.set_page_config(page_title="Hệ Thống Phân Tích Online Retail - Nhóm 10", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('data/cleaned_data.csv', low_memory=False)
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df['CustomerID'] = df['CustomerID'].astype(str)
    df['StockCode'] = df['StockCode'].astype(str)
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

# 1. Bộ lọc Thời gian
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

# 2. Bộ lọc Khu vực (Multiselect)
all_countries = sorted(df['Country'].unique().tolist())
select_all_countries = st.sidebar.checkbox("Chọn tất cả quốc gia", value=True)

if select_all_countries:
    selected_countries = st.sidebar.multiselect("2. Quốc gia:", all_countries, default=all_countries)
else:
    default_top3 = df.groupby('Country')['Revenue'].sum().nlargest(3).index.tolist()
    selected_countries = st.sidebar.multiselect("2. Quốc gia:", all_countries, default=default_top3)

# 3. Bộ lọc Loại khách hàng (Giúp linh hoạt xem tổng doanh thu hoặc chỉ khách có tài khoản)
customer_filter = st.sidebar.radio(
    "3. Phạm vi khách hàng:",
    ["Tất cả (Gồm khách vãng lai)", "Chỉ khách có tài khoản (ID)"],
    index=0
)

# 4. Bộ lọc Đơn giá tối đa (Mặc định = MAX để không cắt ngầm doanh thu)
max_unit_price = float(df['UnitPrice'].max())
price_limit = st.sidebar.slider(
    "4. Lọc theo Đơn giá tối đa (£):",
    min_value=0.0,
    max_value=max_unit_price,
    value=max_unit_price
)

# Áp dụng bộ lọc toàn cục
filtered_df = df[
    (df['Date'] >= start_date) &
    (df['Date'] <= end_date) &
    (df['Country'].isin(selected_countries)) &
    (df['UnitPrice'] <= price_limit)
]

if customer_filter == "Chỉ khách có tài khoản (ID)":
    filtered_df = filtered_df[filtered_df['CustomerID'] != 'Guest']

if filtered_df.empty:
    st.warning("⚠️ Không có dữ liệu khớp với bộ lọc hiện tại. Vui lòng mở rộng điều kiện lọc bên thanh công cụ!")
    st.stop()


# ==========================================
# ĐỊNH NGHĨA CÁC GIAO DIỆN PHÂN TÍCH (PAGES)
# ==========================================

def page_overview(data):
    st.header("📌 1. Tổng Quan Tình Hình Kinh Doanh & EDA")

    total_rev = data['Revenue'].sum()
    total_orders = data['InvoiceNo'].nunique()
    aov = total_rev / total_orders if total_orders > 0 else 0
    total_products = data['StockCode'].nunique()

    # Tính số khách có tài khoản & Tỷ lệ khách quay lại (Repeat Purchase Rate)
    reg_data = data[data['CustomerID'] != 'Guest']
    total_reg_customers = reg_data['CustomerID'].nunique()
    if total_reg_customers > 0:
        orders_per_cust = reg_data.groupby('CustomerID')['InvoiceNo'].nunique()
        repeat_rate = (orders_per_cust > 1).mean() * 100
    else:
        repeat_rate = 0.0

    # Hàng 1: KPI Quy mô
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Tổng Doanh Thu (£)", f"£{total_rev:,.2f}")
    c2.metric("🧾 Tổng Số Đơn Hàng", f"{total_orders:,}")
    c3.metric("📦 Số Mã Sản Phẩm (SKU)", f"{total_products:,}")

    # Hàng 2: KPI Chất lượng
    c4, c5, c6 = st.columns(3)
    c4.metric("🛒 Giá Trị TB/Đơn (AOV)", f"£{aov:,.2f}")
    c5.metric("👥 Khách Hàng Có Tài Khoản", f"{total_reg_customers:,}")
    c6.metric("🔁 Tỷ Lệ Khách Quay Lại", f"{repeat_rate:.1f}%")

    st.markdown("---")

    tab_summary, tab_stat, tab_raw = st.tabs([
        "📊 Tổng hợp theo Nhóm Thị Trường (GroupBy)",
        "📈 Thống kê mô tả (EDA)",
        "🗃️ Dữ liệu chi tiết & Kiểu dữ liệu"
    ])

    with tab_summary:
        col_left, col_right = st.columns([1.3, 1])
        with col_left:
            st.subheader("Bảng tổng hợp theo Thị trường")
            market_grp = data.groupby('Market_Group', as_index=False).agg(
                Tong_Doanh_Thu=('Revenue', 'sum'),
                So_Don_Hang=('InvoiceNo', 'nunique'),
                San_Pham_Ban_Ra=('Quantity', 'sum')
            )
            market_grp['AOV'] = market_grp['Tong_Doanh_Thu'] / market_grp['So_Don_Hang']

            st.dataframe(
                market_grp,
                column_config={
                    "Market_Group": "Nhóm Thị Trường",
                    "Tong_Doanh_Thu": st.column_config.NumberColumn("Tổng Doanh Thu (£)", format="£%.2f"),
                    "So_Don_Hang": st.column_config.NumberColumn("Số Đơn Hàng", format="%d"),
                    "San_Pham_Ban_Ra": st.column_config.NumberColumn("Sản Phẩm Bán Ra", format="%d"),
                    "AOV": st.column_config.NumberColumn("Giá Trị TB/Đơn (£)", format="£%.2f"),
                },
                width="stretch",
                hide_index=True
            )

            # Bảng phụ: Tỷ trọng Khách có tài khoản vs Khách vãng lai
            st.subheader("Cơ cấu Doanh thu theo Loại khách hàng")
            ctype_grp = data.groupby('Customer_Type', as_index=False).agg(
                Doanh_Thu=('Revenue', 'sum'),
                So_Don_Hang=('InvoiceNo', 'nunique')
            )
            ctype_grp['Ty_Trong_%'] = (ctype_grp['Doanh_Thu'] / total_rev * 100).round(1)
            st.dataframe(
                ctype_grp,
                column_config={
                    "Customer_Type": "Loại Khách Hàng",
                    "Doanh_Thu": st.column_config.NumberColumn("Doanh Thu (£)", format="£%.2f"),
                    "So_Don_Hang": st.column_config.NumberColumn("Số Đơn Hàng", format="%d"),
                    "Ty_Trong_%": st.column_config.NumberColumn("Tỷ Trọng (%)", format="%.1f%%"),
                },
                width="stretch",
                hide_index=True
            )

        with col_right:
            fig_pie = px.pie(
                market_grp, values='Tong_Doanh_Thu', names='Market_Group',
                hole=0.45, title="Tỷ trọng doanh thu: Nội địa (UK) vs Quốc tế"
            )
            st.plotly_chart(fig_pie, width="stretch")

    with tab_stat:
        st.subheader("Thống kê mô tả các biến định lượng (Quantity, UnitPrice, Revenue)")
        stat_df = data[['Quantity', 'UnitPrice', 'Revenue']].describe().T.round(2)
        st.dataframe(stat_df, width="stretch")

    with tab_raw:
        c_type, c_sample = st.columns([1, 2])
        with c_type:
            st.write("**Thông tin biến & Kiểu dữ liệu:**")
            dtype_df = pd.DataFrame({'Tên Cột': data.columns, 'Kiểu Dữ Liệu': data.dtypes.astype(str).values})
            st.dataframe(dtype_df, width="stretch", hide_index=True)
        with c_sample:
            st.write("**100 dòng dữ liệu mẫu sau khi lọc:**")
            st.dataframe(data.head(100), width="stretch")


def page_time_trends(data):
    st.header("📈 2. Phân Tích Xu Hướng & Tăng Trưởng Theo Thời Gian")

    col_opt1, col_opt2, col_opt3 = st.columns([1, 1.4, 1.2])
    with col_opt1:
        time_unit = st.selectbox("Chu kỳ thời gian:", ["Theo Tháng (Year-Month)", "Theo Ngày (Date)"])
    with col_opt2:
        chart_mode = st.radio(
            "Kiểu biểu đồ tổng hợp:",
            ["Đường xu hướng (Line)", "Cột chồng (Stacked Bar)", "Cột nhóm (Grouped Bar)"],
            horizontal=True
        )
    with col_opt3:
        exclude_dec = st.checkbox(
            "Loại trừ tháng 12/2011 (chưa đủ ngày)",
            value=False,
            help="Dữ liệu chỉ ghi nhận đến ngày 09/12/2011 nên tổng doanh thu tháng 12/2011 bị thấp giả tạo."
        )

    time_data = data[data['YearMonth'] != '2011-12'] if exclude_dec else data
    if time_data.empty:
        st.warning("⚠️ Bộ lọc thời gian hiện tại chỉ nằm trong tháng 12/2011. Hãy bỏ tích tùy chọn loại trừ tháng 12/2011.")
        return

    if not exclude_dec and '2011-12' in time_data['YearMonth'].unique() and "Tháng" in time_unit:
        st.info("ℹ️ **Lưu ý phân tích:** Tháng **2011-12** chỉ có dữ liệu đến ngày **09/12/2011** (9 ngày), do đó điểm cuối biểu đồ giảm mạnh không phải do sụt giảm kinh doanh thực tế. Bạn có thể tích chọn loại trừ ở góc trên bên phải để xem xu hướng chuẩn.")

    time_col = 'YearMonth' if "Tháng" in time_unit else 'Date'

    if chart_mode == "Đường xu hướng (Line)":
        trend_df = time_data.groupby(time_col, as_index=False)['Revenue'].sum()
        fig_time = px.line(
            trend_df, x=time_col, y='Revenue', markers=True,
            labels={'Revenue': 'Doanh thu (£)', time_col: 'Thời gian'},
            title=f"Xu hướng tổng doanh thu ({time_unit})"
        )
    else:
        trend_grp = time_data.groupby([time_col, 'Market_Group'], as_index=False)['Revenue'].sum()
        barmode = 'stack' if "Stacked" in chart_mode else 'group'
        fig_time = px.bar(
            trend_grp, x=time_col, y='Revenue', color='Market_Group',
            barmode=barmode,
            labels={'Revenue': 'Doanh thu (£)', time_col: 'Thời gian'},
            title=f"Biểu đồ tổng hợp doanh thu theo thị trường ({chart_mode})"
        )
    st.plotly_chart(fig_time, width="stretch")

    # Biểu đồ tốc độ tăng trưởng MoM (%) khi xem theo tháng
    if "Tháng" in time_unit:
        monthly_rev = time_data.groupby('YearMonth', as_index=False)['Revenue'].sum().sort_values('YearMonth')
        if len(monthly_rev) >= 2:
            monthly_rev['MoM_Growth_%'] = monthly_rev['Revenue'].pct_change() * 100
            mom_df = monthly_rev.dropna(subset=['MoM_Growth_%']).copy()
            mom_df['Trang_Thai'] = np.where(mom_df['MoM_Growth_%'] >= 0, 'Tăng trưởng (+)', 'Sụt giảm (-)')

            fig_mom = px.bar(
                mom_df, x='YearMonth', y='MoM_Growth_%', color='Trang_Thai',
                color_discrete_map={'Tăng trưởng (+)': '#2ca02c', 'Sụt giảm (-)': '#d62728'},
                text=mom_df['MoM_Growth_%'].map(lambda v: f"{v:+.1f}%"),
                labels={'YearMonth': 'Tháng', 'MoM_Growth_%': 'Tăng trưởng MoM (%)'},
                title="Tốc độ tăng trưởng doanh thu so với tháng liền trước (MoM %)"
            )
            fig_mom.update_traces(textposition='outside')
            st.plotly_chart(fig_mom, width="stretch")

    st.subheader("🔥 Tần suất mua sắm theo Khung giờ và Thứ trong tuần")
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = (
        time_data.pivot_table(index='DayOfWeek', columns='Hour', values='InvoiceNo', aggfunc='nunique')
        .reindex(days_order)
        .fillna(0)
    )
    fig_heat = px.imshow(
        heatmap_data, aspect="auto", color_continuous_scale="YlGnBu",
        labels=dict(x="Giờ trong ngày (h)", y="Thứ trong tuần", color="Số đơn hàng"),
        title="Mật độ đơn hàng theo Giờ và Thứ"
    )
    st.plotly_chart(fig_heat, width="stretch")


def page_distribution(data):
    st.header("📊 3. Phân Tích Phân Phối & Ngoại Lệ (Histogram & Boxplot)")
    st.caption("Trực quan hóa phân phối giá trị đơn hàng kèm đường Trung bình (Mean) và Trung vị (Median) để nhận diện độ lệch và đơn hàng sỉ.")

    order_df = data.groupby(['InvoiceNo', 'Country', 'Market_Group'], as_index=False).agg(
        Order_Value=('Revenue', 'sum'),
        Total_Items=('Quantity', 'sum')
    )

    quantile_cutoff = st.slider(
        "Chọn ngưỡng phần trăm dữ liệu hiển thị (Lọc bớt cực trị để nhìn rõ phân phối):",
        80, 100, 95
    )
    val_limit = order_df['Order_Value'].quantile(quantile_cutoff / 100.0)
    filtered_orders = order_df[order_df['Order_Value'] <= val_limit]

    mean_val = filtered_orders['Order_Value'].mean()
    median_val = filtered_orders['Order_Value'].median()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Biểu đồ Histogram (Kèm Mean & Median)")
        fig_hist = px.histogram(
            filtered_orders, x='Order_Value', nbins=40, color='Market_Group',
            barmode='overlay', opacity=0.72,
            labels={'Order_Value': 'Giá trị đơn hàng (£)'},
            title=f"Phân phối Giá trị đơn hàng (Dưới mức £{val_limit:,.0f})"
        )
        fig_hist.add_vline(
            x=mean_val, line_dash="dash", line_color="red",
            annotation_text=f"Mean: £{mean_val:,.0f}", annotation_position="top right"
        )
        fig_hist.add_vline(
            x=median_val, line_dash="dot", line_color="green",
            annotation_text=f"Median: £{median_val:,.0f}", annotation_position="top left"
        )
        st.plotly_chart(fig_hist, width="stretch")

    with col2:
        st.subheader("2. Biểu đồ Boxplot")
        top_c = filtered_orders['Country'].value_counts().nlargest(8).index
        box_data = filtered_orders[filtered_orders['Country'].isin(top_c)]
        fig_box = px.box(
            box_data, x='Country', y='Order_Value', color='Country',
            points="outliers",
            labels={'Order_Value': 'Giá trị đơn hàng (£)', 'Country': 'Quốc gia'},
            title="Phân phối & Ngoại lệ (Outliers) tại Top 8 Quốc gia"
        )
        st.plotly_chart(fig_box, width="stretch")


def page_regional(data):
    st.header("🌍 4. Phân Tích Hiệu Quả Theo Khu Vực (Quốc Gia)")

    c_opt1, c_opt2 = st.columns([1.2, 1])
    with c_opt1:
        include_uk = st.checkbox("Bao gồm Vương quốc Anh (United Kingdom) trong biểu đồ so sánh", value=False)
    with c_opt2:
        rank_metric = st.radio(
            "Xếp hạng biểu đồ theo:",
            ["Tổng Doanh Thu (£)", "Giá Trị TB/Đơn - AOV (£)"],
            horizontal=True
        )

    reg_data = data if include_uk else data[data['Country'] != 'United Kingdom']
    if reg_data.empty:
        st.info("Dữ liệu hiện tại chỉ có United Kingdom. Đang hiển thị United Kingdom.")
        reg_data = data

    country_summary = reg_data.groupby('Country', as_index=False).agg(
        Revenue=('Revenue', 'sum'),
        Orders=('InvoiceNo', 'nunique'),
        Customers=('CustomerID', lambda s: s[s != 'Guest'].nunique())
    )
    country_summary['AOV'] = country_summary['Revenue'] / country_summary['Orders']

    sort_col = 'Revenue' if "Tổng Doanh Thu" in rank_metric else 'AOV'
    country_summary = country_summary.sort_values(by=sort_col, ascending=False)

    col1, col2 = st.columns([1.45, 1])
    with col1:
        fig_bar = px.bar(
            country_summary.head(15), x='Country', y=sort_col, color=sort_col,
            color_continuous_scale='Viridis',
            labels={sort_col: rank_metric, 'Country': 'Quốc gia'},
            title=f"Top 15 Quốc gia dẫn đầu theo {rank_metric}"
        )
        st.plotly_chart(fig_bar, width="stretch")

    with col2:
        st.subheader("Bảng xếp hạng Khu vực (Kèm AOV)")
        st.dataframe(
            country_summary,
            column_config={
                "Country": "Quốc gia",
                "Revenue": st.column_config.NumberColumn("Doanh thu (£)", format="£%.2f"),
                "Orders": st.column_config.NumberColumn("Số đơn", format="%d"),
                "Customers": st.column_config.NumberColumn("Khách (ID)", format="%d"),
                "AOV": st.column_config.NumberColumn("AOV (£/Đơn)", format="£%.2f"),
            },
            width="stretch",
            hide_index=True
        )


def page_products(data):
    st.header("🛍️ 5. Phân Tích Sản Phẩm, Quy Luật Pareto (80/20) & Pivot Table")

    col1, col2 = st.columns([2, 1])
    with col1:
        top_n = st.slider("Chọn số lượng Top sản phẩm hiển thị:", 5, 30, 10)
    with col2:
        metric_choice = st.selectbox("Tiêu chí xếp hạng:", ["Doanh thu cao nhất (£)", "Số lượng bán nhiều nhất (Cái)"])

    sort_col = 'Revenue' if "Doanh thu" in metric_choice else 'Quantity'

    all_prods = data.groupby(['StockCode', 'Description'], as_index=False).agg(
        Revenue=('Revenue', 'sum'),
        Quantity=('Quantity', 'sum'),
        Orders=('InvoiceNo', 'nunique')
    )
    top_prod_df = all_prods.sort_values(by=sort_col, ascending=False).head(top_n)

    fig_prod = px.bar(
        top_prod_df, x=sort_col, y='Description', orientation='h', color=sort_col,
        color_continuous_scale='Blues',
        labels={'Revenue': 'Doanh thu (£)', 'Quantity': 'Số lượng bán', 'Description': 'Sản phẩm'},
        title=f"Top {top_n} Sản phẩm theo {metric_choice}"
    )
    fig_prod.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_prod, width="stretch")

    # Phân tích Pareto 80/20 trên toàn bộ danh mục sản phẩm đang lọc
    st.markdown("---")
    st.subheader("📐 Kiểm chứng Quy luật Pareto (80/20) trên Danh mục Sản phẩm")
    pareto_df = all_prods.sort_values(by='Revenue', ascending=False).reset_index(drop=True)
    pareto_df['Cum_Revenue_Pct'] = pareto_df['Revenue'].cumsum() / pareto_df['Revenue'].sum() * 100
    pareto_df['Product_Rank_Pct'] = (pareto_df.index + 1) / len(pareto_df) * 100

    prods_for_80 = int((pareto_df['Cum_Revenue_Pct'] <= 80.0).sum()) + 1
    prods_for_80 = min(prods_for_80, len(pareto_df))
    pct_prods_for_80 = prods_for_80 / len(pareto_df) * 100

    st.info(
        f"💡 **Kết quả Pareto thực tế:** Chỉ **{prods_for_80:,} / {len(pareto_df):,} mã sản phẩm** "
        f"(tương đương **{pct_prods_for_80:.1f}%** danh mục) đã tạo ra **80% tổng doanh thu**."
    )

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Scatter(
        x=pareto_df['Product_Rank_Pct'], y=pareto_df['Cum_Revenue_Pct'],
        mode='lines', name='Doanh thu tích lũy (%)', line=dict(color='#1f77b4', width=3)
    ))
    fig_pareto.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Mốc 80% doanh thu")
    fig_pareto.add_vline(x=pct_prods_for_80, line_dash="dot", line_color="green", annotation_text=f"{pct_prods_for_80:.1f}% sản phẩm")
    fig_pareto.update_layout(
        title="Đường cong Pareto: Tỷ lệ Sản phẩm (%) vs Tỷ lệ Doanh thu tích lũy (%)",
        xaxis_title="Tỷ lệ tích lũy số lượng mã sản phẩm (%)",
        yaxis_title="Tỷ lệ tích lũy doanh thu (%)",
        height=380
    )
    st.plotly_chart(fig_pareto, width="stretch")

    # Pivot Table & Heatmap
    st.markdown("---")
    st.subheader("📋 Bảng Pivot Table: Doanh thu (£) của Top 10 Sản phẩm qua các Tháng")
    top10_codes = all_prods.sort_values(by='Revenue', ascending=False).head(10)['StockCode'].tolist()
    pivot_source = data[data['StockCode'].isin(top10_codes)]

    pivot_tbl = pd.pivot_table(
        pivot_source, values='Revenue', index='Description',
        columns='YearMonth', aggfunc='sum', fill_value=0
    ).round(0)

    st.dataframe(pivot_tbl, width="stretch")

    fig_pivot = px.imshow(
        pivot_tbl, aspect="auto", color_continuous_scale="Blues",
        labels=dict(x="Tháng - Năm", y="Sản phẩm", color="Doanh thu (£)"),
        title="Biểu đồ nhiệt (Heatmap) từ Pivot Table Doanh thu Sản phẩm theo Tháng"
    )
    st.plotly_chart(fig_pivot, width="stretch")


def classify_rfm_segment(row):
    r, f = row['R_Score'], row['F_Score']
    if r >= 4 and f >= 4:
        return "Champions (VIP)"
    if r >= 3 and f >= 3:
        return "Loyal (Trung thành)"
    if r >= 4 and f <= 2:
        return "New / Potential (Mới & Tiềm năng)"
    if r <= 2 and f >= 3:
        return "At Risk (Nguy cơ rời bỏ)"
    return "Hibernating / Lost (Ngủ đông & Đã mất)"


def page_customers_insights(data):
    st.header("🎯 6. Phân Cụm Khách Hàng (RFM) & Đề Xuất Chiến Lược (Insights)")

    # Tách riêng khách có tài khoản cho phân tích RFM
    guest_orders = data[data['CustomerID'] == 'Guest']['InvoiceNo'].nunique()
    rfm_source = data[data['CustomerID'] != 'Guest']

    if guest_orders > 0:
        st.caption(f"ℹ️ Đã tự động tách riêng {guest_orders:,} đơn hàng vãng lai (Guest) không có CustomerID để tính toán RFM chính xác trên tệp khách hàng định danh.")

    if rfm_source.empty:
        st.warning("⚠️ Không có dữ liệu khách hàng có CustomerID trong phạm vi bộ lọc hiện tại.")
        return

    # Snapshot date = ngày lớn nhất + 1 ngày để Recency tối thiểu = 1
    snapshot_date = rfm_source['Date'].max() + timedelta(days=1)
    rfm = rfm_source.groupby('CustomerID', as_index=False).agg(
        Recency=('Date', lambda x: (snapshot_date - x.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('Revenue', 'sum')
    )

    # Chấm điểm RFM an toàn (dùng rank để không lỗi trùng bin khi bộ lọc nhỏ)
    if len(rfm) >= 5:
        rfm['R_Score'] = pd.qcut(rfm['Recency'].rank(method='first'), 5, labels=[5, 4, 3, 2, 1]).astype(int)
        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm['Segment'] = rfm.apply(classify_rfm_segment, axis=1)

        seg_summary = rfm.groupby('Segment', as_index=False).agg(
            So_Khach=('CustomerID', 'count'),
            Tong_Chi_Tieu=('Monetary', 'sum'),
            Recency_TB=('Recency', 'mean'),
            Frequency_TB=('Frequency', 'mean')
        ).sort_values(by='Tong_Chi_Tieu', ascending=False)
        seg_summary['Ty_Trong_DT_%'] = seg_summary['Tong_Chi_Tieu'] / seg_summary['Tong_Chi_Tieu'].sum() * 100

        col_tree, col_tbl = st.columns([1.3, 1])
        with col_tree:
            st.subheader("Bản đồ Phân cụm Khách hàng RFM (Treemap)")
            fig_tree = px.treemap(
                seg_summary, path=['Segment'], values='Tong_Chi_Tieu',
                color='Recency_TB', color_continuous_scale='RdYlGn_r',
                hover_data={'So_Khach': True, 'Ty_Trong_DT_%': ':.1f'},
                title="Quy mô Doanh thu (£) & Số ngày chưa mua lại TB theo Phân khúc"
            )
            st.plotly_chart(fig_tree, width="stretch")

        with col_tbl:
            st.subheader("Chi tiết từng Phân khúc Khách hàng")
            st.dataframe(
                seg_summary,
                column_config={
                    "Segment": "Phân Khúc",
                    "So_Khach": st.column_config.NumberColumn("Số Khách", format="%d"),
                    "Tong_Chi_Tieu": st.column_config.NumberColumn("Doanh Thu (£)", format="£%.0f"),
                    "Ty_Trong_DT_%": st.column_config.NumberColumn("Tỷ Trọng", format="%.1f%%"),
                    "Recency_TB": st.column_config.NumberColumn("Recency TB", format="%.0f ngày"),
                    "Frequency_TB": st.column_config.NumberColumn("Tần Suất TB", format="%.1f đơn"),
                },
                width="stretch",
                hide_index=True
            )
    else:
        rfm['Segment'] = "Khách hàng"

    st.markdown("---")
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.subheader("Top 15 Khách hàng VIP (Đóng góp doanh thu lớn nhất)")
        top_cust = rfm.sort_values(by='Monetary', ascending=False).head(15)
        fig_cust = px.bar(
            top_cust, x='CustomerID', y='Monetary', color='Frequency',
            labels={'Monetary': 'Tổng chi tiêu (£)', 'Frequency': 'Số lần mua'},
            title="Top 15 Khách hàng chi tiêu cao nhất và Tần suất mua hàng"
        )
        st.plotly_chart(fig_cust, width="stretch")

    with col2:
        st.subheader("Tương quan Tần suất mua & Tổng chi tiêu")
        rfm_clean = rfm[rfm['Monetary'] <= rfm['Monetary'].quantile(0.99)]
        fig_scatter = px.scatter(
            rfm_clean, x='Frequency', y='Monetary', color='Segment',
            size='Monetary', hover_data=['CustomerID', 'Recency'],
            labels={'Frequency': 'Tần suất mua (đơn)', 'Monetary': 'Tổng chi tiêu (£)'},
            title="Phân bố RFM của Khách hàng theo Phân khúc"
        )
        st.plotly_chart(fig_scatter, width="stretch")

    # PHẦN 5: TỰ ĐỘNG RÚT RA NHẬN XÉT & INSIGHT TỪ DỮ LIỆU
    st.markdown("---")
    st.subheader("💡 Nhận Xét Tự Động & Gợi Ý Ra Quyết Định (Business Insights)")

    country_rev = data.groupby('Country')['Revenue'].sum()
    top1_country = country_rev.idxmax()
    top1_country_rev = country_rev.max()
    top1_prod = data.groupby('Description')['Revenue'].sum().idxmax()
    peak_hour = data.groupby('Hour')['InvoiceNo'].nunique().idxmax()
    avg_order_val = data['Revenue'].sum() / data['InvoiceNo'].nunique()

    vip_share_text = ""
    if 'Segment' in rfm.columns and (rfm['Segment'] == 'Champions (VIP)').any():
        vip_rev = rfm[rfm['Segment'] == 'Champions (VIP)']['Monetary'].sum()
        vip_cnt = (rfm['Segment'] == 'Champions (VIP)').sum()
        vip_share_text = (
            f"\n    * **Phân khúc Champions (VIP):** Gồm **{vip_cnt:,} khách hàng** "
            f"({vip_cnt/len(rfm)*100:.1f}% tệp khách có ID) nhưng đóng góp tới "
            f"**£{vip_rev:,.2f}** (**{vip_rev/rfm['Monetary'].sum()*100:.1f}%** doanh thu định danh)."
        )

    st.success(f"""
    **1. Phát hiện chính từ dữ liệu đang lọc:**
    * **Thị trường trọng điểm:** Quốc gia mang lại doanh thu số 1 là **{top1_country}** với **£{top1_country_rev:,.2f}** (chiếm **{top1_country_rev/data['Revenue'].sum()*100:.1f}%** tổng doanh thu).
    * **Sản phẩm ngôi sao (Best-seller):** Mặt hàng mang lại doanh thu cao nhất là **"{top1_prod}"**.
    * **Hành vi thời gian & Đơn hàng:** Khung giờ vàng có lượng đơn đặt hàng cao nhất trong ngày là **{peak_hour}:00 giờ**. Giá trị trung bình mỗi đơn hàng (AOV) đạt **£{avg_order_val:,.2f}**.{vip_share_text}

    **2. Gợi ý ra quyết định cho Doanh nghiệp bán lẻ (Recommendations):**
    * **Tối ưu Marketing theo khung giờ:** Gửi email/thông báo đẩy và tung ưu đãi trước khung giờ **{peak_hour}:00 giờ** để đón đầu lưu lượng đặt hàng cao nhất trong ngày.
    * **Quản trị tồn kho & Bán chéo (Cross-selling):** Đảm bảo không đứt gãy tồn kho đối với nhóm sản phẩm chủ lực (như **{top1_prod}**), đồng thời tạo combo ghép hàng bán chạy với sản phẩm biên lợi nhuận cao để kéo AOV vượt mức **£{avg_order_val:,.2f}**.
    * **Chăm sóc theo phân khúc RFM:** Giữ chân nhóm **Champions (VIP)** bằng chính sách chiết khấu khách sỉ riêng; gửi mã giảm giá kích hoạt lại (win-back campaign) cho nhóm **At Risk** trước khi họ rời bỏ hoàn toàn.
    """)


# ==========================================
# BỘ ĐIỀU KHIỂN TRANG LINH HOẠT (DYNAMIC ROUTER)
# ==========================================
PAGES = {
    "1. Tổng quan & Thống kê (EDA)": page_overview,
    "2. Xu hướng & Tăng trưởng (MoM)": page_time_trends,
    "3. Phân phối & Ngoại lệ (Hist/Box)": page_distribution,
    "4. Phân tích Khu vực & AOV": page_regional,
    "5. Sản phẩm, Pareto & Pivot Table": page_products,
    "6. Phân cụm RFM & Insights": page_customers_insights
}

st.sidebar.markdown("---")
selected_page = st.sidebar.radio("📂 Chọn Giao Diện Phân Tích:", list(PAGES.keys()))

PAGES[selected_page](filtered_df)
#python -m streamlit run app.py
