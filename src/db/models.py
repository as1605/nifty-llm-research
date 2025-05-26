"""
Database models for the Nifty Stock Research project.
"""
from datetime import date
from typing import List, Optional

from sqlalchemy import ARRAY, Column, Date, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StockForecast(Base):
    """Model for storing daily stock price forecasts."""
    
    __tablename__ = 'stock_forecasts'
    
    id = Column(Integer, primary_key=True)
    stock_symbol = Column(String(10), nullable=False)
    current_price = Column(Float, nullable=False)
    forecast_1w = Column(Float, nullable=False)
    forecast_1m = Column(Float, nullable=False)
    forecast_3m = Column(Float, nullable=False)
    forecast_6m = Column(Float, nullable=False)
    forecast_12m = Column(Float, nullable=False)
    forecast_date = Column(Date, nullable=False, default=date.today)
    analysis_summary = Column(Text)
    confidence_score = Column(Float)
    
    def __repr__(self):
        return f"<StockForecast(symbol={self.stock_symbol}, date={self.forecast_date})>"

class WeeklyBasket(Base):
    """Model for storing weekly stock basket recommendations."""
    
    __tablename__ = 'weekly_baskets'
    
    id = Column(Integer, primary_key=True)
    basket_date = Column(Date, nullable=False)
    selected_stocks = Column(ARRAY(String), nullable=False)
    expected_return = Column(Float)
    summary = Column(Text)
    
    def __repr__(self):
        return f"<WeeklyBasket(date={self.basket_date}, stocks={self.selected_stocks})>" 