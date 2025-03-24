from flask import Blueprint, jsonify, request
from app.database import get_db_connection
from datetime import datetime
import json
import traceback

bp = Blueprint('quizzes', __name__)

@bp.route('/api/quizzes', methods=['GET'])
def get_quizzes():
    """
    Endpoint to retrieve quizzes from the database.
    Optional query parameter 'category' to filter quizzes by category.
    Returns a JSON array of quiz objects.
    """
    category = request.args.get('category')
    conn = get_db_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("SELECT * FROM quiz WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT * FROM quiz")

    quizzes = cursor.fetchall()

    quiz_list = []
    for quiz in quizzes:
        quiz_dict = {}
        for key in quiz.keys():
            quiz_dict[key] = quiz[key]
        quiz_list.append(quiz_dict)

    conn.close()
    return jsonify(quiz_list)

@bp.route('/api/quizzes', methods=['POST'])
def create_quiz():
    """
    Endpoint to create a new quiz.
    Accepts JSON data with quiz details and inserts it into the database.
    Returns the newly created quiz with its ID.
    """
    quiz_data = request.get_json()
    required_fields = ['name', 'description', 'image', 'category', 'difficulty']

    for field in required_fields:
        if field not in quiz_data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    current_time = datetime.now().strftime('%Y-%m-%d')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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

        conn.commit()
        new_quiz_id = cursor.lastrowid

        cursor.execute("SELECT * FROM quiz WHERE id = ?", (new_quiz_id,))
        new_quiz = cursor.fetchone()

        result = {}
        for key in new_quiz.keys():
            result[key] = new_quiz[key]

        conn.close()
        return jsonify(result), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/quizzes/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """
    Endpoint to delete a specific quiz by its ID.
    Also deletes all associated questions to maintain database integrity.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM quiz WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            return jsonify({'error': f'Quiz with ID {quiz_id} not found'}), 404

        conn.execute("BEGIN TRANSACTION")
        cursor.execute("DELETE FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions_deleted = cursor.rowcount
        cursor.execute("DELETE FROM quiz WHERE id = ?", (quiz_id,))

        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({
                'success': True,
                'message': f'Quiz with ID {quiz_id} was deleted successfully',
                'questions_deleted': questions_deleted
            }), 200
        else:
            conn.rollback()
            return jsonify({'error': 'Failed to delete the quiz'}), 500

    except Exception as e:
        if conn:
            conn.rollback()
        error_details = traceback.format_exc()
        return jsonify({
            'error': str(e),
            'details': error_details
        }), 500
    finally:
        if conn:
            conn.close()

@bp.route('/api/quizzes/with-questions', methods=['POST'])
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

@bp.route('/api/quizzes/category-samples', methods=['GET'])
def get_category_samples():
    """
    Endpoint to retrieve random quizzes from each category.
    Query parameter 'limit' determines how many quizzes per category (default: 3)
    """
    conn = None
    try:
        limit = request.args.get('limit', default=3, type=int)
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT category FROM quiz ORDER BY category")
        categories = cursor.fetchall()

        result = {}
        for category_row in categories:
            category = category_row['category']
            cursor.execute("""
                SELECT * FROM quiz
                WHERE category = ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (category, limit))

            quizzes = cursor.fetchall()
            quiz_list = []
            for quiz in quizzes:
                quiz_dict = {}
                for key in quiz.keys():
                    quiz_dict[key] = quiz[key]
                quiz_list.append(quiz_dict)

            result[category] = quiz_list

        return jsonify({
            'success': True,
            'samples': result,
            'total_categories': len(categories),
            'quizzes_per_category': limit
        })

    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500
    finally:
        if conn:
            conn.close()