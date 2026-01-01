# 台股智選系統 📈

使用 Python 開發的財務分析與選股工具

![台股智選系統一頁版](docs/台股智選系統一頁版.png)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com/D1204387/twstock-selector)

## 🎯 功能特色

- **🔍 智慧搜尋**：支援股票代號和公司名稱模糊搜尋
- **🤖 AI 智慧選股**：Hybrid 雙模設計 (OpenAI API + Regex 備援)
- **🎛️ 多維篩選**：11 個財務指標自由組合篩選
- **📊 策略篩選**：4 種內建選股策略（成長潛力、價值股、高股息、優質股）
- **🏆 綜合排名**：自動計算 0-10 分評分，Top 20 排行榜

## 📈 資料涵蓋

**120 檔**核心精選台股標的：

| 類別 | 說明 |
|------|------|
| 台灣 50 成分股 | 台灣市值最大 50 家企業 |
| 中型 100 精選 | 中型股代表 50 檔 |
| ETF 10 檔 | 0050、0056、00878、00713、00919 等熱門 ETF |
| 補充熱門股 10 檔 | 2312 金寶、2388 威盛、3481 群創等 |

> 採用 **Offline-First** 架構，資料來源為 FinMind API。

## 📊 11 個核心財務指標

| 類別 | 指標 |
|------|------|
| 獲利能力 | ROE、ROA、淨利率、毛利率、營業利潤率 |
| 估值指標 | PE、PB、EPS、殖利率 |
| 財務安全 | 負債率 |
| 股息穩定 | 配息年數 |

## 🚀 快速開始

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 資料準備 (首次執行，約需 15-20 分鐘)
python scripts/robust_download.py

# 3. 啟動應用程式
streamlit run main.py
```

##  內建策略

| 策略 | 條件 |
|------|------|
| 🚀 成長股 | ROE > 20%, 淨利率 > 20%, 負債率 < 50% |
| 💎 價值股 | PE < 15, PB < 2, ROE > 10%, 殖利率 > 3% |
| 💰 高股息 | 殖利率 > 5%, 配息年數 > 5年, 負債率 < 60% |
| ⭐ 優質股 | ROE > 15%, PE 10-20, 負債率 < 40% |

## 🔧 評分系統

**一般個股**

| 指標 | 權重 |
|------|------|
| ROE | 40% |
| PE | 30% |
| PB | 15% |
| 負債率 | 15% |

**ETF**

| 指標 | 權重 |
|------|------|
| 殖利率 | 80% |
| 配息年數 | 20% |

## 📚 技術棧

Python 3.10+ / Streamlit / Pandas / Plotly / FinMind
**AI 整合**：OpenAI API (GPT-3.5) + Regex Keyword Matching (Fallback)



