# Nifty Stock Research and Analysis System

An AI-powered system for analyzing Indian stocks (NSE Top 100) using market news, financial data, and investor reports to generate price forecasts and portfolio recommendations.

## Features

- Deep research analysis of NSE Top 100 stocks using Google Gemini AI
- Price forecasting for multiple time horizons (1w, 1m, 3m, 6m, 1y)
- Automated portfolio recommendation system
- Data persistence in MongoDB
- Automated email reporting via Amazon SES
- Interactive visualization of price predictions
- Prompt-based configuration system for AI interactions
- Google Search integration for real-time market data

## Project Structure

```
nifty-llm-research/
├── src/
│   ├── agents/             # AI agent implementations
│   ├── data/              # Data handling and processing
│   ├── db/                # MongoDB operations
│   ├── visualization/     # Plotting and charting
│   └── utils/             # Helper functions and utilities
├── prompts/              # Documentation of prompt history and usage
├── tests/                # Test cases
├── docs/                 # Documentation
├── scripts/              # Automation scripts
├── config/              # Configuration files
└── cache/               # Cached data and results
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy env.template to .env and fill in your credentials:
   ```bash
   cp env.template .env
   ```

4. Set up MongoDB:
   - Install MongoDB locally or use MongoDB Atlas
   - Update the MongoDB connection string in .env
   - Run the database initialization script:
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
- Linting: `ruff check .`
- Run tests: `pytest`

## Documentation

Detailed documentation is available in the `docs/` directory. To view the documentation locally:

```bash
mkdocs serve
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

### Best Practices

- Follow PEP 8 style guide
- Write meaningful commit messages
- Document all new features
- Add type hints to new code
- Update prompts in the `prompts/` directory
- Run tests before submitting PRs

### Prompt Management

The `prompts/` directory serves as a historical record of all AI prompts used to generate and modify this repository. This includes:
- Initial repository setup prompts
- Code generation and modification prompts
- Documentation update prompts
- Any other AI-assisted changes

When making changes using AI assistance:
1. Create a new file in the `prompts/` directory
2. Document the prompt used and its purpose
3. Never modify existing prompt files
4. Follow the naming convention: `YYYY-MM-DD-description.md`

This helps maintain transparency and allows others to understand how the repository evolved.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## License

MIT License
