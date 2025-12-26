"""
台股智選系統 - 應用程式入口
Taiwan Stock Selection System - Application Entry Point
"""

import streamlit as st

# 設定頁面
st.set_page_config(
    page_title="台股智選系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 導向首頁
st.switch_page("pages/0_🏠_首頁.py")
