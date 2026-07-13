import sqlite3
import json
import os
import uuid

# 把数据库文件固定存放在 memory 文件夹下
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_memory.db")

def _get_connection():
    """获取数据库连接并确保表结构存在"""
    conn = sqlite3.connect(DB_PATH)
    
    # 历史对话记录表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            session_id TEXT PRIMARY KEY,
            history TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 文件夹表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id TEXT PRIMARY KEY,
            name TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 为老版本数据库尝试添加新列 (标题和文件夹外键)
    try:
        conn.execute("ALTER TABLE conversations ADD COLUMN folder_id TEXT")
    except sqlite3.OperationalError:
        pass # 列已存在
    try:
        conn.execute("ALTER TABLE conversations ADD COLUMN title TEXT")
    except sqlite3.OperationalError:
        pass # 列已存在

    conn.commit()
    return conn

def get_folders() -> list:
    """获取所有文件夹"""
    conn = _get_connection()
    rows = conn.execute("SELECT id, name FROM folders ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1]} for row in rows]

def create_folder(name: str) -> str:
    """新建文件夹，返回文件夹 ID"""
    conn = _get_connection()
    folder_id = "folder_" + str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO folders (id, name, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (folder_id, name)
    )
    conn.commit()
    conn.close()
    return folder_id

def get_sessions() -> list:
    """获取所有历史会话列表"""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT session_id, title, folder_id, updated_at FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [{
        "session_id": row[0], 
        "title": row[1] or ("新会话 " + row[0][-4:]),
        "folder_id": row[2],
        "updated_at": row[3]
    } for row in rows]

def update_session_folder(session_id: str, folder_id: str):
    """将会话移动到文件夹"""
    conn = _get_connection()
    conn.execute("UPDATE conversations SET folder_id = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (folder_id, session_id))
    conn.commit()
    conn.close()

def update_session_title(session_id: str, title: str):
    """更新会话标题"""
    conn = _get_connection()
    conn.execute("UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (title, session_id))
    conn.commit()
    conn.close()

def get_history(session_id: str) -> list:
    """从 SQLite 数据库中取出历史记忆"""
    conn = _get_connection()
    row = conn.execute(
        "SELECT history FROM conversations WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()
    
    if row and row[0]:
        # 从 JSON 字符串反序列化为 Python list
        return json.loads(row[0])  
    return []

def save_history(session_id: str, new_history: list):
    """将最新记忆序列化后持久化到 SQLite 数据库"""
    conn = _get_connection()
    # 先检查是否存在
    exists = conn.execute("SELECT 1 FROM conversations WHERE session_id = ?", (session_id,)).fetchone()
    
    # 提取标题
    title = "新会话"
    if new_history and len(new_history) > 0:
        first_msg = new_history[0].get("content", "")
        if isinstance(first_msg, list):
            # 处理多模态数组情况
            text_parts = [c["text"] for c in first_msg if isinstance(c, dict) and c.get("type") == "text"]
            if text_parts:
                first_msg = text_parts[0]
            else:
                first_msg = "图片分析会话"
                
        if isinstance(first_msg, str) and first_msg.strip():
            title = first_msg.strip()
            if len(title) > 15:
                title = title[:15] + "..."
                
    if exists:
        conn.execute(
            """UPDATE conversations SET history = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?""",
            (json.dumps(new_history, ensure_ascii=False), session_id)
        )
        # 不覆盖老标题，除非你想每次都更新
    else:
        conn.execute(
            """INSERT INTO conversations (session_id, history, title, updated_at) 
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            (session_id, json.dumps(new_history, ensure_ascii=False), title)
        )
    conn.commit()
    conn.close()
