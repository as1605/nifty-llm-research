Switch from SQL to MongoDB as our database. We will be using a managed Atlas connection. Remove SQL usage anywhere and from dependencies too.
@models.py @database.py @settings.py @setup_db.py @requirements.txt 
Also, change the schema models, and make the following collections. Make necessary changes to the code too, and make sure the schema is being used correctly with their purpose.
@agents @scripts @utils 
Ensure best practices for MongoDB are used, with proper types. Change the field names or type if required for best practice.

Collections:
- PromptConfig:
    - name: string (a short code to identify it)
    - system_prompt: string
    - user_prompt: string
    - params: list[string]
    - model: string (the openai model name)
    - tools: list[string] (tools allowed to use)
    - default: boolean (if this will be used by default)
    - created_time: date
    - modified_time: date
- Invocation:
    - invocation_time: date
    - result_time: date
    - prompt_config_id: ObjectId
    - params: object (mapping from the param key to its value)
    - response: string
    - metadata: Object (of OpenAI metadata type)
- Stock:
    - ticker: string
    - price: number
    - modified_time: date
    - market_cap: number
    - industry: string
- Forecast:
    - stock_ticker: string
    - created_time: date
    - invocation_id: ObjectId
    - forecast_date: date
    - target_price: number
    - gain: number (percentage gain)
    - days: number
    - reason_summary: string
    - sources: list[string]
- Basket:
    - creation_date: date
    - stocks_ticker_candidates: list[string]
    - stocks_picked: list[string]
    - weights: Object (stock ticker vs their ratio, all summing to 1)
    - reason_summary: string
    - expected_gain_1w: number
- Email:
    - created_time: date
    - sent_time: date
    - service: string (amazon-ses)
    - type: string (account related/generic alert/basket update)
    - status: string
    - subject: string
    - content_html: string
    - from: string
    - to: list[string]
    - cc: list[string]
    - bcc: list[string]
- Orders:
    - stock_ticker: string
    - type: enum (buy/sell)
    - price: number (final trade price)
    - isMarketOrder: boolean
    - placed_time: date
    - executed_time: date
    - demat_account: string

The PromptConfig should have fields of system_prompt, user_prompt, and params
    - system_prompt: string
    - user_prompt: string
    - params: list[string]
Invocation should have field of params which will be a mapping from the param key to its value. 
    - params: object (mapping from the param key to its value) 
Make sure this is used in the code too. For example the param key can be \[STOCK_TICKER\]