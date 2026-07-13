import json
import datetime
from .tool_schema import tools_declaration
from .tool_router import dispatch_tool
from memory.persistent import save_history
from core_agent.agent_state import AgentState
from .planner import generate_plan
from .reflector import check_quality

from .llm_adapter import call_llm

def run_agent(user_message:str, session_id:str="default_user", model:str="gemini-3.1-flash-lite", images:list=None, api_key:str=None, base_url:str=None, enable_finance:bool=True, enable_search:bool=False) -> str:
    """
    Agent 的核心大脑：运行完整的ReAct (思考 - 调用 - 观察) 循环
    """

    state = AgentState(session_id, user_message)

    print(f"\n [Agent中枢] 收到新任务：{user_message}")
    if enable_finance:
        print(f" [Planner] 正在拆解任务，生成执行计划...")
        state.plan = generate_plan(user_message, model, api_key, base_url)
        plan_text = "\n".join([f" - {step}" for step in state.plan])
        print(f" [Planner] 计划生成完毕:\n{plan_text}\n\n开始深度思考...")
    else:
        state.plan = ["直接回答用户问题"]
        plan_text = "直接回答用户的问题"
        print(f" [Planner] 开始深度思考...")

    # 1,记忆初始化：使用统一的 OpenAI 标准格式
    user_content = [{"type": "text", "text": user_message}]
    if images:
        for img in images:
            user_content.append({"type": "image_url", "image_url": {"url": img}})
    state.history_messages.append({"role":"user", "content": user_content})

    print(f"\n [Agent大脑] 收到新任务：{user_message}\n开始深度思考...")

    # 开启带有安全阀的状态机循环
    while state.iteration_count < state.max_iterations:
        state.iteration_count += 1
        state.status = "thinking"
        
        # 获取当前真实的系统时间
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日")
        
        # 组装发给大模型的数据
        system_rules = f"""你是一个冷酷、理性的顶级华尔街量化分析师。
系统当前真实时间是：{current_time}。
你的执行计划是：
{plan_text}

规则：
1. 分析股票时，必须主动综合调用【基本面因子】和【技术面因子】两个工具。
2. 不管报告写得多复杂，最后必须强制输出一个 0-100 的【综合交易打分】。
3. 绝不允许使用模棱两可的套话，必须给出明确方向。"""

        # 通过统一适配器调用 LLM
        response = call_llm(
            messages=state.history_messages,
            system_prompt=system_rules,
            tools=tools_declaration,
            model=model,
            api_key=api_key,
            base_url=base_url
        )

        # 架构师防坑设计：先检查大模型 API 是否报错了
        if response.error:
            print(f"\n❌ [大模型 API 报错]: {response.error}")
            return f"大模型接口发生错误，请查看终端日志。"

        # 判断AI的意图
        if response.tool_calls:
            state.history_messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": response.tool_calls
            })
            
            # 调度真正执行的物理工具
            tc = response.tool_calls[0]
            func_name = tc["function"]["name"]
            func_args_str = tc["function"].get("arguments", "{}")
            try:
                func_args = json.loads(func_args_str)
            except:
                func_args = {}

            state.status = "executing"
            tool_result = dispatch_tool(func_name, func_args)
            print(f"[工具执行结果] {tool_result}")

             # 物理操作完成后，把结果包装塞回记忆列表中
            state.history_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": func_name,
                "content": json.dumps({"result": tool_result})
            })
            
        else:
            # 分支 B：AI 决定输出普通文本（它认为草稿写好了）
            state.status = "reflecting"
            draft_answer = response.text
            state.history_messages.append({
                "role": "assistant",
                "content": draft_answer
            })
            
            if enable_finance:
                print(f"\n [Reflector] 正在对报告草稿进行严格的质量自检...")
                reflect_result = check_quality(draft_answer, state.goal, model, api_key, base_url)
            else:
                reflect_result = "PASS"
            
            if reflect_result.upper().startswith("PASS"):
                if enable_finance:
                    print(f" [Reflector] 质量自检通过！(PASS)")
                state.status = "done"
                state.final_answer = draft_answer
                save_history(session_id, state.history_messages)
                return state.final_answer
            else:
                print(f" [Reflector] ❌ 质量不达标，报告被打回重写！打回原因：\n{reflect_result}")
                state.history_messages.append({
                    "role": "user",
                    "content": f"你的报告被质检员打回！质检反馈如下：\n{reflect_result}\n请严格根据反馈重新修改并生成终版报告！"
                })

    # 触发了死循环安全阀
    save_history(session_id, state.history_messages)
    return f"系统保护：Agent 已达到最大思考次数 ({state.max_iterations})，已被强制终止。"

def run_agent_stream(user_message:str, session_id:str="default_user", model:str="gemini-3.1-flash-lite", images:list=None, api_key:str=None, base_url:str=None, enable_finance:bool=True, enable_search:bool=False):
    """
    流式输出版本的 Agent 大脑
    """
    state = AgentState(session_id, user_message)

    # 动态组装工具
    active_tools = {"functionDeclarations": []}
    if enable_finance:
        active_tools["functionDeclarations"].extend(tools_declaration.get("functionDeclarations", []))
    
    # 记录使用的工具名字
    used_tools_set = set()

    yield f"data: [Agent中枢] 收到新任务：{user_message}\n\n"
    yield f"data: [Agent中枢] 收到新任务：{user_message}\n\n"
    
    if enable_finance:
        yield f"data: [Planner] 正在拆解任务，生成执行计划...\n\n"
        state.plan = generate_plan(user_message, model, api_key, base_url)
        plan_text = "\n".join([f" - {step}" for step in state.plan])
        safe_plan = plan_text.replace('\n', '\\n')
        yield f"data: [Planner] 计划生成完毕:\\n{safe_plan}\n\n"
    else:
        state.plan = ["直接回答用户问题"]
        plan_text = "直接回答用户的问题"

    user_content = [{"type": "text", "text": user_message}]
    if images:
        for img in images:
            user_content.append({"type": "image_url", "image_url": {"url": img}})
    state.history_messages.append({"role":"user","content": user_content})

    while state.iteration_count < state.max_iterations:
        state.iteration_count += 1
        state.status = "thinking"
        
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        if enable_finance:
            system_rules = f"""你是一个冷酷、理性的顶级华尔街量化分析师。
系统当前真实时间是：{current_time}。
你的执行计划是：
{plan_text}

规则：
1. 分析股票时，必须主动综合调用【基本面因子】和【技术面因子】两个工具。
2. 不管报告写得多复杂，最后必须强制输出一个 0-100 的【综合交易打分】。
3. 绝不允许使用模棱两可的套话，必须给出明确方向。"""
        else:
            system_rules = f"""你是一个强大、全能的 AI 智能助手。
系统当前真实时间是：{current_time}。
请直接使用中文和用户进行友好、自然的对话，直接给出答案，绝对不要输出多余的思考过程标签或原始的内部推理状态。"""

        yield f"data: [Agent大脑] 🧠 正在深入思考...\n\n"
        
        # 兼容 Google Search Grounding: 目前仅支持 Gemini 系列
        call_tools = active_tools if active_tools["functionDeclarations"] else None
        
        # NOTE: 如果开启了 enable_search 并且是 gemini 原生接口，这需要特殊结构
        # 由于我们封装了统一适配器，暂时先不深入修改适配器的 tools 结构，
        # 只要这里记录 enable_search 的状态用于前端展示即可。
        
        response = call_llm(
            messages=state.history_messages,
            system_prompt=system_rules,
            tools=call_tools,
            model=model,
            api_key=api_key,
            base_url=base_url
        )

        if response.error:
            yield f"data: [系统报错] 大模型接口异常：{response.error}\n\n"
            return

        if response.tool_calls:
            state.history_messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": response.tool_calls
            })
            
            tc = response.tool_calls[0]
            func_name = tc["function"]["name"]
            func_args_str = tc["function"].get("arguments", "{}")
            try:
                func_args = json.loads(func_args_str)
            except:
                func_args = {}

            yield f"data: [调度中心] 🔧 正在物理机执行工具：{func_name}\n\n"
            used_tools_set.add(func_name)
            state.status = "executing"
            tool_result = dispatch_tool(func_name, func_args)

            yield f"data: [调度中心] ✅ 工具执行完毕\n\n"
            state.history_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": func_name,
                "content": json.dumps({"result": tool_result})
            })
            
        else:
            state.status = "reflecting"
            draft_answer = response.text
            state.history_messages.append({
                "role": "assistant",
                "content": draft_answer
            })
            
            if enable_finance:
                yield f"data: [Reflector] 🧐 正在对报告草稿进行严格的质量自检...\n\n"
                reflect_result = check_quality(draft_answer, state.goal, model, api_key, base_url)
            else:
                reflect_result = "PASS"
            
            if reflect_result.upper().startswith("PASS"):
                if enable_finance:
                    yield f"data: [Reflector] 🌟 质量自检通过！\n\n"
                state.status = "done"
                state.final_answer = draft_answer
                save_history(session_id, state.history_messages)
                
                # 最终报告输出：分为两个 chunk，第一个触发前端状态机切换，第二个传输安全转义的内容
                safe_final = state.final_answer.replace('\n', '\\n')
                yield f"data: [最终报告]\n\n"
                yield f"data: {safe_final}\n\n"
                
                # 追加 Metadata 用于前端优雅展示
                tools_str = ", ".join(list(used_tools_set)) if used_tools_set else "无"
                search_str = "启用" if enable_search else "未启用"
                metadata = f"🤖 模型: {model} | 🛠️ 工具: {tools_str} | 🌐 搜索增强: {search_str}"
                safe_metadata = metadata.replace('\n', '\\n')
                yield f"data: [METADATA]{safe_metadata}\n\n"
                
                return
            else:
                safe_reflect = reflect_result.replace('\n', '\\n')
                yield f"data: [Reflector] ❌ 质量不达标，已被打回重写！原因：\\n{safe_reflect}\n\n"
                state.history_messages.append({
                    "role": "user",
                    "content": f"你的报告被质检员打回！质检反馈如下：\n{reflect_result}\n请重新修改生成终版报告！"
                })

    save_history(session_id, state.history_messages)
    yield f"data: [系统保护] Agent 已达到最大思考次数 ({state.max_iterations})，已被强制终止。\n\n"
