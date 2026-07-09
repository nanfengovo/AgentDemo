<div align="center">
  
# 🚀 QuantTrading Agent Terminal

An open-source, full-stack Quant Trading AI Agent platform built with Python and React.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini_API-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)

[English](README.md) | [中文](README_zh.md)

</div>

<br/>

This project demonstrates a production-ready AI Agent architecture tailored for quantitative finance. It breaks away from rigid wrapper frameworks like LangChain, featuring a **custom-built ReAct (Reason + Act) loop**, **multimodal chart analysis**, and **dynamic model routing**. 

Whether you are executing a fundamental analysis on AAPL, or relying on technical indicators (MACD/RSI) for short-term sentiment evaluation, the QuantTrading Agent handles it all while exposing its "Chain of Thought" in real-time.

## 🏗 System Architecture

The system operates on a highly decoupled dual-node architecture, engineered for ultra-low latency streaming and safe tool execution.

<div align="center">
  <img src="assets/architecture.jpg" alt="QuantTrading Agent System Architecture" width="100%" />
</div>

### 🧩 The Agent Core (ReAct Engine)
- **Agent 中枢 (Brain)**: The central orchestration unit. It manages conversation history, maintains context, and dynamically decides whether to call external tools or formulate a final response.
- **规划器 (Planner)**: When the Brain receives a complex goal, the Planner breaks it down into actionable, sequential steps.
- **审核员 (Reflector)**: A strict quality assurance node. It evaluates the drafted report for quantitative strictness, ensuring scores are firmly bounded between 0-100 and no vague "maybe" advice is given.
- **调度中心 (Tool Router)**: Safely dispatches physical tools (market data fetchers via `yfinance`, file I/O operations, and terminal bash execution).

## ✨ Core Features & Tech Stack

<details open>
<summary><b>1. ⚡ Next-Gen Streaming UI (SSE + Next.js)</b></summary>
Powered by Server-Sent Events (SSE), the Next.js React frontend streams the AI's internal thoughts and tool execution logs in real-time. We implemented an interactive "Chain of Thought" (CoT) UI—foldable reasoning blocks that visualize the exact logic the agent followed before rendering the final financial report.
</details>

<details open>
<summary><b>2. 👁️ Multimodal Vision Engine</b></summary>
Seamlessly paste (Ctrl+V) or upload K-line charts, screenshots of financial reports, or market heatmaps directly into the terminal. The Agent processes Base64 image streams dynamically, applying visual technical analysis alongside its textual reasoning. Features a sleek full-screen image lightbox built from scratch.
</details>

<details open>
<summary><b>3. 🔄 Dynamic Multi-Model Routing</b></summary>
The terminal supports hot-swapping between the Gemini 3.5 Pro, Flash, and Lite models mid-conversation. Use the high-speed Lite model for simple queries, and seamlessly switch to Pro for heavy fundamental deep dives.
</details>

<details open>
<summary><b>4. 🛠 Extensible Quant Tool Arsenal</b></summary>
The backend tool schema is highly plug-and-play. Currently ships with real-time stock price fetchers, technical indicator calculators (MA, RSI), and fundamental data pullers utilizing `yfinance`.
</details>


## 🎥 Live Demo

Experience the glassmorphism UI, real-time reasoning, and multimodal capabilities in action:

<div align="center">
  <img src="assets/demo.jpg" alt="QuantTrading Agent Demo" width="100%" />
</div>


## 🚀 Quick Start

### 1. Backend Setup (FastAPI)
Navigate to the backend directory, configure your API key, and start the high-performance ASGI server:

```bash
cd agent_backend

# 1. Install dependencies using uv (or pip)
uv venv
source .venv/bin/activate
uv pip install fastapi uvicorn requests yfinance

# 2. Configure your Gemini API Key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 3. Start the server
uv run --with fastapi --with uvicorn --with requests --with yfinance main.py
```
*The backend will run on `http://127.0.0.1:8000`.*

### 2. Frontend Setup (React/Next.js)
Open a new terminal, navigate to the frontend directory, and start the development server:

```bash
cd agent_frontend

# 1. Install dependencies
npm install

# 2. Start the client
npm run dev
```
*The frontend will run on `http://localhost:3000`.*


## 🛣 Roadmap

- [x] **Agent Core Engine**: Custom Planner, Brain, and Reflector implementation
- [x] **Streaming UI**: SSE streaming with foldable CoT visualization
- [x] **Financial Tools**: Basic fundamental and technical data fetchers
- [x] **Multimodal**: Chart image parsing and lightbox
- [ ] **Long-term Memory**: Vector Database integration to store user risk profiles
- [ ] **Multi-Agent Collaboration**: Separation of Macro, Tech, and Risk specialist agents
- [ ] **Automated Backtesting**: Connecting strategy outputs directly to a Backtrader engine


## 🤝 Contributing

Welcome! This is a foundational project demonstrating raw AI Agent design patterns in the Quantitative Finance domain. If you are interested in AI, LLMs, or Quant Trading, feel free to open an issue, submit a PR, or reach out!

---
<div align="center">
  <i>Built with ❤️ to explore the boundaries of AI in Financial Engineering.</i>
</div>
