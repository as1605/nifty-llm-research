# Nifty Stock Research and Analysis System

An AI-powered system for analyzing Indian stocks (NSE Top 100) using market news, financial data, and investor reports to generate price forecasts and portfolio recommendations.

## Features

- Deep research analysis of NSE Top 100 stocks
- Price forecasting for multiple time horizons (1w, 1m, 3m, 6m, 1y)
- Automated portfolio recommendation system
- Data persistence in Amazon Aurora PostgreSQL
- Automated email reporting via Amazon SES
- Interactive visualization of price predictions

## Project Structure

```
nifty-llm-research/
├── src/
│   ├── agents/             # AI agent implementations
│   ├── data/              # Data handling and processing
│   ├── db/                # Database operations
│   ├── visualization/     # Plotting and charting
│   └── utils/             # Helper functions and utilities
├── tests/                 # Test cases
├── docs/                  # Documentation
├── scripts/              # Automation scripts
└── config/              # Configuration files
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy env.template to .env and fill in your credentials:
   ```bash
   cp env.template .env
   ```

4. Set up the database:
   ```bash
   python scripts/setup_db.py
   ```

## Usage

1. Run the stock analysis:
   ```bash
   python scripts/analyze_stocks.py
   ```

2. Generate portfolio recommendations:
   ```bash
   python scripts/generate_portfolio.py
   ```

3. View visualizations:
   ```bash
   python scripts/visualize_predictions.py
   ```

## Development

- Code formatting: `black .`
- Import sorting: `isort .`
- Type checking: `mypy .`
- Linting: `flake8`
- Run tests: `pytest`

## Documentation

Detailed documentation is available in the `docs/` directory. To view the documentation locally:

```bash
mkdocs serve
```

## License

MIT License
