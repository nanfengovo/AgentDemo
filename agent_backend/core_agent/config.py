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

if not GEMINI_API_KEY:
    print("⚠️ 严重警告：未找到 GEMINI_API_KEY，请确保项目根目录下存在 .env 文件并且已经配置！")

# 动态拼接模型请求 URL
def get_model_url(model: str = "gemini-3.1-flash-lite") -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
