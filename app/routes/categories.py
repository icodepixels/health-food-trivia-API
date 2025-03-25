from fastapi import APIRouter, HTTPException, Depends
from typing import List
from databases import Database
from app.database import get_db

# Remove the /api prefix from here since it's added in the main app
router = APIRouter()

@router.get("/categories", response_model=List[str])
async def get_categories(db: Database = Depends(get_db)):
    """Get all unique category names"""
    try:
        query = "SELECT DISTINCT category FROM quiz ORDER BY category"
        categories = await db.fetch_all(query=query)

        # Extract category names from the result
        return [category['category'] for category in categories]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )