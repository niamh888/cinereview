import os

from flask import Flask

from config import configure_app
from extensions import db, mail, login_manager
from models import User, WatchedMovie, ExcludedMovie, Review, MovieCache

# Declare public re-exports so the test suite can do: from app import db, User, ...
__all__ = ['app', 'db', 'User', 'WatchedMovie', 'ExcludedMovie', 'Review', 'MovieCache']
from routes import register_routes

app = Flask(__name__)
configure_app(app)

db.init_app(app)
mail.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to use this feature.'
login_manager.login_message_category = 'error'

register_routes(app)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
