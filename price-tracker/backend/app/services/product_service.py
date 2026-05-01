from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.product import Product, PriceHistory
from app.scraper.factory import get_scraper, detect_platform
from app.services.notifications import check_and_notify
import logging

logger = logging.getLogger(__name__)


async def add_product(db: Session, url: str, target_price: Optional[float] = None, user_id: int = None) -> Product:
    """
    Add a new product to track. Immediately scrapes the URL for initial data.
    """
    # Check if already tracked by this user
    existing = db.query(Product).filter(Product.url == url, Product.user_id == user_id).first()
    if existing:
        raise ValueError(f"This product is already being tracked (ID: {existing.id})")

    platform = detect_platform(url)
    if platform == "unknown":
        raise ValueError("Unsupported URL. Supported: Amazon, Flipkart, Blinkit, Zepto.")

    # Scrape initial data
    scraper = get_scraper(url)
    try:
        scraped = await scraper.scrape(url)
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        raise ValueError(f"Failed to scrape product: {e}")

    # Create product record
    product = Product(
        url=url,
        name=scraped.name or "Unknown Product",
        image_url=scraped.image_url,
        platform=platform,
        current_price=scraped.price,
        lowest_price=scraped.price,
        highest_price=scraped.price,
        target_price=target_price,
        currency=scraped.currency,
        is_available=scraped.is_available,
        user_id=user_id,
    )
    db.add(product)
    db.flush()  # Get the product ID

    # Record initial price history
    if scraped.price:
        history_entry = PriceHistory(
            product_id=product.id,
            price=scraped.price,
        )
        db.add(history_entry)

    db.commit()
    db.refresh(product)
    logger.info(f"Added product: {product.name} at {product.current_price}")
    return product


def get_all_products(db: Session, user_id: int = None) -> list[Product]:
    """Get all tracked products for a user, most recent first."""
    query = db.query(Product)
    if user_id:
        query = query.filter(Product.user_id == user_id)
    return query.order_by(Product.updated_at.desc()).all()


def get_product_by_id(db: Session, product_id: int, user_id: int = None) -> Optional[Product]:
    """Get a single product, optionally scoped to a user."""
    query = db.query(Product).filter(Product.id == product_id)
    if user_id:
        query = query.filter(Product.user_id == user_id)
    return query.first()


def get_price_history(db: Session, product_id: int, limit: int = 100) -> list[PriceHistory]:
    """Get price history for a product, oldest first."""
    return (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.asc())
        .limit(limit)
        .all()
    )


def delete_product(db: Session, product_id: int, user_id: int = None) -> bool:
    """Delete a product and all its price history."""
    query = db.query(Product).filter(Product.id == product_id)
    if user_id:
        query = query.filter(Product.user_id == user_id)
    product = query.first()
    if not product:
        return False
    db.delete(product)
    db.commit()
    logger.info(f"Deleted product ID {product_id}")
    return True


async def refresh_price(db: Session, product_id: int, user_id: int = None) -> Optional[Product]:
    """
    Re-scrape the product page and update the price.
    Records a new price history entry if the price changed.
    Triggers notifications if price drops.
    """
    query = db.query(Product).filter(Product.id == product_id)
    if user_id:
        query = query.filter(Product.user_id == user_id)
    product = query.first()
    if not product:
        return None

    try:
        scraper = get_scraper(product.url)
        scraped = await scraper.scrape(product.url)
    except Exception as e:
        logger.error(f"Failed to scrape product {product_id}: {e}")
        return product

    old_price = product.current_price

    # Update availability
    product.is_available = scraped.is_available

    if scraped.price and scraped.price > 0:
        # Update current price
        product.current_price = scraped.price
        product.updated_at = datetime.utcnow()

        # Update name/image if they were missing
        if scraped.name and (not product.name or product.name == "Unknown Product"):
            product.name = scraped.name
        if scraped.image_url and not product.image_url:
            product.image_url = scraped.image_url

        # Update min/max
        if product.lowest_price is None or scraped.price < product.lowest_price:
            product.lowest_price = scraped.price
        if product.highest_price is None or scraped.price > product.highest_price:
            product.highest_price = scraped.price

        # Record history
        history_entry = PriceHistory(
            product_id=product.id,
            price=scraped.price,
        )
        db.add(history_entry)
        db.commit()
        db.refresh(product)
        logger.info(f"Refreshed product {product.id}: {product.name} → ₹{scraped.price}")

        # Check for notifications
        await check_and_notify(product, old_price, scraped.price)
    else:
        logger.warning(f"No price found during refresh for product {product_id}")

    return product


async def refresh_all_prices(db: Session):
    """Refresh prices for all tracked products."""
    products = db.query(Product).all()
    logger.info(f"Starting scheduled refresh for {len(products)} products")

    for product in products:
        try:
            await refresh_price(db, product.id)
        except Exception as e:
            logger.error(f"Error refreshing product {product.id}: {e}")

    logger.info("Scheduled refresh complete")
