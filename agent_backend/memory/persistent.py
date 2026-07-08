import sqlite3
import json
import os

# 把数据库文件固定存放在 memory 文件夹下
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_memory.db")

def _get_connection():
    """获取数据库连接并确保表结构存在"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            session_id TEXT PRIMARY KEY,
            history TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

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
    # INSERT OR REPLACE：如果 session_id 存在就覆盖更新，不存在就插入新记录
    conn.execute(
        """INSERT OR REPLACE INTO conversations (session_id, history, updated_at) 
           VALUES (?, ?, CURRENT_TIMESTAMP)""",
        (session_id, json.dumps(new_history, ensure_ascii=False))
    )
    conn.commit()
    conn.close()
