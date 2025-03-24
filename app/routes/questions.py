from flask import Blueprint, jsonify, request
from app.database import get_db_connection
import json
import traceback

bp = Blueprint('questions', __name__)

@bp.route('/api/questions', methods=['POST'])
def add_questions():
    """
    Endpoint to add multiple questions to quizzes.
    Accepts a JSON array of question objects, each containing a quiz_id.
    """
    questions_data = request.get_json()

    if not isinstance(questions_data, list):
        return jsonify({'error': 'Request body must be an array of question objects'}), 400

    results = []
    errors = []
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            choices TEXT NOT NULL,
            correct_answer_index INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            category TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            image TEXT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quiz (id)
        )
        ''')

        for index, question_data in enumerate(questions_data):
            try:
                required_fields = ['quiz_id', 'question_text', 'choices', 'correct_answer_index',
                                'explanation', 'category', 'difficulty', 'image']

                missing_fields = [field for field in required_fields if field not in question_data]
                if missing_fields:
                    errors.append({
                        'index': index,
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    })
                    continue

                quiz_id = question_data['quiz_id']
                cursor.execute("SELECT id FROM quiz WHERE id = ?", (quiz_id,))
                quiz = cursor.fetchone()

                if not quiz:
                    errors.append({
                        'index': index,
                        'error': f'Quiz with ID {quiz_id} not found'
                    })
                    continue

                choices_json = json.dumps(question_data['choices'])

                cursor.execute('''
                    INSERT INTO questions (
                        quiz_id, question_text, choices, correct_answer_index,
                        explanation, category, difficulty, image
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    quiz_id,
                    question_data['question_text'],
                    choices_json,
                    question_data['correct_answer_index'],
                    question_data['explanation'],
                    question_data['category'],
                    question_data['difficulty'],
                    question_data['image']
                ))

                new_question_id = cursor.lastrowid
                cursor.execute("SELECT * FROM questions WHERE id = ?", (new_question_id,))
                new_question = cursor.fetchone()

                result = {}
                for key in new_question.keys():
                    result[key] = new_question[key]
                result['choices'] = json.loads(result['choices'])
                results.append(result)

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

        status_code = 201 if results else 400
        return jsonify(response), status_code

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

@bp.route('/api/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """
    Endpoint to delete a specific question by its ID.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()

        if not question:
            conn.close()
            return jsonify({'error': f'Question with ID {question_id} not found'}), 404

        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return jsonify({
                'success': True,
                'message': f'Question with ID {question_id} was deleted successfully'
            }), 200
        else:
            conn.close()
            return jsonify({'error': 'Failed to delete the question'}), 500

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/quizzes/<int:quiz_id>/questions', methods=['GET'])
def get_questions_by_quiz_id(quiz_id):
    """
    Endpoint to retrieve quiz details and all its questions by quiz_id.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            return jsonify({'error': f'Quiz with ID {quiz_id} not found'}), 404

        quiz_dict = {}
        for key in quiz.keys():
            quiz_dict[key] = quiz[key]

        cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions = cursor.fetchall()

        question_list = []
        for question in questions:
            question_dict = {}
            for key in question.keys():
                question_dict[key] = question[key]

            if 'choices' in question_dict and question_dict['choices']:
                try:
                    question_dict['choices'] = json.loads(question_dict['choices'])
                except json.JSONDecodeError:
                    pass

            question_list.append(question_dict)

        return jsonify({
            'quiz': quiz_dict,
            'questions': question_list,
            'count': len(question_list)
        })

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in get_questions_by_quiz_id: {str(e)}\n{error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500
    finally:
        if conn:
            conn.close()