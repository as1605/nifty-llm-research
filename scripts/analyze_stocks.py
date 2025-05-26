#!/usr/bin/env python
"""
Main script for analyzing NSE stocks and generating forecasts.
"""
import asyncio
import logging
from datetime import date
from pathlib import Path
from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from src.agents.stock_research import StockResearchAgent
from src.db.database import get_db
from src.db.models import StockForecast
from src.visualization.plotter import StockPlotter
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NSE Top 100 stocks (you should maintain this list or fetch it dynamically)
NSE_TOP_100 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    # Add more symbols...
]

async def analyze_stock(symbol: str, agent: StockResearchAgent, db: Session) -> None:
    """Analyze a single stock and save results.
    
    Args:
        symbol: Stock symbol
        agent: Stock research agent instance
        db: Database session
    """
    try:
        # Get analysis from agent
        logger.info(f"Analyzing {symbol}...")
        result = await agent.analyze_stock(symbol)
        
        # Create forecast object
        forecast = StockForecast(
            stock_symbol=symbol,
            current_price=result["current_price"],
            forecast_1w=result["forecast_1w"],
            forecast_1m=result["forecast_1m"],
            forecast_3m=result["forecast_3m"],
            forecast_6m=result["forecast_6m"],
            forecast_12m=result["forecast_12m"],
            forecast_date=date.today(),
            analysis_summary=result.get("summary"),
            confidence_score=result.get("confidence")
        )
        
        # Save to database
        db.add(forecast)
        db.commit()
        
        # Generate visualization
        plotter = StockPlotter()
        
        # Get historical forecasts
        historical_forecasts = (
            db.query(StockForecast)
            .filter(StockForecast.stock_symbol == symbol)
            .order_by(StockForecast.forecast_date)
            .all()
        )
        
        # Create visualization
        save_path = Path(settings.data_dir) / "visualizations" / f"{symbol}_forecast.png"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        plotter.plot_predictions(
            symbol,
            [forecast.__dict__ for forecast in historical_forecasts],
            str(save_path)
        )
        
        logger.info(f"Completed analysis for {symbol}")
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        raise

async def main():
    """Main function to analyze all stocks."""
    agent = StockResearchAgent()
    
    async with asyncio.TaskGroup() as tg:
        with get_db() as db:
            for symbol in NSE_TOP_100:
                tg.create_task(analyze_stock(symbol, agent, db))

if __name__ == "__main__":
    asyncio.run(main()) 