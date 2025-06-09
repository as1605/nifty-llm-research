Migrate all agents to use the Google Gemini API instead of Perplexity API. 
We will use Gemini 2.0 Flash model. And google-genai library.
Use "Grounding with Google Search" feature instead of deep research. 
Replace all configurations and keys accordingly. 
Make sure the models inside the prompt configs are updated, change the format of prompt config if required.
Keep a similar prompt text for the system and user prompt.
Use best practices for Gemini API and use their Python SDK

If the promptconfig contains "google_search" in the list of tools, we should insert GoogleSearch() as a tool to the LLM call.
All LLM calling logic should be inside the base agent. The stock_research agent should be calling the functions from base agent which encapsulates the LLM client, and stock_research agent should be concerned with using the correct DB models and creating the correct output in DB.

Use this starter template to understand the SDK, then use in our base agent accordingly. 
```python
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

client = genai.Client()
model_id = "gemini-2.0-flash"

google_search_tool = Tool(
    google_search = GoogleSearch()
)

response = client.models.generate_content(
    model=model_id,
    contents="When is the next total solar eclipse in the United States?",
    config=GenerateContentConfig(
        tools=[google_search_tool],
        response_modalities=["TEXT"],
    )
)

for each in response.candidates[0].content.parts:
    print(each.text)
# Example response:
# The next total solar eclipse visible in the contiguous United States will be on ...

# To get grounding metadata as web content.
print(response.candidates[0].grounding_metadata.search_entry_point.rendered_content)
```


The model_id should be taken from prompt config each time instead of making property of the base agent. We should use the latest google-genai library instead of google-generative-ai


Update the README and cursorrules regarding this change, and document it in the changelog. Also, go through the pyproject.toml and requirements.txt and remove anything which is no longer needed


use genai.Client(api_key=settings.google_api_key). get api key directly from settings, remove it from self


Remove unnecessary parameters like poll_interval max_tokens, max_poll_time from the init, anything going inside the GenerateContentConfig should be inside the prompt config. Use the max tokens and temperatures from the prompt config model, create a field for max_tokens


Use the seeded prompts to estimate the amount of tokens which might be needed for each token, and keep approximately double the limit as the max_tokens in the prompt config. Keep a minimum of 32k as the max output tokens.


If any of the sources URL begins with `https://vertexaisearch.cloud.google.com/grounding-api-redirect`, hit the url and get the location header if it returns a 302 response, otherwise keep the original URL. Store the final URL in the stock forecasts.


add aiohttp to requirements.txt
