import random
import re

from flask import current_app, session, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from extensions import db, mail
from models import MovieCache
import tmdb


def cache_movie(tmdb_id):
    """Save basic movie info to the local database so it can be shown without calling TMDB again."""
    cached = db.session.get(MovieCache, tmdb_id)
    if cached:
        return cached
    try:
        data = tmdb.movie_detail(tmdb_id)
        cached = MovieCache(
            tmdb_id=tmdb_id,
            title=data['title'],
            year=data.get('release_date', '')[:4],
            poster_path=data.get('poster_path'),
            genres=', '.join(g['name'] for g in data.get('genres', [])[:3]),
            vote_average=data.get('vote_average'),
        )
        db.session.add(cached)
        db.session.commit()
    except Exception:
        return None
    return cached


def check_password_strength(password):
    """Return a list of unmet requirements; an empty list means the password is strong enough."""
    issues = []
    if len(password) < 8:
        issues.append('at least 8 characters')
    if not re.search(r'[A-Z]', password):
        issues.append('an uppercase letter')
    if not re.search(r'[a-z]', password):
        issues.append('a lowercase letter')
    if not re.search(r'\d', password):
        issues.append('a number')
    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?]', password):
        issues.append('a special character (!@#$ etc.)')
    return issues


def make_captcha():
    """Generate a simple addition question and store the answer in the session for later verification."""
    a = random.randint(2, 15)
    b = random.randint(2, 15)
    session['captcha_answer'] = a + b
    return f"{a} + {b}"


def generate_reset_token(email):
    """Create a signed, time-limited token containing the user's email for password reset links."""
    s = URLSafeTimedSerializer(current_app.secret_key)
    return s.dumps(email, salt='password-reset-salt')


def verify_reset_token(token, max_age=3600):
    """Decode a reset token and return the email, or None if the token is expired or tampered with."""
    s = URLSafeTimedSerializer(current_app.secret_key)
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=max_age)
    except Exception:
        return None
    return email


def send_feedback_email(name, rating, comment):
    """Forward a CineReview feedback submission to the site owner's inbox."""
    stars = '★' * int(rating) + '☆' * (5 - int(rating))
    try:
        msg = Message(
            subject=f'CineReview Feedback — {stars} ({rating}/5)',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=['niamh@stjohnlynch.com'],
            body=(
                f"New feedback submitted on CineReview:\n\n"
                f"Name:   {name}\n"
                f"Rating: {rating}/5  {stars}\n\n"
                f"Comment:\n{comment}\n"
            ),
        )
        mail.send(msg)
        return True
    except Exception:
        print(f'\n[DEV] Feedback from {name}: {rating}/5 — {comment}\n')
        return False


def send_reset_email(user, token):
    """Email a password reset link to the user; falls back to printing it in the console if mail fails."""
    reset_url = url_for('reset_password', token=token, _external=True)
    try:
        msg = Message(
            subject='CineReview — Password Reset Request',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[user.email],
            body=(
                f"Hello {user.username},\n\n"
                f"Click the link below to reset your password (valid for 1 hour):\n"
                f"{reset_url}\n\n"
                f"If you did not request this, you can safely ignore this email.\n"
            ),
        )
        mail.send(msg)
        return True
    except Exception:
        print(f'\n[DEV] Password reset link for {user.email}:\n  {reset_url}\n')
        return False
