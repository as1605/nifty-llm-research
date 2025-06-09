#!/usr/bin/env python
"""
Main script for analyzing NSE stocks and generating forecasts.
"""

import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
import aiohttp
from urllib.parse import quote

from config.settings import settings
from src.agents.stock_research import StockResearchAgent
from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Stock
from src.visualization.plotter import StockPlotter

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def fetch_nse_stocks(index: str = "NIFTY 50", force_nse: bool = False) -> list[str]:
    """Fetch stocks from NSE API for a given index.

    Args:
        index: The index to fetch stocks for (default: NIFTY 50)
        force_nse: If True, force fetch from NSE API even if stocks exist in DB

    Returns:
        List of stock tickers
    """
    # First check if we have stocks for this index in DB
    if not force_nse:
        stocks_in_db = await async_db[COLLECTIONS["stocks"]].find(
            {"indices": index}
        ).to_list(length=None)
        
        if stocks_in_db:
            logger.info(f"Found {len(stocks_in_db)} stocks for {index} in database")
            return [stock["ticker"] for stock in stocks_in_db]

    # If no stocks in DB or force_nse is True, fetch from NSE
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={quote(index)}"
    headers = {
        "Referer": f"https://www.nseindia.com/market-data/live-equity-market?symbol={quote(index)}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch stocks for {index}: {response.status}")
                    return []

                data = await response.json()
                stocks = data.get("data", [])
                current_tickers = {stock["symbol"] for stock in stocks}

                # Get all stocks that were previously in this index
                previous_stocks = await async_db[COLLECTIONS["stocks"]].find(
                    {"indices": index}
                ).to_list(length=None)

                # Update stocks in database
                for stock_data in stocks:
                    # Get existing stock data if any
                    existing_stock = await async_db[COLLECTIONS["stocks"]].find_one(
                        {"ticker": stock_data["symbol"]}
                    )
                    
                    # Prepare indices list
                    indices = [index]
                    if existing_stock and "indices" in existing_stock:
                        indices = list(set(existing_stock["indices"] + [index]))

                    stock = Stock(
                        ticker=stock_data["symbol"],
                        name=stock_data["companyName"],
                        price=float(stock_data["lastPrice"]),
                        market_cap=float(stock_data.get("marketCap", 0)),
                        industry=stock_data.get("industry", "Unknown"),
                        indices=indices,
                        modified_time=datetime.now(timezone.utc)
                    )
                    
                    # Upsert the stock data
                    await async_db[COLLECTIONS["stocks"]].update_one(
                        {"ticker": stock.ticker},
                        {"$set": stock.model_dump()},
                        upsert=True
                    )

                # Remove index from stocks that are no longer in the index
                for prev_stock in previous_stocks:
                    if prev_stock["ticker"] not in current_tickers:
                        # Remove this index from the stock's indices list
                        indices = [idx for idx in prev_stock.get("indices", []) if idx != index]
                        await async_db[COLLECTIONS["stocks"]].update_one(
                            {"ticker": prev_stock["ticker"]},
                            {"$set": {"indices": indices}}
                        )
                        logger.info(f"Removed {index} from {prev_stock['ticker']} as it's no longer in the index")

                return [stock["symbol"] for stock in stocks]

    except Exception as e:
        logger.exception(f"Error fetching stocks for {index}: {e}")
        return []


async def analyze_stock(symbol: str, agent: StockResearchAgent, force_llm: bool = False) -> None:
    """Analyze a single stock and save results.

    Args:
        symbol: Stock symbol
        agent: Stock research agent instance
        force_llm: If True, force new analysis even if recent forecasts exist
    """
    start_time = datetime.now(timezone.utc)
    try:
        # Get analysis from agent
        logger.info(f"Starting analysis for {symbol} at {start_time} (force_llm={force_llm})")
        result = await agent.analyze_stock(symbol, force=force_llm)

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

        end_time = datetime.now(timezone.utc)
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
        "--force-llm",
        action="store_true",
        help="Force new LLM analysis even if recent forecasts exist"
    )
    parser.add_argument(
        "--force-nse",
        action="store_true",
        help="Force fetch stock list from NSE API even if stocks exist in DB"
    )
    parser.add_argument(
        "--index",
        default="NIFTY 50",
        help="Index to analyze (default: NIFTY 50)"
    )
    args = parser.parse_args()

    start_time = datetime.now(timezone.utc)
    logger.info(
        f"Starting stock analysis at {start_time} "
        f"(force_llm={args.force_llm}, force_nse={args.force_nse}, index={args.index})"
    )
    
    # Fetch stocks for the specified index
    stocks = await fetch_nse_stocks(args.index, force_nse=args.force_nse)
    if not stocks:
        logger.error(f"No stocks found for index {args.index}")
        return

    logger.info(f"Found {len(stocks)} stocks in {args.index}")
    
    agent = StockResearchAgent()
    logger.info("Initialized StockResearchAgent")

    async with asyncio.TaskGroup() as tg:
        for symbol in stocks:
            tg.create_task(analyze_stock(symbol, agent, force_llm=args.force_llm))

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Completed all stock analysis in {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
