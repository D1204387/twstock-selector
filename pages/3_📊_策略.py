"""
台股智選系統 - 策略篩選頁面
Taiwan Stock Selection System - Strategy Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_screener import apply_strategy, format_strategy_conditions, get_strategy_matches_count
from src.stock_analyzer import calculate_score
from config import STRATEGIES

st.set_page_config(page_title="策略篩選 - 台股智選系統", page_icon="📊", layout="wide")

# 灰藍色調 CSS
st.markdown("""
<style>
    .strategy-card { background: #f9fafb; border: 1px solid #e5e7eb; border-left: 3px solid #2563eb; 
                     border-radius: 6px; padding: 1rem; margin-bottom: 0.5rem; }
    .strategy-card h4 { color: #1f2937; margin: 0 0 0.25rem 0; font-size: 1rem; }
    .strategy-card p { color: #6b7280; margin: 0; font-size: 0.85rem; }
    .strategy-count { color: #2563eb; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("📊 策略篩選")
st.caption("選擇內建投資策略，快速找出符合條件的股票")

@st.cache_data(ttl=3600)
def load_data():
    df = get_stock_list()
    if df.empty or 'roe' not in df.columns:
        df = generate_sample_data()
    return df

df = load_data()
strategy_counts = get_strategy_matches_count(df)

# 策略選擇
st.subheader("選擇策略")

cols = st.columns(4)
for i, (key, strategy) in enumerate(STRATEGIES.items()):
    with cols[i]:
        count = strategy_counts.get(key, 0)
        conditions = format_strategy_conditions(key)
        st.markdown(f"""
        <div class="strategy-card">
            <h4>{strategy['name']}</h4>
            <p>{strategy['description']}</p>
            <p style="margin-top: 0.5rem; font-size: 0.8rem; color: #9ca3af;">{', '.join(conditions)}</p>
            <p style="margin-top: 0.5rem;"><span class="strategy-count">{count}</span> 檔符合</p>
        </div>
        """, unsafe_allow_html=True)

selected_strategy = st.radio(
    "策略",
    list(STRATEGIES.keys()),
    format_func=lambda x: STRATEGIES[x]['name'],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# 篩選結果
filtered_df = apply_strategy(df, selected_strategy)
if not filtered_df.empty and 'roe' in filtered_df.columns:
    filtered_df = calculate_score(filtered_df)
    filtered_df = filtered_df.sort_values('score', ascending=False)

strategy_info = STRATEGIES[selected_strategy]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("符合條件", f"{len(filtered_df)} 檔")
with col2:
    st.metric("通過率", f"{len(filtered_df) / len(df) * 100:.1f}%")
with col3:
    if not filtered_df.empty and 'score' in filtered_df.columns:
        st.metric("平均評分", f"{filtered_df['score'].mean():.2f}")

st.divider()

if filtered_df.empty:
    st.warning("沒有符合條件的股票")
else:
    st.subheader("符合條件的股票")
    
    # 顯示資料
    display_cols = ['stock_id', 'name', 'industry', 'score']
    if selected_strategy == 'growth':
        display_cols.extend(['roe', 'eps_growth', 'revenue_growth'])
    elif selected_strategy == 'value':
        display_cols.extend(['pe', 'pb', 'roe', 'dividend_yield'])
    elif selected_strategy == 'dividend':
        display_cols.extend(['dividend_yield', 'dividend_years', 'debt_ratio'])
    elif selected_strategy == 'quality':
        display_cols.extend(['roe', 'pe', 'debt_ratio'])
    
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[display_cols].head(50).copy()
    
    column_names = {'stock_id': '代號', 'name': '名稱', 'industry': '產業', 'score': '評分',
                    'roe': 'ROE(%)', 'pe': 'PE', 'pb': 'PB', 'dividend_yield': '殖利率(%)',
                    'eps_growth': 'EPS成長(%)', 'revenue_growth': '營收成長(%)',
                    'dividend_years': '配息年數', 'debt_ratio': '負債率(%)'}
    display_df = display_df.rename(columns=column_names)
    
    for col in display_df.select_dtypes(include=['float64']).columns:
        display_df[col] = display_df[col].round(2)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.download_button("匯出 CSV", filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                       f"strategy_{selected_strategy}.csv", "text/csv")
    
    st.divider()
    
    # 圖表
    st.subheader("分析圖表")
    col1, col2 = st.columns(2)
    
    with col1:
        if 'industry' in filtered_df.columns:
            industry_counts = filtered_df['industry'].value_counts().head(8)
            fig = px.pie(values=industry_counts.values, names=industry_counts.index, title="產業分布", hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label', 
                             marker=dict(colors=['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff', '#f8fafc']))
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'score' in filtered_df.columns:
            fig = px.histogram(filtered_df, x='score', nbins=15, title="評分分布")
            fig.update_traces(marker_color='#2563eb')
            fig.update_layout(xaxis_title="評分", yaxis_title="數量")
            st.plotly_chart(fig, use_container_width=True)
