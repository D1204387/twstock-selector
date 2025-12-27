"""
台股智選系統 - 綜合評分模組
Taiwan Stock Selection System - Stock Analyzer Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
from pathlib import Path

# 加入專案根目錄到 path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SCORING_WEIGHTS, ETF_SCORING_WEIGHTS, INDICATORS


def calculate_score(df: pd.DataFrame, weights: Dict = None) -> pd.DataFrame:
    """計算股票綜合評分
    
    評分邏輯：
    - ROE: 越高越好，滿分 10 分對應 ROE >= 25%
    - PE: 適中最好，10-20 為理想區間
    - PB: 越低越好，PB <= 1 為滿分
    - 負債率: 越低越好，負債率 <= 30% 為滿分
    
    Args:
        df: 包含財務指標的 DataFrame
        weights: 自訂權重，預設使用 config 中的設定
    
    Returns:
        加入 score 欄位的 DataFrame
    """
    if weights is None:
        weights = SCORING_WEIGHTS
    
    result = df.copy()
    
    # 初始化各項分數
    result['roe_score'] = 0.0
    result['pe_score'] = 0.0
    result['pb_score'] = 0.0
    result['debt_score'] = 0.0
    result['dividend_score'] = 0.0
    result['dividend_years_score'] = 0.0  # 新增配息年數評分
    
    # 預計算各項分數 function (vectorized apply)
    if 'roe' in result.columns:
        result['roe_score'] = result['roe'].apply(lambda x: score_roe(x))
    if 'pe' in result.columns:
        result['pe_score'] = result['pe'].apply(lambda x: score_pe(x))
    if 'pb' in result.columns:
        result['pb_score'] = result['pb'].apply(lambda x: score_pb(x))
    if 'debt_ratio' in result.columns:
        result['debt_score'] = result['debt_ratio'].apply(lambda x: score_debt_ratio(x))
    if 'dividend_yield' in result.columns:
        result['dividend_score'] = result['dividend_yield'].apply(lambda x: score_dividend_yield(x))
    if 'dividend_years' in result.columns:
        result['dividend_years_score'] = result['dividend_years'].apply(lambda x: score_dividend_years(x))
        
    def calculate_single_score(row):
        stock_id = str(row.get('stock_id', ''))
        is_etf = stock_id.startswith('00')
        
        if is_etf:
            # ETF 動態評分邏輯
            pb_value = row.get('pb', None)
            has_valid_pb = pb_value is not None and not pd.isna(pb_value) and pb_value > 0
            
            if has_valid_pb:
                # PB 有值：殖利率 70% + PB 30%
                score = (
                    row['dividend_score'] * 0.7 +
                    row['pb_score'] * 0.3
                )
            else:
                # PB 無值：殖利率 80% + 配息年數 20%
                score = (
                    row['dividend_score'] * 0.8 +
                    row['dividend_years_score'] * 0.2
                )
        else:
            # 一般股票評分邏輯
            w = weights
            score = (
                row['roe_score'] * w.get('roe', 0.4) +
                row['pe_score'] * w.get('pe', 0.3) +
                row['pb_score'] * w.get('pb', 0.15) +
                row['debt_score'] * w.get('debt_ratio', 0.15)
            )
        return score

    result['score'] = result.apply(calculate_single_score, axis=1)
    
    # 四捨五入
    result['score'] = result['score'].round(2)
    
    return result


def score_roe(roe: float) -> float:
    """ROE 評分函數"""
    if roe is None or pd.isna(roe):
        return 0
    
    if roe <= 0:
        return 0
    elif roe < 5:
        return roe / 5 * 2
    elif roe < 10:
        return 2 + (roe - 5) / 5 * 2
    elif roe < 15:
        return 4 + (roe - 10) / 5 * 2
    elif roe < 20:
        return 6 + (roe - 15) / 5 * 2
    elif roe < 25:
        return 8 + (roe - 20) / 5 * 2
    else:
        return 10


def score_pe(pe: float) -> float:
    """PE 評分函數"""
    if pe is None or pd.isna(pe) or pe <= 0:
        return 0
    
    if pe < 5:
        return 5  # 太低可能有問題
    elif pe < 10:
        return 7 + (pe - 5) / 5 * 3  # 7-10分
    elif pe < 15:
        return 10  # 最佳區間
    elif pe < 20:
        return 10 - (pe - 15) / 5 * 2  # 8-10分
    elif pe < 30:
        return 8 - (pe - 20) / 10 * 4  # 4-8分
    else:
        return max(0, 4 - (pe - 30) / 10 * 4)  # 逐漸降低


def score_pb(pb: float) -> float:
    """PB 評分函數"""
    if pb is None or pd.isna(pb) or pb <= 0:
        return 0
    
    if pb < 0.5:
        return 8  # 太低可能有問題
    elif pb < 1:
        return 10  # 最佳
    elif pb < 1.5:
        return 9
    elif pb < 2:
        return 8
    elif pb < 3:
        return 6
    elif pb < 5:
        return 4
    else:
        return max(0, 4 - (pb - 5) / 5 * 4)


def score_debt_ratio(debt_ratio: float) -> float:
    """負債率評分函數"""
    if debt_ratio is None or pd.isna(debt_ratio):
        return 0
    
    if debt_ratio < 0:
        return 10
    elif debt_ratio < 30:
        return 10
    elif debt_ratio < 40:
        return 9
    elif debt_ratio < 50:
        return 7
    elif debt_ratio < 60:
        return 5
    elif debt_ratio < 70:
        return 3
    else:
        return max(0, 3 - (debt_ratio - 70) / 30 * 3)


def score_dividend_yield(dy: float) -> float:
    """殖利率評分函數"""
    if dy is None or pd.isna(dy):
        return 0
    
    if dy < 0:
        return 0
    elif dy < 2:
        return 1
    elif dy < 3:
        return 3
    elif dy < 4:
        return 5
    elif dy < 5:
        return 7
    elif dy < 7:
        return 9
    else:
        return 10


def score_dividend_years(years: int) -> float:
    """配息年數評分函數（連續配息穩定度）"""
    if years is None or pd.isna(years):
        return 0
    
    years = int(years)
    if years <= 0:
        return 0
    elif years < 2:
        return 2
    elif years < 3:
        return 4
    elif years < 5:
        return 6
    elif years < 7:
        return 8
    else:
        return 10  # 7年以上滿分


def get_top_stocks(df: pd.DataFrame, n: int = 20, weights: Dict = None) -> pd.DataFrame:
    """取得評分最高的前 N 檔股票
    
    Args:
        df: 股票資料 DataFrame
        n: 前幾名
        weights: 自訂權重
    
    Returns:
        排序後的 DataFrame
    """
    scored_df = calculate_score(df, weights)
    
    # 排除評分為 0 的股票
    scored_df = scored_df[scored_df['score'] > 0]
    
    # 依評分排序
    scored_df = scored_df.sort_values('score', ascending=False)
    
    return scored_df.head(n)


def get_score_breakdown(stock_data: pd.Series, weights: Dict = None) -> Dict:
    """取得單一股票的評分明細
    
    Args:
        stock_data: 股票資料 Series
        weights: 自訂權重
    
    Returns:
        評分明細字典
    """
    if weights is None:
        weights = SCORING_WEIGHTS
    
    stock_id = str(stock_data.get('stock_id', ''))
    is_etf = stock_id.startswith('00')
    
    if is_etf:
        # ETF 評分明細
        etf_weights = ETF_SCORING_WEIGHTS
        
        # 計算各項分數
        div_score = score_dividend_yield(stock_data.get('dividend_yield', 0))
        pb_score = score_pb(stock_data.get('pb', 0))
        
        breakdown = {
            'dividend_yield': {
                'value': stock_data.get('dividend_yield'),
                'score': div_score,
                'weight': etf_weights.get('dividend_yield', 0.7),
                'weighted_score': div_score * etf_weights.get('dividend_yield', 0.7)
            },
            'pb': {
                'value': stock_data.get('pb'),
                'score': pb_score,
                'weight': etf_weights.get('pb', 0.3),
                'weighted_score': pb_score * etf_weights.get('pb', 0.3)
            }
        }
    else:
        # 一般個股評分明細
        breakdown = {
            'roe': {
                'value': stock_data.get('roe'),
                'score': score_roe(stock_data.get('roe', 0)),
                'weight': weights.get('roe', 0.4),
                'weighted_score': score_roe(stock_data.get('roe', 0)) * weights.get('roe', 0.4)
            },
            'pe': {
                'value': stock_data.get('pe'),
                'score': score_pe(stock_data.get('pe', 0)),
                'weight': weights.get('pe', 0.3),
                'weighted_score': score_pe(stock_data.get('pe', 0)) * weights.get('pe', 0.3)
            },
            'pb': {
                'value': stock_data.get('pb'),
                'score': score_pb(stock_data.get('pb', 0)),
                'weight': weights.get('pb', 0.15),
                'weighted_score': score_pb(stock_data.get('pb', 0)) * weights.get('pb', 0.15)
            },
            'debt_ratio': {
                'value': stock_data.get('debt_ratio'),
                'score': score_debt_ratio(stock_data.get('debt_ratio', 0)),
                'weight': weights.get('debt_ratio', 0.15),
                'weighted_score': score_debt_ratio(stock_data.get('debt_ratio', 0)) * weights.get('debt_ratio', 0.15)
            }
        }
    
    breakdown['total_score'] = sum(item['weighted_score'] for item in breakdown.values())
    
    return breakdown


def get_score_grade(score: float) -> str:
    """取得評分等級"""
    if score >= 9:
        return "A+"
    elif score >= 8:
        return "A"
    elif score >= 7:
        return "B+"
    elif score >= 6:
        return "B"
    elif score >= 5:
        return "C+"
    elif score >= 4:
        return "C"
    elif score >= 3:
        return "D"
    else:
        return "F"


def get_grade_color(grade: str) -> str:
    """取得等級顏色"""
    colors = {
        'A+': '#1a5f2a',  # 深綠
        'A': '#28a745',   # 綠
        'B+': '#5cb85c',  # 淺綠
        'B': '#8bc34a',   # 黃綠
        'C+': '#ffc107',  # 黃
        'C': '#ff9800',   # 橙
        'D': '#f44336',   # 紅
        'F': '#9e9e9e'    # 灰
    }
    return colors.get(grade, '#6c757d')


def analyze_stock(stock_data: Dict) -> Dict:
    """全面分析單一股票
    
    Args:
        stock_data: 股票資料字典
    
    Returns:
        分析結果字典
    """
    # 判斷是否為 ETF
    stock_id = str(stock_data.get('stock_id', ''))
    is_etf = stock_id.startswith('00')
    
    # 計算各項評分
    roe_score = score_roe(stock_data.get('roe', 0))
    pe_score = score_pe(stock_data.get('pe', 0))
    pb_score = score_pb(stock_data.get('pb', 0))
    debt_score = score_debt_ratio(stock_data.get('debt_ratio', 0))
    dividend_score = score_dividend_yield(stock_data.get('dividend_yield', 0))
    
    if is_etf:
        etf_weights = ETF_SCORING_WEIGHTS
        total_score = (
            dividend_score * etf_weights.get('dividend_yield', 0.7) +
            pb_score * etf_weights.get('pb', 0.3)
        )
    else:
        weights = SCORING_WEIGHTS
        total_score = (
            roe_score * weights['roe'] +
            pe_score * weights['pe'] +
            pb_score * weights['pb'] +
            debt_score * weights['debt_ratio']
        )
    
    grade = get_score_grade(total_score)
    
    # 判斷優缺點
    strengths = []
    weaknesses = []
    
    # 股息分析 (ETF 優先檢查)
    div_yield = stock_data.get('dividend_yield', 0)
    if div_yield and div_yield >= 5:
        strengths.append(f"高殖利率 ({div_yield:.1f}%)")
    elif div_yield and div_yield < 3 and is_etf:
        weaknesses.append(f"殖利率偏低 ({div_yield:.1f}%)")

    # PB 分析
    pb = stock_data.get('pb', 0)
    if pb and pb < 1:
        strengths.append(f"股價低於淨值 (PB {pb:.2f})")
    elif pb and pb > 2 and is_etf:
         # ETF PB > 2 算高溢價風險
        weaknesses.append(f"股價淨值比偏高 ({pb:.2f})")

    if not is_etf:
        # 一般個股才看 ROE / 負債比 / PE
        
        # ROE 分析
        roe = stock_data.get('roe', 0)
        if roe and roe >= 15:
            strengths.append(f"高股東權益報酬率 ({roe:.1f}%)")
        elif roe and roe < 10:
            weaknesses.append(f"股東權益報酬率偏低 ({roe:.1f}%)")
        
        # PE 分析
        pe = stock_data.get('pe', 0)
        if pe and 10 <= pe <= 15:
            strengths.append(f"本益比合理 ({pe:.1f})")
        elif pe and pe > 30:
            weaknesses.append(f"本益比偏高 ({pe:.1f})")
        
        # 負債率分析
        debt = stock_data.get('debt_ratio', 0)
        if debt and debt < 40:
            strengths.append(f"財務結構穩健 (負債率 {debt:.1f}%)")
        elif debt and debt > 60:
            weaknesses.append(f"負債比例偏高 ({debt:.1f}%)")
    
    return {
        'score': round(total_score, 2),
        'grade': grade,
        'grade_color': get_grade_color(grade),
        'strengths': strengths,
        'weaknesses': weaknesses,
        'breakdown': {
            'roe_score': round(roe_score, 2),
            'pe_score': round(pe_score, 2),
            'pb_score': round(pb_score, 2),
            'debt_score': round(debt_score, 2),
            'dividend_score': round(dividend_score, 2)
        }
    }
