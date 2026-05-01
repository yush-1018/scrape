from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.product import User
from app.services import product_service
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])


# ── Request / Response Schemas ──────────────────────────────────────────

class AddProductRequest(BaseModel):
    url: str
    target_price: Optional[float] = None


class ProductResponse(BaseModel):
    id: int
    url: str
    name: Optional[str]
    image_url: Optional[str]
    platform: str
    current_price: Optional[float]
    lowest_price: Optional[float]
    highest_price: Optional[float]
    target_price: Optional[float]
    currency: str
    is_available: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    price: float
    recorded_at: str

    class Config:
        from_attributes = True


class ProductDetailResponse(BaseModel):
    product: ProductResponse
    price_history: list[PriceHistoryResponse]


class MessageResponse(BaseModel):
    message: str


# ── Helper ──────────────────────────────────────────────────────────────

def product_to_response(product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        url=product.url,
        name=product.name,
        image_url=product.image_url,
        platform=product.platform,
        current_price=product.current_price,
        lowest_price=product.lowest_price,
        highest_price=product.highest_price,
        target_price=product.target_price,
        currency=product.currency,
        is_available=product.is_available,
        created_at=product.created_at.isoformat() if product.created_at else "",
        updated_at=product.updated_at.isoformat() if product.updated_at else "",
    )


def history_to_response(entry) -> PriceHistoryResponse:
    return PriceHistoryResponse(
        id=entry.id,
        product_id=entry.product_id,
        price=entry.price,
        recorded_at=entry.recorded_at.isoformat() if entry.recorded_at else "",
    )


# ── Endpoints ───────────────────────────────────────────────────────────

@router.post("/", response_model=ProductResponse, status_code=201)
async def add_product(
    body: AddProductRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new product URL to track. Immediately scrapes for initial data."""
    try:
        product = await product_service.add_product(db, str(body.url), body.target_price, user_id=current_user.id)
        return product_to_response(product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape product: {str(e)}")


@router.get("/", response_model=list[ProductResponse])
def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tracked products for the current user."""
    products = product_service.get_all_products(db, user_id=current_user.id)
    return [product_to_response(p) for p in products]


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a product with its full price history."""
    product = product_service.get_product_by_id(db, product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    history = product_service.get_price_history(db, product_id)

    return ProductDetailResponse(
        product=product_to_response(product),
        price_history=[history_to_response(h) for h in history],
    )


@router.delete("/{product_id}", response_model=MessageResponse)
def remove_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stop tracking a product and delete its history."""
    deleted = product_service.delete_product(db, product_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return MessageResponse(message="Product deleted successfully")


@router.post("/{product_id}/refresh", response_model=ProductResponse)
async def refresh_product_price(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger a price refresh for a specific product."""
    product = await product_service.refresh_price(db, product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_response(product)


@router.get("/{product_id}/export")
def export_price_history(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export price history as CSV data."""
    product = product_service.get_product_by_id(db, product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    history = product_service.get_price_history(db, product_id)

    # Build CSV
    lines = ["Date,Price"]
    for entry in history:
        date_str = entry.recorded_at.isoformat() if entry.recorded_at else ""
        lines.append(f"{date_str},{entry.price}")

    from fastapi.responses import Response
    csv_content = "\n".join(lines)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{product.name or "product"}_{product_id}_price_history.csv"'
        },
    )
