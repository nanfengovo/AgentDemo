# main.py
from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import json
from feishu_service import reply_to_feishu_user

from fastapi.responses import StreamingResponse

# 把我们刚刚写好的 Agent 大脑导进来
from core_agent.brain import run_agent, run_agent_stream

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

from fastapi.staticfiles import StaticFiles
import os

# 挂载静态文件目录，允许前端访问 Agent 生成的本地图表或报告图片
app.mount("/static", StaticFiles(directory=os.path.dirname(os.path.abspath(__file__))), name="static")

# 允许跨域请求（CORS），让本地的 Next.js 前端 (3000 端口) 可以毫无阻碍地连接进来
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"], # 开发环境为了省事可以直接写 "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 强类型校验：规定前端发过来的数据必须包含 message 字段
class ChatRequest(BaseModel):
    message: str
    session_id: str = "user_123"
    model: str = "gemini-3.1-flash-lite"
    images: list = [] # 存放 base64 格式的图片数据

@app.post("/chat")
def chat_with_agent(request: ChatRequest):
    """跟 Agent 聊天的专属网络通道"""
    
    # 核心只有这一行：把用户的消息喂给大脑，等它在后台循环思考，拿到最终答案！
    final_reply = run_agent(request.message, request.session_id, request.model, request.images)
    
    return {"status": "success", "reply": final_reply}

@app.post("/chat/stream")
def chat_with_agent_stream(request: ChatRequest):
    """跟 Agent 聊天的流式输出 (SSE) 通道"""
    return StreamingResponse(
        run_agent_stream(request.message, request.session_id, request.model, request.images),
        media_type="text/event-stream"
    )

from feishu_service import reply_to_feishu_user, reply_to_feishu_card

def process_feishu_message(message_id: str, text: str, session_id: str):
    """后台任务：调用流式 Agent 思考并实时同步状态给飞书"""
    print(f"[飞书对接] 开始处理用户消息: {text}")
    
    # 提前安抚用户
    reply_to_feishu_user(message_id, "👀 Agent 已收到任务，正在大脑中拆解与思考...")
    
    final_reply_chunks = []
    is_final_report = False
    
    for chunk in run_agent_stream(text, session_id=session_id):
        if not chunk.startswith("data: "):
            continue
            
        content = chunk[6:].strip()
        if not content:
            continue
            
        # 拦截状态消息，同步给飞书
        if content.startswith("[调度中心]") or content.startswith("[Reflector]"):
            # 取出状态文本，发送给飞书（去除可能带来的换行符）
            status_text = content.replace("\\n", " ")
            reply_to_feishu_user(message_id, f"🔄 思考进度：{status_text}")
            
        elif content == "[最终报告]":
            is_final_report = True
            
        elif is_final_report:
            # 收集最终报告的 Markdown
            final_reply_chunks.append(content.replace("\\n", "\n"))
            
    # 将收集到的报告拼接并使用飞书富文本卡片发送
    final_markdown = "".join(final_reply_chunks).strip()
    if final_markdown:
        reply_to_feishu_card(message_id, final_markdown)
    else:
        reply_to_feishu_user(message_id, "⚠️ 抱歉，Agent 在思考过程中遇到了问题，未能生成完整报告。")

@app.post("/feishu/callback")
async def feishu_callback(request: Request, background_tasks: BackgroundTasks):
    """接收飞书机器人的事件回调"""
    body = await request.json()
    
    # 1. 验证飞书 URL (首次配置事件订阅时)
    if "challenge" in body:
        return {"challenge": body["challenge"]}
        
    print(f"===> 收到飞书推送的事件内容: {json.dumps(body, ensure_ascii=False)}")
    
    # 2. 处理聊天消息事件 (Event V2 格式)
    if "header" in body and "event" in body:
        event = body["event"]
        event_type = body["header"].get("event_type")
        
        if event_type == "im.message.receive_v1":
            message = event.get("message", {})
            msg_type = message.get("message_type")
            message_id = message.get("message_id")
            
            # 只处理纯文本消息（如果是 @机器人，文本里会带 @，可以进一步清洗）
            if msg_type == "text":
                content_str = message.get("content", "{}")
                try:
                    content_dict = json.loads(content_str)
                    # 去除飞书艾特机器人的后缀 (例如 @机器人名称)
                    raw_text = content_dict.get("text", "").strip()
                    # 这里可以写一段简单的正则或 string replace 来去掉 @ 机器人的名字，目前保持简单
                    
                    sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id", "feishu_user")
                    
                    # 放入后台任务异步执行，因为飞书要求 3 秒内必须返回 200，否则会超时重试
                    background_tasks.add_task(process_feishu_message, message_id, raw_text, sender_id)
                except Exception as e:
                    print(f"解析飞书消息失败: {e}")
                
    return {"status": "success"}

if __name__ == "__main__":
    # 在 8000 端口启动服务器！
    uvicorn.run(app, host="127.0.0.1", port=8000)
