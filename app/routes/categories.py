from flask import Blueprint, jsonify
from app.database import get_db_connection

bp = Blueprint('categories', __name__)

@bp.route('/api/categories', methods=['GET'])
def get_categories():
    """
    Endpoint to retrieve all unique category names from the database.
    Returns a JSON array of category strings.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM quiz ORDER BY category")
    categories = cursor.fetchall()

    category_list = [category['category'] for category in categories]

    conn.close()
    return jsonify(category_list)