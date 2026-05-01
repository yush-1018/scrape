from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.database import Base


class User(Base):
    """A registered user of the price tracker."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(100), nullable=True)  # Per-user Telegram alerts
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to products
    products = relationship("Product", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Product(Base):
    """A product being tracked for price changes."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(Text, nullable=False)
    name = Column(String(500), nullable=True)
    image_url = Column(Text, nullable=True)
    platform = Column(String(50), nullable=False)  # "amazon", "flipkart", "blinkit", "zepto"
    current_price = Column(Float, nullable=True)
    lowest_price = Column(Float, nullable=True)
    highest_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    currency = Column(String(10), default="₹")
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="products")
    price_history = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan",
        order_by="PriceHistory.recorded_at.desc()"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.current_price})>"


class PriceHistory(Base):
    """A single price data point for a tracked product."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to product
    product = relationship("Product", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, at={self.recorded_at})>"
