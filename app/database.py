import sqlite3
from config import Config

def get_db_connection():
    """
    Create and return a database connection with row factory enabled.
    This allows accessing columns by name instead of index.
    """
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database by creating necessary tables.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    # Create quiz_results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quiz_id INTEGER NOT NULL,
        score REAL NOT NULL,
        answers TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (quiz_id) REFERENCES quiz (id)
    )
    ''')

    # Create quiz table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        image TEXT NOT NULL,
        category TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    # Create questions table
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

    conn.commit()
    conn.close()