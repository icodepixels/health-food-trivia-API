from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from databases import Database
from app.database import get_db
from app.models.schemas import Quiz, QuizCreate, Question, QuestionCreate, QuizWithQuestions
import sqlite3
from datetime import datetime
import json
import traceback

router = APIRouter(
    prefix="/api",
    tags=["quizzes"],
    responses={404: {"description": "Not found"}},
)

@router.get("/quizzes",
    response_model=List[Quiz],
    summary="Get all quizzes",
    description="Retrieve all quizzes, optionally filtered by category"
)
async def get_quizzes(
    category: Optional[str] = None,
    db: Database = Depends(get_db)
):
    if category:
        query = "SELECT * FROM quiz WHERE category = :category"
        quizzes = await db.fetch_all(query=query, values={"category": category})
    else:
        query = "SELECT * FROM quiz"
        quizzes = await db.fetch_all(query=query)

    return [dict(quiz) for quiz in quizzes]

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
    query = """
        INSERT INTO quiz (name, description, image, category, difficulty, created_at)
        VALUES (:name, :description, :image, :category, :difficulty, :created_at)
    """
    values = {
        **quiz.dict(),
        "created_at": datetime.now().strftime('%Y-%m-%d')
    }

    try:
        quiz_id = await db.execute(query=query, values=values)

        # Fetch the created quiz
        fetch_query = "SELECT * FROM quiz WHERE id = :id"
        created_quiz = await db.fetch_one(fetch_query, values={"id": quiz_id})

        return dict(created_quiz)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.route('/quizzes/with-questions', methods=['POST'])
def create_quiz_with_questions():
    """
    Endpoint to create a new quiz along with its questions in a single request.
    Accepts JSON with quiz data and an array of questions.
    """
    data = request.get_json()

    if 'quiz' not in data:
        return jsonify({'error': 'Missing quiz data'}), 400
    if 'questions' not in data or not isinstance(data['questions'], list):
        return jsonify({'error': 'Missing or invalid questions array'}), 400

    quiz_data = data['quiz']
    questions_data = data['questions']

    required_quiz_fields = ['name', 'description', 'image', 'category', 'difficulty']
    for field in required_quiz_fields:
        if field not in quiz_data:
            return jsonify({'error': f'Missing required quiz field: {field}'}), 400

    required_question_fields = ['question_text', 'choices', 'correct_answer_index',
                              'explanation', 'image', 'difficulty', 'category']

    for i, question in enumerate(questions_data):
        missing_fields = [field for field in required_question_fields if field not in question]
        if missing_fields:
            return jsonify({
                'error': f'Question at index {i} is missing required fields: {", ".join(missing_fields)}'
            }), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION")

        current_time = datetime.now().strftime('%Y-%m-%d')

        # Insert the quiz
        cursor.execute('''
            INSERT INTO quiz (name, description, image, category, difficulty, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            quiz_data['name'],
            quiz_data['description'],
            quiz_data['image'],
            quiz_data['category'],
            quiz_data['difficulty'],
            current_time
        ))

        new_quiz_id = cursor.lastrowid

        # Insert all questions
        inserted_questions = []
        for question in questions_data:
            choices_json = json.dumps(question['choices'])

            cursor.execute('''
                INSERT INTO questions (
                    quiz_id, question_text, choices, correct_answer_index,
                    explanation, category, difficulty, image
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_quiz_id,
                question['question_text'],
                choices_json,
                question['correct_answer_index'],
                question['explanation'],
                question['category'],
                question['difficulty'],
                question['image']
            ))

            new_question_id = cursor.lastrowid
            cursor.execute("SELECT * FROM questions WHERE id = ?", (new_question_id,))
            new_question = cursor.fetchone()

            question_dict = {}
            for key in new_question.keys():
                question_dict[key] = new_question[key]
            question_dict['choices'] = json.loads(question_dict['choices'])
            inserted_questions.append(question_dict)

        # Get the created quiz
        cursor.execute("SELECT * FROM quiz WHERE id = ?", (new_quiz_id,))
        new_quiz = cursor.fetchone()
        quiz_result = {}
        for key in new_quiz.keys():
            quiz_result[key] = new_quiz[key]

        conn.commit()

        return jsonify({
            'success': True,
            'quiz': quiz_result,
            'questions': inserted_questions,
            'total_questions': len(inserted_questions)
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        error_details = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500
    finally:
        if conn:
            conn.close()

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