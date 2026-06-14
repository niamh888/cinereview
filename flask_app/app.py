import os

import sqlalchemy as sa
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
    # Add user_id to review table if it doesn't exist yet (safe to run on every startup)
    with db.engine.connect() as _conn:
        try:
            _conn.execute(sa.text(
                'ALTER TABLE review ADD COLUMN user_id INTEGER REFERENCES "user"(id)'
            ))
            _conn.commit()
        except Exception:
            _conn.rollback()
    # Backfill user_id on reviews submitted before the column existed
    with db.engine.connect() as _conn:
        try:
            _conn.execute(sa.text(
                'UPDATE review SET user_id = '
                '(SELECT id FROM "user" WHERE username = review.name) '
                'WHERE user_id IS NULL'
            ))
            _conn.commit()
        except Exception:
            _conn.rollback()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
