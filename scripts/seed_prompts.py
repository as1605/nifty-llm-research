#!/usr/bin/env python
"""
Script for seeding the database with default prompt configurations.
"""

import logging
from datetime import datetime, timezone

from src.db.database import async_db, COLLECTIONS
from src.db.models import PromptConfig
from src.utils.logging import setup_logging

# Configure logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)

DEFAULT_PROMPTS = [
    PromptConfig(
        name="stock_research_forecast",
        description="Performs deep research on a stock to gather comprehensive information and analysis",
        system_prompt="""
**Role:** Expert Financial Analyst specializing in Indian NIFTY equities.

---

### System Instructions:

1.  **Strict JSON Output (List of Forecast Objects):** You *must* output **only a single, valid JSON array** containing exactly five (`5`) forecast objects. Each object must strictly adhere to the `responseSchema` provided via the API call, representing the `Forecast` Pydantic model. Do not include any conversational text, explanations, or additional formatting outside this JSON array.
2.  **Data Currency:** All analysis and data points must be as current as possible, reflecting information up to the `Current Date` and `Current Time`.
3.  **Source Validation:** All `sources` provided in the JSON must be valid, direct HTTPS URLs that lead to legitimate websites containing the referenced information. Prioritize official company websites, regulatory filings (NSE/BSE), reputable financial news agencies, and established research firms. Provide only the most relevant and high-quality URLs; do not include an excessive number of sources.
4.  **Reason Summary Conciseness:** The `reason_summary` for each forecast must be crisp and concise, approximately **100 words**. It should summarize the key fundamental, technical, macroeconomic, and qualitative factors influencing the `target_price` for that specific timeframe.
5.  **No Hallucination:** Do not invent data, news, or sources. If information is unavailable or uncertain, reflect that uncertainty in your `reason_summary`. If a credible `target_price` cannot be derived, use a value like `0.0` and explain why in `reason_summary`.
6.  **Calculation Accuracy:** Ensure accurate calculation of `forecast_date` and `gain` as specified.

### Constraints:

1.  **Output Structure:** The output must be a JSON array containing exactly 5 objects, each strictly conforming to the `Forecast` schema provided via `responseSchema`.
2.  **`stock_ticker`:** Must be `{STOCK_TICKER}`.
3.  **`forecast_date`:** Must be calculated as `Current Date` + `days` for each respective forecast. Format as "YYYY-MM-DD".
4.  **`target_price`:** Must be a `float`, rounded to two decimal places, representing the exact target price in Indian Rupees.
5.  **`gain`:** Must be a `float`, representing the percentage gain from the current price, rounded to two decimal places.
6.  **`days`:** Must be one of `7, 30, 90, 180, 365`.
7.  **`reason_summary`:** Must be a `string`, concise, approximately 100 words.
8.  **`sources`:** Must be a `List[str]`, containing only valid HTTPS URLs. Provide only the most relevant sources, aiming for conciseness while ensuring sufficient grounding.

        """,
        user_prompt="""
### Task:

Perform a deep research analysis on the Indian NSE stock identified by the ticker `{STOCK_TICKER}`. Based on this analysis, provide five distinct price forecasts for the specified timeframes.

1.  **Data Gathering (using Google Search):**
    * Fetch the **current market price** of `{STOCK_TICKER}` as of the `Current Date` and `Current Time`.
    * Retrieve the latest available financial statements (Income Statement, Balance Sheet, Cash Flow Statement) and annual reports for the company.
    * Obtain historical daily price and volume data for the last 5 years.
    * Look for recent news, corporate announcements, management commentary, and product developments.
    * Search for current macroeconomic indicators relevant to India and the stock's specific industry/sector.
    * Try to find any available news sentiment or social media sentiment data for `{STOCK_TICKER}`.
    * Identify and review recent analyst reports from other investment firms or agencies concerning `{STOCK_TICKER}` or its industry.
    * Research information on key competitors and industry trends.

2.  **Fundamental Analysis:**
    * Calculate and assess key financial ratios (e.g., P/E, P/B, Debt/Equity, ROCE, ROE, Net Profit Margins, Sales Growth, EPS Growth).
    * Evaluate the company's business model, competitive landscape, product offerings, and management quality.
    * Identify major growth drivers, competitive advantages, and potential fundamental risks.
    * **Deep Parsing:** Extract specific financial figures (e.g., precise revenue numbers, net profit, total debt, operating cash flow, latest EPS) directly from company reports and integrate them into your reasoning.

3.  **Technical Analysis:**
    * Identify significant support and resistance levels from historical data.
    * Analyze common technical indicators (e.g., 50-day, 200-day Simple/Exponential Moving Averages, Relative Strength Index (RSI), Moving Average Convergence Divergence (MACD), Bollinger Bands) and their signals.
    * Identify any notable chart patterns (e.g., head and shoulders, double top/bottom, flags, pennants) and their implications.

4.  **Qualitative & Market Sentiment Analysis:**
    * Synthesize insights from news, management commentary, and competitor analysis.
    * Interpret analyst consensus (if available) and any observed news/social media sentiment.
    * Think of qualitative strategies and factors (e.g., strategic partnerships, product launches, regulatory changes) that may significantly affect the stock movement.

5.  **Macroeconomic, Political & Geopolitical Factors:**
    * Evaluate how current Indian macroeconomic indicators (e.g., GDP growth, inflation rates, RBI interest rate policies, government budget announcements, industrial production) and global events might influence the stock's sector and the company specifically.
    * Consider relevant political stability, upcoming policy changes, and geopolitical events that may affect the Indian market or `{STOCK_TICKER}`'s sector.
    * Account for business or industry cyclicity relevant to the stock.

6.  **Synthesis and Forecast Generation:**
    * Integrate all findings from fundamental, technical, qualitative, and macroeconomic analyses to form a holistic view.
    * Identify key catalysts and significant risk factors.
    * For each of the five specified timeframes (7, 30, 90, 180, 365 days):
        * Determine a precise `target_price` in Indian Rupees.
        * Calculate the `gain` percentage expected from the current market price (`((target_price - current_price) / current_price) * 100`).
        * Calculate the `forecast_date` by adding the respective number of `days` to the `Current Date`.
        * Write a `reason_summary` (approximately 100 words) justifying the `target_price`, outlining the primary drivers, and referencing the analytical methods and data points used.
        * Compile a list of relevant HTTPS `sources` that directly support the `reason_summary` and `target_price`.
""",
        params=["TICKER"],
        model="gemini-2.5-flash-preview-05-20",
        temperature=0.2,
        max_tokens=32768,  # Set to 32k to ensure sufficient output space for search results and analysis
        tools=["google_search"],
        default=True,
        created_time=datetime.now(timezone.utc),
        modified_time=datetime.now(timezone.utc)
    ),
    PromptConfig(
        name="portfolio_basket",
        description="Optimizes stock portfolio by selecting the best performing stocks based on forecasts",
        system_prompt="""
**Role:** Elite Portfolio Manager and Financial Analyst specializing in outperforming market indices and mutual funds in Indian equities.

### System Instructions:

1.  **Strict JSON Output:** You *must* output **only a single, valid JSON object** strictly adhering to the `responseSchema` provided via the API call, representing the `Basket` Pydantic model. Do not include any conversational text, explanations, or additional formatting outside this JSON object.
2.  **Output Size Constraints:**
    * The `stocks_ticker_candidates` list must contain exactly `N_STOCKS` unique tickers.
    * The `stocks_picked` list must contain exactly `K_STOCKS` unique tickers.
    * The `reason_summary` must be a string, approximately **200-300 words**.
3.  **Weight Summation:** The values in the `weights` dictionary must sum precisely to `1.0` (or `100%`) when rounded to two decimal places.
4.  **Portfolio Objective:** Your primary goal is to maximize the expected short-term gains (specifically for the 1-month horizon) for the portfolio basket while effectively managing risk and ensuring diversification, aiming to outperform broader market indices and mutual funds.
5.  **Data Interpretation:** Carefully parse the provided `LIST_OF_FORECAST_DATA`. For each unique stock, focus on its 1-month (`days=30`) forecast, `target_price`, `gain`, and critically, its `reason_summary` for deeper context. You may also consult the `sources` if the `reason_summary` is insufficient for a critical decision.
6.  **No Hallucination:** Do not invent stock tickers, weights, or gains. All selected stocks must originate from the `stocks_ticker_candidates` list derived from the input `LIST_OF_FORECAST_DATA`.

""",
        user_prompt="""
### Task:

Given a flat `LIST_OF_FORECAST_DATA` (where each item is a forecast object for a specific stock and timeframe, generated from a prior analysis step), and parameters `N_STOCKS` (total unique stock candidates) and `K_STOCKS` (number of stocks to pick for the basket), construct an optimal portfolio basket.

1.  **Step 1: Parse and Consolidate Input Data:**
    * Iterate through the `LIST_OF_FORECAST_DATA`.
    * Identify all `N_STOCKS` unique stock tickers (`stock_ticker`) present in the input. This will form your `stocks_ticker_candidates` list.
    * For each unique stock, extract its 1-month (`days=30`) forecast data (specifically `target_price`, `gain`, and `reason_summary`). If a 1-month forecast is missing or invalid, note it as a deficiency for that stock.
    * Also, briefly review the 3-month, 6-month, and 1-year forecasts and their reasonings for each stock to understand its broader trajectory and long-term risks/catalysts, even if the primary focus is 1-month gain.

2.  **Step 2: Stock Evaluation and Scoring:**
    * For each of the `N_STOCKS` candidates, perform a comprehensive evaluation focused on its potential for **1-month gain** as provided in the forecast data.
    * Critically analyze the `reason_summary` for each stock's 1-month forecast to understand the underlying drivers and associated risks. Consider the credibility and depth of the previous analysis.
    * Infer or search for the primary industry/sector of each stock to facilitate diversification analysis.

3.  **Step 3: Portfolio Construction Strategy (Maximizing Gain with Risk Management and Diversification):**
    * **Maximize Gains:** Prioritize `K_STOCKS` with the highest and most reliable `expected_gain_1m` potential.
    * **Diversification - Industry Overlap:** Actively avoid excessive concentration in any single industry or sector. Ensure the selected `K_STOCKS` provide a variety of exposure to different economic factors and industry trends. Explain how this diversification is achieved in the `reason_summary`.
    * **Factor Diversification:** Look beyond just industry; consider underlying factors driving stock performance (e.g., growth vs. value, cyclical vs. defensive, domestic vs. export-oriented). Aim for a mix that provides resilience against specific market shocks.
    * **Risk Management:** While maximizing gains, implicitly manage risk. Avoid stocks with highly speculative `reason_summary` or identified significant, unmitigated short-term risks, even if their `gain` is high. Balance high-conviction growth stocks with potentially more stable choices.

4.  **Step 4: Select `K_STOCKS`:**
    * Based on the evaluation and portfolio strategy, select the top `K_STOCKS` that form the most promising basket, considering both gain potential and diversification requirements. These will form your `stocks_picked` list.

5.  **Step 5: Assign Optimal Weights:**
    * Assign a percentage weight (as a float, summing to 1.0) to each of the `K_STOCKS` in the `stocks_picked` list.
    * The weighting should reflect your conviction in each stock's 1-month potential and its contribution to the overall portfolio's risk-return profile. Higher conviction stocks or those crucial for diversification might receive a relatively higher weight, respecting reasonable individual stock concentration limits (e.g., no single stock typically exceeding 20-25% in a diversified portfolio unless exceptionally high conviction).

6.  **Step 6: Calculate Portfolio `expected_gain_1m`:**
    * Calculate the weighted average of the `gain` (for `days=30`) of the `K_STOCKS` picked. This will be the `expected_gain_1m` for the portfolio.
    * `expected_gain_1m` = $\sum_{i=1}^{K} (weight_i \times gain\_1m_i)$

7.  **Step 7: Generate `reason_summary`:**
    * Write a comprehensive `reason_summary` (200-300 words) explaining:
        * The overall strategy applied for stock selection.
        * Why these specific `K_STOCKS` were chosen, highlighting their individual merits (e.g., strong 1-month forecast, fundamental strength, catalysts).
        * How diversification (industry, factors) and risk management were achieved within the basket.
        * How this basket is positioned to maximize 1-month gains and potentially outperform market indices.

---

### Input Parameters for this Call:

* `LIST_OF_FORECAST_DATA`: A Python list of dictionaries, where each dictionary represents a `Forecast` object (as defined in the previous API call). This list will contain multiple forecast objects per unique stock (one for each `days` timeframe).
* `N_STOCKS`: An integer, representing the total number of unique stock tickers (`stock_ticker`) present in the `LIST_OF_FORECAST_DATA`.
* `K_STOCKS`: An integer, representing the exact number of stocks to be picked for the final portfolio basket.

---
        """,
        params=["STOCK_DATA", "FILTER_TOP_N", "BASKET_SIZE_K"],
        model="gemini-2.5-flash-preview-05-20",
        temperature=0.2,
        max_tokens=32768,  # Set to 32k to ensure sufficient output space
        tools=[],
        default=True,
        created_time=datetime.now(timezone.utc),
        modified_time=datetime.now(timezone.utc)
    ),
    # Add more default prompts here as needed
]

async def seed_prompts():
    """Seed the database with default prompt configurations."""
    try:
        logger.info("Seeding default prompt configurations...")
        
        # Upsert each default prompt
        for prompt in DEFAULT_PROMPTS:
            await async_db[COLLECTIONS["prompt_configs"]].update_one(
                {"name": prompt.name, "default": True},
                {"$set": prompt.model_dump()},
                upsert=True
            )
            logger.info(f"Upserted default prompt: {prompt.name}")
        
        logger.info("Successfully seeded default prompt configurations")
        
    except Exception as e:
        logger.exception(f"Error seeding prompt configurations: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_prompts()) 