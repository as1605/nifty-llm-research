# Nifty LLM Research

A research project using LLMs to analyze and forecast NSE-listed stocks, with a focus on portfolio optimization.

## Overview

This project uses Google's Gemini AI to:
1. Analyze NSE-listed stocks and generate price forecasts
2. Optimize stock portfolios based on these forecasts
3. Track and visualize portfolio performance

## Key Features

- **Stock Analysis**: Deep research on individual stocks using Google Search integration
- **Portfolio Optimization**: Selection of optimal stock combinations based on forecasts
- **Performance Tracking**: Historical tracking of portfolio performance
- **Visualization**: Performance charts and analysis reports
- **Output Generation**: Detailed reports in both JSON and Markdown formats

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- Google Cloud API key for Gemini AI
- Google Search API key

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
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Usage

1. Seed the database with default prompts:
```bash
python scripts/seed_prompts.py
```

2. Generate stock forecasts:
```bash
python scripts/analyze_stocks.py --index "NIFTY 50" --force-nse
```

3. Generate portfolio recommendations:
```bash
python scripts/generate_portfolio.py --index "NIFTY 50" --filter-top-n 20 --basket-size-k 5
```

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
- Files are named as: `{index}-{timestamp}-{n}-{k}.{json/md}`

## Project Structure

```
nifty-llm-research/
├── config/             # Configuration files
├── docs/              # Documentation and outputs
│   └── baskets/       # Portfolio recommendations
├── prompts/           # Development history and Cursor prompts
├── scripts/           # Command-line scripts
├── src/              # Source code
│   ├── agents/       # LLM agents
│   ├── db/          # Database models and utilities
│   ├── utils/       # Utility functions
│   └── visualization/# Plotting and visualization
└── tests/            # Test files
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
- NSE for stock data
- Contributors and maintainers
