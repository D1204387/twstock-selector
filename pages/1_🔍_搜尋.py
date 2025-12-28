"""
台股智選系統 - 搜尋頁面
Taiwan Stock Selection System - Search Page
Glarity 風格設計
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data, load_robust_data
from src.stock_analyzer import analyze_stock, get_score_grade
from src.indicators import get_indicators_by_category
from src.styles import GLARITY_STYLE
from config import INDICATORS

st.set_page_config(page_title="搜尋 - 台股智選系統", page_icon="🔍", layout="wide")

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

# 隱藏側邊欄的 "main" 標籤
st.markdown('<style>[data-testid="stSidebarNav"] li:first-child { display: none; }</style>', unsafe_allow_html=True)

# 側邊欄首頁連結
if st.sidebar.button("🏠 首頁", use_container_width=True, type="primary", key="home_btn"):
    st.switch_page("main.py")
st.sidebar.markdown("---")

# 額外的搜尋頁樣式
st.markdown("""
<style>
    .score-card {
        background: #2563eb;
        color: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .score-card .score {
        font-size: 2.5rem;
        font-weight: 600;
    }
    .score-card .grade {
        font-size: 1rem;
        opacity: 0.9;
    }
    .stock-header {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .stock-header h2 {
        color: #1f2937;
        margin: 0 0 0.5rem 0;
    }
    .stock-header .meta {
        color: #6b7280;
        font-size: 0.9rem;
    }
    .analysis-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 股票搜尋")
st.caption("輸入股票代號或公司名稱，查看詳細資訊")

# 側邊欄說明
with st.sidebar:
    st.divider()
    with st.expander("📚 快速說明"):
        st.markdown("""
        **關鍵指標**
        - 權益報酬率 > 15%：獲利能力佳
        - 本益比 10-20：估值合理
        - 殖利率 > 4%：高股息
        - 負債率 < 50%：財務穩健
        
        [返回首頁查看完整說明](/)
        """)

@st.cache_data(ttl=3600)
def load_data():
    df = load_robust_data()
    return df

df = load_data()

# 搜尋區塊
col1, col2 = st.columns([4, 1])
with col1:
    keyword = st.text_input("搜尋", placeholder="輸入股票代號或公司名稱", label_visibility="collapsed")
with col2:
    search_type = st.selectbox("範圍", ["全部", "股票", "ETF"], label_visibility="collapsed")

if keyword:
    results = df[
        df['stock_id'].str.contains(keyword, case=False, na=False) |
        df['name'].str.contains(keyword, case=False, na=False)
    ]
    
    if search_type == "股票" and 'asset_type' in results.columns:
        results = results[results['asset_type'] == 'stock']
    elif search_type == "ETF" and 'asset_type' in results.columns:
        results = results[results['asset_type'] == 'etf']
    
    if results.empty:
        st.warning(f"找不到「{keyword}」")
    else:
        st.success(f"找到 {len(results)} 筆")
        
        selected = st.selectbox(
            "選擇股票",
            results.apply(lambda x: f"{x['stock_id']} - {x['name']}", axis=1).tolist(),
            label_visibility="collapsed"
        )
        
        if selected:
            stock_id = selected.split(" - ")[0]
            stock = results[results['stock_id'] == stock_id].iloc[0]
            analysis = analyze_stock(stock.to_dict())
            
            st.divider()
            
            # 基本資訊
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="stock-header">
                    <h2>{stock['name']} ({stock['stock_id']})</h2>
                    <div class="meta">
                        {f"產業：{stock['industry']}" if 'industry' in stock else ""} 
                        {f" | 市場：{stock['market']}" if 'market' in stock else ""}
                        {f" | 股價：${stock['price']:.2f}" if 'price' in stock and pd.notna(stock['price']) else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score">{analysis['score']:.1f}</div>
                    <div class="grade">等級 {analysis['grade']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 虧損警示
            eps_val = stock.get('eps')
            roe_val = stock.get('roe')
            if (pd.notna(eps_val) and eps_val < 0) or (pd.notna(roe_val) and roe_val < 0):
                st.warning("⚠️ **虧損警示**：該公司 EPS 或 ROE 為負值，請審慎評估投資風險。")
            
            st.divider()
            
            # 財務指標
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("財務指標")
                categories = get_indicators_by_category()
                
                for category, indicators in categories.items():
                    with st.expander(category, expanded=(category == "獲利能力")):
                        for key in indicators:
                            info = INDICATORS.get(key, {})
                            value = stock.get(key)
                            
                            # 建立說明文字
                            description = info.get('description', '')
                            formula = info.get('formula', '')
                            ideal_text = ""
                            if info.get('ideal_min') and info.get('ideal_max'):
                                ideal_text = f"理想值: {info['ideal_min']} ~ {info['ideal_max']}{info.get('unit', '')}"
                            elif info.get('ideal_min'):
                                ideal_text = f"理想值: > {info['ideal_min']}{info.get('unit', '')}"
                            elif info.get('ideal_max'):
                                ideal_text = f"理想值: < {info['ideal_max']}{info.get('unit', '')}"
                            
                            # 組合說明文字
                            help_parts = []
                            if description:
                                help_parts.append(description)
                            if formula:
                                help_parts.append(f"公式: {formula}")
                            if ideal_text:
                                help_parts.append(ideal_text)
                            help_text = "\n".join(help_parts) if help_parts else None
                            
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                st.markdown(f"**{info.get('name', key)}**", help=help_text)
                            with c2:
                                if pd.notna(value):
                                    # 虧損標示：負值顯示紅色
                                    if value < 0:
                                        st.markdown(f"🔴 <span style='color: red;'>{value:.2f}{info.get('unit', '')}</span>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"{value:.2f}{info.get('unit', '')}")
                                else:
                                    st.markdown("N/A")
            
            with col2:
                st.subheader("指標雷達圖")
                
                # 判斷是否為 ETF
                is_etf = str(stock.get('stock_id', '')).startswith('00')
                
                if is_etf:
                    # ETF 專用雷達圖：5 個維度
                    categories_radar = ['殖利率', '折溢價(PB)', '配息穩定度', '分散風險', '追蹤效率']
                    
                    # 殖利率（7%+ = 滿分）
                    div_yield = stock.get('dividend_yield', 0) or 0
                    div_s = min(10, max(0, div_yield * 1.2))  # 8% = 9.6分
                    
                    # PB（折溢價，ETF PB < 1 代表折價買入）
                    pb = stock.get('pb', 1) or 1
                    if pb <= 1:
                        pb_s = 10  # 折價 = 滿分
                    elif pb <= 1.05:
                        pb_s = 8   # 小幅溢價
                    elif pb <= 1.1:
                        pb_s = 6   # 中度溢價
                    else:
                        pb_s = max(0, 10 - (pb - 1) * 20)  # 溢價越高分數越低
                    
                    # 配息穩定度（連續配息年數，5年+ = 滿分）
                    years = stock.get('dividend_years', 0) or 0
                    years_s = min(10, years * 2)  # 5年 = 10分
                    
                    # 分散風險（ETF 固有優勢，給予高分）
                    diversify_s = 9  # ETF 天生分散風險
                    
                    # 追蹤效率（假設良好，根據殖利率間接評估）
                    track_s = min(10, 7 + div_yield * 0.3) if div_yield > 3 else 6
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=[div_s, pb_s, years_s, diversify_s, track_s],
                        theta=categories_radar,
                        fill='toself',
                        fillcolor='rgba(16, 185, 129, 0.2)',  # 綠色調 for ETF
                        line_color='#10b981',
                        name='ETF 指標'
                    ))
                else:
                    # 一般股票雷達圖
                    categories_radar = ['權益報酬率', '本益比', '淨值比', '負債率', '殖利率']
                    roe_s = min(10, max(0, (stock.get('roe', 0) or 0) / 3))
                    pe = stock.get('pe', 15) or 15
                    pe_s = 10 - min(10, max(0, abs(pe - 15) / 3))
                    pb = stock.get('pb', 2) or 2
                    pb_s = min(10, max(0, (3 - pb) * 3))
                    debt_s = min(10, max(0, (100 - (stock.get('debt_ratio', 50) or 50)) / 10))
                    div_s = min(10, max(0, (stock.get('dividend_yield', 0) or 0) * 2))
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=[roe_s, pe_s, pb_s, debt_s, div_s],
                        theta=categories_radar,
                        fill='toself',
                        fillcolor='rgba(37, 99, 235, 0.2)',
                        line_color='#2563eb'
                    ))
                
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor='#e5e7eb')),
                    showlegend=False, height=300, margin=dict(l=40, r=40, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 優缺點
                st.subheader("投資分析")
                if analysis['strengths']:
                    for s in analysis['strengths']:
                        st.markdown(f"✅ {s}")
                if analysis['weaknesses']:
                    for w in analysis['weaknesses']:
                        st.markdown(f"⚠️ {w}")
else:
    # 未輸入搜尋條件時，顯示使用指南
    st.subheader("💡 使用指南")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔍 搜尋方式
        
        **股票代號搜尋**
        - 輸入股票代號如 `2330`、`2317`
        - 支援部分代號搜尋
        
        **公司名稱搜尋**
        - 輸入公司名稱如 `台積電`、`鴻海`
        - 支援模糊搜尋
        
        **ETF 搜尋**
        - 輸入 ETF 代號如 `0050`、`0056`
        - 在下拉選單選擇「ETF」可過濾
        """)
    
    with col2:
        st.markdown("""
        ### 📊 功能說明
        
        **詳細資訊**
        - 查看股票的財務指標
        - 雷達圖顯示各項評分
        - 優缺點分析
        
        **快速連結**
        - 🏆 **[排名](/🏆_排名)** - 查看評分最高的股票
        - 🎛️ **[篩選](/🎛️_篩選)** - 自訂條件篩選
        - 🤖 **[AI 選股](/🤖_AI智慧選股)** - 用自然語言查詢
        """)
    
    st.divider()
    
    # 顯示資料庫統計
    st.subheader("📈 資料庫概況")
    
    total = len(df)
    stocks = len(df[df['asset_type'] == 'stock']) if 'asset_type' in df.columns else total
    etfs = len(df[df['asset_type'] == 'etf']) if 'asset_type' in df.columns else 0
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("總標的數", f"{total} 檔")
    col_b.metric("股票", f"{stocks} 檔")
    col_c.metric("ETF", f"{etfs} 檔")
    
    # 熱門搜尋建議
    st.subheader("🔥 熱門股票")
    popular_stocks = df.nlargest(5, 'score')[['stock_id', 'name', 'score']].values.tolist() if 'score' in df.columns else []
    if popular_stocks:
        cols = st.columns(5)
        for i, (sid, name, score) in enumerate(popular_stocks):
            with cols[i]:
                st.button(f"{sid} {name}", key=f"popular_{sid}", help=f"評分: {score:.1f}")
