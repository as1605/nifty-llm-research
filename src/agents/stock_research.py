"""
Stock research agent for analyzing and forecasting stock prices using Perplexity models.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import aiohttp
from urllib.parse import urlparse

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Forecast
from src.db.models import Stock

from .base import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class StockResearchAgent(BaseAgent):
    """Agent for analyzing stocks and generating price forecasts using Perplexity models."""

    def __init__(self):
        """Initialize the stock research agent."""
        super().__init__()

    def _get_days_from_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to number of days.
        
        Args:
            timeframe: Timeframe string (1w, 1m, 3m, 6m, 1y)
            
        Returns:
            Number of days
        """
        timeframe_map = {
            "1w": 7,
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365
        }
        return timeframe_map.get(timeframe, 0)

    async def _get_recent_forecasts(self, symbol: str, hours_threshold: int = 12) -> List[Dict[str, Any]]:
        """Get recent forecasts for a stock.
        
        Args:
            symbol: Stock symbol
            hours_threshold: Hours threshold for considering forecasts recent
            
        Returns:
            List of recent forecasts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)
        
        forecasts = await async_db[COLLECTIONS["forecasts"]].find({
            "stock_ticker": symbol,
            "created_time": {"$gte": cutoff_time}
        }).to_list(length=None)
        
        return forecasts

    async def _resolve_vertex_url(self, url: str) -> str:
        """Resolve Vertex AI Search redirect URLs to their final destination.
        
        Args:
            url: The URL to resolve
            
        Returns:
            The final URL after following redirects
        """
        if not url.startswith("https://vertexaisearch.cloud.google.com/grounding-api-redirect"):
            return url
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, allow_redirects=False) as response:
                    if response.status == 302:
                        location = response.headers.get("Location")
                        if location:
                            logger.info(f"Resolved Vertex AI URL: {url} -> {location}")
                            return location
                    logger.warning(f"Vertex AI URL did not return 302: {url}")
                    return url
        except Exception as e:
            logger.error(f"Error resolving Vertex AI URL {url}: {e}")
            return url

    async def _process_sources(self, sources: List[str]) -> List[str]:
        """Process a list of source URLs, resolving any Vertex AI redirects.
        
        Args:
            sources: List of source URLs
            
        Returns:
            List of processed URLs
        """
        if not sources:
            return []
            
        processed_sources = []
        for url in sources:
            final_url = await self._resolve_vertex_url(url)
            processed_sources.append(final_url)
            
        return processed_sources

    async def analyze_stock(self, symbol: str, force: bool = False) -> dict:
        """Analyze a stock and generate price forecasts.

        Args:
            symbol: The stock symbol (NSE format)
            force: If True, force new analysis even if recent forecasts exist

        Returns:
            Dictionary containing forecasts and analysis
        """
        logger.info(f"Starting analysis for {symbol} (force={force})")
        
        # Check for recent forecasts if not forcing
        if not force:
            recent_forecasts = await self._get_recent_forecasts(symbol)
            if recent_forecasts:
                logger.info(
                    f"Found {len(recent_forecasts)} recent forecasts for {symbol} "
                    f"within last 12 hours. Using cached forecasts."
                )
                return {
                    "stock_data": {
                        "current_price": recent_forecasts[0].get("target_price", 0),
                        "market_cap": recent_forecasts[0].get("market_cap", 0),
                        "industry": recent_forecasts[0].get("industry", "Unknown"),
                        "forecasts": [
                            {
                                "timeframe": f"{f['days']}d",
                                "target_price": f["target_price"],
                                "reasoning": f["reason_summary"],
                                "sources": f.get("sources", [])
                            }
                            for f in recent_forecasts
                        ]
                    },
                    "forecasts": recent_forecasts
                }
        
        # Get prompt config for deep research
        research_config = await self.get_prompt_config("stock_research_forecast")
        logger.info(f"Using research model: {research_config.model}")

        # Get deep research completion
        logger.info(f"Requesting research analysis for {symbol}")
        research_response, research_invocation_id = await self.get_completion(
            prompt_config=research_config,
            params={"TICKER": symbol}
        )

        # Parse research data with fallback
        try:
            stock_data = self._parse_json_response(research_response['choices'][0]['message']['content'])
            logger.info(f"Successfully parsed research data for {symbol}")
        except ValueError as e:
            logger.error(f"Failed to parse research data for {symbol}: {e}")
            raise

        # Store stock data
        stock = Stock(
            ticker=symbol,
            price=stock_data["current_price"],
            market_cap=stock_data["market_cap"],
            industry=stock_data.get("industry", "Unknown"),
        )
        await async_db[COLLECTIONS["stocks"]].update_one(
            {"ticker": symbol}, {"$set": stock.model_dump()}, upsert=True
        )
        logger.info(f"Updated stock data for {symbol}: Price={stock.price}, Market Cap={stock.market_cap}")

        # Process and store each forecast
        current_price = stock_data["current_price"]
        forecasts = []
        
        logger.info(f"Processing forecasts for {symbol}")
        for forecast_data in stock_data["forecasts"]:
            # Get days from timeframe
            days_ahead = self._get_days_from_timeframe(forecast_data["timeframe"])
            if days_ahead == 0:
                logger.warning(f"Skipping invalid timeframe: {forecast_data['timeframe']}")
                continue
            
            # Calculate target date
            target_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            # Calculate percentage gain
            gain = ((forecast_data["target_price"] - current_price) / current_price) * 100
            
            # Process sources
            forecast_sources = await self._process_sources(forecast_data.get("sources", []))
            stock_sources = await self._process_sources(stock_data.get("sources", []))
            all_sources = list(set(forecast_sources + stock_sources))  # Remove duplicates
            
            # Log forecast details
            logger.info(
                f"Forecast for {symbol} ({forecast_data['timeframe']}): "
                f"Target Price={forecast_data['target_price']:.2f}, "
                f"Gain={gain:.2f}%, "
                f"Sources={len(all_sources)}"
            )
            
            # Create forecast object
            forecast = Forecast(
                stock_ticker=symbol,
                invocation_id=research_invocation_id,
                forecast_date=target_date,
                target_price=forecast_data["target_price"],
                gain=gain,
                days=days_ahead,
                reason_summary=forecast_data["reasoning"],
                sources=all_sources,
            )
            
            # Store forecast in database
            await async_db[COLLECTIONS["forecasts"]].insert_one(forecast.model_dump())
            forecasts.append(forecast.model_dump())
            logger.info(f"Stored {forecast_data['timeframe']} forecast for {symbol}")

        logger.info(f"Completed analysis for {symbol} with {len(forecasts)} forecasts")
        return {
            "stock_data": stock_data,
            "forecasts": forecasts
        }
