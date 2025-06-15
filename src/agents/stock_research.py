"""
Stock research agent for analyzing and forecasting stock prices using Perplexity models.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import aiohttp

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Forecast, ListForecast

from .base import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class StockResearchAgent(BaseAgent):
    """Agent for analyzing stocks and generating price forecasts using Perplexity models."""

    def __init__(self):
        """Initialize the stock research agent."""
        super().__init__()

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
        """Process a list of source URLs, checking response status and following redirects.
        
        Args:
            sources: List of source URLs
            
        Returns:
            List of processed URLs
        """
        if not sources:
            return []
            
        processed_sources = []
        async with aiohttp.ClientSession() as session:
            for url in sources:
                try:
                    async with session.get(url, allow_redirects=False) as response:
                        if response.status == 302:
                            location = response.headers.get("Location")
                            if location:
                                logger.info(f"Following redirect: {url} -> {location}")
                                processed_sources.append(location)
                            else:
                                logger.warning(f"Redirect without Location header: {url}")
                        elif response.status in [400, 404, 500, 501, 502, 503, 504]:
                            logger.warning(f"Invalid or unavailable source URL: {url} (Status: {response.status})")
                        else:
                            processed_sources.append(url)
                except Exception as e:
                    logger.error(f"Error processing source URL {url}: {str(e)}")
                    
        return processed_sources

    def _validate_forecast_date(self, forecast_date_str: str | datetime, days: int) -> datetime:
        """Validate that the forecast date is approximately current date + days.
        
        Args:
            forecast_date_str: The forecast date string in YYYY-MM-DD format or datetime object
            days: Number of days to add to current date
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValueError: If the date format is invalid or the date differs significantly
        """
        try:
            # If already a datetime object, just ensure it has timezone
            if isinstance(forecast_date_str, datetime):
                forecast_date = forecast_date_str.replace(tzinfo=timezone.utc)
            else:
                # Parse string date
                forecast_date = datetime.strptime(forecast_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
            expected_date = datetime.now(timezone.utc) + timedelta(days=days)
            date_diff = abs((forecast_date - expected_date).days)
            
            if date_diff > 2:
                logger.warning(
                    f"Forecast date {forecast_date} differs significantly from expected date "
                    f"{expected_date} (difference: {date_diff} days)"
                )
                
            return forecast_date
            
        except ValueError as e:
            raise ValueError(f"Invalid forecast date format: {forecast_date_str}. Expected YYYY-MM-DD") from e

    async def analyze_stock(self, symbol: str, force: bool = False) -> List[Dict[str, Any]]:
        """Analyze a stock and generate price forecasts.

        Args:
            symbol: The stock symbol (NSE format)
            force: If True, force new analysis even if recent forecasts exist

        Returns:
            List of forecasts for the stock
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
                return recent_forecasts

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
            # First parse the JSON response
            response_data = self._parse_json_response(response['choices'][0]['message']['content'])
            
            # Then construct the ListForecast object
            list_forecast = ListForecast.model_validate(response_data)
            
            # Process each forecast in the result
            forecasts = []
            
            for forecast_data in list_forecast.forecasts:
                # Validate and parse forecast date
                forecast_date = self._validate_forecast_date(
                    forecast_data.forecast_date,
                    forecast_data.days
                )
                
                # Process sources to resolve URLs
                processed_sources = await self._process_sources(forecast_data.sources)
                
                # Create and store forecast
                forecast = Forecast(
                    stock_ticker=symbol,
                    invocation_id=invocation_id,
                    forecast_date=forecast_date,
                    target_price=float(forecast_data.target_price),
                    days=forecast_data.days,
                    reason_summary=forecast_data.reason_summary,
                    sources=processed_sources,
                    gain=float(forecast_data.gain)
                )
                await async_db[COLLECTIONS["forecasts"]].insert_one(forecast.model_dump())
                
                forecasts.append({
                    "timeframe": f"{forecast_data.days}d",
                    "target_price": forecast_data.target_price,
                    "reasoning": forecast_data.reason_summary,
                    "sources": processed_sources,
                    "gain": forecast_data.gain,
                    "invocation_id": invocation_id
                })

            return forecasts

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")
