"""
Stock research agent for analyzing and forecasting stock prices using Google Gemini models.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import aiohttp

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
        """Format yfinance data into a structured format for the LLM.
        
        Args:
            yfinance_data: Raw yfinance data
            
        Returns:
            Formatted string for LLM consumption
        """
        if "error" in yfinance_data:
            return f"Error fetching yfinance data: {yfinance_data['error']}"
        
        # Format the data in a clear, structured way
        formatted_data = []
        
        # Basic company info
        formatted_data.append("=== COMPANY INFORMATION ===")
        formatted_data.append(f"Company: {yfinance_data.get('company_name', 'N/A')}")
        formatted_data.append(f"Sector: {yfinance_data.get('sector', 'N/A')}")
        formatted_data.append(f"Industry: {yfinance_data.get('industry', 'N/A')}")
        formatted_data.append(f"Website: {yfinance_data.get('website', 'N/A')}")
        
        # Market data
        formatted_data.append("\n=== CURRENT MARKET DATA ===")
        formatted_data.append(f"Current Price: ₹{yfinance_data.get('current_price', 'N/A')}")
        formatted_data.append(f"Day High: ₹{yfinance_data.get('day_high', 'N/A')}")
        formatted_data.append(f"Day Low: ₹{yfinance_data.get('day_low', 'N/A')}")
        formatted_data.append(f"Volume: {yfinance_data.get('volume', 'N/A'):,}" if yfinance_data.get('volume') else "Volume: N/A")
        formatted_data.append(f"Market Cap: ₹{yfinance_data.get('market_cap', 'N/A'):,.0f}" if yfinance_data.get('market_cap') else "Market Cap: N/A")
        
        # Technical indicators
        formatted_data.append("\n=== TECHNICAL INDICATORS ===")
        formatted_data.append(f"Beta: {yfinance_data.get('beta', 'N/A')}")
        formatted_data.append(f"52-Week High: ₹{yfinance_data.get('fifty_two_week_high', 'N/A')}")
        formatted_data.append(f"52-Week Low: ₹{yfinance_data.get('fifty_two_week_low', 'N/A')}")
        formatted_data.append(f"50-Day Average: ₹{yfinance_data.get('fifty_day_average', 'N/A')}")
        formatted_data.append(f"200-Day Average: ₹{yfinance_data.get('two_hundred_day_average', 'N/A')}")
        
        # Valuation metrics
        formatted_data.append("\n=== VALUATION METRICS ===")
        formatted_data.append(f"Trailing PE: {yfinance_data.get('trailing_pe', 'N/A')}")
        formatted_data.append(f"Forward PE: {yfinance_data.get('forward_pe', 'N/A')}")
        formatted_data.append(f"Price to Book: {yfinance_data.get('price_to_book', 'N/A')}")
        formatted_data.append(f"Price to Sales: {yfinance_data.get('price_to_sales', 'N/A')}")
        formatted_data.append(f"PEG Ratio: {yfinance_data.get('peg_ratio', 'N/A')}")
        
        # Financial ratios
        formatted_data.append("\n=== FINANCIAL RATIOS ===")
        formatted_data.append(f"Debt to Equity: {yfinance_data.get('debt_to_equity', 'N/A')}")
        formatted_data.append(f"Return on Equity: {yfinance_data.get('return_on_equity', 'N/A')}")
        formatted_data.append(f"Return on Assets: {yfinance_data.get('return_on_assets', 'N/A')}")
        formatted_data.append(f"Operating Margin: {yfinance_data.get('operating_margins', 'N/A')}")
        formatted_data.append(f"Profit Margin: {yfinance_data.get('profit_margins', 'N/A')}")
        
        # Growth metrics
        formatted_data.append("\n=== GROWTH METRICS ===")
        formatted_data.append(f"Revenue Growth: {yfinance_data.get('revenue_growth', 'N/A')}")
        formatted_data.append(f"Earnings Growth: {yfinance_data.get('earnings_growth', 'N/A')}")
        
        # Historical data
        hist_data = yfinance_data.get('historical_data', {})
        if hist_data:
            formatted_data.append("\n=== RECENT PRICE PERFORMANCE (30 days) ===")
            formatted_data.append(f"Days Available: {hist_data.get('days_available', 'N/A')}")
            formatted_data.append(f"Latest Close: ₹{hist_data.get('latest_close', 'N/A')}")
            formatted_data.append(f"30-Day High: ₹{hist_data.get('thirty_day_high', 'N/A')}")
            formatted_data.append(f"30-Day Low: ₹{hist_data.get('thirty_day_low', 'N/A')}")
            formatted_data.append(f"30-Day Change: {hist_data.get('thirty_day_change_pct', 'N/A')}%")
            formatted_data.append(f"Average Volume: {hist_data.get('average_volume', 'N/A'):,.0f}" if hist_data.get('average_volume') else "Average Volume: N/A")
            formatted_data.append(f"Volume Trend: {hist_data.get('volume_trend', 'N/A')}")
        
        # Financial statements
        financials = yfinance_data.get('financials', {})
        if financials and financials.get('quarters_available', 0) > 0:
            formatted_data.append("\n=== FINANCIAL STATEMENTS ===")
            formatted_data.append(f"Quarters Available: {financials.get('quarters_available', 'N/A')}")
            formatted_data.append(f"Latest Quarter: {financials.get('latest_quarter', 'N/A')}")
            formatted_data.append(f"Total Revenue: ₹{financials.get('total_revenue', 'N/A'):,.0f}" if financials.get('total_revenue') else "Total Revenue: N/A")
            formatted_data.append(f"Net Income: ₹{financials.get('net_income', 'N/A'):,.0f}" if financials.get('net_income') else "Net Income: N/A")
            formatted_data.append(f"EBITDA: ₹{financials.get('ebitda', 'N/A'):,.0f}" if financials.get('ebitda') else "EBITDA: N/A")
            formatted_data.append(f"Operating Income: ₹{financials.get('operating_income', 'N/A'):,.0f}" if financials.get('operating_income') else "Operating Income: N/A")
        
        # Balance sheet
        balance_sheet = yfinance_data.get('balance_sheet', {})
        if balance_sheet and balance_sheet.get('quarters_available', 0) > 0:
            formatted_data.append("\n=== BALANCE SHEET ===")
            formatted_data.append(f"Total Assets: ₹{balance_sheet.get('total_assets', 'N/A'):,.0f}" if balance_sheet.get('total_assets') else "Total Assets: N/A")
            formatted_data.append(f"Total Debt: ₹{balance_sheet.get('total_debt', 'N/A'):,.0f}" if balance_sheet.get('total_debt') else "Total Debt: N/A")
            formatted_data.append(f"Common Stock Equity: ₹{balance_sheet.get('common_stock_equity', 'N/A'):,.0f}" if balance_sheet.get('common_stock_equity') else "Common Stock Equity: N/A")
            formatted_data.append(f"Working Capital: ₹{balance_sheet.get('working_capital', 'N/A'):,.0f}" if balance_sheet.get('working_capital') else "Working Capital: N/A")
        
        # Cash flow
        cash_flow = yfinance_data.get('cash_flow', {})
        if cash_flow and cash_flow.get('quarters_available', 0) > 0:
            formatted_data.append("\n=== CASH FLOW ===")
            formatted_data.append(f"Free Cash Flow: ₹{cash_flow.get('free_cash_flow', 'N/A'):,.0f}" if cash_flow.get('free_cash_flow') else "Free Cash Flow: N/A")
            formatted_data.append(f"Operating Cash Flow: ₹{cash_flow.get('operating_cash_flow', 'N/A'):,.0f}" if cash_flow.get('operating_cash_flow') else "Operating Cash Flow: N/A")
            formatted_data.append(f"Capital Expenditure: ₹{cash_flow.get('capital_expenditure', 'N/A'):,.0f}" if cash_flow.get('capital_expenditure') else "Capital Expenditure: N/A")
        
        # Corporate events
        corporate_events = yfinance_data.get('corporate_events', {})
        if corporate_events:
            formatted_data.append("\n=== CORPORATE EVENTS ===")
            formatted_data.append(f"Ex-Dividend Date: {corporate_events.get('ex_dividend_date', 'N/A')}")
            earnings_dates = corporate_events.get('earnings_dates')
            if earnings_dates:
                if isinstance(earnings_dates, list):
                    formatted_data.append(f"Earnings Dates: {', '.join([str(d) for d in earnings_dates])}")
                else:
                    formatted_data.append(f"Earnings Date: {earnings_dates}")
            formatted_data.append(f"Earnings Estimate (High): {corporate_events.get('earnings_estimate_high', 'N/A')}")
            formatted_data.append(f"Earnings Estimate (Low): {corporate_events.get('earnings_estimate_low', 'N/A')}")
            formatted_data.append(f"Earnings Estimate (Average): {corporate_events.get('earnings_estimate_average', 'N/A')}")
        
        # Dividends and splits
        dividends = yfinance_data.get('dividends', {})
        if dividends and dividends.get('total_dividends', 0) > 0:
            formatted_data.append("\n=== DIVIDENDS ===")
            formatted_data.append(f"Total Dividends: {dividends.get('total_dividends', 'N/A')}")
            formatted_data.append(f"Latest Dividend: ₹{dividends.get('latest_dividend', 'N/A')}")
            formatted_data.append(f"Latest Dividend Date: {dividends.get('latest_dividend_date', 'N/A')}")
        
        splits = yfinance_data.get('splits', {})
        if splits and splits.get('total_splits', 0) > 0:
            formatted_data.append("\n=== STOCK SPLITS ===")
            formatted_data.append(f"Total Splits: {splits.get('total_splits', 'N/A')}")
            formatted_data.append(f"Latest Split: {splits.get('latest_split', 'N/A')}")
            formatted_data.append(f"Latest Split Date: {splits.get('latest_split_date', 'N/A')}")
        
        # Shareholder information
        shareholders = yfinance_data.get('shareholders', {})
        if shareholders:
            formatted_data.append("\n=== SHAREHOLDER INFORMATION ===")
            insiders_pct = shareholders.get('insiders_percent_held')
            institutions_pct = shareholders.get('institutions_percent_held')
            institutions_count = shareholders.get('institutions_count')
            
            if insiders_pct is not None:
                formatted_data.append(f"Insiders % Held: {insiders_pct:.2f}%")
            else:
                formatted_data.append("Insiders % Held: N/A")
                
            if institutions_pct is not None:
                formatted_data.append(f"Institutions % Held: {institutions_pct:.2f}%")
            else:
                formatted_data.append("Institutions % Held: N/A")
                
            if institutions_count is not None:
                formatted_data.append(f"Institutions Count: {institutions_count}")
            else:
                formatted_data.append("Institutions Count: N/A")
        
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
