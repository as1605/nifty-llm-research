#!/usr/bin/env python
"""
Script for generating and sending portfolio recommendations.
"""
import asyncio
import logging
from datetime import date
from pathlib import Path

from sqlalchemy import func

from src.agents.portfolio import PortfolioAgent
from src.db.database import get_db
from src.db.models import StockForecast, WeeklyBasket
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
        with get_db() as db:
            today = date.today()
            
            # Get latest forecasts
            forecasts = (
                db.query(StockForecast)
                .filter(StockForecast.forecast_date == today)
                .all()
            )
            
            if not forecasts:
                logger.error("No forecasts found for today")
                return
            
            # Convert to list of dictionaries
            forecast_data = [forecast.__dict__ for forecast in forecasts]
            
            # Generate portfolio recommendations
            agent = PortfolioAgent()
            result = await agent.optimize_portfolio(forecast_data)
            
            # Save to database
            basket = WeeklyBasket(
                basket_date=today,
                selected_stocks=result["selected_stocks"],
                expected_return=result["expected_return"],
                summary=result["summary"]
            )
            db.add(basket)
            
            # Generate visualization
            plotter = StockPlotter()
            
            # Get historical baskets
            historical_baskets = (
                db.query(WeeklyBasket)
                .order_by(WeeklyBasket.basket_date)
                .all()
            )
            
            # Create performance visualization
            save_path = Path(settings.data_dir) / "visualizations" / "portfolio_performance.png"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            plotter.plot_portfolio_performance(
                [b.__dict__ for b in historical_baskets],
                str(save_path)
            )
            
            db.commit()
            
            # Send email
            email_sender = EmailSender()
            email_sent = email_sender.send_portfolio_update(
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