"""
台股智選系統 - 公開資訊觀測站（MOPS）爬蟲模組
Taiwan Stock Selection System - MOPS Scraper Module

從公開資訊觀測站取得財務報表資料
資料來源：https://mops.twse.com.tw/
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import time
from pathlib import Path
import warnings

# 忽略 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# MOPS 端點
MOPS_BASE_URL = "https://mops.twse.com.tw/mops/web"

# 快取目錄
CACHE_DIR = Path(__file__).parent.parent / "data" / "mops_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 請求標頭（模擬瀏覽器）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
}


def fetch_income_statement(year: int, season: int, market_type: str = "sii") -> pd.DataFrame:
    """取得綜合損益表彙總
    
    Args:
        year: 民國年（例如：112）
        season: 季度（1, 2, 3, 4）
        market_type: 市場類型 ("sii" 上市, "otc" 上櫃)
    
    Returns:
        包含 EPS、營收等資料的 DataFrame
    """
    url = f"{MOPS_BASE_URL}/ajax_t163sb04"
    
    data = {
        'encodeURIComponent': '1',
        'step': '1',
        'firstin': '1',
        'off': '1',
        'isQuery': 'Y',
        'TYPEK': market_type,
        'year': str(year),
        'season': str(season).zfill(2),
    }
    
    try:
        response = requests.post(url, data=data, headers=HEADERS, timeout=30, verify=False)
        response.encoding = 'utf-8'
        
        # 解析 HTML 表格
        tables = pd.read_html(response.text, encoding='utf-8')
        
        if tables:
            # 通常第一個表格是主要資料
            df = tables[0]
            print(f"✅ 取得 {market_type} {year}Q{season} 損益表: {len(df)} 筆")
            return df
        else:
            print(f"⚠️ 無法解析表格: {market_type} {year}Q{season}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ 取得損益表失敗: {e}")
        return pd.DataFrame()


def fetch_balance_sheet(year: int, season: int, market_type: str = "sii") -> pd.DataFrame:
    """取得資產負債表彙總
    
    Args:
        year: 民國年
        season: 季度
        market_type: 市場類型
    
    Returns:
        包含資產、負債等資料的 DataFrame
    """
    url = f"{MOPS_BASE_URL}/ajax_t163sb05"
    
    data = {
        'encodeURIComponent': '1',
        'step': '1',
        'firstin': '1',
        'off': '1',
        'isQuery': 'Y',
        'TYPEK': market_type,
        'year': str(year),
        'season': str(season).zfill(2),
    }
    
    try:
        response = requests.post(url, data=data, headers=HEADERS, timeout=30, verify=False)
        response.encoding = 'utf-8'
        
        tables = pd.read_html(response.text, encoding='utf-8')
        
        if tables:
            df = tables[0]
            print(f"✅ 取得 {market_type} {year}Q{season} 資產負債表: {len(df)} 筆")
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ 取得資產負債表失敗: {e}")
        return pd.DataFrame()


def fetch_profit_analysis(year: int, season: int, market_type: str = "sii") -> pd.DataFrame:
    """取得營益分析表（包含 ROE、ROA 等）
    
    Args:
        year: 民國年
        season: 季度
        market_type: 市場類型
    
    Returns:
        包含 ROE、ROA、毛利率等資料的 DataFrame
    """
    url = f"{MOPS_BASE_URL}/ajax_t163sb06"
    
    data = {
        'encodeURIComponent': '1',
        'step': '1',
        'firstin': '1',
        'off': '1',
        'isQuery': 'Y',
        'TYPEK': market_type,
        'year': str(year),
        'season': str(season).zfill(2),
    }
    
    try:
        response = requests.post(url, data=data, headers=HEADERS, timeout=30, verify=False)
        response.encoding = 'utf-8'
        
        tables = pd.read_html(response.text, encoding='utf-8')
        
        if tables:
            df = tables[0]
            print(f"✅ 取得 {market_type} {year}Q{season} 營益分析表: {len(df)} 筆")
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ 取得營益分析表失敗: {e}")
        return pd.DataFrame()


def fetch_dividend_info(year: int, market_type: str = "sii") -> pd.DataFrame:
    """取得股利分派情形
    
    Args:
        year: 民國年
        market_type: 市場類型
    
    Returns:
        包含現金股利、股票股利等資料的 DataFrame
    """
    url = f"{MOPS_BASE_URL}/ajax_t05st09"
    
    data = {
        'encodeURIComponent': '1',
        'step': '1',
        'firstin': '1',
        'off': '1',
        'TYPEK': market_type,
        'year': str(year),
    }
    
    try:
        response = requests.post(url, data=data, headers=HEADERS, timeout=30, verify=False)
        response.encoding = 'utf-8'
        
        tables = pd.read_html(response.text, encoding='utf-8')
        
        if tables:
            df = tables[0]
            print(f"✅ 取得 {market_type} {year} 股利資料: {len(df)} 筆")
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ 取得股利資料失敗: {e}")
        return pd.DataFrame()


def get_current_season() -> tuple:
    """取得當前的民國年和季度"""
    now = datetime.now()
    tw_year = now.year - 1911
    month = now.month
    
    # 季報公布時間：Q1(5月), Q2(8月), Q3(11月), Q4(隔年3月)
    # 所以我們取前一季的資料
    if month >= 11:
        return tw_year, 3  # Q3
    elif month >= 8:
        return tw_year, 2  # Q2
    elif month >= 5:
        return tw_year, 1  # Q1
    else:
        return tw_year - 1, 4  # 去年 Q4


def fetch_all_financial_data(progress_callback=None) -> pd.DataFrame:
    """取得所有上市櫃公司的財務資料
    
    Returns:
        合併後的財務資料 DataFrame
    """
    year, season = get_current_season()
    print(f"📊 正在取得 {year}年 Q{season} 財務資料...")
    
    all_data = []
    
    # 取得上市公司資料
    for market, market_name in [("sii", "上市"), ("otc", "上櫃")]:
        if progress_callback:
            progress_callback(f"取得{market_name}公司營益分析表...")
        
        # 營益分析表（包含 ROE、ROA 等）
        profit_df = fetch_profit_analysis(year, season, market)
        time.sleep(1)  # 避免請求過快
        
        if not profit_df.empty:
            profit_df['market'] = market
            all_data.append(profit_df)
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        
        # 儲存到快取
        cache_file = CACHE_DIR / f"financial_{year}Q{season}.csv"
        combined.to_csv(cache_file, index=False, encoding='utf-8-sig')
        print(f"💾 已儲存至: {cache_file}")
        
        return combined
    
    return pd.DataFrame()


def load_cached_financial_data() -> Optional[pd.DataFrame]:
    """載入快取的財務資料"""
    year, season = get_current_season()
    cache_file = CACHE_DIR / f"financial_{year}Q{season}.csv"
    
    if cache_file.exists():
        print(f"📂 載入快取資料: {cache_file}")
        return pd.read_csv(cache_file, encoding='utf-8-sig')
    
    return None


# 測試函數
if __name__ == "__main__":
    print("🔍 測試 MOPS 爬蟲...")
    
    # 測試取得營益分析表
    year, season = get_current_season()
    print(f"當前財報期間: {year}年 Q{season}")
    
    df = fetch_profit_analysis(year, season, "sii")
    if not df.empty:
        print(f"\n取得 {len(df)} 筆資料")
        print(df.head())
    else:
        print("無法取得資料")
