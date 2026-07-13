<div align="center">
  
# 🚀 QuantTrading Agent Terminal

一个基于 Python 和 React 构建的开源全栈量化交易 AI Agent 平台。

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

本项目展示了一个专为量化金融打造的生产级 AI Agent 架构。它抛弃了诸如 LangChain 这样臃肿的黑盒框架，选择从底层实现 **原生定制的 ReAct (Reason + Act) 循环引擎**、**多模态图表视觉分析**，以及 **动态模型热切换路由**。

无论你是要对 AAPL 执行深度的基本面拆解，还是依赖技术指标 (MACD/RSI) 评估短线市场情绪，QuantTrading Agent 都能游刃有余地处理，并实时将它的“思维链 (Chain of Thought)”完全透明地展示给你。

## 🏗 系统架构

系统采用高度解耦的双节点架构，专为超低延迟的流式传输和安全的物理工具调度而设计。

<div align="center">
  <img src="assets/architecture.jpg" alt="QuantTrading Agent System Architecture" width="100%" />
</div>

### 🧩 核心组件详解 (Core Components Deep Dive)

本系统并不是简单调用大模型的 API，而是从零构建了一套拥有自我规划、自我反思、物理执行与多端响应的完整生命周期系统。以下是核心构建模块的详细说明：

#### 1. 🧠 Agent 中枢 (Brain) - `core_agent/brain.py`
**构建原理**：系统的中央交响乐团指挥，基于原生的 **ReAct (Reason + Act)** 循环机制。
*   **状态机循环**：通过一个带有最大迭代次数（死循环安全阀）的 `while` 循环，持续解析大模型的回复。如果大模型触发了 `functionCall`，大脑会将其拦截，转交调度中心执行，并把结果强制塞回记忆上下文中继续下一轮推理；如果大模型直接输出文本，大脑则判定思考结束，流转到质检环节。
*   **流式输出 (SSE)**：为了极致的用户体验，我们在 `run_agent_stream` 中使用了 Python 的 `yield` 生成器引擎，将 Planner、Tool Router 和大模型每一次微小的思考状态（如：`[调度中心] 正在执行...`）实时转化为 Server-Sent Events (SSE) 数据流，无缝推送到前端和飞书。

#### 2. 🗺️ 规划器 (Planner) - `core_agent/planner.py`
**构建原理**：负责**复杂任务降维与目标拆解**。
*   当接收到一个宏大的金融问题时，直接扔给大模型容易导致逻辑混乱。Planner 会作为一个前置节点，调用一次大模型进行宏观思考，将问题强制拆解为 `1. 提取股票代码 -> 2. 拉取基本面 -> 3. 拉取技术面 -> 4. 交叉验证` 这样线性、结构化的 JSON 任务流，然后将这份清单“注入”到后续的系统提示词中，像导航仪一样约束 Agent 的推理路径。

#### 3. 🧐 审核员 (Reflector) - `core_agent/reflector.py`
**构建原理**：极为严苛的**后置质量保证节点 (QA)**。
*   **强硬对抗机制**：大模型天生喜欢写“套话”（如：*“这只股票存在风险但也可能上涨，建议投资者谨慎操作”*）。Reflector 的作用是在草稿报告生成后，截停数据，要求大模型以质检员身份对草稿进行严格打分。
*   **打回重写**：如果报告中没有明确的 `0-100` 打分，或者结论模棱两可，Reflector 会直接返回 `FAIL` 和修改意见。大脑会带着这些修改意见（如：“你的报告被质检员打回！必须包含具体的止损点位”）重新驱动大模型修改，直到 Reflector 输出 `PASS` 才会放行给最终用户。

#### 4. 🔧 调度中心 (Tool Router) - `core_agent/tool_router.py` & `tool_schema.py`
**构建原理**：安全地分发并执行“物理兵器”。
*   **声明式 Schema**：在 `tool_schema.py` 中严格按照 Google Gemini 规定的 JSON Schema 格式定义了各个工具的能力边界（如 `get_stock_price`、`search_local_files`）。
*   **解耦分发引擎**：`tool_router.py` 使用动态字典分发请求。当大模型产生函数调用意图时，Router 会捕捉具体的函数名和参数，调用真正的本地 Python 脚本（如 `finance_tools.py` 通过 `yfinance` 拉取纳斯达克数据），然后将报错捕获或数据清洗后的结果包装返回。

#### 5. 🔔 飞书协同矩阵 (Feishu Integration) - `feishu_service.py` & `main.py`
**构建原理**：不仅局限于 Web 端，系统深入对接了飞书的 OpenAPI，实现了强大的即时通讯办公自动化。
*   **双向监听与异步处理**：在 FastAPI 中通过 `/feishu/callback` 处理飞书企业机器人的事件订阅。利用 FastAPI 的 `BackgroundTasks` 将耗时的量化计算直接扔到后台执行，确保飞书 Webhook 3秒内返回 200，避免超时重试风暴。
*   **富文本动态卡片**：彻底抛弃了简陋的纯文本回复，创新性地将大模型生成的思考进度与最终 Markdown 报告，通过 JSON 序列化组装成飞书专属的 **互动消息卡片 (Interactive Message Card)**。它能动态渲染高亮色块、结构化排版，在聊天窗口内提供降维打击般的专业阅读体验。

#### 6. 🔌 通用大模型适配器 (LLM Adapter) - `core_agent/llm_adapter.py`
**构建原理**：实现多模型自由切换的核心桥梁。
*   **架构解耦引擎**：在系统内部使用行业标准的 OpenAI 格式维护上下文状态，并在发送请求时，动态将其翻译为 Google Gemini、OpenAI 或 DeepSeek API 所要求的特定格式。
*   **动态参数注入**：支持直接从前端界面的“设置”面板中，热更新 API Key 和 Base URL。用户无需重启后端服务，即可在不同厂商的模型之间瞬间切换。

## ✨ 核心特性与技术栈

<details open>
<summary><b>1. ⚡ 现代化的流式交互 UI (SSE + Next.js)</b></summary>
基于 Server-Sent Events (SSE) 协议，Next.js 客户端能够毫秒级实时渲染 AI 的内部思考过程与工具执行日志。我们实现了交互式的“思维链” (CoT) UI——通过精美的折叠面板，清晰可视化 Agent 最终输出金融报告前的每一滴逻辑推演。
</details>

<details open>
<summary><b>2. 👁️ 多模态视觉解析引擎</b></summary>
直接在终端内粘贴 (Ctrl+V) 或上传 K 线图、财报截图或是热力图。Agent 能够动态处理 Base64 图像流，将视觉形态分析与纯文本逻辑推演完美融合。并搭载了从零手写的全屏图片放大沉浸预览 (Lightbox) 交互。
</details>

<details open>
<summary><b>3. 🔄 跨厂商动态多模型热切换</b></summary>
平台支持在一次会话中，通过 UI 设置面板随时在不同厂商的大模型间无缝切换。你可以使用 <b>DeepSeek v4/R1</b> 进行极其复杂的深度逻辑推演，切换至 <b>OpenAI GPT-4o</b> 获取稳健的综合分析，或者使用 <b>Gemini Flash</b> 处理极速的轻量化查询。
</details>

<details open>
<summary><b>4. 🛠 即插即用的量化兵器库</b></summary>
后端的工具 Schema 设计高度解耦。当前已内置基于 `yfinance` 的实时股票价格获取、技术指标计算脚本 (MA, RSI)，以及基本面数据拉取器。
</details>


## 🎥 快速演示

感受高质感的毛玻璃 UI (Glassmorphism)、实时逻辑推演以及多模态视觉的魅力：

<div align="center">
  <img src="assets/demo.jpg" alt="QuantTrading Agent Demo" width="100%" />
</div>


## 🚀 快速开始

### 1. 启动后端 (FastAPI)
进入后端目录，配置你的 API Key，然后启动高性能的 ASGI 服务器：

```bash
cd agent_backend

# 1. 使用 uv (或 pip) 安装依赖
uv venv
source .venv/bin/activate
uv pip install fastapi uvicorn requests yfinance

# 2. 配置你的 API Key (可以配置多个厂商的 Key)
echo "GEMINI_API_KEY=你的_gemini_key" > .env
echo "OPENAI_API_KEY=你的_openai_key" >> .env
echo "DEEPSEEK_API_KEY=你的_deepseek_key" >> .env
echo "OPENAI_BASE_URL=https://api.openai.com/v1" >> .env

# 3. 启动服务器
uv run --with fastapi --with uvicorn --with requests --with yfinance main.py
```
*后端服务将运行在 `http://127.0.0.1:8000`。*

### 2. 启动前端 (React/Next.js)
打开一个新的终端窗口，进入前端目录，启动开发服务器：

```bash
cd agent_frontend

# 1. 安装前端依赖
npm install

# 2. 启动客户端
npm run dev
```
*前端界面将运行在 `http://localhost:3000`。*


## 🛣 演进路线图

- [x] **Agent 核心引擎**: 原生定制 Planner、Brain 和 Reflector 模块
- [x] **通用模型适配器**: 原生支持 OpenAI、DeepSeek 与 Gemini 的架构解耦
- [x] **流式交互 UI**: 基于 SSE 的可折叠思维链 (CoT) 可视化与动态设置面板
- [x] **金融兵器库**: 基础的基本面和技术面数据获取工具
- [x] **多模态能力**: 终端图片上传、粘贴与 Lightbox 沉浸解析
- [ ] **长期记忆 (Memory)**: 接入向量数据库，构建用户的专属风险画像
- [ ] **多智能体协同 (Multi-Agent)**: 拆分宏观 (Macro)、技术 (Tech) 和风控 (Risk) 专用的子 Agent
- [ ] **自动化回测框架**: 将策略输出直接无缝接入 Backtrader 回测引擎


## 🤝 参与贡献

欢迎！这是一个旨在展示量化金融领域最纯粹的 AI Agent 设计模式的基础开源项目。如果你对 AI、大模型或量化交易感兴趣，欢迎随时提交 Issue、发起 PR 或与我们联系探讨！

---
<div align="center">
  <i>Built with ❤️ to explore the boundaries of AI in Financial Engineering.</i>
</div>
