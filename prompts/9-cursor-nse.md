In analyse_stocks.py, create a function which can get the list of stocks from the NSE API and store them as Stock objects.
Use the following headers and referrer to make the request. Allow the index to be taken as a parameter. The function should update the data for each stock in the database, and also return the list of the stock tickers in that index as a list of string.
Add "index" as a parameter to the analyze_stocks script, make the default value as "NIFTY 50"
requests.get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050", headers={
    "Referer": "https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY%2050",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
})
Further, remove the updation of the Stock db from the stock_research agent, and also from the prompt we do not require those fields anymore.


Keep "index" of a stock as a list of string, as each stock may belong to multiple indices


Add a fallback mechanism to fetch_nse_stocks. First check the Stocks db to see if there are stocks of that index. If there is atleast 1 stock, return the list of indices, otherwise fetch it from NSE. Rather than a single force parameter, add force-nse and force-llm parameters. force-llm will be the old force parameter.
If force-nse is true, then it should fetch the list from NSE, and if there are stocks in the db which were previously in that index, but are no longer in the latest response, that index should be removed from their indices list.


In the base_agent, The invocation_time of each Invocation object should be the time before each LLM call is made, and the result_time should be the time after we have got the response. Make sure to use latest python datetime function `datetime.now(timezone.utc)` instead of the deprecated `datetime.utcnow`, replace it with everywhere it is used. Scan other files where datetime.utc now is used and update them too


Remove the unused parameters   "current_price": float,
  "market_cap": float,
  "pe_ratio": float,
  "volume": float,
  "industry": string,
from the seeded prompt, and make sure these are not used in the code too. Removed unused imports everywhere in the code.


Move the logic of fetching the forecasts from @generate_portfolio.py  script to the @portfolio.py  agent. Rather than passing the list of stocks, pass 4 parameters: index, since_time, filter_top_n, basket_size_n. We will be querying the Forecast collection and passing it to the LLM using "portfolio_basket" PromptConfig and define in @seed_prompts.py 
- index: this should be the index we want to find the forecasts. We will first find the Stock objects which have this string in indices array, then we will search for those tickers in forecasts.
- since_time: We want to get the forecasts which were created after since_time
- filter_top_n: We will pass the top `filter_top_n` gain stocks to the LLM and ask it to choose the best `basket_size_n` stocks from them. To find the top N stocks, we will compute the average gain of each stock ticker among the selected forecasts of various windows, and then pick the highest N from them. Add this to the PromptConfig as a param rather than hardcoding the value 20.
- basket_size_k: We should pass this to the PromptConfig instead of hardcoding the value 5. If the length of the output from LLM differs from this, log a warning.

In the generate_portfolio script, add cli params for each parameter, and keep default value of index to NIFTY 50, since_time to current time - 1 day, filter_top_n to 20 and basket_size_k to 5


Make sure the naming for basket_size is consistent to basket_size_k or BASKET_SIZE_K in prompt.

Compute the top N average gain stocks using a MongoDB query/aggregation itself by grouping the gains by the ticker and selecting top 20 tickers, rather than doing that in the python logic.

The output of the @_get_top_stocks  should give ALL the forecasts for the top N selected stocks, as a list of forecast object


Keep the send_email as a cli param and keep it to false by default. If it is false, simply print a well-formatted message in the console instead of sending email. The resulting stock basket from the output of portfolio should be saved in both a JSON and Markdown table format in docs/baskets directory. It should be named as `docs/baskets/{index}-{since (formatted for filesystem compatibility)}-{n}-{k}.{json/md}`


Update the documentation to reflect these changes. Change NIFTY top 100 stocks to any NIFTY index. Emphasise the repository visitors to read the prompts folder to understand how the code was written. Also ask them to check the docs/baskets directory to see outputs.

Ask them to read the `prompts/` directory to see the cursor prompts which were used for vibe coding this project, as a proof of authenticity.
