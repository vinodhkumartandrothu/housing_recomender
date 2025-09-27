from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ...core.database import get_db
from ...models.listing import Listing
from ...services.realtor_service import fetch_realtor_listings

# router = APIRouter()

# @router.get("/search")
router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
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

            # 🔹 NEW: Ensure full address is included for each listing
            

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

            # Return mock data for testing when API fails
            mock_listings = [
                {
                    "id": 1,
                    "title": f"Beautiful {bedrooms or 2}BR/{bedrooms or 2}BA Apartment in {city}",
                    "price": max_price - 200 if max_price else 2000,
                    "bedrooms": bedrooms or 2,
                    "bathrooms": 2.0,
                    "square_feet": 1200,
                    "city": city,
                    "state": state_code,
                    "description": f"Modern apartment located in the heart of {city}. Features updated appliances and great amenities.",
                    "photo_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop&auto=format&q=80",
                    "url": "https://example.com/property/1",
                    # 🔹 NEW: Mock full address
                    "full_address": f"123 Main St, {city}, {state_code}"
                },
                {
                    "id": 2,
                    "title": f"Spacious {(bedrooms or 2) + 1}BR/{(bedrooms or 2) + 1}BA House in {city}",
                    "price": (max_price + 500) if max_price else 2800,
                    "bedrooms": (bedrooms or 2) + 1,
                    "bathrooms": 2.5,
                    "square_feet": 1800,
                    "city": city,
                    "state": state_code,
                    "description": f"Charming house with a yard in {city}. Perfect for families looking for space and comfort.",
                    "photo_url": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&h=300&fit=crop&auto=format&q=80",
                    "url": "https://example.com/property/2",
                    "full_address": f"456 Oak St, {city}, {state_code}"
                },
                {
                    "id": 3,
                    "title": f"Cozy {bedrooms or 1}BR/{bedrooms or 1}BA Condo in {city}",
                    "price": (max_price - 400) if max_price else 1600,
                    "bedrooms": bedrooms or 1,
                    "bathrooms": 1.0,
                    "square_feet": 900,
                    "city": city,
                    "state": state_code,
                    "description": f"Affordable condo in {city} with great access to downtown and public transportation.",
                    "photo_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400&h=300&fit=crop&auto=format&q=80",
                    "url": "https://example.com/property/3",
                    "full_address": f"789 Pine St, {city}, {state_code}"
                }
            ]

            return {
                "listings": mock_listings,
                "count": len(mock_listings),
                "source": "Mock Data (API unavailable)",
                "filters": {
                    "city": city,
                    "state_code": state_code,
                    "bedrooms": bedrooms,
                    "max_price": max_price,
                    "search_type": search_type,
                    "property_type": property_type,
                }
            }

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
                    # 🔹 NEW: Build address from DB fields
                    "full_address": f"{listing.title}, {listing.city}, {listing.state}"
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

# router = APIRouter()

# @router.get("/search")
# async def search_listings(
#     city: Optional[str] = Query(None, description="City to search in"),
#     state_code: Optional[str] = Query(None, description="2-letter state code (required for API search)"),
#     bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
#     max_price: Optional[float] = Query(None, description="Maximum price (monthly rent for rentals, sale price for purchases)"),
#     search_type: str = Query("rent", description="Search type: 'rent' for rentals or 'buy' for purchases"),
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
#                 bedrooms=bedrooms,
#                 max_price=max_price,
#                 search_type=search_type,
#                 property_type=property_type
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
#                     "search_type": search_type,
#                     "property_type": property_type,
#                 }
#             }

#         except Exception as e:
#             print(f"API search error: {str(e)}")  # Debug logging

#             # Return mock data for testing when API fails
#             mock_listings = [
#                 {
#                     "id": 1,
#                     "title": f"Beautiful {bedrooms or 2}BR/{bedrooms or 2}BA Apartment in {city}",
#                     "price": max_price - 200 if max_price else 2000,
#                     "bedrooms": bedrooms or 2,
#                     "bathrooms": 2.0,
#                     "square_feet": 1200,
#                     "city": city,
#                     "state": state_code,
#                     "description": f"Modern apartment located in the heart of {city}. Features updated appliances and great amenities.",
#                     "photo_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop&auto=format&q=80",
#                     "url": "https://example.com/property/1"
#                 },
#                 {
#                     "id": 2,
#                     "title": f"Spacious {(bedrooms or 2) + 1}BR/{(bedrooms or 2) + 1}BA House in {city}",
#                     "price": (max_price + 500) if max_price else 2800,
#                     "bedrooms": (bedrooms or 2) + 1,
#                     "bathrooms": 2.5,
#                     "square_feet": 1800,
#                     "city": city,
#                     "state": state_code,
#                     "description": f"Charming house with a yard in {city}. Perfect for families looking for space and comfort.",
#                     "photo_url": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&h=300&fit=crop&auto=format&q=80",
#                     "url": "https://example.com/property/2"
#                 },
#                 {
#                     "id": 3,
#                     "title": f"Cozy {bedrooms or 1}BR/{bedrooms or 1}BA Condo in {city}",
#                     "price": (max_price - 400) if max_price else 1600,
#                     "bedrooms": bedrooms or 1,
#                     "bathrooms": 1.0,
#                     "square_feet": 900,
#                     "city": city,
#                     "state": state_code,
#                     "description": f"Affordable condo in {city} with great access to downtown and public transportation.",
#                     "photo_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400&h=300&fit=crop&auto=format&q=80",
#                     "url": "https://example.com/property/3"
#                 }
#             ]

#             return {
#                 "listings": mock_listings,
#                 "count": len(mock_listings),
#                 "source": "Mock Data (API unavailable)",
#                 "filters": {
#                     "city": city,
#                     "state_code": state_code,
#                     "bedrooms": bedrooms,
#                     "max_price": max_price,
#                     "search_type": search_type,
#                     "property_type": property_type,
#                 }
#             }

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
#             "listings": [
#                 {
#                     "id": listing.id,
#                     "title": listing.title,
#                     "description": listing.description,
#                     "price": listing.price,
#                     "bedrooms": listing.bedrooms,
#                     "bathrooms": listing.bathrooms,
#                     "square_feet": listing.square_feet,
#                     "city": listing.city,
#                     "state": listing.state,
#                     "url": listing.source_url,
#                 } for listing in listings
#             ],
#             "count": len(listings),
#             "source": "Local Database",
#             "filters": {
#                 "city": city,
#                 "bedrooms": bedrooms,
#                 "max_price": max_price
#             }
#         }



# # from fastapi import APIRouter, Depends, Query, HTTPException
# # from sqlalchemy.orm import Session
# # from typing import Optional
# # from ...core.database import get_db
# # from ...models.listing import Listing
# # from ...services.realtor_service import fetch_realtor_listings
# # from enum import Enum 

# # router = APIRouter()

# # class PropertyType(str, Enum):
# #     apartment = "apartment"
# #     house = "house"
# #     condo = "condo"
# #     townhouse = "townhouse"


# # @router.get("/search")
# # async def search_listings(
# #     city: Optional[str] = Query(None, description="City to search in"),
# #     state_code: Optional[str] = Query(None, description="2-letter state code (required for API search)"),
# #     bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
# #     max_price: Optional[float] = Query(None, description="Maximum price"),
# #     property_type: Optional[str] = Query(None, description="Property type (apartment, house, condo, townhouse)"), 
# #     use_api: bool = Query(True, description="Use Realtor API (True) or local DB (False)"),
# #     db: Session = Depends(get_db)
# # ):
# #     """
# #     Search for listings based on criteria.
# #     Can search via Realtor API or local database.
# #     """

# #     if use_api:
# #         if not city or not state_code:
# #             raise HTTPException(status_code=400, detail="City and state_code are required for API search")

# #         try:
# #             api_listings = await fetch_realtor_listings(
# #                 city=city,
# #                 state_code=state_code,
# #                 bedrooms=bedrooms if bedrooms else None,
# #                 max_price=max_price if max_price else None,
# #                 property_type=property_type.value if property_type else None
# #             )

# #             return {
# #                 "listings": api_listings,
# #                 "count": len(api_listings),
# #                 "source": "Realtor API",
# #                 "filters": {
# #                     "city": city,
# #                     "state_code": state_code,
# #                     "bedrooms": bedrooms,
# #                     "max_price": max_price,
# #                     "property_type":property_type,
# #                 }
# #             }

# #         except Exception as e:
# #             raise HTTPException(
# #                 status_code=500,
# #                 detail=f"API search failed: {str(e)}"
# #             )

# #     else:
# #         # Database-based search (original functionality)
# #         query = db.query(Listing)

# #         if city:
# #             query = query.filter(Listing.city.ilike(f"%{city}%"))

# #         if bedrooms:
# #             query = query.filter(Listing.bedrooms == bedrooms)

# #         if max_price:
# #             query = query.filter(Listing.price <= max_price)

# #         listings = query.limit(10).all()

# #         return {
# #             "listings": listings,
# #             "count": len(listings),
# #             "source": "Local Database",
# #             "filters": {
# #                 "city": city,
# #                 "bedrooms": bedrooms,
# #                 "max_price": max_price
# #             }
# #         }



