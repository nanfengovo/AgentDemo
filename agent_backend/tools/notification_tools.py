import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_service import send_feishu_webhook

def push_to_feishu(message: str) -> str:
    """
    提供给大模型调用的工具：用于将重要信息或告警主动推送到飞书群聊
    """
    print(f" [Tool: push_to_feishu] 正在推送消息到飞书...")
    return send_feishu_webhook(message)
