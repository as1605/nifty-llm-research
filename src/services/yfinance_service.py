"""
YFinance service for fetching stock data and market information.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


class YFinanceService:
    """Service for fetching stock data using yfinance."""
    
    def __init__(self):
        """Initialize the yfinance service."""
        pass
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize stock symbol to ensure .NS suffix for NSE stocks.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'RELIANCE.NS', 'SBIN.BO', 'OLECTRA')
            
        Returns:
            Normalized symbol with .NS suffix (only if no other suffix exists)
        """
        if not symbol or not symbol.strip():
            return symbol
        
        # Clean and standardize the symbol
        symbol = symbol.upper().strip()
        
        # If symbol already has a suffix (contains a dot), return as-is
        if '.' in symbol:
            return symbol
        
        # If no suffix exists, add .NS for NSE stocks
        return f"{symbol}.NS"
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get stock information in the new format for LLM consumption.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'RELIANCE.NS', 'OLECTRA')
            
        Returns:
            Dictionary containing stock information in the new format
        """
        try:
            # Normalize symbol to ensure .NS suffix
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"Fetching stock info for {symbol} (normalized to {normalized_symbol})")
            
            ticker = yf.Ticker(normalized_symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get historical data for last 20 trading days
            hist = ticker.history(period='1mo')  # Get more data to ensure we have 20 trading days
            
            # Get news headlines
            news = ticker.news
            
            # Helper function to safely get values
            def safe_get(key, default="N/A"):
                value = info.get(key)
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    return default
                return value
            
            # Helper function to format price
            def format_price(price, default="N/A"):
                if price is None or (isinstance(price, float) and pd.isna(price)):
                    return default
                return f"₹{price:.2f}"
            
            # Helper function to format volume
            def format_volume(volume, default="N/A"):
                if volume is None or (isinstance(volume, float) and pd.isna(volume)):
                    return default
                return f"{volume:,.0f}"
            
            # Get 10-day average volume
            ten_day_avg_volume = None
            if not hist.empty and len(hist) >= 10:
                ten_day_avg_volume = hist['Volume'].tail(10).mean()
            elif not hist.empty:
                ten_day_avg_volume = hist['Volume'].mean()
            
            # Process historical data for last 20 days
            historical_data = []
            if not hist.empty:
                # Get last 20 trading days
                last_20_days = hist.tail(20)
                for date, row in last_20_days.iterrows():
                    historical_data.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": int(row['Volume'])
                    })
            
            # Process news headlines (limit to 3 most recent)
            news_headlines = []
            if news:
                for article in news[:3]:  # Limit to 3 most recent
                    news_headlines.append({
                        "timestamp": datetime.fromtimestamp(article.get('providerPublishTime', 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if article.get('providerPublishTime') else "N/A",
                        "headline": article.get('title', 'N/A'),
                        "publisher": article.get('publisher', 'N/A')
                    })
            
            # Compile data in new format
            stock_data = {
                "company_name": safe_get("longName", "N/A"),
                "ticker": normalized_symbol,
                "data_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                
                # Key Information
                "beta": safe_get("beta", "N/A"),
                "fifty_two_week_high": safe_get("fiftyTwoWeekHigh", "N/A"),
                "fifty_two_week_low": safe_get("fiftyTwoWeekLow", "N/A"),
                "previous_close": safe_get("previousClose", "N/A"),
                "ten_day_avg_volume": format_volume(ten_day_avg_volume, "N/A"),
                "day_high": safe_get("dayHigh", "N/A"),
                "day_low": safe_get("dayLow", "N/A"),
                
                # News headlines
                "news_headlines": news_headlines,
                
                # Historical data
                "historical_data": historical_data,
                
                # Data quality indicators
                "data_quality": {
                    "has_real_time_data": info.get("currentPrice") is not None,
                    "has_historical_data": not hist.empty,
                    "has_news": len(news) > 0,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info(f"Successfully fetched data for {normalized_symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "company_name": "N/A",
                "ticker": self._normalize_symbol(symbol),
                "data_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "data_quality": {
                    "has_real_time_data": False,
                    "has_historical_data": False,
                    "has_news": False,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            }
    
    def get_stock_ltp(self, symbol: str) -> Optional[float]:
        """Get Last Traded Price (LTP) for a stock - used for rebalancing.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'RELIANCE.NS', 'OLECTRA')
            
        Returns:
            Current stock price or None if error
        """
        try:
            # Normalize symbol to ensure .NS suffix
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"Fetching LTP for {symbol} (normalized to {normalized_symbol})")
            
            ticker = yf.Ticker(normalized_symbol)
            current_price = ticker.info.get("currentPrice")
            
            if current_price is not None:
                logger.info(f"Successfully fetched LTP for {normalized_symbol}: {current_price}")
                return float(current_price)
            else:
                logger.warning(f"No current price available for {normalized_symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching LTP for {symbol}: {e}")
            return None
    
    def get_multiple_stock_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """Get LTP for multiple stocks - used for portfolio rebalancing.
        
        Args:
            symbols: List of stock symbols (e.g., ['RELIANCE', 'SBIN', 'OLECTRA'])
            
        Returns:
            Dictionary mapping symbols to their current prices
        """
        results = {}
        
        for symbol in symbols:
            ltp = self.get_stock_ltp(symbol)
            if ltp is not None:
                results[symbol] = ltp
            else:
                logger.warning(f"Skipping {symbol} due to LTP fetch failure")
        
        logger.info(f"Successfully fetched LTP for {len(results)} out of {len(symbols)} stocks")
        return results
    
    def get_stock_ohlc_last_5_days(self, symbol: str) -> List[Dict[str, Any]]:
        """Get OHLC (Open, High, Low, Close) data for the last 5 trading days.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'RELIANCE.NS', 'OLECTRA')
            
        Returns:
            List of dictionaries containing OHLC data for last 5 trading days
            Each dictionary has: date, open, high, low, close
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            
            # Get historical data for last 5 trading days
            hist = ticker.history(period='5d')
            
            if hist.empty:
                logger.warning(f"No historical data available for {symbol}")
                return []
            
            # Convert to list of dictionaries
            ohlc_data = []
            for date, row in hist.tail(5).iterrows():
                ohlc_data.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "open": float(row['Open']) if pd.notna(row['Open']) else None,
                    "high": float(row['High']) if pd.notna(row['High']) else None,
                    "low": float(row['Low']) if pd.notna(row['Low']) else None,
                    "close": float(row['Close']) if pd.notna(row['Close']) else None
                })
            
            return ohlc_data
            
        except Exception as e:
            logger.error(f"Error fetching OHLC data for {symbol}: {e}")
            return []
