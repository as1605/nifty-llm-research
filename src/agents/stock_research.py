"""
Stock research agent for analyzing and forecasting stock prices.
"""

from datetime import datetime

import requests
import yfinance as yf
from bs4 import BeautifulSoup

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Forecast
from src.db.models import Invocation
from src.db.models import PromptConfig
from src.db.models import Stock

from .base import BaseAgent


class StockResearchAgent(BaseAgent):
    """Agent for analyzing stocks and generating price forecasts."""

    def __init__(self):
        """Initialize the stock research agent."""
        super().__init__(model="gpt-4-turbo-preview", temperature=0.7)

    async def analyze_stock(self, symbol: str) -> dict:
        """Analyze a stock and generate price forecasts.

        Args:
            symbol: The stock symbol (NSE format)

        Returns:
            Dictionary containing forecasts and analysis
        """
        # Gather data
        stock_data = self._get_stock_data(f"{symbol}.NS")
        news_data = self._get_news_data(symbol)

        # Get or create prompt config
        prompt_config = await self._get_prompt_config()

        # Create parameter mapping
        params = {
            "STOCK_TICKER": symbol,
            "STOCK_DATA": str(stock_data),
            "NEWS_DATA": str(news_data),
        }

        # Get completion
        response = await self.get_completion(
            prompt_config.system_prompt, prompt_config.user_prompt.format(**params)
        )

        # Parse results
        try:
            result = eval(response.choices[0].message.content)

            # Store stock data
            stock = Stock(
                ticker=symbol,
                price=stock_data["current_price"],
                market_cap=stock_data["market_cap"],
                industry=stock_data.get("industry", "Unknown"),
            )
            await async_db[COLLECTIONS["stocks"]].update_one(
                {"ticker": symbol}, {"$set": stock.dict()}, upsert=True
            )

            # Store invocation
            invocation = Invocation(
                prompt_config_id=prompt_config.id,
                params=params,
                response=response.choices[0].message.content,
                metadata=response.usage.dict() if hasattr(response, "usage") else {},
            )
            invocation_result = await async_db[COLLECTIONS["invocations"]].insert_one(
                invocation.dict()
            )

            # Store forecast
            forecast = Forecast(
                stock_ticker=symbol,
                invocation_id=invocation_result.inserted_id,
                forecast_date=datetime.utcnow(),
                target_price=result["forecast_1m"],  # Using 1-month forecast as target
                gain=(
                    (result["forecast_1m"] - stock_data["current_price"])
                    / stock_data["current_price"]
                )
                * 100,
                days=30,  # 1 month
                reason_summary=result["analysis_summary"],
                sources=[news["url"] for news in news_data],
            )
            await async_db[COLLECTIONS["forecasts"]].insert_one(forecast.dict())

            return result

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")

    async def _get_prompt_config(self) -> PromptConfig:
        """Get or create the stock analysis prompt configuration."""
        # Try to get existing config
        config = await async_db[COLLECTIONS["prompt_configs"]].find_one(
            {"name": "stock_analysis"}
        )

        if config:
            return PromptConfig(**config)

        # Create new config if not exists
        config = PromptConfig(
            name="stock_analysis",
            system_prompt="""You are an expert financial analyst specializing in Indian stocks.
            Analyze the provided stock data and news to generate price forecasts.
            Your analysis should be data-driven and consider both technical and fundamental factors.""",
            user_prompt="""Analyze {STOCK_TICKER} based on the following data:

            Stock Data:
            {STOCK_DATA}

            Recent News:
            {NEWS_DATA}

            Generate price forecasts for:
            - 1 week
            - 1 month
            - 3 months
            - 6 months
            - 12 months

            Also provide:
            - Brief analysis summary
            - Confidence score (0-1)

            Format your response as a JSON object.""",
            params=["STOCK_TICKER", "STOCK_DATA", "NEWS_DATA"],
            model="gpt-4-turbo-preview",
            default=True,
        )

        result = await async_db[COLLECTIONS["prompt_configs"]].insert_one(config.dict())
        config.id = result.inserted_id
        return config

    def _get_stock_data(self, symbol: str) -> dict:
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
            "industry": info.get("industry"),
            "price_history": hist[["Close", "Volume"]].to_dict(),
        }

    def _get_news_data(self, symbol: str) -> list[dict]:
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
                    news_items.append({"title": title.text, "url": g.find("a")["href"]})

            return news_items[:5]  # Return top 5 news items

        except Exception:
            return []
