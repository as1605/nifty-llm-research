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


Use the following documentation for computing the total portfolio value. The weight of each stock will be taken relative to the total value.
```
Portfolio¶
A user's portfolio consists of long term equity holdings and short term positions. The portfolio APIs return instruments in a portfolio with up-to-date profit and loss computations.

type	endpoint	 
GET	/portfolio/holdings	Retrieve the list of long term equity holdings
GET	/portfolio/positions	Retrieve the list of short term positions
PUT	/portfolio/positions	Convert the margin product of an open position
GET	/portfolio/holdings/auctions	Retrieve the list of auctions that are currently being held
Holdings¶
Holdings contain the user's portfolio of long term equity delivery stocks. An instrument in a holdings portfolio remains there indefinitely until its sold or is delisted or changed by the exchanges. Underneath it all, instruments in the holdings reside in the user's DEMAT account, as settled by exchanges and clearing institutions.

curl "https://api.kite.trade/portfolio/holdings" \
    -H "X-Kite-Version: 3" \
    -H "Authorization: token api_key:access_token"
{
  "status": "success",
  "data": [
    {
      "tradingsymbol": "AARON",
      "exchange": "NSE",
      "instrument_token": 263681,
      "isin": "INE721Z01010",
      "product": "CNC",
      "price": 0,
      "quantity": 1,
      "used_quantity": 0,
      "t1_quantity": 0,
      "realised_quantity": 1,
      "authorised_quantity": 0,
      "authorised_date": "2025-01-17 00:00:00",
      "authorisation": {},
      "opening_quantity": 1,
      "short_quantity": 0,
      "collateral_quantity": 0,
      "collateral_type": "",
      "discrepancy": false,
      "average_price": 161,
      "last_price": 352.95,
      "close_price": 352.35,
      "pnl": 191.95,
      "day_change": 0.5999999999999659,
      "day_change_percentage": 0.17028522775648244,
      "mtf": {
        "quantity": 1000,
        "used_quantity": 0,
        "average_price": 100,
        "value": 100000,
        "initial_margin": 0
      }
    },
    {
      "tradingsymbol": "SBIN",
      "exchange": "BSE",
      "instrument_token": 128028676,
      "isin": "INE062A01020",
      "product": "CNC",
      "price": 0,
      "quantity": 16,
      "used_quantity": 0,
      "t1_quantity": 0,
      "realised_quantity": 16,
      "authorised_quantity": 0,
      "authorised_date": "2025-01-17 00:00:00",
      "authorisation": {},
      "opening_quantity": 16,
      "short_quantity": 0,
      "collateral_quantity": 0,
      "collateral_type": "",
      "discrepancy": false,
      "average_price": 801.78125,
      "last_price": 762.45,
      "close_price": 766.4,
      "pnl": -629.2999999999993,
      "day_change": -3.949999999999932,
      "day_change_percentage": -0.5153966597077155,
      "mtf": {
        "quantity": 0,
        "used_quantity": 0,
        "average_price": 0,
        "value": 0,
        "initial_margin": 0
      }
    }
  ]
}
Response attributes¶
attribute	 
tradingsymbol
string
Exchange tradingsymbol of the instrument
exchange
string
Exchange
instrument_token
uint32
Unique instrument identifier (used for WebSocket subscriptions)
isin
string
The standard ISIN representing stocks listed on multiple exchanges
t1_quantity
int64
Quantity on T+1 day after order execution. Stocks are usually delivered into DEMAT accounts on T+2 ?
realised_quantity
int64
Quantity delivered to Demat
quantity
int64
Realised Quantity(T+2)
used_quantity
int64
Quantity sold from the net holding quantity
authorised_quantity
int64
Quantity authorised at the depository for sale
opening_quantity
int64
Quantity carried forward over night
authorised_date
string
Date on which user can sell required holding stock
price
float64
average_price
float64
Average price at which the net holding quantity was acquired
last_price
float64
Last traded market price of the instrument
close_price
float64
Closing price of the instrument from the last trading day
pnl
float64
Net returns on the stock; Profit and loss
day_change
float64
Day's change in absolute value for the stock
day_change_percentage
float64
Day's change in percentage for the stock
product
string
Margin product applied to the holding
collateral_quantity
int64
Quantity used as collateral
collateral_type
null,string
Type of collateral
discrepancy
bool
Indicates whether holding has any price discrepancy
Holdings auction list¶
This API returns a list of auctions that are currently being held, along with details about each auction such as the auction number, the security being auctioned, the last price of the security, and the quantity of the security being offered. Only the stocks that you hold in your demat account will be shown in the auctions list.

curl "https://api.kite.trade/portfolio/holdings/auctions" \
    -H "X-Kite-Version: 3" \
    -H "Authorization: token api_key:access_token"
{
  "status": "success",
  "data": [
    {
      "tradingsymbol": "ASHOKLEY",
      "exchange": "NSE",
      "instrument_token": 54282,
      "isin": "INE208A01029",
      "product": "CNC",
      "price": 0,
      "quantity": 1,
      "t1_quantity": 0,
      "realised_quantity": 1,
      "authorised_quantity": 0,
      "authorised_date": "2022-12-21 00:00:00",
      "opening_quantity": 1,
      "collateral_quantity": 0,
      "collateral_type": "",
      "discrepancy": false,
      "average_price": 131.95,
      "last_price": 142.5,
      "close_price": 145.1,
      "pnl": 10.550000000000011,
      "day_change": -2.5999999999999943,
      "day_change_percentage": -1.7918676774638143,
      "auction_number": "20"
    },
    {
      "tradingsymbol": "BHEL",
      "exchange": "NSE",
      "instrument_token": 112138,
      "isin": "INE257A01026",
      "product": "CNC",
      "price": 0,
      "quantity": 5,
      "t1_quantity": 0,
      "realised_quantity": 5,
      "authorised_quantity": 0,
      "authorised_date": "2022-12-21 00:00:00",
      "opening_quantity": 5,
      "collateral_quantity": 0,
      "collateral_type": "",
      "discrepancy": false,
      "average_price": 75.95,
      "last_price": 81.1,
      "close_price": 84,
      "pnl": 25.749999999999957,
      "day_change": -2.9000000000000057,
      "day_change_percentage": -3.4523809523809588,
      "auction_number": "34"
    },
    {
      "tradingsymbol": "SBIN",
      "exchange": "NSE",
      "instrument_token": 779530,
      "isin": "INE062A01020",
      "product": "CNC",
      "price": 0,
      "quantity": 3,
      "t1_quantity": 0,
      "realised_quantity": 3,
      "authorised_quantity": 0,
      "authorised_date": "2022-12-21 00:00:00",
      "opening_quantity": 3,
      "collateral_quantity": 0,
      "collateral_type": "",
      "discrepancy": false,
      "average_price": 573.4,
      "last_price": 593.75,
      "close_price": 604.6,
      "pnl": 61.05000000000007,
      "day_change": -10.850000000000023,
      "day_change_percentage": -1.794574925570629,
      "auction_number": "7529"
    }
  ]
}
Response attributes¶
attribute	 
auction_number
string
A unique identifier for a particular auction
Positions¶
Positions contain the user's portfolio of short to medium term derivatives (futures and options contracts) and intraday equity stocks. Instruments in the positions portfolio remain there until they're sold, or until expiry, which, for derivatives, is typically three months. Equity positions carried overnight move to the holdings portfolio the next day.

The positions API returns two sets of positions, net and day. net is the actual, current net position portfolio, while day is a snapshot of the buying and selling activity for that particular day. This is useful for computing intraday profits and losses for trading strategies.

curl "https://api.kite.trade/portfolio/positions" \
    -H "X-Kite-Version: 3" \
    -H "Authorization: token api_key:access_token"
{
    "status": "success",
    "data": {
        "net": [
            {
                "tradingsymbol": "LEADMINI17DECFUT",
                "exchange": "MCX",
                "instrument_token": 53496327,
                "product": "NRML",
                "quantity": 1,
                "overnight_quantity": 0,
                "multiplier": 1000,
                "average_price": 161.05,
                "close_price": 0,
                "last_price": 161.05,
                "value": -161050,
                "pnl": 0,
                "m2m": 0,
                "unrealised": 0,
                "realised": 0,
                "buy_quantity": 1,
                "buy_price": 161.05,
                "buy_value": 161050,
                "buy_m2m": 161050,
                "sell_quantity": 0,
                "sell_price": 0,
                "sell_value": 0,
                "sell_m2m": 0,
                "day_buy_quantity": 1,
                "day_buy_price": 161.05,
                "day_buy_value": 161050,
                "day_sell_quantity": 0,
                "day_sell_price": 0,
                "day_sell_value": 0
            },
            {
                "tradingsymbol": "GOLDGUINEA17DECFUT",
                "exchange": "MCX",
                "instrument_token": 53505799,
                "product": "NRML",
                "quantity": 0,
                "overnight_quantity": 3,
                "multiplier": 1,
                "average_price": 0,
                "close_price": 23232,
                "last_price": 23355,
                "value": 801,
                "pnl": 801,
                "m2m": 276,
                "unrealised": 801,
                "realised": 0,
                "buy_quantity": 4,
                "buy_price": 23139.75,
                "buy_value": 92559,
                "buy_m2m": 93084,
                "sell_quantity": 4,
                "sell_price": 23340,
                "sell_value": 93360,
                "sell_m2m": 93360,
                "day_buy_quantity": 1,
                "day_buy_price": 23388,
                "day_buy_value": 23388,
                "day_sell_quantity": 4,
                "day_sell_price": 23340,
                "day_sell_value": 93360
            },
            {
                "tradingsymbol": "SBIN",
                "exchange": "NSE",
                "instrument_token": 779521,
                "product": "CO",
                "quantity": 0,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": 0,
                "close_price": 0,
                "last_price": 308.4,
                "value": -2,
                "pnl": -2,
                "m2m": -2,
                "unrealised": -2,
                "realised": 0,
                "buy_quantity": 1,
                "buy_price": 311,
                "buy_value": 311,
                "buy_m2m": 311,
                "sell_quantity": 1,
                "sell_price": 309,
                "sell_value": 309,
                "sell_m2m": 309,
                "day_buy_quantity": 1,
                "day_buy_price": 311,
                "day_buy_value": 311,
                "day_sell_quantity": 1,
                "day_sell_price": 309,
                "day_sell_value": 309
            }
        ],
        "day": [
            {
                "tradingsymbol": "GOLDGUINEA17DECFUT",
                "exchange": "MCX",
                "instrument_token": 53505799,
                "product": "NRML",
                "quantity": -3,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": 23340,
                "close_price": 23232,
                "last_price": 23355,
                "value": 69972,
                "pnl": -93,
                "m2m": -93,
                "unrealised": -93,
                "realised": 0,
                "buy_quantity": 1,
                "buy_price": 23388,
                "buy_value": 23388,
                "buy_m2m": 23388,
                "sell_quantity": 4,
                "sell_price": 23340,
                "sell_value": 93360,
                "sell_m2m": 93360,
                "day_buy_quantity": 1,
                "day_buy_price": 23388,
                "day_buy_value": 23388,
                "day_sell_quantity": 4,
                "day_sell_price": 23340,
                "day_sell_value": 93360
            },
            {
                "tradingsymbol": "LEADMINI17DECFUT",
                "exchange": "MCX",
                "instrument_token": 53496327,
                "product": "NRML",
                "quantity": 1,
                "overnight_quantity": 0,
                "multiplier": 1000,
                "average_price": 161.05,
                "close_price": 0,
                "last_price": 161.05,
                "value": -161050,
                "pnl": 0,
                "m2m": 0,
                "unrealised": 0,
                "realised": 0,
                "buy_quantity": 1,
                "buy_price": 161.05,
                "buy_value": 161050,
                "buy_m2m": 161050,
                "sell_quantity": 0,
                "sell_price": 0,
                "sell_value": 0,
                "sell_m2m": 0,
                "day_buy_quantity": 1,
                "day_buy_price": 161.05,
                "day_buy_value": 161050,
                "day_sell_quantity": 0,
                "day_sell_price": 0,
                "day_sell_value": 0
            },
            {
                "tradingsymbol": "SBIN",
                "exchange": "NSE",
                "instrument_token": 779521,
                "product": "CO",
                "quantity": 0,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": 0,
                "close_price": 0,
                "last_price": 308.4,
                "value": -2,
                "pnl": -2,
                "m2m": -2,
                "unrealised": -2,
                "realised": 0,
                "buy_quantity": 1,
                "buy_price": 311,
                "buy_value": 311,
                "buy_m2m": 311,
                "sell_quantity": 1,
                "sell_price": 309,
                "sell_value": 309,
                "sell_m2m": 309,
                "day_buy_quantity": 1,
                "day_buy_price": 311,
                "day_buy_value": 311,
                "day_sell_quantity": 1,
                "day_sell_price": 309,
                "day_sell_value": 309
            }
        ]
    }
}
Response attributes¶
attribute	 
tradingsymbol
string
Exchange tradingsymbol of the instrument
exchange
string
Exchange
instrument_token
uint32
The numerical identifier issued by the exchange representing the instrument. Used for subscribing to live market data over WebSocket
product
string
Margin product applied to the position
quantity
int64
Quantity held
overnight_quantity
int64
Quantity held previously and carried forward over night
multiplier
int64
The quantity/lot size multiplier used for calculating P&Ls.
average_price
float64
Average price at which the net position quantity was acquired
close_price
float64
Closing price of the instrument from the last trading day
last_price
float64
Last traded market price of the instrument
value
float64
Net value of the position
pnl
float64
Net returns on the position; Profit and loss
m2m
float64
Mark to market returns (computed based on the last close and the last traded price)
unrealised
float64
Unrealised intraday returns
realised
float64
Realised intraday returns
buy_quantity
int64
Quantity bought and added to the position
buy_price
float64
Average price at which quantities were bought
buy_value
float64
Net value of the bought quantities
buy_m2m
float64
Mark to market returns on the bought quantities
day_buy_quantity
int64
Quantity bought and added to the position during the day
day_buy_price
float64
Average price at which quantities were bought during the day
day_buy_value
float64
Net value of the quantities bought during the day
sell_quantity
int64
Quantity sold off from the position
sell_price
float64
Average price at which quantities were sold
sell_value
float64
Net value of the sold quantities
sell_m2m
float64
Mark to market returns on the sold quantities
day_sell_quantity
int64
Quantity sold off from the position during the day
day_sell_price
float64
Average price at which quantities were sold during the day
day_sell_value
float64
Net value of the quantities sold during the day
Position conversion¶
All positions held are of specific margin products such as NRML, MIS etc. A position can have one and only one margin product. These products affect how the user's margin usage and free cash values are computed, and a user may want to covert or change a position's margin product from time to time. More on margin policies.

curl --request PUT https://api.kite.trade/portfolio/positions
    -H "X-Kite-Version: 3" \
    -H "Authorization: token api_key:access_token" \
    -d "tradingsymbol=INFY" \
    -d "exchange=NSE" \
    -d "transaction_type=BUY" \
    -d "position_type=overnight" \
    -d "quantity=3" \
    -d "old_product=NRML" \
    -d "new_product=MIS"
{
    "status": "success",
    "data": true
}
Request parameters¶
parameter	 
tradingsymbol	Tradingsymbol of the instrument
exchange	Name of the exchange
transaction_type	BUY or SELL
position_type	overnight or day
quantity	Quantity to convert
old_product	Existing margin product of the position
new_product	Margin product to convert to
Exiting holdings and positions¶
There are no special API calls for exiting instruments from holdings and positions portfolios. The way to do it is to place an opposite BUY or SELL order depending on whether the position is a long or a short (MARKET order for an immediate exit). It is important to note that the exit order should carry the same product as the existing position. If the exit order is of a different margin product, it may be treated as a new position in the portfolio.

Holdings authorisation¶
When executing sell transactions on equity holdings, where shares have to be debited from a user's demat account, a broker either requires a PoA (Power of Attorney) or an electronic authorisation at the depository from the user, to debit shares and settle the transactions.

Electronic authorisation happens centrally on the depostiory's portal (CDSL in Zerodha's case) when the user executing the sell transaction keys in their demat PIN, similar to a netbanking flow. The demat PIN is known only to the demat account holder and the depository, and not the broker.

In a single authorisation transaction, multiple shares with n quantities each, can be authorised. The authorisations are valid for a single trading session in a day (beginning of the day till 5:30 PM, after which, the authorisations are for the next trading day). The quantity in a sell transaction need not be the same as n, just that at any point, the total sell quantities, even over multiple days, should not exceed n. When it does, the order API throws an error asking for authorisation, at which point, the user has to be directed to the authorisation flow. To illustrate:

User has 50 quantity of INFY in their demat. There is no authorisation at this point.
User attempts to sell 10 quantity of INFY. The POST /orders API throws error “10 quantity needs authorisation at depository.” (HTTP status 428).
On encountering 428, the authorisation flow is initiated and the user is redirected to the depository's portal. By default, Kite prompts the user to authorise the maximum quantities for every stock in their holding to avoid having to disrupt the sell transactions with the authorisation flow every time. In this case, 50 quantity of INFY is authorised.
User retries the transaction and 10 quantity is sold. 40 quantity remains authorised for the rest of the trading day (until 5:30 PM) and the user is not prompted for further authorisation until the remaining quantities have been sold.
Initiating authorisation¶
curl --request POST https://api.kite.trade/portfolio/holdings/authorise
    -H "X-Kite-Version: 3" \
    -H "Authorization: token api_key:access_token" \
    -d "isin=INE002A01018" -d "quantity=50" \
    -d "isin=INE009A01021" -d "quantity=50"
{
  "status": "success",
  "data": {
    "request_id": "na8QgCeQm05UHG6NL9sAGRzdfSF64UdB"
  }
}
The isin and quantity pairs here are optional. If they're provided, authorisation is sought only for those instruments and otherwise, the entire holdings is presented for authorisation. The request_id is then used to redirect the user to the following URL in a webivew or a popup.

https://kite.zerodha.com/connect/portfolio/authorise/holdings/:api_key/:request_id

After the user finishes the transaction, the webview is redirected to /connect/portfolio/authorise/holdings/:api_key/:request_id/finish?status=success. Mobile applications can watch for this URL to detect the end of the transaction. success or error value in the status query param indicates the result.

Web applications can invoke this flow using the authHoldings() call in the Publisher Javascript plugin. It provides a callback event with the completion status along with additional metadata.

Funds and margins¶
A GET request to /user/margins returns funds, cash, and margin information for the user for equity and commodity segments.

A GET request to /user/margins/:segment returns funds, cash, and margin information for the user. segment in the URI can be either equity or commodity.

curl "https://api.kite.trade/user/margins" \
    -H "X-Kite-Version: 3" \
    -H "Authorization: token api_key:access_token"
{
    "status": "success",
    "data": {
      "equity": {
        "enabled": true,
        "net": 99725.05000000002,
        "available": {
          "adhoc_margin": 0,
          "cash": 245431.6,
          "opening_balance": 245431.6,
          "live_balance": 99725.05000000002,
          "collateral": 0,
          "intraday_payin": 0
        },
        "utilised": {
          "debits": 145706.55,
          "exposure": 38981.25,
          "m2m_realised": 761.7,
          "m2m_unrealised": 0,
          "option_premium": 0,
          "payout": 0,
          "span": 101989,
          "holding_sales": 0,
          "turnover": 0,
          "liquid_collateral": 0,
          "stock_collateral": 0,
          "delivery": 0
        }
      },
      "commodity": {
        "enabled": true,
        "net": 100661.7,
        "available": {
          "adhoc_margin": 0,
          "cash": 100661.7,
          "opening_balance": 100661.7,
          "live_balance": 100661.7,
          "collateral": 0,
          "intraday_payin": 0
        },
        "utilised": {
          "debits": 0,
          "exposure": 0,
          "m2m_realised": 0,
          "m2m_unrealised": 0,
          "option_premium": 0,
          "payout": 0,
          "span": 0,
          "holding_sales": 0,
          "turnover": 0,
          "liquid_collateral": 0,
          "stock_collateral": 0,
          "delivery": 0
        }
      }
    }
  }
Response attributes¶
attribute	 
enabled
bool
Indicates whether the segment is enabled for the user
net
float64
Net cash balance available for trading (intraday_payin + adhoc_margin + collateral)
available.cash
float64
Raw cash balance in the account available for trading (also includes intraday_payin)
available.opening_balance
float64
Opening balance at the day start
available.live_balance
float64
Current available balance
available.intraday_payin
float64
Amount that was deposited during the day
available.adhoc_margin
float64
Additional margin provided by the broker
available.collateral
float64
Margin derived from pledged stocks
utilised.m2m_unrealised
float64
Un-booked (open) intraday profits and losses
utilised.m2m_realised
float64
Booked intraday profits and losses
utilised.debits
float64
Sum of all utilised margins (unrealised M2M + realised M2M + SPAN + Exposure + Premium + Holding sales)
utilised.span
float64
SPAN margin blocked for all open F&O positions
utilised.option_premium
float64
Value of options premium received by shorting
utilised.holding_sales
float64
Value of holdings sold during the day
utilised.exposure
float64
Exposure margin blocked for all open F&O positions
utilised.liquid_collateral
float64
Margin utilised against pledged liquidbees ETFs and liquid mutual funds
utilised.delivery
float64
Margin blocked when you sell securities (20% of the value of stocks sold) from your demat or T1 holdings
utilised.stock_collateral
float64
Margin utilised against pledged stocks/ETFs
utilised.turnover
float64
Utilised portion of the maximum turnover limit (only applicable to certain clients)
utilised.payout
float64
Funds paid out or withdrawn to bank account during the day
```


Update @get_current_portfolio  and @calculate_rebalancing_actions  according to this API definition


After rebalancing, report the total deficit amount. Create a parameter for target deficit amount, and keep running the rebalance till the total deficit is below the target deficit, or upto 10 tries


Update the documentation (@README.md  @README_REBALANCING.md ) and the @run.sh  script according to the new algorithm