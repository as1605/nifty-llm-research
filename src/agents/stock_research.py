"""
Stock research agent for analyzing and forecasting stock prices using Perplexity models.
"""

import logging
from datetime import datetime, timezone, timedelta
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
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        
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
                        "forecasts": [
                            {
                                "timeframe": f"{f['days']}d",
                                "target_price": f["target_price"],
                                "reasoning": f["reason_summary"],
                                "sources": f.get("sources", [])
                            }
                            for f in recent_forecasts
                        ]
                    }
                }

        # Get stock data from database
        stock = await async_db[COLLECTIONS["stocks"]].find_one({"ticker": symbol})
        if not stock:
            raise ValueError(f"Stock {symbol} not found in database")

        # Get prompt config
        prompt_config = await self.get_prompt_config("stock_research_forecast")

        # Get completion
        response, invocation_id = await self.get_completion(
            prompt_config=prompt_config,
            params={"TICKER": symbol}
        )

        # Parse results
        try:
            result = self._parse_json_response(response['choices'][0]['message']['content'])
            
            # Store forecast
            forecast = Forecast(
                stock_ticker=symbol,
                invocation_id=invocation_id,
                forecast_date=datetime.now(timezone.utc),
                target_price=result["target_price"],
                gain=result["gain"],
                days=result["days"],
                reason_summary=result["reason_summary"],
                sources=result.get("sources", [])
            )
            await async_db[COLLECTIONS["forecasts"]].insert_one(forecast.model_dump())

            return {
                "stock_data": {
                    "forecasts": [
                        {
                            "timeframe": f"{result['days']}d",
                            "target_price": result["target_price"],
                            "reasoning": result["reason_summary"],
                            "sources": result.get("sources", [])
                        }
                    ]
                }
            }

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")
