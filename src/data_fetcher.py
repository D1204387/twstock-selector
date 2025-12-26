"""
台股智選系統 - 資料取得模組
Taiwan Stock Selection System - Data Fetcher Module

資料來源：
1. twstock - 台股即時資料
2. 公開資訊觀測站 MOPS - 財務報表
3. 證交所 TWSE - 股票列表
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import json

try:
    import twstock
except ImportError:
    twstock = None

from .database import (
    get_connection, save_stocks, get_all_stocks,
    save_financial_data, get_cache, set_cache
)


# API URLs
TWSE_STOCK_LIST_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TPEX_STOCK_LIST_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"
TWSE_ETF_URL = "https://www.twse.com.tw/rwd/zh/ETF/etfDiv"


def fetch_twse_stocks() -> pd.DataFrame:
    """從證交所取得上市股票列表"""
    try:
        response = requests.get(TWSE_STOCK_LIST_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.rename(columns={
                'Code': 'stock_id',
                'Name': 'name'
            })
            df['market'] = '上市'
            df['asset_type'] = df['stock_id'].apply(
                lambda x: 'etf' if x.startswith('00') else 'stock'
            )
            df['industry'] = '其他'  # 需要另外取得產業分類
            
            return df[['stock_id', 'name', 'industry', 'market', 'asset_type']]
    except Exception as e:
        print(f"❌ 取得上市股票失敗: {e}")
    
    return pd.DataFrame()


def fetch_tpex_stocks() -> pd.DataFrame:
    """從櫃買中心取得上櫃股票列表"""
    try:
        response = requests.get(TPEX_STOCK_LIST_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.rename(columns={
                'SecuritiesCompanyCode': 'stock_id',
                'CompanyName': 'name'
            })
            df['market'] = '上櫃'
            df['asset_type'] = df['stock_id'].apply(
                lambda x: 'etf' if x.startswith('00') else 'stock'
            )
            df['industry'] = '其他'
            
            return df[['stock_id', 'name', 'industry', 'market', 'asset_type']]
    except Exception as e:
        print(f"❌ 取得上櫃股票失敗: {e}")
    
    return pd.DataFrame()


def fetch_stock_industry() -> Dict[str, str]:
    """取得股票產業分類（使用 twstock）"""
    industry_map = {}
    
    # 優先使用 twstock 的資料
    if twstock is not None:
        try:
            for code, info in twstock.codes.items():
                if info.group:  # group 欄位包含產業分類
                    industry_map[code] = info.group
        except Exception as e:
            print(f"⚠️ twstock 產業分類取得失敗: {e}")
    
    # 如果 twstock 沒有資料，嘗試從 API 取得
    if not industry_map:
        url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for item in data:
                stock_id = item.get('公司代號', '')
                industry = item.get('產業類別', '其他')
                if stock_id:
                    industry_map[stock_id] = industry
        except Exception as e:
            print(f"❌ API 產業分類取得失敗: {e}")
    
    print(f"✅ 已取得 {len(industry_map)} 筆產業分類")
    return industry_map


def get_stock_list(force_refresh: bool = False, core_only: bool = True) -> pd.DataFrame:
    """取得股票列表
    
    Args:
        force_refresh: 是否強制重新取得資料
        core_only: 是否只回傳精選 120 檔股票（預設 True）
    
    Returns:
        包含股票的 DataFrame
    """
    from .finmind_api import get_core_stocks_list
    
    # 檢查快取
    if not force_refresh:
        cached = get_cache('stock_list')
        if cached:
            df = pd.DataFrame(cached)
            if core_only:
                core_stocks = get_core_stocks_list()
                df = df[df['stock_id'].isin(core_stocks)]
            return df
        
        # 檢查資料庫
        df = get_all_stocks()
        if not df.empty:
            if core_only:
                core_stocks = get_core_stocks_list()
                df = df[df['stock_id'].isin(core_stocks)]
            return df
    
    print("📊 正在取得股票列表...")
    
    # 取得上市股票
    twse_df = fetch_twse_stocks()
    
    # 取得上櫃股票
    tpex_df = fetch_tpex_stocks()
    
    # 合併
    df = pd.concat([twse_df, tpex_df], ignore_index=True)
    
    # 取得產業分類
    industry_map = fetch_stock_industry()
    df['industry'] = df['stock_id'].map(industry_map).fillna('其他')
    
    if not df.empty:
        # 儲存到資料庫
        save_stocks(df)
        
        # 設定快取
        set_cache('stock_list', df.to_dict('records'), ttl_seconds=86400)
        
        print(f"✅ 已取得 {len(df)} 檔標的")
    
    # 過濾精選股票
    if core_only:
        core_stocks = get_core_stocks_list()
        df = df[df['stock_id'].isin(core_stocks)]
        print(f"📍 精選股票: {len(df)} 檔（涵蓋約 85% 市值）")
    
    return df


def get_etf_list() -> pd.DataFrame:
    """取得所有 ETF 列表"""
    df = get_stock_list()
    return df[df['asset_type'] == 'etf']


def search_stock(keyword: str) -> pd.DataFrame:
    """搜尋股票（支援代號和名稱）
    
    Args:
        keyword: 搜尋關鍵字
    
    Returns:
        符合條件的股票 DataFrame
    """
    df = get_stock_list()
    
    if df.empty:
        return df
    
    # 搜尋代號或名稱
    mask = (
        df['stock_id'].str.contains(keyword, case=False, na=False) |
        df['name'].str.contains(keyword, case=False, na=False)
    )
    
    return df[mask].head(50)


def get_stock_info(stock_id: str) -> Optional[Dict]:
    """取得單一股票詳細資訊"""
    df = get_stock_list()
    
    if df.empty:
        return None
    
    stock = df[df['stock_id'] == stock_id]
    
    if stock.empty:
        return None
    
    return stock.iloc[0].to_dict()


def fetch_stock_price(stock_id: str) -> Optional[float]:
    """取得股票即時價格"""
    if twstock is None:
        return None
    
    try:
        stock = twstock.realtime.get(stock_id)
        if stock['success']:
            return float(stock['realtime']['latest_trade_price'])
    except Exception as e:
        print(f"❌ 取得 {stock_id} 價格失敗: {e}")
    
    return None


def fetch_financial_report(stock_id: str, year: int = None, quarter: int = None) -> Dict:
    """取得財務報表資料（從公開資訊觀測站）
    
    這是一個模擬函數，實際使用時需要爬取公開資訊觀測站
    """
    if year is None:
        year = datetime.now().year
    if quarter is None:
        quarter = (datetime.now().month - 1) // 3 + 1
    
    # 這裡返回模擬資料，實際應用時需要爬取真實資料
    # 可以使用 FinMind API 或爬蟲取得
    return {}


def fetch_dividend_history(stock_id: str) -> List[Dict]:
    """取得股利發放歷史"""
    # 這裡返回模擬資料，實際應用時需要取得真實資料
    return []


def calculate_dividend_years(stock_id: str) -> int:
    """計算連續配息年數"""
    history = fetch_dividend_history(stock_id)
    
    if not history:
        return 0
    
    # 計算連續配息年數
    years = 0
    current_year = datetime.now().year
    
    for i, record in enumerate(history):
        if record.get('year') == current_year - i - 1:
            if record.get('dividend', 0) > 0:
                years += 1
            else:
                break
        else:
            break
    
    return years


def update_all_financial_data(progress_callback=None):
    """更新所有股票的財務資料
    
    Args:
        progress_callback: 進度回調函數 (current, total, stock_id)
    """
    df = get_stock_list()
    
    if df.empty:
        return
    
    total = len(df)
    
    for i, row in df.iterrows():
        stock_id = row['stock_id']
        
        if progress_callback:
            progress_callback(i + 1, total, stock_id)
        
        try:
            # 取得財務資料
            financial_data = fetch_financial_report(stock_id)
            
            if financial_data:
                save_financial_data(stock_id, financial_data)
            
            # 避免請求過快
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ 更新 {stock_id} 失敗: {e}")
            continue


# 模擬資料生成（用於開發測試）
def generate_sample_data(use_real_data: bool = True, token: str = None) -> pd.DataFrame:
    """生成財務資料
    
    Args:
        use_real_data: 是否使用真實資料（精選股票）
        token: FinMind API Token（可選，也會嘗試從環境變數讀取）
    
    Returns:
        包含財務指標的 DataFrame
    """
    import numpy as np
    import os
    
    # 嘗試從環境變數或 .env 讀取 Token
    if token is None:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
            token = os.getenv('FINMIND_TOKEN')
        except ImportError:
            pass
    
    df = get_stock_list()
    
    if df.empty:
        return df
    
    n = len(df)
    np.random.seed(42)
    
    # 先為所有股票生成基礎隨機資料（作為備用）
    df['roe'] = np.random.uniform(5, 30, n)
    df['roa'] = np.random.uniform(3, 15, n)
    df['net_profit_margin'] = np.random.uniform(5, 25, n)
    df['gross_margin'] = np.random.uniform(15, 50, n)
    df['operating_margin'] = np.random.uniform(5, 20, n)
    df['pe'] = np.random.uniform(5, 40, n)
    df['pb'] = np.random.uniform(0.5, 5, n)
    df['eps'] = np.random.uniform(1, 15, n)
    df['dividend_yield'] = np.random.uniform(1, 8, n)
    df['revenue_growth'] = np.random.uniform(-10, 30, n)
    df['eps_growth'] = np.random.uniform(-20, 50, n)
    df['dividend_years'] = np.random.randint(0, 15, n)
    df['debt_ratio'] = np.random.uniform(20, 70, n)
    df['current_ratio'] = np.random.uniform(80, 300, n)
    df['quick_ratio'] = np.random.uniform(60, 250, n)
    df['price'] = np.random.uniform(10, 500, n)
    
    # 標記是否為真實資料
    df['is_real_data'] = False
    
    # 嘗試使用 FinMind 真實資料
    if use_real_data:
        try:
            from .finmind_api import (
                get_quick_financial_data, 
                CORE_STOCKS,
                fetch_all_indicators,
                batch_fetch_indicators
            )
            
            print("📊 載入 FinMind 真實資料...")
            
            # 檢查是否有快取的完整資料
            cache_dir = Path(__file__).parent.parent / "data" / "cache"
            today = datetime.now().strftime('%Y%m%d')
            cache_file = cache_dir / f"batch_indicators_{today}.csv"
            
            if cache_file.exists():
                # 使用今日快取
                print("📂 使用今日快取的完整財務資料")
                cached_df = pd.read_csv(cache_file, encoding='utf-8-sig')
                
                for _, row in cached_df.iterrows():
                    stock_id = row.get('stock_id')
                    if stock_id in df['stock_id'].values:
                        idx = df[df['stock_id'] == stock_id].index[0]
                        
                        # 更新所有有效的指標
                        for col in ['roe', 'roa', 'eps', 'net_profit_margin', 'gross_margin',
                                   'operating_margin', 'debt_ratio', 'pe', 'pb', 
                                   'dividend_yield', 'dividend_years', 'revenue_growth', 
                                   'eps_growth', 'price']:
                            if col in row and pd.notna(row[col]):
                                df.loc[idx, col] = row[col]
                        
                        df.loc[idx, 'is_real_data'] = True
                
                print(f"✅ 已更新 {len(cached_df)} 檔股票的真實資料")
            else:
                # 使用快速取得 PE/PB（基本版）
                real_data = get_quick_financial_data(token)
                
                if not real_data.empty:
                    for _, row in real_data.iterrows():
                        stock_id = row.get('stock_id')
                        if stock_id in df['stock_id'].values:
                            idx = df[df['stock_id'] == stock_id].index[0]
                            if row.get('pe') is not None:
                                df.loc[idx, 'pe'] = row['pe']
                            if row.get('pb') is not None:
                                df.loc[idx, 'pb'] = row['pb']
                            df.loc[idx, 'is_real_data'] = True
                    
                    print(f"✅ 已更新 {len(real_data)} 檔股票的真實 PE/PB 資料")
            
            # 標記精選股票
            df['is_core'] = df['stock_id'].isin(CORE_STOCKS)
            
        except Exception as e:
            print(f"⚠️ FinMind 資料載入失敗，使用模擬資料: {e}")
    
    # 統計真實資料比例
    real_count = df['is_real_data'].sum()
    print(f"📈 真實資料比例: {real_count}/{len(df)} ({real_count/len(df)*100:.1f}%)")
    
    # 四捨五入
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].round(2)
    
    return df

