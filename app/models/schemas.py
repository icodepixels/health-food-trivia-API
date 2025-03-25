from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class QuestionBase(BaseModel):
    question_text: str = Field(
        ...,
        description="The text of the question",
        example="What is the capital of France?"
    )
    choices: List[str] = Field(
        ...,
        description="List of possible answers",
        example=["Paris", "London", "Berlin", "Madrid"]
    )
    correct_answer_index: int = Field(
        ...,
        description="Index of the correct answer (0-based)",
        example=0,
        ge=0
    )
    explanation: str = Field(
        ...,
        description="Explanation of the correct answer",
        example="Paris is the capital and largest city of France."
    )
    category: str = Field(
        ...,
        description="Category of the question",
        example="Geography"
    )
    difficulty: str = Field(
        ...,
        description="Difficulty level of the question",
        example="Medium"
    )
    image: str = Field(
        ...,
        description="URL of associated image",
        example="https://example.com/paris.jpg"
    )

class QuestionCreate(QuestionBase):
    quiz_id: int = Field(..., description="ID of the quiz this question belongs to")

class Question(QuestionBase):
    id: int
    quiz_id: int

    class Config:
        from_attributes = True

class QuizBase(BaseModel):
    name: str = Field(
        ...,
        description="Name of the quiz",
        example="European Capitals"
    )
    description: str = Field(
        ...,
        description="Description of the quiz",
        example="Test your knowledge of European capital cities"
    )
    image: str = Field(
        ...,
        description="URL of quiz cover image",
        example="https://example.com/europe.jpg"
    )
    category: str = Field(
        ...,
        description="Quiz category",
        example="Geography"
    )
    difficulty: str = Field(
        ...,
        description="Quiz difficulty level",
        example="Medium"
    )

class QuizCreate(QuizBase):
    pass

class Quiz(QuizBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class QuizWithQuestions(Quiz):
    questions: List[Question]

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class QuizResult(BaseModel):
    quiz_id: int
    score: float
    answers: dict

class QuizResultResponse(QuizResult):
    id: int
    completed_at: datetime

class UserStats(BaseModel):
    total_quizzes: int
    average_score: float
    highest_score: float
    lowest_score: float
    unique_quizzes: int

class CategoryStat(BaseModel):
    category: str
    quizzes_taken: int
    average_score: float

class UserStatsResponse(BaseModel):
    email: str
    overall_stats: UserStats
    category_stats: List[CategoryStat]