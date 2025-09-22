import httpx
from typing import Optional, Dict, Any
from ..core.config import settings


async def fetch_property(
    address: str,
    city: str,
    state: str,
    postal_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch property data from Estated API

    Args:
        address: Street address
        city: City name
        state: State abbreviation (e.g., "TX")
        postal_code: Optional ZIP code

    Returns:
        Dictionary containing property data from Estated API
    """
    if not settings.estated_api_key:
        raise ValueError("Estated API key not configured")

    base_url = "https://apis.estated.com/v4/property"

    params = {
        "token": settings.estated_api_key,
        "address": address,
        "city": city,
        "state": state
    }

    if postal_code:
        params["zip"] = postal_code

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(base_url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise Exception(f"Estated API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}")


async def search_properties(
    city: str,
    state: str,
    limit: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None
) -> Dict[str, Any]:
    """
    Search for properties in a given area using Estated API

    Args:
        city: City name
        state: State abbreviation
        limit: Maximum number of results
        min_price: Minimum price filter
        max_price: Maximum price filter
        bedrooms: Number of bedrooms filter
        bathrooms: Number of bathrooms filter

    Returns:
        Dictionary containing search results from Estated API
    """
    if not settings.estated_api_key:
        raise ValueError("Estated API key not configured")

    base_url = "https://apis.estated.com/v4/property/search"

    params = {
        "token": settings.estated_api_key,
        "city": city,
        "state": state,
        "limit": limit
    }

    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price
    if bedrooms:
        params["bedrooms"] = bedrooms
    if bathrooms:
        params["bathrooms"] = bathrooms

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(base_url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise Exception(f"Estated API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}")