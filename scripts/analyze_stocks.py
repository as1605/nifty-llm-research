#!/usr/bin/env python
"""
Main script for analyzing NSE stocks and generating forecasts.
"""

import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime

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


async def analyze_stock(symbol: str, agent: StockResearchAgent, force: bool = False) -> None:
    """Analyze a single stock and save results.

    Args:
        symbol: Stock symbol
        agent: Stock research agent instance
        force: If True, force new analysis even if recent forecasts exist
    """
    start_time = datetime.utcnow()
    try:
        # Get analysis from agent
        logger.info(f"Starting analysis for {symbol} at {start_time} (force={force})")
        result = await agent.analyze_stock(symbol, force=force)

        # Generate visualization
        logger.info(f"Generating visualization for {symbol}")
        plotter = StockPlotter()

        # Get historical forecasts
        logger.info(f"Fetching historical forecasts for {symbol}")
        historical_forecasts = (
            await async_db[COLLECTIONS["forecasts"]]
            .find({"stock_ticker": symbol})
            .sort("created_time", 1)
            .to_list(length=None)
        )
        logger.info(f"Found {len(historical_forecasts)} historical forecasts for {symbol}")

        # Create visualization
        save_path = (
            Path(settings.data_dir) / "visualizations" / f"{symbol}_forecast.png"
        )
        save_path.parent.mkdir(parents=True, exist_ok=True)

        plotter.plot_predictions(symbol, historical_forecasts, str(save_path))
        logger.info(f"Saved visualization to {save_path}")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Completed analysis for {symbol} in {duration:.2f} seconds")

    except Exception as e:
        logger.exception(f"Error analyzing {symbol}: {e}")
        raise


async def main():
    """Main function to analyze all stocks."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze NSE stocks and generate forecasts")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force new analysis even if recent forecasts exist"
    )
    args = parser.parse_args()

    start_time = datetime.utcnow()
    logger.info(f"Starting stock analysis at {start_time} (force={args.force})")
    
    agent = StockResearchAgent()
    logger.info("Initialized StockResearchAgent")

    async with asyncio.TaskGroup() as tg:
        for symbol in NSE_TOP_100:
            tg.create_task(analyze_stock(symbol, agent, force=args.force))

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Completed all stock analysis in {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
