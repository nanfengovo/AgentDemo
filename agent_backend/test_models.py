import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
models = res.json().get("models", [])
for m in models:
    name = m["name"].replace("models/", "")
    methods = m.get("supportedGenerationMethods", [])
    if "imagen" in name.lower() or "predict" in methods:
        print(f"{name}: {methods}")
