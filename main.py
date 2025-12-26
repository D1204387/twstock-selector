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

from src.database import init_db
from src.data_fetcher import get_stock_list, generate_sample_data
from src.stock_analyzer import get_top_stocks
from src.styles import GLARITY_STYLE
from config import STRATEGIES

# 初始化資料庫
init_db()

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


def main():
    """主程式"""
    # 載入資料
    with st.spinner("正在載入股票資料..."):
        df = get_stock_list()
        if df.empty or 'roe' not in df.columns:
            df = generate_sample_data()
    
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
            <div class="label">精選股票（~85%市值）</div>
        </div>
        <div class="stat-card">
            <div class="number">50+100</div>
            <div class="label">台灣50+中型100</div>
        </div>
        <div class="stat-card">
            <div class="number">10</div>
            <div class="label">熱門 ETF</div>
        </div>
        <div class="stat-card">
            <div class="number">15</div>
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
            <h4>🔍 智慧搜尋</h4>
            <p>支援股票代號和公司名稱搜尋，顯示完整財務資訊和投資分析。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>📊 策略篩選</h4>
            <p>4 種內建策略：成長股、價值股、高股息、優質股，搭配自訂條件篩選。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🏆 綜合排名</h4>
            <p>0-10 分評分系統，Top N 排行榜，支援 CSV 匯出。</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-header">內建策略</div>', unsafe_allow_html=True)
        
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
            <div class="feature-card">
                <h4>{strategy['name']}</h4>
                <p>{strategy['description']} · {', '.join(cond_list)}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # 快速預覽 Top 10
    st.markdown('<div class="section-header" id="開始使用">綜合評分 Top 10</div>', unsafe_allow_html=True)
    
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
        
        我們用 **15 個財務指標** 來分析公司，就像體檢報告一樣：
        
        | 檢查項目 | 對應指標 | 好的標準 |
        |---------|---------|---------|
        | 公司賺錢嗎？ | ROE（獲利能力）| 越高越好，> 15% 很棒 |
        | 股價貴不貴？ | PE（本益比）| 10-20 倍算合理 |
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
        tabs = st.tabs(["📖 使用指南", "📊 15項指標", "🏆 評分系統", "🎯 選股策略"])
        
        with tabs[0]:
            st.markdown("""
            ### 開始使用
            1. **🔍 搜尋**：輸入股票代號或名稱，查看完整財務資訊
            2. **📊 策略篩選**：選擇快速策略或自訂條件篩選股票
            3. **🏆 排名**：查看 Top N 排行榜，匯出 CSV
            4. **🤖 AI 選股**：用自然語言描述，AI 幫您找股票
            
            ---
            
            ### 指標使用說明
            - **分析用**：系統提供 **15 項財務指標**，供個股詳細分析
            - **評分用**：綜合評分使用其中 **4 項核心指標**
            - **策略用**：各策略依特性使用 **不同指標組合**
            """)
        
        with tabs[1]:
            st.markdown("""
            ### 15 項財務指標一覽
            
            #### 🔷 獲利能力（5 項）
            | 指標 | 公式 | 理想值 |
            |------|------|--------|
            | ROE | 淨利 ÷ 股東權益 | > 15% |
            | ROA | 淨利 ÷ 總資產 | > 8% |
            | 淨利率 | 淨利 ÷ 營收 | > 10% |
            | 毛利率 | (營收-成本) ÷ 營收 | > 20% |
            | 營業利潤率 | 營業利益 ÷ 營收 | > 10% |
            
            #### 🔷 估值指標（4 項）
            | 指標 | 公式 | 理想值 |
            |------|------|--------|
            | PE | 股價 ÷ EPS | 10~20 |
            | PB | 股價 ÷ 每股淨值 | < 2 |
            | EPS | 稅後淨利 ÷ 股數 | > 3 元 |
            | 殖利率 | 現金股利 ÷ 股價 | > 4% |
            
            #### 🔷 成長性（3 項）
            | 指標 | 公式 | 理想值 |
            |------|------|--------|
            | 營收成長率 | 營收年增率 | > 10% |
            | EPS成長率 | EPS年增率 | > 15% |
            | 配息年數 | 連續配息年數 | > 5 年 |
            
            #### 🔷 財務安全（3 項）
            | 指標 | 公式 | 理想值 |
            |------|------|--------|
            | 負債率 | 總負債 ÷ 總資產 | < 50% |
            | 流動比率 | 流動資產 ÷ 流動負債 | > 150% |
            | 速動比率 | (流動資產-存貨) ÷ 流動負債 | > 100% |
            """)
        
        with tabs[2]:
            st.markdown("""
            ### 評分系統說明
            
            > ⚠️ **注意**：綜合評分只使用 **4 項核心指標**，用於快速評估股票整體品質
            
            ---
            
            **總分 = ROE×40% + PE×30% + PB×15% + 負債率×15%**
            
            | 評分指標 | 權重 | 計算方式 | 為何選用 |
            |---------|------|---------|---------|
            | **ROE** | 40% | ROE ÷ 3 | 最重要的獲利指標 |
            | **PE** | 30% | 接近15分高 | 估值是否合理 |
            | **PB** | 15% | PB低分高 | 資產價值保護 |
            | **負債率** | 15% | 負債低分高 | 財務安全性 |
            
            **等級：** A+ (9-10) | A (8-9) | B+ (7-8) | B (6-7) | C (5-6) | D/F (<6)
            """)
        
        with tabs[3]:
            st.markdown("""
            ### 選股策略使用的指標
            
            > 不同策略使用 **不同的指標組合**，依投資目標而異
            
            ---
            
            | 策略 | 使用指標 | 篩選條件 |
            |------|---------|---------|
            | 🚀 **成長股** | ROE、EPS成長、營收成長 | ROE>15%, EPS成長>15%, 營收成長>10% |
            | 💎 **價值股** | PE、PB、ROE、殖利率 | PE<15, PB<2, ROE>10%, 殖利率>3% |
            | 💰 **高股息** | 殖利率、配息年數、負債率 | 殖利率>5%, 配息>5年, 負債率<60% |
            | ⭐ **優質股** | ROE、PE、負債率 | ROE>15%, PE 10-20, 負債率<40% |
            
            ---
            
            **自訂篩選** 可使用：ROE、PE、PB、殖利率、負債率等指標自由組合
            """)
    
    # 頁尾
    st.markdown('<div class="footer">台股智選系統 v1.0 | Python 期末報告 | 2024</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
