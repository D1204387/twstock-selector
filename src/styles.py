"""
台股智選系統 - 共用樣式
統一色彩主題：灰色、藍色、淺藍
"""

# 主色調定義
COLORS = {
    'primary': '#2563eb',      # 主藍色
    'primary_dark': '#1d4ed8', # 深藍色
    'primary_light': '#dbeafe', # 淺藍色
    'dark_gray': '#374151',    # 深灰色
    'medium_gray': '#6b7280',  # 中灰色
    'light_gray': '#f3f4f6',   # 淺灰色
    'border': '#e5e7eb',       # 邊框灰色
    'white': '#ffffff',
    'text_primary': '#1f2937',
    'text_secondary': '#4b5563',
    'text_muted': '#9ca3af',
}

# 共用 CSS 樣式
COMMON_CSS = """
<style>
    /* 主色調變數 */
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --primary-light: #dbeafe;
        --gray-900: #111827;
        --gray-800: #1f2937;
        --gray-700: #374151;
        --gray-600: #4b5563;
        --gray-500: #6b7280;
        --gray-400: #9ca3af;
        --gray-300: #d1d5db;
        --gray-200: #e5e7eb;
        --gray-100: #f3f4f6;
        --gray-50: #f9fafb;
    }
    
    /* 隱藏 Streamlit 預設元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 標題樣式 */
    h1, h2, h3 {
        color: var(--gray-800) !important;
    }
    
    /* 統計卡片 */
    [data-testid="stMetric"] {
        background: var(--gray-50);
        border: 1px solid var(--gray-200);
        border-radius: 8px;
        padding: 1rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--gray-500) !important;
    }
    
    [data-testid="stMetricValue"] {
        color: var(--gray-800) !important;
    }
    
    /* 表格樣式 */
    .stDataFrame {
        border: 1px solid var(--gray-200) !important;
        border-radius: 8px !important;
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
    }
    
    .stButton > button:hover {
        background: var(--primary-dark) !important;
    }
    
    /* 下載按鈕 */
    .stDownloadButton > button {
        background: var(--gray-100) !important;
        color: var(--gray-700) !important;
        border: 1px solid var(--gray-300) !important;
    }
    
    .stDownloadButton > button:hover {
        background: var(--gray-200) !important;
    }
    
    /* 選擇框 */
    .stSelectbox > div > div {
        border-color: var(--gray-300) !important;
    }
    
    /* 分隔線 */
    hr {
        border-color: var(--gray-200) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--gray-50) !important;
        border-radius: 6px !important;
    }
    
    /* Info 提示框 */
    .stAlert {
        background: var(--primary-light) !important;
        border: 1px solid var(--primary) !important;
        color: var(--primary-dark) !important;
    }
    
    /* 側邊欄 */
    [data-testid="stSidebar"] {
        background: var(--gray-50) !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--gray-700) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--gray-100) !important;
        border-radius: 6px 6px 0 0 !important;
        color: var(--gray-600) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: white !important;
    }
    
    /* Radio 按鈕 */
    .stRadio > div {
        gap: 0.5rem;
    }
    
    .stRadio label {
        background: var(--gray-100) !important;
        padding: 0.5rem 1rem !important;
        border-radius: 6px !important;
        border: 1px solid var(--gray-200) !important;
    }
    
    .stRadio label[data-checked="true"] {
        background: var(--primary) !important;
        color: white !important;
        border-color: var(--primary) !important;
    }
</style>
"""

def inject_css():
    """注入共用 CSS 樣式"""
    import streamlit as st
    st.markdown(COMMON_CSS, unsafe_allow_html=True)
