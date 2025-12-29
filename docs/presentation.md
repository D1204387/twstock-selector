---
marp: true
theme: default
paginate: true
backgroundColor: #1a1a2e
color: #eaeaea
style: |
  h1, h2 {
    color: #00d4ff;
  }
  h3 {
    color: #ffd700;
  }
  section {
    font-family: 'Noto Sans TC', sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
  }
  table {
    margin: 0 auto;
  }
  th {
    background: #00d4ff;
    color: #1a1a2e;
  }
  td {
    background: #2a2a4e;
    color: #ffffff;
  }
  .big-number {
    font-size: 4em;
    color: #00d4ff;
    font-weight: bold;
  }
---

<!-- _class: lead -->

# 📈 台股智選系統

**Python 期末專案報告**

M1427499 陳憶柔

2025/12

---

## 🎯 解決什麼問題？

<div style="text-align: center; margin-top: 40px;">
<span style="font-size: 3em; color: #00d4ff; font-weight: bold;">2,000+</span>

台灣上市櫃股票與 ETF
</div>

投資人面臨 **資訊過載**，難以快速找到值得投資的標的

---

## 💡 我們的解決方案

- 🔍 智慧搜尋與篩選
- 📊 11 項財務指標分析
- 🏆 0-10 分綜合評分
- 🤖 AI 自然語言選股

---

## 📈 資料涵蓋

<div style="text-align: center;">
<span style="font-size: 3em; color: #00d4ff; font-weight: bold;">120 檔</span>

精選核心標的（涵蓋台股 85% 市值）
</div>

| 類別 | 數量 |
|------|------|
| 台灣 50 成分股 | 50 檔 |
| 中型 100 精選 | 50 檔 |
| 熱門 ETF | 10 檔 |
| 補充熱門股 | 10 檔 |

---

## 🏗️ 系統架構

| 層級 | 說明 |
|------|------|
| **使用者介面** | Streamlit Web App（搜尋/篩選/排名/AI） |
| **業務邏輯** | stock_analyzer 評分、stock_screener 篩選 |
| **資料存取** | Offline-First 架構，讀取本地快取 |
| **資料來源** | FinMind API → robust_indicators_data.csv |

---

## 🔧 評分系統

<div style="display: flex; justify-content: space-around; margin-top: 20px;">
<div>

### 一般個股
| 指標 | 權重 |
|------|------|
| ROE | 40% |
| PE | 30% |
| PB | 15% |
| 負債率 | 15% |

</div>
<div>

### ETF
| 指標 | 權重 |
|------|------|
| 殖利率 | 80% |
| 配息年數 | 20% |

</div>
</div>

---

## 📊 四大內建策略

| 策略 | 核心條件 |
|------|---------|
| 🚀 成長股 | 高 ROE、高淨利率 |
| 💎 價值股 | 低 PE、低 PB |
| 💰 高股息 | 高殖利率、穩定配息 |
| ⭐ 優質股 | 財務穩健、低負債 |

---

## 🛠️ 技術應用

| 技術 | 應用 |
|------|------|
| Pandas | 資料處理 |
| Streamlit | Web UI |
| Requests | API 串接 |
| Plotly | 資料視覺化 |

---

## 🖥️ 系統展示 - 首頁

![w:900](screenshot_home.png)

---

## 🔍 搜尋功能

![w:900](screenshot_search.png)

---

## 🎛️ 策略篩選

![w:900](screenshot_filter.png)

---

## 🏆 排名分析

![w:900](screenshot_ranking.png)

---

## 🤖 AI 智慧選股

![w:900](screenshot_ai.png)

---

<!-- _class: lead -->

## 📝 結語

> 「專注於分析公司的財務體質，
> 幫助投資人找到值得長期持有的好公司。」

# 🙏 謝謝聆聽
