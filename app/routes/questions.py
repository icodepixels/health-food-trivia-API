from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from databases import Database
from app.database import get_db
from app.models.schemas import Question, QuestionCreate, QuizWithQuestions
import json
import traceback

router = APIRouter()

@router.post("/questions", response_model=Dict)
async def add_questions(questions: List[QuestionCreate], db: Database = Depends(get_db)):
    """Add multiple questions to quizzes"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        results = []
        errors = []

        for index, question in enumerate(questions):
            try:
                # Verify quiz exists
                cursor.execute("SELECT id FROM quiz WHERE id = ?", (question.quiz_id,))
                quiz = cursor.fetchone()

                if not quiz:
                    errors.append({
                        'index': index,
                        'error': f'Quiz with ID {question.quiz_id} not found'
                    })
                    continue

                choices_json = json.dumps(question.choices)

                cursor.execute('''
                    INSERT INTO questions (
                        quiz_id, question_text, choices, correct_answer_index,
                        explanation, category, difficulty, image
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question.quiz_id,
                    question.question_text,
                    choices_json,
                    question.correct_answer_index,
                    question.explanation,
                    question.category,
                    question.difficulty,
                    question.image
                ))

                new_question_id = cursor.lastrowid
                cursor.execute("SELECT * FROM questions WHERE id = ?", (new_question_id,))
                new_question = dict(cursor.fetchone())
                new_question['choices'] = json.loads(new_question['choices'])
                results.append(new_question)

            except Exception as e:
                errors.append({
                    'index': index,
                    'error': str(e)
                })

        conn.commit()

        response = {
            'success': True,
            'results': results,
            'total_added': len(results)
        }

        if errors:
            response['errors'] = errors
            response['total_errors'] = len(errors)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: Database = Depends(get_db)):
    """Delete a specific question"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()

        if not question:
            raise HTTPException(
                status_code=404,
                detail=f'Question with ID {question_id} not found'
            )

        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()

        return {
            'success': True,
            'message': f'Question with ID {question_id} was deleted successfully'
        }

    finally:
        if conn:
            conn.close()

@router.get("/quizzes/{quiz_id}/questions", response_model=QuizWithQuestions)
async def get_questions_by_quiz_id(quiz_id: int, db: Database = Depends(get_db)):
    """Get quiz details and all its questions"""
    try:
        # First, get the quiz details
        quiz_query = "SELECT * FROM quiz WHERE id = :quiz_id"
        quiz = await db.fetch_one(quiz_query, values={"quiz_id": quiz_id})

        if not quiz:
            raise HTTPException(
                status_code=404,
                detail=f'Quiz with ID {quiz_id} not found'
            )

        quiz_dict = dict(quiz)

        # Get all questions for this quiz
        questions_query = "SELECT * FROM questions WHERE quiz_id = :quiz_id"
        questions = await db.fetch_all(questions_query, values={"quiz_id": quiz_id})

        question_list = []
        for question in questions:
            question_dict = dict(question)
            if 'choices' in question_dict and question_dict['choices']:
                try:
                    question_dict['choices'] = json.loads(question_dict['choices'])
                except json.JSONDecodeError:
                    pass
            question_list.append(question_dict)

        quiz_dict['questions'] = question_list
        return quiz_dict

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))