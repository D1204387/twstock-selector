# 台股智選系統 📈

使用 Python 開發的財務分析與選股工具

## 🎯 功能特色

### 核心功能
- **🔍 智慧搜尋**：支援股票代號和公司名稱模糊搜尋
- **🤖 AI 智慧選股**：自然語言查詢（New!）
- **🎛️ 多維篩選**：15 個財務指標自由組合篩選
- **📊 策略篩選**：4 種內建選股策略（成長股、價值股、高股息、優質股）
- **🏆 綜合排名**：自動計算 0-10 分評分，Top 20 排行榜

### 資料涵蓋
- **離線優先 (Offline-First)** 數據架構
- 包含 **120 檔** 核心精選台股標的：
   - 台灣 50 成分股
   - 中型 100 代表股
   - 熱門 ETF
- **資料真實性**：全面採用 FinMind 真實股市數據，拒絕模擬資料

### 12 個核心財務指標
| 類別 | 指標 |
|------|------|
| 獲利能力 | ROE、ROA、淨利率、毛利率、營業利潤率 |
| 估值指標 | PE、PB、EPS、股息率 |
| 財務安全 | 負債率 |
| 成長性 | 配息年數 |

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 資料準備 (首次執行)
本專案採用 **Offline-First** 架構，需先下載真實數據：
```bash
python scripts/robust_download.py
```
> 下載約需 15-20 分鐘，將自動建立 `data/cache/robust_indicators_data.csv`。

### 3. 啟動應用程式
```bash
streamlit run main.py
```

啟動後瀏覽器會自動開啟 `http://localhost:8501`

## 📁 專案結構

```
twstock-selector/
├── main.py                 # 主程式入口
├── requirements.txt        # 依賴套件
├── config.py              # 設定檔（指標定義、策略條件）
├── data/
│   └── cache/
│       └── robust_indicators_data.csv  # 核心資料快取 (Offline-First)
├── docs/
│   ├── 專案報告.md         # 完整專案報告
│   └── 介面規劃文件.md     # UI/UX 設計文件
├── src/
│   ├── finmind_api.py     # FinMind API 串接 (含手動 ROE 計算)
│   ├── data_fetcher.py    # 資料整合與快取讀取
│   ├── indicators.py      # 指標運算邏輯
│   ├── stock_analyzer.py  # 綜合評分系統
│   ├── ai_query.py        # AI 自然語言查詢
│   └── styles.py          # UI 風格定義
├── scripts/
│   └── robust_download.py # 穩健資料下載腳本
└── pages/
    ├── 1_🔍_搜尋.py        # 搜尋頁面
    ├── 2_🎛️_篩選.py        # 篩選頁面
    ├── 3_🏆_排名.py        # 排名頁面
    └── 4_🤖_AI智慧選股.py  # AI 選股頁面
```

## 📊 內建策略

| 策略 | 條件 |
|------|------|
| 🚀 成長股 | ROE > 15%, EPS成長 > 15%, 營收成長 > 10% |
| 💎 價值股 | PE < 15, PB < 2, ROE > 10%, 股息率 > 3% |
| 💰 高股息 | 股息率 > 5%, 配息年數 > 5年, 負債率 < 60% |
| ⭐ 優質股 | ROE > 15%, PE 10-20, 負債率 < 40% |

## 🔧 評分系統

綜合評分採用以下權重：

| 指標 | 權重 |
|------|------|
| ROE | 40% |
| PE | 30% |
| PB | 15% |
| 負債率 | 15% |

## 📚 技術棧

- **Python 3.9+**
- **Streamlit** - 互動式網頁與儀表板
- **Pandas** - 高效能數據清洗與向量化運算
- **Plotly** - 互動式金融圖表
- **FinMind** - 台灣股市真實財務數據 API
- **OpenAI API** - 自然語言語意理解 (Optional)

## 📄 專案文件

*   **[專案完整報告](docs/專案報告.md)**：包含完整架構、功能介紹與 Python 技術實作細節。
*   **[介面規劃文件](docs/台股智選系統_介面規劃文件.md)**：系統設計藍圖與 UI/UX 規劃。

## 📄 授權

MIT License

---

**Python 期末報告 | 2025**
