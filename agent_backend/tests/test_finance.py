import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.finance_tools import get_stock_price

def test_get_apple_stock():
    result = get_stock_price("AAPL")
    print(f"\n苹果测试结果：{result}")
    assert "AAPL" in result
    assert "未知" not in result

def test_get_tencent_stock():
    result = get_stock_price("0700.HK")
    print(f"\n腾讯测试结果: {result}")
    assert "HKD" in result