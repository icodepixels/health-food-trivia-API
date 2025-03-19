# Trivia API Documentation

A Flask-based REST API for managing trivia quizzes and questions.

## Base URL
`/api`

## Endpoints

### Quizzes

#### Get All Quizzes
- **URL:** `/quizzes`
- **Method:** `GET`
- **URL Parameters:**
  - `category` (optional): Filter quizzes by category
- **Success Response:**
  - **Code:** 200
  - **Content:** Array of quiz objects
    ```json
    [
      {
        "id": 1,
        "name": "Quiz Name",
        "description": "Quiz Description",
        "image": "image_url",
        "category": "Category",
        "difficulty": "Easy",
        "created_at": "2024-03-20"
      }
    ]
    ```

#### Create Quiz
- **URL:** `/quizzes`
- **Method:** `POST`
- **Data Parameters:**
  ```json
  {
    "name": "Quiz Name",
    "description": "Quiz Description",
    "image": "image_url",
    "category": "Category",
    "difficulty": "Easy"
  }
  ```
- **Success Response:**
  - **Code:** 201
  - **Content:** Created quiz object

#### Get Category Samples
- **URL:** `/quizzes/category-samples`
- **Method:** `GET`
- **Success Response:**
  - **Code:** 200
  - **Content:**
    ```json
    {
      "success": true,
      "samples": {
        "Category1": [
          {
            "id": 1,
            "name": "Quiz Name",
            "description": "Description",
            "image": "image_url",
            "category": "Category1",
            "difficulty": "Easy",
            "created_at": "2024-03-20"
          }
          // ... up to 3 quizzes per category
        ]
      },
      "total_categories": 1
    }
    ```

#### Delete Quiz
- **URL:** `/quizzes/:quiz_id`
- **Method:** `DELETE`
- **Success Response:**
  - **Code:** 200
  - **Content:**
    ```json
    {
      "success": true,
      "message": "Quiz with ID {quiz_id} was deleted successfully",
      "questions_deleted": 5
    }
    ```

### Questions

#### Get Questions by Quiz
- **URL:** `/quizzes/:quiz_id/questions`
- **Method:** `GET`
- **Success Response:**
  - **Code:** 200
  - **Content:**
    ```json
    {
      "quiz_id": 1,
      "questions": [
        {
          "id": 1,
          "quiz_id": 1,
          "question_text": "Question text",
          "choices": ["choice1", "choice2", "choice3", "choice4"],
          "correct_answer_index": 0,
          "explanation": "Explanation",
          "category": "Category",
          "difficulty": "Easy",
          "image": "image_url"
        }
      ],
      "count": 1
    }
    ```

#### Add Questions
- **URL:** `/questions`
- **Method:** `POST`
- **Data Parameters:**
  ```json
  [
    {
      "quiz_id": 1,
      "question_text": "Question text",
      "choices": ["choice1", "choice2", "choice3", "choice4"],
      "correct_answer_index": 0,
      "explanation": "Explanation",
      "category": "Category",
      "difficulty": "Easy",
      "image": "image_url"
    }
  ]
  ```
- **Success Response:**
  - **Code:** 201
  - **Content:** Array of created question objects

#### Delete Question
- **URL:** `/questions/:question_id`
- **Method:** `DELETE`
- **Success Response:**
  - **Code:** 200
  - **Content:**
    ```json
    {
      "success": true,
      "message": "Question with ID {question_id} was deleted successfully"
    }
    ```

### Categories

#### Get Categories
- **URL:** `/categories`
- **Method:** `GET`
- **Success Response:**
  - **Code:** 200
  - **Content:** Array of category strings
    ```json
    ["Category1", "Category2", "Category3"]
    ```

### Create Quiz with Questions

#### Create Quiz with Questions
- **URL:** `/quizzes/with-questions`
- **Method:** `POST`
- **Data Parameters:**
  ```json
  {
    "quiz": {
      "name": "Quiz Name",
      "description": "Quiz Description",
      "image": "image_url",
      "category": "Category",
      "difficulty": "Easy"
    },
    "questions": [
      {
        "question_text": "Question text",
        "choices": ["choice1", "choice2", "choice3", "choice4"],
        "correct_answer_index": 0,
        "explanation": "Explanation",
        "category": "Category",
        "difficulty": "Easy",
        "image": "image_url"
      }
    ]
  }
  ```
- **Success Response:**
  - **Code:** 201
  - **Content:**
    ```json
    {
      "success": true,
      "quiz": {
        // quiz object
      },
      "questions": [
        // array of question objects
      ],
      "total_questions": 1
    }
    ```

## Error Responses
All endpoints may return the following errors:

- **Code:** 400 BAD REQUEST
  ```json
  {
    "error": "Error description"
  }
  ```
- **Code:** 404 NOT FOUND
  ```json
  {
    "error": "Resource not found"
  }
  ```
- **Code:** 500 INTERNAL SERVER ERROR
  ```json
  {
    "error": "Error message",
    "details": "Detailed error information"
  }
  ```

## Database Schema

### Quiz Table
```sql
CREATE TABLE quiz (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    image TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    created_at TEXT NOT NULL
)
```

### Questions Table
```sql
CREATE TABLE questions (
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
```
```

This README provides comprehensive documentation for all endpoints currently implemented in your app.js, including the new category samples endpoint. It includes:
- All available endpoints
- Request/response formats
- Error handling
- Database schema

If you have an existing README with additional sections (like installation instructions, deployment guide, etc.), let me know and I can help integrate this API documentation with your existing content.