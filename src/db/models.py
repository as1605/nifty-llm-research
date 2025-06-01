"""
Database models for the Nifty Stock Research project using MongoDB.
"""

from datetime import datetime
from enum import Enum
from typing import Any

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
    BUY = "buy"
    SELL = "sell"


class BaseMongoModel(BaseModel):
    """Base model with MongoDB configuration."""
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat(),
        },
    }


class PromptConfig(BaseMongoModel):
    """Model for storing prompt configurations."""

    id: PyObjectId | None = Field(None, alias="_id")
    name: str = Field(..., description="Short code to identify the prompt")
    description: str = Field(..., description="Detailed description of what this prompt is used for")
    system_prompt: str = Field(..., description="The system prompt text")
    user_prompt: str = Field(..., description="The user prompt template")
    params: list[str] = Field(
        default_factory=list,
        description="List of parameter keys to be replaced in the prompt",
    )
    model: str = Field(..., description="The OpenAI model name")
    temperature: float = Field(
        default=0.7,
        description="Controls randomness in responses (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    tools: list[str] = Field(default_factory=list, description="Tools allowed to use")
    default: bool = Field(default=False, description="If this will be used by default")
    created_time: datetime = Field(default_factory=datetime.utcnow)
    modified_time: datetime = Field(default_factory=datetime.utcnow)


class Invocation(BaseMongoModel):
    """Model for storing LLM invocations."""

    invocation_time: datetime = Field(default_factory=datetime.utcnow)
    result_time: datetime | None = None
    prompt_config_id: PyObjectId
    params: dict[str, str] = Field(
        default_factory=dict, description="Mapping of parameter keys to their values"
    )
    response: str
    metadata: dict = Field(default_factory=dict)


class Stock(BaseMongoModel):
    """Model for storing stock information."""

    ticker: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., description="Current stock price")
    modified_time: datetime = Field(default_factory=datetime.utcnow)
    market_cap: float = Field(..., description="Market capitalization in USD")
    industry: str = Field(..., description="Industry sector")


class Forecast(BaseMongoModel):
    """Model for storing stock price forecasts."""

    stock_ticker: str = Field(..., description="Stock ticker symbol")
    created_time: datetime = Field(default_factory=datetime.utcnow)
    invocation_id: PyObjectId
    forecast_date: datetime
    target_price: float
    gain: float = Field(..., description="Percentage gain")
    days: int = Field(..., description="Number of days for the forecast")
    reason_summary: str
    sources: list[str] = Field(default_factory=list)


class Basket(BaseMongoModel):
    """Model for storing stock basket recommendations."""

    creation_date: datetime = Field(default_factory=datetime.utcnow)
    stocks_ticker_candidates: list[str] = Field(default_factory=list)
    stocks_picked: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(
        ..., description="Stock ticker vs their ratio, all summing to 1"
    )
    reason_summary: str
    expected_gain_1w: float


class Email(BaseMongoModel):
    """Model for storing email records."""

    created_time: datetime = Field(default_factory=datetime.utcnow)
    sent_time: datetime | None = None
    service: str = Field(default="amazon-ses")
    type: str = Field(..., description="account related/generic alert/basket update")
    status: str
    subject: str
    content_html: str
    from_: str = Field(..., alias="from")
    to: list[str]
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)


class Order(BaseMongoModel):
    """Model for storing trade orders."""

    stock_ticker: str
    type: OrderType
    price: float
    is_market_order: bool = Field(..., alias="isMarketOrder")
    placed_time: datetime = Field(default_factory=datetime.utcnow)
    executed_time: datetime | None = None
    demat_account: str
