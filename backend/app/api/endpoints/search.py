from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ...core.database import get_db
from ...models.listing import Listing
from ...services.realtor_service import fetch_realtor_listings

router = APIRouter()


@router.get("/search")
async def search_listings(
    city: Optional[str] = Query(None, description="City to search in"),
    state_code: Optional[str] = Query(None, description="2-letter state code (required for API search)"),
    bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    use_api: bool = Query(True, description="Use Realtor API (True) or local DB (False)"),
    db: Session = Depends(get_db)
):
    """
    Search for listings based on criteria.
    Can search via Realtor API or local database.
    """

    if use_api:
        if not city or not state_code:
            raise HTTPException(status_code=400, detail="City and state_code are required for API search")

        try:
            api_listings = await fetch_realtor_listings(
                city=city,
                state_code=state_code,
                bedrooms=bedrooms if bedrooms else None,
                max_price=max_price if max_price else None
            )

            return {
                "listings": api_listings,
                "count": len(api_listings),
                "source": "Realtor API",
                "filters": {
                    "city": city,
                    "state_code": state_code,
                    "bedrooms": bedrooms,
                    "max_price": max_price
                }
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"API search failed: {str(e)}"
            )

    else:
        # Database-based search (original functionality)
        query = db.query(Listing)

        if city:
            query = query.filter(Listing.city.ilike(f"%{city}%"))

        if bedrooms:
            query = query.filter(Listing.bedrooms == bedrooms)

        if max_price:
            query = query.filter(Listing.price <= max_price)

        listings = query.limit(10).all()

        return {
            "listings": listings,
            "count": len(listings),
            "source": "Local Database",
            "filters": {
                "city": city,
                "bedrooms": bedrooms,
                "max_price": max_price
            }
        }
