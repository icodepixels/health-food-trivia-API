from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from databases import Database
from app.database import get_db
from app.models.schemas import Quiz, QuizCreate, Question, QuestionCreate, QuizWithQuestions
import sqlite3
from datetime import datetime
import json
import traceback

router = APIRouter()

@router.get("/quizzes",
    response_model=List[Quiz],
    summary="Get all quizzes",
    description="Retrieve all quizzes, optionally filtered by category"
)
async def get_quizzes(
    category: Optional[str] = None,
    db: Database = Depends(get_db)
):
    try:
        if category:
            query = "SELECT * FROM quiz WHERE category = :category"
            quizzes = await db.fetch_all(query=query, values={"category": category})
        else:
            query = "SELECT * FROM quiz"
            quizzes = await db.fetch_all(query=query)

        # Convert the results to a list of dictionaries
        return [dict(quiz) for quiz in quizzes]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.post("/quizzes",
    response_model=Quiz,
    status_code=201,
    summary="Create a new quiz",
    description="Create a new quiz with the provided details"
)
async def create_quiz(
    quiz: QuizCreate,
    db: Database = Depends(get_db)
):
    try:
        current_time = datetime.now().date().isoformat()  # Format as YYYY-MM-DD

        query = """
            INSERT INTO quiz (name, description, image, category, difficulty, created_at)
            VALUES (:name, :description, :image, :category, :difficulty, :created_at)
        """
        values = {
            **quiz.dict(),
            "created_at": current_time
        }

        quiz_id = await db.execute(query=query, values=values)

        # Fetch the created quiz
        fetch_query = "SELECT * FROM quiz WHERE id = :id"
        created_quiz = await db.fetch_one(fetch_query, values={"id": quiz_id})

        return dict(created_quiz)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create quiz: {str(e)}"
        )

@router.delete("/quizzes/{quiz_id}", status_code=200)
async def delete_quiz(quiz_id: int, db: Database = Depends(get_db)):
    """Delete a quiz and its questions"""
    try:
        conn = await db.connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM quiz WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")

        conn.execute("BEGIN TRANSACTION")
        cursor.execute("DELETE FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions_deleted = cursor.rowcount
        cursor.execute("DELETE FROM quiz WHERE id = ?", (quiz_id,))

        conn.commit()

        return {
            "success": True,
            "message": f"Quiz with ID {quiz_id} was deleted successfully",
            "questions_deleted": questions_deleted
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quizzes/with-questions")
async def create_quiz_with_questions(
    data: Dict,
    db: Database = Depends(get_db)
):
    """Create a new quiz with questions"""
    try:
        if 'quiz' not in data:
            raise HTTPException(status_code=400, detail="Missing quiz data")
        if 'questions' not in data or not isinstance(data['questions'], list):
            raise HTTPException(status_code=400, detail="Missing or invalid questions array")

        quiz_data = data['quiz']
        questions_data = data['questions']

        # Create quiz
        quiz_query = """
            INSERT INTO quiz (name, description, image, category, difficulty, created_at)
            VALUES (:name, :description, :image, :category, :difficulty, :created_at)
        """
        quiz_values = {
            **quiz_data,
            "created_at": datetime.now().strftime('%Y-%m-%d')
        }

        quiz_id = await db.execute(query=quiz_query, values=quiz_values)

        # Insert questions
        inserted_questions = []
        for question in questions_data:
            question['quiz_id'] = quiz_id
            choices_json = json.dumps(question['choices'])

            question_query = """
                INSERT INTO questions (
                    quiz_id, question_text, choices, correct_answer_index,
                    explanation, category, difficulty, image
                ) VALUES (
                    :quiz_id, :question_text, :choices, :correct_answer_index,
                    :explanation, :category, :difficulty, :image
                )
            """
            question_values = {
                **question,
                "choices": choices_json
            }

            question_id = await db.execute(query=question_query, values=question_values)

            # Fetch the created question
            fetch_query = "SELECT * FROM questions WHERE id = :id"
            new_question = await db.fetch_one(
                query=fetch_query,
                values={"id": question_id}
            )

            question_dict = dict(new_question)
            question_dict['choices'] = json.loads(question_dict['choices'])
            inserted_questions.append(question_dict)

        # Fetch the created quiz
        fetch_quiz_query = "SELECT * FROM quiz WHERE id = :id"
        created_quiz = await db.fetch_one(
            query=fetch_quiz_query,
            values={"id": quiz_id}
        )

        return {
            'success': True,
            'quiz': dict(created_quiz),
            'questions': inserted_questions,
            'total_questions': len(inserted_questions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quizzes/category-samples",
    response_model=Dict,
    summary="Get sample quizzes by category",
    description="Retrieve random quizzes from each category"
)
async def get_category_samples(
    limit: int = Query(default=3, description="Number of quizzes per category"),
    db: Database = Depends(get_db)
):
    try:
        # Get all unique categories
        categories_query = "SELECT DISTINCT category FROM quiz ORDER BY category"
        categories = await db.fetch_all(query=categories_query)

        result = {}
        for category_row in categories:
            category = category_row['category']
            # Get random quizzes for this category
            quizzes_query = """
                SELECT * FROM quiz
                WHERE category = :category
                ORDER BY RANDOM()
                LIMIT :limit
            """
            quizzes = await db.fetch_all(
                query=quizzes_query,
                values={"category": category, "limit": limit}
            )

            result[category] = [dict(quiz) for quiz in quizzes]

        return {
            'success': True,
            'samples': result,
            'total_categories': len(categories),
            'quizzes_per_category': limit
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching category samples: {str(e)}"
        )