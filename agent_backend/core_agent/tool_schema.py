tools_declaration = {
    "functionDeclarations":[
        {
            "name": "get_stock_price",
            "description": "获取指定股票的最新价格",
            "parameters":{
                "type":"OBJECT",
                "properties":{
                    "symbol":{
                        "type":"STRING",
                        "description":"股票代码。注意：美股直接写代码(如 AAPL)；港股加上.HK(如 0700.HK)；中国A股上海股票加上.SS(如 600519.SS)，深圳股票加上.SZ(如 002428.SZ)。"
                    }
                },
                "required":["symbol"]
            }
        },
        {
            "name": "get_fundamental_factors",
            "description": "获取股票的基本面多因子数据（市盈率PE、ROE、营收增速、分析师评级等），用于深度财务分析",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "symbol": {"type": "STRING", "description": "股票代码。注意：A股上海必须加.SS，深圳必须加.SZ。"}
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "get_technical_factors",
            "description": "获取股票的技术面多因子数据（MA5/20均线, RSI相对强弱, MACD趋势），用于判断短期买卖点和技术面趋势。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "symbol": {"type": "STRING", "description": "股票代码。注意：A股上海必须加.SS，深圳必须加.SZ。"}
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "write_flie",
            "description": "保存文本内容到本地电脑的文件中",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "path": {"type": "STRING", "description": "要保存的文件路径，例如 report.txt"},
                    "content": {"type": "STRING", "description": "要写入的具体文本内容"}
                },
                "required": ["path", "content"]
            }
        },
        {
            "name": "read_flie",
            "description": "读取本地电脑的文件内容",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "path": {"type": "STRING", "description": "要读取的文件路径，例如 report.txt"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "run_terminal_command",
            "description": "在计算机的终端执行 Shell/Bash 命令（例如 mkdir, mv, ls 等）。这赋予了你极大的自由度来管理电脑。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "command": {"type": "STRING", "description": "要执行的具体终端命令"}
                },
                "required": ["command"]
            }
        }

    ]
}