"""
Portfolio optimization agent for selecting the best stocks.
"""

from datetime import datetime

import pandas as pd

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Basket
from src.db.models import Invocation
from src.db.models import PromptConfig

from .base import BaseAgent


class PortfolioAgent(BaseAgent):
    """Agent for optimizing stock portfolios."""

    def __init__(self):
        """Initialize the portfolio agent."""
        super().__init__(
            model="gpt-4-turbo-preview",
            temperature=0.5,  # Lower temperature for more consistent recommendations
        )

    async def optimize_portfolio(self, stock_data: list[dict]) -> dict:
        """Generate optimized portfolio recommendations.

        Args:
            stock_data: List of stock forecast dictionaries

        Returns:
            Dictionary containing selected stocks and analysis
        """
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(stock_data)

        # Get or create prompt config
        prompt_config = await self._get_prompt_config()

        # Create parameter mapping
        params = {"STOCK_DATA": df.to_string()}

        # Get completion
        response = await self.get_completion(
            prompt_config.system_prompt, prompt_config.user_prompt.format(**params)
        )

        # Parse results
        try:
            result = eval(response.choices[0].message.content)

            # Store invocation
            invocation = Invocation(
                prompt_config_id=prompt_config.id,
                params=params,
                response=response.choices[0].message.content,
                metadata=response.usage.dict() if hasattr(response, "usage") else {},
            )
            await async_db[COLLECTIONS["invocations"]].insert_one(
                invocation.dict()
            )

            # Calculate equal weights for selected stocks
            weights = {
                stock: 1.0 / len(result["selected_stocks"])
                for stock in result["selected_stocks"]
            }

            # Store basket
            basket = Basket(
                creation_date=datetime.utcnow(),
                stocks_ticker_candidates=[stock["symbol"] for stock in stock_data],
                stocks_picked=result["selected_stocks"],
                weights=weights,
                reason_summary=result["summary"],
                expected_gain_1w=result["expected_return"],
            )
            await async_db[COLLECTIONS["baskets"]].insert_one(basket.dict())

            return result

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")

    async def _get_prompt_config(self) -> PromptConfig:
        """Get or create the portfolio optimization prompt configuration."""
        # Try to get existing config
        config = await async_db[COLLECTIONS["prompt_configs"]].find_one(
            {"name": "portfolio_optimization"}
        )

        if config:
            return PromptConfig(**config)

        # Create new config if not exists
        config = PromptConfig(
            name="portfolio_optimization",
            system_prompt="""You are an expert portfolio manager specializing in Indian stocks.
            Analyze the provided stock forecasts and select the 5 best stocks for a weekly portfolio.
            Consider both potential returns and risk factors in your selection.""",
            user_prompt="""Analyze the following stock forecasts and select the best 5 stocks:

            Stock Data:
            {STOCK_DATA}

            Provide:
            - List of 5 selected stocks (symbols only)
            - Expected 1-month portfolio return
            - Brief explanation of selection rationale

            Format your response as a JSON object with keys:
            - selected_stocks (list)
            - expected_return (float)
            - summary (string)""",
            params=["STOCK_DATA"],
            model="gpt-4-turbo-preview",
            default=True,
        )

        result = await async_db[COLLECTIONS["prompt_configs"]].insert_one(config.dict())
        config.id = result.inserted_id
        return config

    def _calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional metrics for portfolio selection.

        Args:
            df: DataFrame of stock forecasts

        Returns:
            DataFrame with additional metrics
        """
        # Calculate potential returns
        df["1m_return"] = (df["forecast_1m"] - df["current_price"]) / df[
            "current_price"
        ]
        df["3m_return"] = (df["forecast_3m"] - df["current_price"]) / df[
            "current_price"
        ]
        df["6m_return"] = (df["forecast_6m"] - df["current_price"]) / df[
            "current_price"
        ]

        # Calculate volatility score (difference between highest and lowest forecasts)
        df["volatility"] = df[
            ["forecast_1w", "forecast_1m", "forecast_3m", "forecast_6m", "forecast_12m"]
        ].apply(lambda x: (max(x) - min(x)) / x.mean(), axis=1)

        return df
