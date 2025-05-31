#!/usr/bin/env python
"""
Main script for analyzing NSE stocks and generating forecasts.
"""

import asyncio
import logging
from pathlib import Path

from config.settings import settings
from src.agents.stock_research import StockResearchAgent
from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.visualization.plotter import StockPlotter

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# NSE Top 100 stocks (you should maintain this list or fetch it dynamically)
NSE_TOP_100 = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    # Add more symbols...
]


async def analyze_stock(symbol: str, agent: StockResearchAgent) -> None:
    """Analyze a single stock and save results.

    Args:
        symbol: Stock symbol
        agent: Stock research agent instance
    """
    try:
        # Get analysis from agent
        logger.info(f"Analyzing {symbol}...")
        await agent.analyze_stock(symbol)

        # Generate visualization
        plotter = StockPlotter()

        # Get historical forecasts
        historical_forecasts = (
            await async_db[COLLECTIONS["forecasts"]]
            .find({"stock_ticker": symbol})
            .sort("created_time", 1)
            .to_list(length=None)
        )

        # Create visualization
        save_path = (
            Path(settings.data_dir) / "visualizations" / f"{symbol}_forecast.png"
        )
        save_path.parent.mkdir(parents=True, exist_ok=True)

        plotter.plot_predictions(symbol, historical_forecasts, str(save_path))

        logger.info(f"Completed analysis for {symbol}")

    except Exception as e:
        logger.exception(f"Error analyzing {symbol}: {e}")
        raise


async def main():
    """Main function to analyze all stocks."""
    agent = StockResearchAgent()

    async with asyncio.TaskGroup() as tg:
        for symbol in NSE_TOP_100:
            tg.create_task(analyze_stock(symbol, agent))


if __name__ == "__main__":
    asyncio.run(main())
