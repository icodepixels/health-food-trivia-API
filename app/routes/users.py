from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from databases import Database
from app.database import get_db
from app.models.schemas import (
    UserCreate, User, QuizResult, QuizResultResponse,
    UserStatsResponse
)
import json
from datetime import datetime

router = APIRouter()

@router.post("/users", response_model=Dict)
async def create_user(user: UserCreate, db: Database = Depends(get_db)):
    """Create a new user or return existing user"""
    try:
        # Check if user exists
        query = "SELECT id FROM users WHERE email = :email"
        existing_user = await db.fetch_one(query=query, values={"email": user.email})

        if existing_user:
            return {
                'success': False,
                'message': 'User already exists',
                'user_id': existing_user['id']
            }

        # Create new user
        query = """
            INSERT INTO users (email, created_at)
            VALUES (:email, :created_at)
        """
        values = {
            "email": user.email,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        user_id = await db.execute(query=query, values=values)

        return {
            'success': True,
            'message': 'User created successfully',
            'user_id': user_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{email}/results", response_model=Dict)
async def save_quiz_result(email: str, result: QuizResult, db: Database = Depends(get_db)):
    """Save a quiz result for a user"""
    try:
        # Get user ID
        query = "SELECT id FROM users WHERE email = :email"
        user = await db.fetch_one(query=query, values={"email": email})

        if not user:
            # Create user if they don't exist
            create_user_query = """
                INSERT INTO users (email, created_at)
                VALUES (:email, :created_at)
            """
            values = {
                "email": email,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            user_id = await db.execute(query=create_user_query, values=values)
        else:
            user_id = user['id']

        # Save quiz result
        query = """
            INSERT INTO quiz_results (user_id, quiz_id, score, answers, completed_at)
            VALUES (:user_id, :quiz_id, :score, :answers, :completed_at)
        """
        values = {
            "user_id": user_id,
            "quiz_id": result.quiz_id,
            "score": result.score,
            "answers": json.dumps(result.answers),
            "completed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        result_id = await db.execute(query=query, values=values)

        return {
            'success': True,
            'message': 'Quiz result saved successfully',
            'result_id': result_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{email}/results")
async def get_user_results(email: str, db: Database = Depends(get_db)):
    """Get all quiz results for a user"""
    try:
        # Get user ID
        query = "SELECT id FROM users WHERE email = :email"
        user = await db.fetch_one(query=query, values={"email": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all results with quiz details
        query = """
            SELECT
                qr.id as result_id,
                qr.score,
                qr.answers,
                qr.completed_at,
                q.id as quiz_id,
                q.name as quiz_name,
                q.category,
                q.difficulty
            FROM quiz_results qr
            JOIN quiz q ON qr.quiz_id = q.id
            WHERE qr.user_id = :user_id
            ORDER BY qr.completed_at DESC
        """
        results = await db.fetch_all(query=query, values={"user_id": user['id']})

        # Format results
        formatted_results = []
        for result in results:
            result_dict = dict(result)
            if 'answers' in result_dict:
                result_dict['answers'] = json.loads(result_dict['answers'])
            formatted_results.append(result_dict)

        return {
            'email': email,
            'results': formatted_results,
            'total_results': len(formatted_results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{email}/stats", response_model=Dict)
async def get_user_stats(email: str, db: Database = Depends(get_db)):
    """Get user statistics across all quizzes"""
    try:
        # Get user ID
        query = "SELECT id FROM users WHERE email = :email"
        user = await db.fetch_one(query=query, values={"email": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get overall stats
        stats_query = """
            SELECT
                COUNT(*) as total_quizzes,
                AVG(score) as average_score,
                MAX(score) as highest_score,
                MIN(score) as lowest_score,
                COUNT(DISTINCT quiz_id) as unique_quizzes
            FROM quiz_results
            WHERE user_id = :user_id
        """
        stats = await db.fetch_one(stats_query, values={"user_id": user['id']})

        # Get category breakdown
        categories_query = """
            SELECT
                q.category,
                COUNT(*) as quizzes_taken,
                AVG(qr.score) as average_score
            FROM quiz_results qr
            JOIN quiz q ON qr.quiz_id = q.id
            WHERE qr.user_id = :user_id
            GROUP BY q.category
        """
        categories = await db.fetch_all(categories_query, values={"user_id": user['id']})

        return {
            'email': email,
            'overall_stats': dict(stats) if stats else {
                'total_quizzes': 0,
                'average_score': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'unique_quizzes': 0
            },
            'category_stats': [dict(cat) for cat in categories]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))