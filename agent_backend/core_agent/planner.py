import json
from .llm_adapter import call_llm

PLAN_PROMPT = """
你是一个顶级的 AI 任务拆解规划专家。
当前用户的目标是：{goal}

请你输出一个严格的 JSON 格式的执行计划，包含具体的步骤列表。
注意：不要执行任何实际操作，只能输出一段 JSON 数据。

输出示例（请严格遵守 JSON 格式）：
```json
{{
    "plan": [
        "第一步：调用基本面工具查询PE、ROE等估值数据",
        "第二步：调用技术面工具查询均线、MACD等趋势数据",
        "第三步：综合两方面数据得出0-100分的交易打分并撰写报告"
    ]
}}
```
"""

def generate_plan(goal: str, model: str = "gemini-3.1-flash-lite", api_key: str = None, base_url: str = None) -> list:
    """调用大模型生成任务计划（纯文本输出 JSON）"""
    messages = [{"role": "user", "content": PLAN_PROMPT.format(goal=goal)}]
    
    try:
        response = call_llm(messages, model=model, api_key=api_key, base_url=base_url)
        
        if response.error:
            print(f"❌ [Planner] API 报错: {response.error}")
            return ["按默认流程直接执行任务"]
            
        text = response.text.strip()
        
        # 清理可能存在的 markdown 标记
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        return data.get("plan", ["按默认流程直接执行任务"])
        
    except Exception as e:
        print(f"❌ [Planner] 解析计划失败: {e}")
        return ["按默认流程直接执行任务"]
