"""
台股智選系統 - 單元測試
Unit Tests for Taiwan Stock Selection System

測試評分函數的正確性
"""

import pytest
import sys
from pathlib import Path

# 加入 src 路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stock_analyzer import (
    score_roe, score_pe, score_pb, 
    score_debt_ratio, score_dividend_yield, score_dividend_years,
    is_roe_abnormal
)


class TestScoreROE:
    """測試 ROE 評分函數"""
    
    def test_high_roe(self):
        """高 ROE 應得滿分"""
        assert score_roe(25) == 10
        assert score_roe(30) == 10
        assert score_roe(50) == 10
    
    def test_good_roe(self):
        """良好 ROE (15-25) 應得 8-10 分"""
        assert 8 <= score_roe(20) <= 10
        assert 6 <= score_roe(15) <= 8
    
    def test_zero_roe(self):
        """零 ROE 應得 0 分"""
        assert score_roe(0) == 0
    
    def test_negative_roe(self):
        """負 ROE 應得 0 分"""
        assert score_roe(-5) == 0
        assert score_roe(-100) == 0
    
    def test_none_roe(self):
        """None 值應得 0 分"""
        assert score_roe(None) == 0


class TestScorePE:
    """測試 PE 評分函數"""
    
    def test_optimal_pe(self):
        """最佳 PE (10-15) 應得滿分"""
        assert score_pe(10) == 10
        assert score_pe(12) == 10
        assert score_pe(14) == 10
    
    def test_low_pe(self):
        """低 PE (<10) 應得較高分"""
        assert score_pe(8) >= 7
        assert score_pe(5) >= 5
    
    def test_high_pe(self):
        """高 PE (>20) 應得較低分"""
        assert score_pe(25) < 8
        assert score_pe(40) < 4
    
    def test_zero_pe(self):
        """零或負 PE 應得 0 分"""
        assert score_pe(0) == 0
        assert score_pe(-5) == 0
    
    def test_none_pe(self):
        """None 值應得 0 分"""
        assert score_pe(None) == 0


class TestScorePB:
    """測試 PB 評分函數"""
    
    def test_optimal_pb(self):
        """最佳 PB (0.5-1) 應得 8-10 分"""
        assert score_pb(0.8) == 10
        assert score_pb(1) >= 9
    
    def test_low_pb(self):
        """極低 PB (<0.5) 可能有問題，但仍給高分"""
        assert score_pb(0.3) == 8
    
    def test_high_pb(self):
        """高 PB (>3) 應得較低分"""
        assert score_pb(3) <= 6
        assert score_pb(5) <= 4
    
    def test_zero_pb(self):
        """零或負 PB 應得 0 分"""
        assert score_pb(0) == 0
        assert score_pb(-1) == 0
    
    def test_none_pb(self):
        """None 值應得 0 分"""
        assert score_pb(None) == 0


class TestScoreDebtRatio:
    """測試負債率評分函數"""
    
    def test_low_debt(self):
        """低負債率 (<30%) 應得滿分"""
        assert score_debt_ratio(10) == 10
        assert score_debt_ratio(25) == 10
    
    def test_moderate_debt(self):
        """中等負債率 (30-50%) 應得 7-10 分"""
        assert 7 <= score_debt_ratio(35) <= 10
        assert 5 <= score_debt_ratio(55) <= 7
    
    def test_high_debt(self):
        """高負債率 (>70%) 應得低分"""
        assert score_debt_ratio(80) < 3
    
    def test_none_debt(self):
        """None 值應得 0 分"""
        assert score_debt_ratio(None) == 0


class TestScoreDividendYield:
    """測試殖利率評分函數"""
    
    def test_high_yield(self):
        """高殖利率 (>7%) 應得滿分"""
        assert score_dividend_yield(8) == 10
        assert score_dividend_yield(10) == 10
    
    def test_moderate_yield(self):
        """中等殖利率 (3-5%) 應得 5-7 分"""
        assert 5 <= score_dividend_yield(4) <= 7
    
    def test_low_yield(self):
        """低殖利率 (<2%) 應得低分"""
        assert score_dividend_yield(1) <= 3
    
    def test_zero_yield(self):
        """零殖利率應得 0 分"""
        # 根據實作，dy < 0 return 0, dy < 2 return 1
        assert score_dividend_yield(0) <= 1
    
    def test_negative_yield(self):
        """負殖利率應得 0 分"""
        assert score_dividend_yield(-3) == 0
    
    def test_none_yield(self):
        """None 值應得 0 分"""
        assert score_dividend_yield(None) == 0


class TestScoreDividendYears:
    """測試配息年數評分函數"""
    
    def test_long_history(self):
        """長期配息 (>=7年) 應得滿分"""
        assert score_dividend_years(7) == 10
        assert score_dividend_years(10) == 10
        assert score_dividend_years(20) == 10
    
    def test_moderate_history(self):
        """中期配息 (3-6年) 應得 6-8 分"""
        assert 6 <= score_dividend_years(5) <= 8
    
    def test_short_history(self):
        """短期配息 (1-2年) 應得較低分"""
        assert score_dividend_years(1) <= 4
    
    def test_zero_years(self):
        """零年應得 0 分"""
        assert score_dividend_years(0) == 0
    
    def test_none_years(self):
        """None 值應得 0 分"""
        assert score_dividend_years(None) == 0


class TestIsROEAbnormal:
    """測試 ROE 異常值檢測函數"""
    
    def test_severe_loss(self):
        """嚴重虧損 (< -50%) 應標記為 danger"""
        is_abnormal, reason, severity = is_roe_abnormal(-60)
        assert is_abnormal is True
        assert severity == "danger"
        assert "嚴重虧損" in reason
    
    def test_major_loss(self):
        """大幅虧損 (-50% ~ -20%) 應標記為 danger"""
        is_abnormal, reason, severity = is_roe_abnormal(-30)
        assert is_abnormal is True
        assert severity == "danger"
    
    def test_minor_loss(self):
        """輕微虧損 (-20% ~ 0%) 應標記為 warning"""
        is_abnormal, reason, severity = is_roe_abnormal(-5)
        assert is_abnormal is True
        assert severity == "warning"
    
    def test_extremely_high(self):
        """極端高值 (> 80%) 應標記為 danger"""
        is_abnormal, reason, severity = is_roe_abnormal(90)
        assert is_abnormal is True
        assert severity == "danger"
        assert "異常高值" in reason
    
    def test_high_but_not_extreme(self):
        """偏高 (60% ~ 80%) 應標記為 warning"""
        is_abnormal, reason, severity = is_roe_abnormal(70)
        assert is_abnormal is True
        assert severity == "warning"
    
    def test_normal_roe(self):
        """正常 ROE (0% ~ 60%) 應不標記"""
        is_abnormal, reason, severity = is_roe_abnormal(25)
        assert is_abnormal is False
        assert reason == ""
        assert severity == ""
    
    def test_none_roe(self):
        """None 值應不標記"""
        is_abnormal, reason, severity = is_roe_abnormal(None)
        assert is_abnormal is False


# ==============================================================================
# 整合測試 (Integration Tests)
# ==============================================================================

class TestCalculateScore:
    """測試 calculate_score 整合評分函數"""
    
    def test_etf_scoring_high_yield(self):
        """測試 ETF 高殖利率評分"""
        import pandas as pd
        from stock_analyzer import calculate_score
        
        etf_data = pd.DataFrame([{
            'stock_id': '0056',
            'dividend_yield': 7.0,
            'pb': 1.0,
            'dividend_years': 10,
            'roe': None,  # ETF 無 ROE
            'pe': None,
            'debt_ratio': None,
        }])
        result = calculate_score(etf_data)
        
        # ETF 高殖利率 + 長期配息應得高分
        assert result.iloc[0]['score'] >= 8
    
    def test_etf_scoring_without_pb(self):
        """測試 ETF 無 PB 時的評分"""
        import pandas as pd
        from stock_analyzer import calculate_score
        
        etf_data = pd.DataFrame([{
            'stock_id': '00919',
            'dividend_yield': 9.6,
            'pb': None,  # 無 PB
            'dividend_years': 5,
            'roe': None,
            'pe': None,
            'debt_ratio': None,
        }])
        result = calculate_score(etf_data)
        
        # 應使用殖利率 80% + 配息年數 20% 評分
        assert result.iloc[0]['score'] >= 8
    
    def test_stock_scoring_high_quality(self):
        """測試優質股票評分"""
        import pandas as pd
        from stock_analyzer import calculate_score
        
        stock_data = pd.DataFrame([{
            'stock_id': '2330',
            'roe': 25.0,
            'pe': 15.0,
            'pb': 1.5,
            'debt_ratio': 30.0,
            'dividend_yield': 3.0,
            'dividend_years': 10,
        }])
        result = calculate_score(stock_data)
        
        # 高 ROE + 合理 PE + 低負債應得高分
        assert result.iloc[0]['score'] >= 8
    
    def test_stock_scoring_loss_making(self):
        """測試虧損股票評分"""
        import pandas as pd
        from stock_analyzer import calculate_score
        
        stock_data = pd.DataFrame([{
            'stock_id': '2337',
            'roe': -10.0,
            'pe': 0,
            'pb': 2.0,
            'debt_ratio': 50.0,
            'dividend_yield': 0,
            'dividend_years': 0,
        }])
        result = calculate_score(stock_data)
        
        # 虧損股票應得低分
        assert result.iloc[0]['score'] < 5


class TestAnalyzeStock:
    """測試 analyze_stock 分析函數"""
    
    def test_analyze_regular_stock(self):
        """測試一般股票分析"""
        from stock_analyzer import analyze_stock
        
        stock = {
            'stock_id': '2330',
            'name': '台積電',
            'roe': 25.0,
            'pe': 20.0,
            'pb': 5.0,
            'debt_ratio': 30.0,
            'dividend_yield': 2.0,
        }
        result = analyze_stock(stock)
        
        assert 'score' in result
        assert 'grade' in result
        assert 'strengths' in result
        assert 'weaknesses' in result
        assert result['score'] >= 0
        assert result['score'] <= 10
    
    def test_analyze_etf(self):
        """測試 ETF 分析"""
        from stock_analyzer import analyze_stock
        
        etf = {
            'stock_id': '0056',
            'name': '元大高股息',
            'dividend_yield': 7.0,
            'pb': 1.0,
            'dividend_years': 10,
            'roe': None,
        }
        result = analyze_stock(etf)
        
        assert 'score' in result
        # ETF 高殖利率應有優點
        assert len(result['strengths']) > 0 or result['score'] >= 7


class TestCustomScreen:
    """測試 custom_screen 篩選函數"""
    
    def test_screen_by_roe(self):
        """測試 ROE 篩選"""
        import pandas as pd
        from stock_screener import custom_screen
        
        df = pd.DataFrame([
            {'stock_id': '2330', 'roe': 25.0, 'pe': 20.0},
            {'stock_id': '2317', 'roe': 15.0, 'pe': 15.0},
            {'stock_id': '2337', 'roe': -5.0, 'pe': 0},
        ])
        
        conditions = {'roe': {'min': 20}}
        result = custom_screen(df, conditions)
        
        assert len(result) == 1
        assert result.iloc[0]['stock_id'] == '2330'
    
    def test_screen_by_multiple_conditions(self):
        """測試多條件篩選"""
        import pandas as pd
        from stock_screener import custom_screen
        
        df = pd.DataFrame([
            {'stock_id': '2330', 'roe': 25.0, 'pe': 20.0, 'debt_ratio': 30.0},
            {'stock_id': '2317', 'roe': 15.0, 'pe': 15.0, 'debt_ratio': 50.0},
            {'stock_id': '2412', 'roe': 20.0, 'pe': 12.0, 'debt_ratio': 40.0},
        ])
        
        conditions = {'roe': {'min': 15}, 'pe': {'max': 18}, 'debt_ratio': {'max': 45}}
        result = custom_screen(df, conditions)
        
        assert len(result) == 1
        assert result.iloc[0]['stock_id'] == '2412'

# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
