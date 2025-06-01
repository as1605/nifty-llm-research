"""
Stock research agent for analyzing and forecasting stock prices using Perplexity models.
"""

import json
from datetime import datetime

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Forecast
from src.db.models import Stock

from .base import BaseAgent


class StockResearchAgent(BaseAgent):
    """Agent for analyzing stocks and generating price forecasts using Perplexity models."""

    def __init__(self):
        """Initialize the stock research agent."""
        super().__init__()

    async def analyze_stock(self, symbol: str) -> dict:
        """Analyze a stock and generate price forecasts.

        Args:
            symbol: The stock symbol (NSE format)

        Returns:
            Dictionary containing forecasts and analysis
        """
        # Get prompt config for deep research
        research_config = await self.get_prompt_config("stock_research")

        # Get deep research completion
        research_response, research_invocation_id = await self.get_completion(
            prompt_config=research_config,
            params={"symbol": symbol}
        )

        # Parse research data
        try:
            stock_data = json.loads(research_response['choices'][0]['message']['content'])
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse research data: {e}")

        # Get analysis config
        analysis_config = await self.get_prompt_config("stock_analysis")

        # Get final analysis
        analysis_response, analysis_invocation_id = await self.get_completion(
            prompt_config=analysis_config,
            params={
                "symbol": symbol,
                "research": research_response['choices'][0]['message']['content']
            }
        )

        # Parse results
        try:
            result = json.loads(analysis_response['choices'][0]['message']['content'])

            # Store stock data
            stock = Stock(
                ticker=symbol,
                price=stock_data["current_price"],
                market_cap=stock_data["market_cap"],
                industry=stock_data.get("industry", "Unknown"),
            )
            await async_db[COLLECTIONS["stocks"]].update_one(
                {"ticker": symbol}, {"$set": stock.dict()}, upsert=True
            )

            # Store forecast
            forecast = Forecast(
                stock_ticker=symbol,
                invocation_id=analysis_invocation_id,
                forecast_date=datetime.utcnow(),
                target_price=result["forecast_1m"],  # Using 1-month forecast as target
                gain=(
                    (result["forecast_1m"] - stock_data["current_price"])
                    / stock_data["current_price"]
                )
                * 100,
                days=30,  # 1 month
                reason_summary=result["analysis_summary"],
                sources=result.get("sources", []),
            )
            await async_db[COLLECTIONS["forecasts"]].insert_one(forecast.dict())

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse agent response: {e}")
