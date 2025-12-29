"""
台股智選系統 - 策略與篩選頁面
Taiwan Stock Selection System - Strategy & Filter Page
Glarity 風格設計
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_stock_list, generate_sample_data, load_robust_data
from src.stock_screener import custom_screen, apply_strategy, format_strategy_conditions, get_strategy_matches_count
from src.stock_analyzer import calculate_score
from src.styles import GLARITY_STYLE
from config import INDICATORS, INDUSTRIES, ASSET_TYPES, STRATEGIES, COLUMN_NAMES, STRATEGY_SUMMARIES

st.set_page_config(page_title="策略篩選 - 台股智選系統", page_icon="📊", layout="wide")

# 套用 Glarity 風格
st.markdown(GLARITY_STYLE, unsafe_allow_html=True)

# 隱藏側邊欄的 "main" 標籤
st.markdown('<style>[data-testid="stSidebarNav"] li:first-child { display: none; }</style>', unsafe_allow_html=True)

# 側邊欄首頁連結
if st.sidebar.button("🏠 首頁", use_container_width=True, type="primary", key="home_btn"):
    st.switch_page("main.py")
st.sidebar.markdown("---")

# 額外的篩選頁樣式
st.markdown("""
<style>
    .strategy-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border: 2px solid transparent;
        transition: all 0.2s;
    }
    .strategy-card:hover {
        border-color: #2563eb;
    }
    .strategy-card h4 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1rem;
    }
    .strategy-card .desc {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .strategy-card .count {
        color: #2563eb;
        font-weight: 600;
        font-size: 1.25rem;
    }
    .filter-section {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin: 1rem 0;
    }
    .result-badge {
        display: inline-block;
        background: #dbeafe;
        color: #1d4ed8;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 策略篩選")
st.caption("選擇快速策略或自訂條件，找出符合需求的股票")

# 頁面使用說明
with st.expander("💡 如何使用本頁", expanded=False):
    st.markdown("""
    ### 📌 使用流程
    
    **方法一：快速策略（推薦新手）**
    1. 在下方「快速策略」區選擇一個策略（如成長股、價值股）
    2. 點擊「選擇」按鈕
    3. 系統自動篩選符合條件的股票
    
    **方法二：自訂篩選**
    1. 點擊「自訂篩選」按鈕
    2. 展開「自訂篩選條件」
    3. 調整各指標滑桿設定條件
    4. 結果即時更新
    
    ### 📊 指標速查
    | 指標 | 說明 | 理想值 |
    |------|------|--------|
    | ROE (%) | 權益報酬率，衡量獲利能力 | > 15% |
    | 本益比上限 | 股價相對盈餘的倍數 | 10-20 倍 |
    | 殖利率 (%) | 每年配息相對股價的比率 | > 4% |
    | 負債率上限 (%) | 負債占總資產比例 | < 50% |
    """)

# 側邊欄說明
with st.sidebar:
    st.divider()
    with st.expander("📚 快速說明"):
        st.markdown("**策略說明**")
        for key, strategy in STRATEGIES.items():
            summary = STRATEGY_SUMMARIES.get(key, "")
            st.markdown(f"- {strategy['name']}：{summary}")
        st.markdown("\n[返回首頁查看完整說明](/)")

@st.cache_data(ttl=3600)
def load_data():
    df = load_robust_data()
    return df

df = load_data()
strategy_counts = get_strategy_matches_count(df)

# ========== 快速策略區 ==========
st.subheader("🚀 快速策略")

# 策略卡片 - 可點擊
cols = st.columns(4)
strategy_keys = list(STRATEGIES.keys())

# 初始化 session state
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = None

for i, (key, strategy) in enumerate(STRATEGIES.items()):
    with cols[i]:
        count = strategy_counts.get(key, 0)
        # 生成條件標準文字
        conditions = strategy.get('conditions', {})
        criteria_list = []
        # 簡易中文對照表（含單位）
        display_map = {
            'roe': ('權益報酬率', '%'),
            'roa': ('資產報酬率', '%'),
            'net_profit_margin': ('淨利率', '%'),
            'gross_margin': ('毛利率', '%'),
            'operating_margin': ('營業利潤率', '%'),
            'pe': ('本益比', '倍'),
            'pb': ('淨值比', '倍'),
            'eps': ('每股盈餘', '元'),
            'dividend_yield': ('殖利率', '%'),
            'dividend_years': ('配息年數', '年'),
            'debt_ratio': ('負債率', '%')
        }

        for cond_key, cond_val in conditions.items():
            name_info = display_map.get(cond_key, (cond_key.upper(), ''))
            name, unit = name_info if isinstance(name_info, tuple) else (name_info, '')
            if 'min' in cond_val and 'max' in cond_val:
                criteria_list.append(f"{name}: {cond_val['min']}-{cond_val['max']}{unit}")
            elif 'min' in cond_val:
                criteria_list.append(f"{name} ≥ {cond_val['min']}{unit}")
            elif 'max' in cond_val:
                criteria_list.append(f"{name} ≤ {cond_val['max']}{unit}")
        criteria_text = " | ".join(criteria_list) if criteria_list else ""
        
        # 判斷是否為選中狀態
        is_selected = st.session_state.selected_strategy == key
        border_style = "border: 2px solid #2563eb;" if is_selected else ""
        
        st.markdown(f"""
        <div class="strategy-card" style="min-height: 150px; {border_style}">
            <h4>{strategy['name']}</h4>
            <div class="desc">{strategy['description']}</div>
            <div class="criteria" style="font-size: 0.7rem; color: #6b7280; margin: 0.5rem 0; min-height: 2.5rem;">{criteria_text}</div>
            <div class="count">{count} 檔</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 可點擊按鈕
        if st.button(f"選擇", key=f"btn_{key}", use_container_width=True):
            st.session_state.selected_strategy = key
            st.rerun()

# 自訂篩選按鈕
st.markdown("")
col_custom, col_clear = st.columns([1, 1])
with col_custom:
    if st.button("🔧 自訂篩選", use_container_width=True):
        st.session_state.selected_strategy = None
        st.rerun()
with col_clear:
    if st.session_state.selected_strategy:
        if st.button("❌ 清除選擇", use_container_width=True):
            st.session_state.selected_strategy = None
            st.rerun()

selected_strategy = st.session_state.selected_strategy

st.divider()

# ========== 篩選條件區 ==========
with st.expander("⚙️ 自訂篩選條件", expanded=(selected_strategy is None)):
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        asset_type = st.selectbox("資產類型", list(ASSET_TYPES.keys()), format_func=lambda x: ASSET_TYPES[x])
        industry = st.selectbox("產業別", INDUSTRIES)
    
    with col2:
        roe_min = st.slider(
            "ROE (%)", 0, 50, 0,
            help="權益報酬率：衡量公司運用股東資本創造利潤的能力。\n理想值：> 15%，越高代表獲利能力越強。"
        )
        pe_max = st.slider(
            "本益比上限", 5, 100, 100,
            help="本益比 (PE)：股價 ÷ 每股盈餘。\n理想區間：10-20 倍。過高可能偏貴，過低可能有隱憂。"
        )
    
    with col3:
        div_min = st.slider(
            "殖利率 (%)", 0.0, 15.0, 0.0, 0.5,
            help="現金殖利率：每年配息 ÷ 股價 × 100%。\n理想值：> 4%，適合追求穩定現金流的投資人。"
        )
        debt_max = st.slider(
            "負債率上限 (%)", 0, 100, 100,
            help="負債比率：總負債 ÷ 總資產 × 100%。\n理想值：< 50%，越低代表財務越穩健。"
        )
    
    exclude_loss = st.checkbox("排除虧損公司")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 執行篩選 ==========
if selected_strategy:
    filtered_df = apply_strategy(df, selected_strategy)
    filter_mode = f"策略：{STRATEGIES[selected_strategy]['name']}"
    st.success(f"✅ 已選擇策略：**{STRATEGIES[selected_strategy]['name']}**，共 {len(filtered_df)} 檔符合條件")
else:
    filters = {}
    if roe_min > 0: filters['roe'] = {'min': roe_min}
    if pe_max < 100: filters['pe'] = {'max': pe_max}
    if div_min > 0: filters['dividend_yield'] = {'min': div_min}
    if debt_max < 100: filters['debt_ratio'] = {'max': debt_max}
    
    filtered_df = custom_screen(df, filters=filters, industry=industry, asset_type=asset_type, exclude_loss=exclude_loss)
    filter_mode = "自訂篩選"

if not filtered_df.empty and 'roe' in filtered_df.columns:
    filtered_df = calculate_score(filtered_df)
    filtered_df = filtered_df.sort_values('score', ascending=False)

# ========== 統計數據 ==========
col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
with col1:
    st.metric("篩選模式", filter_mode)
with col2:
    st.metric("符合條件", f"{len(filtered_df)} 檔")
with col3:
    st.metric("通過率", f"{len(filtered_df) / len(df) * 100:.1f}%")
with col4:
    avg_score = filtered_df['score'].mean() if not filtered_df.empty and 'score' in filtered_df.columns else 0
    st.metric("平均評分", f"{avg_score:.2f}")

st.divider()

# ========== 結果顯示 ==========
if filtered_df.empty:
    st.warning("沒有符合條件的股票，請調整篩選條件")
else:
    st.subheader("📋 篩選結果")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        sort_by = st.selectbox("排序依據", ['score', 'roe', 'pe', 'dividend_yield'], 
                               format_func=lambda x: {'score': '評分', 'roe': '權益報酬率', 'pe': '本益比', 'dividend_yield': '殖利率'}[x],
                               label_visibility="collapsed")
    with col2:
        sort_asc = st.selectbox("順序", ["降冪", "升冪"], label_visibility="collapsed") == "升冪"
    
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by, ascending=sort_asc)
    
    # 顯示設定
    col_a, col_b = st.columns([1, 3])
    with col_a:
        display_mode = st.selectbox("顯示方式", ["分頁", "全部"], label_visibility="collapsed")
    with col_b:
        if display_mode == "分頁":
            page_size = st.selectbox("每頁筆數", [20, 50, 100], index=1, label_visibility="collapsed")
        else:
            page_size = len(filtered_df)
    
    # 分頁邏輯
    total_count = len(filtered_df)
    total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
    
    if display_mode == "分頁" and total_pages > 1:
        page = st.number_input(f"頁數 (共 {total_pages} 頁)", min_value=1, max_value=total_pages, value=1, step=1)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        st.caption(f"顯示第 {start_idx + 1} - {end_idx} 筆，共 {total_count} 筆")
    else:
        start_idx = 0
        end_idx = total_count
        st.caption(f"顯示全部 {total_count} 筆")
    
    # 欄位順序：一般股票指標在前，ETF 指標在後
    display_cols = ['stock_id', 'name', 'price', 'score', 'roe', 'pe', 'pb', 'debt_ratio', 'dividend_yield', 'dividend_years']
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[display_cols].iloc[start_idx:end_idx].copy()
    
    # 加入序號欄位
    display_df.insert(0, '序號', range(start_idx + 1, end_idx + 1))
    
    display_df = display_df.rename(columns=COLUMN_NAMES)
    
    for col in display_df.select_dtypes(include=['float64']).columns:
        display_df[col] = display_df[col].round(2)
    
    # 評分權重說明
    st.caption("📊 **評分權重** — 一般股票：權益報酬率(ROE) 40% + 本益比(PE) 30% + 淨值比(PB) 15% + 負債率 15% ｜ ETF：殖利率 80% + 配息年數 20%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # 匯出全部資料
    export_df = filtered_df[['stock_id', 'name', 'industry', 'score', 'roe', 'pe', 'pb', 'dividend_yield', 'debt_ratio'] if all(c in filtered_df.columns for c in ['stock_id', 'name']) else filtered_df.columns].copy()
    export_df.insert(0, '序號', range(1, len(export_df) + 1))
    csv_data = export_df.to_csv(index=False)
    # 加入 BOM 讓 Excel 正確顯示中文
    csv_bytes = b'\xef\xbb\xbf' + csv_data.encode('utf-8')
    st.download_button(f"📥 匯出全部 {total_count} 筆 CSV", csv_bytes,
                       "filtered_stocks.csv", "text/csv")
    
    st.divider()
    
    # ========== 個股評分明細 ==========
    st.subheader("🔍 查看個股評分明細")
    
    from src.stock_analyzer import score_roe, score_pe, score_pb, score_debt_ratio, score_dividend_yield, score_dividend_years, get_score_grade, generate_score_explanation
    
    with st.expander("展開查看個股詳細評分", expanded=False):
        stock_options = [f"{row['stock_id']} - {row['name']}" for _, row in filtered_df.iterrows()]
        if stock_options:
            selected_option = st.selectbox("選擇股票", stock_options, key="filter_stock_select")
            selected_id = selected_option.split(" - ")[0]
            stock = filtered_df[filtered_df['stock_id'] == selected_id].iloc[0]
            
            # 判斷是否為 ETF
            is_etf = str(stock.get('stock_id', '')).startswith('00')
            
            if is_etf:
                # ETF 評分明細
                c1, c2 = st.columns(2)
                
                div_yield_val = stock.get('dividend_yield', 0) or 0
                div_yield_score = score_dividend_yield(div_yield_val)
                div_yield_contrib = div_yield_score * 0.8
                
                div_years_val = stock.get('dividend_years', 0) or 0
                div_years_score = score_dividend_years(div_years_val)
                div_years_contrib = div_years_score * 0.2
                
                total_score = div_yield_contrib + div_years_contrib
                grade = get_score_grade(total_score)
                
                with c1:
                    st.metric("殖利率 (80%)", f"{div_yield_val:.2f}%")
                    st.caption(f"得分: {div_yield_score:.1f} (貢獻 {div_yield_contrib:.1f} 分)")
                
                with c2:
                    st.metric("配息年數 (20%)", f"{int(div_years_val)} 年")
                    st.caption(f"得分: {div_years_score:.1f} (貢獻 {div_years_contrib:.1f} 分)")
                
                # 評分合計
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 1rem; border-radius: 8px; margin-top: 1rem; text-align: center;">
                    <span style="font-size: 0.9rem;">評分合計</span><br>
                    <span style="font-size: 2rem; font-weight: bold;">{total_score:.2f}</span>
                    <span style="font-size: 1rem;"> / 10 分</span>
                    <span style="background: rgba(255,255,255,0.2); padding: 0.25rem 0.75rem; border-radius: 6px; margin-left: 0.5rem; font-size: 1.2rem; font-weight: bold;">{grade} 級</span>
                </div>
                """, unsafe_allow_html=True)
                
                # ETF 評分說明
                st.markdown("""
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #10b981;">
                    <h4 style="margin: 0 0 0.5rem 0; font-size: 1rem; color: #059669;">📊 ETF 評分指標說明</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.9rem; color: #4b5563;">
                        <div><strong>殖利率 (80%)</strong><br>配息收益能力</div>
                        <div><strong>配息年數 (20%)</strong><br>配息穩定度</div>
                    </div>
                    <hr style="margin: 0.75rem 0; border: none; border-top: 1px solid #e2e8f0;">
                    <div style="font-size: 0.85rem; color: #6b7280;">
                        <strong>📌 滿分 10 分標準：</strong>
                        殖利率 ≥ 6% ｜ 配息年數 ≥ 10 年
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 總評
                analysis = {
                    'score': total_score,
                    'grade': grade,
                    'breakdown': {
                        'dividend_yield_score': div_yield_score,
                        'dividend_years_score': div_years_score
                    }
                }
                explanation = generate_score_explanation(stock.to_dict(), analysis)
                st.info(f"💬 **總評**：{explanation}")
                
            else:
                # 一般個股評分明細
                c1, c2, c3, c4 = st.columns(4)
                
                roe_val = stock.get('roe', 0) or 0
                roe_score = score_roe(roe_val)
                roe_contrib = roe_score * 0.4
                
                pe_val = stock.get('pe', 0) or 0
                pe_score = score_pe(pe_val)
                pe_contrib = pe_score * 0.3
                
                pb_val = stock.get('pb', 0) or 0
                pb_score = score_pb(pb_val)
                pb_contrib = pb_score * 0.15
                
                debt_val = stock.get('debt_ratio', 0) or 0
                debt_score = score_debt_ratio(debt_val)
                debt_contrib = debt_score * 0.15
                
                total_score = roe_contrib + pe_contrib + pb_contrib + debt_contrib
                grade = get_score_grade(total_score)
                
                with c1:
                    st.metric("權益報酬率 (40%)", f"{roe_val:.2f}%")
                    st.caption(f"得分: {roe_score:.1f} (貢獻 {roe_contrib:.1f} 分)")
                    
                with c2:
                    st.metric("本益比 (30%)", f"{pe_val:.2f}")
                    st.caption(f"得分: {pe_score:.1f} (貢獻 {pe_contrib:.1f} 分)")
                    
                with c3:
                    st.metric("淨值比 (15%)", f"{pb_val:.2f}")
                    st.caption(f"得分: {pb_score:.1f} (貢獻 {pb_contrib:.1f} 分)")
                    
                with c4:
                    st.metric("負債率 (15%)", f"{debt_val:.2f}%")
                    st.caption(f"得分: {debt_score:.1f} (貢獻 {debt_contrib:.1f} 分)")
                
                # 評分合計
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 1rem; border-radius: 8px; margin-top: 1rem; text-align: center;">
                    <span style="font-size: 0.9rem;">評分合計</span><br>
                    <span style="font-size: 2rem; font-weight: bold;">{total_score:.2f}</span>
                    <span style="font-size: 1rem;"> / 10 分</span>
                    <span style="background: rgba(255,255,255,0.2); padding: 0.25rem 0.75rem; border-radius: 6px; margin-left: 0.5rem; font-size: 1.2rem; font-weight: bold;">{grade} 級</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 評分指標說明
                st.markdown("""
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #3b82f6;">
                    <h4 style="margin: 0 0 0.5rem 0; font-size: 1rem; color: #1e40af;">📊 評分指標說明</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.9rem; color: #4b5563;">
                        <div><strong>權益報酬率 (40%)</strong><br>核心獲利指標</div>
                        <div><strong>本益比 (30%)</strong><br>估值合理性</div>
                        <div><strong>淨值比 (15%)</strong><br>資產價值保護</div>
                        <div><strong>負債率 (15%)</strong><br>財務安全性</div>
                    </div>
                    <hr style="margin: 0.75rem 0; border: none; border-top: 1px solid #e2e8f0;">
                    <div style="font-size: 0.85rem; color: #6b7280;">
                        <strong>📌 滿分 10 分標準：</strong>
                        權益報酬率 ≥ 25% ｜ 本益比 10~15 倍 ｜ 淨值比 ≤ 1 倍 ｜ 負債率 ≤ 30%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 總評
                analysis = {
                    'score': total_score,
                    'grade': grade,
                    'breakdown': {
                        'roe_score': roe_score,
                        'pe_score': pe_score,
                        'pb_score': pb_score,
                        'debt_ratio_score': debt_score
                    }
                }
                explanation = generate_score_explanation(stock.to_dict(), analysis)
                st.info(f"💬 **總評**：{explanation}")
