"""
台股智選系統 - 搜尋頁面
Taiwan Stock Selection System - Search Page
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
from config import INDICATORS

st.set_page_config(page_title="搜尋 - 台股智選系統", page_icon="🔍", layout="wide")

# 灰藍色調 CSS
st.markdown("""
<style>
    .search-header { color: #1f2937; margin-bottom: 0.5rem; }
    .stock-info { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.25rem; }
    .score-box { background: #2563eb; color: white; border-radius: 8px; padding: 1rem; text-align: center; }
    .score-box .score { font-size: 2rem; font-weight: 600; }
    .score-box .grade { font-size: 1rem; opacity: 0.9; }
    .indicator-row { padding: 0.75rem 0; border-bottom: 1px solid #f3f4f6; }
    .indicator-row:last-child { border-bottom: none; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 股票搜尋")
st.caption("輸入股票代號或公司名稱，查看詳細資訊")

@st.cache_data(ttl=3600)
def load_data():
    df = get_stock_list()
    if df.empty or 'roe' not in df.columns:
        df = generate_sample_data()
    return df

df = load_data()

# 搜尋
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
                st.subheader(f"{stock['name']} ({stock['stock_id']})")
                info = []
                if 'industry' in stock: info.append(f"產業：{stock['industry']}")
                if 'market' in stock: info.append(f"市場：{stock['market']}")
                if 'price' in stock and pd.notna(stock['price']): info.append(f"股價：${stock['price']:.2f}")
                st.caption(" | ".join(info))
            
            with col2:
                st.markdown(f"""
                <div class="score-box">
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
                            
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                st.markdown(f"**{info.get('name', key)}**")
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
                    showlegend=False, height=300, margin=dict(l=40, r=40, t=20, b=20)
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
    
    # 顯示篩選後的資料
    display_cols = ['stock_id', 'name', 'industry', 'score', 'roe', 'pe', 'dividend_yield']
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df.head(15)[display_cols].copy()
    
    column_names = {
        'stock_id': '代號', 'name': '名稱', 'industry': '產業', 'score': '評分',
        'roe': 'ROE(%)', 'pe': 'PE', 'dividend_yield': '殖利率(%)'
    }
    display_df = display_df.rename(columns=column_names)
    
    for col in display_df.select_dtypes(include=['float64']).columns:
        display_df[col] = display_df[col].round(2)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.caption(f"共 {len(filtered_df)} 檔{search_type if search_type != '全部' else '標的'}")
