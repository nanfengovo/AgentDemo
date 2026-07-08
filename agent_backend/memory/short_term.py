global_memory_store = {}

def get_history(session_id: str) -> list:
    """
    获取某一个用户的历史记忆当中对话记录，如果是新的就初始化一个空的
    """
    if session_id not in global_memory_store:
        global_memory_store[session_id] = []
    return global_memory_store[session_id]

def save_history(session_id:str, new_history: list):
    """
    任务结束后保存记忆
    """
    global_memory_store[session_id] = new_history