Instead of OpenAI, use Perplexity `sonar-deep-research` model for researching about the given stock, and `sonar-reasoning-pro` for finally picking the stock basket by analysing the summaries and forecasts for each stock along with their sources. Use the deep research model directly to get the web sources and parse them, do not create your own agent for getting the web search and documents or finance news. Learn about the capabilities and documentation for both models online and use them appropriately. 
@agents

Do not use yahoo finance.

Make the handling of Invocations model a part of the BaseAgent rather than in the specific agent like portfolio or stock research

put store_invocation inside get_completion. 
Remove OpenAI dependencies. Use perplexity api key configurations in settings.py

Use perplexity's async API instead of sync api
Example code: 

# Submit Request
```python
import requests

url = "https://api.perplexity.ai/async/chat/completions"

payload = {
    "request": {
        "model": "sonar-deep-research",
        "messages": [
            {
                "role": "user",
                "content": "Provide an in-depth analysis of the impact of AI on global job markets over the next decade."
            }
        ]
    }
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

# Poll Until Completion
```python
import requests
import time

def poll_request_status(request_id, token):
    url = f"https://api.perplexity.ai/async/chat/completions/{request_id}"
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get('status') == 'COMPLETED':
            return data.get('response')
        time.sleep(1)

# Usage:
# result = poll_request_status("784312ac-b8fd-405f-99fa-9bcbf48865bb", "<token>")
# print(result)
```