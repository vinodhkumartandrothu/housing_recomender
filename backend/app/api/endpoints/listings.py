from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...core.database import get_db
from ...models.listing import Listing

router = APIRouter()


@router.get("/listings")
async def get_listings(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all listings from database with pagination"""
    listings = db.query(Listing).offset(offset).limit(limit).all()
    total = db.query(Listing).count()

    return {
        "listings": listings,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/listings/{listing_id}/analyze")
async def analyze_listing(
    listing_id: int,
    db: Session = Depends(get_db)
):
    """Generate AI analysis (pros/cons) for a specific listing"""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Placeholder for AI analysis - will implement with OpenAI later
    ai_analysis = {
        "summary": f"Analysis for {listing.title}",
        "pros": [
            "Good location",
            "Reasonable price for the area",
            "Good square footage"
        ],
        "cons": [
            "May need updates",
            "Limited parking information",
            "No recent photos"
        ]
    }

    # Update listing with AI analysis
    listing.ai_summary = ai_analysis["summary"]
    listing.pros = ai_analysis["pros"]
    listing.cons = ai_analysis["cons"]

    db.commit()
    db.refresh(listing)

    return {
        "listing_id": listing_id,
        "analysis": ai_analysis,
        "message": "AI analysis generated successfully"
    }