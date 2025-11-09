#!/usr/bin/env python
"""
Main script for analyzing NSE stocks and generating forecasts.
"""

import asyncio
import logging
import argparse
from datetime import datetime, timezone
import requests
from urllib.parse import quote
from typing import List, Dict, Any

from src.config.settings import settings
from src.agents.stock_research import StockResearchAgent
from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Stock
from src.utils.logging import setup_logging

# Configure logging
setup_logging(level=settings.log_level)
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
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch stocks for {index}: {response.status_code}")
            print(f"\nNSE API request failed with status code {response.status_code}.")
            print("This is likely due to IP filtering. Please:")
            print(f"1. Open this URL in your browser: {headers['Referer']}")
            print("2. Complete any CAPTCHA or verification if required")
            print("3. Wait for the page to load successfully")
            print("4. Then run this script again\n")
            return []

        data = response.json()
        stocks = data.get("data", [])
        current_tickers = set()

        # Get all stocks that were previously in this index
        previous_stocks = await async_db[COLLECTIONS["stocks"]].find(
            {"indices": index}
        ).to_list(length=None)

        # Update stocks in database
        for stock_data in stocks:
            meta = stock_data.get("meta", {})
            company_name = meta.get("companyName")
            
            # Skip if company name is missing
            if not company_name:
                logger.warning(f"Skipping stock {meta.get('symbol')} due to missing company name")
                continue

            symbol = meta.get("symbol")
            current_tickers.add(symbol)

            # Get existing stock data if any
            existing_stock = await async_db[COLLECTIONS["stocks"]].find_one(
                {"ticker": symbol}
            )
            
            # Prepare indices list
            indices = [index]
            if existing_stock and "indices" in existing_stock:
                indices = list(set(existing_stock["indices"] + [index]))

            stock = Stock(
                ticker=symbol,
                name=company_name,
                price=float(stock_data["lastPrice"]),
                industry=meta.get("industry", "Unknown"),
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

        return list(current_tickers)

    except Exception as e:
        logger.exception(f"Error fetching stocks for {index}: {e}")
        print(f"\nError fetching stocks from NSE API: {str(e)}")
        print("This might be due to IP filtering. Please:")
        print(f"1. Open this URL in your browser: {headers['Referer']}")
        print("2. Complete any CAPTCHA or verification if required")
        print("3. Wait for the page to load successfully")
        print("4. Then run this script again\n")
        return []


async def analyze_stock(symbol: str, agent: StockResearchAgent, force_llm: bool = False) -> List[Dict[str, Any]]:
    """Analyze a single stock and save results.

    Args:
        symbol: Stock symbol
        agent: Stock research agent instance
        force_llm: If True, force new analysis even if recent forecasts exist

    Returns:
        List of forecasts for the stock, empty list if analysis fails
    """
    start_time = datetime.now(timezone.utc)
    try:
        # Get analysis from agent
        logger.info(f"Starting analysis for {symbol} at {start_time} (force_llm={force_llm})")
        forecasts = await agent.analyze_stock(symbol, force=force_llm)

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Completed analysis for {symbol} in {duration:.2f} seconds")
        return forecasts

    except Exception as e:
        logger.error(f"Failed to analyze {symbol}: {str(e)}")
        return []


async def process_stocks_with_semaphore(stocks: List[str], force_llm: bool, max_workers: int) -> Dict[str, List[Dict[str, Any]]]:
    """Process stocks with a semaphore to limit concurrent tasks.
    
    Args:
        stocks: List of stock symbols to process
        force_llm: If True, force new analysis even if recent forecasts exist
        max_workers: Maximum number of concurrent tasks
        
    Returns:
        Dictionary mapping stock symbols to their forecasts
    """
    # Get API keys to determine distribution
    api_keys = settings.get_google_api_keys() or [settings.google_api_key]
    num_keys = len(api_keys)
    
    if num_keys > 1:
        logger.info(f"Distributing {len(stocks)} stocks across {num_keys} API keys evenly")
    
    semaphore = asyncio.Semaphore(max_workers)
    results = {}
    
    async def process_with_semaphore(symbol: str, stock_index: int) -> None:
        async with semaphore:
            # Assign API key based on stock position for even distribution
            # Stock at index i uses key at index (i % num_keys)
            api_key_index = stock_index % num_keys if num_keys > 1 else None
            agent = StockResearchAgent(api_key_index=api_key_index)
            forecasts = await analyze_stock(symbol, agent, force_llm=force_llm)
            results[symbol] = forecasts
    
    # Create tasks for all stocks with their indices
    tasks = [asyncio.create_task(process_with_semaphore(symbol, idx)) for idx, symbol in enumerate(stocks)]
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    return results


async def main():
    """Main function to analyze all stocks."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze NSE stocks and generate forecasts")
    parser.add_argument(
        "-fl",
        "--force-llm",
        action="store_true",
        help="Force new LLM analysis even if recent forecasts exist"
    )
    parser.add_argument(
        "-fn",
        "--force-nse",
        action="store_true",
        help="Force fetch stock list from NSE API even if stocks exist in DB"
    )
    parser.add_argument(
        "-i",
        "--index",
        default="NIFTY 50",
        help="Index to analyze (default: NIFTY 50)"
    )
    parser.add_argument(
        "-p",
        "--parallel",
        action="store_true",
        help="Process stocks in parallel using TaskGroup (default: False)"
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=10,
        help="Maximum number of concurrent tasks when processing in parallel (default: 10)"
    )
    args = parser.parse_args()

    start_time = datetime.now(timezone.utc)
    logger.info(
        f"Starting stock analysis at {start_time} "
        f"(force_llm={args.force_llm}, force_nse={args.force_nse}, index={args.index}, "
        f"parallel={args.parallel}, workers={args.workers})"
    )
    
    # Fetch stocks for the specified index
    stocks = await fetch_nse_stocks(args.index, force_nse=args.force_nse)
    if not stocks:
        logger.error(f"No stocks found for index {args.index}")
        return

    logger.info(f"Found {len(stocks)} stocks in {args.index}")

    if args.parallel:
        # Process stocks in parallel with worker limit
        logger.info(f"Processing stocks in parallel with {args.workers} workers")
        results = await process_stocks_with_semaphore(stocks, args.force_llm, args.workers)
    else:
        # Process stocks sequentially
        logger.info("Processing stocks sequentially")
        # Get API keys for sequential processing too
        api_keys = settings.get_google_api_keys() or [settings.google_api_key]
        num_keys = len(api_keys)
        results = {}
        for idx, symbol in enumerate(stocks):
            # Assign API key based on stock position for even distribution
            api_key_index = idx % num_keys if num_keys > 1 else None
            agent = StockResearchAgent(api_key_index=api_key_index)
            forecasts = await analyze_stock(symbol, agent, force_llm=args.force_llm)
            results[symbol] = forecasts

    # Log results
    successful = sum(1 for forecasts in results.values() if forecasts)
    failed = sum(1 for forecasts in results.values() if not forecasts)
    
    logger.info(f"Analysis complete. Successful: {successful}, Failed: {failed}")
    
    # Log failed stocks
    if failed > 0:
        failed_stocks = [symbol for symbol, forecasts in results.items() if not forecasts]
        logger.warning(f"Failed stocks: {', '.join(failed_stocks)}")

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Completed all stock analysis in {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
