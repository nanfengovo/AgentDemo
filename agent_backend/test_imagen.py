import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={key}"
payload = {
    "model": "gemini-3.1-flash-image",
    "input": [{"type": "text", "text": "a cute cat"}]
}
res = requests.post(url, json=payload)
print(res.status_code)
data = res.json()
if "output_image" in data:
    print("Success! Image data length:", len(data["output_image"].get("data", "")))
else:
    print(json.dumps(data, indent=2))
