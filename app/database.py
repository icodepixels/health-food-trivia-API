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
async def get_db():
    """Async database connection dependency"""
    async with database.connection() as connection:
        yield connection