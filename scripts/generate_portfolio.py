#!/usr/bin/env python
"""
Script for generating and sending portfolio recommendations.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from src.agents.portfolio import PortfolioAgent
from src.db.database import async_db, COLLECTIONS
from src.utils.email import EmailSender
from src.visualization.plotter import StockPlotter
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def generate_portfolio():
    """Generate portfolio recommendations and send email."""
    try:
        # Get today's forecasts
        today = datetime.utcnow().date()
        
        # Get latest forecasts
        forecasts = await async_db[COLLECTIONS['forecasts']].find(
            {"created_time": {"$gte": today}}
        ).to_list(length=None)
        
        if not forecasts:
            logger.error("No forecasts found for today")
            return
        
        # Generate portfolio recommendations
        agent = PortfolioAgent()
        result = await agent.optimize_portfolio(forecasts)
        
        # Generate visualization
        plotter = StockPlotter()
        
        # Get historical baskets
        historical_baskets = await async_db[COLLECTIONS['baskets']].find().sort(
            "creation_date", 1
        ).to_list(length=None)
        
        # Create performance visualization
        save_path = Path(settings.data_dir) / "visualizations" / "portfolio_performance.png"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        plotter.plot_portfolio_performance(
            historical_baskets,
            str(save_path)
        )
        
        # Send email
        email_sender = EmailSender()
        email_sent = await email_sender.send_portfolio_update(
            selected_stocks=result["selected_stocks"],
            expected_return=result["expected_return"],
            summary=result["summary"]
        )
        
        if email_sent:
            logger.info("Portfolio recommendation email sent successfully")
        else:
            logger.error("Failed to send portfolio recommendation email")
        
    except Exception as e:
        logger.error(f"Error generating portfolio: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(generate_portfolio()) 