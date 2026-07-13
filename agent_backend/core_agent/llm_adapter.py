import os
import requests
import json
import uuid

class LLMResponse:
    def __init__(self, text="", tool_calls=None, error=None):
        self.text = text
        self.tool_calls = tool_calls or []
        self.error = error

def is_google_model(model: str) -> bool:
    google_prefixes = ("gemini", "gemma", "learnlm", "imagen", "veo", "nano", "lyria", "deep-research", "computer-use")
    return model.lower().startswith(google_prefixes)

def get_api_key(model, custom_key=None):
    if custom_key:
        return custom_key
    if is_google_model(model):
        return os.getenv("GEMINI_API_KEY")
    elif model.startswith("deepseek"):
        return os.getenv("DEEPSEEK_API_KEY")
    else:
        return os.getenv("OPENAI_API_KEY")

def get_base_url(model, custom_url=None):
    if custom_url:
        return custom_url
    if is_google_model(model):
        return "https://generativelanguage.googleapis.com/v1beta/models/"
    elif model.startswith("deepseek"):
        return "https://api.deepseek.com"
    else:
        return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

def convert_to_gemini(messages, system_prompt):
    contents = []
    sys_instruction = None
    if system_prompt:
        sys_instruction = {"parts": [{"text": system_prompt}]}
        
    for msg in messages:
        role = msg["role"]
        
        if role == "user":
            parts = []
            content = msg.get("content", [])
            # 兼容旧版本直接存了 parts 的情况
            if not content and "parts" in msg:
                contents.append({"role": "user", "parts": msg["parts"]})
                continue
                
            if isinstance(content, str):
                parts.append({"text": content})
            elif isinstance(content, list):
                for item in content:
                    if item["type"] == "text":
                        parts.append({"text": item["text"]})
                    elif item["type"] == "image_url":
                        url = item["image_url"]["url"]
                        if url.startswith("data:"):
                            header, b64 = url.split(",", 1)
                            mime = header.split(":")[1].split(";")[0]
                            parts.append({"inlineData": {"mimeType": mime, "data": b64}})
            contents.append({"role": "user", "parts": parts})
            
        elif role in ["assistant", "model"]:
            parts = []
            if msg.get("content"):
                parts.append({"text": msg["content"]})
            # 兼容旧版本的 parts
            if not msg.get("content") and "parts" in msg:
                contents.append({"role": "model", "parts": msg["parts"]})
                continue
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    args = tc["function"].get("arguments", "{}")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            args = {}
                    parts.append({"functionCall": {"name": tc["function"]["name"], "args": args}})
            contents.append({"role": "model", "parts": parts})
            
        elif role == "tool":
            args = msg.get("content", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except:
                    args = {"result": args}
            contents.append({"role": "function", "parts": [{"functionResponse": {"name": msg.get("name", "tool"), "response": args}}]})

    return sys_instruction, contents

def gemini_tools_to_openai(gemini_tools):
    def convert_schema(schema):
        if not isinstance(schema, dict):
            return schema
        new_schema = {}
        for k, v in schema.items():
            if k == "type" and isinstance(v, str):
                new_schema[k] = v.lower()
            elif isinstance(v, dict):
                new_schema[k] = convert_schema(v)
            elif isinstance(v, list):
                new_schema[k] = [convert_schema(item) if isinstance(item, dict) else item for item in v]
            else:
                new_schema[k] = v
        return new_schema

    openai_tools = []
    for decl in gemini_tools.get("functionDeclarations", []):
        new_decl = convert_schema(decl)
        openai_tools.append({"type": "function", "function": new_decl})
    return openai_tools

def call_gemini(messages, system_prompt, tools, model, api_key, base_url):
    model_lower = model.lower()
    is_legacy_imagen = model_lower.startswith("imagen")
    is_media_model = any(k in model_lower for k in ["veo", "lyria", "nano banana", "image"]) and not is_legacy_imagen
    
    # Extract the last user message text for media/image generation
    prompt = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            if isinstance(msg["content"], str):
                prompt = msg["content"]
            elif isinstance(msg["content"], list):
                prompt = " ".join([c["text"] for c in msg["content"] if c["type"] == "text"])
            break

    if is_legacy_imagen:
        # 用户要求：将所有旧版 Imagen 强制映射到 Imagen 4 Fast 以尝试利用 25 次免费额度
        override_model = "imagen-4.0-fast-generate-001"
        url = f"{base_url}{override_model}:predict?key={api_key}"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1}
        }
        res = requests.post(url, json=payload)
        data = res.json()
        if "error" in data:
            return LLMResponse(error=data["error"].get("message", str(data["error"])))
        
        if "predictions" in data and data["predictions"]:
            image_data = data["predictions"][0].get("bytesBase64Encoded", "")
            if image_data:
                return LLMResponse(text=f"![Generated Image](data:image/jpeg;base64,{image_data})")
        return LLMResponse(error=f"Gemini Predict API 返回异常: {data}")

    if is_media_model:
        # Route to interactions API for media models
        interactions_url = base_url.replace("/models/", "/interactions")
        if not interactions_url.endswith("interactions"):
            if interactions_url.endswith("/"):
                interactions_url = interactions_url[:-1]
            interactions_url = f"{interactions_url}/interactions"
        url = f"{interactions_url}?key={api_key}"
                
        payload = {
            "model": model,
            "input": [{"type": "text", "text": prompt}]
        }
        
        res = requests.post(url, json=payload)
        data = res.json()
        if "error" in data:
            return LLMResponse(error=data["error"].get("message", str(data["error"])))
            
        if "output_image" in data:
            image_data = data["output_image"].get("data", "")
            if image_data:
                # 返回 Base64 编码的图片，Markdown 格式，这样前端就可以解析出来了
                return LLMResponse(text=f"![Generated Image](data:image/jpeg;base64,{image_data})")
        return LLMResponse(error=f"Gemini Interactions API 返回异常: {data}")

    sys_instr, contents = convert_to_gemini(messages, system_prompt)
    url = f"{base_url}{model}:generateContent?key={api_key}"
    payload = {"contents": contents}
    if sys_instr:
        payload["system_instruction"] = sys_instr
    if tools:
        payload["tools"] = [tools]
        
    res = requests.post(url, json=payload)
    data = res.json()
    if "error" in data:
        return LLMResponse(error=data["error"].get("message", str(data["error"])))
        
    if "candidates" not in data or not data["candidates"]:
        return LLMResponse(error=f"Gemini API 返回异常: {data}")
        
    ai_part = data["candidates"][0]["content"]["parts"][0]
    if "functionCall" in ai_part:
        args = ai_part["functionCall"].get("args", {})
        return LLMResponse(tool_calls=[{
            "id": "call_" + str(uuid.uuid4())[:8],
            "type": "function",
            "function": {
                "name": ai_part["functionCall"]["name"],
                "arguments": json.dumps(args)
            }
        }])
    else:
        return LLMResponse(text=ai_part.get("text", ""))

def call_openai(messages, system_prompt, tools, model, api_key, base_url):
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload_msgs = []
    if system_prompt:
        payload_msgs.append({"role": "system", "content": system_prompt})
        
    openai_tools = gemini_tools_to_openai(tools) if tools else None
    
    for msg in messages:
        sanitized_msg = dict(msg)
        if isinstance(sanitized_msg.get("content"), list):
            # If the list only contains text (no images), flatten it to a string for maximum compatibility
            has_image = any(item.get("type") == "image_url" for item in sanitized_msg["content"])
            if not has_image:
                text_parts = [item.get("text", "") for item in sanitized_msg["content"] if item.get("type") == "text"]
                sanitized_msg["content"] = "\n".join(text_parts)
        payload_msgs.append(sanitized_msg)
    
    payload = {
        "model": model,
        "messages": payload_msgs,
    }
    if openai_tools:
        payload["tools"] = openai_tools
        
    with open("payload_debug.json", "w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    res = requests.post(url, headers=headers, json=payload)
    data = res.json()
    
    if "error" in data:
        return LLMResponse(error=data["error"].get("message", str(data["error"])))
        
    if "choices" not in data or not data["choices"]:
        return LLMResponse(error=f"OpenAI 格式返回异常: {data}")
        
    msg = data["choices"][0]["message"]
    if msg.get("tool_calls"):
        for tc in msg["tool_calls"]:
            if not isinstance(tc["function"]["arguments"], str):
                 tc["function"]["arguments"] = json.dumps(tc["function"]["arguments"])
        return LLMResponse(tool_calls=msg["tool_calls"])
    else:
        return LLMResponse(text=msg.get("content", ""))

def call_imagen(messages, model, api_key, base_url):
    prompt = ""
    for m in reversed(messages):
        if m["role"] == "user":
            content = m.get("content", "")
            if isinstance(content, list):
                prompt = next((c["text"] for c in content if c.get("type") == "text"), "")
            elif isinstance(content, str):
                prompt = content
            break
            
    url = f"{base_url}{model}:predict?key={api_key}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1}
    }
    res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
    data = res.json()
    if "error" in data:
        return LLMResponse(error=data["error"].get("message", str(data["error"])))
    if "predictions" in data and len(data["predictions"]) > 0:
        b64 = data["predictions"][0].get("bytesBase64Encoded")
        if b64:
            return LLMResponse(text=f"![Generated Image](data:image/png;base64,{b64})")
    return LLMResponse(error=f"Imagen 接口无有效返回: {data}")

def call_huggingface(messages, model, api_key):
    prompt = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                prompt = next((c["text"] for c in content if c.get("type") == "text"), "")
            elif isinstance(content, str):
                prompt = content
            break

    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": prompt}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        if res.status_code == 200:
            import base64
            image_data = base64.b64encode(res.content).decode("utf-8")
            return LLMResponse(text=f"![Generated Image](data:image/jpeg;base64,{image_data})")
        else:
            try:
                err = res.json()
                return LLMResponse(error=f"HuggingFace API 报错: {err}")
            except:
                return LLMResponse(error=f"HuggingFace API 错误状态码: {res.status_code}, {res.text}")
    except Exception as e:
        return LLMResponse(error=f"连接 HuggingFace 发生网络/SSL 错误: {str(e)}\n\n(可能由于 macOS 系统自带 Python 的 LibreSSL 版本过低，无法与 HuggingFace 建立安全连接)")

def call_siliconflow_image(messages, model, api_key):
    prompt = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                prompt = next((c["text"] for c in content if c.get("type") == "text"), "")
            elif isinstance(content, str):
                prompt = content
            break

    url = "https://api.siliconflow.cn/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    real_model = model.replace("siliconflow/", "")
    payload = {
        "model": real_model,
        "prompt": prompt,
        "image_size": "1024x1024",
        "response_format": "b64_json"
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        data = res.json()
        if res.status_code == 200:
            if "data" in data and len(data["data"]) > 0:
                b64 = data["data"][0].get("b64_json") or data["data"][0].get("url")
                if b64:
                    if b64.startswith("http"):
                        return LLMResponse(text=f"![Generated Image]({b64})")
                    return LLMResponse(text=f"![Generated Image](data:image/png;base64,{b64})")
        return LLMResponse(error=f"硅基流动 API 报错: {data}")
    except Exception as e:
        return LLMResponse(error=f"硅基流动 API 网络错误: {str(e)}")

def call_llm(messages, system_prompt=None, tools=None, model="gemini-3.1-flash-lite", api_key=None, base_url=None) -> LLMResponse:
    key = get_api_key(model, api_key)
    url = get_base_url(model, base_url)
    
    if not key:
        # 针对 HuggingFace 进行特殊处理
        if model.startswith("black-forest-labs/"):
            import os
            hf_key = api_key or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
            if not hf_key:
                return LLMResponse(error="⚠️ 未找到 HF_TOKEN，请在 .env 文件中设置 HF_TOKEN 以使用 HuggingFace 模型！")
            return call_huggingface(messages, model, hf_key)
            
        # 针对硅基流动进行特殊处理
        if model.startswith("siliconflow/"):
            import os
            sf_key = api_key or os.getenv("SILICONFLOW_API_KEY")
            if not sf_key:
                return LLMResponse(error="⚠️ 未找到 SILICONFLOW_API_KEY，请在 .env 文件中设置它以使用硅基流动模型！")
            return call_siliconflow_image(messages, model, sf_key)
            
        return LLMResponse(error=f"⚠️ 未找到 {model} 对应的 API Key，请在前端设置或配置后端 .env 文件！")
        
    if model.startswith("imagen"):
        return call_imagen(messages, model, key, url)
    elif model.startswith("black-forest-labs/"):
        return call_huggingface(messages, model, key)
    elif model.startswith("siliconflow/"):
        return call_siliconflow_image(messages, model, key)
    elif is_google_model(model):
        return call_gemini(messages, system_prompt, tools, model, key, url)
    else:
        return call_openai(messages, system_prompt, tools, model, key, url)
