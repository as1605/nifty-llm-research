# Nifty Stock Research System Documentation

## Overview

The Nifty Stock Research System is an AI-powered platform for analyzing Indian stocks, specifically focusing on the NSE Top 100 companies. The system leverages advanced AI models and data analysis techniques to provide comprehensive stock research and portfolio recommendations.

## Architecture

The system is built with a modular architecture consisting of several key components:

1. **AI Agents**
   - Stock Research Agent: Performs deep research using Perplexity AI
   - Portfolio Agent: Generates optimized portfolio recommendations

2. **Data Storage**
   - MongoDB database for storing:
     - Stock forecasts and predictions
     - Historical price data
     - Research reports
     - Portfolio recommendations

3. **Visualization**
   - Interactive charts and graphs
   - Performance metrics
   - Portfolio analytics

4. **Automation**
   - Scheduled stock analysis
   - Automated email reports
   - Portfolio rebalancing

## Setup and Configuration

1. **Environment Setup**
   - Create and activate virtual environment
   - Install dependencies
   - Configure environment variables

2. **Database Setup**
   - Install MongoDB
   - Configure connection string
   - Initialize collections

3. **API Configuration**
   - Set up Perplexity API key
   - Configure AWS credentials
   - Set up email notifications

## Usage Guide

1. **Running Analysis**
   ```bash
   python scripts/analyze_stocks.py
   ```

2. **Generating Portfolio**
   ```bash
   python scripts/generate_portfolio.py
   ```

3. **Viewing Reports**
   ```bash
   python scripts/visualize_predictions.py
   ```

## Development Guidelines

1. **Code Standards**
   - Use type hints
   - Follow PEP 8
   - Write unit tests
   - Document new features

2. **Prompt Management**
   - Store prompts in `prompts/` directory
   - Version control prompt changes
   - Document prompt modifications

3. **Testing**
   - Run tests before committing
   - Maintain test coverage
   - Update tests for new features

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## Support

For issues and feature requests, please use the GitHub issue tracker. 