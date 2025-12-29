"""
台股智選系統 - 搜尋頁面
Taiwan Stock Selection System - Search Page
Glarity 風格設計
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data, load_robust_data
from src.stock_analyzer import analyze_stock, get_score_grade, is_roe_abnormal, get_score_breakdown, generate_score_explanation
from src.indicators import get_indicators_by_category
from src.styles import GLARITY_STYLE
from config import INDICATORS

st.set_page_config(page_title="搜尋 - 台股智選系統", page_icon="🔍", layout="wide")

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

# 隱藏側邊欄的 "main" 標籤
st.markdown('<style>[data-testid="stSidebarNav"] li:first-child { display: none; }</style>', unsafe_allow_html=True)

# 側邊欄首頁連結
if st.sidebar.button("🏠 首頁", use_container_width=True, type="primary", key="home_btn"):
    st.switch_page("main.py")
st.sidebar.markdown("---")

# 額外的搜尋頁樣式
st.markdown("""
<style>
    .score-card {
        background: #2563eb;
        color: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .score-card .score {
        font-size: 2.5rem;
        font-weight: 600;
    }
    .score-card .grade {
        font-size: 1rem;
        opacity: 0.9;
    }
    .stock-header {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .stock-header h2 {
        color: #1f2937;
        margin: 0 0 0.5rem 0;
    }
    .stock-header .meta {
        color: #6b7280;
        font-size: 0.9rem;
    }
    .analysis-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 股票搜尋")
st.caption("輸入股票代號或公司名稱，查看詳細資訊")

# 側邊欄說明
with st.sidebar:
    st.divider()
    with st.expander("📚 快速說明"):
        st.markdown("""
        **關鍵指標**
        - 權益報酬率 > 15%：獲利能力佳
        - 本益比 10-20：估值合理
        - 殖利率 > 4%：高股息
        - 負債率 < 50%：財務穩健
        
        [返回首頁查看完整說明](/)
        """)

@st.cache_data(ttl=3600)
def load_data():
    df = load_robust_data()
    return df

df = load_data()

# 搜尋區塊
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
                st.markdown(f"""
                <div class="stock-header">
                    <h2>{stock['name']} ({stock['stock_id']})</h2>
                    <div class="meta">
                        {f"產業：{stock['industry']}" if 'industry' in stock else ""} 
                        {f" | 市場：{stock['market']}" if 'market' in stock else ""}
                        {f" | 股價：${stock['price']:.2f}" if 'price' in stock and pd.notna(stock['price']) else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score">{analysis['score']:.1f}</div>
                    <div class="grade">等級 {analysis['grade']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # ROE 異常警示（更詳細的分級警示）
            roe_val = stock.get('roe')
            if pd.notna(roe_val):
                is_abnormal, reason, severity = is_roe_abnormal(roe_val)
                if is_abnormal:
                    if severity == 'danger':
                        st.error(f"🚨 **ROE 異常警示**：{reason}")
                    else:  # warning
                        st.warning(f"⚠️ **ROE 注意**：{reason}")
            
            # EPS 虧損警示
            eps_val = stock.get('eps')
            if pd.notna(eps_val) and eps_val < 0:
                st.warning(f"⚠️ **EPS 虧損**：每股盈餘為負值 ({eps_val:.2f} 元)，請審慎評估投資風險。")
            
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
                            
                            # 建立說明文字
                            description = info.get('description', '')
                            formula = info.get('formula', '')
                            ideal_text = ""
                            if info.get('ideal_min') and info.get('ideal_max'):
                                ideal_text = f"理想值: {info['ideal_min']} ~ {info['ideal_max']}{info.get('unit', '')}"
                            elif info.get('ideal_min'):
                                ideal_text = f"理想值: > {info['ideal_min']}{info.get('unit', '')}"
                            elif info.get('ideal_max'):
                                ideal_text = f"理想值: < {info['ideal_max']}{info.get('unit', '')}"
                            
                            # 組合說明文字
                            help_parts = []
                            if description:
                                help_parts.append(description)
                            if formula:
                                help_parts.append(f"公式: {formula}")
                            if ideal_text:
                                help_parts.append(ideal_text)
                            help_text = "\n".join(help_parts) if help_parts else None
                            
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                st.markdown(f"**{info.get('name', key)}**", help=help_text)
                            with c2:
                                if pd.notna(value):
                                    # 特別處理 ROE 異常值
                                    if key == 'roe':
                                        is_abnormal, reason, severity = is_roe_abnormal(value)
                                        if is_abnormal:
                                            if severity == 'danger':
                                                st.markdown(f"🔴 <span style='color: red;' title='{reason}'>{value:.2f}{info.get('unit', '')}</span>", unsafe_allow_html=True)
                                            else:  # warning
                                                st.markdown(f"🟡 <span style='color: orange;' title='{reason}'>{value:.2f}{info.get('unit', '')}</span>", unsafe_allow_html=True)
                                        else:
                                            st.markdown(f"{value:.2f}{info.get('unit', '')}")
                                    # 其他指標：負值顯示紅色
                                    elif value < 0:
                                        st.markdown(f"🔴 <span style='color: red;'>{value:.2f}{info.get('unit', '')}</span>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"{value:.2f}{info.get('unit', '')}")
                                else:
                                    st.markdown("N/A")
            
            with col2:
                st.subheader("📊 指標評分儀表板")
                
                # 判斷是否為 ETF
                is_etf = str(stock.get('stock_id', '')).startswith('00')
                
                # 進度條樣式
                def render_progress_bar(label, value, score, weight=None, unit=""):
                    """渲染單一指標的進度條"""
                    # 根據分數決定顏色
                    if score >= 8:
                        color = "#22c55e"  # 綠色
                    elif score >= 6:
                        color = "#3b82f6"  # 藍色
                    elif score >= 4:
                        color = "#f59e0b"  # 橙色
                    else:
                        color = "#ef4444"  # 紅色
                    
                    percentage = min(100, score * 10)
                    weight_text = f" ({weight})" if weight else ""
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span style="font-weight: 500; color: #374151;">{label}{weight_text}</span>
                            <span style="color: #6b7280;">{value}{unit} → <strong style="color: {color};">{score:.1f} 分</strong></span>
                        </div>
                        <div style="background: #e5e7eb; border-radius: 4px; height: 12px; overflow: hidden;">
                            <div style="background: {color}; width: {percentage}%; height: 100%; border-radius: 4px; transition: width 0.3s;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if is_etf:
                    # ETF 評分儀表板
                    from src.stock_analyzer import score_dividend_yield, score_dividend_years
                    
                    div_yield = stock.get('dividend_yield', 0) or 0
                    div_s = score_dividend_yield(div_yield)
                    
                    years = stock.get('dividend_years', 0) or 0
                    years_s = score_dividend_years(years)
                    
                    total_score = div_s * 0.8 + years_s * 0.2
                    
                    render_progress_bar("殖利率", f"{div_yield:.2f}", div_s, "80%", "%")
                    render_progress_bar("配息年數", f"{int(years)}", years_s, "20%", " 年")
                    
                    # 總分區塊
                    grade = get_score_grade(total_score)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 1rem; border-radius: 8px; margin-top: 0.5rem; text-align: center;">
                        <span style="font-size: 0.85rem;">ETF 評分合計</span><br>
                        <span style="font-size: 1.8rem; font-weight: bold;">{total_score:.2f}</span>
                        <span style="font-size: 0.9rem;"> / 10 分</span>
                        <span style="background: rgba(255,255,255,0.2); padding: 0.2rem 0.6rem; border-radius: 4px; margin-left: 0.5rem; font-weight: bold;">{grade} 級</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    # 一般股票評分儀表板
                    from src.stock_analyzer import score_roe, score_pe, score_pb, score_debt_ratio
                    
                    roe_val = stock.get('roe', 0) or 0
                    roe_s = score_roe(roe_val)
                    
                    pe_val = stock.get('pe', 0) or 0
                    pe_s = score_pe(pe_val)
                    
                    pb_val = stock.get('pb', 0) or 0
                    pb_s = score_pb(pb_val)
                    
                    debt_val = stock.get('debt_ratio', 0) or 0
                    debt_s = score_debt_ratio(debt_val)
                    
                    total_score = roe_s * 0.4 + pe_s * 0.3 + pb_s * 0.15 + debt_s * 0.15
                    
                    render_progress_bar("權益報酬率", f"{roe_val:.2f}", roe_s, "40%", "%")
                    render_progress_bar("本益比", f"{pe_val:.2f}", pe_s, "30%", " 倍")
                    render_progress_bar("淨值比", f"{pb_val:.2f}", pb_s, "15%", " 倍")
                    render_progress_bar("負債率", f"{debt_val:.2f}", debt_s, "15%", "%")
                    
                    # 總分區塊
                    grade = get_score_grade(total_score)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 1rem; border-radius: 8px; margin-top: 0.5rem; text-align: center;">
                        <span style="font-size: 0.85rem;">綜合評分</span><br>
                        <span style="font-size: 1.8rem; font-weight: bold;">{total_score:.2f}</span>
                        <span style="font-size: 0.9rem;"> / 10 分</span>
                        <span style="background: rgba(255,255,255,0.2); padding: 0.2rem 0.6rem; border-radius: 4px; margin-left: 0.5rem; font-weight: bold;">{grade} 級</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 📊 評分明細區塊
                st.subheader("📊 評分明細")
                
                # 取得評分明細
                score_breakdown = get_score_breakdown(stock)
                is_etf_stock = str(stock.get('stock_id', '')).startswith('00')
                
                if is_etf_stock:
                    # ETF 評分明細表格
                    breakdown_data = [
                        {
                            "指標": "殖利率",
                            "數值": f"{stock.get('dividend_yield', 0):.1f}%",
                            "分數": f"{score_breakdown['dividend_yield']['score']:.1f}",
                            "權重": "80%",
                            "貢獻": f"{score_breakdown['dividend_yield']['weighted_score']:.1f}"
                        },
                        {
                            "指標": "配息年數",
                            "數值": f"{int(stock.get('dividend_years', 0) or 0)} 年",
                            "分數": f"{score_breakdown['dividend_years']['score']:.1f}",
                            "權重": "20%",
                            "貢獻": f"{score_breakdown['dividend_years']['weighted_score']:.1f}"
                        }
                    ]
                else:
                    # 一般個股評分明細表格
                    breakdown_data = [
                        {
                            "指標": "權益報酬率 (ROE)",
                            "數值": f"{stock.get('roe', 0):.1f}%",
                            "分數": f"{score_breakdown['roe']['score']:.1f}",
                            "權重": "40%",
                            "貢獻": f"{score_breakdown['roe']['weighted_score']:.1f}"
                        },
                        {
                            "指標": "本益比 (PE)",
                            "數值": f"{stock.get('pe', 0):.1f}",
                            "分數": f"{score_breakdown['pe']['score']:.1f}",
                            "權重": "30%",
                            "貢獻": f"{score_breakdown['pe']['weighted_score']:.1f}"
                        },
                        {
                            "指標": "淨值比 (PB)",
                            "數值": f"{stock.get('pb', 0):.1f}",
                            "分數": f"{score_breakdown['pb']['score']:.1f}",
                            "權重": "15%",
                            "貢獻": f"{score_breakdown['pb']['weighted_score']:.1f}"
                        },
                        {
                            "指標": "負債率",
                            "數值": f"{stock.get('debt_ratio', 0):.1f}%",
                            "分數": f"{score_breakdown['debt_ratio']['score']:.1f}",
                            "權重": "15%",
                            "貢獻": f"{score_breakdown['debt_ratio']['weighted_score']:.1f}"
                        }
                    ]
                
                # 顯示表格
                breakdown_df = pd.DataFrame(breakdown_data)
                st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
                
                # 口語化說明
                explanation = generate_score_explanation(stock.to_dict(), analysis)
                st.info(f"💬 **總評**：{explanation}")
                
                # 優缺點
                st.subheader("投資分析")
                if analysis['strengths']:
                    for s in analysis['strengths']:
                        st.markdown(f"✅ {s}")
                if analysis['weaknesses']:
                    for w in analysis['weaknesses']:
                        st.markdown(f"⚠️ {w}")
else:
    # 未輸入搜尋條件時，顯示使用指南
    st.subheader("💡 使用指南")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔍 搜尋方式
        
        **股票代號搜尋**
        - 輸入股票代號如 `2330`、`2317`
        - 支援部分代號搜尋
        
        **公司名稱搜尋**
        - 輸入公司名稱如 `台積電`、`鴻海`
        - 支援模糊搜尋
        
        **ETF 搜尋**
        - 輸入 ETF 代號如 `0050`、`0056`
        - 在下拉選單選擇「ETF」可過濾
        """)
    
    with col2:
        st.markdown("""
        ### 📊 功能說明
        
        **詳細資訊**
        - 查看股票的財務指標
        - 進度條儀表板顯示各項評分
        - 優缺點分析
        
        **快速連結**
        """)
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            st.page_link("pages/3_🏆_排名.py", label="🏆 排名", help="查看評分最高的股票")
        with col_l2:
            st.page_link("pages/2_🎛️_篩選.py", label="🎛️ 篩選", help="自訂條件篩選")
        with col_l3:
            st.page_link("pages/4_🤖_AI智慧選股.py", label="🤖 AI選股", help="用自然語言查詢")
    
    st.divider()
    
    # 顯示資料庫統計
    st.subheader("📈 資料庫概況")
    
    total = len(df)
    stocks = len(df[df['asset_type'] == 'stock']) if 'asset_type' in df.columns else total
    etfs = len(df[df['asset_type'] == 'etf']) if 'asset_type' in df.columns else 0
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("總標的數", f"{total} 檔")
    col_b.metric("股票", f"{stocks} 檔")
    col_c.metric("ETF", f"{etfs} 檔")
    
    # 熱門搜尋建議
    st.subheader("🔥 熱門股票")
    popular_stocks = df.nlargest(5, 'score')[['stock_id', 'name', 'score']].values.tolist() if 'score' in df.columns else []
    if popular_stocks:
        cols = st.columns(5)
        for i, (sid, name, score) in enumerate(popular_stocks):
            with cols[i]:
                st.button(f"{sid} {name}", key=f"popular_{sid}", help=f"評分: {score:.1f}")
