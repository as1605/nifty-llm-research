"""
YFinance service for fetching stock data and market information.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
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
        """Get comprehensive stock information for research purposes.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'RELIANCE.NS', 'OLECTRA')
            
        Returns:
            Dictionary containing comprehensive stock information
        """
        try:
            # Normalize symbol to ensure .NS suffix
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"Fetching stock info for {symbol} (normalized to {normalized_symbol})")
            
            ticker = yf.Ticker(normalized_symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get historical data for technical analysis
            hist = ticker.history(period='30d')
            
            # Get financial statements
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow
            
            # Get corporate events
            calendar = ticker.calendar
            dividends = ticker.dividends
            splits = ticker.splits
            
            # Get shareholder information
            major_holders = ticker.major_holders
            institutional_holders = ticker.institutional_holders
            
            # Compile comprehensive data
            stock_data = {
                # Basic company info
                "company_name": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "website": info.get("website"),
                "country": info.get("country"),
                
                # Market data
                "current_price": info.get("currentPrice"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap"),
                "beta": info.get("beta"),
                
                # Technical indicators
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "fifty_day_average": info.get("fiftyDayAverage"),
                "two_hundred_day_average": info.get("twoHundredDayAverage"),
                
                # Valuation metrics
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "peg_ratio": info.get("pegRatio"),
                
                # Financial ratios
                "debt_to_equity": info.get("debtToEquity"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                "operating_margins": info.get("operatingMargins"),
                "profit_margins": info.get("profitMargins"),
                
                # Growth metrics
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                
                # Historical price data
                "historical_data": {
                    "period": "30d",
                    "days_available": len(hist) if not hist.empty else 0,
                    "latest_close": float(hist['Close'].iloc[-1]) if not hist.empty else None,
                    "thirty_day_high": float(hist['High'].max()) if not hist.empty else None,
                    "thirty_day_low": float(hist['Low'].min()) if not hist.empty else None,
                    "thirty_day_change_pct": float(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100)) if len(hist) > 1 else None,
                    "average_volume": float(hist['Volume'].mean()) if not hist.empty else None,
                    "volume_trend": "increasing" if not hist.empty and len(hist) > 5 and hist['Volume'].iloc[-1] > hist['Volume'].iloc[-5:].mean() else "decreasing" if not hist.empty and len(hist) > 5 else "stable"
                },
                
                # Financial statements
                "financials": {
                    "quarters_available": len(financials.columns) if not financials.empty else 0,
                    "latest_quarter": str(financials.columns[0].date()) if not financials.empty else None,
                    "total_revenue": float(financials.loc['Total Revenue'].iloc[0]) if not financials.empty and 'Total Revenue' in financials.index else None,
                    "net_income": float(financials.loc['Net Income'].iloc[0]) if not financials.empty and 'Net Income' in financials.index else None,
                    "ebitda": float(financials.loc['EBITDA'].iloc[0]) if not financials.empty and 'EBITDA' in financials.index else None,
                    "operating_income": float(financials.loc['Operating Income'].iloc[0]) if not financials.empty and 'Operating Income' in financials.index else None
                },
                
                # Balance sheet
                "balance_sheet": {
                    "quarters_available": len(balance_sheet.columns) if not balance_sheet.empty else 0,
                    "total_assets": float(balance_sheet.loc['Total Assets'].iloc[0]) if not balance_sheet.empty and 'Total Assets' in balance_sheet.index else None,
                    "total_debt": float(balance_sheet.loc['Total Debt'].iloc[0]) if not balance_sheet.empty and 'Total Debt' in balance_sheet.index else None,
                    "common_stock_equity": float(balance_sheet.loc['Common Stock Equity'].iloc[0]) if not balance_sheet.empty and 'Common Stock Equity' in balance_sheet.index else None,
                    "working_capital": float(balance_sheet.loc['Working Capital'].iloc[0]) if not balance_sheet.empty and 'Working Capital' in balance_sheet.index else None
                },
                
                # Cash flow
                "cash_flow": {
                    "quarters_available": len(cash_flow.columns) if not cash_flow.empty else 0,
                    "free_cash_flow": float(cash_flow.loc['Free Cash Flow'].iloc[0]) if not cash_flow.empty and 'Free Cash Flow' in cash_flow.index else None,
                    "operating_cash_flow": float(cash_flow.loc['Operating Cash Flow'].iloc[0]) if not cash_flow.empty and 'Operating Cash Flow' in cash_flow.index else None,
                    "capital_expenditure": float(cash_flow.loc['Capital Expenditure'].iloc[0]) if not cash_flow.empty and 'Capital Expenditure' in cash_flow.index else None
                },
                
                # Corporate events
                "corporate_events": {
                    "ex_dividend_date": calendar.get("Ex-Dividend Date") if calendar else None,
                    "earnings_dates": calendar.get("Earnings Date") if calendar else None,
                    "earnings_estimate_high": calendar.get("Earnings High") if calendar else None,
                    "earnings_estimate_low": calendar.get("Earnings Low") if calendar else None,
                    "earnings_estimate_average": calendar.get("Earnings Average") if calendar else None,
                    "revenue_estimate_high": calendar.get("Revenue High") if calendar else None,
                    "revenue_estimate_low": calendar.get("Revenue Low") if calendar else None,
                    "revenue_estimate_average": calendar.get("Revenue Average") if calendar else None
                },
                
                # Dividends and splits
                "dividends": {
                    "total_dividends": len(dividends) if not dividends.empty else 0,
                    "latest_dividend": float(dividends.iloc[-1]) if not dividends.empty else None,
                    "latest_dividend_date": str(dividends.index[-1].date()) if not dividends.empty else None
                },
                
                "splits": {
                    "total_splits": len(splits) if not splits.empty else 0,
                    "latest_split": float(splits.iloc[-1]) if not splits.empty else None,
                    "latest_split_date": str(splits.index[-1].date()) if not splits.empty else None
                },
                
                # Shareholder information
                "shareholders": {
                    "insiders_percent_held": float(major_holders.loc['insidersPercentHeld'].iloc[0] * 100) if not major_holders.empty and 'insidersPercentHeld' in major_holders.index else None,
                    "institutions_percent_held": float(major_holders.loc['institutionsPercentHeld'].iloc[0] * 100) if not major_holders.empty and 'institutionsPercentHeld' in major_holders.index else None,
                    "institutions_count": int(major_holders.loc['institutionsCount'].iloc[0]) if not major_holders.empty and 'institutionsCount' in major_holders.index else None
                },
                
                # Data quality indicators
                "data_quality": {
                    "has_real_time_data": info.get("currentPrice") is not None,
                    "has_financials": not financials.empty,
                    "has_balance_sheet": not balance_sheet.empty,
                    "has_cash_flow": not cash_flow.empty,
                    "has_corporate_events": calendar is not None and len(calendar) > 0,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info(f"Successfully fetched comprehensive data for {normalized_symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "last_updated": datetime.now(timezone.utc).isoformat()
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
    
    def get_stock_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical price data for technical analysis.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'RELIANCE.NS', 'OLECTRA')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            # Normalize symbol to ensure .NS suffix
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"Fetching historical data for {symbol} (normalized to {normalized_symbol})")
            
            ticker = yf.Ticker(normalized_symbol)
            hist = ticker.history(period=period)
            
            if not hist.empty:
                logger.info(f"Successfully fetched {period} historical data for {normalized_symbol}: {len(hist)} data points")
                return hist
            else:
                logger.warning(f"No historical data available for {normalized_symbol} for period {period}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators from historical data.
        
        Args:
            hist_data: Historical OHLCV data
            
        Returns:
            Dictionary with calculated technical indicators
        """
        try:
            if hist_data.empty or len(hist_data) < 20:
                return {"error": "Insufficient data for technical analysis"}
            
            # Calculate moving averages
            sma_10 = hist_data['Close'].rolling(window=10).mean().iloc[-1]
            sma_20 = hist_data['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = hist_data['Close'].rolling(window=50).mean().iloc[-1]
            
            # Calculate RSI (14-period)
            delta = hist_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Calculate MACD
            ema_12 = hist_data['Close'].ewm(span=12).mean()
            ema_26 = hist_data['Close'].ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            macd_histogram = macd_line - signal_line
            
            # Calculate Bollinger Bands
            bb_20 = hist_data['Close'].rolling(window=20).mean()
            bb_std = hist_data['Close'].rolling(window=20).std()
            bb_upper = bb_20 + (bb_std * 2)
            bb_lower = bb_20 - (bb_std * 2)
            
            # Calculate ATR (Average True Range)
            high_low = hist_data['High'] - hist_data['Low']
            high_close = abs(hist_data['High'] - hist_data['Close'].shift())
            low_close = abs(hist_data['Low'] - hist_data['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
            
            # Volume analysis
            avg_volume = hist_data['Volume'].mean()
            current_volume = hist_data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Price momentum
            current_price = hist_data['Close'].iloc[-1]
            price_20d_ago = hist_data['Close'].iloc[-20] if len(hist_data) >= 20 else hist_data['Close'].iloc[0]
            momentum_20d = ((current_price - price_20d_ago) / price_20d_ago * 100) if price_20d_ago > 0 else 0
            
            # Helper function to safely convert to float
            def safe_float(value):
                if pd.isna(value) or value is None:
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            technical_data = {
                "moving_averages": {
                    "sma_10": safe_float(sma_10),
                    "sma_20": safe_float(sma_20),
                    "sma_50": safe_float(sma_50),
                    "price_vs_sma_20": "above" if current_price > sma_20 else "below",
                    "price_vs_sma_50": "above" if current_price > sma_50 else "below"
                },
                "momentum": {
                    "rsi_14": safe_float(rsi),
                    "rsi_status": "overbought" if safe_float(rsi) and safe_float(rsi) > 70 else "oversold" if safe_float(rsi) and safe_float(rsi) < 30 else "neutral",
                    "macd_line": safe_float(macd_line.iloc[-1]),
                    "macd_signal": safe_float(signal_line.iloc[-1]),
                    "macd_histogram": safe_float(macd_histogram.iloc[-1]),
                    "macd_signal": "bullish" if safe_float(macd_line.iloc[-1]) and safe_float(signal_line.iloc[-1]) and safe_float(macd_line.iloc[-1]) > safe_float(signal_line.iloc[-1]) else "bearish"
                },
                "volatility": {
                    "bollinger_upper": safe_float(bb_upper.iloc[-1]),
                    "bollinger_middle": safe_float(bb_20.iloc[-1]),
                    "bollinger_lower": safe_float(bb_lower.iloc[-1]),
                    "bollinger_position": "upper" if safe_float(bb_upper.iloc[-1]) and current_price > safe_float(bb_upper.iloc[-1]) else "lower" if safe_float(bb_lower.iloc[-1]) and current_price < safe_float(bb_lower.iloc[-1]) else "middle",
                    "atr_14": safe_float(atr),
                    "atr_percentage": safe_float((atr / current_price) * 100) if safe_float(atr) and current_price > 0 else None
                },
                "volume": {
                    "current_volume": int(current_volume) if not pd.isna(current_volume) else None,
                    "average_volume": int(avg_volume) if not pd.isna(avg_volume) else None,
                    "volume_ratio": safe_float(volume_ratio),
                    "volume_status": "high" if safe_float(volume_ratio) and safe_float(volume_ratio) > 1.5 else "low" if safe_float(volume_ratio) and safe_float(volume_ratio) < 0.5 else "normal"
                },
                "momentum": {
                    "momentum_20d": safe_float(momentum_20d),
                    "momentum_status": "positive" if safe_float(momentum_20d) and safe_float(momentum_20d) > 0 else "negative"
                },
                "support_resistance": {
                    "recent_high": safe_float(hist_data['High'].tail(20).max()),
                    "recent_low": safe_float(hist_data['Low'].tail(20).min()),
                    "current_price": safe_float(current_price)
                }
            }
            
            logger.info(f"Successfully calculated technical indicators")
            return technical_data
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {"error": f"Failed to calculate technical indicators: {str(e)}"}
    
    def get_stock_summary(self, symbol: str) -> Dict[str, Any]:
        """Get a concise summary of stock data for quick analysis.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'RELIANCE.NS', 'OLECTRA')
            
        Returns:
            Dictionary with key stock metrics
        """
        try:
            # Normalize symbol to ensure .NS suffix
            normalized_symbol = self._normalize_symbol(symbol)
            logger.info(f"Generating summary for {symbol} (normalized to {normalized_symbol})")
            
            # Get basic info
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info
            
            # Get recent price data
            hist = ticker.history(period='5d')
            
            summary = {
                "symbol": symbol,
                "company_name": info.get("longName"),
                "current_price": info.get("currentPrice"),
                "day_change": {
                    "high": info.get("dayHigh"),
                    "low": info.get("dayLow"),
                    "volume": info.get("volume")
                },
                "market_metrics": {
                    "market_cap": info.get("marketCap"),
                    "beta": info.get("beta"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "price_to_book": info.get("priceToBook")
                },
                "technical_position": {
                    "price_vs_50ma": "above" if info.get("currentPrice", 0) > info.get("fiftyDayAverage", 0) else "below",
                    "price_vs_200ma": "above" if info.get("currentPrice", 0) > info.get("twoHundredDayAverage", 0) else "below",
                    "fifty_two_week_range": f"{info.get('fiftyTwoWeekLow', 'N/A')} - {info.get('fiftyTwoWeekHigh', 'N/A')}"
                },
                "recent_performance": {
                    "five_day_change": float(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100)) if len(hist) > 1 else None,
                    "volume_trend": "increasing" if len(hist) > 1 and hist['Volume'].iloc[-1] > hist['Volume'].iloc[-2] else "decreasing"
                },
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Successfully generated summary for {normalized_symbol}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
