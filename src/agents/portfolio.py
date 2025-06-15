"""
Portfolio optimization agent for selecting the best stocks.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Basket, BasketStock

from .base import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

class PortfolioAgent(BaseAgent):
    """Agent for optimizing stock portfolios."""

    def __init__(self):
        """Initialize the portfolio agent."""
        super().__init__()

    async def _get_top_stocks(
        self,
        index: str,
        since_time: datetime,
        filter_top_n: int,
        force_llm: bool = False
    ) -> List[Dict[str, Any]]:
        """Get top performing stocks based on forecasts.
        
        Args:
            index: Index to filter stocks by
            since_time: Only consider forecasts after this time
            filter_top_n: Number of top stocks to return
            force_llm: If True, require at least 5 forecasts per stock
            
        Returns:
            List of all forecasts for the top N stocks by average gain
        """
        # First get all stocks in the index
        stocks = await async_db[COLLECTIONS["stocks"]].find(
            {"indices": index}
        ).to_list(length=None)
        
        if not stocks:
            raise ValueError(f"No stocks found for index {index}")
            
        tickers = [stock["ticker"] for stock in stocks]
        
        # Use MongoDB aggregation to get top N stocks by average gain
        pipeline = [
            # Match forecasts for stocks in the index after since_time
            {
                "$match": {
                    "stock_ticker": {"$in": tickers},
                    "created_time": {"$gte": since_time}
                }
            },
            # Group by stock_ticker and calculate average gain
            {
                "$group": {
                    "_id": "$stock_ticker",
                    "avg_gain": {"$avg": "$gain"},
                    "forecast_count": {"$sum": 1},
                    "forecasts": {"$push": "$$ROOT"}
                }
            },
            # Filter stocks with enough forecasts if force_llm is True
            {
                "$match": {
                    "forecast_count": {"$gte": 5 if force_llm else 1}
                }
            },
            # Sort by average gain in descending order
            {"$sort": {"avg_gain": -1}},
            # Limit to top N stocks
            {"$limit": filter_top_n},
            # Unwind the forecasts array to get all forecasts
            {"$unwind": "$forecasts"},
            # Project only the forecast data
            {
                "$project": {
                    "_id": 0,
                    "forecast": "$forecasts"
                }
            }
        ]
        
        # Execute aggregation
        forecasts = await async_db[COLLECTIONS["forecasts"]].aggregate(pipeline).to_list(length=None)
        
        if not forecasts:
            raise ValueError(f"No forecasts found for stocks in {index} after {since_time}")
            
        # Extract just the forecast data from the aggregation result
        return [forecast["forecast"] for forecast in forecasts]

    async def optimize_portfolio(
        self,
        index: str,
        since_time: datetime,
        filter_top_n: int,
        basket_size_k: int,
        force_llm: bool = False
    ) -> Basket:
        """Generate optimized portfolio recommendations.

        Args:
            index: Index to filter stocks by
            since_time: Only consider forecasts after this time
            filter_top_n: Number of top stocks to consider
            basket_size_k: Number of stocks to select for portfolio
            force_llm: If True, require at least 5 forecasts per stock

        Returns:
            Basket object containing selected stocks and analysis
        """
        # Get top performing stocks
        stock_data = await self._get_top_stocks(index, since_time, filter_top_n, force_llm)
        
        if not stock_data:
            raise ValueError("No stock data available for portfolio optimization")

        # Clean forecast data by removing MongoDB specific fields
        cleaned_stock_data = []
        # Track sources for each stock
        stock_sources = {}
        
        for forecast in stock_data:
            cleaned_forecast = forecast.copy()
            # Remove MongoDB specific fields
            cleaned_forecast.pop('_id', None)
            cleaned_forecast.pop('invocation_id', None)
            cleaned_forecast.pop('created_time', None)
            cleaned_forecast.pop('modified_time', None)
            
            # Convert forecast_date to simple date string
            if 'forecast_date' in cleaned_forecast:
                cleaned_forecast['forecast_date'] = cleaned_forecast['forecast_date'].strftime('%Y-%m-%d')
            
            # Track sources for each stock
            ticker = cleaned_forecast['stock_ticker']
            if ticker not in stock_sources:
                stock_sources[ticker] = []
            stock_sources[ticker].extend(cleaned_forecast.get('sources', []))
            
            cleaned_stock_data.append(cleaned_forecast)

        # Get prompt config
        prompt_config = await self.get_prompt_config("portfolio_basket")

        # Get completion
        response, invocation_id = await self.get_completion(
            prompt_config=prompt_config,
            params={
                "STOCK_DATA": json.dumps(cleaned_stock_data, indent=2),
                "FILTER_TOP_N": str(filter_top_n),
                "BASKET_SIZE_K": str(basket_size_k)
            }
        )

        # Parse results
        try:
            basket_data = self._parse_json_response(response['choices'][0]['message']['content'])
            
            # Create BasketStock objects
            stocks = []
            for stock in basket_data["stocks"]:
                basket_stock = BasketStock(
                    stock_ticker=stock["stock_ticker"],
                    weight=stock["weight"],
                    sources=stock.get("sources", [])
                )
                stocks.append(basket_stock)

            # Create and store basket
            basket = Basket(
                creation_date=datetime.now(timezone.utc),
                invocation_id=invocation_id,
                stocks_ticker_candidates=[stock["stock_ticker"] for stock in stock_data],
                stocks=stocks,
                reason_summary=basket_data["reason_summary"],
                expected_gain_1m=basket_data["expected_gain_1m"]
            )
            await async_db[COLLECTIONS["baskets"]].insert_one(basket.model_dump())

            return basket

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")
