# main.py
from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import json
from feishu_service import reply_to_feishu_user

from fastapi.responses import StreamingResponse

# 把我们刚刚写好的 Agent 大脑导进来
from core_agent.brain import run_agent, run_agent_stream
import core_agent.config # 显式导入 config，触发 .env 文件加载机制

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
    api_key: str = None
    base_url: str = None
    images: list = [] # 存放 base64 格式的图片数据
    enable_finance: bool = True
    enable_search: bool = False

class FolderRequest(BaseModel):
    name: str

class SessionTitleRequest(BaseModel):
    title: str

class SessionFolderRequest(BaseModel):
    folder_id: str

class ModelsRequest(BaseModel):
    api_key: str = None
    base_url: str = None

@app.post("/models")
def get_available_models(request: ModelsRequest):
    import requests
    models = []
    
    # 1. 尝试获取 Gemini 模型
    gemini_key = request.api_key or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}", timeout=5)
            if res.status_code == 200:
                for m in res.json().get("models", []):
                    model_name = m["name"].replace("models/", "")
                    # 排除纯音频输出的 TTS 模型，避免 The requested combination of response modalities (TEXT) is not supported 错误
                    if "tts" in model_name.lower() or "audio" in model_name.lower():
                        continue
                    
                    if "generateContent" in m.get("supportedGenerationMethods", []) or "predict" in m.get("supportedGenerationMethods", []):
                        models.append(model_name)
        except Exception:
            pass
            
    # 2. 尝试获取 OpenAI 兼容接口的模型（如 DeepSeek, OpenAI, Groq 等）
    openai_key = request.api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    # 智能判断默认代理地址
    default_url = "https://api.deepseek.com" if (not request.api_key and not os.getenv("OPENAI_API_KEY") and os.getenv("DEEPSEEK_API_KEY")) else "https://api.openai.com/v1"
    openai_url = request.base_url or os.getenv("OPENAI_BASE_URL", default_url)
    
    if openai_key:
        try:
            headers = {"Authorization": f"Bearer {openai_key}"}
            res = requests.get(f"{openai_url.rstrip('/')}/models", headers=headers, timeout=5)
            if res.status_code == 200:
                for m in res.json().get("data", []):
                    models.append(m["id"])
        except Exception:
            pass
            
    # 3. 添加免费高质量开源生图模型
    models.append("black-forest-labs/FLUX.1-schnell")
    models.append("siliconflow/FLUX.1-schnell")
            
    # 如果都失败或为空，则返回默认备用列表
    if not models:
        models = [
            "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-1.5-pro", "gemini-1.5-flash",
            "gpt-4o", "deepseek-chat", "deepseek-reasoner"
        ]
        
    return {"status": "success", "models": list(set(models))}


@app.post("/chat")
def chat_with_agent(request: ChatRequest):
    """跟 Agent 聊天的专属网络通道"""
    
    # 核心只有这一行：把用户的消息喂给大脑，等它在后台循环思考，拿到最终答案！
    final_reply = run_agent(request.message, request.session_id, request.model, request.images, request.api_key, request.base_url, request.enable_finance, request.enable_search)
    
    return {"status": "success", "reply": final_reply}

@app.post("/chat/stream")
def chat_with_agent_stream(request: ChatRequest):
    """跟 Agent 聊天的流式输出 (SSE) 通道"""
    return StreamingResponse(
        run_agent_stream(request.message, request.session_id, request.model, request.images, request.api_key, request.base_url, request.enable_finance, request.enable_search),
        media_type="text/event-stream"
    )

from memory.persistent import get_folders, create_folder, get_sessions, update_session_folder, update_session_title, get_history

@app.get("/folders")
def api_get_folders():
    return {"status": "success", "folders": get_folders()}

@app.post("/folders")
def api_create_folder(req: FolderRequest):
    folder_id = create_folder(req.name)
    return {"status": "success", "folder_id": folder_id}

@app.get("/sessions")
def api_get_sessions():
    return {"status": "success", "sessions": get_sessions()}

@app.get("/sessions/{session_id}")
def api_get_session_history(session_id: str):
    history = get_history(session_id)
    return {"status": "success", "history": history}

@app.post("/sessions/{session_id}/title")
def api_update_session_title(session_id: str, req: SessionTitleRequest):
    update_session_title(session_id, req.title)
    return {"status": "success"}

@app.post("/sessions/{session_id}/folder")
def api_update_session_folder(session_id: str, req: SessionFolderRequest):
    update_session_folder(session_id, req.folder_id)
    return {"status": "success"}

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
    # 在 8000 端口启动服务器，开启 reload=True 实现代码热更新！
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
