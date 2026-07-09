# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

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

if __name__ == "__main__":
    # 在 8000 端口启动服务器！
    uvicorn.run(app, host="127.0.0.1", port=8000)
