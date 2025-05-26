"""
Stock research agent for analyzing and forecasting stock prices.
"""
from typing import Dict, List, Optional

import yfinance as yf
from bs4 import BeautifulSoup
import requests
import pandas as pd

from .base import BaseAgent

class StockResearchAgent(BaseAgent):
    """Agent for analyzing stocks and generating price forecasts."""
    
    def __init__(self):
        """Initialize the stock research agent."""
        super().__init__(
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        
    async def analyze_stock(self, symbol: str) -> Dict:
        """Analyze a stock and generate price forecasts.
        
        Args:
            symbol: The stock symbol (NSE format)
            
        Returns:
            Dictionary containing forecasts and analysis
        """
        # Gather data
        stock_data = self._get_stock_data(f"{symbol}.NS")
        news_data = self._get_news_data(symbol)
        
        # Create analysis prompt
        system_prompt = """You are an expert financial analyst specializing in Indian stocks.
        Analyze the provided stock data and news to generate price forecasts.
        Your analysis should be data-driven and consider both technical and fundamental factors."""
        
        user_message = f"""Analyze {symbol} based on the following data:
        
        Stock Data:
        {stock_data}
        
        Recent News:
        {news_data}
        
        Generate price forecasts for:
        - 1 week
        - 1 month
        - 3 months
        - 6 months
        - 12 months
        
        Also provide:
        - Brief analysis summary
        - Confidence score (0-1)
        
        Format your response as a JSON object."""
        
        # Get completion
        response = await self.get_completion(system_prompt, user_message)
        
        # Parse and return results
        try:
            result = eval(response.choices[0].message.content)
            return result
        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")
    
    def _get_stock_data(self, symbol: str) -> Dict:
        """Get stock data from Yahoo Finance.
        
        Args:
            symbol: The stock symbol with .NS suffix
            
        Returns:
            Dictionary of stock data
        """
        stock = yf.Ticker(symbol)
        
        # Get historical data
        hist = stock.history(period="1y")
        
        # Get info
        info = stock.info
        
        return {
            "current_price": info.get("currentPrice"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "price_history": hist[["Close", "Volume"]].to_dict()
        }
    
    def _get_news_data(self, symbol: str) -> List[Dict]:
        """Get recent news articles about the stock.
        
        Args:
            symbol: The stock symbol
            
        Returns:
            List of news article dictionaries
        """
        # Use a search query to find news
        query = f"{symbol} stock NSE news"
        
        # Get Google News results
        url = f"https://www.google.com/search?q={query}&tbm=nws"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            
            news_items = []
            for g in soup.find_all("div", class_="g"):
                title = g.find("h3", class_="r")
                if title:
                    news_items.append({
                        "title": title.text,
                        "url": g.find("a")["href"]
                    })
            
            return news_items[:5]  # Return top 5 news items
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return [] 