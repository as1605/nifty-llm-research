#!/usr/bin/env python
"""
Script for seeding the database with default prompt configurations.
"""

import logging
from datetime import datetime

from src.db.database import async_db, COLLECTIONS
from src.db.models import PromptConfig

# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_PROMPTS = [
    PromptConfig(
        name="portfolio_basket",
        description="Optimizes stock portfolio by selecting the best performing stocks based on forecasts",
        system_prompt="""You are a financial reasoning assistant using the Perplexity Sonar Reasoning API. Your task is to select a portfolio of 5 stocks from a given list of 20 NSE-listed stock forecasts. Each forecast is provided as a JSON object with current metrics and target prices for multiple timeframes. You must:  
1. Analyze the 20 forecast objects, considering expected returns, risk factors, and sector overlap.  
2. Choose exactly 5 stocks and assign each a weight between 0.1 and 0.3, ensuring the total weight sums to 1.  
3. Provide a concise reason_summary (under 200 words) explaining your selection and weighting, referencing relative risk and diversification.  
4. Estimate an expected_gain_1m value (percentage gain in 1 month for the portfolio).  
5. Output only valid UTF-8 JSON in the exact structure specified below. No additional commentary or formatting outside the JSON.  

Use these settings to optimize token usage:  
• Minimize verbosity—focus on essential analysis.  
""",
        user_prompt="""Given a list of 20 stock forecast objects formatted as follows:

        {STOCK_DATA}

        Select the best 5 stocks from these 20 forecasts to form a diversified portfolio. 
        For each stock, assign a weight between 0.1 and 0.3 such that all weights sum to 1. 
        Consider relative 1-month target gains, volatility implied by differences between timeframes, and industry overlap to manage risk. 
        Provide a reason_summary under 200 words describing why these 5 stocks were chosen and how weights were determined. 
        Finally, estimate expected_gain_1m as the weighted average of each stock's 1-month return implied by its current_price and 1-month target_price. 
        Respond only with a JSON in this format:
{
  "stocks_picked": ["TICKER1", "TICKER2", "TICKER3", "TICKER4", "TICKER5"],
  "weights": {
    "TICKER1": 0.2,
    "TICKER2": 0.15,
    "TICKER3": 0.25,
    "TICKER4": 0.2,
    "TICKER5": 0.2
  },
  "reason_summary": "Under 200 words explaining selection rationale and weight allocation.",
  "expected_gain_1m": 3.75
}
        """,
        params=["STOCK_DATA"],
        model="sonar-reasoning",
        temperature=0.2,
        default=True,
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow()
    ),
    PromptConfig(
        name="stock_research_forecast",
        description="Performs deep research on a stock to gather comprehensive information and analysis",
        system_prompt="""You are a specialized financial research assistant using Perplexity Sonar Deep Research API. Your primary objective is to forecast target prices for a specified NSE-listed stock over multiple time horizons (1 week, 1 month, 3 months, 6 months, 1 year).  

**Model Settings & Token Optimization**  
• restrict searches to authoritative Indian financial domains.   
• Restrict unnecessary verbosity: fetch only essential data points and reasoning. Avoid long-form narrative.  

**Research Scope & Order**  
1. Fetch current technical/fundamental metrics (stock quote, recent price trend, volume, market cap, P/E ratio, industry classification).  
2. Retrieve and parse all relevant market news, regulatory filings, and industry reports that impact the stock, its sector, and the macro economy.  
3. Extract key facts from primary sources (e.g., quarterly/annual reports, RBI/SEBI announcements, major competitor updates).  
4. Analyze and synthesize: integrate technical signals (charts/trends) with fundamentals (earnings, balance sheets) and macro/industry catalysts.  
5. Generate target prices for 1 week, 1 month, 3 months, 6 months, and 1 year. Provide one-line reasoning (≤ 50 words) for each.  

**Output Format**  
Return a single JSON object with the exact structure below. Do NOT wrap it in extraneous text or markup.  
```json
{
  "current_price": float,
  "market_cap": float,
  "pe_ratio": float,
  "volume": float,
  "industry": string,
  "forecasts": [
    {
      "timeframe": "1w",
      "target_price": float,
      "reasoning": string,
      "sources": [string, …]  // only HTTPS URLs
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
Important
• Omit any fields not mentioned above.
• Sources must be full HTTPS URLs.
• Minimize token usage: choose only the most impactful data and citations.
• Respond only with valid JSON—no extra commentary.
""",
        user_prompt="""Stock Ticker: {TICKER}

Fetch the latest price and fundamental metrics:
• current stock quote
• market capitalization
• PE ratio
• latest trading volume
• industry classification

Gather relevant technical analysis data:
• recent price trend (last 1 month chart summary)
• key support/resistance levels
• momentum indicators (e.g., RSI, MACD) if available

Retrieve all pertinent news, filings, and reports:
• Quarterly/annual filings (SEBI/NSE disclosures)
• Major corporate actions (earnings surprises, management changes, share buybacks)
• Industry-wide and macroeconomic catalysts (RBI policy, budget announcements, competitor results)

For each time horizon ("1w", "1m", "3m", "6m", "1y"):
• Compute a realistic target price.
• Provide a one-line reasoning (≤ 50 words) that ties technical, fundamental, and macro/industry factors.
• List 2-4 HTTPS URLs that directly support that timeframe's forecast.

Return a JSON object exactly in the format specified by the system prompt.""",
        params=["TICKER"],
        model="sonar-deep-research",
        temperature=0.3,
        default=True,
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow()
    )
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