from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ucd-flask-assignment-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cinereview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to use this feature.'
login_manager.login_message_category = 'error'

MOVIES = [
    {
        'id': 1,
        'title': 'Inception',
        'year': 2010,
        'genre': 'Sci-Fi',
        'director': 'Christopher Nolan',
        'description': 'A skilled thief is offered a chance to have his criminal record erased if he can successfully perform inception — planting an idea into someone\'s mind.',
        'rating': 8.8,
    },
    {
        'id': 2,
        'title': 'The Shawshank Redemption',
        'year': 1994,
        'genre': 'Drama',
        'director': 'Frank Darabont',
        'description': 'Two imprisoned men bond over years, finding solace and eventual redemption through acts of common decency.',
        'rating': 9.3,
    },
    {
        'id': 3,
        'title': 'The Dark Knight',
        'year': 2008,
        'genre': 'Action',
        'director': 'Christopher Nolan',
        'description': 'Batman faces the Joker, a criminal mastermind who seeks to plunge Gotham City into anarchy.',
        'rating': 9.0,
    },
    {
        'id': 4,
        'title': 'Pulp Fiction',
        'year': 1994,
        'genre': 'Crime',
        'director': 'Quentin Tarantino',
        'description': 'The lives of two mob hitmen, a boxer, a gangster and his wife intertwine in four tales of violence and redemption.',
        'rating': 8.9,
    },
    {
        'id': 5,
        'title': 'Interstellar',
        'year': 2014,
        'genre': 'Sci-Fi',
        'director': 'Christopher Nolan',
        'description': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
        'rating': 8.6,
    },
]


# ---- Models ----

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class WatchedMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id'),)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---- Routes ----

@app.route('/')
def index():
    genres = sorted(set(m['genre'] for m in MOVIES))
    watched_ids = set()
    if current_user.is_authenticated:
        watched_ids = {w.movie_id for w in WatchedMovie.query.filter_by(user_id=current_user.id).all()}
    return render_template('index.html', movies=MOVIES, genres=genres, watched_ids=watched_ids)


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    film = next((m for m in MOVIES if m['id'] == movie_id), None)
    if film is None:
        return render_template('404.html'), 404
    movie_reviews = Review.query.filter_by(movie_id=movie_id).order_by(Review.created_at.desc()).all()
    watched = False
    if current_user.is_authenticated:
        watched = WatchedMovie.query.filter_by(user_id=current_user.id, movie_id=movie_id).first() is not None
    return render_template('movie.html', movie=film, reviews=movie_reviews, watched=watched)


@app.route('/toggle-watched/<int:movie_id>', methods=['POST'])
@login_required
def toggle_watched(movie_id):
    if not any(m['id'] == movie_id for m in MOVIES):
        return jsonify({'error': 'Movie not found'}), 404
    existing = WatchedMovie.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'watched': False})
    db.session.add(WatchedMovie(user_id=current_user.id, movie_id=movie_id))
    db.session.commit()
    return jsonify({'watched': True})


@app.route('/my-movies')
@login_required
def my_movies():
    watched_ids = {w.movie_id for w in WatchedMovie.query.filter_by(user_id=current_user.id).all()}
    watched_movies = [m for m in MOVIES if m['id'] in watched_ids]
    unwatched_movies = [m for m in MOVIES if m['id'] not in watched_ids]
    return render_template('my_movies.html', watched_movies=watched_movies, unwatched_movies=unwatched_movies)


@app.route('/add-review', methods=['GET', 'POST'])
def add_review():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        movie_id_raw = request.form.get('movie_id', '').strip()
        rating_raw = request.form.get('rating', '').strip()
        comment = request.form.get('comment', '').strip()

        form_data = {'name': name, 'movie_id': movie_id_raw, 'rating': rating_raw, 'comment': comment}

        if not name:
            errors['name'] = 'Your name is required.'
        elif len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters.'

        if not movie_id_raw:
            errors['movie_id'] = 'Please select a movie.'
        else:
            try:
                movie_id = int(movie_id_raw)
                if not any(m['id'] == movie_id for m in MOVIES):
                    errors['movie_id'] = 'Invalid movie selected.'
            except ValueError:
                errors['movie_id'] = 'Invalid movie selected.'

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

    preselect = request.args.get('movie_id', '')
    if not form_data:
        form_data['movie_id'] = preselect
    if not form_data.get('name') and current_user.is_authenticated:
        form_data['name'] = current_user.username

    return render_template('add_review.html', movies=MOVIES, errors=errors, form_data=form_data)


@app.route('/suggestions')
def suggestions():
    good_reviews = Review.query.filter(Review.rating >= 4).all()
    if good_reviews:
        genre_counts = {}
        for r in good_reviews:
            movie = next((m for m in MOVIES if m['id'] == r.movie_id), None)
            if movie:
                genre_counts[movie['genre']] = genre_counts.get(movie['genre'], 0) + 1
        top_genre = max(genre_counts, key=genre_counts.get)
        picks = sorted([m for m in MOVIES if m['genre'] == top_genre], key=lambda m: m['rating'], reverse=True)[:3]
        reason = f'Based on highly-rated {top_genre} reviews'
    else:
        picks = sorted(MOVIES, key=lambda m: m['rating'], reverse=True)[:3]
        reason = 'Top rated films in our catalogue'
    return jsonify({'suggestions': picks, 'reason': reason})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    errors = {}
    form_data = {}

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        form_data = {'username': username, 'email': email}

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
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters.'

        if password and not errors.get('password') and password != confirm:
            errors['confirm_password'] = 'Passwords do not match.'

        if not errors:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f'Welcome to CineReview, {username}!', 'success')
            return redirect(url_for('index'))

    return render_template('register.html', errors=errors, form_data=form_data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    errors = {}
    form_data = {}

    if request.method == 'POST':
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
            else:
                errors['general'] = 'Incorrect username or password.'

    return render_template('login.html', errors=errors, form_data=form_data)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/about')
def about():
    total_reviews = Review.query.count()
    top_movie = max(MOVIES, key=lambda m: m['rating'])
    return render_template('about.html', total_reviews=total_reviews, top_movie=top_movie, movie_count=len(MOVIES))


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
