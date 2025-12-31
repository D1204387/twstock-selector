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
import urllib3
from pathlib import Path

# 抑制 SSL 警告（因為台灣證交所 SSL 證書有時會有問題）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import twstock
except ImportError:
    twstock = None

# from .database import (
#     get_connection, save_stocks, get_all_stocks,
#     save_financial_data, get_cache, set_cache
# )


# API URLs
TWSE_STOCK_LIST_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TPEX_STOCK_LIST_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"
TWSE_ETF_URL = "https://www.twse.com.tw/rwd/zh/ETF/etfDiv"

# 快取目錄
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
STOCK_LIST_CACHE = CACHE_DIR / "stock_list_cache.csv"


def fetch_twse_stocks() -> pd.DataFrame:
    """從證交所取得上市股票列表"""
    try:
        # 添加 verify=False 來繞過 SSL 驗證問題
        response = requests.get(TWSE_STOCK_LIST_URL, timeout=30, verify=False)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.rename(columns={
                'Code': 'stock_id',
                'Name': 'name',
                'IndustryCategory': 'industry'  # Map industry category
            })
            df['market'] = '上市'
            df['asset_type'] = df['stock_id'].apply(
                lambda x: 'etf' if x.startswith('00') else 'stock'
            )
            # Handle cases where IndustryCategory might be missing or titled differently
            if 'industry' not in df.columns:
                df['industry'] = '其他'
            
            return df[['stock_id', 'name', 'industry', 'market', 'asset_type']]
    except Exception as e:
        print(f"❌ 取得上市股票失敗: {e}")
    
    return pd.DataFrame()


def fetch_tpex_stocks() -> pd.DataFrame:
    """從櫃買中心取得上櫃股票列表"""
    try:
        # 添加 verify=False 來繞過 SSL 驗證問題
        response = requests.get(TPEX_STOCK_LIST_URL, timeout=30, verify=False)
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


def _load_stock_list_cache() -> pd.DataFrame:
    """從快取載入股票列表"""
    if STOCK_LIST_CACHE.exists():
        try:
            df = pd.read_csv(STOCK_LIST_CACHE, dtype={'stock_id': str})
            print(f"📂 使用股票列表快取: {len(df)} 檔")
            return df
        except Exception as e:
            print(f"❌ 讀取股票列表快取失敗: {e}")
    return pd.DataFrame()


def _save_stock_list_cache(df: pd.DataFrame):
    """儲存股票列表到快取"""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(STOCK_LIST_CACHE, index=False, encoding='utf-8-sig')
        print(f"💾 已儲存股票列表快取: {len(df)} 檔")
    except Exception as e:
        print(f"❌ 儲存股票列表快取失敗: {e}")


# 離線/備援用：核心股票產業對照表
HARDCODED_INDUSTRIES = {
    # 半導體
    "2330": "半導體", "2454": "半導體", "2303": "半導體", "3711": "半導體", "3034": "半導體",
    "2379": "半導體", "3035": "半導體", "3661": "半導體", "2408": "半導體", "3443": "半導體",
    # 電腦週邊/電子零組件
    "2317": "其他電子", "2308": "電子零組件", "2382": "電腦及週邊設備", "3231": "電腦及週邊設備",
    "2357": "電腦及週邊設備", "2301": "電腦及週邊設備", "2353": "電腦及週邊設備", 
    "3037": "電子零組件", "3008": "光電",
    # 金融
    "2881": "金融保險", "2882": "金融保險", "2891": "金融保險", "2886": "金融保險", "2880": "金融保險",
    "2885": "金融保險", "2892": "金融保險", "2884": "金融保險", "5880": "金融保險", "2883": "金融保險",
    "2887": "金融保險", "2890": "金融保險", "5871": "金融保險", "5876": "金融保險", "2801": "金融保險",
    "2889": "金融保險",
    # 傳產
    "1301": "塑膠", "1303": "塑膠", "1326": "化學", "6505": "油電燃氣",
    "2002": "鋼鐵", "1101": "水泥", "1102": "水泥",
    "2603": "航運", "2609": "航運", "2615": "航運", "2618": "航運",
    "2912": "貿易百貨", "2207": "貿易百貨", "9904": "其他",
    "1216": "食品",
    # 通信
    "2412": "通信網路", "3045": "通信網路", "4904": "通信網路"
}


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
            # 添加 verify=False 來繞過 SSL 驗證問題
            response = requests.get(url, timeout=30, verify=False)
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
    
    from .finmind_api import get_core_stocks_list
    
    print("📊 正在取得股票列表...")
    
    # 取得上市股票
    twse_df = fetch_twse_stocks()
    
    # 取得上櫃股票
    tpex_df = fetch_tpex_stocks()
    
    # 合併
    df = pd.concat([twse_df, tpex_df], ignore_index=True)
    
    # 如果 API 失敗（空的 DataFrame），嘗試使用快取
    if df.empty:
        print("⚠️ API 取得股票列表失敗，嘗試使用快取...")
        df = _load_stock_list_cache()
        
        # 如果快取也沒有，從 robust_indicators_data.csv 建立基礎列表
        if df.empty:
            from .finmind_api import CACHE_DIR as FINMIND_CACHE_DIR, get_core_stocks_list
            robust_file = FINMIND_CACHE_DIR / "robust_indicators_data.csv"
            if robust_file.exists():
                try:
                    cached_df = pd.read_csv(robust_file, dtype={'stock_id': str})
                    if 'stock_id' in cached_df.columns:
                        df = cached_df[['stock_id', 'name']].copy() if 'name' in cached_df.columns else cached_df[['stock_id']].copy()
                        if 'name' not in df.columns:
                            df['name'] = df['stock_id']  # 暫時使用代號作為名稱
                        df['industry'] = '其他'
                        df['market'] = '上市'
                        df['asset_type'] = df['stock_id'].apply(
                            lambda x: 'etf' if str(x).startswith('00') else 'stock'
                        )
                        print(f"📂 從快取指標資料建立股票列表: {len(df)} 檔")
                except Exception as e:
                    print(f"❌ 讀取指標快取失敗: {e}")
    
    
    # 如果還是空的，返回空 DataFrame
    if df.empty:
        print("❌ 無法取得股票列表")
        return df

    # -----------------------------------------------------------
    # [Robust Fix] 強制校正產業資料 (Offline-First 核心修正)
    # -----------------------------------------------------------
    if not df.empty:
        # 確保有 industry 欄位
        if 'industry' not in df.columns:
            df['industry'] = '其他'
            
        # 自動修正 ETF (00開頭)
        # 將所有 00 開頭的股票產業設為 'ETF'，方便篩選
        mask_etf = df['stock_id'].astype(str).str.startswith('00')
        df.loc[mask_etf, 'industry'] = 'ETF'
        
        # 根據硬編碼表修正核心股票產業 (避免 API 失敗變 '其他')
        for stock_id, ind in HARDCODED_INDUSTRIES.items():
            mask = (df['stock_id'] == stock_id)
            if mask.any():
                df.loc[mask, 'industry'] = ind
    
    # 取得產業分類
    industry_map = fetch_stock_industry()
    if 'stock_id' in df.columns:
        df['industry'] = df['stock_id'].map(industry_map).fillna('其他')
    
    if not df.empty:
        # 儲存到快取供下次使用
        _save_stock_list_cache(df)
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
                
                # 優化：使用向量化操作取代迴圈
                # 先將 stock_id 設為兩者的 index 以便對齊
                df.set_index('stock_id', inplace=True)
                cached_df.set_index('stock_id', inplace=True)
                
                # 找出共有的欄位
                common_cols = list(set(df.columns) & set(cached_df.columns))
                common_cols = [c for c in common_cols if c != 'stock_id']
                
                # 使用真實資料更新 (僅更新共有的欄位)
                # update 會保留 df 中那些 cached_df 為 NaN 的值，這不是我們要的
                # 我們想要 cached_df 有值的就覆蓋
                
                # 更好的方式：直接賦值真實資料的欄位
                # 但要小心 cached_df 可能包含 df 沒有的股票，或少了 df 有的股票
                
                # 過濾出需要的欄位
                target_cols = ['roe', 'roa', 'eps', 'net_profit_margin', 'gross_margin',
                               'operating_margin', 'debt_ratio', 'pe', 'pb', 
                               'dividend_yield', 'dividend_years', 'revenue_growth', 
                               'eps_growth', 'price']
                
                valid_cols = [c for c in target_cols if c in cached_df.columns]
                
                if valid_cols:
                    # 僅更新 df 中存在的股票
                    # 使用 update，它會用 cached_df 的非 NA 值更新 df
                    df.update(cached_df[valid_cols])
                    
                    # 標記真實資料
                    # 找出在 cached_df 中有資料的股票索引
                    common_indices = df.index.intersection(cached_df.index)
                    if not common_indices.empty:
                        df.loc[common_indices, 'is_real_data'] = True
                
                # 還原 index
                df.reset_index(inplace=True)
                
                print(f"✅ 已更新 {len(cached_df)} 檔股票的真實資料")
            else:
                # 使用快速取得 PE/PB（基本版）
                real_data = get_quick_financial_data(token)
                
                if not real_data.empty:
                    df.set_index('stock_id', inplace=True)
                    real_data.set_index('stock_id', inplace=True)
                    
                    # 更新 PE/PB
                    if 'pe' in real_data.columns:
                        df.update(real_data[['pe']])
                    if 'pb' in real_data.columns:
                        df.update(real_data[['pb']])
                    
                    # 標記真實資料
                    common_indices = df.index.intersection(real_data.index)
                    if not common_indices.empty:
                        df.loc[common_indices, 'is_real_data'] = True
                        
                    df.reset_index(inplace=True)
                    
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


def load_robust_data() -> pd.DataFrame:
    """載入真實財務資料（無模擬數據）
    
    Returns:
        包含真實財務指標的 DataFrame，若無資料則為 NaN
    """
    from .finmind_api import CACHE_DIR
    import numpy as np
    
    # 1. 取得基礎股票列表
    df = get_stock_list()
    if df.empty:
        return df
        
    # 2. 初始化欄位為 NaN
    cols = ['roe', 'roa', 'eps', 'net_profit_margin', 'gross_margin',
            'operating_margin', 'debt_ratio', 'pe', 'pb', 
            'dividend_yield', 'dividend_years', 'revenue_growth', 
            'eps_growth', 'price']
            
    for col in cols:
        df[col] = np.nan
        
    df['is_real_data'] = False
    
    # 3. 讀取穩健下載的快取資料
    cache_file = CACHE_DIR / "robust_indicators_data.csv"
    
    if cache_file.exists():
        try:
            cached_df = pd.read_csv(cache_file, dtype={'stock_id': str})
            
            # 使用 update 更新資料
            df.set_index('stock_id', inplace=True)
            cached_df.set_index('stock_id', inplace=True)
            
            valid_cols = [c for c in cols if c in cached_df.columns]
            if valid_cols:
                df.update(cached_df[valid_cols])
                
                # 標記有資料的列
                common = df.index.intersection(cached_df.index)
                df.loc[common, 'is_real_data'] = True
                
            df.reset_index(inplace=True)
            print(f"✅ 已載入穩健真實資料: {len(common)} 筆")
            
        except Exception as e:
            print(f"❌ 讀取真實資料快取失敗: {e}")
    else:
        print("⚠️ 找不到真實資料快取檔案 (robust_indicators_data.csv)")
    
    # 四捨五入
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].round(2)
        
    return df


def get_data_update_time() -> str:
    """取得資料最後更新時間
    
    Returns:
        格化後的時間字串，若無檔案則回傳 '尚未更新'
    """
    from .finmind_api import CACHE_DIR
    cache_file = CACHE_DIR / "robust_indicators_data.csv"
    
    if cache_file.exists():
        timestamp = cache_file.stat().st_mtime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    
    return "尚未更新"


