"""
Tests for the stock research agent.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.agents.stock_research import StockResearchAgent


@pytest.fixture
def mock_stock_data():
    """Mock stock data fixture."""
    return {
        "current_price": 1000.0,
        "52_week_high": 1200.0,
        "52_week_low": 800.0,
        "market_cap": 1000000000000,
        "pe_ratio": 25.5,
        "volume": 1000000,
        "avg_volume": 1200000,
        "price_history": {
            "Close": {0: 990.0, 1: 995.0, 2: 1000.0},
            "Volume": {0: 900000, 1: 950000, 2: 1000000},
        },
    }


@pytest.fixture
def mock_news_data():
    """Mock news data fixture."""
    return [
        {"title": "Test News 1", "url": "http://example.com/1"},
        {"title": "Test News 2", "url": "http://example.com/2"},
    ]


@pytest.mark.asyncio
async def test_analyze_stock(mock_stock_data, mock_news_data):
    """Test stock analysis."""
    with patch(
        "src.agents.stock_research.StockResearchAgent._get_stock_data"
    ) as mock_get_stock, patch(
        "src.agents.stock_research.StockResearchAgent._get_news_data"
    ) as mock_get_news:
        # Setup mocks
        mock_get_stock.return_value = mock_stock_data
        mock_get_news.return_value = mock_news_data

        # Create agent
        agent = StockResearchAgent()

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=str(
                        {
                            "current_price": 1000.0,
                            "forecast_1w": 1020.0,
                            "forecast_1m": 1050.0,
                            "forecast_3m": 1100.0,
                            "forecast_6m": 1150.0,
                            "forecast_12m": 1200.0,
                            "summary": "Test analysis",
                            "confidence": 0.8,
                        }
                    )
                )
            )
        ]

        with patch("openai.chat.completions.create") as mock_openai:
            mock_openai.return_value = mock_response

            # Test analysis
            result = await agent.analyze_stock("RELIANCE")

            # Verify result structure
            assert isinstance(result, dict)
            assert "current_price" in result
            assert "forecast_1w" in result
            assert "forecast_1m" in result
            assert "forecast_3m" in result
            assert "forecast_6m" in result
            assert "forecast_12m" in result
            assert "summary" in result
            assert "confidence" in result

            # Verify values
            assert result["current_price"] == 1000.0
            assert result["forecast_1w"] == 1020.0
            assert result["confidence"] == 0.8
