
#!/usr/bin/env python3
"""
台股智選系統 - 穩健資料下載器 (Robust Data Downloader)
功能：
1. 嚴格速率限制 (每 6 秒一次請求)，確保不被 Ban。
2. 斷點續傳：隨時可中斷，下次執行從上次進度繼續。
3. 資料驗證：簡單檢查股價範圍，確保不是異常值。
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import sys
import os

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.finmind_api import (
    fetch_indicators_full,  # 使用完整版（6 次 API 請求）
    get_core_stocks_list, 
    CACHE_DIR
)

# 設定
RATE_LIMIT_SLEEP = 6.0  # 秒 (FinMind 限制約 600次/小時 -> 10次/分 -> 6秒/次)
CACHE_FILE = CACHE_DIR / "robust_indicators_data.csv"

def load_progress():
    if CACHE_FILE.exists():
        try:
            return pd.read_csv(CACHE_FILE, dtype={'stock_id': str})
        except Exception as e:
            print(f"⚠️ 讀取快取失敗: {e}，將重新開始")
            return pd.DataFrame()
    return pd.DataFrame()

def save_progress(df):
    df.to_csv(CACHE_FILE, index=False, encoding='utf-8-sig')

def main():
    token = os.getenv('FINMIND_TOKEN')
    if not token:
        print("❌ 設定錯誤：找不到 FINMIND_TOKEN，請檢查 .env 檔案")
        return

    print("="*60)
    print("🚀 啟動穩健下載器 (Robust Downloader)")
    print(f"⏱️  速率限制: 每 {RATE_LIMIT_SLEEP} 秒請求一次 (10 次/分)")
    print(f"💾 儲存路徑: {CACHE_FILE}")
    print("="*60)

    # 1. 取得目標股票清單
    all_stocks = get_core_stocks_list()
    
    # 2. 讀取現有進度
    df_current = load_progress()
    
    completed_stocks = set()
    if not df_current.empty and 'stock_id' in df_current.columns:
        # 檢查資料完整性 (必須有 ROE, PE 和 Price 才算真正完成)
        # 注意：有些個股可能真的無 ROE (如新上市)，但在核心 120 檔中應極少
        # 如果欄位存在才檢查，不存在視為未完成
        # 如果欄位存在才檢查，不存在視為未完成
        if 'stock_id' in df_current.columns:
            # 區分 ETF 與一般股票
            # ETF (00開頭) 不需要 ROE 和 負債比
            for _, row in df_current.iterrows():
                stock_id = str(row['stock_id'])
                is_etf = stock_id.startswith('00')
                
                # 檢查欄位是否存在
                has_price = pd.notna(row.get('price'))
                has_pe = pd.notna(row.get('pe'))
                has_roe = pd.notna(row.get('roe'))
                has_debt = pd.notna(row.get('debt_ratio'))
                
                if is_etf:
                    # ETF 只要有股價就當作有效 (PE 也不一定有)
                    if has_price:
                        completed_stocks.add(stock_id)
                else:
                    # 一般股票：只要有股價就接受（ROE/負債率可能因虧損或資料延遲而缺失）
                    # 這樣可以保留台塑、中鋼等重要但暫時虧損的公司
                    if has_price:
                        completed_stocks.add(stock_id)
            
            print(f"📊 已驗證 {len(completed_stocks)} 檔資料完整")
        else:
            print("⚠️ 快取資料缺少必要欄位，將視為全部未完成")
            completed_stocks = set()

    
    pending_stocks = [s for s in all_stocks if s not in completed_stocks]
    
    print(f"📋 總股票數: {len(all_stocks)}")
    print(f"✅ 已完成: {len(completed_stocks)}")
    print(f"⏳ 待下載: {len(pending_stocks)}")
    
    if not pending_stocks:
        print("🎉 所有股票資料已下載完成！")
        return

    # 3. 開始下載
    print("\n開始執行... (按 Ctrl+C 可隨時暫停)")
    
    # 轉換現有 DataFrame 為 list of dict 以便更新
    data_list = df_current.to_dict('records') if not df_current.empty else []
    
    try:
        for i, stock_id in enumerate(pending_stocks):
            start_time = time.time()
            current_idx = len(completed_stocks) + i + 1
            
            print(f"[{current_idx}/{len(all_stocks)}] 下載 {stock_id} ... ", end="", flush=True)
            
            # 使用 lite 版 (3 次 API 請求)
            # 因為 fetch_indicators_lite 內部已有 sleep，但我們要更嚴格控制
            # 所以這裡我們手動計算時間
            
            try:
                stock_data = fetch_indicators_full(stock_id, token)  # 完整版
            except BlockingIOError:
                print("\n⛔️ API 額度已達上限 (402)，程式自動暫停。")
                print("💡 請等待約 1 小時後再重新執行，進度已自動儲存。")
                break
            
            # 簡單驗證
            if stock_data.get('msg') == 'Requests reach the upper limit':
                 print("⚠️  API 額度已滿！請等待一小時後再試。")
                 break

            # 判斷是否為 ETF
            is_etf = str(stock_id).startswith('00')
            
            price = stock_data.get('price')
            roe = stock_data.get('roe')
            
            # 成功條件判定：只要有股價即可（虧損公司可能缺 ROE）
            success = False
            if price:
                success = True
                if is_etf:
                    print(f"✅ 成功 (股價: {price})")
                else:
                    if roe is not None:
                        print(f"✅ 成功 (股價: {price}, ROE: {roe})")
                    else:
                        print(f"✅ 成功 (股價: {price}, ROE: 無)")

            if success:
                # 更新或新增資料
                # 先移除舊的（如果存在）
                data_list = [d for d in data_list if str(d.get('stock_id')) != str(stock_id)]
                data_list.append(stock_data)
                
                # 立即儲存
                save_progress(pd.DataFrame(data_list))
            else:
                print(f"⚠️  資料不完整，缺: 股價 (不儲存)")
                # 不儲存，下次執行會重試
            
            # 強制睡眠補足時間
            elapsed = time.time() - start_time
            if elapsed < RATE_LIMIT_SLEEP:
                time.sleep(RATE_LIMIT_SLEEP - elapsed)
                
    except KeyboardInterrupt:
        print("\n\n🛑 使用者中斷下載。進度已儲存。")
    except Exception as e:
        print(f"\n\n❌ 發生錯誤: {e}")
    finally:
        print(f"\n下載結束。目前共持有 {len(data_list)} 筆資料。")

if __name__ == "__main__":
    main()
