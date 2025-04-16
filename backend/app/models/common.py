import uuid
from datetime import timezone, datetime
from decimal import Decimal
from typing import Optional, Any, TYPE_CHECKING

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Relationship

from app.models.gamification import Achievement
if TYPE_CHECKING:
    from app.models.user import User
from app.schemas.types.common_types import TransactionStatus


class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=100)
    description: str = Field(max_length=2000)
    category: str
    price: Decimal = Field(max_digits=12, decimal_places=2, ge=0)
    pv_value: Decimal = Field(default=Decimal(0), max_digits=12, decimal_places=2, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    webinar_link: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    is_collection: bool = Field(default=False)
    collection_items: Optional[list[dict[str, Any]]] = Field(default=None, sa_type=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    interactions: list["UserProductInteraction"] = Relationship(back_populates="product")

class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    product_id: uuid.UUID = Field(foreign_key="products.id")
    quantity: int = Field(default=1, ge=1)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="cart_items")
    product: "Product" = Relationship()

class UserProductInteraction(SQLModel, table=True):
    __tablename__ = "user_product_interactions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    product_id: Optional[uuid.UUID] = Field(default=None, foreign_key="products.id")
    interaction_type: str
    pv_awarded: Decimal = Field(default=Decimal(0), max_digits=12, decimal_places=2, ge=0)
    interaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    achievement_id: Optional[uuid.UUID] = Field(default=None, foreign_key="achievements.id")
    additional_info: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)

    user: "User" = Relationship(back_populates="interactions")
    product: Optional["Product"] = Relationship(back_populates="interactions")
    achievement: Optional["Achievement"] = Relationship()


class PurchaseItem(SQLModel, table=True):
    __tablename__ = "purchase_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign keys to the Purchase and Product tables
    purchase_id: uuid.UUID = Field(foreign_key="purchases.id")
    product_id: uuid.UUID = Field(foreign_key="products.id")

    # Fields specific to the purchased item
    quantity: int = Field(..., ge=1)  # Ensure that the quantity is greater than or equal to 1
    unit_price: Decimal = Field(..., max_digits=12, decimal_places=2)  # Unit price of the product
    pv_value: Decimal = Field(..., max_digits=12, decimal_places=2)  # Personal Volume value associated with the product

    # Relationships
    purchase: "Purchase" = Relationship(back_populates="items")
    product: "Product" = Relationship()

    # Optionally, you can add extra fields like 'total_price' for better readability if necessary
    # Logic to automatically calculate total price
    @property
    def total_price(self):
        return self.unit_price * self.quantity

class Purchase(SQLModel, table=True):
    __tablename__ = "purchases"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    is_starter: bool = Field(default=False)
    purchase_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    pv_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    currency: str = Field(...,)
    is_client_purchase: bool = Field(default=False)

    # Optional reference to a client if needed, otherwise it could be omitted if purchases are always for a user
    client_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")

    # Link to Transaction for financial details
    transaction_id: Optional[uuid.UUID] = Field(default=None, foreign_key="transactions.id")  # Link to Transaction

    # Relationships
    user: "User" = Relationship(
        back_populates="purchases",
        sa_relationship_kwargs={"foreign_keys": "[Purchase.user_id]"}
    )
    client: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Purchase.client_id]"}
    ) # Optional, for when purchases are made by a client
    transaction: Optional["Transaction"] = Relationship()  # Link to the associated transaction
    items: list["PurchaseItem"] = Relationship(back_populates="purchase")

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # User relationships
    buyer_id: uuid.UUID = Field(foreign_key="users.id")
    seller_id: uuid.UUID = Field(foreign_key="users.id")

    # Amount fields
    cash_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    pv_amount: Decimal = Field(..., max_digits=12, decimal_places=2)

    # Transaction details
    type: str = Field(...,)
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)

    # Optional references to product and achievement
    product_id: Optional[uuid.UUID] = Field(default=None, foreign_key="products.id")
    achievement_id: Optional[uuid.UUID] = Field(default=None, foreign_key="achievements.id")

    # Timestamp and additional info
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    additional_info: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)

    # Relationships
    buyer: "User" = Relationship(
        back_populates="buyer_transactions",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.buyer_id]"}
    )

    seller: "User" = Relationship(
        back_populates="seller_transactions",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.seller_id]"}
    )
    product: Optional["Product"] = Relationship()
    achievement: Optional["Achievement"] = Relationship()
