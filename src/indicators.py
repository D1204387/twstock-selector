"""
台股智選系統 - 財務指標計算模組
Taiwan Stock Selection System - Financial Indicators Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
from pathlib import Path

# 加入專案根目錄到 path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import INDICATORS


def calculate_roe(net_income: float, equity: float) -> Optional[float]:
    """計算股東權益報酬率 (ROE)"""
    if equity and equity != 0:
        return round((net_income / equity) * 100, 2)
    return None


def calculate_roa(net_income: float, total_assets: float) -> Optional[float]:
    """計算資產報酬率 (ROA)"""
    if total_assets and total_assets != 0:
        return round((net_income / total_assets) * 100, 2)
    return None


def calculate_net_profit_margin(net_income: float, revenue: float) -> Optional[float]:
    """計算淨利率"""
    if revenue and revenue != 0:
        return round((net_income / revenue) * 100, 2)
    return None


def calculate_gross_margin(revenue: float, cost: float) -> Optional[float]:
    """計算毛利率"""
    if revenue and revenue != 0:
        return round(((revenue - cost) / revenue) * 100, 2)
    return None


def calculate_operating_margin(operating_income: float, revenue: float) -> Optional[float]:
    """計算營業利潤率"""
    if revenue and revenue != 0:
        return round((operating_income / revenue) * 100, 2)
    return None


def calculate_pe(price: float, eps: float) -> Optional[float]:
    """計算本益比 (P/E Ratio)"""
    if eps and eps > 0:
        return round(price / eps, 2)
    return None


def calculate_pb(price: float, book_value_per_share: float) -> Optional[float]:
    """計算股價淨值比 (P/B Ratio)"""
    if book_value_per_share and book_value_per_share > 0:
        return round(price / book_value_per_share, 2)
    return None


def calculate_dividend_yield(dividend: float, price: float) -> Optional[float]:
    """計算股息率"""
    if price and price > 0:
        return round((dividend / price) * 100, 2)
    return None


def calculate_growth_rate(current: float, previous: float) -> Optional[float]:
    """計算成長率"""
    if previous and previous != 0:
        return round(((current - previous) / abs(previous)) * 100, 2)
    return None


def calculate_debt_ratio(total_debt: float, total_assets: float) -> Optional[float]:
    """計算負債率"""
    if total_assets and total_assets != 0:
        return round((total_debt / total_assets) * 100, 2)
    return None


def calculate_current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
    """計算流動比率"""
    if current_liabilities and current_liabilities != 0:
        return round((current_assets / current_liabilities) * 100, 2)
    return None


def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> Optional[float]:
    """計算速動比率"""
    if current_liabilities and current_liabilities != 0:
        return round(((current_assets - inventory) / current_liabilities) * 100, 2)
    return None


def get_indicator_info(indicator_key: str) -> Dict:
    """取得指標詳細資訊"""
    return INDICATORS.get(indicator_key, {})


def get_all_indicators() -> Dict:
    """取得所有指標定義"""
    return INDICATORS


def get_indicators_by_category() -> Dict[str, List[str]]:
    """按類別分組取得指標"""
    categories = {}
    for key, info in INDICATORS.items():
        category = info.get('category', '其他')
        if category not in categories:
            categories[category] = []
        categories[category].append(key)
    return categories


def filter_by_indicators(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """根據指標條件篩選股票
    
    Args:
        df: 股票資料 DataFrame
        filters: 篩選條件字典，格式如 {'roe': {'min': 15, 'max': None}}
    
    Returns:
        符合條件的股票 DataFrame
    """
    result = df.copy()
    
    for indicator, conditions in filters.items():
        if indicator not in result.columns:
            continue
        
        min_val = conditions.get('min')
        max_val = conditions.get('max')
        
        if min_val is not None:
            result = result[result[indicator] >= min_val]
        
        if max_val is not None:
            result = result[result[indicator] <= max_val]
    
    return result


def check_indicator_health(value: float, indicator_key: str) -> str:
    """檢查指標健康狀態
    
    Returns:
        'good', 'neutral', 'bad'
    """
    info = INDICATORS.get(indicator_key, {})
    ideal_min = info.get('ideal_min')
    ideal_max = info.get('ideal_max')
    
    if value is None:
        return 'neutral'
    
    # 特殊處理：負債率越低越好
    if indicator_key in ['debt_ratio']:
        if ideal_max and value <= ideal_max:
            return 'good'
        elif ideal_max and value > ideal_max:
            return 'bad'
        return 'neutral'
    
    # 一般情況
    if ideal_min and ideal_max:
        if ideal_min <= value <= ideal_max:
            return 'good'
        else:
            return 'neutral' if value > ideal_max else 'bad'
    elif ideal_min:
        return 'good' if value >= ideal_min else 'bad'
    elif ideal_max:
        return 'good' if value <= ideal_max else 'bad'
    
    return 'neutral'


def format_indicator_value(value: float, indicator_key: str) -> str:
    """格式化指標顯示值"""
    if value is None:
        return "N/A"
    
    info = INDICATORS.get(indicator_key, {})
    unit = info.get('unit', '')
    
    if unit == '%':
        return f"{value:.2f}%"
    elif unit == '倍':
        return f"{value:.2f}倍"
    elif unit == '元':
        return f"{value:.2f}元"
    elif unit == '年':
        return f"{int(value)}年"
    else:
        return f"{value:.2f}"


def get_indicator_color(status: str) -> str:
    """取得指標狀態顏色"""
    colors = {
        'good': '#28a745',    # 綠色
        'neutral': '#ffc107', # 黃色
        'bad': '#dc3545'      # 紅色
    }
    return colors.get(status, '#6c757d')


def calculate_all_indicators(financial_data: Dict) -> Dict:
    """計算所有財務指標
    
    Args:
        financial_data: 原始財務數據
    
    Returns:
        計算後的指標字典
    """
    result = {}
    
    # 獲利能力
    if 'net_income' in financial_data and 'equity' in financial_data:
        result['roe'] = calculate_roe(
            financial_data['net_income'],
            financial_data['equity']
        )
    
    if 'net_income' in financial_data and 'total_assets' in financial_data:
        result['roa'] = calculate_roa(
            financial_data['net_income'],
            financial_data['total_assets']
        )
    
    if 'net_income' in financial_data and 'revenue' in financial_data:
        result['net_profit_margin'] = calculate_net_profit_margin(
            financial_data['net_income'],
            financial_data['revenue']
        )
    
    if 'revenue' in financial_data and 'cost' in financial_data:
        result['gross_margin'] = calculate_gross_margin(
            financial_data['revenue'],
            financial_data['cost']
        )
    
    if 'operating_income' in financial_data and 'revenue' in financial_data:
        result['operating_margin'] = calculate_operating_margin(
            financial_data['operating_income'],
            financial_data['revenue']
        )
    
    # 估值指標
    if 'price' in financial_data and 'eps' in financial_data:
        result['pe'] = calculate_pe(
            financial_data['price'],
            financial_data['eps']
        )
    
    if 'price' in financial_data and 'book_value_per_share' in financial_data:
        result['pb'] = calculate_pb(
            financial_data['price'],
            financial_data['book_value_per_share']
        )
    
    if 'eps' in financial_data:
        result['eps'] = financial_data['eps']
    
    if 'dividend' in financial_data and 'price' in financial_data:
        result['dividend_yield'] = calculate_dividend_yield(
            financial_data['dividend'],
            financial_data['price']
        )
    
    # 成長性
    if 'revenue' in financial_data and 'prev_revenue' in financial_data:
        result['revenue_growth'] = calculate_growth_rate(
            financial_data['revenue'],
            financial_data['prev_revenue']
        )
    
    if 'eps' in financial_data and 'prev_eps' in financial_data:
        result['eps_growth'] = calculate_growth_rate(
            financial_data['eps'],
            financial_data['prev_eps']
        )
    
    if 'dividend_years' in financial_data:
        result['dividend_years'] = financial_data['dividend_years']
    
    # 財務安全
    if 'total_debt' in financial_data and 'total_assets' in financial_data:
        result['debt_ratio'] = calculate_debt_ratio(
            financial_data['total_debt'],
            financial_data['total_assets']
        )
    
    if 'current_assets' in financial_data and 'current_liabilities' in financial_data:
        result['current_ratio'] = calculate_current_ratio(
            financial_data['current_assets'],
            financial_data['current_liabilities']
        )
    
    if all(k in financial_data for k in ['current_assets', 'inventory', 'current_liabilities']):
        result['quick_ratio'] = calculate_quick_ratio(
            financial_data['current_assets'],
            financial_data['inventory'],
            financial_data['current_liabilities']
        )
    
    return result
