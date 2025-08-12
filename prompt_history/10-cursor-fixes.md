@analyze_stocks.py Use requests instead of aiohttp for getting data from NSE API. 
The response object will be a json of format where the data will have a list of details for each stock.
{..., "data": [{"lastPrice": ..., "meta": {"symbol": "...", "companyName": "...", "industry": "..."}}]}
If the companyName is missing in the meta, ignore that stock and go to others.

Remove the parameter of market_cap from @Stock 


In analyze_stock inside stock_research agent, the result will be having a list of forecasts in the format 
```json
{
  "forecasts": [
    {
      "timeframe": "1w",
      "target_price": float,
      "reasoning": string,
      "sources": [string, …]  // only HTTPS URLs
    },
    {
      "timeframe": "1m",
      "target_price": float,
      "reasoning": string,
      "sources": [string, …]
    },
    {
      "timeframe": "3m",
      "target_price": float,
      "reasoning": string,
      "sources": [string, …]
    },
    {
      "timeframe": "6m",
      "target_price": float,
      "reasoning": string,
      "sources": [string, …]
    },
    {
      "timeframe": "1y",
      "target_price": float,
      "reasoning": string,
      "sources": [string, …]
    }
  ]
}
```
Parse it accordingly and create multiple forecasts from the same result


Also, process the sources to resolve the urls before saving the forecasts


In the call to self.client.models.generate_content, handle google.genai.errors.ServerError 503 errors of the google gemini client with an exponential backoff retry as appropriate. Start with 1 second delay and retry 10 times reaching upto 5 minute of time


In case the NSE api call fails, ask the user to open https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050 or the appropriate URL in their browser to allow IP filtering


Calculate the gains for the forecast by comparing with the current price for that Stock before saving it in the Forecast object. @analyze_stock 


STOCK_DATA passed to the portfolio prompt should be a JSON of the forecasts rather than a dataframe. Pass the stock_data directly rather than converting it to a df. 

Remove the _id and invocation_id fields in the forecast before passing it to the LLM, handle this in the python logic before passing the parameters. 

Convert the date time object fields to a simple date field, before passing to LLM. Remove created_time and modified_time, just keep the forecast_date


Rather than prompt_config.user_prompt.format(**params), replace each param key (along with {}) with its value using string replace function, and also do for both system and user prompt.


Remove all plotting and emailing logic. Update this in the documentation and configuration settings etc too. Remove the usage from scripts too. Delete the empty folders. Remove tests folder


While naming the outputs to docs/basket, make the date-time easier to read by using 3 letter Month, and time in only hour and minute. Escape the special character and space with _. Show example of what could be a potential file name after this change. Keep some separation between the datetime and the N and K parameters so they do not look mixed up 


Remove BaseMongoModel from db models.
Restore the weights of the Basket to be a dict of string to float instead of a list
Instead of zipping the stock ticket and weight, use the dict in @save_basket_outputs. 
Output the overall gain separately for the whole basket, without multiplying by 100. 
Do not give Expected 1M gain for each stock, it is for the whole basket
Add % sign to the expected 1M gain, and keep only 2 digit of precision
Remove Analysis Period

In the seed_prompt of the portfolio_basket, do not put the condition to limit the ratio from 0.1 to 0.3.


In case of the NSE errors, ask the user to open the referer url rather than the targer url in the browser


Rewrite the env.template according to the settings which are required for the configuration
