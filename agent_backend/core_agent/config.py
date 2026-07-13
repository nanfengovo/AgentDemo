import os

# 零依赖：手动解析同级目录或上级目录的 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# 现在可以安全地拿到了
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not GEMINI_API_KEY and not OPENAI_API_KEY and not DEEPSEEK_API_KEY:
    print("⚠️ 严重警告：未找到任何大模型的 API_KEY，请确保在前端设置或配置了 .env 文件！")
