"""
台股智選系統 - AI 自然語言查詢模組
Taiwan Stock Selection System - AI Natural Language Query Module

使用 OpenAI API 將口語化查詢轉換為篩選條件
"""

import os
import json
import re
from typing import Dict, Optional

# OpenAI API 設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 系統提示詞
SYSTEM_PROMPT = """你是一個台股選股助手，專門幫助用戶將口語化的股票查詢轉換為篩選條件。

可用的篩選指標：
- roe: 股東權益報酬率 (%)，越高越好，優質標準 > 15%
- roa: 資產報酬率 (%)，越高越好，優質標準 > 8%
- pe: 本益比，合理區間 10-20，越低越便宜
- pb: 股價淨值比，合理區間 1-3，越低越便宜
- dividend_yield: 殖利率 (%)，越高越好，高股息標準 > 5%
- dividend_years: 連續配息年數，越多越穩定
- debt_ratio: 負債率 (%)，越低越安全，安全標準 < 50%
- revenue_growth: 營收成長率 (%)，正值表示成長
- eps_growth: EPS成長率 (%)，正值表示成長
- net_profit_margin: 淨利率 (%)，越高越好
- current_ratio: 流動比率 (%)，>100% 較安全

你需要將用戶的查詢轉換為 JSON 格式的篩選條件。

回應格式（只回應 JSON，不要其他文字）：
{
    "filters": {
        "指標名稱": {"min": 數值} 或 {"max": 數值} 或 {"min": 數值, "max": 數值}
    },
    "strategy": "growth" | "value" | "dividend" | "quality" | null,
    "explanation": "簡短說明篩選邏輯"
}

策略對應：
- growth: 成長股（ROE>15%, EPS成長>15%, 營收成長>10%）
- value: 價值股（PE<15, PB<2, ROE>10%）
- dividend: 高股息（殖利率>5%, 配息年數>5）
- quality: 優質股（ROE>15%, PE 10-20, 負債率<40%）

範例：
用戶: "每年利息超過5%的股票"
回應: {"filters": {"dividend_yield": {"min": 5}}, "strategy": "dividend", "explanation": "篩選殖利率超過5%的高股息股票"}

用戶: "最具成長性的股票"
回應: {"filters": {"revenue_growth": {"min": 10}, "eps_growth": {"min": 15}, "roe": {"min": 15}}, "strategy": "growth", "explanation": "篩選營收和EPS都有高成長的成長股"}
"""


def parse_query_with_openai(query: str, api_key: str = None) -> Dict:
    """使用 OpenAI API 解析自然語言查詢
    
    Args:
        query: 用戶的自然語言查詢
        api_key: OpenAI API Key
    
    Returns:
        包含 filters, strategy, explanation 的字典
    """
    import requests
    
    key = api_key or OPENAI_API_KEY
    if not key:
        return {"error": "未設定 OpenAI API Key", "filters": {}, "strategy": None}
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # 解析回應
        content = result["choices"][0]["message"]["content"].strip()
        
        # 嘗試解析 JSON
        try:
            # 移除可能的 markdown 標記
            if content.startswith("```"):
                content = re.sub(r'^```json?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError:
            return {
                "filters": {},
                "strategy": None,
                "explanation": content,
                "raw_response": content
            }
            
    except requests.exceptions.RequestException as e:
        return {"error": f"API 請求失敗: {str(e)}", "filters": {}, "strategy": None}
    except Exception as e:
        return {"error": f"解析失敗: {str(e)}", "filters": {}, "strategy": None}


def parse_query_fallback(query: str) -> Dict:
    """關鍵字匹配備用方案（不需要 API）
    
    Args:
        query: 用戶的自然語言查詢
    
    Returns:
        包含 filters, strategy, explanation 的字典
    """
    filters = {}
    strategy = None
    explanation = ""
    
    query_lower = query.lower()
    
    # 股息/殖利率相關
    if any(k in query for k in ["利息", "股息", "殖利率", "配息", "存股"]):
        nums = re.findall(r'(\d+(?:\.\d+)?)\s*%?', query)
        if nums:
            filters['dividend_yield'] = {'min': float(nums[0])}
            explanation = f"篩選殖利率超過 {nums[0]}% 的股票"
        else:
            filters['dividend_yield'] = {'min': 5}
            explanation = "篩選殖利率超過 5% 的高股息股票"
        strategy = "dividend"
    
    # 成長相關
    elif any(k in query for k in ["成長", "成長性", "增長", "擴張"]):
        filters['revenue_growth'] = {'min': 10}
        filters['eps_growth'] = {'min': 15}
        filters['roe'] = {'min': 15}
        strategy = "growth"
        explanation = "篩選營收成長 > 10% 且 EPS 成長 > 15% 的成長股"
    
    # 價值/低估相關
    elif any(k in query for k in ["便宜", "低估", "價值", "撿便宜"]):
        filters['pe'] = {'max': 15}
        filters['pb'] = {'max': 2}
        filters['roe'] = {'min': 10}
        strategy = "value"
        explanation = "篩選 PE < 15、PB < 2 且 ROE > 10% 的價值股"
    
    # 安全/穩健相關
    elif any(k in query for k in ["安全", "穩健", "保守", "低風險"]):
        filters['debt_ratio'] = {'max': 40}
        filters['current_ratio'] = {'min': 150}
        filters['dividend_years'] = {'min': 5}
        strategy = "quality"
        explanation = "篩選負債率 < 40% 且連續配息 > 5 年的穩健股"
    
    # 優質/好公司
    elif any(k in query for k in ["優質", "好公司", "績優", "龍頭"]):
        filters['roe'] = {'min': 15}
        filters['pe'] = {'min': 10, 'max': 25}
        filters['debt_ratio'] = {'max': 50}
        strategy = "quality"
        explanation = "篩選 ROE > 15%、PE 合理、負債率低的優質股"
    
    # ROE 相關
    elif "roe" in query_lower or "股東權益" in query:
        nums = re.findall(r'(\d+(?:\.\d+)?)\s*%?', query)
        if nums:
            filters['roe'] = {'min': float(nums[0])}
            explanation = f"篩選 ROE 超過 {nums[0]}% 的股票"
        else:
            filters['roe'] = {'min': 15}
            explanation = "篩選 ROE 超過 15% 的股票"
    
    # PE 相關
    elif "pe" in query_lower or "本益比" in query:
        nums = re.findall(r'(\d+(?:\.\d+)?)', query)
        if nums:
            if "低" in query or "小" in query:
                filters['pe'] = {'max': float(nums[0])}
                explanation = f"篩選 PE 低於 {nums[0]} 的股票"
            else:
                filters['pe'] = {'min': float(nums[0])}
                explanation = f"篩選 PE 高於 {nums[0]} 的股票"
        else:
            filters['pe'] = {'max': 15}
            explanation = "篩選 PE 低於 15 的低估股票"
    
    # 負債相關
    elif any(k in query for k in ["負債", "財務"]):
        nums = re.findall(r'(\d+(?:\.\d+)?)\s*%?', query)
        if nums:
            filters['debt_ratio'] = {'max': float(nums[0])}
            explanation = f"篩選負債率低於 {nums[0]}% 的股票"
        else:
            filters['debt_ratio'] = {'max': 50}
            explanation = "篩選負債率低於 50% 的股票"
    
    # 預設
    else:
        filters['roe'] = {'min': 10}
        filters['pe'] = {'max': 25}
        explanation = "篩選基本條件良好的股票（ROE > 10%、PE < 25）"
    
    # 產業別識別（可與其他條件組合）
    industry = None
    if any(k in query for k in ["半導體", "晶片", "IC"]):
        industry = "半導體"
    elif any(k in query for k in ["金融", "銀行", "壽險", "保險"]):
        industry = "金融保險"
    elif any(k in query for k in ["科技", "電子", "電腦"]):
        industry = "電子"  # 通用電子類
    elif any(k in query for k in ["航運", "海運", "貨運"]):
        industry = "航運"
    elif any(k in query for k in ["生技", "醫療", "製藥"]):
        industry = "生技醫療"
    elif any(k in query for k in ["食品", "飲料"]):
        industry = "食品"
    elif any(k in query for k in ["鋼鐵", "金屬"]):
        industry = "鋼鐵"
    elif any(k in query for k in ["營建", "建設", "房地產"]):
        industry = "建材營造"
    
    if industry:
        explanation += f"（限 {industry} 產業）"
    
    return {
        "filters": filters,
        "strategy": strategy,
        "explanation": explanation,
        "industry": industry
    }


def parse_natural_query(query: str, api_key: str = None, use_ai: bool = True) -> Dict:
    """解析自然語言查詢的主函數
    
    Args:
        query: 用戶的自然語言查詢
        api_key: OpenAI API Key（可選）
        use_ai: 是否使用 AI（如果為 False 或 API 失敗，使用關鍵字匹配）
    
    Returns:
        包含 filters, strategy, explanation 的字典
    """
    if use_ai and api_key:
        result = parse_query_with_openai(query, api_key)
        if "error" not in result:
            return result
        # AI 失敗時降級到關鍵字匹配
        print(f"⚠️ AI 解析失敗，使用關鍵字匹配: {result.get('error')}")
    
    return parse_query_fallback(query)


# 預設查詢範例
EXAMPLE_QUERIES = [
    "每年配息超過5%的股票",
    "最具成長性的科技股",
    "財務穩健的金融股",
    "適合存股的標的",
    "ROE超過20%的優質公司",
    "本益比低於10的便宜股",
    "連續配息10年以上的穩定股",
]
