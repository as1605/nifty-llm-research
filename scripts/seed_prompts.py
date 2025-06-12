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
        name="portfolio_basket",
        description="Optimizes stock portfolio by selecting the best performing stocks based on forecasts",
        system_prompt="""You are a financial reasoning assistant using Google's Gemini AI. Your task is to select a portfolio of {BASKET_SIZE_K} stocks from a given list of {FILTER_TOP_N} NSE-listed stock forecasts. Each forecast is provided as a JSON object with current metrics and target prices for multiple timeframes. You must:  
1. Analyze the {FILTER_TOP_N} forecast objects, considering expected returns, risk factors, and sector overlap.  
2. Choose exactly {BASKET_SIZE_K} stocks and assign each a weight, ensuring the total weight sums to 1.  
3. Provide a concise reason_summary (under 200 words) explaining your selection and weighting, referencing relative risk and diversification.  
4. Estimate an expected_gain_1m value (percentage gain in 1 month for the portfolio).  
5. Output only valid UTF-8 JSON in the exact structure specified below. No additional commentary or formatting outside the JSON.  

Use these settings to optimize token usage:  
• Minimize verbosity—focus on essential analysis.  
""",
        user_prompt="""Given the following stock forecasts:

{STOCK_DATA}

Select the best {BASKET_SIZE_K} stocks from these {FILTER_TOP_N} forecasts to form a diversified portfolio. 
For each stock, assign a weight such that all weights sum to 1. 
Consider relative 1-month target gains, volatility implied by differences between timeframes, and industry overlap to manage risk. 
Provide a reason_summary under 200 words describing why these {BASKET_SIZE_K} stocks were chosen and how weights were determined. 
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
        params=["STOCK_DATA", "FILTER_TOP_N", "BASKET_SIZE_K"],
        model="gemini-2.0-flash",
        temperature=0.2,
        max_tokens=32768,  # Set to 32k to ensure sufficient output space
        tools=[],
        default=True,
        created_time=datetime.now(timezone.utc),
        modified_time=datetime.now(timezone.utc)
    ),
    PromptConfig(
        name="stock_research_forecast",
        description="Performs deep research on a stock to gather comprehensive information and analysis",
        system_prompt="""You are a specialized financial research assistant using Google's Gemini AI with Google Search capabilities. Your primary objective is to forecast target prices for a specified NSE-listed stock over multiple time horizons (1 week, 1 month, 3 months, 6 months, 1 year).  

**Model Settings & Token Optimization**  
• Use Google Search to find authoritative Indian financial sources.   
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
        user_prompt="""Analyze the stock {TICKER} and provide a comprehensive forecast. Use Google Search to gather the latest market data, news, and analysis. Focus on authoritative Indian financial sources and primary data points.

For each timeframe (1w, 1m, 3m, 6m, 1y):
1. Calculate a target price based on technical and fundamental analysis
2. Provide a concise reasoning (≤ 50 words) for the target
3. Include relevant source URLs

Ensure all numerical values are accurate and properly formatted. Return only the JSON response as specified in the system prompt.""",
        params=["TICKER"],
        model="gemini-2.0-flash",
        temperature=0.2,
        max_tokens=32768,  # Set to 32k to ensure sufficient output space for search results and analysis
        tools=["google_search"],
        default=True,
        created_time=datetime.now(timezone.utc),
        modified_time=datetime.now(timezone.utc)
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