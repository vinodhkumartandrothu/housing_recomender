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
    max_price: Optional[float] = Query(None, description="Maximum price (monthly rent for rentals, sale price for purchases)"),
    search_type: str = Query("rent", description="Search type: 'rent' for rentals or 'buy' for purchases"),
    property_type: Optional[str] = Query(None, description="Property type (apartment, house, condo, townhouse)"),
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
                bedrooms=bedrooms,
                max_price=max_price,
                search_type=search_type,
                property_type=property_type
            )

            return {
                "listings": api_listings,
                "count": len(api_listings),
                "source": "Realtor API",
                "filters": {
                    "city": city,
                    "state_code": state_code,
                    "bedrooms": bedrooms,
                    "max_price": max_price,
                    "search_type": search_type,
                    "property_type": property_type,
                }
            }

        except Exception as e:
            print(f"API search error: {str(e)}")  # Debug logging
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
            "listings": [
                {
                    "id": listing.id,
                    "title": listing.title,
                    "description": listing.description,
                    "price": listing.price,
                    "bedrooms": listing.bedrooms,
                    "bathrooms": listing.bathrooms,
                    "square_feet": listing.square_feet,
                    "city": listing.city,
                    "state": listing.state,
                    "url": listing.source_url,
                } for listing in listings
            ],
            "count": len(listings),
            "source": "Local Database",
            "filters": {
                "city": city,
                "bedrooms": bedrooms,
                "max_price": max_price
            }
        }



# from fastapi import APIRouter, Depends, Query, HTTPException
# from sqlalchemy.orm import Session
# from typing import Optional
# from ...core.database import get_db
# from ...models.listing import Listing
# from ...services.realtor_service import fetch_realtor_listings
# from enum import Enum 

# router = APIRouter()

# class PropertyType(str, Enum):
#     apartment = "apartment"
#     house = "house"
#     condo = "condo"
#     townhouse = "townhouse"


# @router.get("/search")
# async def search_listings(
#     city: Optional[str] = Query(None, description="City to search in"),
#     state_code: Optional[str] = Query(None, description="2-letter state code (required for API search)"),
#     bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
#     max_price: Optional[float] = Query(None, description="Maximum price"),
#     property_type: Optional[str] = Query(None, description="Property type (apartment, house, condo, townhouse)"), 
#     use_api: bool = Query(True, description="Use Realtor API (True) or local DB (False)"),
#     db: Session = Depends(get_db)
# ):
#     """
#     Search for listings based on criteria.
#     Can search via Realtor API or local database.
#     """

#     if use_api:
#         if not city or not state_code:
#             raise HTTPException(status_code=400, detail="City and state_code are required for API search")

#         try:
#             api_listings = await fetch_realtor_listings(
#                 city=city,
#                 state_code=state_code,
#                 bedrooms=bedrooms if bedrooms else None,
#                 max_price=max_price if max_price else None,
#                 property_type=property_type.value if property_type else None
#             )

#             return {
#                 "listings": api_listings,
#                 "count": len(api_listings),
#                 "source": "Realtor API",
#                 "filters": {
#                     "city": city,
#                     "state_code": state_code,
#                     "bedrooms": bedrooms,
#                     "max_price": max_price,
#                     "property_type":property_type,
#                 }
#             }

#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"API search failed: {str(e)}"
#             )

#     else:
#         # Database-based search (original functionality)
#         query = db.query(Listing)

#         if city:
#             query = query.filter(Listing.city.ilike(f"%{city}%"))

#         if bedrooms:
#             query = query.filter(Listing.bedrooms == bedrooms)

#         if max_price:
#             query = query.filter(Listing.price <= max_price)

#         listings = query.limit(10).all()

#         return {
#             "listings": listings,
#             "count": len(listings),
#             "source": "Local Database",
#             "filters": {
#                 "city": city,
#                 "bedrooms": bedrooms,
#                 "max_price": max_price
#             }
#         }



