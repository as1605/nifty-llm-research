"""
Database models for the Nifty Stock Research project using MongoDB.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


class PyObjectId(ObjectId):
    """Custom type for handling MongoDB ObjectId fields."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetJsonSchemaHandler,
    ) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x),
                return_schema=core_schema.str_schema(),
                when_used='json',
            ),
        )

    @classmethod
    def validate(cls, v: str) -> ObjectId:
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class OrderType(str, Enum):
    """Types of trade orders."""

    BUY = "buy"
    SELL = "sell"


class PromptConfig(BaseModel):
    """Model for storing prompt configurations."""

    id: PyObjectId | None = Field(None, alias="_id")
    name: str = Field(..., description="Unique name for the prompt configuration")
    description: str = Field(..., description="Description of what this prompt does")
    system_prompt: str = Field(..., description="System prompt for the model")
    user_prompt: str = Field(..., description="User prompt template")
    params: List[str] = Field(default_factory=list, description="Required parameters for the prompt")
    model: str = Field(default="gemini-pro", description="Model to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    tools: List[str] = Field(default_factory=list, description="Tools to enable")
    default: bool = Field(default=False, description="Whether this is the default config")
    created_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Invocation(BaseModel):
    """Model for storing LLM invocations."""

    prompt_config_id: PyObjectId
    params: dict
    response: str
    invocation_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_time: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class Stock(BaseModel):
    """Model for storing stock information."""

    ticker: str
    name: str
    price: float
    industry: str
    indices: List[str]
    modified_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Forecast(BaseModel):
    """Model for storing stock price forecasts."""

    stock_ticker: str
    forecast_date: datetime
    target_price: float
    gain: float
    days: int
    reason_summary: str
    sources: List[str]
    created_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Basket(BaseModel):
    """Model for storing portfolio baskets."""

    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stocks_ticker_candidates: List[str] = Field(
        ..., description="List of stock tickers considered for the basket"
    )
    stocks_picked: List[str] = Field(..., description="List of selected stock tickers")
    weights: dict[str, float] = Field(
        ..., description="Dictionary mapping stock tickers to their weights (summing to 1)"
    )
    reason_summary: str
    expected_gain_1m: float


class Order(BaseModel):
    """Model for storing trade orders."""

    stock_ticker: str
    type: OrderType
    price: float
    is_market_order: bool
    placed_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_time: Optional[datetime] = None
    status: str = Field(default="pending")
    demat_account: str
    quantity: int
    metadata: dict = Field(default_factory=dict)
