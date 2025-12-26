#!/usr/bin/env python3
"""
台股智選系統 - FinMind 資料下載腳本
Taiwan Stock Selection System - FinMind Data Download Script

使用方式：
1. 先在 .env 檔案中設定 FINMIND_TOKEN
2. 執行: python scripts/download_data.py [--mode core|all]

選項：
- core: 只下載精選 110 檔（約 1-2 小時）
- all: 下載全部股票（約 20 小時，可分次執行）
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 載入環境變數
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
except ImportError:
    print("⚠️ 請安裝 python-dotenv: pip install python-dotenv")

from src.finmind_api import (
    batch_fetch_indicators,
    get_core_stocks_list,
    CACHE_DIR
)
from src.data_fetcher import get_stock_list


def download_core_stocks(token: str):
    """下載精選 110 檔股票的財務資料"""
    print("=" * 60)
    print("📊 開始下載精選股票財務資料")
    print("=" * 60)
    
    core_stocks = get_core_stocks_list()
    print(f"📋 精選股票數量: {len(core_stocks)} 檔")
    print(f"⏱️ 預估時間: 1-2 小時")
    print()
    
    # 詢問確認
    confirm = input("確定要開始下載嗎？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    start_time = datetime.now()
    
    def progress_callback(current, total, stock_id):
        elapsed = (datetime.now() - start_time).seconds
        eta = (elapsed / current * total - elapsed) if current > 0 else 0
        print(f"\r  [{current}/{total}] {stock_id} - 已用時 {elapsed//60}分{elapsed%60}秒, 預估剩餘 {eta//60:.0f}分", end="")
    
    df = batch_fetch_indicators(core_stocks, token, progress_callback)
    
    end_time = datetime.now()
    duration = (end_time - start_time).seconds
    
    print()
    print("=" * 60)
    print(f"✅ 下載完成！")
    print(f"📊 成功取得: {len(df)} 檔股票")
    print(f"⏱️ 總耗時: {duration//60} 分 {duration%60} 秒")
    print(f"💾 資料儲存於: {CACHE_DIR}")
    print("=" * 60)


def download_all_stocks(token: str, start_from: int = 0):
    """下載全部股票的財務資料（支援斷點續傳）"""
    print("=" * 60)
    print("📊 開始下載全部股票財務資料")
    print("=" * 60)
    
    df = get_stock_list()
    all_stocks = df['stock_id'].tolist()
    
    # 從指定位置開始（斷點續傳）
    stocks_to_download = all_stocks[start_from:]
    
    print(f"📋 全部股票數量: {len(all_stocks)} 檔")
    print(f"📋 本次下載數量: {len(stocks_to_download)} 檔（從第 {start_from+1} 檔開始）")
    print(f"⏱️ 預估時間: {len(stocks_to_download) * 5 / 600:.1f} 小時")
    print()
    print("⚠️ 注意：可隨時按 Ctrl+C 中斷，下次從中斷處繼續")
    print()
    
    # 詢問確認
    confirm = input("確定要開始下載嗎？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    start_time = datetime.now()
    last_index = start_from
    
    def progress_callback(current, total, stock_id):
        nonlocal last_index
        last_index = start_from + current
        elapsed = (datetime.now() - start_time).seconds
        eta = (elapsed / current * total - elapsed) if current > 0 else 0
        print(f"\r  [{start_from + current}/{len(all_stocks)}] {stock_id} - 剩餘 {eta//3600:.0f}時{(eta%3600)//60:.0f}分", end="")
    
    try:
        df = batch_fetch_indicators(stocks_to_download, token, progress_callback)
        print()
        print("=" * 60)
        print(f"✅ 下載完成！")
        print(f"📊 成功取得: {len(df)} 檔股票")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("⚠️ 下載中斷")
        print(f"📊 已下載到第 {last_index} 檔")
        print(f"💡 下次繼續請執行: python scripts/download_data.py --mode all --start {last_index}")
        print("=" * 60)


def check_token():
    """檢查 Token 是否設定"""
    token = os.getenv('FINMIND_TOKEN')
    
    if not token or token == 'your_token_here':
        print("❌ 錯誤：尚未設定 FINMIND_TOKEN")
        print()
        print("請依照以下步驟設定：")
        print("1. 到 https://finmindtrade.com/ 註冊帳號")
        print("2. 登入後取得 API Token")
        print("3. 在專案根目錄建立 .env 檔案：")
        print("   cp .env.example .env")
        print("4. 編輯 .env，填入您的 Token：")
        print("   FINMIND_TOKEN=你的token")
        print()
        return None
    
    return token


def main():
    parser = argparse.ArgumentParser(description='FinMind 財務資料下載腳本')
    parser.add_argument('--mode', choices=['core', 'all'], default='core',
                       help='core: 精選110檔, all: 全部股票')
    parser.add_argument('--start', type=int, default=0,
                       help='從第幾檔開始（用於斷點續傳）')
    
    args = parser.parse_args()
    
    print()
    print("🚀 台股智選系統 - FinMind 資料下載器")
    print()
    
    # 檢查 Token
    token = check_token()
    if not token:
        return
    
    print(f"✅ Token 已設定")
    print()
    
    if args.mode == 'core':
        download_core_stocks(token)
    else:
        download_all_stocks(token, args.start)


if __name__ == "__main__":
    main()
