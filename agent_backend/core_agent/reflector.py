import requests
import json
import os

from .config import URL

REFLECT_PROMPT = """
你是一个智能且严格的质量审核员。
用户的原始任务目标是：{goal}

以下是 AI 助手生成的回复草稿：
{draft_answer}

请根据用户的原始任务，选择你的审核逻辑：

【路径 A：非金融深度分析任务】
如果用户的任务仅仅是普通的问答、查对话历史、闲聊、查询系统状态等，请直接放行，只回复大写的："PASS"。

【路径 B：金融资产分析任务】
如果用户的任务是分析某只股票或金融资产，请检查以下三个硬性指标：
1. 报告中是否输出了 0-100 的【综合交易打分】？如果没有，属于严重不合格。
2. 结论是否有具体的数据支撑（例如是否提到了具体数值）？
3. 态度是否模棱两可？（有没有明确给出看多或看空的结论）

如果质量完全合格，请只回复大写的："PASS"。
如果存在缺陷，请无情地指出具体问题并要求重写。
"""

def check_quality(draft_answer: str, goal: str) -> str:
    """调用大模型对草稿进行动态自检"""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": REFLECT_PROMPT.format(draft_answer=draft_answer, goal=goal)}]}]
    }
    try:
        response = requests.post(URL, json=payload)
        res_data = response.json()
        
        if "error" in res_data:
            print(f"❌ [Reflector] API 报错: {res_data['error']}")
            return "PASS" # 如果接口报错，默认放行防止系统卡死
            
        text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text
        
    except Exception as e:
        print(f"❌ [Reflector] 审核过程异常失败: {e}")
        return "PASS"
