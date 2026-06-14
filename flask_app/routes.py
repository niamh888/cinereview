from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, login_user, logout_user, current_user

from extensions import db
from models import User, WatchedMovie, ExcludedMovie, Review, MovieCache
from utils import (
    cache_movie, check_password_strength, make_captcha,
    generate_reset_token, verify_reset_token, send_reset_email,
    send_feedback_email,
)
import tmdb


LAST_UPDATED = 'June 2026'

CATEGORIES = {
    'now_playing': 'Now Playing',
    'popular':     'Popular',
    'top_rated':   'Top Rated',
    'upcoming':    'Upcoming',
}

DECADES = {
    '1970': ('1970-01-01', '1979-12-31'),
    '1980': ('1980-01-01', '1989-12-31'),
    '1990': ('1990-01-01', '1999-12-31'),
    '2000': ('2000-01-01', '2009-12-31'),
    '2010': ('2010-01-01', '2019-12-31'),
    '2020': ('2020-01-01', '2029-12-31'),
}

# US certification ratings used for child-friendly filtering in the suggestions panel
AGE_RATINGS = {
    'little_ones': {'cert':     'G',     'label': 'Little Ones', 'desc': 'G rated'},
    'kids':        {'cert_lte': 'PG',    'label': 'Kids',        'desc': 'G & PG rated'},
    'tweens':      {'cert_lte': 'PG-13', 'label': 'Tweens',      'desc': 'up to PG-13'},
}

LANGUAGES = {
    'fr': 'French',
    'it': 'Italian',
    'es': 'Spanish',
    'de': 'German',
    'ko': 'Korean',
    'ja': 'Japanese',
    'hi': 'Hindi',
}


def register_routes(app):

    @app.context_processor
    def inject_tmdb():
        """Make tmdb helper functions available in every Jinja template without passing them manually."""
        return {
            'poster_url': tmdb.poster_url,
            'profile_url': tmdb.profile_url,
            'genre_names': tmdb.genre_names,
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
                               error=error, genres=genres, age_ratings=AGE_RATINGS,
                               languages=LANGUAGES)

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
        poster_path = None
        if movie_id_param:
            try:
                cached = db.session.get(MovieCache, int(movie_id_param))
                if cached:
                    movie_title = cached.title
                    poster_path = cached.poster_path
                else:
                    data = tmdb.movie_detail(int(movie_id_param))
                    movie_title = data.get('title', '')
                    poster_path = data.get('poster_path')
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

            if movie_id_raw:
                try:
                    cached = db.session.get(MovieCache, int(movie_id_raw))
                    if cached:
                        poster_path = cached.poster_path
                except Exception:
                    pass

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

        recent_watched = []
        if not movie_id_param and current_user.is_authenticated:
            entries = WatchedMovie.query.filter_by(
                user_id=current_user.id
            ).order_by(WatchedMovie.watched_at.desc()).limit(4).all()
            for entry in entries:
                cached = db.session.get(MovieCache, entry.movie_id)
                if not cached:
                    cached = cache_movie(entry.movie_id)
                if cached:
                    recent_watched.append(cached)

        return render_template('add_review.html', errors=errors, form_data=form_data,
                               poster_path=poster_path, recent_watched=recent_watched)

    @app.route('/suggestions')
    def suggestions():
        """Return up to 4 movie suggestions as JSON — filtered by genre and page if provided."""
        try:
            page = request.args.get('page', 1, type=int)

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

            # Parse comma-separated multi-select values from the query string
            genre_ids   = [int(g) for g in request.args.get('genre_ids', '').split(',')
                           if g.strip().isdigit()]
            decade_keys = [d for d in request.args.get('decades', '').split(',')
                           if d in DECADES]
            age_keys    = [a for a in request.args.get('age_ratings', '').split(',')
                           if a in AGE_RATINGS]
            lang_codes  = [l for l in request.args.get('languages', '').split(',')
                           if l in LANGUAGES]

            # Build TMDB discover params from multi-select values
            genre_param = '|'.join(str(g) for g in genre_ids) if genre_ids else None

            date_range = None
            if decade_keys:
                date_range = (min(DECADES[d][0] for d in decade_keys),
                              max(DECADES[d][1] for d in decade_keys))

            lang_param = '|'.join(lang_codes) if lang_codes else None

            # Take the most permissive age rating when multiple are selected
            certification = None
            age_priority = ['tweens', 'kids', 'little_ones']
            for key in age_priority:
                if key in age_keys:
                    info = AGE_RATINGS[key]
                    certification = ('lte', info['cert_lte']) if 'cert_lte' in info \
                                    else ('exact', info['cert'])
                    break

            if genre_ids or date_range or certification or lang_codes:
                picks = tmdb.discover(
                    genre_id=genre_param, date_range=date_range,
                    certification=certification, language=lang_param, page=page
                )
                genre_labels  = [tmdb.GENRE_MAP[g] for g in genre_ids if g in tmdb.GENRE_MAP]
                decade_labels = [f'{d}s' for d in decade_keys]
                age_labels    = [AGE_RATINGS[a]['label'] for a in age_keys]
                lang_labels   = [LANGUAGES[l] for l in lang_codes]

                parts = age_labels + lang_labels + genre_labels
                reason = 'Popular ' + (', '.join(parts) + ' films' if parts else 'films')
                if decade_labels:
                    reason += ' from the ' + ' & '.join(decade_labels)
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

    @app.route('/about', methods=['GET', 'POST'])
    def about():
        """Pass site-wide stats to the about page and handle the feedback form submission."""
        feedback_errors = {}
        feedback_sent = False
        feedback_data = {}

        if request.method == 'POST':
            name = request.form.get('feedback_name', '').strip()
            rating = request.form.get('feedback_rating', '').strip()
            comment = request.form.get('feedback_comment', '').strip()
            feedback_data = {'feedback_name': name, 'feedback_rating': rating,
                             'feedback_comment': comment}

            if not name:
                feedback_errors['feedback_name'] = 'Your name is required.'
            if not rating:
                feedback_errors['feedback_rating'] = 'Please select a star rating.'
            else:
                try:
                    r = int(rating)
                    if not 1 <= r <= 5:
                        feedback_errors['feedback_rating'] = 'Rating must be between 1 and 5.'
                except ValueError:
                    feedback_errors['feedback_rating'] = 'Invalid rating.'
            if not comment:
                feedback_errors['feedback_comment'] = 'Please write a comment.'
            elif len(comment) < 5:
                feedback_errors['feedback_comment'] = 'Comment is too short.'

            if not feedback_errors:
                send_feedback_email(name, rating, comment)
                feedback_sent = True
                feedback_data = {}

        total_reviews = Review.query.count()
        total_users = User.query.count()
        total_watched = WatchedMovie.query.count()
        return render_template('about.html', total_reviews=total_reviews,
                               total_users=total_users, total_watched=total_watched,
                               last_updated=LAST_UPDATED,
                               feedback_errors=feedback_errors,
                               feedback_sent=feedback_sent,
                               feedback_data=feedback_data)
