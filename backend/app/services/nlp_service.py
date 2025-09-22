import openai
from typing import Dict, List
from ..core.config import settings


def analyze_listing(description: str) -> Dict[str, any]:
    """
    Analyze a property listing using OpenAI GPT to extract insights

    Args:
        description: Property description text to analyze

    Returns:
        Dictionary with ai_summary, pros, and cons
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")

    if not description or not description.strip():
        return {
            "ai_summary": "No description provided for analysis",
            "pros": [],
            "cons": ["No description available"]
        }

    client = openai.OpenAI(api_key=settings.openai_api_key)

    prompt = f"""
    Analyze this real estate listing description and provide insights for potential buyers/renters.

    Description: {description}

    Please provide:
    1. A brief summary (2-3 sentences)
    2. Top 3-5 pros/advantages
    3. Top 3-5 cons/potential concerns

    Respond in this exact JSON format:
    {{
        "ai_summary": "Brief summary here",
        "pros": ["Pro 1", "Pro 2", "Pro 3"],
        "cons": ["Con 1", "Con 2", "Con 3"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a real estate expert helping analyze property listings. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        # Try to parse JSON response
        import json
        try:
            result = json.loads(content)
            return {
                "ai_summary": result.get("ai_summary", "Analysis completed"),
                "pros": result.get("pros", []),
                "cons": result.get("cons", [])
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "ai_summary": "AI analysis completed but formatting error occurred",
                "pros": ["Analysis available in raw format"],
                "cons": ["Could not parse structured analysis"]
            }

    except Exception as e:
        return {
            "ai_summary": f"Error during AI analysis: {str(e)}",
            "pros": [],
            "cons": ["AI analysis failed"]
        }


def generate_search_insights(listings: List[Dict]) -> Dict[str, any]:
    """
    Generate insights about a collection of listings

    Args:
        listings: List of property listings

    Returns:
        Dictionary with market insights and recommendations
    """
    if not settings.openai_api_key:
        return {"error": "OpenAI API key not configured"}

    if not listings:
        return {
            "market_summary": "No listings available for analysis",
            "recommendations": []
        }

    client = openai.OpenAI(api_key=settings.openai_api_key)

    # Prepare listings summary for analysis
    listings_summary = []
    for listing in listings[:10]:  # Limit to first 10 for token efficiency
        summary = {
            "price": listing.get("price"),
            "bedrooms": listing.get("bedrooms"),
            "bathrooms": listing.get("bathrooms"),
            "city": listing.get("city"),
            "title": listing.get("title", "")[:100]  # Truncate long titles
        }
        listings_summary.append(summary)

    prompt = f"""
    Analyze these real estate listings and provide market insights:

    Listings: {listings_summary}

    Please provide:
    1. Market summary (2-3 sentences about pricing and availability)
    2. Top 3 recommendations for buyers/renters

    Respond in JSON format:
    {{
        "market_summary": "Summary here",
        "recommendations": ["Rec 1", "Rec 2", "Rec 3"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a real estate market analyst. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "market_summary": "Market analysis completed",
                "recommendations": ["Analysis available"]
            }

    except Exception as e:
        return {
            "market_summary": f"Error in market analysis: {str(e)}",
            "recommendations": []
        }