What all news, websites, documents and articles and content should be studied to predict an indian NSE listed stock's price for the next week, next month or next year? Give a comprehensive list of all such sources of information which can help to forecast the price of a stock, and explain how they can help. Make sure all possible factors like competitor analysis, new launches or initiatives, and government, geopolitical and economic factors are taken into account. Go through multiple such sources which are available online, and filter out redundant ones and pick the ones with the most appropriate information.


we are focused on a particular stock. we want time horizon for all 3, short term medium term long term. We want only free resources which can be accessed by the perplexity deep research API


Find best practices for Perplexity Sonar Deep Research API, and how to write prompts for it, and how to optimise the cost for each call, without wasting many tokens.


What is temperature, and how is the perplexity deep research, and reasoning tokens calculated for billing, and what factors can increase or decrease them?


Using all the above information, we have to write a prompt for forecasting a target price for a particular NSE stock, using Perplexity's Sonar Deep Research API. It should also optimise the token cost, and try to cost less for each query, by focusing only on relevant data as described above. Utilise both system prompt and user prompt. Make sure the model knows it has to focus on financial technical and fundamental research 
- It should first fetch the technical and fundamental analysis numbers, like stock quote and previous price trend/charts
- It should read market news and find all relevant documents and strategies for that stock, and the industry and economy
- It should also parse the reports where necessary and read through them to identify important facts for the future of that stock
- After all the analysis, it should set target prices for 1 week, 1 month, 3 months, 6 months and 1 year taking into account the found factors. It should also give the reasoning for each forecast as a summary in 1 line, and also list the web sources in https url format, for that particular forecast and target price.
- Final output of the Perplexity Sonar Deep Research LLM should be in JSON format as given below
{{
    "current_price": float,
    "market_cap": float,
    "pe_ratio": float,
    "volume": float,
    "industry": str,
    "forecasts": [
        {{
            "timeframe": str,    // "1w", "1m", "3m", "6m", "1y"
            "target_price": float,
            "reasoning": str,
            "sources": list[str]  // List of https URLs as sources
        }}
    ]
}}


Now write a prompt for Perplexity Sonar Reasoning API, to go through the forecasts for 20 such stocks in a similar format, and then generate a portfolio by picking best 5 stocks from them. It can give each stock a weight of 0.1 to 0.3 in the portfolio, by taking into account the risk and overlap. It should provide a list of stocks along and estimate an expected monthly gain from them. Understand how the costing would work, and use the best practices for this prompt too, with a separate system and user prompt.
Make it output a JSON of format 
{
stocks_picked: list[str] (List of the stocks which we are picking),
weights: dict (a dictionary of stock to its ratio in the portfolio, should sum to 1)
reason_summary: str (in under 200 words)
expected_gain_1m: float (expected gain in % in 1 month)
}
Make sure your message has valid utf-8 string characters only and no special symbols or emojis