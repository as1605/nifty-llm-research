Research strategies for predicting prices of an Indian NSE stock, for a period of 1 week. Find prediction strategies which give high accuracy and risk based on technical data and also by using news and googling about the stock. Find how to use google effectively to analyse a stock for a week or a month, and what to search to find crucial information. Focus on strategies which work for smallcap stocks. Include geopolitical affects too


For indian stock market, and especially for small cap stocks, what are good news sources for strategic info related to stocks, industry events and competitors and contracts, and which market analysts reports give accurate price targets and detailed analysis? How to read such info and what data to look out for? How to leverage social media like youtube, twitter and reddit etc? Can they be accessed by google search grounding of gemini?


How to instruct an LLM with tools like gemini 2.5 flash, to search for market analyst reports and read them in detail to analyse a stock. Include reading PDFs and documents or opinions published by people in news or on forums like reddit


Assume we have python yfinance library for yfinance API. Which relevant data should be fetched from yfinance API for such an analysis? List key fields, and format in which the data should be provided to an LLM for analysis. Make sure to include OHLC history and news. Focus only on short term analysis of 1 week.


Write a prompt for Gemini 2.5 Flash to analyse a NSE stock and give a price target for 3 days, 7 days, 14 days and 30 days. Use the above strategies for analysing correctly. Make sure to take into account risks, and research the news deeply. Divide into system prompt, user prompt, and also any tools to use. Assume google_search tool is provided
Input:
{TICKER} which will be NSE ticker
{YFINANCE_DATA} which will be of format given above

Output:
The output must be of type ListForecast. The sources can be of https://vertexaisearch.cloud.google.com/grounding-api-redirect if required
```python
class ListForecast(BaseModel):
    forecasts: List[Forecast] = Field(
        ...,
        description="List of forecasts for different time periods"
    )

class Forecast(BaseModel):
    stock_ticker: str
    invocation_id: PyObjectId = None
    forecast_date: datetime
    target_price: float
    gain: float
    days: int
    reason_summary: str
    sources: List[str]
    created_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```


Enrich this prompt to make the LLM think deeper and explore more sources and do more analysis for predicting the stock forecast prices, and make full utilisation of the google search tool. The methodology should focus on accuracy in short term analysis for our use case and be able to focus on factors which move the price within a week's timeframe, and read news properly. The target_price should weigh in key risks too. The LLM should be creative in formulating the google search queries dynamically as per the responses and scenario for that stock, Do not explicitly give what query to make. Make sure the LLM performs multiple levels of research. Also use the OHLCV data provided in the above format. Do not add more fields to the output, adhere to this json structure


Write a prompt for a portfolio generator, which will take in a list of such forecasts as {STOCK_DATA} for {FILTER_TOP_N} stocks, analyses them and builds a portfolio of {BASKET_SIZE_K} stocks. Give flexibility to choose weights of the stocks in the portfolio. Balance risk factors according to the given reasons. Output should be strictly a json of format BasketStock. Include the definition optimally for the prompt

class BasketStock(BaseModel):
    stock_ticker: str = Field(..., description="Stock ticker symbol")
    weight: float = Field(..., description="Weight of this stock in the basket (0-1)")
    sources: List[str] = Field(default_factory=list, description="List of source URLs for this stock")

class Basket(BaseModel):
    stocks_ticker_candidates: List[str] = Field(
        ..., description="List of stock tickers considered for the basket"
    )
    stocks: List[BasketStock] = Field(
        ..., description="List of selected stocks with their weights and sources"
    )
    reason_summary: str = Field(..., description="Summary of why these stocks were picked")




