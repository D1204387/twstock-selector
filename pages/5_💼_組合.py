"""
台股智選系統 - 投資組合頁面
Taiwan Stock Selection System - Portfolio Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_analyzer import calculate_score, get_score_grade

st.set_page_config(page_title="投資組合 - 台股智選系統", page_icon="💼", layout="wide")

# 灰藍色調 CSS
st.markdown("""
<style>
    .compare-header { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; 
                      padding: 1rem; margin-bottom: 1rem; text-align: center; }
    .compare-header h3 { color: #2563eb; margin: 0; }
    .portfolio-item { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;
                      padding: 0.75rem; margin-bottom: 0.5rem; }
    .weight-badge { background: #2563eb; color: white; padding: 0.25rem 0.5rem; 
                    border-radius: 4px; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.title("💼 投資組合")
st.caption("股票與 ETF 分開比較，建立投資組合配置")

@st.cache_data(ttl=3600)
def load_data():
    df = get_stock_list()
    if df.empty or 'roe' not in df.columns:
        df = generate_sample_data()
    return df

df = load_data()

# 分離股票和 ETF
stocks_df = df[df['asset_type'] == 'stock'].copy()
etf_df = df[df['asset_type'] == 'etf'].copy()

# 計算評分
if 'roe' in stocks_df.columns:
    stocks_df = calculate_score(stocks_df)
if 'roe' in etf_df.columns:
    etf_df = calculate_score(etf_df)

# 選項卡
tab1, tab2, tab3 = st.tabs(["📊 股票 vs ETF 比較", "💼 建立投資組合", "📈 組合分析"])

# ===== Tab 1: 比較 =====
with tab1:
    st.subheader("股票與 ETF 比較")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="compare-header"><h3>🏢 一般股票</h3></div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("數量", f"{len(stocks_df)} 檔")
        with c2:
            if 'score' in stocks_df.columns:
                st.metric("平均評分", f"{stocks_df['score'].mean():.2f}")
        with c3:
            if 'dividend_yield' in stocks_df.columns:
                st.metric("平均殖利率", f"{stocks_df['dividend_yield'].mean():.2f}%")
        
        # Top 10 股票
        st.markdown("**Top 10 股票**")
        if 'score' in stocks_df.columns:
            top_stocks = stocks_df.nlargest(10, 'score')[['stock_id', 'name', 'industry', 'score', 'roe', 'dividend_yield']]
            top_stocks.columns = ['代號', '名稱', '產業', '評分', 'ROE(%)', '殖利率(%)']
            for col in top_stocks.select_dtypes(include=['float64']).columns:
                top_stocks[col] = top_stocks[col].round(2)
            st.dataframe(top_stocks, use_container_width=True, hide_index=True, height=300)
    
    with col2:
        st.markdown('<div class="compare-header"><h3>📦 ETF</h3></div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("數量", f"{len(etf_df)} 檔")
        with c2:
            if 'score' in etf_df.columns and not etf_df.empty:
                st.metric("平均評分", f"{etf_df['score'].mean():.2f}")
            else:
                st.metric("平均評分", "N/A")
        with c3:
            if 'dividend_yield' in etf_df.columns and not etf_df.empty:
                st.metric("平均殖利率", f"{etf_df['dividend_yield'].mean():.2f}%")
            else:
                st.metric("平均殖利率", "N/A")
        
        # Top 10 ETF
        st.markdown("**Top 10 ETF**")
        if 'score' in etf_df.columns and not etf_df.empty:
            top_etf = etf_df.nlargest(10, 'score')[['stock_id', 'name', 'score', 'dividend_yield']]
            top_etf.columns = ['代號', '名稱', '評分', '殖利率(%)']
            for col in top_etf.select_dtypes(include=['float64']).columns:
                top_etf[col] = top_etf[col].round(2)
            st.dataframe(top_etf, use_container_width=True, hide_index=True, height=300)
        else:
            st.info("ETF 資料載入中...")
    
    st.divider()
    
    # 比較圖表
    st.subheader("比較圖表")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 評分分布比較
        if 'score' in stocks_df.columns and 'score' in etf_df.columns:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=stocks_df['score'], name='股票', marker_color='#2563eb', opacity=0.7))
            fig.add_trace(go.Histogram(x=etf_df['score'], name='ETF', marker_color='#60a5fa', opacity=0.7))
            fig.update_layout(title="評分分布比較", barmode='overlay', xaxis_title="評分", yaxis_title="數量")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 殖利率分布比較
        if 'dividend_yield' in stocks_df.columns:
            fig = go.Figure()
            fig.add_trace(go.Box(y=stocks_df['dividend_yield'], name='股票', marker_color='#2563eb'))
            if not etf_df.empty and 'dividend_yield' in etf_df.columns:
                fig.add_trace(go.Box(y=etf_df['dividend_yield'], name='ETF', marker_color='#60a5fa'))
            fig.update_layout(title="殖利率分布比較", yaxis_title="殖利率 (%)")
            st.plotly_chart(fig, use_container_width=True)

# ===== Tab 2: 建立組合 =====
with tab2:
    st.subheader("建立投資組合")
    
    # 初始化 session state
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**新增標的**")
        
        # 搜尋輸入
        search_keyword = st.text_input("搜尋股票/ETF", placeholder="輸入代號或名稱（如 2330 或 台積電）", key="portfolio_search")
        
        # 選擇類型
        asset_type_select = st.radio("類型", ["全部", "股票", "ETF"], horizontal=True, label_visibility="collapsed")
        
        # 根據類型篩選
        if asset_type_select == "股票":
            options_df = stocks_df
        elif asset_type_select == "ETF":
            options_df = etf_df
        else:
            options_df = df.copy()
        
        # 搜尋篩選
        if search_keyword:
            options_df = options_df[
                options_df['stock_id'].str.contains(search_keyword, case=False, na=False) |
                options_df['name'].str.contains(search_keyword, case=False, na=False)
            ]
        
        if not options_df.empty:
            # 限制顯示數量
            display_options = options_df.head(50)
            options = display_options.apply(lambda x: f"{x['stock_id']} - {x['name']}", axis=1).tolist()
            
            if options:
                selected = st.selectbox(
                    f"選擇標的（找到 {len(options_df)} 筆）", 
                    options,
                    label_visibility="collapsed"
                )
                
                # 權重
                weight = st.slider("配置比例 (%)", 1, 100, 10)
                
                if st.button("➕ 加入組合", type="primary"):
                    stock_id = selected.split(" - ")[0]
                    stock_name = selected.split(" - ")[1]
                    
                    # 檢查是否已存在
                    existing = [p for p in st.session_state.portfolio if p['stock_id'] == stock_id]
                    if existing:
                        st.warning(f"{stock_name} 已在組合中")
                    else:
                        stock_data = options_df[options_df['stock_id'] == stock_id].iloc[0]
                        st.session_state.portfolio.append({
                            'stock_id': stock_id,
                            'name': stock_name,
                            'type': '股票' if stock_data.get('asset_type') == 'stock' else 'ETF',
                            'weight': weight,
                            'score': stock_data.get('score', 0),
                            'roe': stock_data.get('roe', 0),
                            'dividend_yield': stock_data.get('dividend_yield', 0),
                            'debt_ratio': stock_data.get('debt_ratio', 0)
                        })
                        st.success(f"已加入 {stock_name}")
                        st.rerun()
            else:
                st.info("請輸入搜尋關鍵字")
        else:
            st.warning(f"找不到符合「{search_keyword}」的{asset_type_select}")
    
    with col2:
        st.markdown("**目前組合**")
        
        if not st.session_state.portfolio:
            st.info("尚未加入任何標的")
        else:
            total_weight = sum(p['weight'] for p in st.session_state.portfolio)
            
            for i, item in enumerate(st.session_state.portfolio):
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.markdown(f"**{item['name']}** ({item['type']})")
                with col_b:
                    st.markdown(f"<span class='weight-badge'>{item['weight']}%</span>", unsafe_allow_html=True)
                with col_c:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.portfolio.pop(i)
                        st.rerun()
            
            st.divider()
            st.markdown(f"**總配置：{total_weight}%**")
            
            if total_weight != 100:
                st.warning(f"建議總配置為 100%（目前 {total_weight}%）")
            
            if st.button("🗑️ 清空組合"):
                st.session_state.portfolio = []
                st.rerun()

# ===== Tab 3: 組合分析 =====
with tab3:
    st.subheader("組合分析")
    
    if not st.session_state.portfolio:
        st.info("請先在「建立投資組合」中加入標的")
    else:
        portfolio = st.session_state.portfolio
        total_weight = sum(p['weight'] for p in portfolio)
        
        # 計算加權平均
        weighted_score = sum(p['score'] * p['weight'] for p in portfolio) / total_weight if total_weight > 0 else 0
        weighted_roe = sum(p['roe'] * p['weight'] for p in portfolio) / total_weight if total_weight > 0 else 0
        weighted_dividend = sum(p['dividend_yield'] * p['weight'] for p in portfolio) / total_weight if total_weight > 0 else 0
        weighted_debt = sum(p['debt_ratio'] * p['weight'] for p in portfolio) / total_weight if total_weight > 0 else 0
        
        # 統計
        stock_count = len([p for p in portfolio if p['type'] == '股票'])
        etf_count = len([p for p in portfolio if p['type'] == 'ETF'])
        stock_weight = sum(p['weight'] for p in portfolio if p['type'] == '股票')
        etf_weight = sum(p['weight'] for p in portfolio if p['type'] == 'ETF')
        
        # 顯示統計
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("組合評分", f"{weighted_score:.2f}", get_score_grade(weighted_score))
        with col2:
            st.metric("加權 ROE", f"{weighted_roe:.2f}%")
        with col3:
            st.metric("加權殖利率", f"{weighted_dividend:.2f}%")
        with col4:
            st.metric("加權負債率", f"{weighted_debt:.2f}%")
        
        st.divider()
        
        # 組合明細
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**組合配置**")
            
            portfolio_df = pd.DataFrame(portfolio)
            fig = px.pie(portfolio_df, values='weight', names='name', title="配置比例", hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label',
                             marker=dict(colors=['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe']))
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**資產類型配置**")
            
            type_data = pd.DataFrame([
                {'類型': '股票', '比例': stock_weight},
                {'類型': 'ETF', '比例': etf_weight}
            ])
            fig = px.pie(type_data, values='比例', names='類型', title="股票 vs ETF", hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label',
                             marker=dict(colors=['#2563eb', '#60a5fa']))
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # 組合明細表
        st.markdown("**組合明細**")
        detail_df = pd.DataFrame(portfolio)[['stock_id', 'name', 'type', 'weight', 'score', 'roe', 'dividend_yield', 'debt_ratio']]
        detail_df.columns = ['代號', '名稱', '類型', '權重(%)', '評分', 'ROE(%)', '殖利率(%)', '負債率(%)']
        for col in detail_df.select_dtypes(include=['float64']).columns:
            detail_df[col] = detail_df[col].round(2)
        st.dataframe(detail_df, use_container_width=True, hide_index=True)
        
        # 風險評估
        st.divider()
        st.markdown("**風險評估**")
        
        risk_items = []
        if stock_weight > 80:
            risk_items.append("⚠️ 股票比例過高（>80%），建議增加 ETF 分散風險")
        if etf_weight > 80:
            risk_items.append("ℹ️ ETF 比例過高（>80%），收益可能較為保守")
        if len(portfolio) < 3:
            risk_items.append("⚠️ 持有標的過少（<3），建議增加標的分散風險")
        if weighted_debt > 60:
            risk_items.append("⚠️ 組合平均負債率偏高（>60%）")
        if weighted_score < 5:
            risk_items.append("⚠️ 組合評分偏低（<5），建議重新檢視配置")
        
        if not risk_items:
            st.success("✅ 組合配置良好，風險分散適當")
        else:
            for item in risk_items:
                st.markdown(item)
