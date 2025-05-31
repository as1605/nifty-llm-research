"""
Stock research agent for analyzing and forecasting stock prices using Perplexity models.
"""

from datetime import datetime

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Forecast
from src.db.models import Stock

from .base import BaseAgent


class StockResearchAgent(BaseAgent):
    """Agent for analyzing stocks and generating price forecasts using Perplexity models."""

    def __init__(self):
        """Initialize the stock research agent."""
        super().__init__(model="sonar-deep-research", temperature=0.7)

    async def analyze_stock(self, symbol: str) -> dict:
        """Analyze a stock and generate price forecasts.

        Args:
            symbol: The stock symbol (NSE format)

        Returns:
            Dictionary containing forecasts and analysis
        """
        # Get or create prompt config for deep research
        research_config = await self.get_prompt_config(
            name="stock_research",
            system_prompt="""You are an expert financial analyst specializing in Indian stocks.
            Use your deep research capabilities to gather and analyze comprehensive information about the given stock.
            Focus on factual data, market trends, and reliable sources.
            Include specific numbers, dates, and sources in your analysis.
            Ensure all numerical data is accurate and properly sourced.""",
            user_prompt="{query}",
            params=["query"],
        )

        # Create research query
        research_query = f"""Analyze {symbol} stock on NSE. Provide comprehensive information including:
        1. Current stock price and recent price movements
        2. Market capitalization
        3. P/E ratio and other key financial metrics
        4. Recent financial performance and quarterly results
        5. Market position and competitive advantages
        6. Industry trends and challenges
        7. Management quality and strategy
        8. Growth prospects and risks
        9. Technical analysis indicators
        10. Market sentiment and news
        
        Format your response as a JSON object with the following structure:
        {{
            "current_price": float,
            "market_cap": float,
            "pe_ratio": float,
            "volume": float,
            "industry": str,
            "financial_metrics": {{
                "revenue_growth": float,
                "profit_margin": float,
                "debt_to_equity": float
            }},
            "analysis": {{
                "strengths": list[str],
                "weaknesses": list[str],
                "opportunities": list[str],
                "threats": list[str]
            }},
            "sources": list[str]
        }}
        
        Ensure all numerical values are accurate and include sources for your data."""

        # Get deep research completion
        research_response, research_invocation_id = await self.get_completion(
            research_config.system_prompt,
            research_query,
            prompt_config=research_config,
            params={"symbol": symbol}
        )

        # Parse research data
        try:
            stock_data = eval(research_response['choices'][0]['message']['content'])
        except Exception as e:
            raise ValueError(f"Failed to parse research data: {e}")

        # Switch to reasoning model for final analysis
        self.model = "sonar-reasoning-pro"
        analysis_config = await self.get_prompt_config(
            name="stock_analysis",
            system_prompt="""You are an expert financial analyst specializing in Indian stocks.
            Based on the provided research and data, generate precise price forecasts and analysis.
            Your analysis should be data-driven and consider both technical and fundamental factors.
            Provide specific numbers and clear reasoning for your forecasts.
            Ensure your forecasts are realistic and well-justified by the available data.""",
            user_prompt="{query}",
            params=["query"],
        )

        # Create analysis query
        analysis_query = f"""Based on the following research about {symbol}, provide:
        1. Price forecasts for:
           - 1 week
           - 1 month
           - 3 months
           - 6 months
           - 12 months
        2. Confidence score (0-1)
        3. Key factors influencing the forecast
        4. Risk factors to consider

        Research findings:
        {research_response['choices'][0]['message']['content']}

        Format your response as a JSON object with the following structure:
        {{
            "forecast_1w": float,
            "forecast_1m": float,
            "forecast_3m": float,
            "forecast_6m": float,
            "forecast_12m": float,
            "confidence_score": float,
            "key_factors": list[str],
            "risk_factors": list[str],
            "analysis_summary": str,
            "sources": list[str]
        }}"""

        # Get final analysis
        analysis_response, analysis_invocation_id = await self.get_completion(
            analysis_config.system_prompt,
            analysis_query,
            prompt_config=analysis_config,
            params={
                "symbol": symbol,
                "research": research_response['choices'][0]['message']['content']
            }
        )

        # Parse results
        try:
            result = eval(analysis_response['choices'][0]['message']['content'])

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

            # Store forecast
            forecast = Forecast(
                stock_ticker=symbol,
                invocation_id=analysis_invocation_id,
                forecast_date=datetime.utcnow(),
                target_price=result["forecast_1m"],  # Using 1-month forecast as target
                gain=(
                    (result["forecast_1m"] - stock_data["current_price"])
                    / stock_data["current_price"]
                )
                * 100,
                days=30,  # 1 month
                reason_summary=result["analysis_summary"],
                sources=result.get("sources", []),
            )
            await async_db[COLLECTIONS["forecasts"]].insert_one(forecast.dict())

            return result

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")
