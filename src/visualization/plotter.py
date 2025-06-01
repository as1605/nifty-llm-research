"""
Visualization module for plotting stock predictions.
"""

from datetime import timedelta
import logging
from typing import List, Dict, Any, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Configure logging
logger = logging.getLogger(__name__)


class StockPlotter:
    """Class for creating stock prediction visualizations."""

    def __init__(self):
        """Initialize the plotter."""
        # Set seaborn theme
        sns.set_theme(style="whitegrid")
        sns.set_palette("husl")

    def _validate_forecast_data(self, forecast: Dict[str, Any]) -> bool:
        """Validate forecast data has required fields.
        
        Args:
            forecast: Forecast dictionary to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = {
            "forecast_date",
            "target_price",
            "gain",
            "days",
            "reason_summary"
        }
        return all(field in forecast for field in required_fields)

    def plot_predictions(
        self, 
        stock_symbol: str, 
        predictions: List[Dict[str, Any]], 
        save_path: Optional[str] = None
    ) -> None:
        """Plot stock price predictions over time.

        Args:
            stock_symbol: The stock symbol
            predictions: List of prediction dictionaries
            save_path: Optional path to save the plot
        """
        if not predictions:
            logger.warning(f"No predictions available for {stock_symbol}")
            return

        # Filter and validate predictions
        valid_predictions = [
            pred for pred in predictions 
            if self._validate_forecast_data(pred)
        ]
        
        if not valid_predictions:
            logger.error(f"No valid predictions found for {stock_symbol}")
            return

        # Convert predictions to DataFrame
        df = pd.DataFrame(valid_predictions)
        
        # Ensure datetime format
        df['forecast_date'] = pd.to_datetime(df['forecast_date'])

        # Create figure
        plt.figure(figsize=(12, 8))

        # Plot each prediction line
        for i, row in df.iterrows():
            # Calculate dates for the prediction line
            dates = [
                row['forecast_date'],
                row['forecast_date'] + timedelta(days=row['days'])
            ]

            # Get current price from the first prediction
            current_price = df.iloc[0]['target_price'] / (1 + df.iloc[0]['gain']/100)
            
            # Calculate prices
            prices = [
                current_price,
                row['target_price']
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
                label=row['forecast_date'].strftime("%Y-%m-%d"),
            )

            # Add gain percentage annotation
            plt.annotate(
                f"{row['gain']:.1f}%",
                xy=(dates[1], prices[1]),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=8,
                color=color
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
            try:
                plt.savefig(save_path, dpi=300, bbox_inches="tight")
                logger.info(f"Saved plot to {save_path}")
            except Exception as e:
                logger.error(f"Failed to save plot to {save_path}: {e}")
        else:
            plt.show()

        plt.close()

    def plot_portfolio_performance(
        self, 
        portfolio_history: List[Dict[str, Any]], 
        save_path: Optional[str] = None
    ) -> None:
        """Plot portfolio performance over time.

        Args:
            portfolio_history: List of portfolio dictionaries
            save_path: Optional path to save the plot
        """
        if not portfolio_history:
            logger.warning("No portfolio history available")
            return

        # Convert to DataFrame
        df = pd.DataFrame(portfolio_history)
        
        # Ensure datetime format
        df['basket_date'] = pd.to_datetime(df['basket_date'])

        # Create figure
        plt.figure(figsize=(12, 6))

        # Plot expected returns
        plt.plot(
            df['basket_date'],
            df['expected_return'] * 100,
            marker="o",
            linestyle="-",
            color="blue",
            label="Expected Return"
        )

        # Add confidence intervals if available
        if 'confidence_interval' in df.columns:
            confidence = df['confidence_interval'].apply(lambda x: x if isinstance(x, (int, float)) else 0)
            plt.fill_between(
                df['basket_date'],
                (df['expected_return'] - confidence) * 100,
                (df['expected_return'] + confidence) * 100,
                alpha=0.2,
                color="blue",
                label="Confidence Interval"
            )

        # Customize plot
        plt.title("Portfolio Expected Monthly Returns")
        plt.xlabel("Date")
        plt.ylabel("Expected Return (%)")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        # Save or show plot
        if save_path:
            try:
                plt.savefig(save_path, dpi=300, bbox_inches="tight")
                logger.info(f"Saved portfolio plot to {save_path}")
            except Exception as e:
                logger.error(f"Failed to save portfolio plot to {save_path}: {e}")
        else:
            plt.show()

        plt.close()
