"""
台股智選系統 - 策略篩選模組
Taiwan Stock Selection System - Stock Screener Module
"""

import pandas as pd
from typing import Dict, List, Optional
import sys
from pathlib import Path

# 加入專案根目錄到 path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import STRATEGIES


def apply_strategy(df: pd.DataFrame, strategy_key: str) -> pd.DataFrame:
    """根據策略篩選股票
    
    Args:
        df: 股票資料 DataFrame
        strategy_key: 策略代碼 ('growth', 'value', 'dividend', 'quality')
    
    Returns:
        符合策略條件的股票 DataFrame
    """
    if strategy_key not in STRATEGIES:
        return df
    
    strategy = STRATEGIES[strategy_key]
    conditions = strategy.get('conditions', {})
    
    return apply_conditions(df, conditions)


def apply_conditions(df: pd.DataFrame, conditions: Dict) -> pd.DataFrame:
    """根據條件篩選股票
    
    Args:
        df: 股票資料 DataFrame
        conditions: 條件字典，格式如 {'roe': {'min': 15, 'max': None}}
    
    Returns:
        符合條件的股票 DataFrame
    """
    result = df.copy()
    
    for indicator, cond in conditions.items():
        if indicator not in result.columns:
            continue
        
        min_val = cond.get('min')
        max_val = cond.get('max')
        
        if min_val is not None:
            result = result[result[indicator] >= min_val]
        
        if max_val is not None:
            result = result[result[indicator] <= max_val]
    
    return result


def get_strategy_info(strategy_key: str) -> Dict:
    """取得策略詳細資訊"""
    return STRATEGIES.get(strategy_key, {})


def get_all_strategies() -> Dict:
    """取得所有策略定義"""
    return STRATEGIES


def screen_growth_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """篩選成長股
    
    條件：
    - ROE > 15%
    - EPS 成長率 > 15%
    - 營收成長率 > 10%
    """
    return apply_strategy(df, 'growth')


def screen_value_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """篩選價值股
    
    條件：
    - PE < 15
    - PB < 2
    - ROE > 10%
    - 股息率 > 3%
    """
    return apply_strategy(df, 'value')


def screen_dividend_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """篩選高股息股
    
    條件：
    - 股息率 > 5%
    - 配息年數 > 5 年
    - 負債率 < 60%
    """
    return apply_strategy(df, 'dividend')


def screen_quality_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """篩選優質股
    
    條件：
    - ROE > 15%
    - PE 10-20
    - 負債率 < 40%
    """
    return apply_strategy(df, 'quality')


def custom_screen(df: pd.DataFrame, 
                  filters: Dict = None,
                  industry: str = None,
                  asset_type: str = None,
                  exclude_loss: bool = False) -> pd.DataFrame:
    """自訂條件篩選
    
    Args:
        df: 股票資料 DataFrame
        filters: 指標篩選條件
        industry: 產業別
        asset_type: 資產類型 ('all', 'stock', 'etf')
        exclude_loss: 是否排除虧損公司
    
    Returns:
        符合條件的股票 DataFrame
    """
    result = df.copy()
    
    # 資產類型篩選
    if asset_type and asset_type != 'all':
        if 'asset_type' in result.columns:
            result = result[result['asset_type'] == asset_type]
    
    # 產業別篩選
    if industry and industry != '全部':
        if 'industry' in result.columns:
            result = result[result['industry'] == industry]
    
    # 排除虧損公司
    if exclude_loss:
        if 'eps' in result.columns:
            result = result[result['eps'] > 0]
    
    # 指標篩選
    if filters:
        result = apply_conditions(result, filters)
    
    return result


def get_strategy_matches_count(df: pd.DataFrame) -> Dict[str, int]:
    """取得各策略符合的股票數量"""
    counts = {}
    
    for key in STRATEGIES.keys():
        matched = apply_strategy(df, key)
        counts[key] = len(matched)
    
    return counts


def format_strategy_conditions(strategy_key: str) -> List[str]:
    """格式化策略條件為可讀字串"""
    strategy = STRATEGIES.get(strategy_key, {})
    conditions = strategy.get('conditions', {})
    
    formatted = []
    
    for indicator, cond in conditions.items():
        min_val = cond.get('min')
        max_val = cond.get('max')
        
        indicator_name = get_indicator_display_name(indicator)
        
        if min_val is not None and max_val is not None:
            formatted.append(f"{indicator_name}: {min_val} ~ {max_val}")
        elif min_val is not None:
            formatted.append(f"{indicator_name} > {min_val}")
        elif max_val is not None:
            formatted.append(f"{indicator_name} < {max_val}")
    
    return formatted


def get_indicator_display_name(indicator_key: str) -> str:
    """取得指標顯示名稱 (中文優先，英文縮寫為輔)"""
    names = {
        'roe': '權益報酬率(ROE)',
        'roa': '資產報酬率(ROA)',
        'net_profit_margin': '淨利率',
        'gross_margin': '毛利率',
        'operating_margin': '營業利潤率',
        'pe': '本益比(PE)',
        'pb': '淨值比(PB)',
        'eps': '每股盈餘(EPS)',
        'dividend_yield': '殖利率',
        'dividend_years': '配息年數',
        'debt_ratio': '負債率'
    }
    return names.get(indicator_key, indicator_key)


def analyze_strategy_performance(df: pd.DataFrame) -> Dict:
    """分析各策略的表現
    
    Returns:
        各策略的統計資訊
    """
    from .stock_analyzer import calculate_score
    
    performance = {}
    
    for key, strategy in STRATEGIES.items():
        matched = apply_strategy(df, key)
        
        if matched.empty:
            performance[key] = {
                'count': 0,
                'avg_score': 0,
                'best_stocks': []
            }
            continue
        
        # 計算評分
        scored = calculate_score(matched)
        
        performance[key] = {
            'count': len(matched),
            'avg_score': round(scored['score'].mean(), 2) if 'score' in scored.columns else 0,
            'best_stocks': scored.nlargest(5, 'score')[['stock_id', 'name', 'score']].to_dict('records') if 'score' in scored.columns else []
        }
    
    return performance
