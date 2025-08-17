# Nifty LLM Research

A research project using LLMs to analyze and forecast NSE-listed stocks, with a focus on portfolio optimization.

## Overview

This project uses Google's Gemini AI to:
1. Analyze NSE-listed stocks and generate price forecasts
2. Optimize stock portfolios based on these forecasts
3. Track portfolio performance
4. Rebalance live Zerodha portfolios based on target allocations

## Key Features

- **Stock Analysis**: Deep research on individual stocks using Google Search integration
- **Portfolio Optimization**: Selection of optimal stock combinations based on forecasts
- **Rebalancing (Zerodha)**: Connect to Zerodha Kite API, fetch holdings/positions, and place orders to match a target basket
- **Performance Tracking**: Historical tracking of portfolio performance
- **Output Generation**: Detailed reports in both JSON and Markdown formats

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- Google Gemini API key(s) (supports comma-separated list for key rotation)
- Zerodha Kite Connect API key and secret
- Fernet `ENCRYPTION_KEY` for securely storing access tokens

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nifty-llm-research.git
cd nifty-llm-research
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.template .env
# Edit .env with your API keys and configuration
# GOOGLE_API_KEY can be comma-separated for key rotation on 429s
# Add ZERODHA_API_KEY, ZERODHA_API_SECRET, ENCRYPTION_KEY
```

## Usage

### One-click end-to-end run

Use `run.sh` to automate the full flow: analyze twice, generate portfolio, commit docs, push to Git, and rebalance using the latest basket.

```bash
./run.sh
```

- **Logs**: All Python script output is saved to `data/logs/` with timestamped filenames, while still echoed to console
- **Live orders**: Rebalancing runs in LIVE mode by default. Set `LIVE_REBALANCE=0` to dry-run.
- **Quiet mode**: Rebalancing uses `--quiet` by default to avoid interactive prompts (auto-confirms; picks first stored user if available)

Environment overrides (examples):
```bash
FILTER_TOP_N=50 BASKET_SIZE_K=10 PARALLEL=1 WORKERS=12 ./run.sh
LIVE_REBALANCE=0 QUIET_REBALANCE=1 MIN_ORDER_VALUE=2000 TARGET_DEFICIT=5000 ./run.sh
```

### Individual scripts

1. Seed the database with default prompts:
```bash
python scripts/seed_prompts.py
```

2. Generate stock forecasts:
```bash
python scripts/analyze_stocks.py --index "NIFTY 50" --force-nse --parallel -w 10
```

3. Generate portfolio recommendations:
```bash
python scripts/generate_portfolio.py --index "NIFTY 50" --filter-top-n 20 --basket-size-k 5
```

4. Rebalance portfolio (Zerodha):
```bash
# Dry run (safe)
python scripts/rebalance_portfolio.py docs/baskets/"NIFTY 50__Jun_30_2025_00_58__N20_K5.json" --dry-run --quiet --target-deficit 5000

# Live execution (places orders)
python scripts/rebalance_portfolio.py docs/baskets/"NIFTY 50__Jun_30_2025_00_58__N20_K5.json" --live --quiet --target-deficit 5000
```

See the dedicated guide: [Rebalancing README](README_REBALANCING.md).

## Rebalancing (Brief)

- **Access token flow**: Secure OAuth via a local FastAPI callback server; tokens are encrypted and stored in MongoDB
- **Market-hour handling**: If outside 9:15–15:30 IST, the script waits until 09:14 IST, then retries rapidly until market open; if between 09:14 and 09:15, it starts immediately
- **Prices**: Uses yfinance service for last price with automatic symbol normalization (`NSE:TICKER` → `TICKER.NS`, `BSE:TICKER` → `TICKER.BO`)
- **Portfolio value**: Holdings use `last_price × opening_quantity`; positions use `last_price × quantity × multiplier`; available cash uses `margins.equity.net`
- **Order strategy**: Prioritizes biggest deficits first, places MARKET CNC orders on NSE; exponential backoff on transient errors
- **Iterative convergence**: Computes total deficit (sum of absolute diffs from targets) and repeats up to 10 iterations until total deficit ≤ `--target-deficit` (dry-run performs a single iteration)
- **Quiet mode**: `--quiet` auto-confirms and avoids prompts; picks first stored user token if available

For full details and safety considerations, see [README_REBALANCING.md](README_REBALANCING.md).

## Understanding the Code

### Development History

This project was developed using Cursor IDE's AI pair programming capabilities. To see how the code was written:

1. Check the `prompts/` directory to see the actual Cursor prompts used during development
2. Each prompt file shows the exact conversation that led to the implementation
3. This serves as a proof of authenticity and helps understand the development process

### Prompts

The core of this project lies in its carefully crafted prompts. To understand how the code works:

1. Check the `scripts/seed_prompts.py` file to see the default prompts
2. Review the prompt configurations in the database
3. Understand how each prompt is used in the respective agents

### Outputs

All portfolio recommendations are saved in the `docs/baskets` directory:
- JSON files containing the full analysis
- Markdown files with formatted tables and explanations
- Files are named as: `{index}__{timestamp}__N{n}_K{k}.{json|md}`

## Project Structure

```
nifty-llm-research/
├── config/             # Configuration files
├── docs/               # Documentation and outputs
│   └── baskets/        # Portfolio recommendations
├── prompts/            # Development history and Cursor prompts
├── scripts/            # Command-line scripts
├── src/                # Source code
│   ├── agents/         # LLM agents
│   ├── db/             # Database models and utilities
│   ├── services/       # External services (Zerodha)
│   └── utils/          # Utility functions
└── tests/              # Test files
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for the LLM capabilities
- Zerodha Kite Connect for trading APIs
- NSE for stock data
- Contributors and maintainers
