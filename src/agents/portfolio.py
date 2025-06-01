"""
Portfolio optimization agent for selecting the best stocks.
"""

from datetime import datetime

import pandas as pd

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Basket

from .base import BaseAgent


class PortfolioAgent(BaseAgent):
    """Agent for optimizing stock portfolios."""

    def __init__(self):
        """Initialize the portfolio agent."""
        super().__init__()

    async def optimize_portfolio(self, stock_data: list[dict]) -> dict:
        """Generate optimized portfolio recommendations.

        Args:
            stock_data: List of stock forecast dictionaries

        Returns:
            Dictionary containing selected stocks and analysis
        """
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(stock_data)

        # Get prompt config
        prompt_config = await self.get_prompt_config("portfolio_optimization")

        # Get completion
        response, invocation_id = await self.get_completion(
            prompt_config=prompt_config,
            params={"STOCK_DATA": df.to_string()}
        )

        # Parse results
        try:
            result = self._parse_json_response(response['choices'][0]['message']['content'])

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
            await async_db[COLLECTIONS["baskets"]].insert_one(basket.model_dump())

            return result

        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}")

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
