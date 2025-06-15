How to forecast the price of an Indian NSE stock in NIFTY Small Cap. We want to predict the price movements for next 1 week, 1 month, 3 month, 6 months and 1 year. Give an exhaustive list of the types of approaches, and all the data which should be fetched for each type of analysis, along with the reasoning techniques which can be used. Find techniques which have been used by experts, as well as which can be used by an LLM to do Google Search for data and perform analysis like a financial expert and stock research predictor


What are the best practices to writing a deep research prompt for Gemini 2.5 Flash using the API and Grounding with Google Search as a tool? Explain how it can go deeper into the analysis and parse documents for the results. Also how to make the API always output a valid JSON according to the pydantic schema. We want to know the best practices for making the LLM balance the information through a variety of sources and give a conclusion
Also understand the Gemini 2.5 API costing and make sure we are using everything efficiently and making the best use of it


We want to make an API call for analysing 1 stock at a time. And then we want to collect the results and pass N such stocks to another API call which will pick the best K stocks and assign them weights for the portfolio. Read all the above sources and reports from the previous queries, and give a list of information, guidance, strategies and sources which should be provided to both the prompts. Also request whatever further clarification is needed to write the prompts. Do not write the prompts yet


Using all the above information, write the complete prompt for the Gemini 2.5 Flash LLM, which would take a single {STOCK} ticker as a parameter, perform deep research on it, then output the JSON which will have a list of the following structure

{
  "forecasts": [
    {
      "timeframe": "1w",
      "target_price": float,
      "reasoning": string,
      "sources": [string, …]  // only HTTPS URLs
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
Make sure the LLM outputs only the JSON. The reasonings should be crisp and around 100 words, mentioning all points which would be helpful for further analysis. The sources should be valid HTTPS urls which lead to legitimate websites. 

Make sure the LLM does a complete technical as well as fundamental analysis before making the decisions. It should also read reports from analysts of other investment firms and agencies. It should also read general news about the company as well as the industry and competitors and products, and think of strategies and factors which may affect the stock movement. It should also take into account macroscopic economical political and geopolitical factors as well as cyclicity. Include all these factors along with the findings of the previous researches done above. The result should be an excellent financial analysis and accurate price target forecasts

Divide the prompt into system instructions, tasks, constraints. Also suggest appropriate model parameters to be passed like temperature etc.


Now, write a prompt for a call which will take a list of Forecast Objects of some N stocks, and picks a basket of K stocks along with weights. The number of objects will be more than N, as we will be passing multiple different objects for each stock for different days.
It should also output a reasoning and a expected 1 month gain for the portfolio basket. We want to maximise the gains for the portfolio and beat the market indices and potentially other mutual funds too.
As an financial analyser, it should make sure to have a variety of stocks to avoid too much of industry overlap on the same factor, as well as manage risk in the portfolio. It should also go through the reasonings and maybe the sources provided if needed to gain more context on the decision. 
We will provide the responseSchema in the following Pydantic format, so this does not need to be explicitly written in the prompt, but we should explain the constraints
class Basket(BaseModel):
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stocks_ticker_candidates: List[str] = Field(
        ..., description="List of stock tickers considered for the basket"
    )
    stocks_picked: List[str] = Field(..., description="List of selected stock tickers")
    weights: dict[str, float] = Field(
        ..., description="Dictionary mapping stock tickers to their weights (summing to 1)"
    )
    reason_summary: str
    expected_gain_1m: float
in this, the stocks_ticker_candiates should be of size N, and stocks_picked should be of K. The reason summary should be around 200-300 words