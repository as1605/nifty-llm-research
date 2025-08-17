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
from urllib.parse import urlparse, quote

from src.config.settings import settings
from src.db.models import Basket
from src.agents.portfolio import PortfolioAgent
from src.utils.logging import setup_logging

# Configure logging
setup_logging(level=settings.log_level)
logger = logging.getLogger(__name__)

# Define IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def format_timestamp_for_filesystem(dt: datetime) -> str:
    """Format datetime for filesystem compatibility.
    
    Example output: 'Jan_15_2024_14_30'
    """
    # Convert to IST if not already
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ist_dt = dt.astimezone(IST)
    return ist_dt.strftime("%b_%d_%Y_%H_%M")


def human_date_ist(dt: datetime) -> str:
    """Return human-readable date like '3 Aug 2025' in IST."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ist_dt = dt.astimezone(IST)
    # Day without leading zero + abbreviated month + year
    day = ist_dt.strftime("%d").lstrip("0")
    month = ist_dt.strftime("%b")
    year = ist_dt.strftime("%Y")
    return f"{day} {month} {year}"


def update_index_md(index: str, current_time: datetime, base_name: str) -> None:
    """Update docs/index.md to reflect latest basket link for the given index.
    - Replaces existing bullet for the index if present
    - Otherwise inserts a new bullet under 'Latest Research Outputs'
    - Preserves any trailing 'Invest with ...' part if it existed
    """
    index_md_path = Path("docs/index.md")
    if not index_md_path.exists():
        logger.warning("docs/index.md not found; skipping index update")
        return
    try:
        content = index_md_path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        logger.error(f"Failed to read docs/index.md: {e}")
        return

    bullet_prefix = f"- **{index}**"
    new_date = human_date_ist(current_time)
    link_target = f"baskets/{quote(base_name)}"
    # Construct new bullet; preserve 'Invest with ...' tail if we can find it on existing line
    new_bullet = None

    # Try to find existing bullet for index
    idx_line = -1
    existing_tail = ""
    for i, line in enumerate(content):
        if line.strip().startswith(bullet_prefix):
            idx_line = i
            # If existing tail contains 'Invest with', preserve it
            if 'Invest with' in line:
                tail_pos = line.find('Invest with')
                existing_tail = ' ' + line[tail_pos:].rstrip()
            break

    new_bullet = f"{bullet_prefix} ({new_date}): [Analysis]({link_target}).{existing_tail}"

    if idx_line >= 0:
        # Replace existing line
        content[idx_line] = new_bullet
    else:
        # Insert after '## Latest Research Outputs' header (first bullet position), or append
        insert_pos = None
        for i, line in enumerate(content):
            if line.strip() == "## Latest Research Outputs":
                insert_pos = i + 1
                # Skip any blank lines immediately following header
                while insert_pos < len(content) and content[insert_pos].strip() == "":
                    insert_pos += 1
                break
        if insert_pos is None:
            # Append at end if header not found
            content.append("")
            content.append(new_bullet)
        else:
            content.insert(insert_pos, new_bullet)

    try:
        index_md_path.write_text("\n".join(content) + "\n", encoding="utf-8")
        logger.info("Updated docs/index.md with latest basket link")
    except Exception as e:
        logger.error(f"Failed to write docs/index.md: {e}")


def save_basket_outputs(
    result: Basket,
    index: str,
    filter_top_n: int,
    basket_size_k: int
) -> None:
    """Save basket outputs in JSON and Markdown formats.
    
    Args:
        result: Portfolio optimization result (Basket model)
        index: Index name
        filter_top_n: Number of top stocks considered
        basket_size_k: Number of stocks selected
    """
    # Create baskets directory if it doesn't exist
    baskets_dir = Path("docs/baskets")
    baskets_dir.mkdir(parents=True, exist_ok=True)
    
    # Get current time in IST once
    current_time = datetime.now(IST)
    
    # Format timestamp for filename
    timestamp = format_timestamp_for_filesystem(current_time)
    
    # Base filename with better separation
    base_name = f"{index}__{timestamp}__N{filter_top_n}_K{basket_size_k}"
    
    # Convert model to dict and handle datetime serialization
    basket_dict = result.model_dump()
    
    # Remove MongoDB _id field
    basket_dict.pop('_id', None)
    
    # Convert invocation_id to string if it exists
    if basket_dict.get('invocation_id'):
        basket_dict['invocation_id'] = str(basket_dict['invocation_id'])
    
    # Handle datetime serialization
    if isinstance(basket_dict.get('creation_date'), datetime):
        basket_dict['creation_date'] = basket_dict['creation_date'].isoformat()
    
    # Save JSON
    json_path = baskets_dir / f"{base_name}.json"
    with open(json_path, "w") as f:
        json.dump(basket_dict, f, indent=2)
    
    # Generate and save Markdown table
    md_content = f"""# Portfolio Basket Analysis
Generated on: {current_time.strftime("%Y-%m-%d %H:%M:%S IST")}
Index: {index}
Top N Stocks Considered: {filter_top_n}
Selected K Stocks: {basket_size_k}

## Selected Stocks and Weights

| Stock | Weight | Sources |
|-------|--------|---------|
"""
    
    # Add rows for each stock
    for stock in result.stocks:
        # Format sources with domain names
        if stock.sources:
            sources_str = "<br>".join([
                f"[{urlparse(src).netloc}]({src})"
                for src in stock.sources
            ])
        else:
            sources_str = "No sources available"
            
        md_content += f"| {stock.stock_ticker} | {stock.weight:.2%} | {sources_str} |\n"
    
    # Add overall gain
    md_content += f"\n## Overall Basket Gain\n\nExpected 1W Gain: {result.expected_gain_1w:.2f}%\n"
    
    # Add analysis summary
    md_content += f"\n## Analysis Summary\n\n{result.reason_summary}\n"
    
    # Save Markdown
    md_path = baskets_dir / f"{base_name}.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    
    logger.info(f"Saved basket outputs to {baskets_dir}")

    # Update docs index with the new link
    try:
        update_index_md(index=index, current_time=current_time, base_name=base_name)
    except Exception as e:
        logger.error(f"Failed to update docs/index.md: {e}")


async def main():
    """Main function to generate portfolio recommendations."""
    parser = argparse.ArgumentParser(description="Generate portfolio recommendations")
    parser.add_argument("-i", "--index", default="NIFTY 50", help="Index to analyze")
    parser.add_argument(
        "-n",
        "--filter-top-n",
        type=int,
        default=20,
        help="Number of top stocks to consider"
    )
    parser.add_argument(
        "-k",
        "--basket-size-k",
        type=int,
        default=5,
        help="Number of stocks to select for portfolio"
    )
    parser.add_argument(
        "-d",
        "--since-days",
        type=int,
        default=7,
        help="Number of days to look back for forecasts"
    )
    args = parser.parse_args()

    # Calculate since_time in IST
    since_time = datetime.now(IST) - timedelta(days=args.since_days)

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
            filter_top_n=args.filter_top_n,
            basket_size_k=args.basket_size_k
        )

        logger.info("Portfolio generation completed successfully")

    except Exception as e:
        logger.error(f"Failed to generate portfolio: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
