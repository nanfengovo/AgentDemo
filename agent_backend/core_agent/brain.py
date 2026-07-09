import requests
import json
import datetime
from .tool_schema import tools_declaration
from .tool_router import dispatch_tool
from memory.persistent import save_history
from core_agent.agent_state import AgentState
from .planner import generate_plan
from .reflector import check_quality

from .config import get_model_url

def run_agent(user_message:str, session_id:str="default_user", model:str="gemini-3.1-flash-lite", images:list=None) -> str:
    """
    Agent 的核心大脑：运行完整的ReAct (思考 - 调用 - 观察) 循环
    """

    state = AgentState(session_id, user_message)

    print(f"\n [Agent中枢] 收到新任务：{user_message}")
    print(f" [Planner] 正在拆解任务，生成执行计划...")
    state.plan = generate_plan(user_message, model)
    plan_text = "\n".join([f" - {step}" for step in state.plan])
    print(f" [Planner] 计划生成完毕:\n{plan_text}\n\n开始深度思考...")

    # 1,记忆初始化：把用户说的话用标准的JSON存入列表
    user_parts = [{"text": user_message}]
    if images:
        for img in images:
            if img.startswith("data:"):
                header, base64_data = img.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
                user_parts.append({
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_data
                    }
                })
    state.history_messages.append({"role":"user","parts": user_parts})

    print(f"\n [Agent大脑] 收到新任务：{user_message}\n开始深度思考...")

    # 开启带有安全阀的状态机循环
    while state.iteration_count < state.max_iterations:
        state.iteration_count += 1
        state.status = "thinking"
        
        # 获取当前真实的系统时间
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日")
        
        # 组装发给大模型的数据：记忆+工具说明
        system_rules = f"""你是一个冷酷、理性的顶级华尔街量化分析师。
系统当前真实时间是：{current_time}。
你的执行计划是：
{plan_text}

规则：
1. 分析股票时，必须主动综合调用【基本面因子】和【技术面因子】两个工具。
2. 不管报告写得多复杂，最后必须强制输出一个 0-100 的【综合交易打分】。
3. 绝不允许使用模棱两可的套话，必须给出明确方向。"""

        payload = {
            "system_instruction": {
                "parts": [{"text": system_rules}]
            },
            "contents": state.history_messages,
            "tools":[tools_declaration]
        }

        # 发送网络请求给Gemini
        url = get_model_url(model)
        response = requests.post(url, json=payload)
        res_data = response.json()

        # 架构师防坑设计：先检查大模型 API 是否报错了
        if "error" in res_data:
            print(f"\n❌ [大模型 API 报错]: {res_data['error']}")
            return f"大模型接口发生错误，请查看终端日志。"

        # 提取AI回复内容
        ai_message = res_data["candidates"][0]["content"]
        ai_part = ai_message["parts"][0]

        # 对话记录加入记忆列表
        state.history_messages.append(ai_message)

        # 判断AI的意图
        if "functionCall" in ai_part:
            func_name = ai_part["functionCall"]["name"]
            func_args = ai_part["functionCall"].get("args",{})

            # 调度真正执行的物理工具
            state.status = "executing"
            tool_result = dispatch_tool(func_name,func_args)

            print(f"[工具执行结果] {tool_result}")

             # 物理操作完成后，把结果包装成规定的 JSON 格式，塞回记忆列表中
            state.history_messages.append({
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
            # 分支 B：AI 决定输出普通文本（它认为草稿写好了）
            state.status = "reflecting"
            draft_answer = ai_part.get("text", "")
            
            print(f"\n [Reflector] 正在对报告草稿进行严格的质量自检...")
            reflect_result = check_quality(draft_answer, state.goal, model)
            
            if reflect_result.upper().startswith("PASS"):
                print(f" [Reflector] 质量自检通过！(PASS)")
                state.status = "done"
                state.final_answer = draft_answer
                save_history(session_id, state.history_messages)
                return state.final_answer
            else:
                print(f" [Reflector] ❌ 质量不达标，报告被打回重写！打回原因：\n{reflect_result}")
                # 把打回原因强行注入大模型记忆，强迫它在下一轮循环中修改
                state.history_messages.append({
                    "role": "user",
                    "parts": [{"text": f"你的报告被质检员打回！质检反馈如下：\n{reflect_result}\n请严格根据反馈重新修改并生成终版报告！"}]
                })
                # 注意：这里不 return，让 while 循环继续跑下一轮！

    # 触发了死循环安全阀
    save_history(session_id, state.history_messages)
    return f"系统保护：Agent 已达到最大思考次数 ({state.max_iterations})，已被强制终止。"

def run_agent_stream(user_message:str, session_id:str="default_user", model:str="gemini-3.1-flash-lite", images:list=None):
    """
    流式输出版本的 Agent 大脑
    """
    state = AgentState(session_id, user_message)

    yield f"data: [Agent中枢] 收到新任务：{user_message}\n\n"
    yield f"data: [Planner] 正在拆解任务，生成执行计划...\n\n"
    state.plan = generate_plan(user_message, model)
    plan_text = "\n".join([f" - {step}" for step in state.plan])
    safe_plan = plan_text.replace('\n', '\\n')
    yield f"data: [Planner] 计划生成完毕:\\n{safe_plan}\n\n"

    user_parts = [{"text": user_message}]
    if images:
        for img in images:
            if img.startswith("data:"):
                header, base64_data = img.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
                user_parts.append({
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_data
                    }
                })
    state.history_messages.append({"role":"user","parts": user_parts})

    while state.iteration_count < state.max_iterations:
        state.iteration_count += 1
        state.status = "thinking"
        
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日")
        system_rules = f"""你是一个冷酷、理性的顶级华尔街量化分析师。
系统当前真实时间是：{current_time}。
你的执行计划是：
{plan_text}

规则：
1. 分析股票时，必须主动综合调用【基本面因子】和【技术面因子】两个工具。
2. 不管报告写得多复杂，最后必须强制输出一个 0-100 的【综合交易打分】。
3. 绝不允许使用模棱两可的套话，必须给出明确方向。"""

        payload = {
            "system_instruction": {"parts": [{"text": system_rules}]},
            "contents": state.history_messages,
            "tools": [tools_declaration]
        }

        yield f"data: [Agent大脑] 🧠 正在深入思考...\n\n"
        url = get_model_url(model)
        response = requests.post(url, json=payload)
        res_data = response.json()

        if "error" in res_data:
            yield f"data: [系统报错] 大模型接口异常：{res_data['error']}\n\n"
            return

        ai_message = res_data["candidates"][0]["content"]
        ai_part = ai_message["parts"][0]
        state.history_messages.append(ai_message)

        if "functionCall" in ai_part:
            func_name = ai_part["functionCall"]["name"]
            func_args = ai_part["functionCall"].get("args",{})

            yield f"data: [调度中心] 🔧 正在物理机执行工具：{func_name}\n\n"
            state.status = "executing"
            tool_result = dispatch_tool(func_name, func_args)

            yield f"data: [调度中心] ✅ 工具执行完毕\n\n"
            state.history_messages.append({
                "role": "function",
                "parts": [{"functionResponse": {"name": func_name, "response": {"result": tool_result}}}]
            })
            
        else:
            state.status = "reflecting"
            draft_answer = ai_part.get("text", "")
            
            yield f"data: [Reflector] 🧐 正在对报告草稿进行严格的质量自检...\n\n"
            reflect_result = check_quality(draft_answer, state.goal, model)
            
            if reflect_result.upper().startswith("PASS"):
                yield f"data: [Reflector] 🌟 质量自检通过！\n\n"
                state.status = "done"
                state.final_answer = draft_answer
                save_history(session_id, state.history_messages)
                
                # 最终报告输出：分为两个 chunk，第一个触发前端状态机切换，第二个传输安全转义的内容
                safe_final = state.final_answer.replace('\n', '\\n')
                yield f"data: [最终报告]\n\n"
                yield f"data: {safe_final}\n\n"
                return
            else:
                safe_reflect = reflect_result.replace('\n', '\\n')
                yield f"data: [Reflector] ❌ 质量不达标，已被打回重写！原因：\\n{safe_reflect}\n\n"
                state.history_messages.append({
                    "role": "user",
                    "parts": [{"text": f"你的报告被质检员打回！质检反馈如下：\n{reflect_result}\n请重新修改生成终版报告！"}]
                })

    save_history(session_id, state.history_messages)
    yield f"data: [系统保护] Agent 已达到最大思考次数 ({state.max_iterations})，已被强制终止。\n\n"
