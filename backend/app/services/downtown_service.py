"""
Downtown mapping service for housing recommendations

Handles:
1. Finding the appropriate downtown for each property
2. Proper fallback to nearest major downtown using Google Places
3. Dynamic distance calculation to correct downtown
4. Clear labeling (e.g., "Dallas Downtown", "Princeton Downtown")
"""

import aiohttp
import math
from typing import Optional, Tuple
from ..core.config import settings


class DowntownService:
    """Service for mapping properties to appropriate downtown areas"""

    def __init__(self):
        self.google_api_key = settings.google_maps_api_key

    async def find_appropriate_downtown(
        self,
        property_city: str,
        property_state: str,
        property_lat: float,
        property_lng: float
    ) -> Tuple[str, Optional[Tuple[float, float]]]:
        """
        Find the most appropriate downtown for a property

        Returns:
            Tuple of (downtown_label, downtown_coordinates)
            e.g., ("Princeton Downtown", (40.3573, -74.6672))
        """

        if not self.google_api_key:
            return (f"{property_city} area", None)

        # Step 1: Try to find local downtown
        local_downtown = await self._find_local_downtown(
            property_city, property_state, property_lat, property_lng
        )

        if local_downtown:
            return local_downtown

        # Step 2: Fallback to nearest major downtown
        return await self._find_nearest_major_downtown(
            property_city, property_state, property_lat, property_lng
        )

    async def _find_local_downtown(
        self,
        city: str,
        state: str,
        property_lat: float,
        property_lng: float
    ) -> Optional[Tuple[str, Tuple[float, float]]]:
        """Try to find the local downtown for the property's city"""

        try:
            async with aiohttp.ClientSession() as session:
                # Search for city's downtown
                query = f"Downtown {city}, {state}"
                url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                params = {"query": query, "key": self.google_api_key}

                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("status") == "OK" and data.get("results"):
                        for result in data["results"][:3]:  # Check top 3 results
                            downtown_coords = await self._geocode_address(result["formatted_address"])

                            if downtown_coords:
                                dt_lat, dt_lng = downtown_coords
                                distance = self._calculate_distance(property_lat, property_lng, dt_lat, dt_lng)

                                # Accept local downtown if within 50 miles and matches city
                                if distance <= 50 and city.lower() in result["formatted_address"].lower():
                                    print(f"✅ Found local downtown: {city} Downtown, distance: {distance:.1f} miles")
                                    return (f"{city} Downtown", (dt_lat, dt_lng))

        except Exception as e:
            print(f"❌ Error finding local downtown for {city}, {state}: {e}")

        return None

    async def _find_nearest_major_downtown(
        self,
        property_city: str,
        property_state: str,
        property_lat: float,
        property_lng: float
    ) -> Tuple[str, Optional[Tuple[float, float]]]:
        """Find nearest major downtown dynamically using Google Places"""

        try:
            async with aiohttp.ClientSession() as session:
                # Search for major city downtown in the state
                query = f"major city downtown in {property_state}"
                url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                params = {"query": query, "key": self.google_api_key}

                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("status") == "OK" and data.get("results"):
                        # Get the first major downtown result
                        result = data["results"][0]
                        coords = await self._geocode_address(result["formatted_address"])

                        if coords:
                            # Extract city name from the result
                            city_name = result.get("name", "").replace(" Downtown", "").replace("Downtown ", "")
                            if not city_name:
                                # Fallback: extract from formatted address
                                address_parts = result["formatted_address"].split(",")
                                city_name = address_parts[0].strip() if address_parts else property_city

                            distance = self._calculate_distance(property_lat, property_lng, coords[0], coords[1])

                            print(f"✅ Using nearest major downtown: {city_name} Downtown, distance: {distance:.1f} miles")
                            return (f"{city_name} Downtown", coords)

        except Exception as e:
            print(f"❌ Error finding major downtown: {e}")

        # Final fallback
        return (f"{property_city} area", None)

    async def get_commute_time_to_downtown(
        self,
        property_lat: float,
        property_lng: float,
        downtown_label: str,
        downtown_coords: Optional[Tuple[float, float]]
    ) -> Optional[str]:
        """Get accurate commute time from property to the specific downtown"""

        if not self.google_api_key or not downtown_coords:
            return f"Research commute to {downtown_label}"

        try:
            dt_lat, dt_lng = downtown_coords

            async with aiohttp.ClientSession() as session:
                url = "https://maps.googleapis.com/maps/api/distancematrix/json"
                params = {
                    "origins": f"{property_lat},{property_lng}",
                    "destinations": f"{dt_lat},{dt_lng}",
                    "mode": "driving",
                    "departure_time": "now",
                    "key": self.google_api_key,
                }

                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("status") == "OK" and data["rows"]:
                        element = data["rows"][0]["elements"][0]
                        if element.get("status") == "OK":
                            duration = element["duration"]["text"]
                            return f"{duration} drive to {downtown_label}"

        except Exception as e:
            print(f"❌ Commute time error to {downtown_label}: {e}")

        return f"Research commute to {downtown_label}"

    async def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode an address to coordinates"""

        if not self.google_api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {"address": address, "key": self.google_api_key}

                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("status") == "OK" and data["results"]:
                        location = data["results"][0]["geometry"]["location"]
                        return (location["lat"], location["lng"])

        except Exception as e:
            print(f"❌ Geocoding error for {address}: {e}")

        return None

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula"""

        R = 3959  # Earth's radius in miles
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)

        a = (
            math.sin(dlat/2)**2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dlng/2)**2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c


# Global service instance
downtown_service = DowntownService()