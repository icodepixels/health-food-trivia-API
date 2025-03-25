from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.database import get_db_connection
from app.models.schemas import Question, QuestionCreate, QuizWithQuestions
import json
import traceback

router = APIRouter()

@router.post("/api/questions", response_model=Dict)
async def add_questions(questions: List[QuestionCreate]):
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

@router.delete("/api/questions/{question_id}")
async def delete_question(question_id: int):
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

@router.get("/api/quizzes/{quiz_id}/questions", response_model=QuizWithQuestions)
async def get_questions_by_quiz_id(quiz_id: int):
    """Get quiz details and all its questions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            raise HTTPException(
                status_code=404,
                detail=f'Quiz with ID {quiz_id} not found'
            )

        quiz_dict = dict(quiz)

        cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions = cursor.fetchall()

        question_list = []
        for question in questions:
            question_dict = dict(question)
            if 'choices' in question_dict and question_dict['choices']:
                question_dict['choices'] = json.loads(question_dict['choices'])
            question_list.append(question_dict)

        quiz_dict['questions'] = question_list
        return quiz_dict

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()