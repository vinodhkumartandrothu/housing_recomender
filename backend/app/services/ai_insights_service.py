import openai
from openai import AsyncOpenAI
from typing import Dict, Any, Optional
from ..core.config import settings
from .insights_service import property_insights_service
from .downtown_service import downtown_service


class AIInsightsService:
    """Agentic AI service for generating property insights"""

    def __init__(self):
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            print("⚠️ Warning: OpenAI API key not configured")
            self.client = None

        self.google_api_key = settings.google_maps_api_key
        self.google_places_base = "https://maps.googleapis.com/maps/api/place"

    async def generate_property_insights(
        self,
        property_data: Dict[str, Any],
        search_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:

        city = property_data.get('city', '').strip()
        state = property_data.get('state', '').strip()
        # 🔹 NEW: Try to pull full address directly from property data
        full_address = (
            property_data.get('address') or
            property_data.get('full_address') or
            None
            # f"{property_data.get('city')}, {property_data.get('state')}"
            
        )

        # lat, lng = await self._get_coordinates_from_address(full_address)

        if full_address:
            full_address = full_address.strip()

        price = property_data.get('price')
        bedrooms = property_data.get('bedrooms')
        property_type = property_data.get('property_type', 'property')
        search_type = search_criteria.get('search_type', 'rent') if search_criteria else 'rent'

        # ------------------------
        # 🔹 FIX 1: Prefer full property address for commute calc
        # ------------------------
        if full_address and full_address != f"{city}, {state}":
            print(f"🏠 Using full property address for commute: {full_address}")
            lat, lng = await self._get_coordinates_from_address(full_address)
            address = full_address
        else:
            print(f"⚠️ Property missing full address → fallback to city center {city}, {state}")
            lat, lng = await self._get_coordinates(city, state)
            address = f"{city}, {state}"

        if not lat or not lng:
            print(f"❌ Could not resolve coordinates for {address}")
            return self._generate_fallback_insights(city, state, property_type, search_type)

        # ------------------------
        # 🔹 FIX 2: Reject fake/duplicate downtowns (like Denton, Plainsboro)
        # ------------------------
        downtown_label, downtown_coords = await downtown_service.find_appropriate_downtown(
            city, state, lat, lng
        )

        if not downtown_label or "usa" in downtown_label.lower():
            print(f"⚠️ No valid downtown found for {city}, {state}. Using nearest MAJOR city downtown.")
            downtown_label, downtown_coords = await downtown_service.find_nearest_major_downtown(
                city, state, lat, lng
            )

        # Commute calculation per property
        commute_time = await downtown_service.get_commute_time_to_downtown(
            lat, lng, downtown_label, downtown_coords
        )

        try:
            api_insights = await property_insights_service.get_all_insights(
                address=address, lat=lat, lng=lng, city=city, state=state
            )

            # ✅ Inject commute time specific to this property
            if commute_time:
                api_insights["commute"] = {
                    "driving_to_downtown": commute_time  # Already includes "to Princeton Downtown"
            }

            return await self.generate_ai_insights(property_data, api_insights, search_criteria)

        except Exception as e:
            print(f"Error generating insights with API data: {e}")
            return self._generate_fallback_insights(city, state, property_type, search_type)

    async def generate_ai_insights(
        self,
        property_data: Dict[str, Any],
        insights_data: Dict[str, Any],
        search_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Use GPT-4.1 to turn raw API insights into 4 concise property insights"""

        city = property_data.get("city", "").strip()
        state = property_data.get("state", "").strip()
        price = property_data.get("price")
        bedrooms = property_data.get("bedrooms")
        search_type = search_criteria.get("search_type", "rent") if search_criteria else "rent"

        prompt = f"""
You are a real estate expert. Based on the following data, generate **exactly 4 insights**.

Property: {bedrooms or 'N/A'} BR in {city}, {state} - ${price or 'Contact for pricing'} {'/month' if search_type == 'rent' else 'purchase'}

**Important: Use the EXACT downtown name provided in the commute data. Do not change it to match the property city.**

Neighborhood: {insights_data.get('neighborhood')}
Commute: {insights_data.get('commute')}
Lifestyle: {insights_data.get('lifestyle')}
Schools: {insights_data.get('schools')}

Output format (keep short and specific, use exact location names):
- 🏡 Neighborhood: [Brief area description]
- 🚗 Commute: [Use exact commute info provided above - do not modify]
- 🛒 Lifestyle: [List 2-3 major stores with distance, e.g., "Walmart and Target within 3 miles, 25+ restaurants"]
- 🎓 Schools: [School rating/quality]
"""

        try:
            if not self.client:
                print("⚠️ OpenAI client not configured, falling back to data-based insights")
                return self._generate_data_based_fallback(insights_data, city, state)

            response = await self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a data-driven real estate analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.5,
            )

            content = response.choices[0].message.content.strip()
            return self._parse_insights(content)

        except Exception as e:
            print(f"AI formatting error: {e}")
            return self._generate_data_based_fallback(insights_data, city, state)

    # ------------------------
    # Helpers
    # ------------------------

    async def _get_coordinates(self, city: str, state: str) -> tuple:
        """Get real coordinates for city/state via Google Geocoding API"""
        if not self.google_api_key:
            return (None, None)

        try:
            import aiohttp
            geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": f"{city}, {state}", "key": self.google_api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(geocoding_url, params=params) as response:
                    data = await response.json()
                    if data.get("status") == "OK" and data["results"]:
                        loc = data["results"][0]["geometry"]["location"]
                        return loc["lat"], loc["lng"]

        except Exception as e:
            print(f"❌ Geocoding error for {city}, {state}: {e}")
        return (None, None)

    async def _get_coordinates_from_address(self, address: str) -> tuple:
        """Geocode full property address"""
        if not self.google_api_key:
            return (None, None)

        try:
            import aiohttp
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": address, "key": self.google_api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    if data.get("status") == "OK" and data["results"]:
                        loc = data["results"][0]["geometry"]["location"]
                        return loc["lat"], loc["lng"]

        except Exception as e:
            print(f"❌ Address geocoding error: {e}")
        return (None, None)

    def _parse_insights(self, ai_response: str) -> Dict[str, str]:
        """Parse GPT output into structured insights, even if slightly misformatted"""
        insights = {
            "neighborhood": "Neighborhood data unavailable",
            "commute": "Commute data unavailable",
            "lifestyle": "Lifestyle data unavailable",
            "schools": "School data unavailable"
        }

        lines = ai_response.split("\n")
        for line in lines:
            clean = line.strip().lower()
            if "neighborhood" in clean:
                insights["neighborhood"] = line.split(":", 1)[-1].strip()
            elif "commute" in clean:
                insights["commute"] = line.split(":", 1)[-1].strip()
            elif "lifestyle" in clean:
                insights["lifestyle"] = line.split(":", 1)[-1].strip()
            elif "school" in clean:
                insights["schools"] = line.split(":", 1)[-1].strip()

        return insights

    def _generate_data_based_fallback(self, insights_data: Dict[str, Any], city: str, state: str) -> Dict[str, str]:
        """Fallback if GPT fails, use raw API values"""
        neighborhood = insights_data.get("neighborhood", {})
        commute = insights_data.get("commute", {})
        lifestyle = insights_data.get("lifestyle", {})
        schools = insights_data.get("schools", {})

        commute_text = commute.get("driving_to_downtown", "Drive time unavailable")


        return {
            "neighborhood": f"Walk Score {neighborhood.get('walkability', {}).get('walk_score', 'N/A')}/100",
            "commute": commute_text,  # ✅ Don't modify the downtown name
            "lifestyle": lifestyle.get("lifestyle_insight", "Standard amenities nearby"),
            "schools": f"District rating {schools.get('district_rating', 'N/A')}/10"
        }

    def _generate_fallback_insights(self, city: str, state: str, property_type: str, search_type: str) -> Dict[str, str]:
        """Simple static fallback if both API and AI fail"""
        return {
            "neighborhood": f"Suburban area in {city}, check local vibe",
            "commute": f"Research commute to nearest downtown",
            "lifestyle": "Standard amenities nearby",
            "schools": f"Research {city} school district"
        }


# Global service instance
ai_insights_service = AIInsightsService()




# import openai
# from openai import AsyncOpenAI
# from typing import Dict, Any, Optional
# from ..core.config import settings
# from .insights_service import property_insights_service


# class AIInsightsService:
#     """Agentic AI service for generating property insights"""

#     def __init__(self):
       

#         # Store Google API key for geocoding
        
#         if settings.openai_api_key:
#             self.client = AsyncOpenAI(api_key=settings.openai_api_key)
#         else:
#             print("⚠️ Warning: OpenAI API key not configured")
#             self.client = None

#         self.google_api_key = settings.google_maps_api_key

#     async def generate_property_insights(
#         self,
#         property_data: Dict[str, Any],
#         search_criteria: Optional[Dict[str, Any]] = None
#     ) -> Dict[str, str]:
#         """
#         Generate exactly 4 insights for a property card using real API data + AI

#         Args:
#             property_data: Property details (city, state, price, bedrooms, etc.)
#             search_criteria: User's search parameters (search_type, budget, etc.)

#         Returns:
#             Dict with 4 insights: neighborhood, commute, lifestyle, schools
#         """

#         # Extract key information
#         city = property_data.get('city', '').strip()
#         state = property_data.get('state', '').strip()
#         full_address = property_data.get('address', '').strip() if property_data.get('address') else None
#         price = property_data.get('price')
#         bedrooms = property_data.get('bedrooms')
#         property_type = property_data.get('property_type', 'property')
#         search_type = search_criteria.get('search_type', 'rent') if search_criteria else 'rent'

#         # Use full address if available, otherwise fall back to city/state
#         if full_address:
#             print(f"🏠 Using full property address: {full_address}")
#             lat, lng = await self._get_coordinates_from_address(full_address)
#             address = full_address
#         else:
#             print(f"🏙️ Using city center coordinates for {city}, {state}")
#             # lat, lng = await self._get_coordinates(city, state)
#             # address = f"{city}, {state}"
#             address = property_data.get('address') or f"{city}, {state}"
#             lat, lng = await self._get_coordinates(address, state)


#         try:
#             # Fetch real API data for insights
#             api_insights = await property_insights_service.get_all_insights(
#                 address=address, lat=lat, lng=lng, city=city, state=state
#             )

#             # Use AI to format the API data into user-friendly insights
#             return await self.generate_ai_insights(property_data, api_insights, search_criteria)

#         except Exception as e:
#             print(f"Error generating insights with API data: {e}")
#             return self._generate_fallback_insights(city, state, property_type, search_type)

#     async def generate_ai_insights(
#         self,
#         property_data: Dict[str, Any],
#         insights_data: Dict[str, Any],
#         search_criteria: Optional[Dict[str, Any]] = None
#     ) -> Dict[str, str]:
#         """
#         Generate AI-formatted insights using real API data

#         Args:
#             property_data: Property details
#             insights_data: Real API data from insights_service
#             search_criteria: Search parameters

#         Returns:
#             Dict with formatted insights
#         """

#         # Extract key information
#         city = property_data.get('city', '').strip()
#         state = property_data.get('state', '').strip()
#         price = property_data.get('price')
#         bedrooms = property_data.get('bedrooms')
#         search_type = search_criteria.get('search_type', 'rent') if search_criteria else 'rent'

#         # Extract API data
#         neighborhood = insights_data.get('neighborhood', {})
#         commute = insights_data.get('commute', {})
#         lifestyle = insights_data.get('lifestyle', {})
#         schools = insights_data.get('schools', {})

#         # Build context-rich prompt with real data
#         prompt = f"""You are a real estate expert creating property insights based on actual data.

# Property: {bedrooms or 'N/A'}BR in {city}, {state} - ${price:,}/{'month' if search_type == 'rent' else 'purchase' if price else 'Contact for pricing'}

# REAL DATA ANALYSIS:
# 🏡 NEIGHBORHOOD DATA:
# - Walk Score: {neighborhood.get('walkability', {}).get('walk_score', 'N/A')}/100 ({neighborhood.get('walkability', {}).get('description', 'Unknown')})
# - Transit Score: {neighborhood.get('walkability', {}).get('transit_score', 'N/A')}/100
# - Safety Score: {neighborhood.get('safety_score', 'N/A')}/100
# - Nearby amenities: {neighborhood.get('nearby_amenities', 'Unknown')}

# 🚗 COMMUTE DATA:
# - Drive to downtown: {commute.get('driving_to_downtown', 'Unknown')}
# - Public transit: {commute.get('transit_to_downtown', 'Limited')}
# - Transit available: {commute.get('has_public_transit', False)}

# 🛒 LIFESTYLE DATA:
# - Total amenities nearby: {lifestyle.get('total_amenities', 'Unknown')}
# - Grocery stores: {lifestyle.get('grocery_options', 'Unknown')} (Top: {lifestyle.get('top_grocery', 'Unknown')})
# - Restaurants: {lifestyle.get('dining_options', 'Unknown')}
# - Gyms/fitness: {lifestyle.get('fitness_options', 'Unknown')}
# - Lifestyle score: {lifestyle.get('lifestyle_score', 'Unknown')}/100

# 🎓 SCHOOL DATA:
# - District rating: {schools.get('district_rating', 'Unknown')}/10
# - Elementary schools: {schools.get('elementary_count', 'Unknown')}
# - High schools: {schools.get('high_count', 'Unknown')}
# - Best elementary: {schools.get('best_elementary', 'Unknown')} (Rating: {schools.get('best_elementary_rating', 'N/A')}/10)
# - Best high school: {schools.get('best_high', 'Unknown')} (Rating: {schools.get('best_high_rating', 'N/A')}/10)

# Create exactly 4 concise, practical insights using this real data:
# - 🏡 Neighborhood: [Focus on walkability, safety, and character - max 12 words]
# - 🚗 Commute: [Mention actual drive times and transit options - max 12 words]
# - 🛒 Lifestyle: [Highlight specific amenities found nearby - max 12 words]
# - 🎓 Schools: [Reference actual ratings and school names if good - max 12 words]

# Make each insight specific, actionable, and based on the real data provided. Use actual numbers and place names when they're meaningful."""

#         try:
#             if not settings.openai_api_key:
#                 return self._generate_data_based_fallback(insights_data, city, state)

#             response = await self.client.chat.completions.create(
#                 model="gpt-4",
#                 messages=[
#                     {"role": "system", "content": "You are a data-driven real estate analyst creating insights from actual API data. Be specific and factual."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=250,
#                 temperature=0.5
#             )

#             content = response.choices[0].message.content.strip()
#             return self._parse_insights(content)

#         except Exception as e:
#             print(f"AI formatting error: {e}")
#             return self._generate_data_based_fallback(insights_data, city, state)

#     async def _get_coordinates(self, city: str, state: str) -> tuple:
#         """Get real coordinates for any city using Google Geocoding API"""
#         if not self.google_api_key:
#             print(f"⚠️ No Google API key available for geocoding {city}, {state}")
#             # Fallback to hardcoded coordinates for major cities
#             city_coords = {
#                 'dallas': (32.7767, -96.7970),
#                 'houston': (29.7604, -95.3698),
#                 'austin': (30.2672, -97.7431),
#                 'san antonio': (29.4241, -98.4936),
#                 'new york': (40.7128, -74.0060),
#                 'los angeles': (34.0522, -118.2437),
#                 'chicago': (41.8781, -87.6298),
#                 'phoenix': (33.4484, -112.0740),
#                 'philadelphia': (39.9526, -75.1652),
#                 'miami': (25.7617, -80.1918),
#                 'atlanta': (33.7490, -84.3880),
#                 'denver': (39.7392, -104.9903)
#             }
#             city_key = city.lower().replace(' ', '')
#             return city_coords.get(city_key, (32.7767, -96.7970))  # Default to Dallas

#         try:
#             import aiohttp

#             # Use Google Geocoding API to get real coordinates
#             geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
#             address = f"{city}, {state}"

#             params = {
#                 'address': address,
#                 'key': self.google_api_key
#             }

#             print(f"🌍 Geocoding {address} using Google Maps API")

#             async with aiohttp.ClientSession() as session:
#                 async with session.get(geocoding_url, params=params) as response:
#                     geocoding_data = await response.json()
#                     print(f"🌍 Geocoding API Response for {address}: status={geocoding_data.get('status')}")

#                     if (geocoding_data.get('status') == 'OK' and
#                         geocoding_data.get('results') and
#                         len(geocoding_data['results']) > 0):

#                         location = geocoding_data['results'][0]['geometry']['location']
#                         lat = location['lat']
#                         lng = location['lng']

#                         print(f"✅ Successfully geocoded {address} to ({lat}, {lng})")
#                         return (lat, lng)
#                     else:
#                         print(f"⚠️ Geocoding failed for {address}: {geocoding_data.get('status')}")
#                         if geocoding_data.get('error_message'):
#                             print(f"⚠️ Geocoding error: {geocoding_data.get('error_message')}")

#         except Exception as e:
#             print(f"❌ Error during geocoding for {city}, {state}: {e}")

#         # Fallback to Dallas coordinates if geocoding fails
#         print(f"🔄 Falling back to Dallas coordinates for {city}, {state}")
#         return (32.7767, -96.7970)

#     async def _get_coordinates_from_address(self, address: str) -> tuple:
#         """Get coordinates from a full street address using Google Geocoding API"""
#         if not self.google_api_key:
#             print(f"⚠️ No Google API key available for geocoding address: {address}")
#             # Extract city/state from address as fallback
#             parts = address.split(',')
#             if len(parts) >= 2:
#                 city = parts[-2].strip()
#                 state = parts[-1].strip()
#                 return await self._get_coordinates(city, state)
#             else:
#                 return (32.7767, -96.7970)  # Dallas fallback

#         try:
#             import aiohttp

#             # Use Google Geocoding API to get real coordinates
#             geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"

#             params = {
#                 'address': address,
#                 'key': self.google_api_key
#             }

#             print(f"🏠 Geocoding full address: {address}")

#             async with aiohttp.ClientSession() as session:
#                 async with session.get(geocoding_url, params=params) as response:
#                     geocoding_data = await response.json()
#                     print(f"🏠 Address Geocoding API Response: status={geocoding_data.get('status')}")

#                     if (geocoding_data.get('status') == 'OK' and
#                         geocoding_data.get('results') and
#                         len(geocoding_data['results']) > 0):

#                         location = geocoding_data['results'][0]['geometry']['location']
#                         lat = location['lat']
#                         lng = location['lng']

#                         print(f"✅ Successfully geocoded address to ({lat}, {lng})")
#                         return (lat, lng)
#                     else:
#                         print(f"⚠️ Address geocoding failed: {geocoding_data.get('status')}")
#                         if geocoding_data.get('error_message'):
#                             print(f"⚠️ Address geocoding error: {geocoding_data.get('error_message')}")

#         except Exception as e:
#             print(f"❌ Error during address geocoding: {e}")

#         # Fallback to city/state geocoding if full address fails
#         parts = address.split(',')
#         if len(parts) >= 2:
#             city = parts[-2].strip()
#             state = parts[-1].strip()
#             print(f"🔄 Falling back to city geocoding: {city}, {state}")
#             return await self._get_coordinates(city, state)
#         else:
#             print(f"🔄 Falling back to Dallas coordinates for unparseable address: {address}")
#             return (32.7767, -96.7970)

#     def _generate_data_based_fallback(self, insights_data: Dict[str, Any], city: str, state: str) -> Dict[str, str]:
#         """Generate fallback insights based on API data when OpenAI is unavailable"""

#         neighborhood = insights_data.get('neighborhood', {})
#         commute = insights_data.get('commute', {})
#         lifestyle = insights_data.get('lifestyle', {})
#         schools = insights_data.get('schools', {})

#         # Format insights based on actual data
#         walk_score = neighborhood.get('walkability', {}).get('walk_score', 50)
#         drive_time = commute.get('driving_to_downtown', '25 mins')
#         grocery_count = lifestyle.get('grocery_options', 2)
#         school_rating = schools.get('district_rating', 7.0)

#         return {
#             'neighborhood': f"Walk Score {walk_score}/100, {'very walkable' if walk_score > 70 else 'car-dependent'} area",
#             'commute': drive_time if 'drive to downtown' in drive_time else f"{drive_time}, limited transit",
#             'lifestyle': lifestyle.get('lifestyle_insight', f"{grocery_count} grocery stores, {lifestyle.get('dining_options', 5)} restaurants nearby"),
#             'schools': f"District rated {school_rating}/10, {'excellent' if school_rating > 8 else 'good' if school_rating > 6 else 'average'} schools"
#         }

#     def _parse_insights(self, ai_response: str) -> Dict[str, str]:
#         """Parse AI response into structured insights"""
#         insights = {
#             "neighborhood": "Mixed residential area with local character",
#             "commute": "Varies by destination, check local traffic patterns",
#             "lifestyle": "Standard amenities available in surrounding area",
#             "schools": "Research local school districts and ratings"
#         }

#         lines = ai_response.split('\n')
#         for line in lines:
#             line = line.strip()
#             if '🏡 Neighborhood:' in line:
#                 insights["neighborhood"] = line.replace('- 🏡 Neighborhood:', '').strip()
#             elif '🚗 Commute:' in line:
#                 insights["commute"] = line.replace('- 🚗 Commute:', '').strip()
#             elif '🛒 Lifestyle:' in line:
#                 insights["lifestyle"] = line.replace('- 🛒 Lifestyle:', '').strip()
#             elif '🎓 Schools:' in line:
#                 insights["schools"] = line.replace('- 🎓 Schools:', '').strip()

#         return insights

#     def _generate_fallback_insights(self, city: str, state: str, property_type: str, search_type: str) -> Dict[str, str]:
#         """Generate reasonable fallback insights when AI is unavailable"""

#         # Basic insights based on available data
#         location_type = "urban" if any(word in city.lower() for word in ["downtown", "city", "metro"]) else "suburban"

#         fallback_insights = {
#             "neighborhood": f"{'Urban' if location_type == 'urban' else 'Suburban'} area in {city}, check local vibe",
#             "commute": f"Typical {location_type} commute patterns, research your route",
#             "lifestyle": f"Standard {location_type} amenities and services nearby",
#             "schools": f"Research {city} school district ratings and boundaries"
#         }

#         # Customize based on known major cities
#         if city.lower() in ["dallas", "austin", "houston", "san antonio"]:
#             fallback_insights["commute"] = "Texas traffic, plan for rush hour delays"
#             fallback_insights["lifestyle"] = "Good mix of dining, shopping, and entertainment"
#         elif city.lower() in ["new york", "manhattan", "brooklyn"]:
#             fallback_insights["commute"] = "Public transit available, walk score varies by area"
#             fallback_insights["lifestyle"] = "Urban amenities, dining, and cultural options"
#         elif city.lower() in ["los angeles", "la", "santa monica", "beverly hills"]:
#             fallback_insights["commute"] = "Car-dependent, consider traffic and parking"
#             fallback_insights["lifestyle"] = "California lifestyle with outdoor activities"

#         return fallback_insights


# # Global service instance
# ai_insights_service = AIInsightsService()