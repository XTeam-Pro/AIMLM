import uuid
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timezone


# ======== User Models ======== #
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    full_name: str | None = Field(default=None, max_length=255)

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)

class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)

class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)
    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(default=None)
    full_name: str | None = Field(default=None, max_length=255)

class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)

class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

class User(UserBase, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="user")

class UserPublic(UserBase):
    id: uuid.UUID

class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

# ======== Product Models ======== #
class ProductBase(SQLModel):
    title: str | None = Field(min_length=1, max_length=255, default=None)
    description: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    popularity: int | None = Field(default=0)
    price: float | None = Field(default=None, gt=0.0)
    rating: float | None = Field(default=None, gt=0.0, le=5)

class Product(ProductBase, table=True):
    __tablename__ = "products"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    items: list["Item"] = Relationship(back_populates="product")


class ProductUpdate(SQLModel):
    title: str | None = Field(min_length=1, max_length=255, default=None)
    description: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, gt=0.0)
    rating: float | None = Field(default=None, gt=0.0, le=5)

class ProductCreate(ProductBase):
    pass

class ProductPublic(ProductBase):
    id: uuid.UUID

# ======== Item Models (User-Product Interactions) ======== #
class ItemBase(SQLModel):
    interaction_type: str = Field(default="PURCHASE")  # PURCHASE, CART, FAVORITE, etc.
    quantity: int = Field(default=1, gt=0)
    interaction_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class ItemCreate(ItemBase):
    product_id: uuid.UUID

class ItemUpdate(SQLModel):
    interaction_type: str | None = Field(default=None, min_length=1, max_length=50)
    quantity: int | None = Field(default=None, gt=0)

class Item(ItemBase, table=True):
    __tablename__ = "items"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    category: str | None = Field(default=None, max_length=255)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    product_id: uuid.UUID = Field(foreign_key="products.id")
    user: User = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="items")

class ItemPublic(ItemBase):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    product: ProductPublic

class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int

# ======== Other Models ======== #
class Message(SQLModel):
    message: str

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(SQLModel):
    sub: str | None = None

class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)