from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import httpx
from ..core.config import settings


class RealtorService:
    """Service for fetching listings from Realtor.com API via RapidAPI"""

    def __init__(self):
        self.rapidapi_key = settings.rapidapi_key
        self.rapidapi_host = settings.rapidapi_host

        if not self.rapidapi_key:
            raise ValueError("Missing RAPIDAPI_KEY in .env or config.py")

    async def fetch_realtor_listings(
        self,
        city: str,
        state_code: str,
        bedrooms: Optional[int] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        listing_type: str = "for_rent",
    ) -> List[Dict[str, Any]]:
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host,
            "Content-Type": "application/json",
        }

        url = f"https://{self.rapidapi_host}/properties/v3/list"

        payload = {
            "limit": 50,  # 🔥 Get many more results to choose from
            "offset": 0,
            "city": city,
            "state_code": state_code.upper(),
            "status": [listing_type],
            "sort": {"direction": "desc", "field": "list_date"},
        }

        # 🔥 Only apply max_price filter in API, not bedrooms (filter locally)
        if max_price:
            payload["price_max"] = int(max_price * 1.2)  # Add 20% buffer for better results
            payload["price_min"] = 300  # Very low minimum

        print(f"🔍 Realtor API Request: {payload}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                properties = data.get("data", {}).get("home_search", {}).get("results", [])
                if not properties:
                    return []

                # 🔥 Parse ALL listings first, then filter smartly
                all_listings = []
                for prop in properties:
                    listing = self._parse_listing(prop)
                    if listing:
                        all_listings.append(listing)

                # 🔥 Multi-tier filtering for better results
                perfect_matches = []
                good_matches = []
                acceptable_matches = []
                
                for listing in all_listings:
                    match_level = self._evaluate_listing_match(listing, bedrooms, max_price)
                    
                    if match_level == "perfect":
                        perfect_matches.append(listing)
                    elif match_level == "good": 
                        good_matches.append(listing)
                    elif match_level == "acceptable":
                        acceptable_matches.append(listing)

                # 🔥 Sort each tier by preference
                def sort_by_preference(listings):
                    # Prioritize: has price > has bedrooms > has description
                    return sorted(listings, key=lambda x: (
                        bool(x.get("price")),           # Has price
                        bool(x.get("bedrooms")),        # Has bedroom info
                        bool(x.get("square_feet")),     # Has sqft
                        -(x.get("price", 99999))        # Lower price better
                    ), reverse=True)
                
                perfect_matches = sort_by_preference(perfect_matches)
                good_matches = sort_by_preference(good_matches)
                acceptable_matches = sort_by_preference(acceptable_matches)
                
                # 🔥 Combine results: perfect first, then good, then acceptable
                final_results = (perfect_matches + good_matches + acceptable_matches)[:limit]
                
                print(f"✅ Found {len(perfect_matches)} perfect, {len(good_matches)} good, {len(acceptable_matches)} acceptable matches")
                print(f"✅ Returning {len(final_results)} total listings")
                
                return final_results

        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="Realtor API request timed out")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Realtor API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch listings: {str(e)}")

    def _parse_listing(self, prop: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse and normalize a property result from Realtor API"""
        try:
            location = prop.get("location", {})
            address = location.get("address", {})
            description = prop.get("description", {})
            community = prop.get("community", {})

            # Price with fallback to community price range
            price = (
                prop.get("list_price") or
                prop.get("price") or
                prop.get("rent_price") or
                location.get("price")
            )

            price_range = None
            if not price and (community.get("price_min") or community.get("price_max")):
                price_range = f"${community.get('price_min','')} - ${community.get('price_max','')}"
                if community.get("price_min") and community.get("price_max"):
                    price = (community["price_min"] + community["price_max"]) / 2
                else:
                    price = community.get("price_min") or community.get("price_max")

            # Extract bedroom/bathroom/sqft info
            bedrooms = description.get("beds")
            bathrooms = description.get("baths")
            square_feet = description.get("sqft")

            # 🔥 For apartment complexes, use mid-range estimates
            if bedrooms is None:
                beds_min = description.get("beds_min")
                beds_max = description.get("beds_max") 
                if beds_min is not None and beds_max is not None:
                    bedrooms = int((beds_min + beds_max) / 2)
                elif beds_min is not None:
                    bedrooms = beds_min
                elif beds_max is not None:
                    bedrooms = beds_max

            if bathrooms is None:
                baths_min = description.get("baths_min")
                baths_max = description.get("baths_max")
                if baths_min is not None and baths_max is not None:
                    bathrooms = (baths_min + baths_max) / 2
                elif baths_min is not None:
                    bathrooms = baths_min
                elif baths_max is not None:
                    bathrooms = baths_max

            if square_feet is None:
                sqft_min = description.get("sqft_min")
                sqft_max = description.get("sqft_max")
                if sqft_min is not None and sqft_max is not None:
                    square_feet = int((sqft_min + sqft_max) / 2)
                elif sqft_min is not None:
                    square_feet = sqft_min
                elif sqft_max is not None:
                    square_feet = sqft_max

            # Build title
            address_line = address.get("line", "")
            city = address.get("city", "")
            property_type = description.get("type", "")

            title_parts = []
            if bedrooms: title_parts.append(f"{bedrooms}BR")
            if bathrooms: title_parts.append(f"{bathrooms}BA")
            if property_type: title_parts.append(property_type.title())
            if address_line: title_parts.append(f"- {address_line}")
            elif city: title_parts.append(f"in {city}")
            title = " ".join(title_parts) if title_parts else f"Property in {city}"

            # Build description
            desc_parts = []
            if description.get("sub_type"): desc_parts.append(description["sub_type"].title())
            if property_type: desc_parts.append(f"{property_type} property")
            if bedrooms and bathrooms: desc_parts.append(f"with {bedrooms} bedrooms and {bathrooms} bathrooms")
            if square_feet: desc_parts.append(f"({square_feet} sqft)")
            
            # 🔥 Add range info for apartment complexes
            if description.get("beds_min") and description.get("beds_max") and not description.get("beds"):
                desc_parts.append(f"Available in {description['beds_min']}-{description['beds_max']} bedroom layouts")
            
            full_description = ". ".join(desc_parts) if desc_parts else "Rental property"

            return {
                "id": str(prop.get("property_id", "")),
                "title": title,
                "description": full_description,
                "price": float(price) if price else None,
                "price_range": price_range,
                "bedrooms": int(bedrooms) if bedrooms else None,
                "bathrooms": float(bathrooms) if bathrooms else None,
                "square_feet": int(square_feet) if square_feet else None,
                "city": city,
                "state": address.get("state_code", ""),
                "url": prop.get("href", ""),
                "source": "Realtor",
                "photos": [photo.get("href") for photo in prop.get("photos", [])[:3]],
                # Store original ranges for matching
                "beds_min": description.get("beds_min"),
                "beds_max": description.get("beds_max"),
                "sqft_min": description.get("sqft_min"),
                "sqft_max": description.get("sqft_max"),
            }
        except Exception as e:
            print(f"❌ Error parsing listing: {e}")
            return None

    def _evaluate_listing_match(self, listing: Dict[str, Any], target_bedrooms: Optional[int], max_price: Optional[float]) -> str:
        """Evaluate how well a listing matches the search criteria"""
        
        # Skip listings with no useful info
        if not listing.get("city") or not listing.get("title"):
            return "reject"
        
        price = listing.get("price")
        bedrooms = listing.get("bedrooms")
        beds_min = listing.get("beds_min")
        beds_max = listing.get("beds_max")
        
        # 🔥 Price evaluation
        price_match = "unknown"
        if price:
            if max_price:
                if price <= max_price:
                    price_match = "perfect"
                elif price <= max_price * 1.1:  # 10% over budget
                    price_match = "acceptable"
                else:
                    return "reject"  # Too expensive
            else:
                price_match = "perfect"  # No price limit specified
        
        # 🔥 Bedroom evaluation  
        bedroom_match = "unknown"
        if target_bedrooms:
            if bedrooms:
                if bedrooms == target_bedrooms:
                    bedroom_match = "perfect"
                elif abs(bedrooms - target_bedrooms) <= 1:
                    bedroom_match = "good"
                else:
                    bedroom_match = "acceptable"  # Still might be interesting
            elif beds_min is not None and beds_max is not None:
                if beds_min <= target_bedrooms <= beds_max:
                    bedroom_match = "good"  # Available in desired size
                else:
                    bedroom_match = "acceptable"
            else:
                bedroom_match = "acceptable"  # No bedroom info, but keep it
        else:
            bedroom_match = "perfect"  # No bedroom preference specified
        
        # 🔥 Determine overall match level
        if price_match == "perfect" and bedroom_match == "perfect":
            return "perfect"
        elif (price_match in ["perfect", "good"] and bedroom_match in ["perfect", "good"]) or \
             (price_match == "perfect" and bedroom_match == "acceptable") or \
             (price_match == "good" and bedroom_match == "perfect"):
            return "good"
        else:
            return "acceptable"


# Global instance
realtor_service = RealtorService()


async def fetch_realtor_listings(
    city: str,
    state_code: str,
    bedrooms: Optional[int] = None,
    max_price: Optional[float] = None,
    listing_type: str = "for_rent",
):
    return await realtor_service.fetch_realtor_listings(
        city=city,
        state_code=state_code,
        bedrooms=bedrooms,
        max_price=max_price,
        listing_type=listing_type,
    )