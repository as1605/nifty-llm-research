Optimise the script for NIFTY NEXT 50 instead of NIFTY SMALLCAP 250


shortlist 20 stocks from 50 and finally make basket of 5 of them only


When multiple Gemini API Keys are present, use them evenly for making calls, so when multiple workers are making calls concurrently, different keys are being used. for example if we have 2 keys and 10 workers, 5 of them use key1 and 5 use key2


Change the prompt to make predictions for only 7 days window instead of other days


Review the prompts to make sure they are perfect for picking 5 best stocks (along with weights) from NIFTY NEXT 50 for holding in a period of 1 week, make sure the LLM considers all data before making a price target, and utilises both the given stock data and google search tool properly.

Do not specify NIFTY NEXT 50 in the prompt. Make sure the LLM processes various types of data from the google search tool and also goes deeper into reading the documents and news for the stocks rather than just headlines


The reason_summary should be longer, 50-200 words.


When finally generating the portfolio from the forecasts, use gemini-2.5-pro model, with appropriate reasoning capabilities. provide it the 7 day forecast of each stock along with the reason_summary, and brief financial data like LTP and OHLC of last 5 trading days.


Go through the entire process of run.sh and make sure each script works perfectly and there are no errors when passing data around between the steps


Remove redundant code which is not being used. Analyse carefully that the code being removed is not used anywhere