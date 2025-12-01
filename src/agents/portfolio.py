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
from src.services.yfinance_service import YFinanceService
from src.utils.data_utils import round_floats_to_2_decimals

from .base import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

class PortfolioAgent(BaseAgent):
    """Agent for optimizing stock portfolios."""

    def __init__(self):
        """Initialize the portfolio agent."""
        super().__init__()
        self.yfinance_service = YFinanceService()

    async def _get_top_stocks(
        self,
        index: str,
        since_time: datetime,
        filter_top_n: int,
        force_llm: bool = False
    ) -> List[Dict[str, Any]]:
        """Get top performing stocks based on latest forecasts.
        
        Args:
            index: Index to filter stocks by
            since_time: Only consider forecasts after this time
            filter_top_n: Number of top stocks to return
            force_llm: If True, require at least 5 forecasts per stock (unused, kept for compatibility)
            
        Returns:
            List of latest forecast for the top N stocks by gain of latest forecast
        """
        # First get all stocks in the index
        stocks = await async_db[COLLECTIONS["stocks"]].find(
            {"indices": index}
        ).to_list(length=None)
        
        if not stocks:
            raise ValueError(f"No stocks found for index {index}")
            
        tickers = [stock["ticker"] for stock in stocks]
        
        # Use MongoDB aggregation to get averaged 7-day forecast metrics for each stock
        pipeline = [
            # Match forecasts for stocks in the index after since_time, only 7-day forecasts
            {
                "$match": {
                    "stock_ticker": {"$in": tickers},
                    "created_time": {"$gte": since_time},
                    "days": 7
                }
            },
            # Sort by stock_ticker and created_time descending to get latest first
            {"$sort": {"stock_ticker": 1, "created_time": -1}},
            # Group by stock_ticker, keeping the latest doc but averaging numeric metrics
            {
                "$group": {
                    "_id": "$stock_ticker",
                    "latest_forecast": {"$first": "$$ROOT"},
                    "avg_gain": {"$avg": "$gain"},
                    "avg_target_price": {"$avg": "$target_price"},
                    "forecast_count": {"$sum": 1}
                }
            },
            # Sort by average gain in descending order
            {"$sort": {"avg_gain": -1}},
            # Limit to top N stocks
            {"$limit": filter_top_n},
            # Project only the forecast data
            {
                "$project": {
                    "_id": 0,
                    "forecast": {
                        "$mergeObjects": [
                            "$latest_forecast",
                            {
                                "gain": "$avg_gain",
                                "target_price": "$avg_target_price",
                                "forecast_count": "$forecast_count"
                            }
                        ]
                    }
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

        # Get unique tickers to fetch financial data
        unique_tickers = list(set([forecast['stock_ticker'] for forecast in stock_data]))
        
        # Fetch LTP and OHLC data for each unique ticker
        logger.info(f"Fetching LTP and OHLC data for {len(unique_tickers)} stocks")
        ticker_financial_data = {}
        for ticker in unique_tickers:
            try:
                # Get LTP
                ltp = self.yfinance_service.get_stock_ltp(ticker)
                
                # Get OHLC for last 5 trading days
                ohlc_data = self.yfinance_service.get_stock_ohlc_last_5_days(ticker)
                
                ticker_financial_data[ticker] = {
                    "ltp": ltp,
                    "ohlc_last_5_days": ohlc_data
                }
            except Exception as e:
                logger.warning(f"Failed to fetch financial data for {ticker}: {e}")
                ticker_financial_data[ticker] = {
                    "ltp": None,
                    "ohlc_last_5_days": []
                }
        
        # Check if we have any forecasts
        if not stock_data:
            raise ValueError(
                f"No 7-day forecasts found for stocks in {index}. "
                "Ensure that stock analysis has been run and forecasts have been generated."
            )
        
        # Clean forecast data by removing MongoDB specific fields and add financial data
        cleaned_stock_data = []
        
        # stock_data already contains one 7-day forecast per stock with averaged metrics (from MongoDB aggregation)
        # Process each forecast
        for forecast in stock_data:
            ticker = forecast['stock_ticker']
            cleaned_forecast = forecast.copy()
            # Remove MongoDB specific fields
            cleaned_forecast.pop('_id', None)
            cleaned_forecast.pop('invocation_id', None)
            cleaned_forecast.pop('created_time', None)
            cleaned_forecast.pop('modified_time', None)
            
            # Convert forecast_date to simple date string
            if 'forecast_date' in cleaned_forecast:
                if isinstance(cleaned_forecast['forecast_date'], datetime):
                    cleaned_forecast['forecast_date'] = cleaned_forecast['forecast_date'].strftime('%Y-%m-%d')
            
            # Add financial data
            financial_data = ticker_financial_data.get(ticker, {})
            cleaned_forecast['ltp'] = financial_data.get('ltp')
            cleaned_forecast['ohlc_last_5_days'] = financial_data.get('ohlc_last_5_days', [])
            
            cleaned_stock_data.append(cleaned_forecast)

        # Round all floating point numbers to 2 decimal places before passing to LLM
        cleaned_stock_data = round_floats_to_2_decimals(cleaned_stock_data)

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
            ticker_to_weight = {}
            for stock in basket_data["stocks"]:
                basket_stock = BasketStock(
                    stock_ticker=stock["stock_ticker"],
                    weight=stock["weight"],
                    sources=stock.get("sources", [])
                )
                stocks.append(basket_stock)
                ticker_to_weight[stock["stock_ticker"]] = stock["weight"]

            # Calculate expected_gain_1w as weighted average of 1-week (7d) gains
            # Use the cleaned stock data which already has averaged 7-day forecasts
            # Since cleaned_stock_data has one forecast per ticker (averaged), we can directly use it
            ticker_to_gain = {}
            for cleaned_forecast in cleaned_stock_data:
                ticker = cleaned_forecast["stock_ticker"]
                # All forecasts in cleaned_stock_data are 7-day forecasts
                if cleaned_forecast.get("gain") is not None:
                    ticker_to_gain[ticker] = cleaned_forecast["gain"]
                else:
                    ticker_to_gain[ticker] = 0.0
            
            # Set default 0.0 for any tickers in basket that don't have gain data
            for ticker in ticker_to_weight:
                if ticker not in ticker_to_gain:
                    ticker_to_gain[ticker] = 0.0
                    logger.warning(f"No gain data found for {ticker} in basket, using 0.0")
            
            # Weighted average (using latest forecast gain for each stock)
            expected_gain_1w = sum(
                ticker_to_gain[ticker] * ticker_to_weight[ticker]
                for ticker in ticker_to_weight
            )

            # Ensure stocks_ticker_candidates are unique - use all unique tickers from cleaned_stock_data
            unique_ticker_candidates = list({stock["stock_ticker"] for stock in cleaned_stock_data})

            # Create and store basket
            basket = Basket(
                creation_date=datetime.now(timezone.utc),
                invocation_id=invocation_id,
                stocks_ticker_candidates=unique_ticker_candidates,
                stocks=stocks,
                reason_summary=basket_data["reason_summary"],
                expected_gain_1w=expected_gain_1w
            )
            await async_db[COLLECTIONS["baskets"]].insert_one(basket.model_dump())

            return basket

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")
