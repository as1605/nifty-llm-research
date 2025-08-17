Find the capabilities of the yfinance for analysing smallcap stocks. Try a few smallcase stocks and see what all information can be provided by the yfinance reliably. Then, modify the @stock_research.py  to provide the LLM the information from yfinance about that stock in JSON format. Update the prompt @seed_prompts.py  to inform the LLM about this data too, and also tell it to use google for further information and market sentiment about the company which is not mentioned in our data.
Create a service for yfinance with functions to get ltp (for rebalancing), stock info (for research)

Use dir function in python to explore the functions provided yfinance recursively, and check for underlying functions too in them


Make the @zerodha_service.py  use the yfinance service for ltp instead of importing yfinance directly @get_ltp 


In the yfinance service, append .NS to the stock to be compatible with the API which takes .NS for NSE. Make sure the usages also take note of this
Attach .NS to the symbol only if any other suffix with . is not present @_normalize_symbol

Format the shareholder % in %age instead of fraction when sending to LLM


When sending sources in the response, warn the LLM that the vertex source links should be valid URLs and not be longer than 1000 characters @seed_prompts.py


Fix Cancelled error after server is stopped. Stop it in a way that does not kill the main program


Extract out the fastapi server code into a different file in services


Move the config into src, update imports accordingly