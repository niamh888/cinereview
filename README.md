# CineReview

A Flask web application for discovering movies and writing reviews. Movie data is pulled live from [The Movie Database (TMDB)](https://www.themoviedb.org/), while user accounts and reviews are stored locally.

---

## The Idea

This project came from a very relatable problem — my husband and I could never remember which movies we had already watched together. We'd settle in, start a film, and about 10 minutes in one of us would say *"we've watched this"* or *"this is familiar..."*.

CineReview was built to solve exactly that: a simple way to log the movies you've watched so you never have to sit through the first 10 minutes of a film you've already seen.

---

## Features

- Browse movies by category: Now Playing, Popular, Top Rated, Upcoming
- Search for any film via TMDB
- Read and write reviews (1–5 star rating + comment)
- Mark movies as watched and view your personal watched list
- Personalised suggestions based on your last watched film
- User accounts with registration, login, and password reset by email

---

## Project Structure

```
cinereview/
├── flask_app/
│   ├── app.py            # Main Flask application — routes, models, and helper functions
│   ├── tmdb.py           # Wrapper functions for the TMDB API
│   ├── requirements.txt  # Python dependencies
│   ├── Procfile          # Tells Render how to start the app in production
│   ├── templates/        # HTML templates (Jinja2)
│   │   ├── base.html     # Shared layout — navbar, head, footer
│   │   ├── index.html    # Home page
│   │   ├── movie.html    # Individual film page
│   │   ├── add_review.html
│   │   ├── my_movies.html
│   │   ├── search.html
│   │   ├── register.html
│   │   ├── login.html
│   │   ├── forgot_password.html
│   │   ├── reset_password.html
│   │   ├── about.html
│   │   └── 404.html
│   └── static/
│       └── style.css     # All site styles
```

---

## How Templates Work

All pages inherit from `base.html` using Jinja2's template inheritance system:

```html
{% extends "base.html" %}
```

This means `base.html` defines the shared structure (navbar, `<head>` tags, CSS links) once, and every other page slots its unique content into named blocks:

```html
{% block content %}
  <!-- page-specific HTML goes here -->
{% endblock %}
```

This way, changes to the navbar or layout only need to be made in one place.

### Comment syntax across file types

Each file type uses its own comment syntax:

| File type | Syntax | Notes |
|-----------|--------|-------|
| Python (`.py`) | `# comment` | Processed by Python; never sent to the browser |
| Jinja2 templates (`.html`) | `{# comment #}` | Stripped by Jinja2 before HTML is sent to the browser |
| HTML | `<!-- comment -->` | Sent to the browser and visible in "View Source" |
| CSS (`.css`) | `/* comment */` | Sent to the browser but ignored by the rendering engine |

Jinja2's `{# #}` is preferred over HTML `<!-- -->` inside templates because it never reaches the user's browser.

---

## Running Locally

1. **Clone the repo and create a virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # Mac/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r flask_app/requirements.txt
   ```

3. **Set environment variables** (or create a `.env` file):
   ```
   TMDB_API_KEY=your_tmdb_api_key
   SECRET_KEY=any_random_secret_string
   ```

4. **Run the app:**
   ```bash
   cd flask_app
   flask run
   ```
   Then open `http://localhost:5000` in your browser.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web framework |
| Flask-SQLAlchemy | Database ORM (SQLite locally, PostgreSQL in production) |
| Flask-Login | User session management |
| Flask-Mail | Sending password reset emails |
| requests | Making HTTP calls to the TMDB API |
| gunicorn | Production web server (used on Render) |
| psycopg2-binary | PostgreSQL driver for production |

---

## Deployment

The app is configured to deploy on [Render](https://render.com). The `Procfile` tells Render to start the app with:

```
web: gunicorn app:app
```

Set the following environment variables in your Render dashboard:
- `SECRET_KEY`
- `TMDB_API_KEY`
- `DATABASE_URL` (provided automatically by Render's PostgreSQL add-on)
- `MAIL_USERNAME` and `MAIL_PASSWORD` (optional — for password reset emails)
