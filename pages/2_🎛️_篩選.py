"""
台股智選系統 - 篩選頁面
Taiwan Stock Selection System - Filter Page
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_screener import custom_screen
from src.stock_analyzer import calculate_score
from config import INDICATORS, INDUSTRIES, ASSET_TYPES

st.set_page_config(page_title="篩選 - 台股智選系統", page_icon="🎛️", layout="wide")

# 灰藍色調 CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] { 
        background: #f9fafb; 
        min-width: 280px;
    }
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {
        color: #374151 !important;
    }
    .filter-badge { 
        background: #dbeafe; 
        color: #1d4ed8; 
        padding: 0.25rem 0.75rem; 
        border-radius: 4px; 
        font-size: 0.85rem; 
        margin-right: 0.5rem; 
        display: inline-block; 
        margin-bottom: 0.5rem; 
    }
</style>
""", unsafe_allow_html=True)

st.title("🎛️ 多維篩選")
st.caption("設定財務指標條件，篩選符合條件的股票")

@st.cache_data(ttl=3600)
def load_data():
    df = get_stock_list()
    if df.empty or 'roe' not in df.columns:
        df = generate_sample_data()
    return df

df = load_data()

# 側邊欄
with st.sidebar:
    st.header("篩選條件")
    
    asset_type = st.selectbox("資產類型", list(ASSET_TYPES.keys()), format_func=lambda x: ASSET_TYPES[x])
    industry = st.selectbox("產業別", INDUSTRIES)
    exclude_loss = st.checkbox("排除虧損公司")
    
    st.divider()
    filters = {}
    
    st.subheader("獲利能力")
    roe_min = st.slider("ROE (%)", 0, 50, 0)
    if roe_min > 0: filters['roe'] = {'min': roe_min}
    
    st.subheader("估值指標")
    pe_max = st.slider("本益比上限", 5, 100, 100)
    if pe_max < 100: filters['pe'] = {'max': pe_max}
    
    pb_max = st.slider("PB 上限", 0.5, 10.0, 10.0, 0.5)
    if pb_max < 10: filters['pb'] = {'max': pb_max}
    
    div_min = st.slider("殖利率 (%)", 0.0, 15.0, 0.0, 0.5)
    if div_min > 0: filters['dividend_yield'] = {'min': div_min}
    
    st.subheader("財務安全")
    debt_max = st.slider("負債率上限 (%)", 0, 100, 100)
    if debt_max < 100: filters['debt_ratio'] = {'max': debt_max}

# 執行篩選
filtered_df = custom_screen(df, filters=filters, industry=industry, asset_type=asset_type, exclude_loss=exclude_loss)
if not filtered_df.empty and 'roe' in filtered_df.columns:
    filtered_df = calculate_score(filtered_df)

# 統計
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("符合條件", f"{len(filtered_df)} 檔")
with col2:
    st.metric("已設定條件", f"{len(filters)} 項")
with col3:
    st.metric("通過率", f"{len(filtered_df) / len(df) * 100:.1f}%")

st.divider()

# 已應用條件
if filters:
    conditions_html = ""
    for key, value in filters.items():
        name = INDICATORS.get(key, {}).get('name', key)
        unit = INDICATORS.get(key, {}).get('unit', '')
        if value.get('min'):
            conditions_html += f'<span class="filter-badge">{name} > {value["min"]}{unit}</span>'
        if value.get('max'):
            conditions_html += f'<span class="filter-badge">{name} < {value["max"]}{unit}</span>'
    st.markdown(conditions_html, unsafe_allow_html=True)
    st.divider()

# 結果
st.subheader("篩選結果")

if filtered_df.empty:
    st.warning("沒有符合條件的股票")
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        sort_by = st.selectbox("排序", ['score', 'roe', 'pe', 'dividend_yield'], 
                               format_func=lambda x: {'score': '評分', 'roe': 'ROE', 'pe': 'PE', 'dividend_yield': '殖利率'}[x])
    with col2:
        sort_asc = st.selectbox("順序", ["降冪", "升冪"]) == "升冪"
    
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by, ascending=sort_asc)
    
    display_cols = ['stock_id', 'name', 'industry', 'score', 'roe', 'pe', 'pb', 'dividend_yield', 'debt_ratio']
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[display_cols].head(100).copy()
    
    column_names = {'stock_id': '代號', 'name': '名稱', 'industry': '產業', 'score': '評分',
                    'roe': 'ROE(%)', 'pe': 'PE', 'pb': 'PB', 'dividend_yield': '殖利率(%)', 'debt_ratio': '負債率(%)'}
    display_df = display_df.rename(columns=column_names)
    
    for col in display_df.select_dtypes(include=['float64']).columns:
        display_df[col] = display_df[col].round(2)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.download_button("匯出 CSV", filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                       "filtered_stocks.csv", "text/csv")

# 指標說明
with st.expander("指標說明"):
    for key, info in INDICATORS.items():
        ideal = f"> {info['ideal_min']}" if info.get('ideal_min') else f"< {info['ideal_max']}" if info.get('ideal_max') else "N/A"
        st.markdown(f"**{info['name']}** - {info['description']} (理想值: {ideal}{info.get('unit', '')})")
