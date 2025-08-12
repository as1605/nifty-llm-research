@models.py Modify the PromptConfig to hold a `config` field which will be a dict holding the config settings which can be passed to the Gemini model. It should have response_schema which would be a dict holding the model dump of the response object, response_mime_type, thinkingBudget, temperature, max_tokens and all other fields which should be passed as metadata along with the request. Also add any other important field required by Gemini


Adjust base agent to use the config from the promptconfig, and extract and pass each field properly to the LLM call. 

Follow the structure of google.genai GenerateContentConfig, and load the parameters properly from the PromptConfig into it. Make sure the thinking budget, temperature, response schema, response mime type are passed correctly. 

thinking_config should have thinking_budget as the parameter, and also have include_thoughts. thinking_config should have type ThinkingConfig

The system_instruction should be a part of the GenerateContentConfig instead of the messages


Read the stock_research_forecast prompt from seed_prompts, and update it according to the new config format. Make sure it is compatible with the BaseAgent too. include_thoughts should be false. Keep thinkingBudget of 12*1024, temperature of 0.1. Keep the param as TICKER instead of STOCK_TICKER
response_mime_type = "application/json": Ensures the output is valid JSON.
response_schema: should be List[Forecast].model_json_schema()
do not put any unnecessary configs which are not required or not understood

Read the portfolio_basket prompt from seed_prompts, and update it according to the new config format. Make sure it is compatible with the BaseAgent too. include_thoughts should be false. Keep thinkingBudget of 18*1024, temperature of 0.1. Keep the original params which were in list, and update the prompt to use them
response_mime_type = "application/json": Ensures the output is valid JSON.
response_schema: should be Basket.model_json_schema()
do not put any unnecessary configs which are not required or not understood
Update the prompt with the original params as in the list


Update the stock research agent to use the new output format of the LLM as defined in seed prompts, and also make it compatible with the new behaviour of base agent. let the stock research agent modify the list of forecasts directly from the output if needed and save into the db. Remove any functions which are no longer needed. 

We will still need the process sources function and resolve vertex url, as the URLs provided may be of the vertex. Make sure to parse the forecast_date correctly, checking the format as defined in the seed prompt (YYYY-MM-DD), and log a warning if it is different from current date + days by more than 1 or 2 days

Forecast object model should still include invocation_id, although it will get that from the code and not from the LLM.

analyse_stock should return only a list of forecasts for that stock, do not create a new dict. _get_recent_forecasts is returning a list of forecasts, use this for the analyze function directly

Remove any unused code from the stock research agent. make sure everything should be working


Update the portfolio agent to use the new output format of the LLM as defined in seed prompts, and also make it compatible with the new behaviour of the base agent. The LLM will output the Basket directly. Validate it and save to the DB.

Remove any unused functions which are not needed. Make sure the whole code flow should be working according to the new changes

The Basket model should also have an invocation_id, update the db.models accordingly. This should be set in the portfolio agent while saving the model


While saving the outputs finally, the generate_portfolio script should use indian timezones. Do not change the markdown format. Make the code complaint with new changes. 

Do not use any external module for timezone, use builtin python only. 

The result is an object of Basket model, update the usage accordingly. 

Use same value of datetime.now for both the file name and file content


Analyse models, and the queries made on each of them. Update indices to optimise the queries.

Verify if the Order model is used anywhere, then delete it


The setup_db script should update all previous PromptConfigs to have default=False, then it should invoke the seed_prompts script


Remove unnecessary db call of historical_forecasts from analyze_stocks script


Create a ListForecast model instead of List[Forecast], and update the usage in the code everywhere. Keep it in models too, but do not insert in the database.


The Basket model should include a stock_sources field which is a dictionary of the stock ticker to a list[str] of the sources which were used to predict its price. Set the value in the portfolio agent using the sources of the underlying Forecasts


Remove mime type from the prompt configs. Remove default values inside the config field from the model PromptConfig.


In stock_research agent, we should first parse the json from the response using the _parse_json_response then construct the ListForecast object from it. 

In case a particular stock analysis fails, except it as an log error in the analyze_stocks script, instead of throwing the exception


In the _process_sources, hit all URLs to check the response status. If it gives 302, follow the redirect and save the final location. If it gives 400 or 404 or any 5xx error, ignore this link and log a warning. Allow all other status codes


Fix the error handling logic. The stock research agent may raise errors, but the script should catch errors and log that stock which failed instead of breaking the flow of execution of all stocks


In the analyze_stocks script, add a flag of --workers -w which will have the number of tasks which can be processed parallely. default value should be 10.


Create a BasketStock model, which will have the fields stock_ticker, weight, sources. Modify the Basket model to have a stocks field as a list of BasketStock objects, and use this everywhere in the code.