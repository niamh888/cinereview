from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'ucd-flask-assignment-secret'

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

reviews = []


@app.route('/')
def index():
    genres = sorted(set(m['genre'] for m in MOVIES))
    return render_template('index.html', movies=MOVIES, genres=genres)


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    film = next((m for m in MOVIES if m['id'] == movie_id), None)
    if film is None:
        return render_template('404.html'), 404
    movie_reviews = [r for r in reviews if r['movie_id'] == movie_id]
    return render_template('movie.html', movie=film, reviews=movie_reviews)


@app.route('/add-review', methods=['GET', 'POST'])
def add_review():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        movie_id_raw = request.form.get('movie_id', '').strip()
        rating_raw = request.form.get('rating', '').strip()
        comment = request.form.get('comment', '').strip()

        form_data = {
            'name': name,
            'movie_id': movie_id_raw,
            'rating': rating_raw,
            'comment': comment,
        }

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
            reviews.append({
                'movie_id': int(movie_id_raw),
                'name': name,
                'rating': int(rating_raw),
                'comment': comment,
            })
            flash('Your review has been submitted — thank you!', 'success')
            return redirect(url_for('movie_detail', movie_id=int(movie_id_raw)))

    preselect = request.args.get('movie_id', '')
    if not form_data:
        form_data['movie_id'] = preselect

    return render_template('add_review.html', movies=MOVIES, errors=errors, form_data=form_data)


@app.route('/about')
def about():
    total_reviews = len(reviews)
    top_movie = max(MOVIES, key=lambda m: m['rating'])
    return render_template('about.html', total_reviews=total_reviews, top_movie=top_movie, movie_count=len(MOVIES))


if __name__ == '__main__':
    app.run(debug=True)
