"""
Automated test suite for CineReview.
TC IDs map directly to REQUIREMENTS.md.

Run from the flask_app directory:
    pytest tests/ -v
"""

import json
import pytest
from app import db, User, WatchedMovie, ExcludedMovie, Review
from tests.conftest import register_user, MOCK_MOVIE


# ===========================================================================
# TC-001 to TC-009 — Public routes (no login required)
# ===========================================================================

class TestPublicRoutes:

    def test_home_page_returns_200(self, client):
        """TC-001: GET / returns HTTP 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_home_page_contains_movie_title(self, client):
        """TC-002: Home page body contains the mocked movie title."""
        response = client.get('/')
        assert MOCK_MOVIE['title'].encode() in response.data

    def test_category_filter_popular(self, client):
        """TC-003: GET /?category=popular returns HTTP 200."""
        response = client.get('/?category=popular')
        assert response.status_code == 200

    def test_search_with_query_returns_200(self, client):
        """TC-004: GET /search?q=fight returns HTTP 200."""
        response = client.get('/search?q=fight')
        assert response.status_code == 200

    def test_search_empty_query_returns_200(self, client):
        """TC-005: GET /search (no query) returns HTTP 200 without error."""
        response = client.get('/search')
        assert response.status_code == 200

    def test_movie_detail_valid_id(self, client):
        """TC-006: GET /movie/550 returns HTTP 200."""
        response = client.get('/movie/550')
        assert response.status_code == 200

    def test_movie_detail_non_integer_id(self, client):
        """TC-007: GET /movie/abc returns HTTP 404 (Flask converter rejects non-integers)."""
        response = client.get('/movie/abc')
        assert response.status_code == 404

    def test_about_page_returns_200(self, client):
        """TC-008: GET /about returns HTTP 200."""
        response = client.get('/about')
        assert response.status_code == 200

    def test_unknown_url_returns_404(self, client):
        """TC-009: GET /does-not-exist returns HTTP 404."""
        response = client.get('/does-not-exist')
        assert response.status_code == 404


# ===========================================================================
# TC-010 to TC-017 — Registration
# ===========================================================================

class TestRegistration:

    def test_register_page_returns_200(self, client):
        """TC-010: GET /register returns HTTP 200."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_valid_registration_creates_user(self, client, app):
        """TC-011: Valid POST /register creates a user record and redirects to home."""
        response = register_user(client)
        assert response.status_code == 200
        with app.app_context():
            assert User.query.filter_by(username='newuser').first() is not None

    def test_duplicate_username_shows_error(self, client, test_user):
        """TC-012: Registering with an existing username returns an error."""
        response = register_user(client, username='testuser', email='other@example.com')
        assert b'already taken' in response.data

    def test_duplicate_email_shows_error(self, client, test_user):
        """TC-013: Registering with an existing email returns an error."""
        response = register_user(client, username='brandnew', email='test@example.com')
        assert b'already exists' in response.data

    def test_weak_password_shows_error(self, client):
        """TC-014: Registering with a password that fails strength rules returns an error."""
        response = register_user(client, password='weak', confirm='weak')
        assert b'Password must include' in response.data

    def test_mismatched_passwords_shows_error(self, client):
        """TC-015: Registering with mismatched passwords returns an error."""
        response = register_user(client, password='Test@1234!', confirm='Different@99!')
        assert b'do not match' in response.data

    def test_wrong_captcha_shows_error(self, client):
        """TC-016: Submitting an incorrect CAPTCHA answer returns an error."""
        response = register_user(client, captcha_answer=9999)
        assert b'Incorrect answer' in response.data or b'captcha' in response.data.lower()

    def test_honeypot_filled_does_not_create_user(self, client, app):
        """TC-017: Filling the honeypot field redirects without creating a user."""
        response = register_user(client, honeypot='i-am-a-bot')
        with app.app_context():
            assert User.query.filter_by(username='newuser').first() is None


# ===========================================================================
# TC-018 to TC-022 — Authentication
# ===========================================================================

class TestAuthentication:

    def test_login_page_returns_200(self, client):
        """TC-018: GET /login returns HTTP 200."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_valid_credentials(self, client, test_user):
        """TC-019: Valid login credentials authenticate the user and redirect to home."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@1234!',
            'website': '',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome back' in response.data

    def test_login_wrong_password_shows_error(self, client, test_user):
        """TC-020: Incorrect password returns 200 with an error message."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword!',
            'website': '',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'incorrect' in response.data.lower()

    def test_login_unknown_username_shows_error(self, client):
        """TC-021: Unknown username returns 200 with an error message."""
        response = client.post('/login', data={
            'username': 'nobody',
            'password': 'Test@1234!',
            'website': '',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'incorrect' in response.data.lower()

    def test_logout_redirects(self, auth_client):
        """TC-022: GET /logout logs out the user and redirects to home."""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


# ===========================================================================
# TC-023 to TC-025 — Access control (unauthenticated)
# ===========================================================================

class TestAccessControl:

    def test_my_movies_redirects_to_login(self, client):
        """TC-023: GET /my-movies without login redirects to /login."""
        response = client.get('/my-movies')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_toggle_watched_redirects_to_login(self, client):
        """TC-024: POST /toggle-watched/<id> without login redirects to /login."""
        response = client.post('/toggle-watched/550')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_exclude_movie_redirects_to_login(self, client):
        """TC-025: POST /exclude-movie/<id> without login redirects to /login."""
        response = client.post('/exclude-movie/550')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


# ===========================================================================
# TC-026 to TC-028 — Watch tracking
# ===========================================================================

class TestWatchTracking:

    def test_toggle_watched_marks_movie(self, auth_client, app, test_user):
        """TC-026: First POST /toggle-watched/<id> returns {"watched": true}."""
        response = auth_client.post('/toggle-watched/550')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['watched'] is True

    def test_toggle_watched_unmarks_movie(self, auth_client, app, test_user):
        """TC-027: Second POST /toggle-watched/<id> returns {"watched": false}."""
        auth_client.post('/toggle-watched/550')       # mark
        response = auth_client.post('/toggle-watched/550')  # unmark
        data = json.loads(response.data)
        assert data['watched'] is False

    def test_my_movies_returns_200(self, auth_client):
        """TC-028: GET /my-movies for an authenticated user returns HTTP 200."""
        response = auth_client.get('/my-movies')
        assert response.status_code == 200


# ===========================================================================
# TC-029 to TC-030 — Movie exclusion
# ===========================================================================

class TestMovieExclusion:

    def test_exclude_movie_returns_excluded_true(self, auth_client, app, test_user):
        """TC-029: First POST /exclude-movie/<id> returns {"excluded": true}."""
        response = auth_client.post('/exclude-movie/550')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['excluded'] is True

    def test_exclude_movie_toggles_to_false(self, auth_client, app, test_user):
        """TC-030: Second POST /exclude-movie/<id> returns {"excluded": false}."""
        auth_client.post('/exclude-movie/550')              # exclude
        response = auth_client.post('/exclude-movie/550')   # re-include
        data = json.loads(response.data)
        assert data['excluded'] is False


# ===========================================================================
# TC-031 to TC-035 — Reviews
# ===========================================================================

class TestReviews:

    def test_add_review_page_returns_200(self, client):
        """TC-031: GET /add-review returns HTTP 200."""
        response = client.get('/add-review')
        assert response.status_code == 200

    def test_valid_review_saves_to_db(self, auth_client, app):
        """TC-032: Valid POST /add-review saves a Review record and redirects."""
        response = auth_client.post('/add-review', data={
            'name':       'Alice',
            'movie_id':   '550',
            'movie_title': 'Fight Club',
            'rating':     '5',
            'comment':    'An absolute masterpiece of cinema.',
        }, follow_redirects=True)
        assert response.status_code == 200
        with app.app_context():
            assert Review.query.filter_by(movie_id=550).first() is not None

    def test_missing_name_shows_error(self, auth_client):
        """TC-033: Submitting a review without a name returns a field error."""
        response = auth_client.post('/add-review', data={
            'name':       '',
            'movie_id':   '550',
            'movie_title': 'Fight Club',
            'rating':     '4',
            'comment':    'A decent watch for sure.',
        })
        assert response.status_code == 200
        assert b'required' in response.data.lower()

    def test_short_comment_shows_error(self, auth_client):
        """TC-034: A comment shorter than 10 characters returns a field error."""
        response = auth_client.post('/add-review', data={
            'name':       'Alice',
            'movie_id':   '550',
            'movie_title': 'Fight Club',
            'rating':     '3',
            'comment':    'Too short',
        })
        assert response.status_code == 200
        assert b'10 characters' in response.data or b'at least' in response.data

    def test_invalid_rating_shows_error(self, auth_client):
        """TC-035: A rating outside 1–5 returns a field error."""
        response = auth_client.post('/add-review', data={
            'name':       'Alice',
            'movie_id':   '550',
            'movie_title': 'Fight Club',
            'rating':     '9',
            'comment':    'Rating is way too high to be valid here.',
        })
        assert response.status_code == 200
        assert b'between 1 and 5' in response.data or b'Rating' in response.data


# ===========================================================================
# TC-036 to TC-042 — Suggestions API
# ===========================================================================

class TestSuggestions:

    def test_suggestions_returns_valid_json(self, client):
        """TC-036: GET /suggestions returns HTTP 200 with valid JSON."""
        response = client.get('/suggestions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_suggestions_has_required_keys(self, client):
        """TC-037: Suggestions JSON contains 'suggestions' list and 'reason' string."""
        data = json.loads(client.get('/suggestions').data)
        assert 'suggestions' in data
        assert 'reason' in data
        assert isinstance(data['suggestions'], list)
        assert isinstance(data['reason'], str)

    def test_suggestions_excludes_watched_movies(self, auth_client, app, test_user):
        """TC-037: Watched movie ID does not appear in suggestions results."""
        with app.app_context():
            db.session.add(WatchedMovie(user_id=test_user.id, movie_id=550))
            db.session.commit()
        data = json.loads(auth_client.get('/suggestions').data)
        ids = [m['id'] for m in data['suggestions']]
        assert 550 not in ids

    def test_suggestions_excludes_excluded_movies(self, auth_client, app, test_user):
        """TC-038: Excluded movie ID does not appear in suggestions results."""
        with app.app_context():
            db.session.add(ExcludedMovie(user_id=test_user.id, movie_id=550))
            db.session.commit()
        data = json.loads(auth_client.get('/suggestions').data)
        ids = [m['id'] for m in data['suggestions']]
        assert 550 not in ids

    def test_suggestions_with_genre_filter(self, client):
        """TC-039: genre_ids param returns 200 with valid JSON."""
        response = client.get('/suggestions?genre_ids=28')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data

    def test_suggestions_with_decades_filter(self, client):
        """TC-040: decades param returns 200 with valid JSON."""
        response = client.get('/suggestions?decades=1990')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data

    def test_suggestions_with_age_rating_filter(self, client):
        """TC-041: age_ratings param returns 200 with valid JSON."""
        response = client.get('/suggestions?age_ratings=kids')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data

    def test_suggestions_with_language_filter(self, client):
        """TC-042: languages param returns 200 with valid JSON."""
        response = client.get('/suggestions?languages=fr')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data

    def test_suggestions_combined_filters(self, client):
        """TC-042 extension: All four filter params combined return 200 with valid JSON."""
        response = client.get('/suggestions?genre_ids=18&decades=1990&age_ratings=kids&languages=fr')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data


# ===========================================================================
# TC-043 — Mobile / viewport (automatable portion)
# ===========================================================================

class TestMobileViewport:

    def test_viewport_meta_tag_present(self, client):
        """TC-043: The <meta name='viewport'> tag is present in the base HTML."""
        response = client.get('/')
        assert b'name="viewport"' in response.data
