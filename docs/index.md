---
layout: default
title: Nifty Stock Research System
description: AI-powered platform for analyzing Indian stocks using Gemini AI
---

# Nifty Stock Research System

## Overview

The Nifty Stock Research System is an AI-powered platform for analyzing Indian stocks, specifically focusing on the NSE Top 100 companies. This project leverages Google's Gemini AI model to perform deep research and analysis of stocks, generating comprehensive reports and portfolio recommendations.

The system uses a unique approach called "vibe-coding" (stored in the [`prompts/`](https://github.com/as1605/nifty-llm-research/tree/main/prompts) directory) to generate human-like, contextually aware analysis of stocks. This methodology combines technical analysis with qualitative insights to provide a holistic view of each stock's potential.

## Key Features

- 🤖 AI-powered stock analysis using Gemini AI
- 📊 Comprehensive technical and fundamental analysis
- 💼 Portfolio optimization and recommendations
- 📈 Historical performance tracking
- 📱 Modern, responsive web interface

## Latest Research Outputs

Our latest research outputs are available in the following reports:

- **NIFTY 50** (23 June 2025): [Analysis](baskets/NIFTY%2050__Jun_23_2025_05_31__N20_K5). Invest with [smallcase](https://smlc.se/MIRds)
- **NIFTY SMALLCAP 250** (23 June 2025): [Analysis](baskets/NIFTY%20SMALLCAP%20250__Jun_23_2025_06_18__N50_K10). Invest with [smallcase](https://smlc.se/LBkbT)


## Architecture

The system is built with a modular architecture consisting of several key components:

1. **AI Analysis Engine**
   - Powered by Google's Gemini AI
   - Custom prompt engineering for stock analysis
   - Context-aware research generation

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
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration**
   - Set up environment variables
   - Configure MongoDB connection
   - Set up Gemini API credentials

## Development

1. **Code Standards**
   - Use type hints
   - Follow PEP 8
   - Write unit tests
   - Document new features

2. **Prompt Management**
   - Store prompts in `prompts/` directory
   - Version control prompt changes
   - Document prompt modifications

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