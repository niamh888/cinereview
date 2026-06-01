from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import os
import re
import random
import tmdb

app = Flask(__name__)

# Secret key — set SECRET_KEY environment variable in production
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-key-change-in-production')

# Database — uses PostgreSQL in production (DATABASE_URL env var), SQLite locally
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///cinereview.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email — set MAIL_USERNAME and MAIL_PASSWORD environment variables in production
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to use this feature.'
login_manager.login_message_category = 'error'


# ---- Models ----

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        """Hash the password and store it — never stores the plain text."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)


class WatchedMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id'),)


class ExcludedMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id'),)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MovieCache(db.Model):
    tmdb_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(4))
    poster_path = db.Column(db.String(200))
    genres = db.Column(db.String(200))
    vote_average = db.Column(db.Float)


@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to reload the logged-in user from the database on each request."""
    return db.session.get(User, int(user_id))


# ---- Helpers ----

@app.context_processor
def inject_tmdb():
    """Make tmdb helper functions available in every Jinja template without passing them manually."""
    return {
        'poster_url': tmdb.poster_url,
        'profile_url': tmdb.profile_url,
        'genre_names': tmdb.genre_names,
    }


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
    s = URLSafeTimedSerializer(app.secret_key)
    return s.dumps(email, salt='password-reset-salt')


def verify_reset_token(token, max_age=3600):
    """Decode a reset token and return the email, or None if the token is expired or tampered with."""
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=max_age)
    except Exception:
        return None
    return email


def send_reset_email(user, token):
    """Email a password reset link to the user; falls back to printing it in the console if mail fails."""
    reset_url = url_for('reset_password', token=token, _external=True)
    try:
        msg = Message(
            subject='CineReview — Password Reset Request',
            sender=app.config['MAIL_USERNAME'],
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


# ---- Routes ----

CATEGORIES = {
    'now_playing': 'Now Playing',
    'popular':     'Popular',
    'top_rated':   'Top Rated',
    'upcoming':    'Upcoming',
}


@app.route('/')
def index():
    """Home page — fetch a list of movies from TMDB for the selected category tab."""
    category = request.args.get('category', 'now_playing')
    if category not in CATEGORIES:
        category = 'now_playing'

    movies = []
    error = None
    try:
        fn = {
            'now_playing': tmdb.now_playing,
            'popular':     tmdb.popular,
            'top_rated':   tmdb.top_rated,
            'upcoming':    tmdb.upcoming,
        }[category]
        movies = fn()
    except Exception:
        error = 'Could not reach TMDB. Check your API key or internet connection.'

    watched_ids = set()
    excluded_ids = set()
    if current_user.is_authenticated:
        watched_ids = {
            w.movie_id for w in WatchedMovie.query.filter_by(user_id=current_user.id).all()
        }
        excluded_ids = {
            e.movie_id for e in ExcludedMovie.query.filter_by(user_id=current_user.id).all()
        }
        movies = [m for m in movies if m['id'] not in excluded_ids]

    genres = sorted(tmdb.GENRE_MAP.items(), key=lambda x: x[1])
    return render_template('index.html', movies=movies, category=category,
                           categories=CATEGORIES, watched_ids=watched_ids,
                           error=error, genres=genres)


@app.route('/search')
def search():
    """Search TMDB for movies matching the user's query and display the results."""
    query = request.args.get('q', '').strip()
    movies = []
    error = None

    if query:
        try:
            movies = tmdb.search_movies(query)
        except Exception:
            error = 'Search failed. Please try again.'

    watched_ids = set()
    if current_user.is_authenticated:
        watched_ids = {
            w.movie_id for w in WatchedMovie.query.filter_by(user_id=current_user.id).all()
        }

    return render_template('search.html', movies=movies, query=query,
                           watched_ids=watched_ids, error=error)


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    """Fetch full movie details, cast, and stored reviews for a single film's page."""
    try:
        film = tmdb.movie_detail(movie_id)
        cast, director = tmdb.movie_credits(movie_id)
    except Exception:
        return render_template('404.html'), 404

    movie_reviews = Review.query.filter_by(
        movie_id=movie_id
    ).order_by(Review.created_at.desc()).all()

    watched = False
    excluded = False
    if current_user.is_authenticated:
        watched = WatchedMovie.query.filter_by(
            user_id=current_user.id, movie_id=movie_id
        ).first() is not None
        excluded = ExcludedMovie.query.filter_by(
            user_id=current_user.id, movie_id=movie_id
        ).first() is not None

    return render_template('movie.html', movie=film, cast=cast, director=director,
                           reviews=movie_reviews, watched=watched, excluded=excluded)


@app.route('/toggle-watched/<int:movie_id>', methods=['POST'])
@login_required
def toggle_watched(movie_id):
    """Add or remove a movie from the current user's watched list and return the new state as JSON."""
    existing = WatchedMovie.query.filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'watched': False})
    db.session.add(WatchedMovie(user_id=current_user.id, movie_id=movie_id))
    db.session.commit()
    cache_movie(movie_id)
    return jsonify({'watched': True})


@app.route('/exclude-movie/<int:movie_id>', methods=['POST'])
@login_required
def exclude_movie(movie_id):
    """Mark a movie as 'No Thanks' so it is hidden from the grid and suggestions."""
    existing = ExcludedMovie.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'excluded': False})
    db.session.add(ExcludedMovie(user_id=current_user.id, movie_id=movie_id))
    db.session.commit()
    return jsonify({'excluded': True})


@app.route('/my-movies')
@login_required
def my_movies():
    """Show all movies the logged-in user has marked as watched, loading details from the local cache."""
    watched_entries = WatchedMovie.query.filter_by(
        user_id=current_user.id
    ).order_by(WatchedMovie.watched_at.desc()).all()

    watched_movies = []
    for entry in watched_entries:
        cached = db.session.get(MovieCache, entry.movie_id)
        if not cached:
            cached = cache_movie(entry.movie_id)
        if cached:
            watched_movies.append(cached)

    return render_template('my_movies.html', watched_movies=watched_movies)


@app.route('/add-review', methods=['GET', 'POST'])
def add_review():
    """Display and handle the review form; validate input then save the review to the database."""
    errors = {}
    movie_id_param = request.args.get('movie_id', '').strip()

    movie_title = ''
    if movie_id_param:
        try:
            cached = db.session.get(MovieCache, int(movie_id_param))
            if cached:
                movie_title = cached.title
            else:
                data = tmdb.movie_detail(int(movie_id_param))
                movie_title = data.get('title', '')
        except Exception:
            pass

    form_data = {'movie_id': movie_id_param, 'movie_title': movie_title}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        movie_id_raw = request.form.get('movie_id', '').strip()
        movie_title = request.form.get('movie_title', '')
        rating_raw = request.form.get('rating', '').strip()
        comment = request.form.get('comment', '').strip()

        form_data = {
            'name': name, 'movie_id': movie_id_raw,
            'movie_title': movie_title, 'rating': rating_raw, 'comment': comment,
        }

        if not name:
            errors['name'] = 'Your name is required.'
        elif len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters.'

        if not movie_id_raw:
            errors['movie_id'] = 'No movie selected — please find a film first.'
        else:
            try:
                int(movie_id_raw)
            except ValueError:
                errors['movie_id'] = 'Invalid movie.'

        if not rating_raw:
            errors['rating'] = 'A rating is required.'
        else:
            try:
                rating = int(rating_raw)
                if not 1 <= rating <= 5:
                    errors['rating'] = 'Rating must be between 1 and 5.'
            except ValueError:
                errors['rating'] = 'Rating must be a whole number between 1 and 5.'

        if not comment:
            errors['comment'] = 'A review comment is required.'
        elif len(comment) < 10:
            errors['comment'] = 'Comment must be at least 10 characters.'

        if not errors:
            db.session.add(Review(
                movie_id=int(movie_id_raw),
                name=name,
                rating=int(rating_raw),
                comment=comment,
            ))
            db.session.commit()
            flash('Your review has been submitted — thank you!', 'success')
            return redirect(url_for('movie_detail', movie_id=int(movie_id_raw)))

    if not form_data.get('name') and current_user.is_authenticated:
        form_data['name'] = current_user.username

    return render_template('add_review.html', errors=errors, form_data=form_data)


@app.route('/suggestions')
def suggestions():
    """Return up to 4 movie suggestions as JSON — filtered by genre and page if provided."""
    try:
        page = request.args.get('page', 1, type=int)
        genre_id = request.args.get('genre_id', None, type=int)

        watched_ids = set()
        excluded_ids = set()
        if current_user.is_authenticated:
            watched_ids = {
                w.movie_id for w in WatchedMovie.query.filter_by(user_id=current_user.id).all()
            }
            excluded_ids = {
                e.movie_id for e in ExcludedMovie.query.filter_by(user_id=current_user.id).all()
            }

        skip_ids = watched_ids | excluded_ids

        if genre_id:
            picks = tmdb.discover_by_genre(genre_id, page)
            reason = f'Popular {tmdb.GENRE_MAP.get(genre_id, "genre")} films'
        elif current_user.is_authenticated:
            last = WatchedMovie.query.filter_by(
                user_id=current_user.id
            ).order_by(WatchedMovie.watched_at.desc()).first()
            if last:
                picks = tmdb.similar(last.movie_id, page)
                reason = 'Because of films you have watched'
            else:
                picks = tmdb.trending(page)
                reason = 'Trending this week'
        else:
            picks = tmdb.trending(page)
            reason = 'Trending this week'

        filtered = [m for m in picks if m['id'] not in skip_ids]

        results = [
            {
                'id': m['id'],
                'title': m['title'],
                'year': m.get('release_date', '')[:4],
                'genre': tmdb.genre_names(m.get('genre_ids', []))[0]
                         if tmdb.genre_names(m.get('genre_ids', [])) else '',
                'rating': round(m.get('vote_average', 0), 1),
                'poster': tmdb.poster_url(m.get('poster_path'), 'w200'),
            }
            for m in filtered[:4]
        ]
        return jsonify({'suggestions': results, 'reason': reason})
    except Exception:
        return jsonify({'suggestions': [], 'reason': 'Could not load suggestions'})


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new account creation — validate all fields including CAPTCHA, then log the user in."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    errors = {}
    form_data = {}

    if request.method == 'GET':
        captcha_question = make_captcha()
        return render_template('register.html', errors=errors, form_data=form_data,
                               captcha_question=captcha_question)

    if request.form.get('website', ''):
        return redirect(url_for('index'))

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    captcha_input = request.form.get('captcha', '').strip()

    form_data = {'username': username, 'email': email}

    try:
        if not captcha_input or int(captcha_input) != session.get('captcha_answer'):
            errors['captcha'] = 'Incorrect answer — please try again.'
    except ValueError:
        errors['captcha'] = 'Please enter a number.'

    if not username:
        errors['username'] = 'Username is required.'
    elif len(username) < 3:
        errors['username'] = 'Username must be at least 3 characters.'
    elif len(username) > 20:
        errors['username'] = 'Username must be 20 characters or fewer.'
    elif not username.replace('_', '').isalnum():
        errors['username'] = 'Username can only contain letters, numbers, and underscores.'
    elif User.query.filter_by(username=username).first():
        errors['username'] = 'That username is already taken.'

    if not email:
        errors['email'] = 'Email is required.'
    elif '@' not in email or '.' not in email.split('@')[-1]:
        errors['email'] = 'Please enter a valid email address.'
    elif User.query.filter_by(email=email).first():
        errors['email'] = 'An account with that email already exists.'

    if not password:
        errors['password'] = 'Password is required.'
    else:
        strength_issues = check_password_strength(password)
        if strength_issues:
            errors['password'] = f'Password must include: {", ".join(strength_issues)}.'

    if password and not errors.get('password') and password != confirm:
        errors['confirm_password'] = 'Passwords do not match.'

    if errors:
        captcha_question = make_captcha()
        return render_template('register.html', errors=errors, form_data=form_data,
                               captcha_question=captcha_question)

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash(f'Welcome to CineReview, {username}!', 'success')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate the user and redirect them to wherever they were trying to go."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    errors = {}
    form_data = {}

    if request.method == 'POST':
        if request.form.get('website', ''):
            return redirect(url_for('index'))

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        form_data = {'username': username}

        if not username:
            errors['username'] = 'Username is required.'
        if not password:
            errors['password'] = 'Password is required.'

        if not errors:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash(f'Welcome back, {user.username}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            errors['general'] = 'Incorrect username or password.'

    return render_template('login.html', errors=errors, form_data=form_data)


@app.route('/logout')
@login_required
def logout():
    """Clear the user's session and redirect to the home page."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Accept an email address and send a reset link if an account exists (always shows success to avoid leaking emails)."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    errors = {}
    submitted = False

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors['email'] = 'Please enter a valid email address.'

        if not errors:
            user = User.query.filter_by(email=email).first()
            if user:
                token = generate_reset_token(email)
                send_reset_email(user, token)
            submitted = True

    return render_template('forgot_password.html', errors=errors, submitted=submitted)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Verify the reset token then let the user set a new password; reject expired or invalid tokens."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    email = verify_reset_token(token)
    if not email:
        flash('That reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'error')
        return redirect(url_for('forgot_password'))

    errors = {}

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not password:
            errors['password'] = 'Password is required.'
        else:
            strength_issues = check_password_strength(password)
            if strength_issues:
                errors['password'] = f'Password must include: {", ".join(strength_issues)}.'

        if password and not errors.get('password') and password != confirm:
            errors['confirm_password'] = 'Passwords do not match.'

        if not errors:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been updated. Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html', errors=errors, token=token)


@app.route('/about')
def about():
    """Pass site-wide stats (review count, user count, watched count) to the about page."""
    total_reviews = Review.query.count()
    total_users = User.query.count()
    total_watched = WatchedMovie.query.count()
    return render_template('about.html', total_reviews=total_reviews,
                           total_users=total_users, total_watched=total_watched)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
