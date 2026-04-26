"""
Dashboard Page - Stunning Overview
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sidebar import create_sidebar

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# --- SIDEBAR COLLAPSE FIX ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR COLLAPSE FIX & STRUCTURAL CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Hide sidebar collapse button */
    [data-testid="collapsedControl"] { display: none !important; }
    
    .block-container { padding: 2rem 3rem !important; }
    
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1rem 1.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card);
        border-radius: var(--border-radius);
        padding: 0.5rem;
    }
    
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: 8px !important;
    }
    
    /* Date filter styling */
    .date-filter-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

CHART_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'font': {'color': '#a0a0a0', 'family': 'Inter'},
    'xaxis': {'gridcolor': 'rgba(255,255,255,0.1)', 'linecolor': 'rgba(255,255,255,0.1)'},
    'yaxis': {'gridcolor': 'rgba(255,255,255,0.1)', 'linecolor': 'rgba(255,255,255,0.1)'},
}

def calculate_metrics(df):
    """Calculate key metrics."""
    return {
        'total_rows': len(df),
        'date_range_days': (df['order_date'].max() - df['order_date'].min()).days,
        'unique_products': df['product_name'].nunique(),
        'total_revenue': df['total_value'].sum(),
        'avg_order_value': df['total_value'].mean(),
        'unique_customers': df['customer_id'].nunique() if 'customer_id' in df.columns else None
    }

@st.cache_data
def convert_df(df):
    """Converts the dataframe to CSV format safely without index."""
    return df.to_csv(index=False).encode('utf-8')

def main():
    create_sidebar()
    
    st.markdown("<h1>📊 Sales Dashboard</h1>", unsafe_allow_html=True)
    st.caption("Real-time overview of your sales performance")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please go to the **Home** page to upload your data.")
        st.stop()
    
    df = st.session_state['data']

    # === DATE FILTER ===
    st.markdown('<div class="date-filter-container">', unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        start_date = st.date_input(
            "📅 From",
            value=df['order_date'].min().date(),
            min_value=df['order_date'].min().date(),
            max_value=df['order_date'].max().date()
        )
    with col_f2:
        end_date = st.date_input(
            "📅 To",
            value=df['order_date'].max().date(),
            min_value=df['order_date'].min().date(),
            max_value=df['order_date'].max().date()
        )
    with col_f3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset to Full Range", use_container_width=False):
            start_date = df['order_date'].min().date()
            end_date = df['order_date'].max().date()
    st.markdown('</div>', unsafe_allow_html=True)

    # Apply filter
    df_filtered = df[
        (df['order_date'] >= pd.Timestamp(start_date)) &
        (df['order_date'] <= pd.Timestamp(end_date))
    ]

    if df_filtered.empty:
        st.warning("⚠️ No data in this date range. Try a wider range.")
        st.stop()

    # Show filter info if not full range
    if start_date != df['order_date'].min().date() or end_date != df['order_date'].max().date():
        st.info(f"📅 Showing {len(df_filtered):,} transactions from {start_date} to {end_date}")

    # === METRICS ROW (Using df_filtered) ===
    metrics = calculate_metrics(df_filtered)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Revenue", f"£{metrics['total_revenue']:,.0f}")
    with col2:
        st.metric("🧾 Orders", f"{metrics['total_rows']:,}")
    with col3:
        st.metric("📦 Products", f"{metrics['unique_products']:,}")
    with col4:
        st.metric("💵 Avg Order", f"£{metrics['avg_order_value']:.2f}")
    
    st.markdown("---")
    
    # === TABS (Using df_filtered) ===
    tab1, tab2, tab3 = st.tabs(["📈 Trends", "📅 Time Analysis", "📊 Breakdown"])
    
    with tab1:
        st.markdown("### Revenue Trend")
        
        agg = st.radio("Aggregate by:", ["Daily", "Weekly", "Monthly"], horizontal=True, label_visibility="collapsed")
        agg_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
        
        daily = df_filtered.groupby('order_date')['total_value'].sum().reset_index()
        daily = daily.set_index('order_date').resample(agg_map[agg]).sum().reset_index()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily['order_date'],
            y=daily['total_value'],
            mode='lines',
            name='Revenue',
            line=dict(color='#6366f1', width=3),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)'
        ))
        
        if agg == "Daily" and len(daily) > 7:
            daily['MA'] = daily['total_value'].rolling(7).mean()
            fig.add_trace(go.Scatter(
                x=daily['order_date'],
                y=daily['MA'],
                mode='lines',
                name='7-Day MA',
                line=dict(color='#f59e0b', width=2, dash='dash')
            ))
        
        fig.update_layout(
            **CHART_THEME,
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation='h', y=1.1),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Revenue by Day of Week")
            
            df_copy = df_filtered.copy()
            df_copy['dow'] = df_copy['order_date'].dt.day_name()
            order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow = df_copy.groupby('dow')['total_value'].sum().reindex(order).fillna(0)
            
            fig = px.bar(
                x=dow.index, y=dow.values,
                color=dow.values,
                color_continuous_scale=['#6366f1', '#8b5cf6', '#a78bfa']
            )
            fig.update_layout(**CHART_THEME, height=300, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Revenue by Month")
            
            df_copy = df_filtered.copy()
            df_copy['month'] = df_copy['order_date'].dt.to_period('M').astype(str)
            monthly = df_copy.groupby('month')['total_value'].sum().reset_index()
            
            fig = px.bar(
                monthly, x='month', y='total_value',
                color='total_value',
                color_continuous_scale=['#10b981', '#06b6d4', '#3b82f6']
            )
            fig.update_layout(**CHART_THEME, height=300, showlegend=False, coloraxis_showscale=False, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### Top 10 Products by Revenue")
        
        top = df_filtered.groupby('product_name')['total_value'].sum().sort_values(ascending=True).tail(10)
        
        fig = px.bar(
            x=top.values, y=top.index,
            orientation='h',
            color=top.values,
            color_continuous_scale=['#6366f1', '#8b5cf6']
        )
        fig.update_layout(**CHART_THEME, height=400, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === DATA QUALITY & EXPORT ROW (Using df_filtered) ===
    st.markdown("### 📥 Data Management")
    
    with st.expander("🔍 Data Quality Summary"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Column Info**")
            info = pd.DataFrame({'Column': df_filtered.columns, 'Type': df_filtered.dtypes.astype(str), 'Non-Null': df_filtered.count().values})
            st.dataframe(info, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Statistics**")
            st.dataframe(df_filtered.describe().round(2), use_container_width=True)
            
    with st.expander("💾 Export Cleaned Dataset"):
        st.write("Download your formatted, cleaned dataset based on the selected date range.")
        
        # Call the cached conversion function using the FILTERED data
        csv_data = convert_df(df_filtered)
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="SME_Cleaned_Transactions.csv",
            mime="text/csv",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
else:
    main()