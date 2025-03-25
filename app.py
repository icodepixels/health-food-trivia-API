from flask import Flask, jsonify, request  # Flask for web server, jsonify for JSON responses, request to handle HTTP requests
import sqlite3  # SQLite database library
from datetime import datetime  # For timestamp generation
import json  # For JSON serialization and deserialization
from flask_cors import CORS  # Import CORS for enabling Cross-Origin Resource Sharing

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

def get_db_connection():
    """
    Create and return a database connection with row factory enabled.
    This allows accessing columns by name instead of index.
    """
    conn = sqlite3.connect('trivia.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn


# QUIZZES ---------
@app.route('/quizzes', methods=['GET'])
def get_quizzes():
    """
    Endpoint to retrieve quizzes from the database.
    Optional query parameter 'category' to filter quizzes by category.
    Returns a JSON array of quiz objects.
    """
    # Get the category parameter from the query string (if provided)
    category = request.args.get('category')

    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute query based on whether a category filter was provided
    if category:
        # Filter quizzes by the specified category
        cursor.execute("SELECT * FROM quiz WHERE category = ?", (category,))
    else:
        # Get all quizzes if no category filter was provided
        cursor.execute("SELECT * FROM quiz")

    quizzes = cursor.fetchall()

    # Convert the SQLite Row objects to dictionaries for JSON serialization
    quiz_list = []
    for quiz in quizzes:
        quiz_dict = {}
        for key in quiz.keys():
            quiz_dict[key] = quiz[key]
        quiz_list.append(quiz_dict)

    # Close the database connection
    conn.close()

    # Return the list of quizzes as JSON
    return jsonify(quiz_list)



@app.route('/quizzes', methods=['POST'])
def create_quiz():
    """
    Endpoint to create a new quiz.
    Accepts JSON data with quiz details and inserts it into the database.
    Returns the newly created quiz with its ID.
    """
    # Get the JSON data from the request body
    quiz_data = request.get_json()

    # Validate that all required fields are present in the request
    required_fields = ['name', 'description', 'image', 'category', 'difficulty']
    for field in required_fields:
        if field not in quiz_data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Generate current timestamp for created_at field
    current_time = datetime.now().strftime('%Y-%m-%d')

    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the new quiz into the database
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

        # Commit the transaction to save changes
        conn.commit()

        # Get the ID of the newly inserted quiz
        new_quiz_id = cursor.lastrowid

        # Fetch the newly created quiz to return it in the response
        cursor.execute("SELECT * FROM quiz WHERE id = ?", (new_quiz_id,))
        new_quiz = cursor.fetchone()

        # Convert SQLite Row to dictionary for JSON serialization
        result = {}
        for key in new_quiz.keys():
            result[key] = new_quiz[key]

        # Close the database connection
        conn.close()

        # Return the newly created quiz with 201 Created status
        return jsonify(result), 201

    except Exception as e:
        # Handle any errors that occur during database operations
        return jsonify({'error': str(e)}), 500


# CATEGORIES ---------
@app.route('/categories', methods=['GET'])
def get_categories():
    """
    Endpoint to retrieve all unique category names from the database.
    Returns a JSON array of category strings.
    """
    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute query to get all unique category names
    cursor.execute("SELECT DISTINCT category FROM quiz ORDER BY category")
    categories = cursor.fetchall()

    # Extract category names from the result rows
    category_list = [category['category'] for category in categories]

    # Close the database connection
    conn.close()

    # Return the list of categories as JSON
    return jsonify(category_list)


# QUESTIONS ---------
@app.route('/questions', methods=['POST'])
def add_questions():
    """
    Endpoint to add multiple questions to quizzes.
    Accepts a JSON array of question objects, each containing a quiz_id.
    Returns the newly created questions with their IDs.
    """
    # Get the JSON data from the request body
    questions_data = request.get_json()

    # Validate that we received an array
    if not isinstance(questions_data, list):
        return jsonify({'error': 'Request body must be an array of question objects'}), 400

    # Prepare the response
    results = []
    errors = []

    # Establish database connection
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create questions table if it doesn't exist
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

        # Process each question in the array
        for index, question_data in enumerate(questions_data):
            try:
                # Validate that all required fields are present
                required_fields = ['quiz_id', 'question_text', 'choices', 'correct_answer_index',
                                'explanation', 'category', 'difficulty', 'image']

                # Check for missing fields
                missing_fields = [field for field in required_fields if field not in question_data]
                if missing_fields:
                    errors.append({
                        'index': index,
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    })
                    continue

                # Verify that the quiz exists
                quiz_id = question_data['quiz_id']
                cursor.execute("SELECT id FROM quiz WHERE id = ?", (quiz_id,))
                quiz = cursor.fetchone()

                if not quiz:
                    errors.append({
                        'index': index,
                        'error': f'Quiz with ID {quiz_id} not found'
                    })
                    continue

                # Convert choices array to JSON string for storage
                choices_json = json.dumps(question_data['choices'])

                # Insert the new question into the database
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

                # Get the ID of the newly inserted question
                new_question_id = cursor.lastrowid

                # Fetch the newly created question to return it in the response
                cursor.execute("SELECT * FROM questions WHERE id = ?", (new_question_id,))
                new_question = cursor.fetchone()

                # Convert SQLite Row to dictionary for JSON serialization
                result = {}
                for key in new_question.keys():
                    result[key] = new_question[key]

                # Convert the choices JSON string back to an array
                result['choices'] = json.loads(result['choices'])

                # Add to successful results
                results.append(result)

            except Exception as e:
                # Add error for this specific question
                errors.append({
                    'index': index,
                    'error': str(e)
                })

        # Commit the transaction to save all successful changes
        conn.commit()

        # Prepare the response
        response = {
            'success': True,
            'results': results,
            'total_added': len(results)
        }

        # Include errors if any occurred
        if errors:
            response['errors'] = errors
            response['total_errors'] = len(errors)

        # Return the response with appropriate status code
        status_code = 201 if results else 400
        return jsonify(response), status_code

    except Exception as e:
        # Handle any errors that occur during database operations
        import traceback
        error_details = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500
    finally:
        # Ensure connection is closed even if an error occurs
        if conn:
            conn.close()


@app.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """
    Endpoint to delete a specific question by its ID.
    Returns a success message if the question was deleted successfully.
    """
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the question exists
        cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()

        if not question:
            conn.close()
            return jsonify({'error': f'Question with ID {question_id} not found'}), 404

        # Delete the question
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))

        # Commit the transaction to save changes
        conn.commit()

        # Check if any rows were affected
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
        # Handle any errors that occur during database operations
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/quizzes/<int:quiz_id>/questions', methods=['GET'])
def get_questions_by_quiz_id(quiz_id):
    """
    Endpoint to retrieve quiz details and all its questions by quiz_id.
    Returns a JSON object containing quiz details and an array of question objects.
    """
    conn = None
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # First, get the quiz details
        cursor.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            return jsonify({'error': f'Quiz with ID {quiz_id} not found'}), 404

        # Convert quiz SQLite Row to dictionary
        quiz_dict = {}
        for key in quiz.keys():
            quiz_dict[key] = quiz[key]

        # Get all questions for the specified quiz_id
        cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions = cursor.fetchall()

        # Convert the SQLite Row objects to dictionaries for JSON serialization
        question_list = []
        for question in questions:
            question_dict = {}
            for key in question.keys():
                question_dict[key] = question[key]

            # Convert the choices JSON string back to an array
            if 'choices' in question_dict and question_dict['choices']:
                try:
                    question_dict['choices'] = json.loads(question_dict['choices'])
                except json.JSONDecodeError:
                    # If JSON parsing fails, keep it as a string
                    pass

            question_list.append(question_dict)

        # Return both quiz details and questions as JSON
        return jsonify({
            'quiz': quiz_dict,
            'questions': question_list,
            'count': len(question_list)
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_questions_by_quiz_id: {str(e)}\n{error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500
    finally:
        # Ensure connection is closed even if an error occurs
        if conn:
            conn.close()


@app.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """
    Endpoint to delete a specific quiz by its ID.
    Also deletes all associated questions to maintain database integrity.
    Returns a success message if the quiz was deleted successfully.
    """
    conn = None
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the quiz exists
        cursor.execute("SELECT id FROM quiz WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            return jsonify({'error': f'Quiz with ID {quiz_id} not found'}), 404

        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        # First, delete all questions associated with this quiz
        cursor.execute("DELETE FROM questions WHERE quiz_id = ?", (quiz_id,))
        questions_deleted = cursor.rowcount

        # Then delete the quiz itself
        cursor.execute("DELETE FROM quiz WHERE id = ?", (quiz_id,))

        # Commit the transaction
        conn.commit()

        # Check if the quiz was deleted
        if cursor.rowcount > 0:
            return jsonify({
                'success': True,
                'message': f'Quiz with ID {quiz_id} was deleted successfully',
                'questions_deleted': questions_deleted
            }), 200
        else:
            # Rollback if the quiz wasn't deleted
            conn.rollback()
            return jsonify({'error': 'Failed to delete the quiz'}), 500

    except Exception as e:
        # Rollback the transaction in case of error
        if conn:
            conn.rollback()

        import traceback
        error_details = traceback.format_exc()
        return jsonify({
            'error': str(e),
            'details': error_details
        }), 500

    finally:
        # Ensure connection is closed even if an error occurs
        if conn:
            conn.close()


@app.route('/quizzes/with-questions', methods=['POST'])
def create_quiz_with_questions():
    """
    Endpoint to create a new quiz along with its questions in a single request.
    Accepts JSON with quiz data and an array of questions.
    Returns the newly created quiz with its ID and all inserted questions.
    """
    # Get the JSON data from the request body
    data = request.get_json()

    # Validate the request structure
    if 'quiz' not in data:
        return jsonify({'error': 'Missing quiz data'}), 400
    if 'questions' not in data or not isinstance(data['questions'], list):
        return jsonify({'error': 'Missing or invalid questions array'}), 400

    quiz_data = data['quiz']
    questions_data = data['questions']

    # Validate required quiz fields
    required_quiz_fields = ['name', 'description', 'image', 'category', 'difficulty']
    for field in required_quiz_fields:
        if field not in quiz_data:
            return jsonify({'error': f'Missing required quiz field: {field}'}), 400

    # Validate required question fields
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
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        # Generate current timestamp for created_at field
        current_time = datetime.now().strftime('%Y-%m-%d')

        # Insert the new quiz into the database
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

        # Get the ID of the newly inserted quiz
        new_quiz_id = cursor.lastrowid

        # Create questions table if it doesn't exist
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

        # Insert all questions
        inserted_questions = []
        for question in questions_data:
            # Convert choices array to JSON string for storage
            choices_json = json.dumps(question['choices'])

            # Insert the question
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

            # Get the ID of the newly inserted question
            new_question_id = cursor.lastrowid

            # Fetch the newly created question
            cursor.execute("SELECT * FROM questions WHERE id = ?", (new_question_id,))
            new_question = cursor.fetchone()

            # Convert SQLite Row to dictionary
            question_dict = {}
            for key in new_question.keys():
                question_dict[key] = new_question[key]

            # Convert the choices JSON string back to an array
            question_dict['choices'] = json.loads(question_dict['choices'])

            inserted_questions.append(question_dict)

        # Fetch the newly created quiz
        cursor.execute("SELECT * FROM quiz WHERE id = ?", (new_quiz_id,))
        new_quiz = cursor.fetchone()

        # Convert SQLite Row to dictionary
        quiz_result = {}
        for key in new_quiz.keys():
            quiz_result[key] = new_quiz[key]

        # Commit the transaction
        conn.commit()

        # Prepare the response
        response = {
            'success': True,
            'quiz': quiz_result,
            'questions': inserted_questions,
            'total_questions': len(inserted_questions)
        }

        return jsonify(response), 201

    except Exception as e:
        # Rollback the transaction in case of error
        if conn:
            conn.rollback()

        import traceback
        error_details = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500

    finally:
        # Ensure connection is closed even if an error occurs
        if conn:
            conn.close()


@app.route('/quizzes/category-samples', methods=['GET'])
def get_category_samples():
    """
    Endpoint to retrieve random quizzes from each category.
    Query parameter 'limit' determines how many quizzes per category (default: 3)
    Returns a JSON object with categories as keys and arrays of quizzes as values.
    """
    conn = None
    try:
        # Get the limit parameter from query string, default to 3 if not provided
        limit = request.args.get('limit', default=3, type=int)

        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # First, get all unique categories
        cursor.execute("SELECT DISTINCT category FROM quiz ORDER BY category")
        categories = cursor.fetchall()

        # Prepare the result dictionary
        result = {}

        # For each category, get random quizzes up to the limit
        for category_row in categories:
            category = category_row['category']
            cursor.execute("""
                SELECT * FROM quiz
                WHERE category = ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (category, limit))

            quizzes = cursor.fetchall()

            # Convert the SQLite Row objects to dictionaries
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
        import traceback
        error_details = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500
    finally:
        if conn:
            conn.close()


# APP RUN ---------
# Run the app if this file is executed directly
if __name__ == '__main__':
    app.run(debug=True)  # Run in debug mode for development