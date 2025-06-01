Do not run reasoning model for stock research, use only the research model. And ask the research model to also give the predictions of 1w 1m 3m 6m 12m, along with reason summaries for each. It should output 5 objects of Forecast, where forecase date is the date for which we have the target price (7 days ahead of today, 30 days ahead of today... etc)


Update the @stock_research.py  accordingly to parse and save the forecasts. It should fill all the fields in the @Forecast  model according to the schema, including gain and days ahead as a number. If needed, also update the stock_research prompt in @seed_prompts.py 


@seed_prompts.py @stock_research.py @models.py 
The LLM should not output the exact ISO timestamp, it should only give the window as 1w 1m 3m 6m 1y, we should deduce the timestamp from it. It should also include the sources for each forecast as web links in https format, and all reasons should be in a single text field.
Ensure the output is only a JSON and no text.  In case the JSON parsing fails, try to split by ``` 3 backticks, then the next { and } pair to get the JSON from the markdown response.


seed the prompt only a default prompt of the same name is not present, also use the model_dump function instead of dict. Use upsert operation


move @_parse_json_response  to @base.py  and make it usable by other codes like @portfolio.py  too.


fix seaborn error
    | OSError: 'seaborn' is not a valid package style, path of style file, URL of style file, or library style name (library styles are listed in `style.available`)


@stock_research.py @base.py @scripts Add more logging to the script so we know what the code is doing especially in the critical or time taking steps. for example. when the API calls are made and response is received, and a brief of each forecast like how much gains it is predicting for that stock


fix errors in the @plotter.py  and make sure each key is valid, and all are up to date.


Add a fallback logic that if a forecast is already present for a stock created this day, then use it instead of calling the LLM again. keep a --force flag in the script and in the code as a optional argument to the function, with default value as false. If force is off, the code should use the previous forecast with creation date under 12h ago if it exists, otherwise then it should make the LLM call. If force is on, it should always make LLM call for each invocation. Ensure this is logged too in the console. @stock_research.py