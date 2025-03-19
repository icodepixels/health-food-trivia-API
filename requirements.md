MVP Requirements:
	1.	Frontend (React + Vite + Redux)
    •	Landing page with quiz categories (nutrition, sustainability, ethics, history, science, culture).
    •	Quiz interface with multiple-choice questions.
    •	Email submission form for tracking progress.
    •	Results page showing correct answers and score.
	2.	Backend (Python)
    •	API endpoints for:
    •	Fetching categories data.
    •	Fetching quiz data.
    •	Submitting quiz answers.
    •	Storing user email and quiz results.
    •	Simple input validation and error handling.
	3.	Database (SQLite)
    •	Users table (email, timestamp, results_id).
    •	Quizzes table (see Quiz model).
    •	Results table (user_id, quiz_id, score).
	4.	Additional Features
    •	Basic email format validation.
    •	Session management (using cookies or tokens for tracking progress).
    •	Endpoint to add or modify quizzes via Postman.


Models:

Quiz model:
{
  id string,
  name string,
  description string,
  image string,
  questions string,
  category string,
  difficulty string
}

Question model:
{
  id int,
  question_text string,
  choices array,
  correct_answer_index int,
  explanation string,
  category string,
  difficulty string,
  image string,
}
