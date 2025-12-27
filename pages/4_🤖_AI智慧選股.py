"""
台股智選系統 - AI 智慧選股頁面
Taiwan Stock Selection System - AI Smart Stock Selection Page
使用自然語言查詢股票
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data, load_robust_data
from src.stock_screener import custom_screen
from src.stock_analyzer import calculate_score
from src.ai_query import parse_natural_query, EXAMPLE_QUERIES
from src.styles import GLARITY_STYLE

st.set_page_config(page_title="AI 智慧選股 - 台股智選系統", page_icon="🤖", layout="wide")

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

# 隱藏側邊欄的 "main" 標籤
st.markdown('<style>[data-testid="stSidebarNav"] li:first-child { display: none; }</style>', unsafe_allow_html=True)

# 側邊欄首頁連結
if st.sidebar.button("🏠 首頁", use_container_width=True, type="primary", key="home_btn"):
    st.switch_page("main.py")
st.sidebar.markdown("---")

# 額外的 AI 頁面樣式
st.markdown("""
<style>
    .ai-input-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    .ai-input-card h3 {
        color: #1f2937;
        margin: 0 0 1rem 0;
    }
    .example-chip {
        display: inline-block;
        background: #dbeafe;
        color: #1d4ed8;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .example-chip:hover {
        background: #2563eb;
        color: white;
    }
    .ai-explanation {
        background: #f0f9ff;
        border-left: 4px solid #2563eb;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .ai-explanation p {
        margin: 0;
        color: #1e40af;
    }
    .filter-tag {
        display: inline-block;
        background: #e0e7ff;
        color: #3730a3;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI 智慧選股")
st.caption("用自然語言描述您想找的股票，AI 幫您篩選")

# API Key 設定 - 安全讀取
api_key = ""
try:
    if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

# 如果沒有在 secrets 中，嘗試從 session_state 取得
if not api_key:
    api_key = st.session_state.get("openai_api_key", "")

# 側邊欄設定 API Key
with st.sidebar:
    st.subheader("⚙️ 設定")
    input_key = st.text_input("OpenAI API Key", value=api_key, type="password", 
                               help="輸入您的 OpenAI API Key 以啟用 AI 功能")
    if input_key:
        st.session_state["openai_api_key"] = input_key
        api_key = input_key
    
    use_ai = st.checkbox("使用 AI 解析", value=bool(api_key), 
                         help="如果沒有 API Key，將使用關鍵字匹配")
    
    st.divider()
    st.caption("💡 提示：即使沒有 API Key，系統也能使用關鍵字匹配進行基本的口語查詢解析。")

# 載入資料
@st.cache_data(ttl=3600)
def load_data():
    df = load_robust_data()
    return df

df = load_data()

# AI 輸入區
st.markdown('<div class="ai-input-card">', unsafe_allow_html=True)
st.markdown("### 💬 請描述您想找的股票")

# 查詢輸入
query = st.text_input(
    "輸入查詢",
    placeholder="例如：每年配息超過5%的股票、最具成長性的科技股...",
    label_visibility="collapsed"
)

# 範例查詢
st.markdown("**💡 試試這些查詢：**")
example_cols = st.columns(4)
for i, example in enumerate(EXAMPLE_QUERIES[:8]):
    with example_cols[i % 4]:
        if st.button(example, key=f"example_{i}", use_container_width=True):
            query = example
            st.session_state["current_query"] = example
            st.rerun()

# 檢查 session_state 中的查詢
if "current_query" in st.session_state and not query:
    query = st.session_state["current_query"]

st.markdown('</div>', unsafe_allow_html=True)

# 執行查詢
if query:
    with st.spinner("🔄 AI 正在分析您的查詢..."):
        # 解析自然語言
        result = parse_natural_query(query, api_key=api_key, use_ai=use_ai and bool(api_key))
    
    # 顯示解析結果
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 AI 理解的篩選條件")
        
        # 顯示說明
        explanation = result.get("explanation", "")
        if explanation:
            st.markdown(f"""
            <div class="ai-explanation">
                <p>💡 {explanation}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 簡易中文對照表
        display_map = {
            'roe': 'ROE', 'pe': 'PE', 'pb': 'PB', 'eps': 'EPS',
            'dividend_yield': '殖利率', 'dividend_years': '配息年數',
            'debt_ratio': '負債率'
        }
        
        # 顯示篩選條件標籤
        filters = result.get("filters", {})
        if filters:
            # 映射表：自然語言關鍵字 -> DataFrame 欄位
            query_mapping = {
                'roe': 'roe', '股東權益報酬率': 'roe',
                'pe': 'pe', '本益比': 'pe',
                'pb': 'pb', '股價淨值比': 'pb',
                'dividend_yield': 'dividend_yield', '殖利率': 'dividend_yield',
                'debt_ratio': 'debt_ratio', '負債率': 'debt_ratio'
            }
            
            filter_html = ""
            for key, value in filters.items():
                name = display_map.get(key, key.upper())
                if value.get('min') and value.get('max'):
                    filter_html += f'<span class="filter-tag">{name}: {value["min"]}~{value["max"]}</span>'
                elif value.get('min'):
                    filter_html += f'<span class="filter-tag">{name}≥{value["min"]}</span>'
                elif value.get('max'):
                    filter_html += f'<span class="filter-tag">{name}≤{value["max"]}</span>'
            st.markdown(filter_html, unsafe_allow_html=True)
    
    with col2:
        strategy = result.get("strategy")
        if strategy:
            strategy_names = {
                "growth": "🚀 成長股",
                "value": "💎 價值股", 
                "dividend": "💰 高股息",
                "quality": "⭐ 優質股"
            }
            st.metric("匹配策略", strategy_names.get(strategy, strategy))
        
        if "error" in result:
            st.warning(f"⚠️ {result['error']}")
    
    st.divider()
    
    # 執行篩選
    if filters:
        filtered_df = custom_screen(df, filters=filters)
        
        # 產業別篩選
        industry = result.get("industry")
        if industry and 'industry' in filtered_df.columns:
            # 模糊匹配產業
            filtered_df = filtered_df[filtered_df['industry'].str.contains(industry, na=False)]
        
        if not filtered_df.empty and 'roe' in filtered_df.columns:
            filtered_df = calculate_score(filtered_df)
            filtered_df = filtered_df.sort_values('score', ascending=False)
        
        # 顯示統計
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("符合條件", f"{len(filtered_df)} 檔")
        with col2:
            st.metric("通過率", f"{len(filtered_df) / len(df) * 100:.1f}%")
        with col3:
            if not filtered_df.empty and 'score' in filtered_df.columns:
                st.metric("平均評分", f"{filtered_df['score'].mean():.2f}")
        
        st.divider()
        
        # 顯示結果
        if filtered_df.empty:
            st.warning("😢 沒有符合條件的股票，請嘗試調整您的查詢")
        else:
            st.subheader(f"📋 找到 {len(filtered_df)} 檔符合條件的股票")
            
            # 顯示全部結果
            show_count = len(filtered_df)
            
            # 表格
            display_cols = ['stock_id', 'name', 'price', 'score', 'roe', 'pe', 'pb', 'dividend_yield', 'debt_ratio']
            display_cols = [c for c in display_cols if c in filtered_df.columns]
            display_df = filtered_df[display_cols].head(show_count).copy()
            
            # 加入序號欄位
            display_df.insert(0, '序號', range(1, len(display_df) + 1))
            
            column_names = {'stock_id': '代號', 'name': '名稱', 'price': '股價', 'score': '評分',
                            'roe': 'ROE%(40%)', 'pe': 'PE(30%)', 'pb': 'PB(15%)', 'dividend_yield': '殖利率(%)', 'debt_ratio': '負債率%(15%)'}
            display_df = display_df.rename(columns=column_names)
            
            for col in display_df.select_dtypes(include=['float64']).columns:
                display_df[col] = display_df[col].round(2)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
            
            # 匯出全部資料的 CSV
            st.markdown("---")
            st.markdown(f"**匯出全部 {len(filtered_df)} 檔資料**")
            
            # 準備 CSV 資料（含序號）
            export_df = filtered_df[display_cols].copy()
            export_df.insert(0, '序號', range(1, len(export_df) + 1))
            export_df = export_df.rename(columns=column_names)
            
            # 儲存到專案目錄
            from pathlib import Path
            from datetime import datetime
            
            export_dir = Path(__file__).parent.parent / "exports"
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = export_dir / f"AI選股結果_{timestamp}.csv"
            
            if st.button(f"💾 儲存 CSV 到本機 ({len(filtered_df)} 檔)", type="primary"):
                export_df.to_csv(export_path, index=False, encoding='utf-8-sig')
                st.success(f"✅ 已儲存到：{export_path}")
                st.info(f"📂 請到 Finder 開啟：{export_dir}")
            
            st.caption("💡 點擊按鈕後，檔案會儲存到專案的 exports 資料夾")
    else:
        st.info("🤔 無法解析查詢條件，請嘗試更明確的描述")

else:
    # 沒有查詢時顯示說明
    st.info("👆 請在上方輸入您想找的股票描述，或點擊範例查詢開始")
    
    with st.expander("📚 使用說明"):
        st.markdown("""
        ### 如何使用 AI 智慧選股？
        
        1. **輸入查詢**：用自然語言描述您想找的股票類型
        2. **AI 解析**：系統會將您的描述轉換為篩選條件
        3. **查看結果**：瀏覽符合條件的股票清單
        
        ### 支援的查詢類型
        
        | 類型 | 範例 |
        |------|------|
        | 高股息 | 「每年配息超過5%」、「適合存股」 |
        | 成長股 | 「最具成長性」、「營收成長快」 |
        | 價值股 | 「被低估的」、「本益比低」 |
        | 優質股 | 「財務穩健」、「ROE高」 |
        
        ### 小技巧
        
        - 可以指定具體數字：「殖利率超過 6%」
        - 可以組合多個條件：「高 ROE 且低負債」
        - 越明確的描述，篩選結果越精準
        """)
