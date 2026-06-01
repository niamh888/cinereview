"""TMDB API helpers — thin wrappers around the TMDB v3 REST API."""
import os
import requests

# Set TMDB_API_KEY as an environment variable in production
API_KEY = os.environ.get('TMDB_API_KEY')

BASE_URL = 'https://api.themoviedb.org/3'
IMAGE_BASE = 'https://image.tmdb.org/t/p'

GENRE_MAP = {
    28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy',
    80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
    14: 'Fantasy', 36: 'History', 27: 'Horror', 10402: 'Music',
    9648: 'Mystery', 10749: 'Romance', 878: 'Sci-Fi', 53: 'Thriller',
    10752: 'War', 37: 'Western',
}


def _get(endpoint, **params):
    """Internal helper — adds the API key and language to every TMDB request."""
    params['api_key'] = API_KEY
    params['language'] = 'en-US'
    response = requests.get(f'{BASE_URL}{endpoint}', params=params, timeout=8)
    response.raise_for_status()
    return response.json()


def poster_url(path, size='w500'):
    """Build the full URL for a movie poster image; returns None if no poster exists."""
    if path:
        return f'{IMAGE_BASE}/{size}{path}'
    return None


def profile_url(path):
    """Build the full URL for a cast member's profile photo at 185px width."""
    if path:
        return f'{IMAGE_BASE}/w185{path}'
    return None


def genre_names(genre_ids):
    """Convert a list of TMDB genre IDs into readable genre name strings."""
    return [GENRE_MAP[gid] for gid in genre_ids if gid in GENRE_MAP]


def now_playing():
    """Return movies currently showing in cinemas."""
    return _get('/movie/now_playing')['results']


def popular():
    """Return currently popular movies on TMDB."""
    return _get('/movie/popular')['results']


def top_rated():
    """Return the highest-rated movies on TMDB."""
    return _get('/movie/top_rated')['results']


def upcoming():
    """Return movies that have not yet been released."""
    return _get('/movie/upcoming')['results']


def trending():
    """Return movies that are trending across TMDB this week."""
    return _get('/trending/movie/week')['results']


def search_movies(query):
    """Search TMDB for movies matching the given text query."""
    return _get('/search/movie', query=query)['results']


def movie_detail(tmdb_id):
    """Return the full detail object for a single movie by its TMDB ID."""
    return _get(f'/movie/{tmdb_id}')


def movie_credits(tmdb_id):
    """Return the top 8 cast members and the director's name for a given movie."""
    data = _get(f'/movie/{tmdb_id}/credits')
    cast = data.get('cast', [])[:8]
    director = next(
        (p['name'] for p in data.get('crew', []) if p['job'] == 'Director'),
        None
    )
    return cast, director


def similar(tmdb_id):
    """Return up to 6 movies similar to the given movie, used for suggestions."""
    return _get(f'/movie/{tmdb_id}/similar')['results'][:6]
