import requests
url = "https://api.deepseek.com/chat/completions"
# Use a missing content field!
headers = {"Authorization": "Bearer dummy", "Content-Type": "application/json"}
payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "You are a bot."},
        {"role": "user"}
    ]
}
print(requests.post(url, headers=headers, json=payload).json())
