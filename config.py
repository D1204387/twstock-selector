"""
台股智選系統 - 設定檔
Taiwan Stock Selection System - Configuration
"""

# 財務指標定義與說明
INDICATORS = {
    # 獲利能力指標
    "roe": {
        "name": "ROE",
        "full_name": "股東權益報酬率",
        "description": "衡量公司運用股東資本創造利潤的能力",
        "formula": "淨利 / 股東權益 × 100%",
        "ideal_min": 15,
        "ideal_max": None,
        "unit": "%",
        "category": "獲利能力",
        "interpretation": "越高越好，代表公司善用股東的錢賺取利潤。ROE > 15% 通常被視為優質公司。"
    },
    "roa": {
        "name": "ROA",
        "full_name": "資產報酬率",
        "description": "衡量公司運用總資產創造利潤的效率",
        "formula": "淨利 / 總資產 × 100%",
        "ideal_min": 8,
        "ideal_max": None,
        "unit": "%",
        "category": "獲利能力",
        "interpretation": "越高越好，代表公司資產運用效率高。ROA > 8% 為理想標準。"
    },
    "net_profit_margin": {
        "name": "淨利率",
        "full_name": "淨利率",
        "description": "每一元營收中實際賺取的淨利",
        "formula": "淨利 / 營收 × 100%",
        "ideal_min": 10,
        "ideal_max": None,
        "unit": "%",
        "category": "獲利能力",
        "interpretation": "越高越好，高淨利率代表成本控制佳或產品附加價值高。"
    },
    "gross_margin": {
        "name": "毛利率",
        "full_name": "毛利率",
        "description": "每一元營收扣除直接成本後的毛利",
        "formula": "(營收 - 銷貨成本) / 營收 × 100%",
        "ideal_min": 20,
        "ideal_max": None,
        "unit": "%",
        "category": "獲利能力",
        "interpretation": "越高越好，高毛利率代表產品競爭力強或成本控制佳。"
    },
    "operating_margin": {
        "name": "營業利潤率",
        "full_name": "營業利潤率",
        "description": "本業經營的獲利能力",
        "formula": "營業利益 / 營收 × 100%",
        "ideal_min": 10,
        "ideal_max": None,
        "unit": "%",
        "category": "獲利能力",
        "interpretation": "越高越好，反映公司本業的經營效率。"
    },
    
    # 估值指標
    "pe": {
        "name": "本益比",
        "full_name": "本益比 (P/E Ratio)",
        "description": "股價相對於每股盈餘的倍數",
        "formula": "股價 / 每股盈餘 (EPS)",
        "ideal_min": 10,
        "ideal_max": 20,
        "unit": "倍",
        "category": "估值指標",
        "interpretation": "過高可能代表股價偏貴，過低可能代表被低估。合理區間為 10-20 倍。"
    },
    "pb": {
        "name": "股價淨值比",
        "full_name": "股價淨值比 (P/B Ratio)",
        "description": "股價相對於每股淨值的倍數",
        "formula": "股價 / 每股淨值",
        "ideal_min": None,
        "ideal_max": 2,
        "unit": "倍",
        "category": "估值指標",
        "interpretation": "PB < 1 可能代表股價低於帳面價值，PB < 2 通常被視為合理。"
    },
    "eps": {
        "name": "每股盈餘",
        "full_name": "每股盈餘 (EPS)",
        "description": "每一股可分配到的盈餘",
        "formula": "稅後淨利 / 流通在外股數",
        "ideal_min": 3,
        "ideal_max": None,
        "unit": "元",
        "category": "估值指標",
        "interpretation": "越高越好，代表公司獲利能力強。EPS > 3 元為理想標準。"
    },
    "dividend_yield": {
        "name": "股息率",
        "full_name": "現金殖利率",
        "description": "每年現金股利相對於股價的比率",
        "formula": "每股現金股利 / 股價 × 100%",
        "ideal_min": 4,
        "ideal_max": None,
        "unit": "%",
        "category": "估值指標",
        "interpretation": "越高越好，高殖利率適合追求穩定現金流的投資人。> 4% 為理想。"
    },
    
    # 成長性指標
    "revenue_growth": {
        "name": "營收成長率",
        "full_name": "營收年增率",
        "description": "今年營收相較去年的成長幅度",
        "formula": "(今年營收 - 去年營收) / 去年營收 × 100%",
        "ideal_min": 10,
        "ideal_max": None,
        "unit": "%",
        "category": "成長性",
        "interpretation": "正值代表公司業務成長，> 10% 為高成長。"
    },
    "eps_growth": {
        "name": "EPS成長率",
        "full_name": "每股盈餘年增率",
        "description": "今年EPS相較去年的成長幅度",
        "formula": "(今年EPS - 去年EPS) / 去年EPS × 100%",
        "ideal_min": 15,
        "ideal_max": None,
        "unit": "%",
        "category": "成長性",
        "interpretation": "正值代表獲利成長，> 15% 代表高成長潛力。"
    },
    "dividend_years": {
        "name": "配息年數",
        "full_name": "連續配息年數",
        "description": "公司連續發放現金股利的年數",
        "formula": "統計連續配息年份",
        "ideal_min": 5,
        "ideal_max": None,
        "unit": "年",
        "category": "成長性",
        "interpretation": "越長越好，代表公司經營穩定，股利政策一致。> 5 年為理想。"
    },
    
    # 財務安全指標
    "debt_ratio": {
        "name": "負債率",
        "full_name": "負債比率",
        "description": "公司總負債佔總資產的比例",
        "formula": "總負債 / 總資產 × 100%",
        "ideal_min": None,
        "ideal_max": 50,
        "unit": "%",
        "category": "財務安全",
        "interpretation": "越低越好，高負債率代表財務風險較高。< 50% 為理想。"
    },
    "current_ratio": {
        "name": "流動比率",
        "full_name": "流動比率",
        "description": "短期償債能力指標",
        "formula": "流動資產 / 流動負債 × 100%",
        "ideal_min": 150,
        "ideal_max": None,
        "unit": "%",
        "category": "財務安全",
        "interpretation": "越高越好，> 150% 代表短期償債能力佳。"
    },
    "quick_ratio": {
        "name": "速動比率",
        "full_name": "速動比率",
        "description": "更嚴格的短期償債能力指標（排除存貨）",
        "formula": "(流動資產 - 存貨) / 流動負債 × 100%",
        "ideal_min": 100,
        "ideal_max": None,
        "unit": "%",
        "category": "財務安全",
        "interpretation": "越高越好，> 100% 代表即使不賣存貨也能償還短期債務。"
    }
}

# 評分權重設定
SCORING_WEIGHTS = {
    "roe": 0.40,       # 40%
    "pe": 0.30,        # 30%
    "pb": 0.15,        # 15%
    "debt_ratio": 0.15 # 15%
}

# 策略定義
STRATEGIES = {
    "growth": {
        "name": "🚀 成長股",
        "description": "追求高成長潛力的股票",
        "conditions": {
            "roe": {"min": 15},
            "eps_growth": {"min": 15},
            "revenue_growth": {"min": 10}
        }
    },
    "value": {
        "name": "💎 價值股",
        "description": "尋找被低估的優質股票",
        "conditions": {
            "pe": {"max": 15},
            "pb": {"max": 2},
            "roe": {"min": 10},
            "dividend_yield": {"min": 3}
        }
    },
    "dividend": {
        "name": "💰 高股息",
        "description": "穩定配息的現金流股票",
        "conditions": {
            "dividend_yield": {"min": 5},
            "dividend_years": {"min": 5},
            "debt_ratio": {"max": 60}
        }
    },
    "quality": {
        "name": "⭐ 優質股",
        "description": "財務穩健的績優股",
        "conditions": {
            "roe": {"min": 15},
            "pe": {"min": 10, "max": 20},
            "debt_ratio": {"max": 40}
        }
    }
}

# 產業類別
INDUSTRIES = [
    "全部",
    "半導體",
    "電子零組件",
    "電腦及週邊設備",
    "光電",
    "通信網路",
    "電子通路",
    "資訊服務",
    "其他電子",
    "金融保險",
    "建材營造",
    "航運",
    "觀光餐旅",
    "貿易百貨",
    "食品",
    "塑膠",
    "紡織纖維",
    "電機機械",
    "化學",
    "生技醫療",
    "油電燃氣",
    "汽車",
    "鋼鐵",
    "橡膠",
    "造紙",
    "水泥",
    "玻璃陶瓷",
    "其他"
]

# 資產類型
ASSET_TYPES = {
    "all": "全部",
    "stock": "僅股票",
    "etf": "僅 ETF"
}

# 資料庫設定
DATABASE_PATH = "data/twstock.db"

# 快取設定（秒）
CACHE_TTL = {
    "stock_list": 86400,      # 24 小時
    "financial_data": 86400,  # 24 小時
    "price_data": 300         # 5 分鐘
}
