# Housing Recommender - claude.md

## Project Goal
Build AI-powered housing search that aggregates real estate data and provides smart recommendations with natural language queries.

## Status
- Tech stack decided
- Ready to start building

## Requirements
- Natural language search, e.g. "2 bedroom apartment in Dallas under $2000"
- Data sources: Real estate aggregation (APIs + scraping backup)
- AI insights: pros/cons for each listing
- Output: Top 5–10 ranked recommendations

## Decided Tech Stack
- Backend: FastAPI (Python) + PostgreSQL + Redis
- Data Sources: Estated API (primary) + web scraping backup
- AI/NLP: OpenAI API + Sentence Transformers + spaCy
- Frontend: React + Next.js + Tailwind CSS
- Deployment: Docker + Cloud hosting

## Project Structure
```
housing-recommender/
├── .env
├── requirements.txt
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── listing.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── estated_service.py
│   │   │   ├── nlp_service.py
│   │   │   └── search_service.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── search.py
│   │           └── listings.py
├── data/
│   └── mock_listings.json
└── frontend/
    (planned: React + Next.js + Tailwind)
```

## Next Steps
1. Get Estated API key (FREE – sign up at estated.com/developers)
2. Set up basic FastAPI project structure
3. Implement search + NLP services
4. Build React frontend
5. Deploy and test

## APIs Needed
- Estated API → Real estate data (FREE tier – 1,000 requests/month)
- OpenAI API → AI insights generation

## Rules for Claude
- Always generate minimal working examples (code should run immediately)
- Follow FastAPI project structure: `core/`, `models/`, `services/`, `api/endpoints/`
- Explain code step by step in simple terms
- Add comments inside code for clarity
- When using AI (OpenAI API), summarize listings with pros/cons

## Data Model (Listings)
- id (int, primary key)
- title (string)
- description (text)
- price (float)
- bedrooms (int)
- bathrooms (float)
- square_feet (int)
- city (string)
- state (string)
- url (string, source link)
- source (string: "Estated", "scraper")
- ai_summary (text)
- pros (json)
- cons (json)

## Database Migrations
- Use Alembic for migrations
- After editing models, always run:
  alembic revision --autogenerate -m "update listings model"
  alembic upgrade head

## Endpoints
- GET `/api/v1/search?city=&bedrooms=&max_price=` → Fetch listings from Estated API
- GET `/api/v1/listings` → Return saved listings from DB
- POST `/api/v1/listings/{id}/analyze` → Generate AI pros/cons for a specific listing