"""
台股智選系統 - 主程式
Taiwan Stock Selection System - Main Application

使用 Streamlit 作為網頁介面框架
Glarity 風格設計
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

# from src.database import init_db
from src.data_fetcher import get_stock_list, generate_sample_data, load_robust_data, get_data_update_time
from src.stock_analyzer import get_top_stocks
from src.styles import GLARITY_STYLE
from config import STRATEGIES, STRATEGY_SUMMARIES
from src.help_docs import SCORING_HELP
from src.env_validator import validate_env_vars

# 驗證環境變數
_env_result = validate_env_vars(verbose=False)
if not _env_result['finmind_token']:
    st.warning("⚠️ 未設定 FINMIND_TOKEN，資料更新功能無法使用。請參閱 `.env.example` 設定說明。")

# 初始化資料庫
# init_db()

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

# 隱藏側邊欄的 "main" 標籤，改用自定義標題
st.markdown("""
<style>
    /* 隱藏 main 頁面的預設導航標籤 */
    [data-testid="stSidebarNav"] li:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 側邊欄首頁連結
if st.sidebar.button("🏠 首頁", use_container_width=True, type="primary"):
    st.switch_page("main.py")
st.sidebar.markdown("---")

# 顯示資料更新時間
update_time = get_data_update_time()
st.sidebar.markdown(f"""
<div style="font-size: 0.8rem; color: #666; margin-bottom: 1rem;">
    🟢 資料狀態：已更新<br>
    🕒 {update_time}
</div>
""", unsafe_allow_html=True)


def main():
    """主程式"""
    # 載入資料
    # 載入資料 (加入快取機制)
    @st.cache_data(ttl=3600)
    def load_data():
        # 改用穩健資料載入（無模擬數據）
        df = load_robust_data()
        return df

    with st.spinner("正在載入股票資料..."):
        df = load_data()
    
    stock_count = len(df[df['asset_type'] == 'stock']) if 'asset_type' in df.columns else len(df)
    etf_count = len(df[df['asset_type'] == 'etf']) if 'asset_type' in df.columns else 0
    
    # 歡迎卡片
    st.markdown(f"""
    <div class="welcome-card">
        <h2>👋 歡迎使用台股智選系統！</h2>
        <p>這是一個使用 Python 開發的財務分析與選股工具。<br>
        支援 {len(df):,} 檔標的的財務指標分析、策略篩選和綜合評分排名。</p>
        <a href="#開始使用" class="primary-btn">👇 看系統說明</a>
    </div>
    """, unsafe_allow_html=True)
    
    # 統計卡片
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card highlight">
            <div class="number">120</div>
            <div class="label">精選標的（~85%市值）</div>
        </div>
        <div class="stat-card">
            <div class="number">50+50</div>
            <div class="label">台灣50+中型精選50</div>
        </div>
        <div class="stat-card">
            <div class="number">10+10</div>
            <div class="label">ETF+熱門股</div>
        </div>
        <div class="stat-card">
            <div class="number">11</div>
            <div class="label">財務指標</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 兩欄佈局
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">核心功能</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🔍 搜尋</h4>
            <p>支援股票代號和公司名稱搜尋，顯示完整財務資訊和投資分析。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🎛️ 篩選</h4>
            <p>4 種內建策略：成長股、價值股、高股息、優質股，搭配自訂條件篩選。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🏆 排名</h4>
            <p>0-10 分評分系統，Top N 排行榜，支援 CSV 匯出。</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <h4>🤖 AI 智慧選股</h4>
            <p>用自然語言說出您想要找的股票，AI 幫您自動解析與篩選。</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-header">資料特色</div>', unsafe_allow_html=True)
        
        # 動態取得統計數據
        stock_count = len(df) if not df.empty else 120
        
        st.markdown(f"""
        <div class="feature-card">
            <h4>📊 涵蓋範圍</h4>
            <p>{stock_count} 檔（台灣50+中型精選50+ETF10+熱門股10）</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>📈 分析深度</h4>
            <p>11 項財務指標</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🔗 資料來源</h4>
            <p>FinMind 真實數據</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # 快速預覽 Top 10
    st.markdown('<div class="section-header" id="開始使用">綜合評分 Top 10</div>', unsafe_allow_html=True)
    
    if not df.empty and 'roe' in df.columns:
        top_stocks = get_top_stocks(df, n=10)
        
        if not top_stocks.empty:
            # 欄位順序：一般股票指標在前，ETF 指標在後
            display_cols = ['stock_id', 'name', 'price', 'score', 'roe', 'pe', 'pb', 'debt_ratio', 'dividend_yield', 'dividend_years']
            display_cols = [c for c in display_cols if c in top_stocks.columns]
            display_df = top_stocks[display_cols].copy()
            
            # 加入序號欄位
            display_df.insert(0, '序號', range(1, len(display_df) + 1))
            
            # 統一欄位名稱（與篩選頁和排名頁一致）
            column_names = {'stock_id': '代號', 'name': '名稱', 'price': '股價', 'score': '評分',
                            'roe': '權益報酬率%(40%)', 'pe': '本益比(30%)', 'pb': '淨值比(15%)', 'debt_ratio': '負債率%(15%)',
                            'dividend_yield': '殖利率%', 'dividend_years': '配息年數'}
            display_df = display_df.rename(columns=column_names)
            
            for col in display_df.select_dtypes(include=['float64']).columns:
                display_df[col] = display_df[col].round(2)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("暫無評分資料")
    else:
        st.info("正在載入資料...")
    
    st.divider()
    
    # 新手引導提示
    st.info("👋 **第一次使用？** 展開下方說明了解系統如何幫你選股！")
    
    # 系統邏輯說明（用一般人能理解的語言）- 預設折疊
    with st.expander("💡 這個系統如何幫你選股？", expanded=False):
        st.markdown("""
        ### 🤔 為什麼需要這個系統？
        
        台股有超過 **2,000 檔股票**，要一檔一檔研究太花時間了！
        這個系統幫你**一次分析所有股票**，找出符合你需求的好股票。
        
        ---
        
        ### 📊 系統怎麼判斷好股票？
        
        我們用 **11 個財務指標** 來分析公司，就像體檢報告一樣：
        
        | 檢查項目 | 對應指標 | 好的標準 |
        |---------|---------|---------|
        | 公司賺錢嗎？ | 權益報酬率(ROE)| 越高越好，> 15% 很棒 |
        | 股價貴不貴？ | 本益比(PE)| 10-20 倍算合理 |
        | 會不會倒？ | 負債率 | 越低越安全，< 50% 較好 |
        | 有股息嗎？ | 殖利率 | > 4% 就算高股息 |
        
        ---
        
        ### 🏆 評分怎麼算？
        
        > 綜合評分只看 **4 個最重要的指標**，幫你快速篩選
        
        ```
        總分 = 獲利能力(40%) + 估值合理性(30%) + 資產價值(15%) + 財務安全(15%)
        ```
        
        - 滿分 **10 分**，8 分以上是 A 等級，算是優質股
        - 評分高不代表一定賺錢，只代表**基本面不錯**
        
        ---
        
        ### 🎯 四種策略怎麼選？
        
        | 你的需求 | 建議策略 | 適合的人 |
        |---------|---------|---------|
        | 想賺價差 | 🚀 成長股 | 願意承擔風險、追求高報酬 |
        | 想撿便宜 | 💎 價值股 | 耐心等待、喜歡低買高賣 |
        | 想領股息 | 💰 高股息 | 存股族、喜歡穩定現金流 |
        | 不知道選什麼 | ⭐ 優質股 | 新手、想買好公司長期持有 |
        
        ---
        
        ### ⚠️ 重要提醒
        
        - 這是**選股工具**，不是買賣建議
        - 基本面好 ≠ 股價一定漲（短期可能波動）
        - 投資前請自行評估風險！
        """)
    
    # 系統說明（技術細節）
    with st.expander("📚 系統說明", expanded=False):
        tabs = st.tabs(["📖 使用指南", "📊 11項指標", "🏆 評分系統", "🎯 選股策略"])
        
        with tabs[0]:
            st.markdown("""
            ### 開始使用
            1. **🔍 搜尋**：輸入股票代號或名稱，查看完整財務資訊
            2. **🎛️ 篩選**：選擇快速策略或自訂條件篩選股票
            3. **🏆 排名**：查看 Top N 排行榜，匯出 CSV
            4. **🤖 AI智慧選股**：用自然語言描述，AI 幫您找股票
            
            ---
            
            ### 指標使用說明
            - **分析用**：系統提供 **11 項財務指標**，供個股詳細分析
            - **評分用**：綜合評分使用其中 **4 項核心指標**
            - **策略用**：各策略依特性使用 **不同指標組合**
            """)
        
        with tabs[1]:
            st.markdown("""
            ### 11 項財務指標一覽
            
            #### 🔷 獲利能力（5 項）
            | 指標 | 公式 | 說明 | 理想值 |
            |------|------|------|--------|
            | 權益報酬率(ROE) | 淨利 ÷ 股東權益 | 衡量公司運用股東資本創造利潤的能力 | > 15% |
            | 資產報酬率(ROA) | 淨利 ÷ 總資產 | 衡量公司運用總資產創造利潤的效率 | > 8% |
            | 淨利率 | 淨利 ÷ 營收 | 每一元營收中實際賺取的淨利 | > 10% |
            | 毛利率 | (營收-成本) ÷ 營收 | 每一元營收扣除直接成本後的毛利 | > 20% |
            | 營業利潤率 | 營業利益 ÷ 營收 | 本業經營的獲利能力 | > 10% |
            
            #### 🔷 估值指標（4 項）
            | 指標 | 公式 | 說明 | 理想值 |
            |------|------|------|--------|
            | 本益比(PE) | 股價 ÷ 每股盈餘 | 股價相對於每股盈餘的倍數 | 10~20 |
            | 淨值比(PB) | 股價 ÷ 每股淨值 | 股價相對於每股淨值的倍數 | < 2 |
            | 每股盈餘(EPS) | 稅後淨利 ÷ 股數 | 每一股可分配到的盈餘 | > 3 元 |
            | 殖利率 | 現金股利 ÷ 股價 | 每年現金股利相對於股價的比率 | > 4% |
            
            #### 🔷 財務安全（2 項）
            | 指標 | 公式 | 說明 | 理想值 |
            |------|------|------|--------|
            | 配息年數 | 連續配息年數 | 公司連續發放現金股利的年數 | > 5 年 |
            | 負債率 | 總負債 ÷ 總資產 | 公司總負債佔總資產的比例 | < 50% |
            """)
        
        with tabs[2]:
            st.markdown(SCORING_HELP)
        
        with tabs[3]:
            st.markdown("""
            ### 選股策略使用的指標
            
            > 不同策略使用 **不同的指標組合**，依投資目標而異
            
            ---
            
            | 策略 | 使用指標 | 篩選條件 |
            |------|---------|---------|
            | 🚀 **成長股** | 權益報酬率、淨利率、負債率 | 權益報酬率≥20%, 淨利率≥20%, 負債率≤50% |
            | 💎 **價值股** | 本益比、淨值比、權益報酬率、殖利率 | 本益比≤15倍, 淨值比≤2倍, 權益報酬率≥10%, 殖利率≥3% |
            | 💰 **高股息** | 殖利率、配息年數、負債率 | 殖利率≥5%, 配息年數≥5年, 負債率≤60% |
            | ⭐ **優質股** | 權益報酬率、本益比、負債率 | 權益報酬率≥15%, 本益比:10-20倍, 負債率≤40% |
            
            ---
            
            **自訂篩選** 可使用：ROE、本益比、殖利率、負債率等指標自由組合
            """)
    
    # 頁尾
    st.markdown('<div class="footer">台股智選系統 v1.0</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
