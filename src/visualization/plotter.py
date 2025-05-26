"""
Visualization module for plotting stock predictions.
"""
from datetime import datetime, timedelta
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config.settings import settings

class StockPlotter:
    """Class for creating stock prediction visualizations."""
    
    def __init__(self):
        """Initialize the plotter."""
        # Set style
        plt.style.use("seaborn")
        sns.set_palette("husl")
    
    def plot_predictions(
        self,
        stock_symbol: str,
        predictions: List[Dict],
        save_path: str = None
    ) -> None:
        """Plot stock price predictions over time.
        
        Args:
            stock_symbol: The stock symbol
            predictions: List of prediction dictionaries
            save_path: Optional path to save the plot
        """
        # Convert predictions to DataFrame
        df = pd.DataFrame(predictions)
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Plot each prediction line with a color gradient
        for i, row in df.iterrows():
            dates = [
                row["forecast_date"],
                row["forecast_date"] + timedelta(weeks=1),
                row["forecast_date"] + timedelta(days=30),
                row["forecast_date"] + timedelta(days=90),
                row["forecast_date"] + timedelta(days=180),
                row["forecast_date"] + timedelta(days=365)
            ]
            
            prices = [
                row["current_price"],
                row["forecast_1w"],
                row["forecast_1m"],
                row["forecast_3m"],
                row["forecast_6m"],
                row["forecast_12m"]
            ]
            
            # Create color gradient based on date
            color = plt.cm.viridis(i / len(df))
            
            plt.plot(
                dates,
                prices,
                marker="o",
                linestyle="-",
                alpha=0.7,
                color=color,
                label=row["forecast_date"].strftime("%Y-%m-%d")
            )
        
        # Customize plot
        plt.title(f"Price Predictions for {stock_symbol}")
        plt.xlabel("Date")
        plt.ylabel("Price (INR)")
        plt.grid(True, alpha=0.3)
        plt.legend(title="Prediction Date", bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.tight_layout()
        
        # Save or show plot
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        else:
            plt.show()
        
        plt.close()
    
    def plot_portfolio_performance(
        self,
        portfolio_history: List[Dict],
        save_path: str = None
    ) -> None:
        """Plot portfolio performance over time.
        
        Args:
            portfolio_history: List of portfolio dictionaries
            save_path: Optional path to save the plot
        """
        # Convert to DataFrame
        df = pd.DataFrame(portfolio_history)
        
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot expected returns
        plt.plot(
            df["basket_date"],
            df["expected_return"] * 100,
            marker="o",
            linestyle="-",
            color="blue"
        )
        
        # Customize plot
        plt.title("Portfolio Expected Monthly Returns")
        plt.xlabel("Date")
        plt.ylabel("Expected Return (%)")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save or show plot
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        else:
            plt.show()
        
        plt.close() 