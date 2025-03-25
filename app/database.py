import sqlite3
from databases import Database
from sqlalchemy import create_engine, MetaData
from fastapi import Depends
from typing import AsyncGenerator

# Database URL
DATABASE_URL = "sqlite:///trivia.db"

# Create Database instance for async operations
database = Database(DATABASE_URL)
metadata = MetaData()

# Create SQLAlchemy engine for migrations/table creation
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

# Legacy synchronous connection function
def get_db_connection():
    """Create a database connection with row factory enabled"""
    conn = sqlite3.connect('trivia.db')
    conn.row_factory = sqlite3.Row
    return conn

# New async database functions
async def get_database() -> AsyncGenerator[Database, None]:
    """Dependency for getting async database session"""
    try:
        await database.connect()
        yield database
    finally:
        await database.disconnect()

# FastAPI dependency
async def get_db() -> AsyncGenerator[Database, None]:
    """Async database connection dependency"""
    try:
        await database.connect()
        yield database
    finally:
        await database.disconnect()

def init_db():
    """Initialize the database with required tables and sample data"""
    conn = sqlite3.connect('trivia.db')
    cursor = conn.cursor()

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

    # Add sample data if the table is empty
    cursor.execute("SELECT COUNT(*) FROM quiz")
    if cursor.fetchone()[0] == 0:
        # Insert sample quizzes
        sample_quizzes = [
            ('History Quiz', 'Test your history knowledge', 'https://example.com/history.jpg', 'History', 'Medium', '2024-01-01'),
            ('Science Quiz', 'Test your science knowledge', 'https://example.com/science.jpg', 'Science', 'Easy', '2024-01-01'),
            ('Culture Quiz', 'Test your cultural knowledge', 'https://example.com/culture.jpg', 'Culture', 'Hard', '2024-01-01')
        ]
        cursor.executemany('''
            INSERT INTO quiz (name, description, image, category, difficulty, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_quizzes)

    conn.commit()
    conn.close()

# Initialize the database
init_db()