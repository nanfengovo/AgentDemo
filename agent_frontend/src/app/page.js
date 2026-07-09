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
  const [previewImg, setPreviewImg] = useState(null); // 图片预览状态
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

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

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

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    const currentImages = [...images]; // 保存当前上传的图片
    setMessages(prev => [...prev, { role: "user", content: userMsg, images: currentImages }]);
    setInput("");
    setImages([]); // 发送后清空图片附件
    setLoading(true);

    try {
      // 通过 Fetch API 连接后端的流式通道
      const response = await fetch("http://127.0.0.1:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMsg, 
          session_id: "cross_platform_client",
          model: model,
          images: currentImages
        }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      // 初始化一个空的 AI 消息，默认进入思考模式
      setMessages(prev => [...prev, { role: "ai", content: "", rawChunks: [], inThoughtProcess: true }]);

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
      setMessages(prev => [...prev, { role: "ai", rawChunks: [{ type: "text", text: "❌ 网络错误：无法连接到本地大盘网关，请确保 FastAPI 后端运行在 8000 端口。" }] }]);
    } finally {
      setLoading(false);
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
        <div key="actions" className="message-actions">
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

    return elements;
  };

  return (
    <div className="main-container">
      <header className="header glass-panel">
        <div className="header-title">
          <div className="status-indicator"></div>
          QuantTrading Agent Terminal
        </div>
        <select 
          className="model-selector" 
          value={model} 
          onChange={(e) => setModel(e.target.value)}
          disabled={loading}
        >
          <option value="gemini-3.1-flash-lite">Gemini 3.1 Flash Lite (主力)</option>
          <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</option>
          <option value="gemini-3.5-flash">Gemini 3.5 Flash (最强)</option>
          <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
          <option value="gemini-3-flash">Gemini 3 Flash</option>
        </select>
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
                <div>{msg.content}</div>
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
            placeholder="输入指令或上传图表要求分析 (支持 Ctrl+V 粘贴图片)..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            onPaste={handlePaste}
            disabled={loading}
          />
          <button className="send-btn" onClick={handleSend} disabled={loading || (!input.trim() && images.length === 0)}>
            Send
          </button>
        </div>
      </footer>

      {previewImg && (
        <div className="lightbox-overlay" onClick={() => setPreviewImg(null)}>
          <button className="lightbox-close">×</button>
          <img src={previewImg} alt="Preview" className="lightbox-img" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </div>
  );
}
