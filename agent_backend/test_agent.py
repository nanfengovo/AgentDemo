import requests
import json
import sys

def test_streaming_agent():
    print("🚀 正在连接 QuantTrading Agent 核心系统...")
    
    payload = {
        # 我们故意加上“保存文件”的指令，测试它的一条龙服务
        "message": "帮我深度分析一下特斯拉(TSLA)的基本面和技术面，然后严格给我一个能不能买的打分和交易建议，并保存报告为 tsla_report.txt",
        "session_id": "test_boss_001"
    }
    
    try:
        # 注意：这里请求的是我们刚刚新增的流式接口 /chat/stream
        response = requests.post(
            "http://127.0.0.1:8000/chat/stream", 
            json=payload, 
            stream=True
        )
        
        print("\n" + "="*50)
        
        # 逐行读取 SSE (Server-Sent Events) 数据流
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    # 截取 'data: ' 后面的真实内容并实时打印，实现打字机效果
                    text = decoded_line[6:]
                    # 如果遇到 \n 就换行，否则使用 end="" 实现平滑输出
                    print(text.replace('\\n', '\n'))
                    sys.stdout.flush() # 强制刷新控制台，打字机效果更流畅
                    
        print("\n" + "="*50)
        print("✅ 测试执行完毕。你可以去检查本地是否多了一个 tsla_report.txt 文件！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！请检查 FastAPI 服务器是否已经启动。")

if __name__ == "__main__":
    test_streaming_agent()
