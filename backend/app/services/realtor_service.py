from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import httpx
from ..core.config import settings


PROPERTY_TYPE_MAP = {
    "apartment": "apartment_condo",
    "condo": "apartment_condo",
    "house": "single_family",
    "townhouse": "townhouse"
}


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
        search_type: str = "rent",  # "rent" or "buy"
        property_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host,
            "Content-Type": "application/json",
        }

        url = f"https://{self.rapidapi_host}/properties/v3/list"

        # Map search_type to API listing_type
        if search_type == "rent":
            listing_type = "for_rent"
        elif search_type == "buy":
            listing_type = "for_sale"
        else:
            listing_type = "for_rent"  # Default to rent

        payload = {
            "limit": 50,
            "offset": 0,
            "city": city,
            "state_code": state_code.upper(),
            "status": [listing_type],
            "sort": {"direction": "desc", "field": "list_date"},
        }

        if property_type:
            api_property_type = PROPERTY_TYPE_MAP.get(property_type.lower())
            if api_property_type:
                payload["property_type"] = api_property_type

        if max_price:
            if search_type == "rent":
                payload["price_max"] = int(max_price * 1.2)
                payload["price_min"] = 300
            elif search_type == "buy":
                payload["price_max"] = int(max_price * 1.1)
                payload["price_min"] = 50000

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                properties = data.get("data", {}).get("home_search", {}).get("results", [])
                if not properties:
                    return []

                all_listings = []
                for prop in properties:
                    listing = self._parse_listing(prop)
                    if listing:
                        all_listings.append(listing)

                if property_type:
                    type_filtered_listings = []
                    for listing in all_listings:
                        if self._matches_property_type(listing, property_type):
                            type_filtered_listings.append(listing)
                    all_listings = type_filtered_listings

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

                def sort_by_preference(listings):
                    return sorted(
                        listings,
                        key=lambda x: (
                            bool(x.get("price")),
                            bool(x.get("bedrooms")),
                            bool(x.get("square_feet")),
                            -(x.get("price") or 99999)
                        ),
                        reverse=True
                    )

                perfect_matches = sort_by_preference(perfect_matches)
                good_matches = sort_by_preference(good_matches)
                acceptable_matches = sort_by_preference(acceptable_matches)

                final_results = (perfect_matches + good_matches + acceptable_matches)[:limit]

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
            location = prop.get("location") or {}
            address = location.get("address") or {}
            description = prop.get("description") or {}
            community = prop.get("community") or {}

            # Price extraction with proper range handling
            price = None
            price_range = None

            is_for_sale = "for_sale" in prop.get("status", "")
            price_suffix = "" if is_for_sale else "/mo"

            list_price_min = prop.get("list_price_min")
            list_price_max = prop.get("list_price_max")

            if list_price_min or list_price_max:
                if list_price_min and list_price_max and list_price_min != list_price_max:
                    price_range = f"${int(list_price_min):,} - ${int(list_price_max):,}{price_suffix}"
                    price = (list_price_min + list_price_max) / 2
                elif list_price_min:
                    price_range = f"From ${int(list_price_min):,}{price_suffix}"
                    price = list_price_min
                elif list_price_max:
                    price_range = f"Up to ${int(list_price_max):,}{price_suffix}"
                    price = list_price_max

            if not price:
                price = (
                    prop.get("rent_price")
                    or prop.get("list_price")
                    or prop.get("price")
                    or location.get("price")
                )

            if not price_range and community:
                community_price_min = community.get("price_min")
                community_price_max = community.get("price_max")
                if community_price_min or community_price_max:
                    if community_price_min and community_price_max:
                        price_range = f"${int(community_price_min):,} - ${int(community_price_max):,}{price_suffix}"
                        price = (community_price_min + community_price_max) / 2
                    elif community_price_min:
                        price_range = f"From ${int(community_price_min):,}{price_suffix}"
                        price = community_price_min
                    elif community_price_max:
                        price_range = f"Up to ${int(community_price_max):,}{price_suffix}"
                        price = community_price_max

            if not price_range and price:
                price_range = f"${int(price):,}{price_suffix}"
            elif not price and not price_range:
                price_range = "Contact for pricing"

            # Extract bedroom/bathroom/sqft info
            bedrooms = description.get("beds")
            bathrooms = description.get("baths")
            square_feet = description.get("sqft")

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

            desc_parts = []
            if description.get("sub_type"): desc_parts.append(description["sub_type"].title())
            if property_type: desc_parts.append(f"{property_type} property")
            if bedrooms and bathrooms: desc_parts.append(f"with {bedrooms} bedrooms and {bathrooms} bathrooms")
            if square_feet: desc_parts.append(f"({square_feet} sqft)")
            if description.get("beds_min") and description.get("beds_max") and not description.get("beds"):
                desc_parts.append(f"Available in {description['beds_min']}-{description['beds_max']} bedroom layouts")
            full_description = ". ".join(desc_parts) if desc_parts else "Rental property"

            # Extract photos from multiple possible locations in the API response
            photos_data = []
            primary_photo = None

            # Try different photo field locations that Realtor API might use
            possible_photo_fields = [
                prop.get("photos", []),
                prop.get("photo", []) if isinstance(prop.get("photo"), list) else ([prop.get("photo")] if prop.get("photo") else []),
                prop.get("images", []),
                prop.get("picture", []) if isinstance(prop.get("picture"), list) else ([prop.get("picture")] if prop.get("picture") else [])
            ]

            # Also check nested locations
            if prop.get("primary_photo"):
                possible_photo_fields.append([prop.get("primary_photo")])

            # Check if photos are nested in other objects
            description = prop.get("description", {})
            if isinstance(description, dict) and description.get("photos"):
                possible_photo_fields.append(description.get("photos", []))

            community = prop.get("community", {})
            if isinstance(community, dict) and community.get("photos"):
                possible_photo_fields.append(community.get("photos", []))

            # Find the first valid photo collection
            for photo_collection in possible_photo_fields:
                if photo_collection and len(photo_collection) > 0:
                    photos_data = photo_collection
                    break

            # Extract photo URLs from the found collection
            photo_urls = []
            if photos_data and len(photos_data) > 0:
                for photo in photos_data[:5]:  # Get up to 5 photos
                    photo_url = None

                    # Handle different photo object structures
                    if isinstance(photo, str):
                        # Direct URL string
                        photo_url = photo
                    elif isinstance(photo, dict):
                        # Photo object with possible fields
                        photo_url = (
                            photo.get("href") or
                            photo.get("url") or
                            photo.get("image") or
                            photo.get("src") or
                            photo.get("link")
                        )

                    if photo_url and isinstance(photo_url, str):
                        # Handle different URL formats
                        if photo_url.startswith("//"):
                            photo_url = "https:" + photo_url
                        elif photo_url.startswith("/"):
                            # Relative URL, probably from realtor.com
                            photo_url = "https://realtor.com" + photo_url
                        elif not photo_url.startswith("http"):
                            # Assume it needs https
                            photo_url = "https://" + photo_url

                        # Basic validation that it looks like an image URL
                        if any(ext in photo_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) or 'photo' in photo_url.lower() or 'image' in photo_url.lower():
                            photo_urls.append(photo_url)

                # Set primary photo as the first valid photo
                primary_photo = photo_urls[0] if photo_urls else None


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
                "photo_url": primary_photo,  # Primary photo for easy access
                "photos": photo_urls,  # All available photos
                "beds_min": description.get("beds_min"),
                "beds_max": description.get("beds_max"),
                "sqft_min": description.get("sqft_min"),
                "sqft_max": description.get("sqft_max"),
            }
        except Exception:
            return None

    def _matches_property_type(self, listing: Dict[str, Any], requested_type: str) -> bool:
        description = listing.get("description", "").lower()
        title = listing.get("title", "").lower()

        if requested_type.lower() == "apartment":
            apartment_keywords = ["apartment", "apt", "complex", "community"]
            exclude_keywords = ["single_family", "single family", "townhome", "townhouse"]
            url = listing.get("url", "").lower()
            has_apt_in_url = "apt" in url or "unit" in url
            has_apartment_keywords = any(keyword in description or keyword in title for keyword in apartment_keywords)
            has_exclude_keywords = any(keyword in description for keyword in exclude_keywords)
            return (has_apartment_keywords or has_apt_in_url) and not has_exclude_keywords

        elif requested_type.lower() == "condo":
            return "condo" in description or "condo" in title
        elif requested_type.lower() in ["house", "single_family"]:
            return "single_family" in description or "single family" in description
        elif requested_type.lower() == "townhouse":
            return "townhome" in description or "townhouse" in description
        return True

    def _evaluate_listing_match(self, listing: Dict[str, Any], target_bedrooms: Optional[int], max_price: Optional[float]) -> str:
        if not listing.get("city") or not listing.get("title"):
            return "reject"
        
        price = listing.get("price")
        bedrooms = listing.get("bedrooms")
        beds_min = listing.get("beds_min")
        beds_max = listing.get("beds_max")

        price_match = "unknown"
        if price:
            if max_price:
                if price <= max_price:
                    price_match = "perfect"
                elif price <= max_price * 1.1:
                    price_match = "acceptable"
                else:
                    return "reject"
            else:
                price_match = "perfect"

        bedroom_match = "unknown"
        if target_bedrooms:
            if bedrooms:
                if bedrooms == target_bedrooms:
                    bedroom_match = "perfect"
                else:
                    return "reject"  # Strict: reject if exact bedroom count doesn't match
            elif beds_min is not None and beds_max is not None:
                if beds_min <= target_bedrooms <= beds_max:
                    bedroom_match = "perfect"  # Apartment complex has the requested bedroom count available
                else:
                    return "reject"  # Reject if complex doesn't offer target bedroom count
            else:
                # No bedroom info available - be lenient for now but rank lower
                bedroom_match = "acceptable"
        else:
            bedroom_match = "perfect"  # No bedroom preference specified

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
    search_type: str = "rent",
    property_type: Optional[str] = None,
):
    return await realtor_service.fetch_realtor_listings(
        city=city,
        state_code=state_code,
        bedrooms=bedrooms,
        max_price=max_price,
        search_type=search_type,
        property_type=property_type,
    )
