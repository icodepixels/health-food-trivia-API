from flask import Blueprint, jsonify, request
from app.database import get_db_connection
import json
from datetime import datetime

bp = Blueprint('users', __name__)

@bp.route('/api/users', methods=['POST'])
def create_user():
    """
    Create a new user or update existing user by email.
    """
    data = request.get_json()

    if 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        print(f"Creating user with email: {cursor}")

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (data['email'],))
        user = cursor.fetchone()

        if user:
            return jsonify({
                'success': False,
                'message': 'User already exists',
                'user_id': user['id']
            }), 200

        # Create new user
        cursor.execute('''
            INSERT INTO users (email, created_at)
            VALUES (?, ?)
        ''', (data['email'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        new_user_id = cursor.lastrowid

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': new_user_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@bp.route('/api/users/<string:email>/results', methods=['POST'])
def save_quiz_result(email):
    """
    Save a quiz result for a user.
    """
    data = request.get_json()
    required_fields = ['quiz_id', 'score', 'answers']

    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Save quiz result
        cursor.execute('''
            INSERT INTO quiz_results (
                user_id, quiz_id, score, answers, completed_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            user['id'],
            data['quiz_id'],
            data['score'],
            json.dumps(data['answers']),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        result_id = cursor.lastrowid

        return jsonify({
            'success': True,
            'message': 'Quiz result saved successfully',
            'result_id': result_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@bp.route('/api/users/<string:email>/results', methods=['GET'])
def get_user_results(email):
    """
    Get all quiz results for a user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get all results with quiz details
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

        # Format results
        formatted_results = []
        for result in results:
            result_dict = {}
            for key in result.keys():
                result_dict[key] = result[key]
                if key == 'answers':
                    result_dict[key] = json.loads(result[key])
            formatted_results.append(result_dict)

        return jsonify({
            'email': email,
            'results': formatted_results,
            'total_results': len(formatted_results)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@bp.route('/api/users/<string:email>/stats', methods=['GET'])
def get_user_stats(email):
    """
    Get user statistics across all quizzes.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get overall stats
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

        stats = cursor.fetchone()

        # Get category breakdown
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

        categories = cursor.fetchall()

        # Format response
        stats_dict = {}
        for key in stats.keys():
            stats_dict[key] = stats[key]

        category_stats = []
        for cat in categories:
            cat_dict = {}
            for key in cat.keys():
                cat_dict[key] = cat[key]
            category_stats.append(cat_dict)

        return jsonify({
            'email': email,
            'overall_stats': stats_dict,
            'category_stats': category_stats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()