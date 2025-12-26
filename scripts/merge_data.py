#!/usr/bin/env python3
"""
台股智選系統 - 資料合併腳本
Taiwan Stock Selection System - Data Merge Script

用途：合併多次下載的結果，保留最完整的資料

使用方式：
python scripts/merge_data.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 快取目錄
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"


def merge_indicator_files():
    """合併所有 batch_indicators 檔案"""
    
    print("🔍 搜尋快取檔案...")
    
    # 找出所有 batch_indicators 檔案
    files = list(CACHE_DIR.glob("batch_indicators_*.csv"))
    
    if not files:
        print("❌ 找不到任何快取檔案")
        return
    
    print(f"📂 找到 {len(files)} 個檔案:")
    for f in files:
        print(f"  - {f.name}")
    
    # 讀取並合併
    all_dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            df['source_file'] = f.name
            all_dfs.append(df)
            print(f"  ✅ 讀取 {f.name}: {len(df)} 筆")
        except Exception as e:
            print(f"  ⚠️ 讀取 {f.name} 失敗: {e}")
    
    if not all_dfs:
        print("❌ 沒有可合併的資料")
        return
    
    # 合併所有資料
    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"\n📊 總共 {len(combined)} 筆記錄")
    
    # 按 stock_id 分組，保留每個欄位最完整的值
    def merge_rows(group):
        """合併同一股票的多筆記錄，優先保留非空值"""
        result = {}
        for col in group.columns:
            if col == 'source_file':
                continue
            # 取第一個非空值
            non_null = group[col].dropna()
            if len(non_null) > 0:
                result[col] = non_null.iloc[0]
            else:
                result[col] = None
        return pd.Series(result)
    
    print("\n🔄 合併資料中...")
    merged = combined.groupby('stock_id', as_index=False).apply(merge_rows)
    
    # 確保 stock_id 是字串
    merged['stock_id'] = merged['stock_id'].astype(str)
    
    # 統計各欄位有效資料數
    print("\n📈 合併後各欄位有效資料數:")
    indicator_cols = ['roe', 'roa', 'eps', 'pe', 'pb', 'dividend_yield', 
                      'dividend_years', 'revenue_growth', 'eps_growth', 'price']
    
    for col in indicator_cols:
        if col in merged.columns:
            valid = merged[col].notna().sum()
            print(f"  {col}: {valid}/{len(merged)} ({valid/len(merged)*100:.0f}%)")
    
    # 儲存合併後的檔案
    output_file = CACHE_DIR / f"batch_indicators_{datetime.now().strftime('%Y%m%d')}.csv"
    merged.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 合併完成！")
    print(f"📊 總共 {len(merged)} 檔股票")
    print(f"💾 儲存至: {output_file}")
    
    return merged


def backup_old_files():
    """備份舊檔案"""
    backup_dir = CACHE_DIR / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    files = list(CACHE_DIR.glob("batch_indicators_*.csv"))
    for f in files:
        backup_path = backup_dir / f.name
        if not backup_path.exists():
            import shutil
            shutil.copy(f, backup_path)
            print(f"📦 備份: {f.name}")


if __name__ == "__main__":
    print("=" * 60)
    print("📊 台股智選系統 - 資料合併工具")
    print("=" * 60)
    print()
    
    # 先備份
    backup_old_files()
    print()
    
    # 合併
    merge_indicator_files()
