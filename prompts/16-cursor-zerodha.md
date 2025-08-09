Implement a script to rebalance the stock portfolio by taking in a JSON from docs/baskets and connecting to Zerodha Kite API.

Access Token flow:
First check if the access_token is not present in the database, or is invalid. If invalid, delete the token from db
Make a service for getting the zerodha access_token. Spawn a simple fastapi server at localhost:8080 . This will be the redirect server where Zerodha will send the request_token in query param.
Give the user a clickable link in the console where they can complete the login flow. Once we receive the request token, get the access token using client secret then save it in the db in an encrypted format.

Rebalancing flow:
User will give the json as file path in argument, it will have the intended % for each stock. Fetch the current holdings and positions of the portfolio using access token, and calculate the required change for each stock. The total value of portfolio should be holdings, positions and margins/funds. If a stock is not present in basket but is there in the portfolio, then set it to 0. Among the stocks that are already present but different percentage to total portfolio, try to prioritise those with most deficit and place orders for them.


Failed to get quotes: Insufficient permission for that call.
use kite.ltp instead of kite.quote


When placing orders, if the current time is after 3:30 PM or before 9:15 AM, wait till 9:14 AM IST, and then keep retrying the orders systematically


Add a quiet mode which does not ask for unnecessary interactive inputs or confirmations, and picks the defaults automatically, for example yes or confirm for actions, and taking the 1st user if logged in
 @rebalance_portfolio.py @zerodha_service.py


In the configuration, allow to give a comma separated list for GEMINI key, and in case we get 429 on one llm request, switch the key to the other one and retry


When portfolio is generated, automatically update the index.md to reflect the new link on the github page @generate_portfolio.py


Go through all scripts and make sure the imports are valid, and they can be run by a python3 scripts/name.py type of command. Then, write a run_analysis.sh file in the root folder, and make it run the analysis of NIFTY SMALLCAP 250 twice, then generate portfolio, commit the docs and push to git, and also rebalance the portfolio

Rename it to run.sh 
Put the logs of the python scripts in data/logs folder with appropriate naming. Output the echo in the console
Make it do live ordering by default @run_analysis.sh 


@next_9_14_ist  if the current time is between 9:14 and 9:15, the target should be 0 and we should start retrying immediately


Verify the README and update with new changes and logic. Add brief description of the rebalancing too, and link the readme of rebalancing


In the README_REBALANCING, also give steps on how to setup the zerodha developer account correctly, and to use the correct callback endpoint in configuration. Attach relevant docs