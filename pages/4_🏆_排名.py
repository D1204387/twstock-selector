"""
台股智選系統 - 排名頁面
Taiwan Stock Selection System - Ranking Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_analyzer import calculate_score, get_top_stocks, get_score_grade

st.set_page_config(page_title="排名 - 台股智選系統", page_icon="🏆", layout="wide")

# 灰藍色調 CSS
st.markdown("""
<style>
    .rank-badge { background: #2563eb; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; 
                  font-weight: 600; font-size: 0.85rem; }
    .grade-a { background: #2563eb; color: white; }
    .grade-b { background: #60a5fa; color: white; }
    .grade-c { background: #9ca3af; color: white; }
    .grade-d { background: #d1d5db; color: #374151; }
</style>
""", unsafe_allow_html=True)

st.title("🏆 綜合排名")
st.caption("根據綜合評分系統，找出最優質的股票")

@st.cache_data(ttl=3600)
def load_data():
    df = get_stock_list()
    if df.empty or 'roe' not in df.columns:
        df = generate_sample_data()
    return df

df = load_data()

# 評分說明
with st.expander("評分系統說明"):
    st.markdown("""
    **權重：** ROE (40%) | PE (30%) | PB (15%) | 負債率 (15%)  
    **等級：** A+ (9-10) | A (8-9) | B+ (7-8) | B (6-7) | C (5-6) | D (3-5) | F (0-3)
    """)

# 篩選
col1, col2, col3 = st.columns(3)
with col1:
    top_n = st.selectbox("顯示數量", [10, 20, 30, 50], index=1)
with col2:
    asset_filter = st.selectbox("資產類型", ["全部", "股票", "ETF"])
with col3:
    industry_options = ["全部"] + (df['industry'].unique().tolist() if 'industry' in df.columns else [])
    industry_filter = st.selectbox("產業別", industry_options)

# 套用篩選
filtered_df = df.copy()
if asset_filter == "股票" and 'asset_type' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['asset_type'] == 'stock']
elif asset_filter == "ETF" and 'asset_type' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['asset_type'] == 'etf']
if industry_filter != "全部" and 'industry' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['industry'] == industry_filter]

top_stocks = get_top_stocks(filtered_df, n=top_n)

st.divider()

# 統計
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("參與排名", f"{len(filtered_df)} 檔")
with col2:
    if not top_stocks.empty:
        st.metric("平均評分", f"{top_stocks['score'].mean():.2f}")
with col3:
    if not top_stocks.empty:
        st.metric("最高評分", f"{top_stocks['score'].max():.2f}")
with col4:
    if not top_stocks.empty:
        st.metric("A級以上", f"{len(top_stocks[top_stocks['score'] >= 8])} 檔")

st.divider()

# 排行榜
st.subheader(f"Top {top_n} 排行榜")

if top_stocks.empty:
    st.warning("沒有可排名的股票")
else:
    display_df = top_stocks.copy()
    display_df['排名'] = range(1, len(display_df) + 1)
    display_df['等級'] = display_df['score'].apply(get_score_grade)
    
    display_cols = ['排名', 'stock_id', 'name', 'industry', 'score', '等級', 'roe', 'pe', 'pb', 'dividend_yield', 'debt_ratio']
    display_cols = [c for c in display_cols if c in display_df.columns or c in ['排名', '等級']]
    result_df = display_df[display_cols].copy()
    
    column_names = {'stock_id': '代號', 'name': '名稱', 'industry': '產業', 'score': '評分',
                    'roe': 'ROE(%)', 'pe': 'PE', 'pb': 'PB', 'dividend_yield': '殖利率(%)', 'debt_ratio': '負債率(%)'}
    result_df = result_df.rename(columns=column_names)
    
    for col in result_df.select_dtypes(include=['float64']).columns:
        result_df[col] = result_df[col].round(2)
    
    st.dataframe(result_df, use_container_width=True, hide_index=True)
    
    st.download_button("匯出 CSV", display_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                       f"top_{top_n}_stocks.csv", "text/csv")
    
    st.divider()
    
    # 圖表
    st.subheader("分析圖表")
    col1, col2 = st.columns(2)
    
    with col1:
        top_10 = display_df.head(10)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top_10['name'], x=top_10['score'], orientation='h',
            marker_color='#2563eb', text=top_10['score'].round(2), textposition='outside'
        ))
        fig.update_layout(title="Top 10 評分", xaxis_title="評分", yaxis=dict(autorange="reversed"),
                         height=400, margin=dict(l=10, r=10, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        grade_counts = display_df['等級'].value_counts()
        fig = px.pie(values=grade_counts.values, names=grade_counts.index, title="等級分布", hole=0.4)
        fig.update_traces(textposition='inside', textinfo='percent+label',
                         marker=dict(colors=['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#9ca3af', '#d1d5db']))
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # 個股明細
    with st.expander("查看個股評分明細"):
        selected = st.selectbox("選擇股票", display_df['stock_id'].tolist(),
                               format_func=lambda x: f"{x} - {display_df[display_df['stock_id']==x]['name'].values[0]}")
        if selected:
            stock = display_df[display_df['stock_id'] == selected].iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("ROE", f"{stock.get('roe', 0):.2f}%")
            with c2: st.metric("PE", f"{stock.get('pe', 0):.2f}")
            with c3: st.metric("PB", f"{stock.get('pb', 0):.2f}")
            with c4: st.metric("負債率", f"{stock.get('debt_ratio', 0):.2f}%")
