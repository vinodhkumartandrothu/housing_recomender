from sqlalchemy import Column, Integer, String, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from ..core.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Integer)
    city = Column(String, index=True)
    state = Column(String, index=True)
    url = Column(String)
    source = Column(String)  # "Estated", "scraper"
    ai_summary = Column(Text)
    pros = Column(JSON)
    cons = Column(JSON)