"""
Shared fixtures for the CineReview test suite.

How to run:
    cd flask_app
    pip install pytest
    pytest tests/ -v

All TMDB API calls are patched automatically so tests never hit the real API.
Each test gets a fresh in-memory database — no leftover data between tests.
"""

import os
import sys
import pytest
from unittest.mock import patch

# Ensure the flask_app directory is importable (tests/ is a subdirectory)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Point the app at a disposable test database before importing app.py,
# so the module-level db.create_all() targets the test file, not cinereview.db
os.environ.setdefault('DATABASE_URL', 'sqlite:///cinereview_test.db')

from app import app as flask_app, db, User, WatchedMovie, ExcludedMovie, Review  # noqa: E402


# ---------------------------------------------------------------------------
# Mock TMDB responses — returned in place of real API calls during all tests
# ---------------------------------------------------------------------------

MOCK_MOVIE = {
    'id': 550,
    'title': 'Fight Club',
    'poster_path': '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
    'release_date': '1999-10-15',
    'vote_average': 8.4,
    'genre_ids': [18, 53],
    'overview': 'A ticking-bomb thriller about consumerism and identity.',
    'tagline': 'Mischief. Mayhem. Soap.',
    'runtime': 139,
    'genres': [{'id': 18, 'name': 'Drama'}, {'id': 53, 'name': 'Thriller'}],
}
MOCK_MOVIES = [MOCK_MOVIE]
MOCK_CREDITS = (
    [{'name': 'Brad Pitt', 'character': 'Tyler Durden', 'profile_path': None}],
    'David Fincher',
)


@pytest.fixture(autouse=True)
def mock_tmdb():
    """
    Patch every TMDB function so tests never make real HTTP requests.
    Applied automatically to every test in the suite.
    """
    with patch('tmdb.now_playing',   return_value=MOCK_MOVIES), \
         patch('tmdb.popular',       return_value=MOCK_MOVIES), \
         patch('tmdb.top_rated',     return_value=MOCK_MOVIES), \
         patch('tmdb.upcoming',      return_value=MOCK_MOVIES), \
         patch('tmdb.trending',      return_value=MOCK_MOVIES), \
         patch('tmdb.search_movies', return_value=MOCK_MOVIES), \
         patch('tmdb.movie_detail',  return_value=MOCK_MOVIE), \
         patch('tmdb.movie_credits', return_value=MOCK_CREDITS), \
         patch('tmdb.similar',       return_value=MOCK_MOVIES), \
         patch('tmdb.discover',      return_value=MOCK_MOVIES):
        yield


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """
    Configure Flask for testing: in-memory database, testing mode enabled,
    mail sending suppressed.  Drops and recreates all tables for each test.
    """
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key-not-for-production',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///cinereview_test.db',
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_SERVER': 'localhost',
    })

    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Standard (unauthenticated) Flask test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """A registered user inserted directly into the test database."""
    user = User(username='testuser', email='test@example.com')
    user.set_password('Test@1234!')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_client(client, test_user):
    """
    A test client already logged in as test_user.
    Login is performed via POST so session cookies are set correctly.
    """
    client.post('/login', data={
        'username': 'testuser',
        'password': 'Test@1234!',
        'website': '',        # honeypot must be empty
    }, follow_redirects=True)
    return client


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def register_user(client, username='newuser', email='new@example.com',
                  password='Test@1234!', confirm=None, captcha_answer=None,
                  honeypot=''):
    """
    Perform a full registration POST, automatically using the correct CAPTCHA
    answer stored in the session from the preceding GET /register.
    """
    if confirm is None:
        confirm = password

    # GET /register first so the app sets captcha_answer in the session
    client.get('/register')

    if captcha_answer is None:
        with client.session_transaction() as sess:
            captcha_answer = sess.get('captcha_answer', 0)

    return client.post('/register', data={
        'username':         username,
        'email':            email,
        'password':         password,
        'confirm_password': confirm,
        'captcha':          str(captcha_answer),
        'website':          honeypot,
    }, follow_redirects=True)
