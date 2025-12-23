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
from config import SCORING_WEIGHTS, INDICATORS


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
    
    # ROE 評分 (越高越好)
    # 0-5%: 0-2分, 5-10%: 2-4分, 10-15%: 4-6分, 15-20%: 6-8分, 20%+: 8-10分
    if 'roe' in result.columns:
        result['roe_score'] = result['roe'].apply(lambda x: score_roe(x) if pd.notna(x) else 0)
    
    # PE 評分 (適中最好)
    # PE < 10: 可能風險, PE 10-15: 良好, PE 15-20: 合理, PE > 20: 偏高
    if 'pe' in result.columns:
        result['pe_score'] = result['pe'].apply(lambda x: score_pe(x) if pd.notna(x) else 0)
    
    # PB 評分 (越低越好)
    # PB < 1: 滿分, PB 1-2: 良好, PB 2-3: 普通, PB > 3: 較差
    if 'pb' in result.columns:
        result['pb_score'] = result['pb'].apply(lambda x: score_pb(x) if pd.notna(x) else 0)
    
    # 負債率評分 (越低越好)
    # < 30%: 滿分, 30-50%: 良好, 50-70%: 普通, > 70%: 較差
    if 'debt_ratio' in result.columns:
        result['debt_score'] = result['debt_ratio'].apply(lambda x: score_debt_ratio(x) if pd.notna(x) else 0)
    
    # 計算加權總分
    result['score'] = (
        result['roe_score'] * weights.get('roe', 0.4) +
        result['pe_score'] * weights.get('pe', 0.3) +
        result['pb_score'] * weights.get('pb', 0.15) +
        result['debt_score'] * weights.get('debt_ratio', 0.15)
    )
    
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
    # 計算各項評分
    roe_score = score_roe(stock_data.get('roe', 0))
    pe_score = score_pe(stock_data.get('pe', 0))
    pb_score = score_pb(stock_data.get('pb', 0))
    debt_score = score_debt_ratio(stock_data.get('debt_ratio', 0))
    
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
    
    # 股息分析
    div_yield = stock_data.get('dividend_yield', 0)
    if div_yield and div_yield >= 5:
        strengths.append(f"高殖利率 ({div_yield:.1f}%)")
    
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
            'debt_score': round(debt_score, 2)
        }
    }
