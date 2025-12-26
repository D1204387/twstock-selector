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


# ================== Phase 2: 新增的資料取得函數 ==================

def fetch_revenue_growth(stock_id: str, token: str = None) -> Dict:
    """取得個股營收成長率（YoY）
    
    Args:
        stock_id: 股票代號
        token: API Token
        
    Returns:
        包含營收成長率的字典
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
    
    result = {'revenue_growth': None, 'latest_revenue': None}
    
    df = get_finmind_data(
        "TaiwanStockMonthRevenue",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty and len(df) >= 2:
        # 按日期排序
        df = df.sort_values('date', ascending=False)
        
        # 取得最新月份和去年同期
        latest = df.iloc[0]
        latest_revenue = latest.get('revenue', 0)
        
        # 找去年同期
        latest_date = pd.to_datetime(latest['date'])
        year_ago = latest_date - timedelta(days=365)
        
        # 找最接近去年同期的資料
        df['date'] = pd.to_datetime(df['date'])
        year_ago_df = df[df['date'] <= year_ago]
        
        if not year_ago_df.empty:
            year_ago_revenue = year_ago_df.iloc[0].get('revenue', 0)
            if year_ago_revenue and year_ago_revenue > 0:
                growth = ((latest_revenue - year_ago_revenue) / year_ago_revenue) * 100
                result['revenue_growth'] = round(growth, 2)
                result['latest_revenue'] = latest_revenue
    
    time.sleep(0.2)
    return result


def fetch_eps_growth(stock_id: str, token: str = None) -> Dict:
    """取得個股 EPS 成長率（YoY）
    
    Args:
        stock_id: 股票代號
        token: API Token
        
    Returns:
        包含 EPS 成長率的字典
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d")
    
    result = {'eps_growth': None, 'eps': None}
    
    df = get_finmind_data(
        "TaiwanStockFinancialStatements",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty:
        # 篩選 EPS 相關資料
        eps_df = df[df['type'].str.contains('基本每股盈餘|EPS', case=False, na=False)]
        
        if not eps_df.empty and len(eps_df) >= 2:
            eps_df = eps_df.sort_values('date', ascending=False)
            
            # 取得最新和去年同期
            latest_eps = float(eps_df.iloc[0].get('value', 0))
            year_ago_eps = float(eps_df.iloc[-1].get('value', 0))
            
            if year_ago_eps and year_ago_eps != 0:
                growth = ((latest_eps - year_ago_eps) / abs(year_ago_eps)) * 100
                result['eps_growth'] = round(growth, 2)
                result['eps'] = latest_eps
    
    time.sleep(0.2)
    return result


def fetch_complete_financial_data(stock_id: str, token: str = None) -> Dict:
    """取得個股完整財務資料（ROE, ROA, 毛利率等）
    
    Args:
        stock_id: 股票代號
        token: API Token
        
    Returns:
        包含完整財務指標的字典
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
    
    result = {
        'stock_id': stock_id,
        'roe': None,
        'roa': None,
        'eps': None,
        'net_profit_margin': None,
        'gross_margin': None,
        'operating_margin': None,
        'debt_ratio': None,
    }
    
    df = get_finmind_data(
        "TaiwanStockFinancialStatements",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty:
        # 取得最新一期的資料
        latest_date = df['date'].max()
        latest = df[df['date'] == latest_date]
        
        # 判斷是第幾季（用於年化計算）
        # FinMind 的財報日期格式通常是季報公布日
        quarter = None
        try:
            # 嘗試從日期推算季度
            latest_date_parsed = pd.to_datetime(latest_date)
            month = latest_date_parsed.month
            if month <= 3:
                quarter = 4  # Q4 財報通常在隔年 3 月前公布
            elif month <= 5:
                quarter = 1  # Q1 財報通常在 5 月前公布
            elif month <= 8:
                quarter = 2  # Q2 財報通常在 8 月前公布
            elif month <= 11:
                quarter = 3  # Q3 財報通常在 11 月前公布
            else:
                quarter = 3  # 12月視為 Q3
        except:
            quarter = None
        
        # 解析各項指標
        for _, row in latest.iterrows():
            item_type = str(row.get('type', '')).lower()
            value = row.get('value')
            
            try:
                val = float(value) if value is not None else None
            except:
                val = None
            
            if val is not None:
                if 'roe' in item_type or '股東權益報酬率' in item_type:
                    # ROE 年化：如果是累計值，根據季度年化
                    if quarter and quarter < 4:
                        result['roe'] = round(val / quarter * 4, 2)
                    else:
                        result['roe'] = val
                elif 'roa' in item_type or '資產報酬率' in item_type:
                    # ROA 年化
                    if quarter and quarter < 4:
                        result['roa'] = round(val / quarter * 4, 2)
                    else:
                        result['roa'] = val
                elif '基本每股盈餘' in item_type or 'eps' in item_type:
                    result['eps'] = val
                elif '淨利率' in item_type or 'net profit' in item_type:
                    result['net_profit_margin'] = val
                elif '毛利率' in item_type or 'gross' in item_type:
                    result['gross_margin'] = val
                elif '營業利益率' in item_type:
                    result['operating_margin'] = val
                elif '負債比率' in item_type or 'debt' in item_type:
                    result['debt_ratio'] = val
    
    time.sleep(0.2)
    return result


def fetch_dividend_complete(stock_id: str, token: str = None) -> Dict:
    """取得個股完整股利資料
    
    Args:
        stock_id: 股票代號
        token: API Token
        
    Returns:
        包含殖利率、配息年數的字典
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365*10)).strftime("%Y-%m-%d")
    
    result = {
        'dividend_yield': None,
        'dividend_years': 0,
        'cash_dividend': None
    }
    
    df = get_finmind_data(
        "TaiwanStockDividend",
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df.empty:
        # 計算連續配息年數
        if 'year' in df.columns:
            try:
                # 確保年份為整數
                years = sorted([int(y) for y in df['year'].unique()], reverse=True)
                consecutive = 0
                current_year = datetime.now().year - 1911  # 民國年
                
                for year in years:
                    if year >= current_year - consecutive - 1:
                        consecutive += 1
                    else:
                        break
                
                result['dividend_years'] = consecutive
            except (ValueError, TypeError):
                result['dividend_years'] = len(df['year'].unique())
        
        # 取得最近一年現金股利
        if 'CashEarningsDistribution' in df.columns:
            latest_year_df = df[df['date'] == df['date'].max()]
            if not latest_year_df.empty:
                try:
                    cash_div = latest_year_df['CashEarningsDistribution'].sum()
                    result['cash_dividend'] = float(cash_div) if cash_div else 0
                except (ValueError, TypeError):
                    result['cash_dividend'] = 0
    
    time.sleep(0.2)
    return result


def fetch_all_indicators(stock_id: str, token: str = None, price: float = None) -> Dict:
    """取得個股所有指標（整合所有資料）
    
    Args:
        stock_id: 股票代號
        token: API Token
        price: 股價（用於計算殖利率，如無則自動取得）
        
    Returns:
        包含所有財務指標的字典
    """
    # 取得各項資料
    financial = fetch_complete_financial_data(stock_id, token)
    pe_pb = fetch_stock_pe_pb(stock_id, token)
    dividend = fetch_dividend_complete(stock_id, token)
    revenue = fetch_revenue_growth(stock_id, token)
    eps_growth = fetch_eps_growth(stock_id, token)
    
    # 取得股價（如果沒有提供）
    if price is None:
        price = fetch_stock_price(stock_id, token)
    
    # 計算殖利率
    dividend_yield = None
    if price and price > 0 and dividend.get('cash_dividend'):
        dividend_yield = round((dividend['cash_dividend'] / price) * 100, 2)
    
    # 整合所有資料
    result = {
        'stock_id': stock_id,
        'roe': financial.get('roe'),
        'roa': financial.get('roa'),
        'eps': financial.get('eps') or eps_growth.get('eps'),
        'net_profit_margin': financial.get('net_profit_margin'),
        'gross_margin': financial.get('gross_margin'),
        'operating_margin': financial.get('operating_margin'),
        'debt_ratio': financial.get('debt_ratio'),
        'pe': pe_pb.get('pe'),
        'pb': pe_pb.get('pb'),
        'dividend_yield': dividend_yield or dividend.get('dividend_yield'),
        'dividend_years': dividend.get('dividend_years', 0),
        'revenue_growth': revenue.get('revenue_growth'),
        'eps_growth': eps_growth.get('eps_growth'),
        'price': price,
    }
    
    return result


def fetch_indicators_lite(stock_id: str, token: str = None) -> Dict:
    """取得個股指標（輕量版 - 只需 3 次 API 請求）
    
    優化策略：
    - 合併財務報表請求（ROE/ROA/EPS 都在同一個資料集）
    - 省略月營收（用模擬資料替代）
    - 使用 PE/PB 資料集中的價格計算殖利率
    
    Args:
        stock_id: 股票代號
        token: API Token
        
    Returns:
        包含財務指標的字典
    """
    result = {
        'stock_id': stock_id,
        'roe': None, 'roa': None, 'eps': None,
        'net_profit_margin': None, 'gross_margin': None,
        'operating_margin': None, 'debt_ratio': None,
        'pe': None, 'pb': None, 'dividend_yield': None,
        'dividend_years': 0, 'revenue_growth': None,
        'eps_growth': None, 'price': None,
    }
    
    # === 請求 1: PE/PB + 股價 (TaiwanStockPER) ===
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    df_per = get_finmind_data("TaiwanStockPER", stock_id, start_date, end_date, token)
    if not df_per.empty:
        latest = df_per.iloc[-1]
        result['pe'] = float(latest.get('PER', 0)) if latest.get('PER') else None
        result['pb'] = float(latest.get('PBR', 0)) if latest.get('PBR') else None
        result['price'] = float(latest.get('close', 0)) if latest.get('close') else None
    
    time.sleep(0.15)
    
    # === 請求 2: 股利 (TaiwanStockDividend) ===
    start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
    
    df_div = get_finmind_data("TaiwanStockDividend", stock_id, start_date, end_date, token)
    if not df_div.empty:
        # 配息年數
        if 'year' in df_div.columns:
            try:
                years = sorted([int(y) for y in df_div['year'].unique()], reverse=True)
                result['dividend_years'] = len(years)
            except:
                result['dividend_years'] = len(df_div['year'].unique())
        
        # 殖利率計算
        if 'CashEarningsDistribution' in df_div.columns:
            latest_div = df_div[df_div['date'] == df_div['date'].max()]
            if not latest_div.empty:
                try:
                    cash_div = latest_div['CashEarningsDistribution'].sum()
                    if cash_div and result['price'] and result['price'] > 0:
                        result['dividend_yield'] = round((float(cash_div) / result['price']) * 100, 2)
                except:
                    pass
    
    time.sleep(0.15)
    
    # === 請求 3: 財務報表 (TaiwanStockFinancialStatements) ===
    start_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
    
    df_fin = get_finmind_data("TaiwanStockFinancialStatements", stock_id, start_date, end_date, token)
    if not df_fin.empty:
        latest_date = df_fin['date'].max()
        latest = df_fin[df_fin['date'] == latest_date]
        
        # 季度判斷（用於 ROE/ROA 年化）
        quarter = None
        try:
            month = pd.to_datetime(latest_date).month
            if month <= 3: quarter = 4
            elif month <= 5: quarter = 1
            elif month <= 8: quarter = 2
            elif month <= 11: quarter = 3
            else: quarter = 3
        except:
            pass
        
        for _, row in latest.iterrows():
            item_type = str(row.get('type', '')).lower()
            try:
                val = float(row.get('value')) if row.get('value') is not None else None
            except:
                val = None
            
            if val is not None:
                if 'roe' in item_type or '股東權益報酬率' in item_type:
                    if quarter and quarter < 4:
                        result['roe'] = round(val / quarter * 4, 2)
                    else:
                        result['roe'] = val
                elif 'roa' in item_type or '資產報酬率' in item_type:
                    if quarter and quarter < 4:
                        result['roa'] = round(val / quarter * 4, 2)
                    else:
                        result['roa'] = val
                elif '基本每股盈餘' in item_type or 'eps' in item_type:
                    result['eps'] = val
                elif '淨利率' in item_type:
                    result['net_profit_margin'] = val
                elif '毛利率' in item_type:
                    result['gross_margin'] = val
                elif '營業利益率' in item_type:
                    result['operating_margin'] = val
                elif '負債比率' in item_type:
                    result['debt_ratio'] = val
    
    time.sleep(0.15)
    return result


def batch_fetch_indicators(stock_ids: List[str], token: str = None, 
                           progress_callback=None, batch_size: int = 100,
                           use_lite: bool = True) -> pd.DataFrame:
    """批次取得多檔股票的所有指標
    
    Args:
        stock_ids: 股票代號列表
        token: API Token
        progress_callback: 進度回調函數 (current, total, stock_id)
        batch_size: 每批處理數量
        use_lite: 使用輕量版（3次請求/檔）或完整版（6次請求/檔）
        
    Returns:
        包含所有股票財務指標的 DataFrame
    """
    all_data = []
    total = len(stock_ids)
    
    mode = "輕量版（3次請求/檔）" if use_lite else "完整版（6次請求/檔）"
    print(f"📊 開始批次取得 {total} 檔股票的財務資料（{mode}）...")
    print(f"💡 預估 API 請求數: {total * (3 if use_lite else 6)} 次")
    
    for i, stock_id in enumerate(stock_ids):
        if progress_callback:
            progress_callback(i + 1, total, stock_id)
        
        try:
            # 使用輕量版或完整版
            if use_lite:
                data = fetch_indicators_lite(stock_id, token)
            else:
                data = fetch_all_indicators(stock_id, token)
            all_data.append(data)
            
            if (i + 1) % 10 == 0:
                print(f"  進度: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
            
            # 每 batch_size 檔暫停一下，避免觸發限制
            if (i + 1) % batch_size == 0:
                print(f"  休息 3 秒避免 API 限制...")
                time.sleep(3)
                
        except Exception as e:
            print(f"  ⚠️ {stock_id}: {e}")
            all_data.append({'stock_id': stock_id})
            continue
    
    df = pd.DataFrame(all_data)
    
    # 儲存到快取
    cache_file = CACHE_DIR / f"batch_indicators_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(cache_file, index=False, encoding='utf-8-sig')
    print(f"✅ 已儲存 {len(df)} 檔股票資料到 {cache_file}")
    
    return df


# ================== 批次優化版：全市場資料下載 ==================

def fetch_all_market_data(token: str = None) -> pd.DataFrame:
    """批次取得全市場股票資料（優化版 - 只需 3 次 API 請求）
    
    策略：不指定 stock_id，一次取得全市場資料
    
    Args:
        token: FinMind API Token
        
    Returns:
        包含全市場股票財務指標的 DataFrame
    """
    print("=" * 60)
    print("📊 全市場批次下載（優化版）")
    print("=" * 60)
    print()
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 結果字典
    all_data = {}
    
    # === API 請求 1: PE/PB 資料 (TaiwanStockPER) ===
    print("📈 [1/3] 下載全市場 PE/PB 資料...")
    df_per = get_finmind_data(
        "TaiwanStockPER",
        start_date=yesterday,
        end_date=end_date,
        token=token
    )
    
    if not df_per.empty:
        # 取每檔股票最新一筆
        df_per = df_per.sort_values('date').groupby('stock_id').last().reset_index()
        
        for _, row in df_per.iterrows():
            stock_id = str(row.get('stock_id', ''))
            if stock_id:
                all_data[stock_id] = {
                    'stock_id': stock_id,
                    'pe': float(row.get('PER')) if pd.notna(row.get('PER')) else None,
                    'pb': float(row.get('PBR')) if pd.notna(row.get('PBR')) else None,
                    'price': float(row.get('close')) if pd.notna(row.get('close')) else None,
                }
        
        print(f"  ✅ 取得 {len(all_data)} 檔股票的 PE/PB 資料")
    else:
        print("  ⚠️ PE/PB 資料取得失敗")
    
    time.sleep(1)
    
    # === API 請求 2: 股利資料 (TaiwanStockDividend) ===
    print("💰 [2/3] 下載全市場股利資料...")
    start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y-%m-%d")
    
    df_div = get_finmind_data(
        "TaiwanStockDividend",
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df_div.empty:
        # 計算每檔股票的配息年數和現金股利
        dividend_count = 0
        for stock_id in df_div['stock_id'].unique():
            stock_div = df_div[df_div['stock_id'] == stock_id]
            stock_id = str(stock_id)
            
            if stock_id not in all_data:
                all_data[stock_id] = {'stock_id': stock_id}
            
            # 配息年數
            if 'year' in stock_div.columns:
                try:
                    years = len(stock_div['year'].unique())
                    all_data[stock_id]['dividend_years'] = years
                except:
                    pass
            
            # 殖利率計算
            if 'CashEarningsDistribution' in stock_div.columns:
                latest = stock_div[stock_div['date'] == stock_div['date'].max()]
                if not latest.empty:
                    try:
                        cash_div = latest['CashEarningsDistribution'].sum()
                        price = all_data[stock_id].get('price')
                        if cash_div and price and price > 0:
                            all_data[stock_id]['dividend_yield'] = round((float(cash_div) / price) * 100, 2)
                            dividend_count += 1
                    except:
                        pass
        
        print(f"  ✅ 取得 {len(df_div['stock_id'].unique())} 檔股票的股利資料")
    else:
        print("  ⚠️ 股利資料取得失敗")
    
    time.sleep(1)
    
    # === API 請求 3: 財務報表資料 (TaiwanStockFinancialStatements) - 使用最新季度 ===
    print("📑 [3/3] 下載全市場財務報表...")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    df_fin = get_finmind_data(
        "TaiwanStockFinancialStatements",
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if not df_fin.empty:
        # 取每檔股票最新一期
        latest_date = df_fin['date'].max()
        df_latest = df_fin[df_fin['date'] == latest_date]
        
        eps_count = 0
        for stock_id in df_latest['stock_id'].unique():
            stock_fin = df_latest[df_latest['stock_id'] == stock_id]
            stock_id = str(stock_id)
            
            if stock_id not in all_data:
                all_data[stock_id] = {'stock_id': stock_id}
            
            for _, row in stock_fin.iterrows():
                item_type = str(row.get('type', '')).lower()
                try:
                    val = float(row.get('value')) if row.get('value') is not None else None
                except:
                    val = None
                
                if val is not None:
                    if 'roe' in item_type or '股東權益報酬率' in item_type:
                        all_data[stock_id]['roe'] = val
                    elif 'roa' in item_type or '資產報酬率' in item_type:
                        all_data[stock_id]['roa'] = val
                    elif '基本每股盈餘' in item_type or 'eps' in item_type:
                        all_data[stock_id]['eps'] = val
                        eps_count += 1
                    elif '負債比率' in item_type:
                        all_data[stock_id]['debt_ratio'] = val
        
        print(f"  ✅ 取得 {len(df_latest['stock_id'].unique())} 檔股票的財務報表")
    else:
        print("  ⚠️ 財務報表資料取得失敗")
    
    # 整理結果
    result_df = pd.DataFrame(list(all_data.values()))
    
    # 儲存到快取
    cache_file = CACHE_DIR / f"market_data_{datetime.now().strftime('%Y%m%d')}.csv"
    result_df.to_csv(cache_file, index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 60)
    print("✅ 下載完成！")
    print(f"📊 總共取得: {len(result_df)} 檔股票")
    print(f"💾 儲存至: {cache_file}")
    print("=" * 60)
    
    # 統計各欄位
    print()
    print("📈 各欄位有效資料統計:")
    for col in ['pe', 'pb', 'eps', 'dividend_yield', 'dividend_years', 'price']:
        if col in result_df.columns:
            valid = result_df[col].notna().sum()
            print(f"  {col}: {valid}/{len(result_df)} ({valid/len(result_df)*100:.0f}%)")
    
    return result_df
