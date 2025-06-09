#!/usr/bin/env python
"""
Script to generate portfolio recommendations.
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from config.settings import settings
from src.agents.portfolio import PortfolioAgent
from src.db.database import COLLECTIONS
from src.db.database import async_db

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def format_timestamp_for_filesystem(dt: datetime) -> str:
    """Format datetime for filesystem compatibility.
    
    Example output: 'Jan_15_2024_14_30'
    """
    return dt.strftime("%b_%d_%Y_%H_%M")


def save_basket_outputs(
    result: dict,
    index: str,
    since_time: datetime,
    filter_top_n: int,
    basket_size_k: int
) -> None:
    """Save basket outputs in JSON and Markdown formats.
    
    Args:
        result: Portfolio optimization result
        index: Index name
        since_time: Analysis start time
        filter_top_n: Number of top stocks considered
        basket_size_k: Number of stocks selected
    """
    # Create baskets directory if it doesn't exist
    baskets_dir = Path("docs/baskets")
    baskets_dir.mkdir(parents=True, exist_ok=True)
    
    # Format timestamp for filename
    timestamp = format_timestamp_for_filesystem(since_time)
    
    # Base filename with better separation
    base_name = f"{index}__{timestamp}__N{filter_top_n}_K{basket_size_k}"
    
    # Save JSON
    json_path = baskets_dir / f"{base_name}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    
    # Generate and save Markdown table
    md_content = f"""# Portfolio Basket Analysis
Generated on: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
Index: {index}
Top N Stocks Considered: {filter_top_n}
Selected K Stocks: {basket_size_k}

## Selected Stocks and Weights

| Stock | Weight |
|-------|--------|
"""
    
    # Add rows for each stock using the weights dictionary
    for stock in result["stocks_picked"]:
        weight = result["weights"][stock]
        md_content += f"| {stock} | {weight:.2%} |\n"
    
    # Add overall basket gain
    md_content += f"\n## Overall Basket Gain\n\nExpected 1M Gain: {result['expected_gain_1m']:.2f}%\n"
    
    # Add summary
    md_content += f"\n## Analysis Summary\n\n{result['reason_summary']}\n"
    
    # Save Markdown
    md_path = baskets_dir / f"{base_name}.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    
    logger.info(f"Saved basket outputs to {baskets_dir}")


async def main():
    """Main function to generate portfolio recommendations."""
    parser = argparse.ArgumentParser(description="Generate portfolio recommendations")
    parser.add_argument("--index", default="NIFTY 50", help="Index to analyze")
    parser.add_argument(
        "--filter-top-n",
        type=int,
        default=20,
        help="Number of top stocks to consider"
    )
    parser.add_argument(
        "--basket-size-k",
        type=int,
        default=5,
        help="Number of stocks to select for portfolio"
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=7,
        help="Number of days to look back for forecasts"
    )
    args = parser.parse_args()

    # Calculate since_time
    since_time = datetime.now(timezone.utc) - timedelta(days=args.since_days)

    # Initialize agent
    agent = PortfolioAgent()

    try:
        # Generate portfolio
        result = await agent.optimize_portfolio(
            index=args.index,
            since_time=since_time,
            filter_top_n=args.filter_top_n,
            basket_size_k=args.basket_size_k
        )

        # Save outputs
        save_basket_outputs(
            result=result,
            index=args.index,
            since_time=since_time,
            filter_top_n=args.filter_top_n,
            basket_size_k=args.basket_size_k
        )

        logger.info("Portfolio generation completed successfully")

    except Exception as e:
        logger.error(f"Failed to generate portfolio: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
