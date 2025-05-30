"""
Database models for the Nifty Stock Research project using MongoDB.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class OrderType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class PromptConfig(BaseModel):
    """Model for storing prompt configurations."""
    name: str = Field(..., description="Short code to identify the prompt")
    system_prompt: str = Field(..., description="The system prompt text")
    user_prompt: str = Field(..., description="The user prompt template")
    params: List[str] = Field(default_factory=list, description="List of parameter keys to be replaced in the prompt")
    model: str = Field(..., description="The OpenAI model name")
    tools: List[str] = Field(default_factory=list, description="Tools allowed to use")
    default: bool = Field(default=False, description="If this will be used by default")
    created_time: datetime = Field(default_factory=datetime.utcnow)
    modified_time: datetime = Field(default_factory=datetime.utcnow)


class Invocation(BaseModel):
    """Model for storing LLM invocations."""
    invocation_time: datetime = Field(default_factory=datetime.utcnow)
    result_time: Optional[datetime] = None
    prompt_config_id: ObjectId
    params: Dict[str, str] = Field(default_factory=dict, description="Mapping of parameter keys to their values")
    response: str
    metadata: Dict = Field(default_factory=dict)


class Stock(BaseModel):
    """Model for storing stock information."""
    ticker: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., description="Current stock price")
    modified_time: datetime = Field(default_factory=datetime.utcnow)
    market_cap: float = Field(..., description="Market capitalization in USD")
    industry: str = Field(..., description="Industry sector")


class Forecast(BaseModel):
    """Model for storing stock price forecasts."""
    stock_ticker: str = Field(..., description="Stock ticker symbol")
    created_time: datetime = Field(default_factory=datetime.utcnow)
    invocation_id: ObjectId
    forecast_date: datetime
    target_price: float
    gain: float = Field(..., description="Percentage gain")
    days: int = Field(..., description="Number of days for the forecast")
    reason_summary: str
    sources: List[str] = Field(default_factory=list)


class Basket(BaseModel):
    """Model for storing stock basket recommendations."""
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    stocks_ticker_candidates: List[str] = Field(default_factory=list)
    stocks_picked: List[str] = Field(default_factory=list)
    weights: Dict[str, float] = Field(..., description="Stock ticker vs their ratio, all summing to 1")
    reason_summary: str
    expected_gain_1w: float


class Email(BaseModel):
    """Model for storing email records."""
    created_time: datetime = Field(default_factory=datetime.utcnow)
    sent_time: Optional[datetime] = None
    service: str = Field(default="amazon-ses")
    type: str = Field(..., description="account related/generic alert/basket update")
    status: str
    subject: str
    content_html: str
    from_: str = Field(..., alias="from")
    to: List[str]
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)


class Order(BaseModel):
    """Model for storing trade orders."""
    stock_ticker: str
    type: OrderType
    price: float
    is_market_order: bool = Field(..., alias="isMarketOrder")
    placed_time: datetime = Field(default_factory=datetime.utcnow)
    executed_time: Optional[datetime] = None
    demat_account: str 