"""
台股智選系統 - 環境變數驗證模組
Environment Variables Validation Module

在應用程式啟動時驗證必要的環境變數
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def validate_env_vars(verbose: bool = True) -> dict:
    """驗證環境變數設定
    
    Args:
        verbose: 是否顯示詳細訊息
        
    Returns:
        dict: 包含驗證結果的字典
            - is_valid: bool - 必要變數是否都已設定
            - finmind_token: bool - FinMind Token 是否有效
            - openai_key: bool - OpenAI Key 是否有效
            - warnings: list - 警告訊息列表
            - errors: list - 錯誤訊息列表
    """
    # 載入 .env 檔案
    load_dotenv()
    
    result = {
        'is_valid': True,
        'finmind_token': False,
        'openai_key': False,
        'warnings': [],
        'errors': []
    }
    
    # 檢查 .env 檔案是否存在
    env_file = Path(__file__).parent.parent / '.env'
    if not env_file.exists():
        result['warnings'].append(
            "⚠️ 未找到 .env 檔案，請複製 .env.example 並填入 API 金鑰：\n"
            "   cp .env.example .env"
        )
    
    # 檢查 FinMind Token（必要）
    finmind_token = os.getenv('FINMIND_TOKEN', '')
    if not finmind_token or finmind_token == 'your_token_here' or finmind_token == 'your_finmind_token_here':
        result['is_valid'] = False
        result['errors'].append(
            "❌ FINMIND_TOKEN 未設定或為預設值\n"
            "   請到 https://finmindtrade.com/ 註冊帳號取得 Token"
        )
    elif len(finmind_token) < 20:
        result['warnings'].append(
            "⚠️ FINMIND_TOKEN 長度過短，可能不正確"
        )
        result['finmind_token'] = True
    else:
        result['finmind_token'] = True
    
    # 檢查 OpenAI API Key（可選）
    openai_key = os.getenv('OPENAI_API_KEY', '')
    if not openai_key or openai_key == 'your_openai_key_here':
        result['warnings'].append(
            "ℹ️ OPENAI_API_KEY 未設定，AI 選股將使用規則式解析（功能正常）"
        )
    elif not openai_key.startswith('sk-'):
        result['warnings'].append(
            "⚠️ OPENAI_API_KEY 格式可能不正確（應以 sk- 開頭）"
        )
        result['openai_key'] = True
    else:
        result['openai_key'] = True
    
    # 輸出結果
    if verbose:
        print("=" * 50)
        print("🔐 環境變數驗證")
        print("=" * 50)
        
        # 顯示狀態
        finmind_status = "✅ 已設定" if result['finmind_token'] else "❌ 未設定"
        openai_status = "✅ 已設定" if result['openai_key'] else "ℹ️ 未設定（可選）"
        
        print(f"FINMIND_TOKEN: {finmind_status}")
        print(f"OPENAI_API_KEY: {openai_status}")
        
        # 顯示錯誤
        for error in result['errors']:
            print(f"\n{error}")
        
        # 顯示警告
        for warning in result['warnings']:
            print(f"\n{warning}")
        
        print("=" * 50)
    
    return result


def require_finmind_token() -> str:
    """取得 FinMind Token，若未設定則報錯
    
    Returns:
        str: FinMind API Token
        
    Raises:
        ValueError: 當 Token 未設定時
    """
    load_dotenv()
    token = os.getenv('FINMIND_TOKEN', '')
    
    if not token or token in ['your_token_here', 'your_finmind_token_here']:
        raise ValueError(
            "FINMIND_TOKEN 未設定！\n"
            "請在 .env 檔案中設定您的 FinMind API Token：\n"
            "1. cp .env.example .env\n"
            "2. 編輯 .env 檔案填入 Token"
        )
    
    return token


# 如果直接執行此檔案，執行驗證
if __name__ == "__main__":
    result = validate_env_vars(verbose=True)
    
    if not result['is_valid']:
        print("\n❌ 環境變數驗證失敗，請修正上述問題後再啟動應用程式")
        sys.exit(1)
    else:
        print("\n✅ 環境變數驗證通過")
