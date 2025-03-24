# Trivia Quiz API

A Flask-based REST API for managing trivia quizzes and questions. This API allows you to create, retrieve, and manage quizzes and their associated questions.

## Project Structure
Flask==2.0.1
Flask-CORS==3.0.10atabase file (`trivia.db`)


- The `quiz` table
- The `questions` table

### 5. Start the Application
There are two ways to run the application:

Run the database initialization:
```bash
python -m app.init_db
```

#### Development Mode
```bash
# From the project root directory
python run.py
```
This will start the server with debug mode enabled:
- Auto-reloads when code changes
- Detailed error messages
- Running on http://localhost:5000

#### Production Mode
```bash
# Set environment variable for production
# Windows
set FLASK_ENV=production

# macOS/Linux
export FLASK_ENV=production

# Run the application
python run.py
```

### Verify Installation

1. Check if the server is running:
```bash
curl http://localhost:5000/api/categories
```
Should return an empty array `[]` if the database is new.

2. Create a test quiz:
```bash
curl -X POST http://localhost:5000/api/quizzes \
-H "Content-Type: application/json" \
-d '{
  "name": "Test Quiz",
  "description": "Testing the API",
  "image": "https://example.com/test.jpg",
  "category": "Test",
  "difficulty": "Easy"
}'
```

### Troubleshooting

If you encounter any issues:

1. **Database Errors**
   - Delete the `trivia.db` file
   - Run the initialization script again
   ```bash
   python -m app.init_db
   ```

2. **Port Already in Use**
   - Change the port in `run.py`:
   ```python
   if __name__ == '__main__':
       app.run(debug=True, port=5001)  # Change to different port
   ```

3. **Permission Issues**
   - Check file permissions for the database:
   ```bash
   # Linux/macOS
   chmod 666 trivia.db
   ```

4. **Module Not Found Errors**
   - Verify you're in the virtual environment
   - Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

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

### Users and Quiz Results

#### Create User
- **URL:** `/api/users`
- **Method:** `POST`
- **Data Parameters:**
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Success Response:**
  - **Code:** 201
  - **Content:**
    ```json
    {
      "success": true,
      "message": "User created successfully",
      "user_id": 1
    }
    ```
- **Error Response:**
  - **Code:** 409 CONFLICT
    ```json
    {
      "success": false,
      "message": "User already exists",
      "user_id": 1
    }
    ```

#### Save Quiz Result
- **URL:** `/api/users/:email/results`
- **Method:** `POST`
- **Data Parameters:**
  ```json
  {
    "quiz_id": 1,
    "score": 85.5,
    "answers": [
      {
        "question_id": 1,
        "selected_answer": 2,
        "is_correct": true
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
      "message": "Quiz result saved successfully",
      "result_id": 1
    }
    ```

#### Get User Results
- **URL:** `/api/users/:email/results`
- **Method:** `GET`
- **Success Response:**
  - **Code:** 200
  - **Content:**
    ```json
    {
      "email": "user@example.com",
      "results": [
        {
          "result_id": 1,
          "quiz_id": 1,
          "quiz_name": "Science Quiz",
          "category": "Science",
          "difficulty": "Medium",
          "score": 85.5,
          "answers": [
            {
              "question_id": 1,
              "selected_answer": 2,
              "is_correct": true
            }
          ],
          "completed_at": "2024-03-20 15:30:00"
        }
      ],
      "total_results": 1
    }
    ```

#### Get User Statistics
- **URL:** `/api/users/:email/stats`
- **Method:** `GET`
- **Success Response:**
  - **Code:** 200
  - **Content:**
    ```json
    {
      "email": "user@example.com",
      "overall_stats": {
        "total_quizzes": 10,
        "average_score": 82.5,
        "highest_score": 100,
        "lowest_score": 65,
        "unique_quizzes": 8
      },
      "category_stats": [
        {
          "category": "Science",
          "quizzes_taken": 5,
          "average_score": 85.5
        }
      ]
    }
    ```

### Database Schema

[After existing schema, add:]

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
)
```

### Quiz Results Table
```sql
CREATE TABLE quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score REAL NOT NULL,
    answers TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (quiz_id) REFERENCES quiz (id)
)
```
```