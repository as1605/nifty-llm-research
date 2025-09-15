"""
Stock research agent for analyzing and forecasting stock prices using Google Gemini models.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import aiohttp
import pandas as pd

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Forecast, ListForecast
from src.services.yfinance_service import YFinanceService

from .base import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class StockResearchAgent(BaseAgent):
    """Agent for analyzing stocks and generating price forecasts using Google Gemini models."""

    def __init__(self):
        """Initialize the stock research agent."""
        super().__init__()
        self.yfinance_service = YFinanceService()

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
                    # Ensure URL has protocol
                    if not url.startswith(('http://', 'https://')):
                        url = f"https://{url}"
                        logger.info(f"Added protocol to URL: {url}")
                    
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

    def _format_yfinance_data_for_llm(self, yfinance_data: Dict[str, Any]) -> str:
        """Format yfinance data into the new structured format for the LLM.
        
        Args:
            yfinance_data: Raw yfinance data in new format
            
        Returns:
            Formatted string for LLM consumption
        """
        if "error" in yfinance_data:
            return f"Error fetching yfinance data: {yfinance_data['error']}"
        
        # Format the data in the new structured way
        formatted_data = []
        
        # Header
        company_name = yfinance_data.get('company_name', 'N/A')
        ticker = yfinance_data.get('ticker', 'N/A')
        data_date = yfinance_data.get('data_date', 'N/A')
        
        formatted_data.append(f"**Stock Analysis Data for: {company_name} ({ticker})**")
        formatted_data.append(f"**Date of Data:** {data_date}")
        formatted_data.append("---")
        
        # Key Information section
        formatted_data.append("**## Key Information**")
        
        # Helper function to format values
        def format_value(value, prefix="", suffix=""):
            if value is None or value == "N/A" or (isinstance(value, float) and pd.isna(value)):
                return "N/A"
            return f"{prefix}{value}{suffix}"
        
        # Format 52-week range
        week_52_high = yfinance_data.get('fifty_two_week_high', 'N/A')
        week_52_low = yfinance_data.get('fifty_two_week_low', 'N/A')
        week_52_range = f"₹{week_52_low} - ₹{week_52_high}" if week_52_low != "N/A" and week_52_high != "N/A" else "N/A"
        
        # Format day's range
        day_high = yfinance_data.get('day_high', 'N/A')
        day_low = yfinance_data.get('day_low', 'N/A')
        day_range = f"₹{day_low} - ₹{day_high}" if day_low != "N/A" and day_high != "N/A" else "N/A"
        
        formatted_data.append(f"- **Beta:** {format_value(yfinance_data.get('beta'))}")
        formatted_data.append(f"- **52-Week Range:** {week_52_range}")
        formatted_data.append(f"- **Previous Close:** {format_value(yfinance_data.get('previous_close'), '₹')}")
        formatted_data.append(f"- **10-Day Avg Volume:** {format_value(yfinance_data.get('ten_day_avg_volume'))}")
        formatted_data.append(f"- **Day's Range:** {day_range}")
        formatted_data.append("---")
        
        # Recent News Headlines section
        formatted_data.append("**## Recent News Headlines**")
        news_headlines = yfinance_data.get('news_headlines', [])
        if news_headlines:
            for headline in news_headlines:
                timestamp = headline.get('timestamp', 'N/A')
                title = headline.get('headline', 'N/A')
                publisher = headline.get('publisher', 'N/A')
                formatted_data.append(f"- **[{timestamp}]:** {title} (Publisher: {publisher})")
        else:
            formatted_data.append("- No recent news available")
        formatted_data.append("---")
        
        # Price and Volume History section
        formatted_data.append("**## Price and Volume History (Last 20 Days)**")
        historical_data = yfinance_data.get('historical_data', [])
        if historical_data:
            for day_data in historical_data:
                date = day_data.get('date', 'N/A')
                open_price = day_data.get('open', 'N/A')
                high_price = day_data.get('high', 'N/A')
                low_price = day_data.get('low', 'N/A')
                close_price = day_data.get('close', 'N/A')
                volume = day_data.get('volume', 'N/A')
                
                # Format volume with commas
                if isinstance(volume, int):
                    volume_str = f"{volume:,}"
                elif isinstance(volume, float):
                    volume_str = f"{volume:.2f}"
                else:
                    volume_str = str(volume)
                
                formatted_data.append(f"- **{date}:** Open: {open_price:.2f}, High: {high_price:.2f}, Low: {low_price:.2f}, Close: {close_price:.2f}, Volume: {volume_str}")
        else:
            formatted_data.append("- No historical data available")
        
        return "\n".join(formatted_data)

    async def analyze_stock(self, symbol: str, force: bool = False) -> List[Dict[str, Any]]:
        """Analyze a stock and generate price forecasts.

        Args:
            symbol: The stock symbol (NSE format, e.g., 'RELIANCE', 'OLECTRA')
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

        # Fetch comprehensive yfinance data
        logger.info(f"Fetching yfinance data for {symbol}")
        yfinance_data = self.yfinance_service.get_stock_info(symbol)
        
        if "error" in yfinance_data:
            logger.warning(f"Failed to fetch yfinance data for {symbol}: {yfinance_data['error']}")
            yfinance_data = {}  # Use empty dict to avoid errors
        
        # Format yfinance data for LLM consumption
        yfinance_formatted = self._format_yfinance_data_for_llm(yfinance_data)
        
        # Get prompt config
        prompt_config = await self.get_prompt_config("stock_research_forecast_short_term")

        # Get completion with yfinance data included
        response, invocation_id = await self.get_completion(
            prompt_config=prompt_config,
            params={
                "TICKER": symbol,
                "YFINANCE_DATA": yfinance_formatted
            }
        )

        # Parse results
        try:
            # First parse the JSON response
            response_data = self._parse_json_response(response['choices'][0]['message']['content'])
            
            # Then construct the ListForecast object
            list_forecast = ListForecast.model_validate(response_data)
            
            # Process each forecast in the result
            forecasts = []
            
            # Fetch current LTP once for gain calculation
            ltp = self.yfinance_service.get_stock_ltp(symbol)
            if ltp is None:
                logger.warning(f"LTP unavailable for {symbol}; gain will default to 0.0")
            
            for forecast_data in list_forecast.forecasts:
                # Validate and parse forecast date
                forecast_date = self._validate_forecast_date(
                    forecast_data.forecast_date,
                    forecast_data.days
                )
                
                # Process sources to resolve URLs
                processed_sources = await self._process_sources(forecast_data.sources)
                
                # Calculate gain using LTP and target price
                target_price = float(forecast_data.target_price)
                if ltp is not None and ltp > 0:
                    computed_gain = ((target_price - float(ltp)) / float(ltp)) * 100.0
                else:
                    computed_gain = 0.0
                
                # Compare with LLM-provided gain and warn if off by more than 1%
                try:
                    if ltp is not None and ltp > 0 and getattr(forecast_data, 'gain', None) is not None:
                        llm_gain = float(forecast_data.gain)
                        if abs(computed_gain - llm_gain) > 1.0:
                            logger.warning(
                                f"Computed gain differs from LLM gain for {symbol} ({forecast_data.days}d): "
                                f"computed={computed_gain:.2f}% vs llm={llm_gain:.2f}% | "
                                f"ltp={ltp}, target={target_price}"
                            )
                except Exception as warn_ex:
                    logger.debug(f"Unable to compare computed gain with LLM gain: {warn_ex}")
                
                # Create and store forecast
                forecast = Forecast(
                    stock_ticker=symbol,
                    invocation_id=invocation_id,
                    forecast_date=forecast_date,
                    target_price=target_price,
                    days=forecast_data.days,
                    reason_summary=forecast_data.reason_summary,
                    sources=processed_sources,
                    gain=float(computed_gain)
                )
                await async_db[COLLECTIONS["forecasts"]].insert_one(forecast.model_dump())
                
                forecasts.append({
                    "timeframe": f"{forecast_data.days}d",
                    "target_price": target_price,
                    "reasoning": forecast_data.reason_summary,
                    "sources": processed_sources,
                    "gain": computed_gain,
                    "invocation_id": invocation_id
                })

            return forecasts

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")
