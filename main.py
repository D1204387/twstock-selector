"""
台股智選系統 - 主程式
Taiwan Stock Selection System - Main Application

使用 Streamlit 作為網頁介面框架
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# 設定頁面
st.set_page_config(
    page_title="台股智選系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加入專案根目錄到 path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import init_db
from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_analyzer import get_top_stocks
from config import STRATEGIES, INDUSTRIES

# 初始化資料庫
init_db()


# 統一色彩主題 CSS - 灰色、藍色、淺藍
st.markdown("""
<style>
    /* 主色調定義 */
    :root {
        --primary-blue: #2563eb;
        --light-blue: #dbeafe;
        --dark-gray: #374151;
        --medium-gray: #6b7280;
        --light-gray: #f3f4f6;
        --border-gray: #e5e7eb;
    }
    
    /* 隱藏 Streamlit 預設元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 主標題 */
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    
    .main-header h1 {
        color: #1f2937;
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
    }
    
    .main-header p {
        color: #6b7280;
        margin-top: 0.5rem;
    }
    
    /* 統計卡片 */
    .stat-container {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .stat-box {
        flex: 1;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.25rem;
        text-align: center;
    }
    
    .stat-box.primary {
        background: #2563eb;
        border-color: #2563eb;
    }
    
    .stat-box.primary .stat-number,
    .stat-box.primary .stat-label {
        color: #ffffff;
    }
    
    .stat-number {
        font-size: 1.75rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
    }
    
    .stat-label {
        font-size: 0.875rem;
        color: #6b7280;
        margin-top: 0.25rem;
    }
    
    /* 區塊標題 */
    .section-title {
        color: #1f2937;
        font-size: 1.125rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2563eb;
        display: inline-block;
    }
    
    /* 功能列表 */
    .feature-list {
        background: #f9fafb;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    .feature-list h4 {
        color: #2563eb;
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
    }
    
    .feature-list p {
        color: #4b5563;
        margin: 0;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    /* 策略項目 */
    .strategy-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-left: 3px solid #2563eb;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .strategy-item h5 {
        color: #1f2937;
        margin: 0 0 0.25rem 0;
        font-size: 0.95rem;
    }
    
    .strategy-item p {
        color: #6b7280;
        margin: 0;
        font-size: 0.85rem;
    }
    
    /* 表格樣式優化 */
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }
    
    /* 頁尾 */
    .footer {
        text-align: center;
        color: #9ca3af;
        padding: 2rem 0 1rem 0;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """主程式"""
    # 標題
    st.markdown("""
    <div class="main-header">
        <h1>📈 台股智選系統</h1>
        <p>使用 Python 開發的財務分析與選股工具</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 載入資料
    with st.spinner("正在載入股票資料..."):
        df = get_stock_list()
        if df.empty or 'roe' not in df.columns:
            df = generate_sample_data()
    
    stock_count = len(df[df['asset_type'] == 'stock']) if 'asset_type' in df.columns else len(df)
    etf_count = len(df[df['asset_type'] == 'etf']) if 'asset_type' in df.columns else 0
    
    # 統計數據
    st.markdown(f"""
    <div class="stat-container">
        <div class="stat-box primary">
            <div class="stat-number">{len(df):,}</div>
            <div class="stat-label">總標的數</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{stock_count:,}</div>
            <div class="stat-label">上市櫃股票</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{etf_count}</div>
            <div class="stat-label">ETF</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">15</div>
            <div class="stat-label">財務指標</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 兩欄佈局
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-title">核心功能</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-list">
            <h4>🔍 智慧搜尋</h4>
            <p>支援股票代號和公司名稱搜尋，顯示完整財務資訊和投資分析。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-list">
            <h4>🎛️ 多維篩選</h4>
            <p>15 個財務指標自由組合篩選，包含獲利能力、估值、成長性和財務安全指標。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-list">
            <h4>📊 策略篩選</h4>
            <p>4 種內建策略：成長股、價值股、高股息、優質股，一鍵快速篩選。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-list">
            <h4>🏆 綜合排名</h4>
            <p>0-10 分評分系統，Top N 排行榜，支援 CSV 匯出。</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-title">內建策略</div>', unsafe_allow_html=True)
        
        for key, strategy in STRATEGIES.items():
            conditions = strategy.get('conditions', {})
            cond_list = []
            for k, v in conditions.items():
                if v.get('min') and v.get('max'):
                    cond_list.append(f"{k.upper()} {v['min']}~{v['max']}")
                elif v.get('min'):
                    cond_list.append(f"{k.upper()}>{v['min']}")
                elif v.get('max'):
                    cond_list.append(f"{k.upper()}<{v['max']}")
            
            st.markdown(f"""
            <div class="strategy-item">
                <h5>{strategy['name']}</h5>
                <p>{strategy['description']} · {', '.join(cond_list)}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # 快速預覽 Top 10
    st.markdown('<div class="section-title">綜合評分 Top 10</div>', unsafe_allow_html=True)
    
    if not df.empty and 'roe' in df.columns:
        top_stocks = get_top_stocks(df, n=10)
        
        if not top_stocks.empty:
            display_df = top_stocks[['stock_id', 'name', 'industry', 'roe', 'pe', 'pb', 'dividend_yield', 'score']].copy()
            display_df.columns = ['代號', '名稱', '產業', 'ROE(%)', 'PE', 'PB', '殖利率(%)', '評分']
            
            for col in ['ROE(%)', 'PE', 'PB', '殖利率(%)', '評分']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(2)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("暫無評分資料")
    else:
        st.info("正在載入資料...")
    
    # 使用說明
    with st.expander("使用說明"):
        st.markdown("""
        **開始使用**
        1. 搜尋：左側選單 → 🔍 搜尋 → 輸入股票代號或名稱
        2. 篩選：左側選單 → 🎛️ 篩選 → 設定財務指標條件
        3. 策略：左側選單 → 📊 策略 → 選擇內建策略
        4. 排名：左側選單 → 🏆 排名 → 查看 Top N 排行榜
        
        **指標說明**  
        每個指標旁都有說明按鈕，點擊可查看定義和理想值。
        """)
    
    # 頁尾
    st.markdown('<div class="footer">台股智選系統 v1.0 | Python 期末報告 | 2024</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
