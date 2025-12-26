#!/usr/bin/env python3
"""
台股智選系統 - 智慧資料下載器
Taiwan Stock Selection System - Smart Data Downloader

功能：
1. 檢查現有資料，只下載缺失的股票
2. 追蹤下載進度，支援斷點續傳
3. 自動合併新舊資料
4. 每小時額度管理（600 次請求）
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time
import sys
import os

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.finmind_api import (
    fetch_indicators_lite,
    get_core_stocks_list,
    CACHE_DIR
)


def get_missing_stocks(cache_file: Path, all_stocks: list, required_fields: list = ['pe', 'pb', 'eps']) -> list:
    """找出缺失資料的股票
    
    Args:
        cache_file: 快取檔案路徑
        all_stocks: 所有股票列表
        required_fields: 必須有資料的欄位
        
    Returns:
        缺失資料的股票列表
    """
    if not cache_file.exists():
        return all_stocks
    
    df = pd.read_csv(cache_file)
    
    missing = []
    for stock_id in all_stocks:
        stock_data = df[df['stock_id'] == stock_id]
        
        if stock_data.empty:
            missing.append(stock_id)
            continue
        
        # 檢查必要欄位是否有資料
        row = stock_data.iloc[0]
        for field in required_fields:
            if field in row and pd.isna(row[field]):
                missing.append(stock_id)
                break
    
    return missing


def smart_download(token: str = None, max_requests: int = 180):
    """智慧下載 - 只下載缺失資料的股票
    
    Args:
        token: FinMind API Token
        max_requests: 本次最多使用的 API 請求數（預設 180，約 60 檔股票）
    """
    print("=" * 60)
    print("📊 台股智選系統 - 智慧下載器")
    print("=" * 60)
    print()
    
    # 取得精選股票列表
    all_stocks = get_core_stocks_list()
    
    # 快取檔案
    cache_file = CACHE_DIR / f"batch_indicators_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # 找出缺失資料的股票
    missing_stocks = get_missing_stocks(cache_file, all_stocks)
    
    print(f"📋 精選股票總數: {len(all_stocks)} 檔")
    print(f"✅ 已有完整資料: {len(all_stocks) - len(missing_stocks)} 檔")
    print(f"❓ 需要下載資料: {len(missing_stocks)} 檔")
    print()
    
    if not missing_stocks:
        print("🎉 所有股票都已有完整資料！")
        return
    
    # 計算本次可下載數量（每檔約 3 次請求）
    requests_per_stock = 3
    max_stocks = min(max_requests // requests_per_stock, len(missing_stocks))
    
    print(f"💡 本次將下載: {max_stocks} 檔（使用約 {max_stocks * requests_per_stock} 次 API 請求）")
    print(f"   剩餘待下載: {len(missing_stocks) - max_stocks} 檔")
    print()
    
    confirm = input("確定要開始下載嗎？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消下載")
        return
    
    print()
    print("-" * 60)
    
    # 載入現有資料
    if cache_file.exists():
        existing_df = pd.read_csv(cache_file)
        existing_data = existing_df.to_dict('records')
        existing_ids = set(existing_df['stock_id'].astype(str))
    else:
        existing_data = []
        existing_ids = set()
    
    # 下載資料
    new_data = []
    success_count = 0
    start_time = time.time()
    
    for i, stock_id in enumerate(missing_stocks[:max_stocks]):
        elapsed = time.time() - start_time
        remaining = (elapsed / (i + 1)) * (max_stocks - i - 1) if i > 0 else 0
        
        print(f"\r  [{i+1}/{max_stocks}] {stock_id} - 已用時 {int(elapsed//60)}分{int(elapsed%60)}秒, 預估剩餘 {int(remaining//60)}分", end="")
        
        try:
            data = fetch_indicators_lite(stock_id, token)
            
            # 檢查是否有有效資料
            if data.get('pe') or data.get('pb') or data.get('eps'):
                success_count += 1
            
            # 更新或新增資料
            if stock_id in existing_ids:
                # 更新現有記錄
                for record in existing_data:
                    if str(record.get('stock_id')) == str(stock_id):
                        for key, value in data.items():
                            if value is not None:
                                record[key] = value
                        break
            else:
                new_data.append(data)
            
        except Exception as e:
            print(f"\n  ⚠️ {stock_id}: {e}")
    
    print()
    print("-" * 60)
    
    # 合併並儲存
    all_data = existing_data + new_data
    result_df = pd.DataFrame(all_data)
    result_df.to_csv(cache_file, index=False, encoding='utf-8-sig')
    
    # 統計結果
    print()
    print("=" * 60)
    print("✅ 下載完成！")
    print(f"📊 本次下載: {max_stocks} 檔，成功取得有效資料: {success_count} 檔")
    print(f"💾 資料儲存於: {cache_file}")
    print()
    
    # 顯示各欄位統計
    print("📈 目前資料完整度:")
    for col in ['pe', 'pb', 'eps', 'dividend_years']:
        if col in result_df.columns:
            valid = result_df[col].notna().sum()
            print(f"  {col}: {valid}/{len(result_df)} ({valid/len(result_df)*100:.0f}%)")
    
    # 計算剩餘
    remaining_stocks = get_missing_stocks(cache_file, all_stocks)
    if remaining_stocks:
        print()
        print(f"⏳ 還有 {len(remaining_stocks)} 檔股票需要下載")
        print("   請稍後再執行一次此腳本")
    else:
        print()
        print("🎉 所有股票都已有完整資料！")
    
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='智慧資料下載器')
    parser.add_argument('--max-requests', type=int, default=180, 
                        help='本次最多使用的 API 請求數（預設 180）')
    
    args = parser.parse_args()
    
    token = os.getenv('FINMIND_TOKEN')
    if not token:
        print("❌ 請在 .env 檔案中設定 FINMIND_TOKEN")
        sys.exit(1)
    
    smart_download(token, args.max_requests)
