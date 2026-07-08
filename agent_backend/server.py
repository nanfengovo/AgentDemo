from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# 允许本地前端调用 (端口 3000 是 Next.js 默认端口)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["http://localhost:3000"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

REPORT_DIR = "./分析报告"

@app.get("/api/reports")
async def list_reports():
    if not os.path.exists(REPORT_DIR):
        return {"reports": []}
    return {"reports": [f for f in os.listdir(REPORT_DIR) if f.endswith(('.txt', '.md'))]}

@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    path = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="文件不存在")
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}
