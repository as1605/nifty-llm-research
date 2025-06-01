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
        name="portfolio_optimization",
        description="Optimizes stock portfolio by selecting the best performing stocks based on forecasts",
        system_prompt="""You are an expert portfolio manager specializing in Indian stocks.
        Analyze the provided stock forecasts and select the 5 best stocks for a weekly portfolio.
        Consider both potential returns and risk factors in your selection.
        IMPORTANT: Output ONLY a valid JSON object with no additional text or explanation.""",
        user_prompt="""Analyze the following stock forecasts and select the best 5 stocks:

        Stock Data:
        {STOCK_DATA}

        Provide:
        - List of 5 selected stocks (symbols only)
        - Expected 1-month portfolio return
        - Brief explanation of selection rationale

        Format your response as a JSON object with keys:
        - selected_stocks (list)
        - expected_return (float)
        - summary (string)""",
        params=["STOCK_DATA"],
        model="sonar-reasoning-pro",
        temperature=0.5,
        default=True,
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow()
    ),
    PromptConfig(
        name="stock_research",
        description="Performs deep research on a stock to gather comprehensive information and analysis",
        system_prompt="""You are an expert financial analyst specializing in Indian stocks.
        Use your deep research capabilities to gather and analyze comprehensive information about the given stock.
        Focus on factual data, market trends, and reliable sources.
        Include specific numbers, dates, and sources in your analysis.
        Ensure all numerical data is accurate and properly sourced.
        IMPORTANT: Output ONLY a valid JSON object with no additional text or explanation.""",
        user_prompt="""Analyze {symbol} stock on NSE. Provide comprehensive information including:
        1. Current stock price and recent price movements
        2. Market capitalization
        3. P/E ratio and other key financial metrics
        4. Recent financial performance and quarterly results
        5. Market position and competitive advantages
        6. Industry trends and challenges
        7. Management quality and strategy
        8. Growth prospects and risks
        9. Technical analysis indicators
        10. Market sentiment and news
        
        Format your response as a JSON object with the following structure:
        {{
            "current_price": float,
            "market_cap": float,
            "pe_ratio": float,
            "volume": float,
            "industry": str,
            "financial_metrics": {{
                "revenue_growth": float,
                "profit_margin": float,
                "debt_to_equity": float
            }},
            "analysis": {{
                "strengths": list[str],
                "weaknesses": list[str],
                "opportunities": list[str],
                "threats": list[str]
            }},
            "sources": list[str]
        }}
        
        Ensure all numerical values are accurate and include sources for your data.""",
        params=["symbol"],
        model="sonar-deep-research",
        temperature=0.7,
        default=True,
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow()
    ),
    PromptConfig(
        name="stock_analysis",
        description="Generates price forecasts and analysis based on stock research data",
        system_prompt="""You are an expert financial analyst specializing in Indian stocks.
        Based on the provided research and data, generate precise price forecasts and analysis.
        Your analysis should be data-driven and consider both technical and fundamental factors.
        Provide specific numbers and clear reasoning for your forecasts.
        Ensure your forecasts are realistic and well-justified by the available data.
        IMPORTANT: Output ONLY a valid JSON object with no additional text or explanation.""",
        user_prompt="""Based on the following research about {symbol}, provide:
        1. Price forecasts for:
           - 1 week
           - 1 month
           - 3 months
           - 6 months
           - 12 months
        2. Confidence score (0-1)
        3. Key factors influencing the forecast
        4. Risk factors to consider

        Research findings:
        {research}

        Format your response as a JSON object with the following structure:
        {{
            "forecast_1w": float,
            "forecast_1m": float,
            "forecast_3m": float,
            "forecast_6m": float,
            "forecast_12m": float,
            "confidence_score": float,
            "key_factors": list[str],
            "risk_factors": list[str],
            "analysis_summary": str,
            "sources": list[str]
        }}""",
        params=["symbol", "research"],
        model="sonar-reasoning-pro",
        temperature=0.3,
        default=True,
        created_time=datetime.utcnow(),
        modified_time=datetime.utcnow()
    ),
    # Add more default prompts here as needed
]

async def seed_prompts():
    """Seed the database with default prompt configurations."""
    try:
        logger.info("Seeding default prompt configurations...")
        
        # Clear existing default prompts
        await async_db[COLLECTIONS["prompt_configs"]].delete_many({"default": True})
        
        # Insert new default prompts
        for prompt in DEFAULT_PROMPTS:
            await async_db[COLLECTIONS["prompt_configs"]].insert_one(prompt.dict())
        
        logger.info("Successfully seeded default prompt configurations")
        
    except Exception as e:
        logger.exception(f"Error seeding prompt configurations: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_prompts()) 