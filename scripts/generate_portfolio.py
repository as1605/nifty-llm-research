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
from src.utils.email import EmailSender
from src.visualization.plotter import StockPlotter

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def format_timestamp_for_filesystem(dt: datetime) -> str:
    """Format datetime for filesystem compatibility."""
    return dt.strftime("%Y%m%d-%H%M%S")


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
    
    # Base filename
    base_name = f"{index}-{timestamp}-{filter_top_n}-{basket_size_k}"
    
    # Save JSON
    json_path = baskets_dir / f"{base_name}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    
    # Generate and save Markdown table
    md_content = f"""# Portfolio Basket Analysis
Generated on: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
Index: {index}
Analysis Period: {since_time.strftime("%Y-%m-%d %H:%M:%S UTC")}
Top N Stocks Considered: {filter_top_n}
Selected K Stocks: {basket_size_k}

## Selected Stocks and Weights

| Stock | Weight | Expected 1M Gain |
|-------|--------|-----------------|
"""
    
    # Add rows for each stock
    for stock in result["stocks_picked"]:
        weight = result["weights"][stock]
        md_content += f"| {stock} | {weight:.2%} | {result['expected_gain_1m']:.2f}% |\n"
    
    # Add reason summary
    md_content += f"\n## Selection Rationale\n\n{result['reason_summary']}\n"
    
    # Save Markdown
    md_path = baskets_dir / f"{base_name}.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    
    logger.info(f"Saved basket outputs to {json_path} and {md_path}")


def print_basket_summary(result: dict) -> None:
    """Print a well-formatted summary of the basket to console."""
    print("\n=== Portfolio Basket Summary ===")
    print("\nSelected Stocks and Weights:")
    print("-" * 40)
    for stock in result["stocks_picked"]:
        weight = result["weights"][stock]
        print(f"{stock}: {weight:.2%}")
    print("-" * 40)
    print(f"\nExpected 1M Gain: {result['expected_gain_1m']:.2f}%")
    print("\nSelection Rationale:")
    print(result["reason_summary"])
    print("=" * 40)


async def generate_portfolio(
    index: str = "NIFTY 50",
    since_time: Optional[datetime] = None,
    filter_top_n: int = 20,
    basket_size_k: int = 5,
    send_email: bool = False
) -> None:
    """Generate portfolio recommendations.

    Args:
        index: Index to analyze (default: NIFTY 50)
        since_time: Only consider forecasts after this time (default: 24 hours ago)
        filter_top_n: Number of top stocks to consider (default: 20)
        basket_size_k: Number of stocks to select for portfolio (default: 5)
        send_email: Whether to send email notification
    """
    try:
        # Set default since_time if not provided
        if since_time is None:
            since_time = datetime.now(timezone.utc) - timedelta(days=7)

        # Initialize portfolio agent
        portfolio_agent = PortfolioAgent()

        # Generate portfolio recommendations
        result = await portfolio_agent.optimize_portfolio(
            index=index,
            since_time=since_time,
            filter_top_n=filter_top_n,
            basket_size_k=basket_size_k
        )

        # Visualize portfolio performance
        plotter = StockPlotter()
        plotter.plot_portfolio_performance(result)

        # Save outputs
        save_basket_outputs(
            result=result,
            index=index,
            since_time=since_time,
            filter_top_n=filter_top_n,
            basket_size_k=basket_size_k
        )

        # Print summary to console
        print_basket_summary(result)

        # Send email notification if requested
        if send_email:
            email_sender = EmailSender()
            await email_sender.send_portfolio_update(result)

        logger.info("Portfolio generation completed successfully")

    except Exception as e:
        logger.error(f"Error generating portfolio: {e}")
        raise


def main():
    """Main function to parse arguments and generate portfolio."""
    parser = argparse.ArgumentParser(description="Generate portfolio recommendations")
    parser.add_argument(
        "--index",
        type=str,
        default="NIFTY 50",
        help="Index to analyze (default: NIFTY 50)"
    )
    parser.add_argument(
        "--since-time",
        type=str,
        help="Only consider forecasts after this time (ISO format)"
    )
    parser.add_argument(
        "--filter-top-n",
        type=int,
        default=10,
        help="Number of top stocks to consider"
    )
    parser.add_argument(
        "--basket-size-k",
        type=int,
        default=5,
        help="Number of stocks to select for portfolio"
    )
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send email notification"
    )

    args = parser.parse_args()

    # Parse since_time if provided
    since_time = None
    if args.since_time:
        since_time = datetime.fromisoformat(args.since_time)

    # Run portfolio generation
    asyncio.run(
        generate_portfolio(
            index=args.index,
            since_time=since_time,
            filter_top_n=args.filter_top_n,
            basket_size_k=args.basket_size_k,
            send_email=args.send_email
        )
    )


if __name__ == "__main__":
    main()
