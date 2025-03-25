from fastapi import APIRouter, HTTPException
from typing import List
from app.database import get_db_connection

router = APIRouter()

@router.get("/api/categories", response_model=List[str])
async def get_categories():
    """Get all unique category names"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT category FROM quiz ORDER BY category")
        categories = cursor.fetchall()

        return [category['category'] for category in categories]
    finally:
        conn.close()