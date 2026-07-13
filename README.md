<div align="center">
  
# 🚀 QuantTrading Agent Terminal

An open-source, full-stack Quant Trading AI Agent platform built with Python and React.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-4D90FE?style=for-the-badge&logo=ai&logoColor=white)](https://deepseek.com/)

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

### 🧩 Core Components Deep Dive

This system goes far beyond simple API wrapping. It is a complete, self-governing lifecycle engine built from scratch with capabilities for planning, self-reflection, physical execution, and multi-platform response. Here is a detailed breakdown of the core building blocks:

#### 1. 🧠 Agent Brain (`core_agent/brain.py`)
**Architecture**: The central orchestration unit based on a native **ReAct (Reason + Act)** loop mechanism.
*   **State Machine Loop**: It employs a rigorous `while` loop (with a maximum iteration safety valve) to continuously parse LLM outputs. If the model triggers a `functionCall`, the Brain intercepts it, routes it to the Tool Router for execution, and forces the physical result back into the memory context for the next reasoning cycle. If the model outputs plain text, the Brain determines that the reasoning phase is complete and transitions to the Quality Assurance (Reflector) phase.
*   **Streaming Engine (SSE)**: To ensure a premium user experience, the `run_agent_stream` utilizes Python's `yield` generators. It translates every micro-state of the Planner, Tool Router, and LLM (e.g., `[Tool Router] Executing...`) into real-time Server-Sent Events (SSE) data streams, pushing them seamlessly to the Frontend and Feishu.

#### 2. 🗺️ Planner (`core_agent/planner.py`)
**Architecture**: Responsible for **dimensional reduction and goal breakdown** of complex tasks.
*   Feeding a massive financial query directly to an LLM often causes logical hallucinations. The Planner acts as a prerequisite node, prompting the LLM for macroscopic thinking to break the goal into linear, structured JSON steps (e.g., `1. Extract Ticker -> 2. Fetch Fundamentals -> 3. Fetch Technicals -> 4. Cross-Verify`). This checklist is then "injected" into subsequent system prompts, acting as a strict GPS for the Agent's reasoning path.

#### 3. 🧐 Reflector (`core_agent/reflector.py`)
**Architecture**: A ruthlessly strict **Post-Generation QA Node**.
*   **Adversarial Mechanism**: LLMs naturally tend to write evasive, ambiguous advice (e.g., *"This stock has risks but may also rise, exercise caution"*). The Reflector intercepts the draft report and forces the LLM to act as an auditor to grade the draft.
*   **Reject & Rewrite**: If the report lacks a definitive `0-100` quantitative score or contains ambiguous conclusions, the Reflector returns `FAIL` along with modification directives. The Brain then feeds this critique (e.g., "Your report was rejected! It must contain a precise stop-loss price") back to the LLM, forcing it to rewrite until the Reflector outputs `PASS`.

#### 4. 🔧 Tool Router (`core_agent/tool_router.py` & `tool_schema.py`)
**Architecture**: Safely dispatches and executes physical "weapons."
*   **Declarative Schema**: Capabilities (like `get_stock_price` or `search_local_files`) are strictly defined in `tool_schema.py` using the exact JSON Schema formats mandated by Google Gemini.
*   **Decoupled Dispatcher**: `tool_router.py` uses a dynamic dictionary mapping for request dispatching. When the LLM expresses an intent to call a function, the Router captures the exact function name and arguments, triggers the actual local Python script (e.g., fetching NASDAQ data via `yfinance` in `finance_tools.py`), and packages the cleaned data or caught errors back to the model.

#### 5. 🔔 Feishu Synergy Matrix (`feishu_service.py` & `main.py`)
**Architecture**: The system extends beyond the Web UI, integrating deeply with Feishu's OpenAPI to achieve powerful IM-based office automation.
*   **Bidirectional Async Webhooks**: The FastAPI backend handles Feishu enterprise bot event subscriptions via `/feishu/callback`. It leverages FastAPI's `BackgroundTasks` to offload heavy quant calculations, ensuring the webhook returns a `200 OK` within Feishu's strict 3-second timeout window.
*   **Rich Interactive Cards**: Abandoning basic plain text, it innovatively serializes the LLM's CoT progress and final Markdown reports into Feishu's exclusive **Interactive Message Cards**. This allows for dynamic rendering of syntax highlights and structured layouts directly within the chat window.

#### 6. 🔌 Universal LLM Adapter (`core_agent/llm_adapter.py`)
**Architecture**: The crucial bridge enabling true multi-model freedom.
*   **Decoupling Engine**: It normalizes internal system state (using the industry-standard OpenAI format) and translates payloads on-the-fly to the specific requirements of Google Gemini, OpenAI, or DeepSeek APIs. 
*   **Dynamic Injection**: Supports real-time API Key and Base URL injection from the frontend Settings Modal. This allows users to switch underlying models instantly via the UI without restarting the backend.

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
<summary><b>3. 🔄 Universal Multi-Model Support</b></summary>
The terminal supports hot-swapping between different model providers mid-conversation via the UI Settings panel. Use <b>DeepSeek v4/R1</b> for advanced reasoning, <b>OpenAI GPT-4o</b> for robust analysis, or <b>Gemini Flash</b> for high-speed queries. Inject custom API Keys and proxy Base URLs directly from the web interface.
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

# 2. Configure your API Keys (Choose at least one provider)
echo "GEMINI_API_KEY=your_gemini_key_here" > .env
echo "OPENAI_API_KEY=your_openai_key_here" >> .env
echo "DEEPSEEK_API_KEY=your_deepseek_key_here" >> .env
echo "OPENAI_BASE_URL=https://api.openai.com/v1" >> .env

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
- [x] **Universal Model Adapter**: Native support for OpenAI, DeepSeek, and Gemini formats
- [x] **Streaming UI**: SSE streaming with foldable CoT visualization & Settings Modal
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
