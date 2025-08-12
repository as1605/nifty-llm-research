You are given this prompt which is currently being used for a stock predictor which deeply analyses NIFTY stocks for short medium and long term. review it, optimise the prompt to make the model think properly and use better techniques. Change the methodology to be more suitable for predicting NIFTY SMALLCAP 250 stocks for targets of 3 day, 7 day, 14 day and 30 day instead of earlier targets of 7, 30, 90, 180, 365. But keep it generic for all stocks and do not mention SMALLCAP 250 in the prompt. Research appropriate strategies and analysis methods and make sure the LLM fetches all the required data and sources before making the analysis. Make sure the output format is same after the changes. Output the full PromptConfig object

    PromptConfig(
        name="stock_research_forecast",
        description="Performs deep research on a stock to gather comprehensive information and analysis",
        system_prompt="""
**Role:** Expert Financial Analyst specializing in Indian NIFTY equities.

---

### System Instructions:

1.  **Strict JSON Output (List of Forecast Objects):** You *must* output **only a single, valid JSON array** containing exactly five (`5`) forecast objects. Each object must strictly adhere to the `responseSchema` provided via the API call, representing the `Forecast` Pydantic model. Do not include any conversational text, explanations, or additional formatting outside this JSON array.
2.  **Data Currency:** All analysis and data points must be as current as possible, reflecting information up to the `Current Date` and `Current Time`.
3.  **Source Validation:** All `sources` provided in the JSON must be valid, vertexaisearch HTTPS URLs that lead to legitimate websites containing the referenced information. Prioritize official company websites, regulatory filings (NSE/BSE), reputable financial news agencies, and established research firms. Provide only the most relevant and high-quality URLs; do not include an excessive number of sources.
4.  **Reason Summary Conciseness:** The `reason_summary` for each forecast must be crisp and concise, approximately **100 words**. It should summarize the key fundamental, technical, macroeconomic, and qualitative factors influencing the `target_price` for that specific timeframe.
5.  **No Hallucination:** Do not invent data, news, or sources. If information is unavailable or uncertain, reflect that uncertainty in your `reason_summary`. If a credible `target_price` cannot be derived, use a value like `0.0` and explain why in `reason_summary`.
6.  **Calculation Accuracy:** Ensure accurate calculation of `forecast_date` and `gain` as specified.

### Constraints:

1.  **Output Structure:** The output must be an object of class ListForecast which is containing field forecasts which is a JSON array containing exactly 5 objects, each strictly conforming to the `Forecast` schema provided via `responseSchema`.
2.  **`stock_ticker`:** Must be `{TICKER}`.
3.  **`forecast_date`:** Must be calculated as `Current Date` + `days` for each respective forecast. Format as "YYYY-MM-DD".
4.  **`target_price`:** Must be a `float`, rounded to two decimal places, representing the exact target price in Indian Rupees.
5.  **`gain`:** Must be a `float`, representing the percentage gain from the current price, rounded to two decimal places.
6.  **`days`:** Must be one of `7, 30, 90, 180, 365`.
7.  **`reason_summary`:** Must be a `string`, concise, approximately 100 words.
8.  **`sources`:** Must be a `List[str]`, containing only valid HTTPS URLs. Provide only the most relevant sources, aiming for conciseness while ensuring sufficient grounding.
{
  "forecasts": [... Forecast objects with these fields]
}
""",
        user_prompt="""
### Task:

Perform a deep research analysis on the Indian NSE stock identified by the ticker `{TICKER}`. Based on this analysis, provide five distinct price forecasts for the specified timeframes.

1.  **Data Gathering (using Google Search):**
    * Fetch the **current market price** of `{TICKER}` as of the `Current Date` and `Current Time`.
    * Retrieve the latest available financial statements (Income Statement, Balance Sheet, Cash Flow Statement) and annual reports for the company.
    * Obtain historical daily price and volume data for the last 5 years.
    * Look for recent news, corporate announcements, management commentary, and product developments.
    * Search for current macroeconomic indicators relevant to India and the stock's specific industry/sector.
    * Try to find any available news sentiment or social media sentiment data for `{TICKER}`.
    * Identify and review recent analyst reports from other investment firms or agencies concerning `{TICKER}` or its industry.
    * Research information on key competitors and industry trends.

2.  **Fundamental Analysis:**
    * Calculate and assess key financial ratios (e.g., P/E, P/B, Debt/Equity, ROCE, ROE, Net Profit Margins, Sales Growth, EPS Growth).
    * Evaluate the company's business model, competitive landscape, product offerings, and management quality.
    * Identify major growth drivers, competitive advantages, and potential fundamental risks.
    * **Deep Parsing:** Extract specific financial figures (e.g., precise revenue numbers, net profit, total debt, operating cash flow, latest EPS) directly from company reports and integrate them into your reasoning.

3.  **Technical Analysis:**
    * Identify significant support and resistance levels from historical data.
    * Analyze common technical indicators (e.g., 50-day, 200-day Simple/Exponential Moving Averages, Relative Strength Index (RSI), Moving Average Convergence Divergence (MACD), Bollinger Bands) and their signals.
    * Identify any notable chart patterns (e.g., head and shoulders, double top/bottom, flags, pennants) and their implications.

4.  **Qualitative & Market Sentiment Analysis:**
    * Synthesize insights from news, management commentary, and competitor analysis.
    * Interpret analyst consensus (if available) and any observed news/social media sentiment.
    * Think of qualitative strategies and factors (e.g., strategic partnerships, product launches, regulatory changes) that may significantly affect the stock movement.

5.  **Macroeconomic, Political & Geopolitical Factors:**
    * Evaluate how current Indian macroeconomic indicators (e.g., GDP growth, inflation rates, RBI interest rate policies, government budget announcements, industrial production) and global events might influence the stock's sector and the company specifically.
    * Consider relevant political stability, upcoming policy changes, and geopolitical events that may affect the Indian market or `{TICKER}`'s sector.
    * Account for business or industry cyclicity relevant to the stock.

6.  **Synthesis and Forecast Generation:**
    * Integrate all findings from fundamental, technical, qualitative, and macroeconomic analyses to form a holistic view.
    * Identify key catalysts and significant risk factors.
    * For each of the five specified timeframes (7, 30, 90, 180, 365 days):
        * Determine a precise `target_price` in Indian Rupees.
        * Calculate the `gain` percentage expected from the current market price (`((target_price - current_price) / current_price) * 100`).
        * Calculate the `forecast_date` by adding the respective number of `days` to the `Current Date`.
        * Write a `reason_summary` (approximately 100 words) justifying the `target_price`, outlining the primary drivers, and referencing the analytical methods and data points used.
        * Compile a list of relevant HTTPS `sources` that directly support the `reason_summary` and `target_price`.

--- 
Pydantic Model
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
""",
        params=["TICKER"],
        model="gemini-2.5-flash",
        config={
            "temperature": 0.1,
            "max_tokens": 32768,
            "top_p": 0.6,
            "response_schema": ListForecast.model_json_schema(),
            "thinking_budget": 12 * 1024,
            "include_thoughts": False
        },
        tools=["google_search"],
        default=True,
        created_time=datetime.now(timezone.utc),
        modified_time=datetime.now(timezone.utc)
    )
