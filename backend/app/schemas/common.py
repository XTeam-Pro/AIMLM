from pydantic import BaseModel, field_validator, ConfigDict, Field
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.schemas.types.common_types import ProductCategory, TransactionType, TransactionStatus


class Message(BaseModel):
    message: str = Field(..., max_length=100)

# Models:
class ProductBase(BaseModel):
    title: str
    description: str
    category: ProductCategory
    price: float
    pv_value: float
    webinar_link: Optional[str]
    @field_validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @field_validator('webinar_link')
    def validate_webinar_link(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Webinar link must start with http:// or https://')
        return v


class ProductCreate(ProductBase):
    image_url: Optional[str]
    is_active: bool
    webinar_link: Optional[str]
    is_collection: bool
    collection_items: Optional[List[Dict[str, Any]]]


class ProductUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    category: Optional[ProductCategory]
    price: Optional[Decimal]
    pv_value: Optional[float]
    image_url: Optional[str]
    is_active: Optional[bool]
    webinar_link: Optional[str]
    is_collection: Optional[bool]
    collection_items: Optional[List[Dict[str, Any]]]


class ProductPublic(ProductBase):
    id: uuid.UUID
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    cash_amount: Decimal
    pv_amount: Decimal
    type: TransactionType
    additional_info: Optional[Dict[str, Any]]


class TransactionCreate(TransactionBase):
    product_id: Optional[uuid.UUID]
    status: TransactionStatus
    achievement_id: Optional[uuid.UUID]
    buyer_id: uuid.UUID
    seller_id: uuid.UUID


class TransactionUpdate(BaseModel):
    cash_amount: Decimal
    pv_amount: Optional[float]
    type: Optional[TransactionType]
    status: Optional[TransactionStatus]
    additional_info: Optional[Dict[str, Any]]


class TransactionPublic(TransactionBase):
    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID
    product_id: Optional[uuid.UUID]
    achievement_id: Optional[uuid.UUID]
    model_config = ConfigDict(from_attributes=True)

class UserProductInteractionBase(BaseModel):
    interaction_type: str
    interaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    achievement_id: Optional[uuid.UUID] = Field(default=None)
    additional_info: Optional[Dict[str, Any]] = Field(default=None)

# Схема для создания нового UserProductInteraction
class UserProductInteractionCreate(UserProductInteractionBase):
    user_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)

# Схема для отображения UserProductInteraction
class UserProductInteractionPublic(UserProductInteractionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: Optional[uuid.UUID]
    achievement_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)


class CartItemBase(BaseModel):
    quantity: int = Field(default=1, ge=1)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CartItemCreate(CartItemBase):
    user_id: uuid.UUID
    product_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class CartItemPublic(CartItemBase):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

