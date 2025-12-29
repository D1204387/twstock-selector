"""
台股智選系統 - 排名頁面
Taiwan Stock Selection System - Ranking Page
Glarity 風格設計
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data, load_robust_data
from src.stock_analyzer import calculate_score, get_top_stocks, get_score_grade, score_roe, score_pe, score_pb, score_debt_ratio
from src.styles import GLARITY_STYLE
from src.help_docs import SCORING_HELP
from config import COLUMN_NAMES



st.set_page_config(page_title="排名 - 台股智選系統", page_icon="🏆", layout="wide")

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

# 隱藏側邊欄的 "main" 標籤
st.markdown('<style>[data-testid="stSidebarNav"] li:first-child { display: none; }</style>', unsafe_allow_html=True)

# 側邊欄首頁連結
if st.sidebar.button("🏠 首頁", use_container_width=True, type="primary", key="home_btn"):
    st.switch_page("main.py")
st.sidebar.markdown("---")

# 額外的排名頁樣式
st.markdown("""
<style>
    .rank-header {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .rank-header h2 {
        margin: 0;
        font-size: 1.5rem;
    }
    .rank-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    .grade-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .grade-a { background: #2563eb; color: white; }
    .grade-b { background: #60a5fa; color: white; }
    .grade-c { background: #9ca3af; color: white; }
    .grade-d { background: #d1d5db; color: #374151; }
</style>
""", unsafe_allow_html=True)

st.title("🏆 綜合排名")
st.caption("根據綜合評分系統，找出最優質的股票")

# 側邊欄說明
with st.sidebar:
    st.divider()
    with st.expander("📚 快速說明"):
        st.markdown("""
        **評分權重**
        - ROE：40%
        - PE：30%
        - PB：15%
        - 負債率：15%
        
        [返回首頁查看完整說明](/)
        """)

@st.cache_data(ttl=3600)
def load_data():
    df = load_robust_data()
    return df

df = load_data()

# 評分說明
with st.expander("📚 評分系統說明", expanded=False):
    st.markdown(SCORING_HELP)

# 篩選條件
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    top_n = st.selectbox("顯示數量", [10, 20, 30, 50], index=1)
with col2:
    asset_filter = st.selectbox("資產類型", ["全部", "股票", "ETF"])
with col3:
    industry_options = ["全部"] + (df['industry'].unique().tolist() if 'industry' in df.columns else [])
    industry_filter = st.selectbox("產業別", industry_options)
st.markdown('</div>', unsafe_allow_html=True)

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
    
    # 欄位順序：一般股票指標在前，ETF 指標在後
    display_cols = ['排名', 'stock_id', 'name', 'price', 'score', '等級', 'roe', 'pe', 'pb', 'debt_ratio', 'dividend_yield', 'dividend_years']
    display_cols = [c for c in display_cols if c in display_df.columns or c in ['排名', '等級']]
    result_df = display_df[display_cols].copy()
    
    result_df = result_df.rename(columns=COLUMN_NAMES)
    
    for col in result_df.select_dtypes(include=['float64']).columns:
        result_df[col] = result_df[col].round(2)
    
    # 評分權重說明
    st.caption("📊 **評分權重** — 一般股票：權益報酬率(ROE) 40% + 本益比(PE) 30% + 淨值比(PB) 15% + 負債率 15% ｜ ETF：殖利率 80% + 配息年數 20%")
    
    st.dataframe(result_df, use_container_width=True, hide_index=True)
    
    csv_data = display_df.to_csv(index=False)
    csv_bytes = b'\xef\xbb\xbf' + csv_data.encode('utf-8')
    st.download_button("📥 匯出 CSV", csv_bytes,
                       f"top_{top_n}_stocks.csv", "text/csv")
    
    st.divider()
    
    # 圖表
    st.subheader("📈 分析圖表")
    col1, col2 = st.columns(2)
    
    with col1:
        top_10 = display_df.head(10)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top_10['name'], x=top_10['score'], orientation='h',
            marker_color='#2563eb', text=top_10['score'].round(2), textposition='outside'
        ))
        fig.update_layout(title="Top 10 評分", xaxis_title="評分", yaxis=dict(autorange="reversed"),
                         height=400, margin=dict(l=10, r=10, t=40, b=40),
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        grade_counts = display_df['等級'].value_counts()
        fig = px.pie(values=grade_counts.values, names=grade_counts.index, title="等級分布", hole=0.4)
        fig.update_traces(textposition='inside', textinfo='percent+label',
                         marker=dict(colors=['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#9ca3af', '#d1d5db']))
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    # 個股明細
    with st.expander("🔍 查看個股評分明細"):
        selected = st.selectbox("選擇股票", display_df['stock_id'].tolist(),
                               format_func=lambda x: f"{x} - {display_df[display_df['stock_id']==x]['name'].values[0]}")
        if selected:
            stock = display_df[display_df['stock_id'] == selected].iloc[0]
            # 判斷是否為 ETF
            is_etf = str(stock.get('stock_id', '')).startswith('00')
            
            if is_etf:
                c1, c2 = st.columns(2)
                with c1:
                    val = stock.get('dividend_yield', 0)
                    # ETF 殖利率權重 70%
                    from src.stock_analyzer import score_dividend_yield, ETF_SCORING_WEIGHTS
                    score = score_dividend_yield(val)
                    st.metric("殖利率 (70%)", f"{val:.2f}%")
                    st.caption(f"得分: {score:.1f} (貢獻 {score*0.7:.1f})")
                
                with c2:
                    val = stock.get('pb', 0)
                    # ETF PB 權重 30%
                    from src.stock_analyzer import score_pb
                    score = score_pb(val)
                    st.metric("PB (30%)", f"{val:.2f}")
                    st.caption(f"得分: {score:.1f} (貢獻 {score*0.3:.1f})")
                    
                st.markdown("""
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #3b82f6;">
                    <h4 style="margin: 0 0 0.5rem 0; font-size: 1rem; color: #1e40af;">📊 ETF 評分指標說明</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.9rem; color: #4b5563;">
                        <div><strong>殖利率 (70%)</strong><br>配息收益能力</div>
                        <div><strong>PB (30%)</strong><br>折溢價狀況</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                # 一般個股
                c1, c2, c3, c4 = st.columns(4)
                
                with c1: 
                    val = stock.get('roe', 0)
                    score = score_roe(val)
                    st.metric("ROE", f"{val:.2f}%")
                    st.caption(f"得分: {score:.1f}")
                    
                with c2: 
                    val = stock.get('pe', 0)
                    score = score_pe(val)
                    st.metric("PE", f"{val:.2f}")
                    st.caption(f"得分: {score:.1f}")
                    
                with c3: 
                    val = stock.get('pb', 0)
                    score = score_pb(val)
                    st.metric("PB", f"{val:.2f}")
                    st.caption(f"得分: {score:.1f}")
                    
                with c4: 
                    val = stock.get('debt_ratio', 0)
                    score = score_debt_ratio(val)
                    st.metric("負債率", f"{val:.2f}%")
                    st.caption(f"得分: {score:.1f}")
                
                st.markdown("""
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #3b82f6;">
                    <h4 style="margin: 0 0 0.5rem 0; font-size: 1rem; color: #1e40af;">📊 評分指標說明</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.9rem; color: #4b5563;">
                        <div><strong>ROE (40%)</strong><br>核心獲利指標</div>
                        <div><strong>PE (30%)</strong><br>估值合理性</div>
                        <div><strong>PB (15%)</strong><br>資產價值保護</div>
                        <div><strong>負債率 (15%)</strong><br>財務安全性</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
