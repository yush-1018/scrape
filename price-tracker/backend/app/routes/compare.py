"""
Compare routes — find similar products across platforms for price comparison.
"""

import logging
from difflib import SequenceMatcher
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.product import Product, User
from app.utils.auth_utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compare", tags=["compare"])


def similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio (0–1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalize_name(name: str) -> str:
    """Normalize product name for comparison by removing common noise words."""
    noise = {"the", "a", "an", "for", "with", "and", "or", "in", "of", "by", "from", "|", "-", "–", "—"}
    words = name.lower().split()
    return " ".join(w for w in words if w not in noise)


@router.get("/")
def compare_products(
    query: str = Query(default="", description="Product name to search for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Find similar products across platforms for price comparison.
    Groups user's tracked products by name similarity.
    """
    products = db.query(Product).filter(Product.user_id == current_user.id).all()

    if not products:
        return {"groups": []}

    # If query is provided, filter to matching products first
    if query:
        query_normalized = normalize_name(query)
        matching = [
            p for p in products
            if similarity(normalize_name(p.name or ""), query_normalized) > 0.4
            or query.lower() in (p.name or "").lower()
        ]
    else:
        matching = products

    # Group similar products together
    groups = []
    used = set()

    for i, p1 in enumerate(matching):
        if p1.id in used:
            continue

        group = {
            "name": p1.name or "Unknown Product",
            "products": [_product_to_dict(p1)],
        }
        used.add(p1.id)

        for j, p2 in enumerate(matching):
            if p2.id in used:
                continue
            # Group if names are >50% similar
            if similarity(normalize_name(p1.name or ""), normalize_name(p2.name or "")) > 0.5:
                group["products"].append(_product_to_dict(p2))
                used.add(p2.id)

        # Calculate group stats
        prices = [p["current_price"] for p in group["products"] if p["current_price"]]
        group["cheapest"] = min(prices) if prices else None
        group["most_expensive"] = max(prices) if prices else None
        group["platforms"] = list(set(p["platform"] for p in group["products"]))

        # Mark the cheapest product
        for p in group["products"]:
            p["is_cheapest"] = (p["current_price"] == group["cheapest"]) if p["current_price"] else False

        groups.append(group)

    # Sort groups by number of platforms (most comparable first)
    groups.sort(key=lambda g: len(g["platforms"]), reverse=True)

    return {"groups": groups}


def _product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "platform": product.platform,
        "current_price": product.current_price,
        "lowest_price": product.lowest_price,
        "highest_price": product.highest_price,
        "target_price": product.target_price,
        "is_available": product.is_available,
        "image_url": product.image_url,
        "url": product.url,
        "updated_at": product.updated_at.isoformat() if product.updated_at else "",
    }
