# Portfolio Rebalancing with Zerodha Kite API

This guide explains how to use the portfolio rebalancing script to automatically rebalance your stock portfolio based on AI-generated basket allocations.

## Overview

The rebalancing system connects to the Zerodha Kite API to:
1. Authenticate securely with OAuth flow
2. Fetch current portfolio holdings and positions
3. Calculate required buy/sell orders to match target allocation
4. Place orders on Zerodha (with confirmation)

## Prerequisites

### 1. Zerodha Developer Account Setup (Kite Connect)

Follow these steps to set up your Zerodha developer account and app correctly:

1. Create/login to your account on the Zerodha developer portal:
   - [Kite Connect portal](https://kite.trade/)
   - [Kite Connect docs](https://kite.trade/docs/connect/v3/)
2. Subscribe to the Kite Connect API (paid subscription is required). Full market quote APIs may need an additional Market Data subscription.
   - If you see "Insufficient permission for that call" using full quotes, switch to `ltp()` (Last Traded Price) which works with basic permissions. See [Market quotes](https://kite.trade/docs/connect/v3/market-quotes/).
3. Create a new app (Web app/Standalone) and set the Redirect URL to:
   - `http://localhost:8080/callback`
   - This must match exactly what the script uses during OAuth. You can change it later for production (e.g., to your HTTPS domain), but it must match your app settings when running the script.
   - See [Login flow](https://kite.trade/docs/connect/v3/user/#login-flow).
4. Copy the generated API Key and API Secret from your app page.
5. Add the credentials and encryption key to your `.env` (see next section).

Notes:
- Access tokens on Kite Connect expire daily. This project detects invalid/expired tokens automatically and triggers a new authentication flow when needed.
- Ensure your Zerodha account is in good standing and has requisite permissions for trading.

### 2. Environment

```bash
cp env.template .env
# Edit .env and add your credentials
ZERODHA_API_KEY=your_zerodha_api_key_here
ZERODHA_API_SECRET=your_zerodha_api_secret_here

# Generate encryption key to securely store access tokens
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=the_key_you_generated
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

```bash
python scripts/setup_db.py
```

## Quick Start

### 1. Authenticate (interactive browser flow)

The rebalancing script will automatically start a local OAuth callback server and open your browser. Use a dry run with any basket JSON to trigger authentication:

```bash
python scripts/rebalance_portfolio.py docs/baskets/"NIFTY 50__Jun_30_2025_00_58__N20_K5.json" --dry-run --quiet
```

- Your browser will open Zerodha login.
- On successful login, Zerodha will redirect to `http://localhost:8080/callback` where the script exchanges the request token for an access token and stores it encrypted in MongoDB.
- Subsequent runs will reuse the stored token until it expires (then it will re-auth).

### 2. Run Dry-Run Rebalancing

Test rebalancing without placing actual orders:

```bash
python scripts/rebalance_portfolio.py docs/baskets/NIFTY_50__Jul_27_2025_22_04__N20_K5.json --dry-run
```

### 3. Execute Live Rebalancing

⚠️ CAUTION: This places real orders on Zerodha!

```bash
python scripts/rebalance_portfolio.py docs/baskets/NIFTY_50__Jul_27_2025_22_04__N20_K5.json --live
```

## Authentication Flow Details

- Local FastAPI server listens at `http://localhost:8080/callback` (ensure your Kite app Redirect URL matches this during development)
- Script prints a clickable login URL and tries to open your default browser automatically
- On redirect, the script exchanges `request_token` for `access_token` and stores it encrypted
- Tokens are validated before API calls; invalid tokens are marked inactive and a new login is triggered

## Rebalancing Logic

### Portfolio Value Calculation

Total portfolio value includes:
- Holdings (quantity × price) using `ltp()` for current price
- Positions (day/net P&L)
- Available cash (margins)

### Target Allocation

The script reads basket JSON files with this structure:
```json
{
  "stocks": [
    { "stock_ticker": "RELIANCE", "weight": 0.25 },
    { "stock_ticker": "TCS", "weight": 0.20 }
  ]
}
```

### Order Calculation & Execution

- Calculates `target_value - current_value` per stock
- Prioritizes by largest deficit first
- Places MARKET CNC orders on NSE
- Uses `ltp()` for price to avoid elevated quote permissions
- Market-hour handling:
  - If outside 9:15–15:30 IST, waits until 09:14 IST of next trading day
  - If between 09:14–09:15 IST, starts retrying immediately
  - Exponential backoff after open; stops at 15:30 IST and skips unplaced orders

### Quiet Mode

- `--quiet` auto-confirms and suppresses prompts
- If multiple stored users exist, picks the first token automatically

## Usage Examples

```bash
# Dry run with defaults
python scripts/rebalance_portfolio.py docs/baskets/my_basket.json --dry-run --quiet

# Live execution
python scripts/rebalance_portfolio.py docs/baskets/my_basket.json --live --quiet

# Minimum order value override
python scripts/rebalance_portfolio.py docs/baskets/my_basket.json --live --min-order-value 2000
```

## Relevant Zerodha Docs

- [Kite Connect Overview](https://kite.trade/docs/connect/v3/)
- [Login Flow](https://kite.trade/docs/connect/v3/user/#login-flow)
- [Market Quotes (ltp/quote)](https://kite.trade/docs/connect/v3/market-quotes/)
- [Orders](https://kite.trade/docs/connect/v3/orders/)

## Security & Safety

- Access tokens encrypted with Fernet; stored in MongoDB
- Dry-run mode for safe preview; live mode requires explicit flag
- Quiet mode for non-interactive runs (e.g., CI)
- No sensitive data is logged

## Troubleshooting

- "Insufficient permission for that call": Use `ltp()` instead of `quote()` or obtain proper Market Data subscription
- Authentication loops: Verify the app Redirect URL is exactly `http://localhost:8080/callback`
- Token invalid: The script will deactivate it and re-authenticate; ensure your app keys are correct 