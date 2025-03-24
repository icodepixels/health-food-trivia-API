from flask import Flask
from flask_cors import CORS
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for all routes
    CORS(app)

    # Register blueprints
    from app.routes import quizzes, questions, categories, users
    app.register_blueprint(quizzes.bp)
    app.register_blueprint(questions.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(users.bp)

    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    return app