from memory.persistent import get_history

class AgentState:
    """Agent 的完整运行时状态机"""
    
    def __init__(self, session_id: str, user_message: str):
        self.session_id = session_id
        self.goal = user_message                 # 用户的原始目标
        self.history_messages = get_history(session_id) # 挂载持久化记忆
        self.plan = []                            # 规划步骤列表（留给 Planner 使用）
        self.current_step = 0                     # 当前执行的计划步骤
        self.status = "thinking"                  # 状态机：thinking / executing / reflecting / done
        self.final_answer = ""                    # 最终生成的答案
        self.iteration_count = 0                  # 循环计数器
        self.max_iterations = 10                  # 死循环安全阀，默认最多思考 10 个回合
