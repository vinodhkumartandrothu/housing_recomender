from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ...services.ai_insights_service import ai_insights_service

router = APIRouter()


class PropertyInsightRequest(BaseModel):
    """Request model for generating property insights"""
    city: str
    state: str
    address: Optional[str] = None  # Full street address for more precise location data
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    property_type: Optional[str] = "property"
    search_type: Optional[str] = "rent"


class PropertyInsightResponse(BaseModel):
    """Response model for property insights"""
    neighborhood: str
    commute: str
    lifestyle: str
    schools: str


@router.post("/property-insights", response_model=PropertyInsightResponse)
async def generate_property_insights(request: PropertyInsightRequest):
    """
    Generate AI-powered insights for a property card

    Returns exactly 4 insights:
    - 🏡 Neighborhood: Area character and vibe
    - 🚗 Commute: Transportation and accessibility
    - 🛒 Lifestyle: Daily amenities and conveniences
    - 🎓 Schools: Education quality and family considerations
    """
    try:
        # Convert request to property data dict
        property_data = {
            "city": request.city,
            "state": request.state,
            "address": request.address,  # Include full address for precise location
            "price": request.price,
            "bedrooms": request.bedrooms,
            "bathrooms": request.bathrooms,
            "square_feet": request.square_feet,
            "property_type": request.property_type
        }

        print(f"🎯 INSIGHTS.PY RECEIVED: address={request.address}, city={request.city}, state={request.state}")
        print(f"🎯 PROPERTY_DATA DICT: {property_data}")

        search_criteria = {
            "search_type": request.search_type
        }

        # Generate insights using AI service
        insights = await ai_insights_service.generate_property_insights(
            property_data=property_data,
            search_criteria=search_criteria
        )

        return PropertyInsightResponse(**insights)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate property insights: {str(e)}"
        )


@router.get("/property-insights/batch")
async def generate_batch_insights(
    properties: str,  # JSON string of property list
    search_type: str = "rent"
):
    """
    Generate insights for multiple properties (for search results)

    Args:
        properties: JSON string containing array of property objects
        search_type: "rent" or "buy"
    """
    import json

    try:
        property_list = json.loads(properties)
        results = []

        for prop in property_list:
            property_data = {
                "city": prop.get("city", ""),
                "state": prop.get("state", ""),
                "address": prop.get("address"),  # Include full address for precise location
                "price": prop.get("price"),
                "bedrooms": prop.get("bedrooms"),
                "bathrooms": prop.get("bathrooms"),
                "square_feet": prop.get("square_feet"),
                "property_type": prop.get("property_type", "property")
            }

            search_criteria = {"search_type": search_type}

            insights = await ai_insights_service.generate_property_insights(
                property_data=property_data,
                search_criteria=search_criteria
            )

            results.append({
                "property_id": prop.get("id"),
                "insights": insights
            })

        return {"insights": results}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate batch insights: {str(e)}"
        )