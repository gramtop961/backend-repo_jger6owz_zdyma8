import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


class SchoolImageIn(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    tags: Optional[List[str]] = []
    approved: bool = True


@app.get("/api/school-images")
def school_images(limit: int = 12):
    """
    Returns a list of approved school image URLs from the database.
    Falls back to neutral placeholders if none exist yet.
    """
    try:
        images = []
        if db is not None:
            docs = get_documents("schoolimage", {"approved": True}, limit=limit)
            for d in docs:
                images.append({
                    "url": d.get("url"),
                    "title": d.get("title"),
                    "tags": d.get("tags", [])
                })
        
        # Fallback placeholders if DB empty
        if not images:
            placeholders = [
                {
                    "url": "https://images.unsplash.com/photo-1460518451285-97b6aa326961?q=80&w=1600&auto=format&fit=crop",
                    "title": "Campus lawn (placeholder)",
                    "tags": ["campus", "placeholder"]
                },
                {
                    "url": "https://images.unsplash.com/photo-1523580846011-d3a5bc25702b?q=80&w=1600&auto=format&fit=crop",
                    "title": "Courtyard (placeholder)",
                    "tags": ["courtyard", "placeholder"]
                },
                {
                    "url": "https://images.unsplash.com/photo-1562774053-701939374585?q=80&w=1600&auto=format&fit=crop",
                    "title": "Hallway (placeholder)",
                    "tags": ["hallway", "placeholder"]
                }
            ]
            images = placeholders
        
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/school-images")
def add_school_image(payload: SchoolImageIn):
    """
    Add a new school image URL to the database. Returns the created id.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        new_id = create_document("schoolimage", payload.model_dump())
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db as _db
        
        if _db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = _db.name if hasattr(_db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = _db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
