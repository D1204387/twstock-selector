# Glarity 風格全域樣式

# 全域 CSS 樣式 - 適用於所有頁面
GLARITY_STYLE = """
<style>
    /* 全域背景 */
    .stApp {
        background-color: #f3f4f6;
    }
    
    /* 隱藏預設元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 側邊欄 - 淺藍灰色 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8f0fe 0%, #f0f4f8 100%);
        border-right: 1px solid #e5e7eb;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label {
        color: #374151 !important;
    }
    
    /* 側邊欄連結 */
    [data-testid="stSidebar"] a {
        color: #2563eb !important;
        font-weight: 500;
    }
    
    /* 白色卡片容器 */
    .card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    
    /* 歡迎區塊 */
    .welcome-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin: 1.5rem 0;
    }
    
    .welcome-card h2 {
        color: #1f2937;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0 0 0.75rem 0;
    }
    
    .welcome-card p {
        color: #6b7280;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0;
    }
    
    /* 主按鈕 - 深藍色 */
    .primary-btn {
        background: #2563eb !important;
        color: #ffffff !important;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        cursor: pointer;
        display: inline-block;
        margin-top: 1rem;
        text-decoration: none !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }
    
    .primary-btn:hover {
        background: #1d4ed8 !important;
        color: #ffffff !important;
        text-decoration: none !important;
    }
    
    .primary-btn:visited {
        color: #ffffff !important;
    }
    
    /* 統計卡片 */
    .stat-row {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .stat-card {
        flex: 1;
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    
    .stat-card.highlight {
        background: #2563eb;
        color: white;
    }
    
    .stat-card .number {
        font-size: 1.75rem;
        font-weight: 600;
        color: #1f2937;
    }
    
    .stat-card.highlight .number {
        color: white;
    }
    
    .stat-card .label {
        font-size: 0.85rem;
        color: #6b7280;
        margin-top: 0.25rem;
    }
    
    .stat-card.highlight .label {
        color: rgba(255,255,255,0.85);
    }
    
    /* 區塊標題 */
    .section-header {
        color: #1f2937;
        font-size: 1.125rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* 功能卡片 */
    .feature-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        border-left: 3px solid #2563eb;
    }
    
    .feature-card h4 {
        color: #2563eb;
        font-size: 0.95rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
    }
    
    .feature-card p {
        color: #6b7280;
        font-size: 0.875rem;
        margin: 0;
        line-height: 1.5;
    }
    
    /* 表格容器 */
    .stDataFrame {
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    
    /* 表格欄名置中 */
    .stDataFrame th {
        text-align: center !important;
    }
    
    /* 頁尾 */
    .footer {
        text-align: center;
        color: #9ca3af;
        padding: 2rem 0 1rem 0;
        font-size: 0.8rem;
    }
    
    /* Expander 樣式 */
    .streamlit-expanderHeader {
        background: #ffffff !important;
        border-radius: 8px !important;
    }
    
    /* 下載按鈕 */
    .stDownloadButton button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }
    
    /* Metric 卡片 */
    [data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    
    /* Radio 按鈕 */
    .stRadio > div {
        background: #ffffff;
        border-radius: 8px;
        padding: 0.5rem;
    }
</style>
"""
