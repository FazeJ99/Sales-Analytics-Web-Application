"""
Customer Segmentation Page - RFM Analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sidebar import create_sidebar

st.set_page_config(page_title="Customer Segments", page_icon="👥", layout="wide")

# --- SIDEBAR COLLAPSE FIX ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* --- SIDEBAR COLLAPSE FIX --- */
    [data-testid="collapsedControl"] { display: none !important; }
    
    .stApp { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); }
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stSidebarNav"] { display: none !important; }
    .block-container { padding: 2rem 3rem !important; }
    
    h1, h2, h3 { color: #ffffff !important; }
    h1 { background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    p, span, label { color: #a0a0a0 !important; }
    
    [data-testid="stMetric"] { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 1rem; }
    [data-testid="stMetricLabel"] { color: #a0a0a0 !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    
    .stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 0.5rem; }
    .stTabs [data-baseweb="tab"] { color: #a0a0a0; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; }
    
    .segment-card { padding: 1.25rem; border-radius: 12px; margin-bottom: 0.75rem; border-left: 4px solid; }
    .champion { background: rgba(16,185,129,0.1); border-color: #10b981; }
    .loyal { background: rgba(99,102,241,0.1); border-color: #6366f1; }
    .new-customer { background: rgba(6,182,212,0.1); border-color: #06b6d4; }
    .at-risk { background: rgba(245,158,11,0.1); border-color: #f59e0b; }
    .lost { background: rgba(239,68,68,0.1); border-color: #ef4444; }
    .potential { background: rgba(139,92,246,0.1); border-color: #8b5cf6; }
    
    .segment-title { color: white; font-weight: 600; font-size: 1rem; margin-bottom: 0.4rem; }
    .segment-text { color: #d1d5db; font-size: 0.9rem; line-height: 1.5; }
    
    hr { border-color: rgba(255,255,255,0.1) !important; }
</style>
""", unsafe_allow_html=True)

CHART_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'font': {'color': '#a0a0a0', 'family': 'Inter'},
    'xaxis': {'gridcolor': 'rgba(255,255,255,0.1)'},
    'yaxis': {'gridcolor': 'rgba(255,255,255,0.1)'},
}

SEGMENT_COLORS = {
    'Champion':     '#10b981',
    'Loyal':        '#6366f1',
    'New Customer': '#06b6d4',
    'At Risk':      '#f59e0b',
    'Lost':         '#ef4444',
    'Potential':    '#8b5cf6',
}

SEGMENT_ACTIONS = {
    'Champion':     'VIP customers. Reward them — early access, loyalty discounts, personal thank-you. Never let them feel ignored.',
    'Loyal':        'Reliable buyers. Keep them happy with consistency. Offer a loyalty programme or upsell slightly higher-value products.',
    'New Customer': 'Just discovered you. Follow up quickly with a welcome offer or complementary product recommendation.',
    'At Risk':      '⚠️ URGENT. Used to buy regularly but gone quiet. Re-engage immediately with a personalised "we miss you" offer.',
    'Lost':         'Bought rarely and not for a long time. One last win-back email, then focus energy elsewhere.',
    'Potential':    'On the fence. A targeted bundle offer or promotion can push them into Loyal.',
}


@st.cache_data(show_spinner=False)
def compute_rfm(df):
    snapshot_date = df['order_date'].max()

    if 'transaction_id' in df.columns:
        freq_col = ('transaction_id', 'nunique')
    else:
        freq_col = ('order_date', 'count')

    rfm = df.groupby('customer_id').agg(
        Recency=('order_date', lambda x: (snapshot_date - x.max()).days),
        Frequency=('order_date', 'count'),
        Monetary=('total_value', 'sum')
    ).reset_index()

    # Score 1-5 (5 = best)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1], duplicates='drop')
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5], duplicates='drop')

    rfm['R_Score'] = rfm['R_Score'].astype(int)
    rfm['F_Score'] = rfm['F_Score'].astype(int)
    rfm['M_Score'] = rfm['M_Score'].astype(int)
    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)

    def assign_segment(row):
        r, f = row['R_Score'], row['F_Score']
        if r >= 4 and f >= 4:   return 'Champion'
        elif r >= 3 and f >= 3: return 'Loyal'
        elif r >= 4 and f <= 2: return 'New Customer'
        elif r <= 2 and f >= 3: return 'At Risk'
        elif r <= 2 and f <= 2: return 'Lost'
        else:                   return 'Potential'

    rfm['Segment'] = rfm.apply(assign_segment, axis=1)
    return rfm


def main():
    create_sidebar()

    st.markdown("<h1>👥 Customer Segmentation</h1>", unsafe_allow_html=True)
    st.caption("Automatically group your customers using RFM analysis — Recency, Frequency and Monetary value.")

    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload your dataset on the Home page.")
        st.stop()

    df = st.session_state['data']

    # Check customer_id exists
    if 'customer_id' not in df.columns:
        st.error("⚠️ No Customer ID column detected in your dataset. RFM analysis requires customer identification. Please ensure your CSV includes a CustomerID column.")
        st.stop()

    st.markdown("---")

    with st.spinner("Calculating RFM scores for all customers..."):
        rfm = compute_rfm(df)

    segment_counts = rfm['Segment'].value_counts()
    total_customers = len(rfm)

    # --- KPI ROW ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Customers", f"{total_customers:,}")
    col2.metric("🏆 Champions", f"{segment_counts.get('Champion', 0):,}")
    col3.metric("⚠️ At Risk", f"{segment_counts.get('At Risk', 0):,}")
    col4.metric("💰 Avg Spend", f"£{rfm['Monetary'].mean():,.2f}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 Segment Overview", "🎯 Action Plan", "🔍 Customer Data"])

    with tab1:
        col_chart, col_breakdown = st.columns([1.2, 1])

        with col_chart:
            st.markdown("### Revenue by Segment")
            segment_revenue = rfm.groupby('Segment')['Monetary'].sum().reset_index()
            segment_revenue.columns = ['Segment', 'Total Revenue']

            fig = px.pie(
                segment_revenue,
                names='Segment',
                values='Total Revenue',
                color='Segment',
                color_discrete_map=SEGMENT_COLORS,
                hole=0.45,
                template='plotly_dark'
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=0, b=0, l=0, r=0),
                legend=dict(font=dict(color='#a0a0a0'))
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_breakdown:
            st.markdown("### Customer Count")
            fig2 = px.bar(
                x=segment_counts.index,
                y=segment_counts.values,
                color=segment_counts.index,
                color_discrete_map=SEGMENT_COLORS,
                labels={'x': 'Segment', 'y': 'Customers'}
            )
            fig2.update_layout(**CHART_THEME, height=320, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # RFM Score Distribution
        st.markdown("### RFM Score Distribution")
        fig3 = px.scatter(
            rfm.sample(min(2000, len(rfm))),
            x='Recency', y='Monetary',
            color='Segment',
            size='Frequency',
            color_discrete_map=SEGMENT_COLORS,
            opacity=0.7,
            labels={'Recency': 'Recency (days since last purchase)', 'Monetary': 'Total Spend (£)'},
            template='plotly_dark'
        )
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=380,
            legend=dict(font=dict(color='#a0a0a0'))
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        st.markdown("### What to do with each segment")
        st.markdown("<br>", unsafe_allow_html=True)

        css_class = {
            'Champion': 'champion',
            'Loyal': 'loyal',
            'New Customer': 'new-customer',
            'At Risk': 'at-risk',
            'Lost': 'lost',
            'Potential': 'potential'
        }

        for segment, action in SEGMENT_ACTIONS.items():
            count = segment_counts.get(segment, 0)
            pct = (count / total_customers * 100) if total_customers > 0 else 0
            css = css_class.get(segment, '')
            st.markdown(f"""
            <div class="segment-card {css}">
                <div class="segment-title">{segment} — {count:,} customers ({pct:.1f}%)</div>
                <div class="segment-text">{action}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### Filter and explore customers")

        selected_segment = st.selectbox(
            "Filter by segment:",
            ['All Segments'] + list(rfm['Segment'].unique())
        )

        display_df = rfm.copy() if selected_segment == 'All Segments' else rfm[rfm['Segment'] == selected_segment].copy()

        display_df['Monetary'] = display_df['Monetary'].apply(lambda x: f"£{x:,.2f}")
        display_df.rename(columns={
            'customer_id': 'Customer ID',
            'Recency': 'Days Since Last Purchase',
            'Frequency': 'Total Orders',
            'Monetary': 'Total Spend',
            'RFM_Score': 'RFM Score'
        }, inplace=True)

        st.dataframe(
            display_df[['Customer ID', 'Days Since Last Purchase', 'Total Orders', 'Total Spend', 'R_Score', 'F_Score', 'M_Score', 'RFM Score', 'Segment']],
            use_container_width=True,
            height=400,
            hide_index=True
        )

        st.markdown("---")
        csv = rfm.to_csv(index=False)
        st.download_button("📥 Download RFM Data", csv, "rfm_segments.csv", "text/csv", use_container_width=False)


if __name__ == "__main__":
    main()
else:
    main()