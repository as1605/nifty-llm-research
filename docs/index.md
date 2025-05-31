# Nifty Stock Research Documentation

## Overview

The Nifty Stock Research system is an AI-powered tool for analyzing Indian stocks (NSE Top 100) and generating price forecasts and portfolio recommendations. The system uses Perplexity's models to analyze market news, financial data, and generate predictions.

## Components

### Stock Research Agent

The stock research agent (`src/agents/stock_research.py`) is responsible for:

- Gathering comprehensive stock data and news using Perplexity's sonar-deep-research model
- Analyzing the data using Perplexity's models
- Generating price forecasts for multiple time horizons

### Portfolio Optimization

The portfolio agent (`src/agents/portfolio.py`):

- Analyzes daily stock forecasts
- Selects the best 5 stocks for the portfolio using Perplexity's sonar-reasoning-pro model
- Generates expected return estimates
- Provides a summary of the selection rationale

### Database

The system uses Amazon Aurora PostgreSQL to store:

- Daily stock forecasts
- Weekly portfolio recommendations
- Historical performance data

### Visualization

The visualization module (`src/visualization/plotter.py`) creates:

- Stock price prediction graphs
- Portfolio performance charts
- Interactive visualizations for analysis

### Email Notifications

The email module (`src/utils/email.py`) sends:

- Weekly portfolio recommendations
- Performance summaries
- Analysis reports

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `env.template` to `.env`
   - Fill in your API keys and credentials

5. Set up the database:
   ```bash
   python scripts/setup_db.py
   ```

## Usage

### Running Stock Analysis

```bash
python scripts/analyze_stocks.py
```

This will:
- Analyze all NSE Top 100 stocks
- Generate price forecasts
- Save results to the database
- Create visualizations

### Generating Portfolio Recommendations

```bash
python scripts/generate_portfolio.py
```

This will:
- Read today's forecasts
- Select the best 5 stocks
- Send email recommendations
- Update portfolio history

## Development

### Running Tests

```bash
pytest
```

### Code Style

- Format code: `black .`
- Sort imports: `isort .`
- Type checking: `mypy .`
- Linting: `flake8`

### Documentation

Build documentation:
```bash
mkdocs build
```

Serve documentation locally:
```bash
mkdocs serve
``` 