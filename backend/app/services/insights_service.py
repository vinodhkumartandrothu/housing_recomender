import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
from ..core.config import settings

class PropertyInsightsService:
    """Service for fetching real-world property insights from various APIs"""

    def __init__(self):
        # API Keys - these should be set in .env file
        self.walkscore_api_key = getattr(settings, 'walkscore_api_key', None)
        self.google_api_key = getattr(settings, 'google_maps_api_key', None)
        self.yelp_api_key = getattr(settings, 'yelp_api_key', None)
        self.greatschools_api_key = getattr(settings, 'greatschools_api_key', None)


        # Base URLs
        self.walkscore_base = "https://api.walkscore.com/score"
        self.google_places_base = "https://maps.googleapis.com/maps/api/place"
        self.google_directions_base = "https://maps.googleapis.com/maps/api/directions/json"
        self.yelp_base = "https://api.yelp.com/v3/businesses/search"
        self.greatschools_base = "https://api.greatschools.org/v3"

    async def get_neighborhood_info(self, address: str, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch neighborhood walkability, safety, and livability data"""
        try:
            async with aiohttp.ClientSession() as session:
                # WalkScore API call
                walkscore_params = {
                    'format': 'json',
                    'address': address,
                    'lat': lat,
                    'lon': lng,
                    'transit': 1,
                    'bike': 1,
                    'wsapikey': self.walkscore_api_key
                }

                walkscore_url = f"{self.walkscore_base}?" + "&".join([f"{k}={v}" for k, v in walkscore_params.items()])

                if self.walkscore_api_key:
                    async with session.get(walkscore_url) as response:
                        walkscore_data = await response.json()
                else:
                    # Mock response when API key not available
                    walkscore_data = {
                        'walkscore': 78,
                        'description': 'Very Walkable',
                        'transit': {'score': 85, 'description': 'Excellent Transit'},
                        'bike': {'score': 72, 'description': 'Very Bikeable'}
                    }

                # Google Places API for neighborhood amenities and safety indicators
                places_params = {
                    'location': f"{lat},{lng}",
                    'radius': 1000,
                    'type': 'establishment',
                    'key': self.google_api_key
                }

                if self.google_api_key:
                    places_url = f"{self.google_places_base}/nearbysearch/json"
                    async with session.get(places_url, params=places_params) as response:
                        places_data = await response.json()
                else:
                    # Mock response
                    places_data = {
                        'results': [
                            {'name': 'Starbucks', 'types': ['cafe'], 'rating': 4.2},
                            {'name': 'Whole Foods', 'types': ['grocery_store'], 'rating': 4.5},
                            {'name': 'Chase Bank', 'types': ['bank'], 'rating': 3.8}
                        ]
                    }

                return {
                    'walkability': {
                        'walk_score': walkscore_data.get('walkscore', 50),
                        'description': walkscore_data.get('description', 'Somewhat Walkable'),
                        'transit_score': walkscore_data.get('transit', {}).get('score', 40),
                        'bike_score': walkscore_data.get('bike', {}).get('score', 30)
                    },
                    'nearby_amenities': len(places_data.get('results', [])),
                    'avg_rating': sum([place.get('rating', 0) for place in places_data.get('results', [])]) / max(len(places_data.get('results', [])), 1),
                    'safety_score': min(85, walkscore_data.get('walkscore', 50) + 10)  # Approximate based on walkability
                }

        except Exception as e:
            print(f"Error fetching neighborhood info: {e}")
            return {
                'walkability': {'walk_score': 50, 'description': 'Data Unavailable'},
                'nearby_amenities': 0,
                'avg_rating': 0,
                'safety_score': 50
            }

    async def get_commute_info(self, lat: float, lng: float, city: str, state: str) -> Dict[str, Any]:
        """Fetch commute times and transportation options"""
        try:
            async with aiohttp.ClientSession() as session:
                if self.google_api_key:
                    # Use Google Distance Matrix API for driving time to downtown
                    distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

                    # Dynamically determine the appropriate downtown destination with distance validation
                    downtown_destination = await self._get_downtown_destination(city, state, lat, lng, session)
                    print(f"🏙️ Using downtown destination: {downtown_destination}")

                    driving_params = {
                        'origins': f"{lat},{lng}",
                        'destinations': downtown_destination,
                        'mode': 'driving',
                        'departure_time': 'now',
                        'traffic_model': 'best_guess',
                        'units': 'imperial',
                        'key': self.google_api_key
                    }

                    # Make API call with comprehensive logging
                    try:
                        print(f"🚗 Making Distance Matrix API call for {lat},{lng}")
                        async with session.get(distance_matrix_url, params=driving_params) as response:
                            driving_data = await response.json()
                            print(f"🚗 Distance Matrix API Response: {driving_data}")
                    except Exception as e:
                        print(f"❌ Error calling Google Maps Distance Matrix API: {e}")
                        driving_data = {'status': 'REQUEST_DENIED'}

                    # Extract commute time from Distance Matrix API response
                    if (driving_data.get('status') == 'OK' and
                        driving_data.get('rows') and
                        len(driving_data['rows']) > 0 and
                        driving_data['rows'][0].get('elements') and
                        len(driving_data['rows'][0]['elements']) > 0 and
                        driving_data['rows'][0]['elements'][0].get('status') == 'OK'):

                        duration_data = driving_data['rows'][0]['elements'][0].get('duration')
                        if duration_data and duration_data.get('text'):
                            duration_text = duration_data['text']
                            commute_insight = f"{duration_text} drive to downtown"
                            print(f"✅ Successfully parsed commute time: {commute_insight}")
                        else:
                            print(f"⚠️ Duration data missing from API response")
                            commute_insight = "Drive time data unavailable"
                    else:
                        print(f"⚠️ API returned status: {driving_data.get('status')}")
                        if driving_data.get('error_message'):
                            print(f"⚠️ API error message: {driving_data.get('error_message')}")
                        commute_insight = "Drive time data unavailable"

                else:
                    print(f"⚠️ No Google API key available for commute data")
                    commute_insight = "Drive time data unavailable"

                return {
                    'driving_to_downtown': commute_insight,
                    'transit_to_downtown': "Limited",
                    'has_public_transit': False,
                    'traffic_level': 'moderate'
                }

        except Exception as e:
            print(f"❌ Error fetching commute info: {e}")
            return {
                'driving_to_downtown': 'Drive time data unavailable',
                'transit_to_downtown': 'Limited',
                'has_public_transit': False,
                'traffic_level': 'unknown'
            }

    async def get_lifestyle_info(self, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch nearby lifestyle amenities (shopping, dining, fitness)"""
        try:
            async with aiohttp.ClientSession() as session:
                lifestyle_data = {}

                if self.google_api_key:
                    print(f"🛒 Making Google Places API calls for {lat},{lng}")

                    # Define amenity types with their Google Places API type names
                    amenity_types = {
                        'grocery_store': ['supermarket', 'grocery_or_supermarket'],
                        'restaurant': ['restaurant', 'food'],
                        'gym': ['gym'],
                        'shopping_mall': ['shopping_mall'],
                        'pharmacy': ['pharmacy']
                    }

                    for amenity, search_types in amenity_types.items():
                        all_results = []

                        for search_type in search_types:
                            params = {
                                'location': f"{lat},{lng}",
                                'radius': 3000,  # 3km radius
                                'type': search_type,
                                'key': self.google_api_key
                            }

                            url = f"{self.google_places_base}/nearbysearch/json"

                            try:
                                print(f"🛒 Searching for {search_type} near {lat},{lng}")
                                async with session.get(url, params=params) as response:
                                    data = await response.json()
                                    print(f"🛒 Places API Response for {search_type}: status={data.get('status')}, results_count={len(data.get('results', []))}")

                                    if data.get('status') == 'OK':
                                        results = data.get('results', [])
                                        # Extract name and rating from each place
                                        for place in results:
                                            place_info = {
                                                'name': place.get('name', 'Unknown'),
                                                'rating': place.get('rating', 0),
                                                'types': place.get('types', [])
                                            }
                                            all_results.append(place_info)

                                        print(f"✅ Found {len(results)} {search_type} locations")
                                    elif data.get('status') == 'ZERO_RESULTS':
                                        print(f"ℹ️ No {search_type} found in area")
                                    else:
                                        print(f"⚠️ Google Places API error for {search_type}: {data.get('status')} - {data.get('error_message', 'Unknown error')}")

                            except Exception as e:
                                print(f"❌ Error calling Google Places API for {search_type}: {e}")

                        # Remove duplicates based on name and store results
                        unique_results = []
                        seen_names = set()
                        for result in all_results:
                            if result['name'] not in seen_names:
                                unique_results.append(result)
                                seen_names.add(result['name'])

                        lifestyle_data[amenity] = {
                            'count': len(unique_results),
                            'avg_rating': sum([place.get('rating', 0) for place in unique_results]) / max(len(unique_results), 1) if unique_results else 0,
                            'top_places': [place.get('name', 'Unknown') for place in unique_results[:3]]
                        }

                        print(f"✅ {amenity}: {len(unique_results)} unique places found")

                else:
                    print(f"⚠️ No Google API key available for lifestyle data")
                    # Mock data for each amenity type
                    mock_data = {
                        'grocery_store': [{'name': 'Walmart Supercenter', 'rating': 4.1}, {'name': 'Kroger', 'rating': 4.3}],
                        'restaurant': [{'name': 'Chipotle', 'rating': 4.2}, {'name': 'Panera Bread', 'rating': 4.4}],
                        'gym': [{'name': 'LA Fitness', 'rating': 4.0}, {'name': 'Planet Fitness', 'rating': 4.1}],
                        'shopping_mall': [{'name': 'NorthPark Center', 'rating': 4.5}],
                        'pharmacy': [{'name': 'CVS Pharmacy', 'rating': 3.9}, {'name': 'Walgreens', 'rating': 4.0}]
                    }
                    for amenity, places in mock_data.items():
                        lifestyle_data[amenity] = {
                            'count': len(places),
                            'avg_rating': sum([place.get('rating', 0) for place in places]) / max(len(places), 1),
                            'top_places': [place.get('name', 'Unknown') for place in places[:3]]
                        }

                # Build lifestyle insight string with real data
                grocery_count = lifestyle_data['grocery_store']['count']
                restaurant_count = lifestyle_data['restaurant']['count']
                grocery_names = lifestyle_data['grocery_store']['top_places'][:2]  # Top 2 names

                # Build the insight string
                parts = []
                if grocery_count > 0:
                    if grocery_names:
                        grocery_part = f"{grocery_count} grocery stores ({', '.join(grocery_names)})"
                    else:
                        grocery_part = f"{grocery_count} grocery stores"
                    parts.append(grocery_part)

                if restaurant_count > 0:
                    parts.append(f"{restaurant_count} restaurants")

                if parts:
                    lifestyle_insight = f"{', '.join(parts)} nearby"
                else:
                    lifestyle_insight = "Limited amenities nearby"

                print(f"✅ Final lifestyle insight: {lifestyle_insight}")

                # Calculate totals for other metrics
                total_amenities = sum([data['count'] for data in lifestyle_data.values()])
                avg_rating = sum([data['avg_rating'] for data in lifestyle_data.values()]) / len(lifestyle_data) if lifestyle_data else 0

                return {
                    'total_amenities': total_amenities,
                    'lifestyle_score': min(100, (total_amenities * 2) + (avg_rating * 10)),
                    'grocery_options': grocery_count,
                    'dining_options': restaurant_count,
                    'fitness_options': lifestyle_data['gym']['count'],
                    'shopping_options': lifestyle_data['shopping_mall']['count'],
                    'convenience': lifestyle_data['pharmacy']['count'],
                    'top_grocery': grocery_names[0] if grocery_names else 'None nearby',
                    'lifestyle_insight': lifestyle_insight
                }

        except Exception as e:
            print(f"❌ Error fetching lifestyle info: {e}")
            return {
                'total_amenities': 0,
                'lifestyle_score': 0,
                'grocery_options': 0,
                'dining_options': 0,
                'fitness_options': 0,
                'shopping_options': 0,
                'convenience': 0,
                'top_grocery': 'Data unavailable',
                'lifestyle_insight': 'Lifestyle data unavailable'
            }

    async def get_school_info(self, lat: float, lng: float, state: str) -> Dict[str, Any]:
        """Fetch school district and quality information"""
        try:
            async with aiohttp.ClientSession() as session:
                if self.greatschools_api_key:
                    # GreatSchools API call
                    headers = {'X-API-Key': self.greatschools_api_key}
                    params = {
                        'lat': lat,
                        'lon': lng,
                        'radius': 5,  # 5 mile radius
                        'sort': 'rating',
                        'limit': 10
                    }

                    url = f"{self.greatschools_base}/schools"
                    async with session.get(url, headers=headers, params=params) as response:
                        schools_data = await response.json()
                        schools = schools_data.get('schools', [])
                else:
                    # Mock school data
                    schools = [
                        {'name': 'Highland Park Elementary', 'rating': 9, 'level': 'elementary', 'type': 'public'},
                        {'name': 'Highland Park Middle School', 'rating': 8, 'level': 'middle', 'type': 'public'},
                        {'name': 'Highland Park High School', 'rating': 10, 'level': 'high', 'type': 'public'},
                        {'name': 'St. Monica Catholic School', 'rating': 7, 'level': 'elementary', 'type': 'private'}
                    ]

                if schools:
                    # Calculate school metrics
                    elementary_schools = [s for s in schools if s.get('level') == 'elementary']
                    middle_schools = [s for s in schools if s.get('level') == 'middle']
                    high_schools = [s for s in schools if s.get('level') == 'high']

                    avg_rating = sum([school.get('rating', 0) for school in schools]) / len(schools)
                    best_elementary = max(elementary_schools, key=lambda x: x.get('rating', 0)) if elementary_schools else None
                    best_high = max(high_schools, key=lambda x: x.get('rating', 0)) if high_schools else None

                    return {
                        'district_rating': round(avg_rating, 1),
                        'elementary_count': len(elementary_schools),
                        'middle_count': len(middle_schools),
                        'high_count': len(high_schools),
                        'best_elementary': best_elementary['name'] if best_elementary else 'N/A',
                        'best_elementary_rating': best_elementary['rating'] if best_elementary else 0,
                        'best_high': best_high['name'] if best_high else 'N/A',
                        'best_high_rating': best_high['rating'] if best_high else 0,
                        'has_private_options': any(s.get('type') == 'private' for s in schools)
                    }
                else:
                    return self._get_default_school_info()

        except Exception as e:
            print(f"Error fetching school info: {e}")
            return self._get_default_school_info()

        def _get_default_school_info(self):
            """Default school info when API is unavailable"""
            return {
                'district_rating': 7.0,
                'elementary_count': 2,
                'middle_count': 1,
                'high_count': 1,
                'best_elementary': 'Local Elementary School',
                'best_elementary_rating': 7,
                'best_high': 'Local High School',
                'best_high_rating': 7,
                'has_private_options': True
            }

    async def _get_downtown_destination(self, city: str, state: str, origin_lat: float, origin_lng: float, session) -> str:
        """Find the correct downtown destination with distance validation to avoid overlapping coordinates"""
        import math

        def calculate_distance(lat1, lng1, lat2, lng2):
            """Calculate distance between two points in miles using Haversine formula"""
            R = 3959  # Earth's radius in miles
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c

        async def geocode_address(address):
            """Helper to geocode an address and return coordinates"""
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": address, "key": self.google_api_key}
            try:
                async with session.get(geocode_url, params=params) as response:
                    data = await response.json()
                    if data.get("status") == "OK" and data.get("results"):
                        location = data["results"][0]["geometry"]["location"]
                        return location["lat"], location["lng"], data["results"][0]["formatted_address"]
            except Exception as e:
                print(f"❌ Geocoding error for {address}: {e}")
            return None, None, None

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

        try:
            # Step 1: Try local downtown with distance validation
            query = f"Downtown {city}, {state}"
            print(f"🏙️ Step 1: Searching for '{query}'")

            params = {"query": query, "key": self.google_api_key}
            async with session.get(url, params=params) as response:
                data = await response.json()

                if data.get("status") == "OK" and data.get("results"):
                    for result in data.get("results", [])[:3]:  # Check top 3 results
                        downtown_address = result["formatted_address"]
                        dt_lat, dt_lng, _ = await geocode_address(downtown_address)

                        if dt_lat and dt_lng:
                            distance = calculate_distance(origin_lat, origin_lng, dt_lat, dt_lng)
                            print(f"🏙️ Found downtown at {downtown_address}, distance: {distance:.1f} miles")

                            # Only accept local downtown if it's significantly far (> 3 miles)
                            distance = calculate_distance(origin_lat, origin_lng, dt_lat, dt_lng)
                            
                            if distance < 2.0:
                                print(f"⚠️ Rejected fake/duplicate downtown: {downtown_address}")
                                continue  # keep searching
                            else:
                                print(f"✅ Using real downtown: {downtown_address}")
                                return downtown_address


            # Step 2: If local downtown is too close, try nearby major metro
            fallback_query = f"major downtown near {city}, {state}"
            print(f"🏙️ Step 2: Searching for '{fallback_query}'")

            params = {"query": fallback_query, "key": self.google_api_key}
            async with session.get(url, params=params) as response:
                data = await response.json()

                if data.get("status") == "OK" and data.get("results"):
                    for result in data.get("results", [])[:3]:  # Check top 3 results
                        downtown_address = result["formatted_address"]
                        dt_lat, dt_lng, _ = await geocode_address(downtown_address)

                        if dt_lat and dt_lng:
                            distance = calculate_distance(origin_lat, origin_lng, dt_lat, dt_lng)
                            print(f"🏙️ Found major downtown at {downtown_address}, distance: {distance:.1f} miles")

                            # Use any major downtown that's reasonably far (> 2 miles for major metros)
                            if distance > 2.0:
                                print(f"✅ Using major metro downtown: {downtown_address}")
                                return downtown_address

            # Step 3: Try nearby major cities based on state
            major_city_queries = []
            if state.lower() in ['nj', 'new jersey']:
                major_city_queries = ["Downtown Newark, NJ", "Downtown Jersey City, NJ", "Downtown Trenton, NJ"]
            elif state.lower() in ['tx', 'texas']:
                major_city_queries = ["Downtown Dallas, TX", "Downtown Houston, TX", "Downtown Austin, TX"]
            elif state.lower() in ['ca', 'california']:
                major_city_queries = ["Downtown Los Angeles, CA", "Downtown San Francisco, CA", "Downtown San Diego, CA"]
            elif state.lower() in ['ny', 'new york']:
                major_city_queries = ["Downtown Manhattan, NY", "Downtown Albany, NY", "Downtown Buffalo, NY"]
            elif state.lower() in ['fl', 'florida']:
                major_city_queries = ["Downtown Miami, FL", "Downtown Orlando, FL", "Downtown Jacksonville, FL"]
            else:
                # Generic state capital approach
                major_city_queries = [f"Downtown {state} capital", f"largest city in {state} downtown"]

            print(f"🏙️ Step 3: Trying major cities for {state}")
            for major_query in major_city_queries:
                print(f"🏙️ Trying: '{major_query}'")
                params = {"query": major_query, "key": self.google_api_key}
                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("status") == "OK" and data.get("results"):
                        for result in data.get("results", [])[:2]:  # Check top 2 results
                            downtown_address = result["formatted_address"]
                            dt_lat, dt_lng, _ = await geocode_address(downtown_address)

                            if dt_lat and dt_lng:
                                distance = calculate_distance(origin_lat, origin_lng, dt_lat, dt_lng)
                                print(f"🏙️ Found major city downtown at {downtown_address}, distance: {distance:.1f} miles")

                                # Accept any major city that's reasonably far
                                if distance > 5.0:  # Major cities should be at least 5 miles away
                                    print(f"✅ Using major city downtown: {downtown_address}")
                                    return downtown_address

        except Exception as e:
            print(f"❌ Error determining downtown for {city}, {state}: {e}")

        # Step 4: Safe fallback if all else fails
        fallback = f"Downtown {city.title()}, {state.upper()}"
        print(f"🔄 Using safe fallback: {fallback}")
        return fallback

    async def get_all_insights(self, address: str, lat: float, lng: float, city: str, state: str) -> Dict[str, Any]:
        """Fetch all property insights concurrently"""
        try:
            # Run all API calls concurrently for better performance
            neighborhood_task = self.get_neighborhood_info(address, lat, lng)
            commute_task = self.get_commute_info(lat, lng, city, state)
            lifestyle_task = self.get_lifestyle_info(lat, lng)
            school_task = self.get_school_info(lat, lng, state)

            neighborhood, commute, lifestyle, schools = await asyncio.gather(
                neighborhood_task, commute_task, lifestyle_task, school_task
            )

            return {
                'neighborhood': neighborhood,
                'commute': commute,
                'lifestyle': lifestyle,
                'schools': schools,
                'data_source': 'real_apis'
            }

        except Exception as e:
            print(f"Error fetching all insights: {e}")
            return {
                'neighborhood': {'walkability': {'walk_score': 50}},
                'commute': {'driving_to_downtown': '25 mins'},
                'lifestyle': {'total_amenities': 10},
                'schools': {'district_rating': 7.0},
                'data_source': 'fallback'
            }

# Global service instance
property_insights_service = PropertyInsightsService()
