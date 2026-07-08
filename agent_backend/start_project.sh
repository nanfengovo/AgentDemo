#!/bin/bash
echo "启动后端服务..."
uvicorn server:app --port 8000 &
BACKEND_PID=$!

echo "启动前端服务..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "服务已在后台启动 (后端PID: $BACKEND_PID, 前端PID: $FRONTEND_PID)"
echo "后端: http://localhost:8000"
echo "前端: http://localhost:3000"
