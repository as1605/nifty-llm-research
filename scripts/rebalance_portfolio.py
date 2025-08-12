#!/usr/bin/env python3
"""
Portfolio Rebalancing Script for Zerodha Kite API

This script rebalances a stock portfolio based on a target allocation specified in a JSON file.
It connects to the Zerodha Kite API to fetch current holdings and place orders.

Usage:
    python scripts/rebalance_portfolio.py <basket_json_file> [--user-id USER_ID] [--dry-run] [--min-order-value MIN_VALUE]

Example:
    python scripts/rebalance_portfolio.py docs/baskets/NIFTY_50__Jul_27_2025_22_04__N20_K5.json --dry-run
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings
from src.services.zerodha_service import ZerodhaService, authenticate_user
from src.utils.logging import get_logger

logger = get_logger(__name__)


IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = dt_time(hour=9, minute=15)
MARKET_PREOPEN_TARGET = dt_time(hour=9, minute=14)
MARKET_CLOSE = dt_time(hour=15, minute=30)


def now_ist() -> datetime:
    return datetime.now(IST)


def is_weekday(d: datetime) -> bool:
    # Monday=0, Sunday=6
    return d.weekday() < 5


def is_market_open_ist(current: Optional[datetime] = None) -> bool:
    """Return True if current IST time is during market hours (9:15-15:30) on a weekday."""
    current = current or now_ist()
    if not is_weekday(current):
        return False
    t = current.time()
    return (t >= MARKET_OPEN) and (t < MARKET_CLOSE)


def is_before_market_open_ist(current: Optional[datetime] = None) -> bool:
    current = current or now_ist()
    if not is_weekday(current):
        return True
    return current.time() < MARKET_OPEN


def next_9_14_ist(after: Optional[datetime] = None) -> datetime:
    """Compute the next 9:14 AM IST on a weekday starting from 'after'.
    Special case: if time is between 9:14 and 9:15 on a weekday, return 'after' (immediate, no wait).
    """
    after = after or now_ist()

    # If weekday and between 09:14 and 09:15, start immediately (no wait)
    if is_weekday(after):
        t = after.time()
        if MARKET_PREOPEN_TARGET <= t < MARKET_OPEN:
            return after
        if t < MARKET_PREOPEN_TARGET:
            return datetime.combine(after.date(), MARKET_PREOPEN_TARGET, tzinfo=IST)

    # Otherwise, schedule for next weekday at 09:14
    date = after.date()
    if is_weekday(after):
        # If it's a weekday but already past market open, move to next day
        date = date + timedelta(days=1)
    # For weekends, the while loop below will advance to next weekday
    target_dt = datetime.combine(date, MARKET_PREOPEN_TARGET, tzinfo=IST)
    while target_dt.weekday() >= 5:  # 5=Sat, 6=Sun
        date = date + timedelta(days=1)
        target_dt = datetime.combine(date, MARKET_PREOPEN_TARGET, tzinfo=IST)
    return target_dt


async def sleep_until(target_dt: datetime):
    """Async sleep until target datetime."""
    while True:
        now = now_ist()
        seconds = (target_dt - now).total_seconds()
        if seconds <= 0:
            break
        # Sleep in chunks to allow graceful interruption
        await asyncio.sleep(min(seconds, 60.0))


class PortfolioRebalancer:
    """Main class for portfolio rebalancing operations."""
    
    def __init__(self, user_id: Optional[str] = None):
        self.zerodha_service = ZerodhaService()
        self.user_id = user_id
        
    async def load_basket(self, basket_file: str) -> Dict:
        """Load target basket allocation from JSON file."""
        try:
            with open(basket_file, 'r') as f:
                basket_data = json.load(f)
            
            logger.info(f"Loaded basket from {basket_file}")
            logger.info(f"Basket contains {len(basket_data['stocks'])} stocks")
            
            return basket_data
        except Exception as e:
            logger.error(f"Failed to load basket file {basket_file}: {e}")
            raise
    
    async def get_current_portfolio(self) -> Dict:
        """Get current portfolio holdings and positions."""
        portfolio = await self.zerodha_service.get_portfolio_summary(self.user_id)
        
        # Convert holdings to a more usable format
        current_holdings = {}
        for holding in portfolio['holdings']:
            ticker = holding['tradingsymbol']
            current_holdings[ticker] = {
                'quantity': int(holding['quantity']),
                'average_price': float(holding['average_price']),
                # Per API: use last_price for value computations
                'current_value': float(holding.get('last_price') or 0.0) * int(holding['quantity']),
                'ltp': float(holding.get('last_price', holding['average_price'])),
                'exchange': holding.get('exchange', 'NSE')
            }
        
        # Add positions using net positions (per API, 'net' is actual current portfolio)
        for position in portfolio['positions']['net']:
            ticker = position['tradingsymbol']
            exchange = position.get('exchange', 'NSE')
            qty = int(position.get('quantity') or 0)
            ltp = float(position.get('last_price', position.get('average_price', 0.0)))
            multiplier = int(position.get('multiplier') or 1)
            if ticker in current_holdings:
                # Update quantity if position exists
                current_holdings[ticker]['quantity'] += qty
                # Update latest ltp and exchange if available
                current_holdings[ticker]['ltp'] = ltp or current_holdings[ticker]['ltp']
                current_holdings[ticker]['exchange'] = current_holdings[ticker].get('exchange') or exchange
            elif qty != 0:
                # Add new position
                current_holdings[ticker] = {
                    'quantity': qty,
                    'average_price': float(position.get('average_price') or 0.0),
                    # For positions, value = last_price * quantity * multiplier
                    'current_value': ltp * qty * multiplier,
                    'ltp': ltp,
                    'exchange': exchange
                }
        
        portfolio['current_holdings'] = current_holdings
        return portfolio
    
    async def calculate_rebalancing_actions(self, basket_data: Dict, portfolio: Dict, 
                                          min_order_value: float = 1000.0) -> Tuple[List[Dict], float]:
        """Calculate rebalancing orders and return (actions, total_deficit_amount).

        total_deficit_amount is the sum over all tickers of |target_value - current_value|,
        using current LTPs and current quantities. Actions are only created for deficits
        above min_order_value.
        """
        target_weights = {stock['stock_ticker']: stock['weight'] for stock in basket_data['stocks']}
        current_holdings = portfolio['current_holdings']
        total_value = portfolio['total_value']
        
        logger.info(f"Total portfolio value: ₹{total_value:,.2f}")
        logger.info(f"Target allocation has {len(target_weights)} stocks")
        logger.info(f"Current holdings have {len(current_holdings)} stocks")
        
        actions = []
        total_deficit_amount = 0.0
        
        # Get current LTP for all relevant stocks using their exchange when known
        all_tickers = set(target_weights.keys()) | set(current_holdings.keys())
        instruments = []
        ticker_to_exchange = {}
        for ticker in all_tickers:
            ex = current_holdings.get(ticker, {}).get('exchange', 'NSE')
            ticker_to_exchange[ticker] = ex
            instruments.append(f"{ex}:{ticker}")
        
        try:
            ltp_data = await self.zerodha_service.get_ltp(self.user_id, instruments)
        except Exception as e:
            logger.error(f"Failed to get LTP: {e}")
            # Fallback to using average prices
            ltp_data = {}
            for ticker in all_tickers:
                if ticker in current_holdings:
                    ex = ticker_to_exchange.get(ticker, 'NSE')
                    ltp_data[f"{ex}:{ticker}"] = {
                        'last_price': current_holdings[ticker]['ltp']
                    }
        
        # Calculate required actions for each stock
        deficits = []  # List of (deficit_value, action) tuples for prioritization
        
        for ticker in all_tickers:
            target_weight = target_weights.get(ticker, 0.0)
            target_value = total_value * target_weight
            
            current_quantity = current_holdings.get(ticker, {}).get('quantity', 0)
            
            # Get current price
            ex = ticker_to_exchange.get(ticker, 'NSE')
            ltp_key = f"{ex}:{ticker}"
            if ltp_key in ltp_data:
                current_price = float(ltp_data[ltp_key]['last_price'])
            elif ticker in current_holdings:
                current_price = current_holdings[ticker]['ltp']
            else:
                logger.warning(f"No price available for {ticker}, skipping")
                continue
            
            current_value = current_quantity * current_price
            
            # Calculate difference
            value_diff = target_value - current_value
            total_deficit_amount += abs(value_diff)
            
            if abs(value_diff) < min_order_value:
                logger.info(f"{ticker}: No action needed (diff: ₹{value_diff:.2f})")
                continue
            
            # Determine transaction type
            if value_diff > 0:
                # Need to buy more
                quantity_to_buy = int(value_diff / current_price)
                if quantity_to_buy > 0:
                    action = {
                        'ticker': ticker,
                        'action': 'BUY',
                        'quantity': quantity_to_buy,
                        'price': current_price,
                        'value': quantity_to_buy * current_price,
                        'target_weight': target_weight,
                        'current_weight': current_value / total_value if total_value > 0 else 0,
                        'deficit': value_diff
                    }
                    deficits.append((value_diff, action))
                    
            else:
                # Need to sell
                quantity_to_sell = min(current_quantity, int(abs(value_diff) / current_price))
                if quantity_to_sell > 0:
                    action = {
                        'ticker': ticker,
                        'action': 'SELL',
                        'quantity': quantity_to_sell,
                        'price': current_price,
                        'value': quantity_to_sell * current_price,
                        'target_weight': target_weight,
                        'current_weight': current_value / total_value if total_value > 0 else 0,
                        'deficit': value_diff
                    }
                    deficits.append((abs(value_diff), action))
        
        # Sort by deficit (highest first) to prioritize most out-of-balance positions
        deficits.sort(key=lambda x: x[0], reverse=True)
        actions = [action for deficit, action in deficits]
        
        return actions, total_deficit_amount
    
    async def _wait_for_market_window_if_needed(self):
        """If outside market hours, wait until 9:14 AM IST of next trading day."""
        current = now_ist()
        if is_market_open_ist(current):
            return
        target = next_9_14_ist(current)
        pretty_date = target.strftime("%Y-%m-%d")
        print("\n⏳ Market is closed. Waiting until 9:14 AM IST to start placing orders...")
        print(f"   Current IST time: {current.strftime('%Y-%m-%d %H:%M:%S')} | Target: {target.strftime('%Y-%m-%d %H:%M:%S')}")
        await sleep_until(target)
        print("🕘 It's 9:14 AM IST. Preparing to place orders and will retry until market opens at 9:15.")

    async def _place_order_with_retries(self, action: Dict) -> Optional[str]:
        """Place an order with systematic retries around market open and transient failures.

        Strategy:
        - If before 9:15, retry every 2-5 seconds until 9:16.
        - After 9:16, use backoff retries up to a reasonable limit.
        - Stop retrying if market closes (15:30 IST) for the day.
        """
        max_backoff_seconds = 60
        backoff = 2.0
        attempt = 0
        start_time = now_ist()
        cutoff_close = datetime.combine(start_time.date(), MARKET_CLOSE, tzinfo=IST)

        while True:
            # Stop if market closed for the current day
            if now_ist() >= cutoff_close:
                logger.warning(f"Market closed before completing order for {action['ticker']}")
                return None

            try:
                order_id = await self.zerodha_service.place_order(
                    user_id=self.user_id,
                    variety='regular',
                    exchange='NSE',
                    tradingsymbol=action['ticker'],
                    transaction_type=action['action'],
                    quantity=action['quantity'],
                    product='CNC',  # Cash and Carry for delivery
                    order_type='MARKET'  # Market order for immediate execution
                )
                return order_id
            except Exception as e:
                attempt += 1
                err_msg = str(e)
                now = now_ist()
                # Determine retry interval
                if now.time() < MARKET_OPEN:
                    # Before market open, retry quickly
                    sleep_secs = 3.0
                else:
                    # After open, exponential backoff up to 60s
                    sleep_secs = min(backoff, max_backoff_seconds)
                    backoff = min(backoff * 1.7, max_backoff_seconds)

                logger.warning(f"Order attempt {attempt} for {action['ticker']} failed: {err_msg}. Retrying in {sleep_secs:.0f}s...")
                await asyncio.sleep(sleep_secs)

    async def execute_orders(self, actions: List[Dict], dry_run: bool = True, quiet: bool = False) -> List[str]:
        """Execute the calculated rebalancing orders."""
        order_ids = []
        
        if dry_run:
            print("\n" + "="*80)
            print("DRY RUN MODE - No actual orders will be placed")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("LIVE MODE - Orders will be placed on Zerodha")
            print("="*80)
        
        total_buy_value = sum(action['value'] for action in actions if action['action'] == 'BUY')
        total_sell_value = sum(action['value'] for action in actions if action['action'] == 'SELL')
        
        print(f"\nPortfolio Rebalancing Summary:")
        print(f"Total Buy Orders:  ₹{total_buy_value:,.2f}")
        print(f"Total Sell Orders: ₹{total_sell_value:,.2f}")
        print(f"Net Cash Flow:     ₹{total_sell_value - total_buy_value:,.2f}")
        print(f"\nPlanned Orders ({len(actions)} total):")
        print("-" * 80)
        
        for i, action in enumerate(actions, 1):
            print(f"{i:2d}. {action['action']:<4} {action['quantity']:>6} × {action['ticker']:<12} "
                  f"@ ₹{action['price']:>8.2f} = ₹{action['value']:>10,.2f} "
                  f"({action['current_weight']:.1%} → {action['target_weight']:.1%})")
        
        if not actions:
            print("No rebalancing actions needed!")
            return order_ids
        
        if dry_run:
            print(f"\n✅ Dry run completed. {len(actions)} orders planned.")
            return order_ids
        
        # Confirm before executing
        if not quiet:
            print(f"\n⚠️  Ready to place {len(actions)} orders on Zerodha.")
            confirm = input("Type 'CONFIRM' to proceed: ")
            if confirm != 'CONFIRM':
                print("❌ Orders cancelled.")
                return order_ids
        else:
            print("\n⚠️  Quiet mode enabled: auto-confirming order placement.")
        
        # If market is closed, wait until 9:14 AM IST and then begin retries
        await self._wait_for_market_window_if_needed()

        print("\n🚀 Placing orders...")
        
        # Execute orders with prioritization
        for i, action in enumerate(actions, 1):
            try:
                print(f"[{i}/{len(actions)}] Placing {action['action']} order for {action['ticker']}...")
                order_id = await self._place_order_with_retries(action)
                if not order_id:
                    print(f"⚠️  Skipping {action['ticker']} as market closed before successful placement.")
                    continue

                order_ids.append(order_id)
                print(f"✅ Order placed successfully. Order ID: {order_id}")
                
                # Small delay between orders
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to place order for {action['ticker']}: {e}")
                print(f"❌ Failed to place order for {action['ticker']}: {e}")
                
                # Ask if user wants to continue
                if i < len(actions):
                    if not quiet:
                        continue_trading = input("Continue with remaining orders? (y/n): ")
                        if continue_trading.lower() != 'y':
                            break
                    else:
                        print("Quiet mode: continuing with remaining orders...")
                        continue
        
        print(f"\n✅ Rebalancing completed. {len(order_ids)} orders placed successfully.")
        return order_ids
    
    async def rebalance(self, basket_file: str, dry_run: bool = True, 
                       min_order_value: float = 1000.0, quiet: bool = False,
                       target_deficit: float = 1000.0) -> List[str]:
        """Main rebalancing function. Iteratively rebalance until total deficit is below
        target_deficit or up to 10 tries. In dry-run mode, only one iteration is performed.
        """
        print("Portfolio Rebalancing Tool")
        print("=" * 50)
        print(f"Basket file: {basket_file}")
        print(f"User ID: {self.user_id}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Min order value: ₹{min_order_value}")
        print(f"Target deficit: ₹{target_deficit}")
        print(f"Quiet mode: {'ON' if quiet else 'OFF'}")
        print()
        
        # Load target basket
        basket_data = await self.load_basket(basket_file)

        overall_order_ids: List[str] = []
        attempt = 0

        while True:
            attempt += 1
            print(f"\n📊 Fetching current portfolio (attempt {attempt})...")
            portfolio = await self.get_current_portfolio()

            print("⚖️  Calculating rebalancing actions and total deficit...")
            actions, total_deficit = await self.calculate_rebalancing_actions(
                basket_data, portfolio, min_order_value
            )
            print(f"📉 Total deficit: ₹{total_deficit:,.2f} (target ≤ ₹{target_deficit:,.2f})")

            if total_deficit <= target_deficit:
                print("✅ Target deficit achieved. No further rebalancing needed.")
                break

            if not actions:
                print("ℹ️  No actionable orders (all diffs below min order value). Stopping.")
                break

            if dry_run:
                print("🧪 Dry run mode: not executing orders. Stopping after first iteration.")
                break

            # Execute orders
            order_ids = await self.execute_orders(actions, dry_run, quiet)
            overall_order_ids.extend(order_ids)

            if attempt >= 10:
                print("⚠️  Reached maximum attempts (10). Stopping.")
                break

        return overall_order_ids


async def get_user_id(provided_user_id: Optional[str], quiet: bool = False) -> str:
    """Get user ID either from argument or from stored tokens or new authentication."""
    zerodha_service = ZerodhaService()
    
    if provided_user_id:
        # Check if this user has a valid token
        token = await zerodha_service.get_stored_token(provided_user_id)
        if token:
            print(f"✅ Using provided user ID: {provided_user_id}")
            return provided_user_id
        else:
            print(f"❌ No valid token found for user ID: {provided_user_id}")
            print("Starting authentication process...")
    
    # Check if there are any stored tokens
    from src.db.database import db, COLLECTIONS
    
    stored_tokens = list(db[COLLECTIONS["zerodha_tokens"]].find({"is_active": True}))
    
    if stored_tokens and not provided_user_id:
        if quiet:
            # Auto-pick first user in quiet mode
            selected_token = stored_tokens[0]
            user_id = selected_token['user_id']
            print(f"Quiet mode: auto-selecting stored user {user_id}")
            valid_token = await zerodha_service.get_stored_token(user_id)
            if valid_token:
                print(f"✅ Using stored token for user: {user_id}")
                return user_id
            else:
                print(f"❌ Stored token for {user_id} is invalid; starting new authentication...")
        else:
            print("Found stored authentication tokens:")
            for i, token in enumerate(stored_tokens):
                print(f"{i+1}. User ID: {token['user_id']} (Created: {token['created_time']})")
            
            choice = input(f"Select a user (1-{len(stored_tokens)}) or press Enter for new authentication: ")
            
            if choice.isdigit() and 1 <= int(choice) <= len(stored_tokens):
                selected_token = stored_tokens[int(choice) - 1]
                user_id = selected_token['user_id']
                
                # Verify token is still valid
                valid_token = await zerodha_service.get_stored_token(user_id)
                if valid_token:
                    print(f"✅ Using stored token for user: {user_id}")
                    return user_id
                else:
                    print(f"❌ Stored token for {user_id} is invalid")
    
    # Need to authenticate
    print("Starting new authentication...")
    user_id = await authenticate_user(quiet=quiet)
    return user_id


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Rebalance stock portfolio using Zerodha Kite API")
    parser.add_argument("basket_file", help="Path to basket JSON file")
    parser.add_argument("--user-id", help="Zerodha user ID (if not provided, will use stored token or authenticate)")
    parser.add_argument("--dry-run", action="store_true", default=True, 
                       help="Perform dry run without placing actual orders (default: True)")
    parser.add_argument("--live", action="store_true", 
                       help="Place actual orders (overrides --dry-run)")
    parser.add_argument("--min-order-value", type=float, default=1000.0,
                       help="Minimum order value in rupees (default: 1000)")
    parser.add_argument("--quiet", action="store_true", help="Run in quiet non-interactive mode (auto-select defaults)")
    parser.add_argument("--target-deficit", type=float, default=1000.0,
                       help="Target total deficit to reach before stopping (default: 1000)")
    
    args = parser.parse_args()
    
    # Validate basket file
    if not Path(args.basket_file).exists():
        print(f"❌ Basket file not found: {args.basket_file}")
        sys.exit(1)
    
    # Determine run mode
    dry_run = not args.live  # If --live is specified, dry_run becomes False
    
    try:
        # Get user ID
        user_id = await get_user_id(args.user_id, quiet=args.quiet)
        
        # Create rebalancer and run
        rebalancer = PortfolioRebalancer(user_id)
        order_ids = await rebalancer.rebalance(
            basket_file=args.basket_file,
            dry_run=dry_run,
            min_order_value=args.min_order_value,
            quiet=args.quiet,
            target_deficit=args.target_deficit,
        )
        
        if order_ids:
            print(f"\n📋 Order IDs: {', '.join(order_ids)}")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Rebalancing failed: {e}")
        print(f"❌ Rebalancing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 