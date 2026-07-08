import yfinance as yf

# 工具1:获取某一只的价格
def get_stock_price(symbol:str) -> str:
    """
    获取某一只股票的当前价格
    
    Args:
        symbol: 股票代码
    
    Returns:
         返回当前股票价格信息
    """
    ticker = yf.Ticker(symbol)
    current_price = ticker.info.get("currentPrice","未知")
    currency = ticker.info.get("currency","")
    return f"{symbol} 的当前价格为：{current_price}{currency}" 
    
# 工具2: 支持大模型传入自定义的时间范围的
def get_historical_price(symbol:str,start_date:str,end_date:str) -> str:
    """
    获取某段时间范围的价格详细信息

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        返回某段时间范围内的股票价格详细信息
    """
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(start=start_date,end=end_date)

        if history.empty:
            return f"抱歉，没有找到 {symbol} 在 {start_date} 到 {end_date} 期间的数据。请检查股票代码或日期是否正确。"

        return f"{symbol} 历史行情（{start_date}到{end_date}）:\n {str(history)}"
    except Exception as e:
        return f"获取 {symbol} 历史行情失败：{e}" 

# 工具3:获取基本面多因子数据
def get_fundamental_factors(symbol:str) -> str:
    """
    获取股票的核心基本面因子数据，供大模型进行综合分析

    Args:
        symbol: 股票代码

    Returns:
        返回包含估值、盈利能力、成长性、分析师预期等多维度因子的结构化文本
    """

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # --- 估值类因子 ---
        # PE（市盈率）：股价+每股收益，越低可能越便宜
        # PB（市净率）：股价+每股净资产
        pe = info.get("trailingPE","暂无")
        pb = info.get("priceToBook", "暂无")
        
        # --- 盈利能力类因子 ---
        # ROE(净资产收益率)：衡量公司用股东的钱赚钱的效率
        # 利润率：每赚100块收入，能留下多少净利润
        roe = info.get("returnOnEquity", "暂无")
        profit_margin = info.get("profitMargins", "暂无")
        
        # --- 成长性因子 ---
        # 营收增速：公司收入是在增长还是萎缩
        # 利润增速：公司利润是在增长还是萎缩
        revenue_growth = info.get("revenueGrowth", "暂无")
        earnings_growth = info.get("earningsGrowth", "暂无")
        
        # --- 外部情绪面因子（华尔街分析师）---
        # 分析师目标价：华尔街专家觉得这只股票值多少钱
        # 分析师评级：买入/持有/卖出
        target_price = info.get("targetMeanPrice", "暂无")
        recommendation = info.get("recommendationKey", "暂无")
        
        # 最后拼成一段结构化的文本，交给大模型去"看"
        report = f"""
===== {symbol} 多因子数据报告 =====
【估值因子】
  市盈率(PE): {pe}
  市净率(PB): {pb}
【盈利能力因子】
  净资产收益率(ROE): {roe}
  净利润率: {profit_margin}
【成长性因子】
  营收增速: {revenue_growth}
  利润增速: {earnings_growth}
【分析师预期（情绪面）】
  目标价: {target_price}
  综合评级: {recommendation}
"""
        return report
    except Exception as e:
        return f"获取 {symbol} 基本面因子失败：{e}"

    
    
    


# 内部纯数学计算器：脱离真实环境，只处理纯数字列表

def _calculate_ma(prices: list, window: int) -> list:
    """计算简单移动平均线 (MA)"""
    ma = []
    for i in range(len(prices)):
        if i < window - 1:
            ma.append(None) # 数据不够时用 None 填充
        else:
            window_slice = prices[i - window + 1 : i + 1]
            ma.append(sum(window_slice) / window)
    return ma

def _calculate_ema(prices: list, window: int) -> list:
    """计算指数移动平均线 (EMA)"""
    ema = []
    if not prices: return ema
    
    k = 2 / (window + 1)
    ema.append(prices[0]) # 第一个值默认等于原价
    
    for i in range(1, len(prices)):
        current_ema = prices[i] * k + ema[-1] * (1 - k)
        ema.append(current_ema)
    return ema

def _calculate_rsi(prices: list, period: int = 14) -> list:
    """计算相对强弱指数 (RSI)"""
    rsi = [None] * len(prices)
    if len(prices) <= period:
        return rsi
        
    for i in range(period, len(prices)):
        window_slice = prices[i - period : i + 1]
        gains = 0
        losses = 0
        for j in range(1, len(window_slice)):
            change = window_slice[j] - window_slice[j - 1]
            if change > 0:
                gains += change
            else:
                losses -= change
                
        avg_gain = gains / period
        avg_loss = losses / period
        
        if avg_loss == 0:
            rsi[i] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100 - (100 / (1 + rs))
            
    return rsi

def _calculate_macd(prices: list, short_window=12, long_window=26, signal_window=9):
    """计算平滑异同移动平均线 (MACD)"""
    ema_short = _calculate_ema(prices, short_window)
    ema_long = _calculate_ema(prices, long_window)
    
    macd_line = []
    for s, l in zip(ema_short, ema_long):
        macd_line.append(s - l)
            
    signal_line = _calculate_ema(macd_line, signal_window)
    
    histogram = []
    for m, s in zip(macd_line, signal_line):
        histogram.append(m - s)
        
    return macd_line, signal_line, histogram

# 工具4: 获取技术面多因子数据
def get_technical_factors(symbol: str) -> str:
    """
    获取股票的技术面多因子数据（MA, RSI, MACD 等）
    """
    try:
        ticker = yf.Ticker(symbol)
        # 获取最近半年的日线数据足够计算常规技术指标
        history = ticker.history(period="6mo")
        if history.empty:
            return f"无法获取 {symbol} 的历史数据，计算技术因子失败。"
            
        prices = history["Close"].tolist()
        if len(prices) < 30:
            return f"{symbol} 数据量不足，无法计算有效的技术指标。"
            
        # 调用我们的纯数学计算器，取最后一个值（即最新的一天）
        ma5 = _calculate_ma(prices, 5)[-1]
        ma20 = _calculate_ma(prices, 20)[-1]
        rsi_14 = _calculate_rsi(prices, 14)[-1]
        macd_line, signal_line, hist = _calculate_macd(prices)
        
        # 组装给大模型看的报告
        report = f"""
===== {symbol} 技术面分析报告 =====
当前价格: {prices[-1]:.2f}

【趋势因子 (MA)】
  MA5 (5日均线): {ma5:.2f}
  MA20 (20日均线): {ma20:.2f}
  *规则*: 现价高于MA20通常视为多头趋势

【动能与超买超卖因子 (RSI)】
  RSI(14): {rsi_14:.2f}
  *规则*: >70通常视为超买(过热)，<30视为超卖(过冷)

【趋势动量因子 (MACD)】
  MACD 线 (快线): {macd_line[-1]:.3f}
  Signal 线 (慢线): {signal_line[-1]:.3f}
  柱状图 (Histogram): {hist[-1]:.3f}
  *规则*: MACD线在Signal线之上(柱状图为正)表示多头动能，反之为空头
"""
        return report
    except Exception as e:
        return f"获取 {symbol} 技术面因子失败：{e}"
