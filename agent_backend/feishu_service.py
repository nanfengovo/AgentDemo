import os
import requests
import json

def get_tenant_access_token() -> str:
    """获取飞书应用级 Access Token"""
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        return ""
        
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    try:
        res = requests.post(url, json=payload)
        data = res.json()
        if data.get("code") == 0:
            return data.get("tenant_access_token")
        else:
            print(f"获取飞书 Token 失败: {data}")
            return ""
    except Exception as e:
        print(f"请求飞书 Token 发生异常: {e}")
        return ""

def reply_to_feishu_user(message_id: str, content: str):
    """
    通过 message_id 直接回复用户的消息
    """
    token = get_tenant_access_token()
    if not token:
        print("无有效飞书 Token，无法回复。")
        return
        
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    payload = {
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        print(f"飞书回复结果: {res.json()}")
    except Exception as e:
        print(f"请求飞书 API 回复消息异常: {e}")

def send_feishu_webhook(content: str) -> str:
    """
    通过 Webhook 向飞书群组或自定义机器人发送消息
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return "失败：未配置 FEISHU_WEBHOOK_URL 环境变量"
        
    payload = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }
    
    try:
        res = requests.post(webhook_url, json=payload)
        data = res.json()
        if data.get("code") == 0 or data.get("StatusCode") == 0:
            return "飞书消息推送成功"
        else:
            return f"飞书消息推送失败: {data}"
    except Exception as e:
        return f"请求飞书 Webhook 异常: {str(e)}"

def reply_to_feishu_card(message_id: str, markdown_content: str, title: str = "📊 QuantTrading Agent 报告"):
    """
    发送富文本 (Message Card) 给飞书，支持 Markdown 渲染
    """
    token = get_tenant_access_token()
    if not token:
        print("无有效飞书 Token，无法回复卡片。")
        return
        
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 构造飞书卡片 JSON
    card_dict = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "template": "blue",
            "title": {
                "content": title,
                "tag": "plain_text"
            }
        },
        "elements": [
            {
                "tag": "markdown",
                "content": markdown_content
            }
        ]
    }
    
    payload = {
        "msg_type": "interactive",
        "content": json.dumps(card_dict)
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()
        if data.get("code") != 0:
            print(f"飞书卡片回复失败: {data}")
    except Exception as e:
        print(f"请求飞书 API 回复卡片异常: {e}")
