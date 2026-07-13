"use client";

import { useState, useRef, useEffect } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";
import './globals.css';

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState("gemini-3.1-flash-lite");
  const [images, setImages] = useState([]);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [previewImg, setPreviewImg] = useState(null); 
  const [showSettings, setShowSettings] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [availableModels, setAvailableModels] = useState([]);
  
  const abortControllerRef = useRef(null);
  
  // New States for 3-Column Layout
  const [sessionId, setSessionId] = useState("user_123");
  const [sessions, setSessions] = useState([]);
  const [folders, setFolders] = useState([]);
  const [enableFinance, setEnableFinance] = useState(true);
  const [enableSearch, setEnableSearch] = useState(false);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);
  
  const messagesEndRef = useRef(null);
  
  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    // 限制最多 3 张图片
    if (images.length + files.length > 3) {
        alert("最多只能上传 3 张图片！");
        return;
    }
    
    files.forEach(file => {
        const reader = new FileReader();
        reader.onloadend = () => {
            setImages(prev => [...prev, reader.result]);
        };
        reader.readAsDataURL(file);
    });
    // 清空 input，以便重复上传同一张图片时仍能触发 onChange
    e.target.value = null;
  };
  
  const removeImage = (index) => {
      setImages(prev => prev.filter((_, i) => i !== index));
  };
  
  const handlePaste = (e) => {
    if (e.clipboardData && e.clipboardData.files.length > 0) {
      const files = Array.from(e.clipboardData.files).filter(file => file.type.startsWith("image/"));
      if (files.length === 0) return;
      
      e.preventDefault(); // 拦截默认粘贴文字的行为（如果是图文混合，仅处理图片也可以不拦截）
      
      if (images.length + files.length > 3) {
          alert("最多只能上传 3 张图片！");
          return;
      }
      
      files.forEach(file => {
          const reader = new FileReader();
          reader.onloadend = () => {
              setImages(prev => [...prev, reader.result]);
          };
          reader.readAsDataURL(file);
      });
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchModels = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          api_key: apiKey || undefined,
          base_url: baseUrl || undefined
        }),
      });
      const data = await response.json();
      if (data.status === "success" && data.models && data.models.length > 0) {
        setAvailableModels(data.models);
        // 如果当前选中的模型不在新列表中，默认选中第一个
        setModel(prevModel => data.models.includes(prevModel) ? prevModel : data.models[0]);
      }
    } catch (e) {
      console.error("Failed to fetch models", e);
    }
  };

  const fetchSessionsAndFolders = async () => {
    try {
      const [sessRes, foldRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/sessions"),
        fetch("http://127.0.0.1:8000/folders")
      ]);
      const sessData = await sessRes.json();
      const foldData = await foldRes.json();
      if (sessData.status === "success") setSessions(sessData.sessions);
      if (foldData.status === "success") setFolders(foldData.folders);
    } catch (e) {
      console.error("Failed to fetch sessions or folders", e);
    }
  };

  const loadSession = async (sid) => {
    try {
      setSessionId(sid);
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sid}`);
      const data = await res.json();
      if (data.status === "success") {
        setMessages(data.history || []);
      }
    } catch (e) {
      console.error("Failed to load session", e);
    }
  };

  const createNewSession = () => {
    setSessionId("session_" + Math.random().toString(36).substring(2, 8));
    setMessages([]);
  };

  useEffect(() => {
    fetchModels();
    fetchSessionsAndFolders();
    createNewSession();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const closeSettings = () => {
    setShowSettings(false);
    fetchModels();
  };

  const handleChatClick = (e) => {
    if (e.target.tagName === 'IMG') {
      setPreviewImg(e.target.src);
    }
  };

  const handleQuote = (fullText) => {
    const selection = window.getSelection();
    let textToQuote = fullText;
    
    // 如果用户在页面上有高亮选中的文字，优先引用选中部分
    if (selection && selection.toString().trim()) {
      textToQuote = selection.toString().trim();
    }

    setInput(prev => {
      const quote = "> " + textToQuote.split('\n').join('\n> ') + "\n\n";
      return prev ? prev + "\n" + quote : quote;
    });
    // 聚焦输入框
    const inputEl = document.querySelector(".chat-input");
    if (inputEl) inputEl.focus();
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    const currentImages = [...images]; 
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role: "user", content: userMsg, images: currentImages, timestamp }]);
    setInput("");
    setImages([]); // 发送后清空图片附件
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      // 通过 Fetch API 连接后端的流式通道
      const response = await fetch("http://127.0.0.1:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ 
          message: userMsg, 
          session_id: sessionId,
          model: model,
          images: currentImages,
          api_key: apiKey || undefined,
          base_url: baseUrl || undefined,
          enable_finance: enableFinance,
          enable_search: enableSearch
        }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      // 初始化一个空的 AI 消息，默认进入思考模式
      const aiTimestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
      setMessages(prev => [...prev, { role: "ai", content: "", rawChunks: [], inThoughtProcess: true, timestamp: aiTimestamp }]);

      // 核心修复：引入 buffer 解决长文本被网络底层强制拆包导致的截断问题
      let buffer = "";

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          
          let eolIndex;
          while ((eolIndex = buffer.indexOf('\n')) >= 0) {
            const line = buffer.slice(0, eolIndex);
            buffer = buffer.slice(eolIndex + 1);
            
            if (line.startsWith("data: ")) {
              let textChunk = line.substring(6).replace(/\\n/g, "\n");
              
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = { ...newMsgs[newMsgs.length - 1] };
                lastMsg.rawChunks = [...(lastMsg.rawChunks || [])];

                if (lastMsg.role === "ai") {
                  if (textChunk.startsWith("[METADATA]")) {
                    lastMsg.metadata = textChunk.substring(10);
                    newMsgs[newMsgs.length - 1] = lastMsg;
                    return newMsgs;
                  }

                  if (textChunk.includes("[最终报告]")) {
                    lastMsg.inThoughtProcess = false;
                    newMsgs[newMsgs.length - 1] = lastMsg;
                    return newMsgs;
                  }

                  if (lastMsg.inThoughtProcess) {
                    const lastChunkIdx = lastMsg.rawChunks.length - 1;
                    const lastChunk = lastMsg.rawChunks[lastChunkIdx];
                    
                    if (lastChunk && lastChunk.type === "thought" && !textChunk.match(/^\[(Planner|Agent|Reflector|调度|工具)\]/)) {
                        lastMsg.rawChunks[lastChunkIdx] = { 
                          ...lastChunk, 
                          text: lastChunk.text + "\n" + textChunk 
                        };
                    } else {
                        if (textChunk.trim()) {
                            lastMsg.rawChunks.push({ type: "thought", text: textChunk });
                        }
                    }
                  } else {
                    lastMsg.rawChunks.push({ type: "text", text: textChunk });
                  }
                }
                
                newMsgs[newMsgs.length - 1] = lastMsg;
                return newMsgs;
              });
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
         setMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = { ...newMsgs[newMsgs.length - 1] };
            if (lastMsg && lastMsg.role === "ai") {
                lastMsg.inThoughtProcess = false;
                lastMsg.rawChunks = [...(lastMsg.rawChunks || []), { type: "text", text: "\n\n*(已终止)*" }];
            }
            newMsgs[newMsgs.length - 1] = lastMsg;
            return newMsgs;
         });
      } else {
         setMessages(prev => [...prev, { role: "ai", rawChunks: [{ type: "text", text: "❌ 网络错误：无法连接到本地大盘网关，请确保 FastAPI 后端运行在 8000 端口。" }] }]);
      }
    } finally {
      abortControllerRef.current = null;
      setLoading(false);
      fetchSessionsAndFolders(); // Refresh sessions list
    }
  };

  const renderAiMessage = (msg, msgIdx) => {
    if (!msg.rawChunks) return null;
    
    let textContent = "";
    const elements = [];

    // 配置 marked 解析器以自动补全本地图片路径，如果后端传来的图片路径是相对路径
    const renderer = new marked.Renderer();
    const originalImage = renderer.image.bind(renderer);
    renderer.image = (href, title, text) => {
      // 兼容相对路径转为后端静态资源代理路径，如果你使用 /static 访问
      if (href && !href.startsWith("http") && !href.startsWith("data:")) {
         href = `http://127.0.0.1:8000/static/${href.replace(/^\//, '')}`;
      }
      return originalImage(href, title, text);
    };
    marked.use({ renderer });
    
    msg.rawChunks.forEach((chunk, index) => {
      if (chunk.type === "thought") {
        let thoughtClass = "thought-block";
        if (chunk.text.includes("[Planner]")) thoughtClass += " planner";
        else if (chunk.text.includes("[Reflector]")) thoughtClass += " reflector";
        else if (chunk.text.includes("[Agent大脑]") || chunk.text.includes("深度思考")) thoughtClass += " brain";
        else thoughtClass += " tool";
        
        const lines = chunk.text.trim().split('\n');
        const firstLine = lines[0];
        const restText = lines.slice(1).join('\n');

        // 如果包含多行内容，或者内容非常长，则渲染为可折叠面板
        if (lines.length > 1 || chunk.text.length > 60) {
            const cleanDetailHtml = DOMPurify.sanitize(marked.parse(restText));
            elements.push(
              <details key={index} className={thoughtClass}>
                <summary className="thought-summary">{firstLine}</summary>
                {restText && (
                  <div className="thought-detail" dangerouslySetInnerHTML={{ __html: cleanDetailHtml }}>
                  </div>
                )}
              </details>
            );
        } else {
            elements.push(
              <div key={index} className={`${thoughtClass} non-collapsible`}>
                {chunk.text}
              </div>
            );
        }
      } else {
        textContent += chunk.text;
      }
    });

    if (textContent.trim()) {
      // 去除可能遗留的 [最终报告] 等纯占位标记
      textContent = textContent.replace("[最终报告]", "").trim();
      const cleanHtml = DOMPurify.sanitize(marked.parse(textContent));
      elements.push(<div key="content" dangerouslySetInnerHTML={{ __html: cleanHtml }} />);
      
      // 动作栏：复制和引用
      elements.push(
        <div key="actions" className="message-actions" style={msg.metadata ? { marginBottom: "2rem" } : {}}>
          <button onClick={() => handleCopy(textContent, msgIdx)} className="action-btn" title="复制内容">
            {copiedIndex === msgIdx ? (
              <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> <span style={{color: '#10b981'}}>已复制</span></>
            ) : (
              <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> 复制</>
            )}
          </button>
          <button onClick={() => handleQuote(textContent)} className="action-btn" title="引用该回复">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1.5.5 1.5 1.5L5 15c0 2-2 3-2 3z"></path><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.5c0 2-2 3-2 3z"></path></svg>
            引用
          </button>
        </div>
      );
    }
    
    // 如果有 Metadata (模型、工具信息)，显示在底部
    if (msg.metadata) {
      elements.push(
        <div key="metadata" className="metadata-footer">
          {msg.metadata}
        </div>
      );
    }
    
    // 显示时间戳
    if (msg.timestamp) {
       elements.push(
         <div key="timestamp" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px', textAlign: 'left' }}>
           {msg.timestamp}
         </div>
       );
    }

    return elements;
  };

  const extractMedia = () => {
    const media = [];
    messages.forEach(msg => {
       if (msg.images && msg.images.length > 0) {
          media.push(...msg.images);
       }
       if (msg.role === 'ai' && msg.rawChunks) {
          const textContent = msg.rawChunks.filter(c => c.type === 'text').map(c => c.text).join('\n');
          const regex = /!\[.*?\]\((.*?)\)/g;
          let match;
          while ((match = regex.exec(textContent)) !== null) {
            let href = match[1];
            if (href && !href.startsWith("http") && !href.startsWith("data:")) {
               href = `http://127.0.0.1:8000/static/${href.replace(/^\//, '')}`;
            }
            media.push(href);
          }
       }
    });
    return media;
  };
  
  return (
    <div className="app-container">
      <div 
        className="app-layout"
        style={{ 
          gridTemplateColumns: `${leftSidebarOpen ? '260px' : '0px'} 1fr ${rightSidebarOpen ? '260px' : '0px'}`,
          transition: 'grid-template-columns 0.3s ease'
        }}
      >
      {/* 左侧边栏 (Left Sidebar) */}
      <aside className="sidebar-left" style={{ overflow: 'hidden' }}>
        <div className="sidebar-section">
          <h3>⚡ 引擎能力矩阵</h3>
          <div className="switch-group">
            <span>量化与金融工具</span>
            <label className="switch">
              <input type="checkbox" checked={enableFinance} onChange={e => setEnableFinance(e.target.checked)} />
              <span className="slider"></span>
            </label>
          </div>
          <div className="switch-group">
            <span>Google 联网搜索</span>
            <label className="switch">
              <input type="checkbox" checked={enableSearch} onChange={e => setEnableSearch(e.target.checked)} />
              <span className="slider"></span>
            </label>
          </div>
        </div>

        <div className="sidebar-section" style={{ flex: 1, overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>📁 历史会话</h3>
            <button onClick={createNewSession} style={{ background: 'transparent', border: 'none', color: 'var(--accent-color)', cursor: 'pointer' }}>+ 新开</button>
          </div>
          
          {sessions.map(s => (
            <div 
              key={s.session_id} 
              className={`sidebar-item ${s.session_id === sessionId ? 'active' : ''}`}
              onClick={() => loadSession(s.session_id)}
              title={s.title}
            >
              💬 {s.title.length > 12 ? s.title.substring(0, 12) + "..." : s.title}
            </div>
          ))}
        </div>
      </aside>

      {/* 主聊天区 (Main Chat) */}
      <div className="main-container">
      <header className="header glass-panel">
        <div className="header-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button className="icon-btn" onClick={() => setLeftSidebarOpen(!leftSidebarOpen)} title="切换侧边栏" style={{ padding: '4px' }}>
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
          </button>
          <div className="status-indicator"></div>
          QuantTrading Agent Terminal
        </div>
        <div className="header-actions">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
            <select 
              className="model-selector" 
              value={model} 
              onChange={(e) => setModel(e.target.value)}
              disabled={loading}
            >
              {(() => {
                const imageModels = availableModels.filter(m => {
                  const lower = m.toLowerCase();
                  return lower.includes("imagen") || lower.includes("veo") || lower.includes("lyria") || lower.includes("nano banana") || lower.includes("image");
                });
                const geminiModels = availableModels.filter(m => (m.toLowerCase().includes("gemini") || m.toLowerCase().includes("learnlm")) && !imageModels.includes(m));
                const openaiModels = availableModels.filter(m => (m.toLowerCase().includes("gpt") || m.toLowerCase().includes("o1")) && !imageModels.includes(m));
                const deepseekModels = availableModels.filter(m => m.toLowerCase().includes("deepseek") && !imageModels.includes(m));
                const otherModels = availableModels.filter(m => !geminiModels.includes(m) && !openaiModels.includes(m) && !deepseekModels.includes(m) && !imageModels.includes(m));
                
                return (
                  <>
                    {geminiModels.length > 0 && (
                      <optgroup label="Google Gemini">
                        {geminiModels.map(m => <option key={m} value={m}>{m}</option>)}
                      </optgroup>
                    )}
                    {imageModels.length > 0 && (
                      <optgroup label="AI 生图与视频 (Image & Video)">
                        {imageModels.map(m => <option key={m} value={m}>{m}</option>)}
                      </optgroup>
                    )}
                    {deepseekModels.length > 0 && (
                      <optgroup label="DeepSeek">
                        {deepseekModels.map(m => <option key={m} value={m}>{m}</option>)}
                      </optgroup>
                    )}
                    {openaiModels.length > 0 && (
                      <optgroup label="OpenAI">
                        {openaiModels.map(m => <option key={m} value={m}>{m}</option>)}
                      </optgroup>
                    )}
                    {otherModels.length > 0 && (
                      <optgroup label="Other Models">
                        {otherModels.map(m => <option key={m} value={m}>{m}</option>)}
                      </optgroup>
                    )}
                  </>
                );
              })()}
            </select>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginRight: '4px' }}>
              {model.includes('imagen') ? '🎨 谷歌旗舰级 AI 生图模型，支持极高质量与光影细节' :
               model.includes('veo') ? '🎬 谷歌最强视频生成模型，理解物理规律与电影级运镜' :
               model.includes('flash-lite') ? '⚡ 极速轻量模型，适合快速问答与基础工具调用' :
               model.includes('flash') ? '⚖️ 均衡旗舰，又快又聪明，推荐作为全能主力' :
               model.includes('pro') ? '🧠 深度逻辑推理王者，适合长文本与复杂数学代码' :
               model.includes('deepseek') ? '🚀 开源界顶流，极强的代码与逻辑性价比' :
               model.includes('gpt') ? '🌟 行业标杆模型' : 
               '🔍 探索与其他用途大模型'}
            </span>
          </div>
          <button className="icon-btn" onClick={() => setShowSettings(true)} title="设置 API Key">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          </button>
          <button className="icon-btn" onClick={() => setRightSidebarOpen(!rightSidebarOpen)} title="切换媒体侧边栏">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
          </button>
        </div>
      </header>

      <main className="chat-area" onClick={handleChatClick}>
        {messages.length === 0 && (
          <div style={{ margin: "auto", textAlign: "center", color: "var(--text-secondary)" }}>
            <h2 style={{ color: "var(--text-primary)", marginBottom: "1rem" }}>欢迎进入高阶量化终端</h2>
            <p>基于跨平台 PWA 构建，全端无缝适配。</p>
            <p>试试输入："分析一下苹果(AAPL)的技术面"</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === "user" ? (
              <>
                {msg.images && msg.images.length > 0 && (
                  <div className="message-images" style={{ display: 'flex', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                    {msg.images.map((img, i) => (
                      <img key={i} src={img} alt="upload" style={{ maxWidth: '150px', maxHeight: '150px', borderRadius: '8px', objectFit: 'cover', border: '1px solid var(--panel-border)' }} />
                    ))}
                  </div>
                )}
                <div>
                  {typeof msg.content === 'string' 
                    ? msg.content 
                    : (Array.isArray(msg.content) 
                        ? msg.content.map(c => c.type === 'text' ? c.text : '').join('\n') 
                        : JSON.stringify(msg.content))}
                </div>
                {msg.timestamp && (
                  <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', marginTop: '4px', textAlign: 'right' }}>
                    {msg.timestamp}
                  </div>
                )}
              </>
            ) : renderAiMessage(msg, idx)}
          </div>
        ))}
        
        {loading && (
          <div className="message ai">
             <div className="typing-indicator">
              <span></span><span></span><span></span>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className="input-area">
        {!loading && messages.length > 0 && (
          <div className="suggestions-bar" style={{ display: 'flex', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
            <button className="suggestion-pill" onClick={() => setInput("帮我分析苹果(AAPL)的技术面，并结合MACD等指标判断未来走势。")}>📈 分析苹果(AAPL)</button>
            <button className="suggestion-pill" onClick={() => setInput("画一只赛博朋克风格的猫。")}>🎨 画一只赛博朋克的猫</button>
            <button className="suggestion-pill" onClick={() => setInput("今天美股大盘走势如何？有什么重大新闻？")}>📊 今日美股复盘</button>
          </div>
        )}
        {images.length > 0 && (
          <div className="image-preview-container">
            {images.map((img, idx) => (
              <div key={idx} className="image-thumbnail">
                <img src={img} alt="preview" />
                <button className="remove-img-btn" onClick={() => removeImage(idx)}>×</button>
              </div>
            ))}
          </div>
        )}
        <div className="input-container glass-panel">
          <label className="attachment-btn">
            📎
            <input 
              type="file" 
              accept="image/*" 
              multiple 
              onChange={handleImageUpload} 
              disabled={loading} 
            />
          </label>
          <input 
            type="text" 
            className="chat-input"
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            onPaste={handlePaste}
            placeholder="输入指令或上传图表要求分析 (支持 Ctrl+V 粘贴图片)..."
            disabled={loading}
          />
          {loading ? (
            <button className="send-btn" onClick={handleStop} style={{ backgroundColor: '#dc2626', borderColor: '#dc2626' }}>
              Stop
            </button>
          ) : (
            <button className="send-btn" onClick={handleSend} disabled={!input.trim() && images.length === 0}>
              Send
            </button>
          )}
        </div>
      </footer>

      {previewImg && (
        <div className="lightbox-overlay" onClick={() => setPreviewImg(null)}>
          <button className="lightbox-close">×</button>
          <img src={previewImg} alt="Preview" className="lightbox-img" onClick={(e) => e.stopPropagation()} />
        </div>
      )}

      {showSettings && (
        <div className="settings-overlay" onClick={closeSettings}>
          <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
            <button className="settings-close-btn" onClick={closeSettings}>×</button>
            <h2>⚙️ API 密钥设置</h2>
            
            <div className="settings-group">
              <label>自定义 API Key</label>
              <input 
                type="password" 
                className="settings-input" 
                placeholder="sk-... (如果为空则使用后端 .env 默认配置)"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
            
            <div className="settings-group">
              <label>自定义 Base URL (代理地址)</label>
              <input 
                type="text" 
                className="settings-input" 
                placeholder="https://api.openai.com/v1 (留空则默认)"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
              />
            </div>
            
            <button className="settings-save-btn" onClick={closeSettings}>保存并刷新模型列表</button>
          </div>
        </div>
      )}
      </div>
      
      {/* 右侧边栏 (Right Sidebar - Media Gallery) */}
      <aside className="sidebar-right" style={{ overflow: 'hidden' }}>
        <div className="sidebar-section">
          <h3>🖼️ 媒体缩略图</h3>
          <div className="media-gallery" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginTop: '1rem' }}>
            {extractMedia().length > 0 ? (
                extractMedia().map((src, i) => (
                    <div key={i} className="media-thumbnail" onClick={() => setPreviewImg(src)} style={{ cursor: 'pointer', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--panel-border)', aspectRatio: '1/1' }}>
                        <img src={src} alt={`media-${i}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                ))
            ) : (
                <div style={{ color: "var(--text-secondary)", fontStyle: "italic", fontSize: "0.85rem", gridColumn: 'span 2' }}>
                    暂无生成的图像。
                </div>
            )}
          </div>
        </div>
      </aside>
    </div>
    </div>
  );
}
