"""
Portfolio optimization agent for selecting the best stocks.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

import pandas as pd

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Basket

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
    ) -> dict:
        """Generate optimized portfolio recommendations.

        Args:
            index: Index to filter stocks by
            since_time: Only consider forecasts after this time
            filter_top_n: Number of top stocks to consider
            basket_size_k: Number of stocks to select for portfolio
            force_llm: If True, require at least 5 forecasts per stock

        Returns:
            Dictionary containing selected stocks and analysis
        """
        # Get top performing stocks
        stock_data = await self._get_top_stocks(index, since_time, filter_top_n, force_llm)
        
        if not stock_data:
            raise ValueError("No stock data available for portfolio optimization")

        # Clean forecast data by removing _id and invocation_id fields and converting dates
        cleaned_stock_data = []
        stock_sources = {}  # Dictionary to store sources for each stock
        
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
            
            # Store sources for this stock
            stock_ticker = cleaned_forecast.get('stock_ticker')
            if stock_ticker and 'sources' in cleaned_forecast:
                if stock_ticker not in stock_sources:
                    stock_sources[stock_ticker] = set()
                stock_sources[stock_ticker].update(cleaned_forecast['sources'])
                
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
            result = self._parse_json_response(response['choices'][0]['message']['content'])
            
            # Validate number of stocks selected
            if len(result["stocks_picked"]) != basket_size_k:
                logger.warning(
                    f"LLM selected {len(result['stocks_picked'])} stocks instead of "
                    f"requested {basket_size_k}"
                )

            # Add sources to the result
            result["stock_sources"] = {
                stock: list(stock_sources.get(stock, []))
                for stock in result["stocks_picked"]
            }

            # Store basket
            basket = Basket(
                creation_date=datetime.now(timezone.utc),
                stocks_ticker_candidates=[stock["stock_ticker"] for stock in stock_data],
                stocks_picked=result["stocks_picked"],
                weights=result["weights"],
                reason_summary=result["reason_summary"],
                expected_gain_1m=result["expected_gain_1m"],
            )
            await async_db[COLLECTIONS["baskets"]].insert_one(basket.model_dump())

            return result

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")

    def _calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional metrics for portfolio selection.

        Args:
            df: DataFrame of stock forecasts

        Returns:
            DataFrame with additional metrics
        """
        # Calculate potential returns
        df["1m_return"] = (df["forecast_1m"] - df["current_price"]) / df[
            "current_price"
        ]
        df["3m_return"] = (df["forecast_3m"] - df["current_price"]) / df[
            "current_price"
        ]
        df["6m_return"] = (df["forecast_6m"] - df["current_price"]) / df[
            "current_price"
        ]

        # Calculate volatility score (difference between highest and lowest forecasts)
        df["volatility"] = df[
            ["forecast_1w", "forecast_1m", "forecast_3m", "forecast_6m", "forecast_12m"]
        ].apply(lambda x: (max(x) - min(x)) / x.mean(), axis=1)

        return df
