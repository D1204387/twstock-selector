"""
台股智選系統 - 資料庫模組
Taiwan Stock Selection System - Database Module
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

# 資料庫路徑
DB_PATH = Path(__file__).parent.parent / "data" / "twstock.db"


def get_connection():
    """取得資料庫連線"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH))


def init_db():
    """初始化資料庫表格"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 股票基本資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            stock_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            industry TEXT,
            market TEXT,
            asset_type TEXT DEFAULT 'stock',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 財務資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            year INTEGER,
            quarter INTEGER,
            roe REAL,
            roa REAL,
            net_profit_margin REAL,
            gross_margin REAL,
            operating_margin REAL,
            pe REAL,
            pb REAL,
            eps REAL,
            dividend_yield REAL,
            revenue_growth REAL,
            eps_growth REAL,
            dividend_years INTEGER,
            debt_ratio REAL,
            current_ratio REAL,
            quick_ratio REAL,
            price REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
            UNIQUE(stock_id, year, quarter)
        )
    """)
    
    # ETF 專屬資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            expense_ratio REAL,
            aum REAL,
            tracking_error REAL,
            dividend_frequency TEXT,
            underlying_index TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
            UNIQUE(stock_id)
        )
    """)
    
    # 快取表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            expires_at TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ 資料庫初始化完成")


def save_stocks(df: pd.DataFrame):
    """儲存股票列表到資料庫"""
    conn = get_connection()
    df.to_sql('stocks', conn, if_exists='replace', index=False)
    conn.close()


def get_all_stocks() -> pd.DataFrame:
    """取得所有股票資料"""
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM stocks", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df


def get_stocks_by_type(asset_type: str = 'all') -> pd.DataFrame:
    """根據資產類型取得股票
    
    Args:
        asset_type: 'all', 'stock', 'etf'
    """
    conn = get_connection()
    try:
        if asset_type == 'all':
            df = pd.read_sql("SELECT * FROM stocks", conn)
        else:
            df = pd.read_sql(
                "SELECT * FROM stocks WHERE asset_type = ?", 
                conn, 
                params=(asset_type,)
            )
    except:
        df = pd.DataFrame()
    conn.close()
    return df


def save_financial_data(stock_id: str, data: dict, year: int = None, quarter: int = None):
    """儲存財務資料"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if year is None:
        year = datetime.now().year
    if quarter is None:
        quarter = (datetime.now().month - 1) // 3 + 1
    
    columns = ['stock_id', 'year', 'quarter'] + list(data.keys())
    values = [stock_id, year, quarter] + list(data.values())
    
    placeholders = ', '.join(['?' for _ in values])
    column_names = ', '.join(columns)
    
    cursor.execute(f"""
        INSERT OR REPLACE INTO financial_data ({column_names})
        VALUES ({placeholders})
    """, values)
    
    conn.commit()
    conn.close()


def get_financial_data(stock_id: str = None) -> pd.DataFrame:
    """取得財務資料"""
    conn = get_connection()
    try:
        if stock_id:
            df = pd.read_sql(
                """
                SELECT s.*, f.* 
                FROM stocks s 
                LEFT JOIN financial_data f ON s.stock_id = f.stock_id 
                WHERE s.stock_id = ?
                ORDER BY f.year DESC, f.quarter DESC
                LIMIT 1
                """,
                conn,
                params=(stock_id,)
            )
        else:
            df = pd.read_sql(
                """
                SELECT s.*, f.* 
                FROM stocks s 
                LEFT JOIN (
                    SELECT * FROM financial_data 
                    WHERE (stock_id, year, quarter) IN (
                        SELECT stock_id, MAX(year), MAX(quarter) 
                        FROM financial_data 
                        GROUP BY stock_id
                    )
                ) f ON s.stock_id = f.stock_id
                """,
                conn
            )
    except Exception as e:
        print(f"Error: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


def get_latest_financial_data() -> pd.DataFrame:
    """取得所有股票的最新財務資料（用於篩選和排名）"""
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT 
                s.stock_id,
                s.name,
                s.industry,
                s.market,
                s.asset_type,
                f.roe,
                f.roa,
                f.net_profit_margin,
                f.gross_margin,
                f.operating_margin,
                f.pe,
                f.pb,
                f.eps,
                f.dividend_yield,
                f.revenue_growth,
                f.eps_growth,
                f.dividend_years,
                f.debt_ratio,
                f.current_ratio,
                f.quick_ratio,
                f.price
            FROM stocks s
            LEFT JOIN financial_data f ON s.stock_id = f.stock_id
            WHERE f.id IN (
                SELECT MAX(id) FROM financial_data GROUP BY stock_id
            ) OR f.id IS NULL
            """,
            conn
        )
    except Exception as e:
        print(f"Error getting latest financial data: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


def save_etf_data(stock_id: str, data: dict):
    """儲存 ETF 專屬資料"""
    conn = get_connection()
    cursor = conn.cursor()
    
    data['stock_id'] = stock_id
    columns = list(data.keys())
    values = list(data.values())
    
    placeholders = ', '.join(['?' for _ in values])
    column_names = ', '.join(columns)
    
    cursor.execute(f"""
        INSERT OR REPLACE INTO etf_data ({column_names})
        VALUES ({placeholders})
    """, values)
    
    conn.commit()
    conn.close()


def search_stocks(keyword: str) -> pd.DataFrame:
    """搜尋股票（支援代號和名稱模糊搜尋）"""
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT s.*, f.roe, f.pe, f.pb, f.eps, f.dividend_yield, f.price
            FROM stocks s
            LEFT JOIN financial_data f ON s.stock_id = f.stock_id
            WHERE s.stock_id LIKE ? OR s.name LIKE ?
            GROUP BY s.stock_id
            ORDER BY s.stock_id
            LIMIT 50
            """,
            conn,
            params=(f"%{keyword}%", f"%{keyword}%")
        )
    except:
        df = pd.DataFrame()
    conn.close()
    return df


def export_to_csv(df: pd.DataFrame, filename: str) -> str:
    """匯出 DataFrame 到 CSV"""
    export_path = Path(__file__).parent.parent / "data" / filename
    df.to_csv(export_path, index=False, encoding='utf-8-sig')
    return str(export_path)


def set_cache(key: str, value: any, ttl_seconds: int = 3600):
    """設定快取"""
    conn = get_connection()
    cursor = conn.cursor()
    
    expires_at = datetime.now().timestamp() + ttl_seconds
    value_json = json.dumps(value, default=str)
    
    cursor.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, value_json, expires_at)
    )
    
    conn.commit()
    conn.close()


def get_cache(key: str) -> any:
    """取得快取"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?",
        (key,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        value_json, expires_at = result
        if datetime.now().timestamp() < expires_at:
            return json.loads(value_json)
    
    return None


def clear_expired_cache():
    """清理過期快取"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM cache WHERE expires_at < ?",
        (datetime.now().timestamp(),)
    )
    
    conn.commit()
    conn.close()


# 初始化資料庫（模組載入時執行）
if __name__ == "__main__":
    init_db()
