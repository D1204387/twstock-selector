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

from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_analyzer import analyze_stock, get_score_grade
from src.indicators import get_indicators_by_category
from src.styles import GLARITY_STYLE
from config import INDICATORS

st.set_page_config(page_title="搜尋 - 台股智選系統", page_icon="🔍", layout="wide")

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

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
        - ROE > 15%：獲利能力佳
        - PE 10-20：估值合理
        - 殖利率 > 4%：高股息
        - 負債率 < 50%：財務穩健
        
        [返回首頁查看完整說明](/)
        """)

@st.cache_data(ttl=3600)
def load_data():
    df = get_stock_list()
    if df.empty or 'roe' not in df.columns:
        df = generate_sample_data()
    return df

df = load_data()

# 搜尋區塊
st.markdown('<div class="card">', unsafe_allow_html=True)
col1, col2 = st.columns([4, 1])
with col1:
    keyword = st.text_input("搜尋", placeholder="輸入股票代號或公司名稱", label_visibility="collapsed")
with col2:
    search_type = st.selectbox("範圍", ["全部", "股票", "ETF"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

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
                                    st.markdown(f"{value:.2f}{info.get('unit', '')}")
                                else:
                                    st.markdown("N/A")
            
            with col2:
                st.subheader("指標雷達圖")
                
                categories_radar = ['ROE', 'PE', 'PB', '負債率', '殖利率']
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
                st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                if analysis['strengths']:
                    for s in analysis['strengths']:
                        st.markdown(f"✅ {s}")
                if analysis['weaknesses']:
                    for w in analysis['weaknesses']:
                        st.markdown(f"⚠️ {w}")
                st.markdown('</div>', unsafe_allow_html=True)
else:
    # 根據篩選器過濾資料
    filtered_df = df.copy()
    if search_type == "股票" and 'asset_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['asset_type'] == 'stock']
        st.subheader("🔥 評分最高股票")
    elif search_type == "ETF" and 'asset_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['asset_type'] == 'etf']
        st.subheader("🔥 評分最高 ETF")
    else:
        st.subheader("🔥 評分最高標的")
    
    st.caption("依綜合評分排序，點擊股票代號可搜尋詳細資訊")
    
    # 計算評分並排序
    from src.stock_analyzer import calculate_score
    if 'score' not in filtered_df.columns and 'roe' in filtered_df.columns:
        filtered_df = calculate_score(filtered_df)
    
    # 按評分排序
    if 'score' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('score', ascending=False)
    
    # 顯示設定
    total_count = len(filtered_df)
    col_a, col_b = st.columns([1, 3])
    with col_a:
        display_mode = st.selectbox("顯示方式", ["分頁", "全部"], key="search_display_mode", label_visibility="collapsed")
    with col_b:
        if display_mode == "分頁":
            page_size = st.selectbox("每頁筆數", [15, 30, 50], index=0, key="search_page_size", label_visibility="collapsed")
        else:
            page_size = total_count
    
    # 分頁邏輯
    total_pages = max((total_count + page_size - 1) // page_size, 1) if page_size > 0 else 1
    
    if display_mode == "分頁" and total_pages > 1:
        page = st.number_input(f"頁數 (共 {total_pages} 頁)", min_value=1, max_value=total_pages, value=1, step=1, key="search_page")
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        st.caption(f"顯示第 {start_idx + 1} - {end_idx} 筆，共 {total_count} 檔{search_type if search_type != '全部' else '標的'}")
    else:
        start_idx = 0
        end_idx = total_count
        st.caption(f"顯示全部 {total_count} 檔{search_type if search_type != '全部' else '標的'}")
    
    # 顯示篩選後的資料
    display_cols = ['stock_id', 'name', 'industry', 'score', 'roe', 'pe', 'dividend_yield']
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[display_cols].iloc[start_idx:end_idx].copy()
    
    # 加入序號欄位
    display_df.insert(0, '序號', range(start_idx + 1, end_idx + 1))
    
    column_names = {
        'stock_id': '代號', 'name': '名稱', 'industry': '產業', 'score': '評分',
        'roe': 'ROE%(40%)', 'pe': 'PE(30%)', 'dividend_yield': '殖利率(%)'
    }
    display_df = display_df.rename(columns=column_names)
    
    for col in display_df.select_dtypes(include=['float64']).columns:
        display_df[col] = display_df[col].round(2)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
