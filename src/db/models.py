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


class PromptConfig(BaseModel):
    """Model for storing prompt configurations."""

    id: PyObjectId | None = Field(None, alias="_id")
    name: str = Field(..., description="Unique name for the prompt configuration")
    description: str = Field(..., description="Description of what this prompt does")
    system_prompt: str = Field(..., description="System prompt for the model")
    user_prompt: str = Field(..., description="User prompt template")
    params: List[str] = Field(default_factory=list, description="Required parameters for the prompt")
    model: str = Field(default="gemini-pro", description="Model to use")
    config: dict = Field(
        ...,
        description="Configuration settings for the Gemini model"
    )
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
    invocation_id: PyObjectId = None
    forecast_date: datetime
    target_price: float
    gain: float
    days: int
    reason_summary: str
    sources: List[str]
    created_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ListForecast(BaseModel):
    """Model for LLM response containing a list of forecasts."""

    forecasts: List[Forecast] = Field(
        ...,
        description="List of forecasts for different time periods"
    )


class BasketStock(BaseModel):
    """Model for storing stock information in a basket."""
    
    stock_ticker: str = Field(..., description="Stock ticker symbol")
    weight: float = Field(..., description="Weight of this stock in the basket (0-1)")
    sources: List[str] = Field(default_factory=list, description="List of source URLs for this stock")


class Basket(BaseModel):
    """Model for storing portfolio baskets."""
    
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    invocation_id: PyObjectId = None
    stocks_ticker_candidates: List[str] = Field(
        ..., description="List of stock tickers considered for the basket"
    )
    stocks: List[BasketStock] = Field(
        ..., description="List of selected stocks with their weights and sources"
    )
    reason_summary: str = Field(..., description="Summary of why these stocks were picked")
    expected_gain_1w: Optional[float] = Field(None, description="Expected gain for the basket in 1 week")


class ZerodhaToken(BaseModel):
    """Model for storing encrypted Zerodha access tokens."""
    
    id: PyObjectId | None = Field(None, alias="_id")
    user_id: str = Field(..., description="Zerodha user ID")
    encrypted_access_token: str = Field(..., description="Encrypted access token")
    created_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    is_active: bool = Field(default=True, description="Whether token is currently active")
