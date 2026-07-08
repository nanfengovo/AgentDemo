import requests
import json
import datetime
from .tool_schema import tools_declaration
from .tool_router import dispatch_tool
from memory.short_term import get_history,save_history

GEMINI_API_KEY = "AIzaSyAtUkzItuAZJSoOq6FeXw_6lXNl1Ucn3BI"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"

def run_agent(user_message:str,session_id:str="default_user") -> str:
    """
    Agent 的核心大脑：运行完整的ReAct (思考 - 调用 - 观察) 循环
    """

    history_messages = get_history(session_id)

    # 1,记忆初始化：把用户说的话用标准的JSON存入列表
    history_messages.append({"role":"user","parts":[{"text":user_message}]})

    print(f"\n [Agent大脑] 收到新任务：{user_message}\n开始深度思考...")

    # 开启循环
    while True:
        # 获取当前真实的系统时间
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日")
        
        # 组装发给大模型的数据：记忆+工具说明
        payload = {
            "system_instruction": {
                "parts": [{"text": f"你是一个冷酷、理性的顶级华尔街量化分析师。系统当前真实时间是：{current_time}。规则：1. 分析股票时，必须主动综合调用【基本面因子】和【技术面因子】两个工具。2. 不管报告写得多复杂，最后必须强制输出一个 0-100 的【综合交易打分】（>70强烈建议买入，<40强烈建议卖出）。3. 绝不允许使用模棱两可的套话，必须给出明确方向。"}]
            },
            "contents": history_messages,
            "tools":[tools_declaration]
        }

        # 发送网络请求给Gemini
        response = requests.post(URL,json=payload)
        res_data = response.json()

        # 架构师防坑设计：先检查大模型 API 是否报错了
        if "error" in res_data:
            print(f"\n❌ [大模型 API 报错]: {res_data['error']}")
            return f"大模型接口发生错误，请查看终端日志。"

        # 提取AI回复内容
        ai_message = res_data["candidates"][0]["content"]
        ai_part = ai_message["parts"][0]

        # 对话记录加入记忆列表
        history_messages.append(ai_message)

        # 判断AI的意图
        if "functionCall" in ai_part:
            func_name = ai_part["functionCall"]["name"]
            func_args = ai_part["functionCall"].get("args",{})

            # 调度真正执行的物理工具
            tool_result = dispatch_tool(func_name,func_args)

            print(f"[工具执行结果] {tool_result}")

             # 物理操作完成后，把结果包装成规定的 JSON 格式，塞回记忆列表中
            history_messages.append({
                "role": "function",
                "parts": [{
                    "functionResponse": {
                        "name": func_name,
                        "response": {"result": tool_result}
                    }
                }]
            })
            # 不写 return，让 while 循环继续跑！带着工具结果再次向 AI 发起请求。
            
        else:
            # 分支 B：AI 决定直接输出普通文本（说明它认为任务已经彻底完成了）
            final_text = ai_part.get("text", "")
            save_history(session_id,history_messages)
            return final_text
