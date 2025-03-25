from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.database import get_db_connection
from app.models.schemas import (
    UserCreate, User, QuizResult, QuizResultResponse,
    UserStatsResponse
)
import json
from datetime import datetime

router = APIRouter()

@router.post("/users", response_model=Dict)
async def create_user(user: UserCreate):
    """Create a new user or update existing user by email"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return {
                'success': False,
                'message': 'User already exists',
                'user_id': existing_user['id']
            }

        cursor.execute('''
            INSERT INTO users (email, created_at)
            VALUES (?, ?)
        ''', (user.email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        new_user_id = cursor.lastrowid

        return {
            'success': True,
            'message': 'User created successfully',
            'user_id': new_user_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.post("/users/{email}/results", response_model=Dict)
async def save_quiz_result(email: str, result: QuizResult):
    """Save a quiz result for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute('''
            INSERT INTO quiz_results (
                user_id, quiz_id, score, answers, completed_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            user['id'],
            result.quiz_id,
            result.score,
            json.dumps(result.answers),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        result_id = cursor.lastrowid

        return {
            'success': True,
            'message': 'Quiz result saved successfully',
            'result_id': result_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/users/{email}/results")
async def get_user_results(email: str):
    """Get all quiz results for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute('''
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
            WHERE qr.user_id = ?
            ORDER BY qr.completed_at DESC
        ''', (user['id'],))

        results = cursor.fetchall()
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
    finally:
        if conn:
            conn.close()

@router.get("/users/{email}/stats", response_model=UserStatsResponse)
async def get_user_stats(email: str):
    """Get user statistics across all quizzes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute('''
            SELECT
                COUNT(*) as total_quizzes,
                AVG(score) as average_score,
                MAX(score) as highest_score,
                MIN(score) as lowest_score,
                COUNT(DISTINCT quiz_id) as unique_quizzes
            FROM quiz_results
            WHERE user_id = ?
        ''', (user['id'],))

        stats = dict(cursor.fetchone())

        cursor.execute('''
            SELECT
                q.category,
                COUNT(*) as quizzes_taken,
                AVG(qr.score) as average_score
            FROM quiz_results qr
            JOIN quiz q ON qr.quiz_id = q.id
            WHERE qr.user_id = ?
            GROUP BY q.category
        ''', (user['id'],))

        category_stats = [dict(cat) for cat in cursor.fetchall()]

        return {
            'email': email,
            'overall_stats': stats,
            'category_stats': category_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()