"""
台股智選系統 - FinMind API 模組
Taiwan Stock Selection System - FinMind API Module

使用 FinMind API 取得真實財務資料
免費額度：約 300-600 次/日
策略：只取得精選 150 檔核心股票
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time
import json
from pathlib import Path

# FinMind API URL
FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"

# 精選股票清單（台灣 50 + 熱門股）
CORE_STOCKS = [
    # 台灣 50 成分股
    "2330", "2317", "2454", "2308", "2881", "2882", "2303", "3711", "2891", "2412",
    "2886", "1301", "1303", "2002", "3008", "2880", "1326", "2382", "2357", "2884",
    "3034", "2890", "5871", "2912", "2892", "1216", "2327", "3231", "2379", "2395",
    "5880", "2408", "4938", "1101", "2801", "2883", "3045", "6505", "9910", "2887",
    "2353", "2207", "4904", "9904", "2301", "2885", "3037", "2609", "5876", "6446",
    # 中型 100 部分代表股
    "2603", "2618", "3017", "2615", "1402", "2105", "2474", "1102", "3044", "2377",
    "2324", "1590", "2344", "6415", "2542", "4958", "1504", "2498", "2637", "3443",
    "2227", "8046", "2409", "3533", "2823", "9945", "2049", "6278", "1477", "2352",
    "2401", "8454", "2449", "3702", "2383", "1605", "3406", "2345", "6239", "4966",
    "2356", "6531", "2376", "8464", "5269", "3023", "1476", "3653", "6669", "2404",
    # 熱門 ETF
    "0050", "0056", "00878", "00713", "00692", "00881", "00900", "0051", "006208", "00919",
    # 補充熱門股
    "2312", "2388", "3481", "2337", "6488", "3035", "6409", "2347", "3529", "6452",
]

# 資料快取目錄
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_finmind_data(dataset: str, stock_id: str = None, start_date: str = None, 
                     end_date: str = None, token: str = None) -> pd.DataFrame:
    """從 FinMind API 取得資料
    
    Args:
        dataset: 資料集名稱
        stock_id: 股票代號
        start_date: 開始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        token: API Token (可選，有 token 可增加額度)
    """
    params = {"dataset": dataset}
    
    if stock_id:
        params["data_id"] = stock_id
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if token:
        params["token"] = token
    
    try:
        response = requests.get(FINMIND_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == 200 and data.get("data"):
            return pd.DataFrame(data["data"])
        else:
            print(f"⚠️ FinMind 回應: {data.get('msg', 'No data')}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ FinMind API 錯誤: {e}")
        return pd.DataFrame()


def fetch_stock_financial_statement(stock_id: str, token: str = None) -> Dict:
    """取得個股財務報表資料
    
    Returns:
        包含 ROE, ROA, 淨利率等指標的字典
    """
    # 取得最近 4 季的財務資料
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
    
    result = {
        'stock_id': stock_id,
        'roe': None,
        'roa': None,
        'net_profit_margin': None,
        'gross_margin': None,
        'operating_margin': None,
        'eps': None,
        'debt_ratio': None,
        'current_ratio': None,
        'revenue_growth': None,
    }
    
    # 1. 取得財務比率
    df = get_finmind_data(
        "TaiwanStockFinancialStatements",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty:
        # 取得最新一期的資料
        latest = df[df['date'] == df['date'].max()]
        
        # 解析重要指標
        for _, row in latest.iterrows():
            item_type = row.get('type', '')
            value = row.get('value', 0)
            
            if 'ROE' in item_type or '股東權益報酬率' in item_type:
                result['roe'] = float(value) if value else None
            elif 'ROA' in item_type or '資產報酬率' in item_type:
                result['roa'] = float(value) if value else None
            elif '淨利率' in item_type or 'NetProfitMargin' in item_type:
                result['net_profit_margin'] = float(value) if value else None
            elif '毛利率' in item_type or 'GrossMargin' in item_type:
                result['gross_margin'] = float(value) if value else None
            elif '營業利益率' in item_type:
                result['operating_margin'] = float(value) if value else None
    
    # 避免請求過快
    time.sleep(0.2)
    
    return result


def fetch_stock_pe_pb(stock_id: str, token: str = None) -> Dict:
    """取得個股本益比、股價淨值比"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    result = {'pe': None, 'pb': None}
    
    df = get_finmind_data(
        "TaiwanStockPER",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty:
        latest = df.iloc[-1]
        result['pe'] = float(latest.get('PER', 0)) if latest.get('PER') else None
        result['pb'] = float(latest.get('PBR', 0)) if latest.get('PBR') else None
    
    time.sleep(0.2)
    return result


def fetch_stock_dividend(stock_id: str, token: str = None) -> Dict:
    """取得個股股利資料"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
    
    result = {'dividend_yield': None, 'dividend_years': 0}
    
    df = get_finmind_data(
        "TaiwanStockDividend",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty:
        # 計算連續配息年數
        years = df['year'].nunique() if 'year' in df.columns else 0
        result['dividend_years'] = years
        
        # 計算最近一年殖利率（需要股價資料）
        latest_dividend = df[df['date'] == df['date'].max()]
        if not latest_dividend.empty:
            cash_div = latest_dividend['CashEarningsDistribution'].sum() if 'CashEarningsDistribution' in df.columns else 0
            result['cash_dividend'] = cash_div
    
    time.sleep(0.2)
    return result


def fetch_stock_price(stock_id: str, token: str = None) -> Optional[float]:
    """取得個股最新股價"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    df = get_finmind_data(
        "TaiwanStockPrice",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty:
        return float(df.iloc[-1].get('close', 0))
    
    return None


def fetch_all_core_stocks_data(token: str = None, progress_callback=None) -> pd.DataFrame:
    """取得所有精選股票的財務資料
    
    Args:
        token: FinMind API Token
        progress_callback: 進度回調函數 (current, total, stock_id)
    
    Returns:
        包含所有財務指標的 DataFrame
    """
    # 檢查快取
    cache_file = CACHE_DIR / "core_stocks_data.json"
    
    if cache_file.exists():
        cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        # 快取有效期 24 小時
        if datetime.now() - cache_time < timedelta(hours=24):
            print("📂 使用快取資料")
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    print(f"📊 正在從 FinMind 取得 {len(CORE_STOCKS)} 檔精選股票資料...")
    
    all_data = []
    total = len(CORE_STOCKS)
    
    for i, stock_id in enumerate(CORE_STOCKS):
        if progress_callback:
            progress_callback(i + 1, total, stock_id)
        
        try:
            # 取得財務報表
            financial = fetch_stock_financial_statement(stock_id, token)
            
            # 取得 PE/PB
            pe_pb = fetch_stock_pe_pb(stock_id, token)
            financial.update(pe_pb)
            
            # 取得股利
            dividend = fetch_stock_dividend(stock_id, token)
            financial.update(dividend)
            
            # 取得股價
            price = fetch_stock_price(stock_id, token)
            financial['price'] = price
            
            # 計算殖利率
            if price and financial.get('cash_dividend'):
                financial['dividend_yield'] = (financial['cash_dividend'] / price) * 100
            
            all_data.append(financial)
            
            print(f"  [{i+1}/{total}] {stock_id} ✓")
            
        except Exception as e:
            print(f"  [{i+1}/{total}] {stock_id} ❌ {e}")
            continue
    
    df = pd.DataFrame(all_data)
    
    # 儲存快取
    if not df.empty:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(df.to_dict('records'), f, ensure_ascii=False)
        print(f"✅ 已儲存 {len(df)} 檔股票資料到快取")
    
    return df


def get_quick_financial_data(token: str = None, max_stocks: int = 50) -> pd.DataFrame:
    """快速取得財務資料（精選股票 PE/PB）
    
    Args:
        token: FinMind API Token
        max_stocks: 最大取得股票數（控制 API 使用量）
    
    Returns:
        包含 PE/PB 的 DataFrame
    """
    # 快取檔案
    cache_file = CACHE_DIR / "pe_pb_core.json"
    
    if cache_file.exists():
        cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - cache_time < timedelta(hours=24):
            print("📂 使用 PE/PB 快取")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return pd.DataFrame(json.load(f))
    
    print(f"📊 取得精選股票 PE/PB 資料 (上限 {max_stocks} 檔)...")
    
    # 只取得部分精選股票，避免超出 API 限制
    stocks_to_fetch = CORE_STOCKS[:max_stocks]
    all_data = []
    
    for i, stock_id in enumerate(stocks_to_fetch):
        try:
            pe_pb = fetch_stock_pe_pb(stock_id, token)
            if pe_pb['pe'] is not None or pe_pb['pb'] is not None:
                pe_pb['stock_id'] = stock_id
                all_data.append(pe_pb)
            
            if (i + 1) % 10 == 0:
                print(f"  進度: {i+1}/{len(stocks_to_fetch)}")
                
        except Exception as e:
            print(f"  ⚠️ {stock_id}: {e}")
            continue
    
    df = pd.DataFrame(all_data)
    
    # 儲存快取
    if not df.empty:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(df.to_dict('records'), f, ensure_ascii=False)
        print(f"✅ 已取得 {len(df)} 檔股票真實 PE/PB 資料")
    
    return df


# 匯出精選股票清單
def get_core_stocks_list() -> List[str]:
    """取得精選股票清單"""
    return CORE_STOCKS.copy()
