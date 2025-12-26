"""
台股智選系統 - 策略與篩選頁面
Taiwan Stock Selection System - Strategy & Filter Page
Glarity 風格設計
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_screener import custom_screen, apply_strategy, format_strategy_conditions, get_strategy_matches_count
from src.stock_analyzer import calculate_score
from src.styles import GLARITY_STYLE
from config import INDICATORS, INDUSTRIES, ASSET_TYPES, STRATEGIES

st.set_page_config(page_title="策略篩選 - 台股智選系統", page_icon="📊", layout="wide")

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

# 隱藏側邊欄的 "main" 標籤
st.markdown('<style>[data-testid="stSidebarNav"] li:first-child { display: none; }</style>', unsafe_allow_html=True)

# 側邊欄首頁連結
if st.sidebar.button("🏠 首頁", use_container_width=True, type="primary", key="home_btn"):
    st.switch_page("main.py")
st.sidebar.markdown("---")

# 額外的篩選頁樣式
st.markdown("""
<style>
    .strategy-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border: 2px solid transparent;
        transition: all 0.2s;
    }
    .strategy-card:hover {
        border-color: #2563eb;
    }
    .strategy-card h4 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1rem;
    }
    .strategy-card .desc {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .strategy-card .count {
        color: #2563eb;
        font-weight: 600;
        font-size: 1.25rem;
    }
    .filter-section {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin: 1rem 0;
    }
    .result-badge {
        display: inline-block;
        background: #dbeafe;
        color: #1d4ed8;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 策略篩選")
st.caption("選擇快速策略或自訂條件，找出符合需求的股票")

# 側邊欄說明
with st.sidebar:
    st.divider()
    with st.expander("📚 快速說明"):
        st.markdown("""
        **策略說明**
        - 🚀 成長股：ROE>15%, EPS成長>15%
        - 💎 價值股：PE<15, PB<2
        - 💰 高股息：殖利率>5%
        - ⭐ 優質股：ROE>15%, 負債率<40%
        
        [返回首頁查看完整說明](/)
        """)

@st.cache_data(ttl=3600)
def load_data():
    df = get_stock_list()
    if df.empty or 'roe' not in df.columns:
        df = generate_sample_data()
    return df

df = load_data()
strategy_counts = get_strategy_matches_count(df)

# ========== 快速策略區 ==========
st.subheader("🚀 快速策略")

# 策略卡片
cols = st.columns(4)
for i, (key, strategy) in enumerate(STRATEGIES.items()):
    with cols[i]:
        count = strategy_counts.get(key, 0)
        st.markdown(f"""
        <div class="strategy-card">
            <h4>{strategy['name']}</h4>
            <div class="desc">{strategy['description']}</div>
            <div class="count">{count} 檔</div>
        </div>
        """, unsafe_allow_html=True)

# 策略選擇
selected_strategy = st.radio(
    "選擇策略",
    [None] + list(STRATEGIES.keys()),
    format_func=lambda x: "🔧 自訂篩選" if x is None else STRATEGIES[x]['name'],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# ========== 篩選條件區 ==========
with st.expander("⚙️ 自訂篩選條件", expanded=(selected_strategy is None)):
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        asset_type = st.selectbox("資產類型", list(ASSET_TYPES.keys()), format_func=lambda x: ASSET_TYPES[x])
        industry = st.selectbox("產業別", INDUSTRIES)
    
    with col2:
        roe_min = st.slider("ROE (%)", 0, 50, 0)
        pe_max = st.slider("本益比上限", 5, 100, 100)
    
    with col3:
        div_min = st.slider("殖利率 (%)", 0.0, 15.0, 0.0, 0.5)
        debt_max = st.slider("負債率上限 (%)", 0, 100, 100)
    
    exclude_loss = st.checkbox("排除虧損公司")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 執行篩選 ==========
if selected_strategy:
    filtered_df = apply_strategy(df, selected_strategy)
    filter_mode = f"策略：{STRATEGIES[selected_strategy]['name']}"
else:
    filters = {}
    if roe_min > 0: filters['roe'] = {'min': roe_min}
    if pe_max < 100: filters['pe'] = {'max': pe_max}
    if div_min > 0: filters['dividend_yield'] = {'min': div_min}
    if debt_max < 100: filters['debt_ratio'] = {'max': debt_max}
    
    filtered_df = custom_screen(df, filters=filters, industry=industry, asset_type=asset_type, exclude_loss=exclude_loss)
    filter_mode = "自訂篩選"

if not filtered_df.empty and 'roe' in filtered_df.columns:
    filtered_df = calculate_score(filtered_df)
    filtered_df = filtered_df.sort_values('score', ascending=False)

# ========== 統計數據 ==========
col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
with col1:
    st.metric("篩選模式", filter_mode)
with col2:
    st.metric("符合條件", f"{len(filtered_df)} 檔")
with col3:
    st.metric("通過率", f"{len(filtered_df) / len(df) * 100:.1f}%")
with col4:
    avg_score = filtered_df['score'].mean() if not filtered_df.empty and 'score' in filtered_df.columns else 0
    st.metric("平均評分", f"{avg_score:.2f}")

st.divider()

# ========== 結果顯示 ==========
if filtered_df.empty:
    st.warning("沒有符合條件的股票，請調整篩選條件")
else:
    st.subheader("📋 篩選結果")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        sort_by = st.selectbox("排序依據", ['score', 'roe', 'pe', 'dividend_yield'], 
                               format_func=lambda x: {'score': '評分', 'roe': 'ROE', 'pe': 'PE', 'dividend_yield': '殖利率'}[x],
                               label_visibility="collapsed")
    with col2:
        sort_asc = st.selectbox("順序", ["降冪", "升冪"], label_visibility="collapsed") == "升冪"
    
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by, ascending=sort_asc)
    
    # 顯示設定
    col_a, col_b = st.columns([1, 3])
    with col_a:
        display_mode = st.selectbox("顯示方式", ["分頁", "全部"], label_visibility="collapsed")
    with col_b:
        if display_mode == "分頁":
            page_size = st.selectbox("每頁筆數", [20, 50, 100], index=1, label_visibility="collapsed")
        else:
            page_size = len(filtered_df)
    
    # 分頁邏輯
    total_count = len(filtered_df)
    total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
    
    if display_mode == "分頁" and total_pages > 1:
        page = st.number_input(f"頁數 (共 {total_pages} 頁)", min_value=1, max_value=total_pages, value=1, step=1)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        st.caption(f"顯示第 {start_idx + 1} - {end_idx} 筆，共 {total_count} 筆")
    else:
        start_idx = 0
        end_idx = total_count
        st.caption(f"顯示全部 {total_count} 筆")
    
    display_cols = ['stock_id', 'name', 'price', 'score', 'roe', 'pe', 'pb', 'dividend_yield', 'debt_ratio']
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[display_cols].iloc[start_idx:end_idx].copy()
    
    # 加入序號欄位
    display_df.insert(0, '序號', range(start_idx + 1, end_idx + 1))
    
    column_names = {'stock_id': '代號', 'name': '名稱', 'price': '股價', 'score': '評分',
                    'roe': 'ROE%(40%)', 'pe': 'PE(30%)', 'pb': 'PB(15%)', 'dividend_yield': '殖利率(%)', 'debt_ratio': '負債率%(15%)'}
    display_df = display_df.rename(columns=column_names)
    
    for col in display_df.select_dtypes(include=['float64']).columns:
        display_df[col] = display_df[col].round(2)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # 匯出全部資料
    export_df = filtered_df[['stock_id', 'name', 'industry', 'score', 'roe', 'pe', 'pb', 'dividend_yield', 'debt_ratio'] if all(c in filtered_df.columns for c in ['stock_id', 'name']) else filtered_df.columns].copy()
    export_df.insert(0, '序號', range(1, len(export_df) + 1))
    st.download_button(f"📥 匯出全部 {total_count} 筆 CSV", export_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                       "filtered_stocks.csv", "text/csv")
    
    st.divider()
    
    # ========== 分析圖表 ==========
    st.subheader("📈 分析圖表")
    col1, col2 = st.columns(2)
    
    with col1:
        if 'industry' in filtered_df.columns:
            industry_counts = filtered_df['industry'].value_counts().head(8)
            fig = px.pie(values=industry_counts.values, names=industry_counts.index, title="產業分布", hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label', 
                             marker=dict(colors=['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff', '#f8fafc']))
            fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'score' in filtered_df.columns:
            fig = px.histogram(filtered_df, x='score', nbins=15, title="評分分布")
            fig.update_traces(marker_color='#2563eb')
            fig.update_layout(xaxis_title="評分", yaxis_title="數量", 
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# 指標說明
with st.expander("📚 指標說明"):
    for key, info in INDICATORS.items():
        ideal = f"> {info['ideal_min']}" if info.get('ideal_min') else f"< {info['ideal_max']}" if info.get('ideal_max') else "N/A"
        st.markdown(f"**{info['name']}** - {info['description']} (理想值: {ideal}{info.get('unit', '')})")
