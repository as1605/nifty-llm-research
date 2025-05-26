Organise this requirement of a LLM Stock research agent into a README, write in passive voice as if listing the features rather than asking to build. Keep a simple format for summary of the flow, and then details of each step.

A build a deep research agent, which will take a prompt to analyse the market news for a particular indian stock and forecast it's price for next 1 week,  1 month,  3 month,  6 months, and  12 months. We want to search the web search news, and financial quote and chart data, and also read the PDFs of investor reports and market analysis too. We will call the script everyday to run for each NSE top 100 stock one by one, and save the results to SQL.

We also want a script which takes the list of predictions (current price, 1 week, 1 month, 3 month, 6 month, 1 year) for all the 100 stocks then composes a basket of 5 best stocks to keep in portfolio for that week. This will run after all the 100 stocks have been analysed that day. This should be mailed using Amazon SES to our email.

Write a:
- Deep Research Agent in Python using OpenAI APIs and Agents and Tools which would run the main query for a stock and return the target prices.
- ⁠A function to save the results of each query to an Amazon Aurora  PostgreSQL Database
- ⁠A script which will read the data of all the stocks from the DB and pass it to an LLM to create the stock basket, and mail it to an email. The basket should also be saved to the DB
