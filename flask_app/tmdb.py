import requests

# ---- Configuration ----
# Paste your free TMDB API key here.
# Get one at: themoviedb.org → Settings → API → Request an API Key
API_KEY = '370fd8222c137f1a48a5cf04d2bc9a70'

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
    params['api_key'] = API_KEY
    params['language'] = 'en-US'
    response = requests.get(f'{BASE_URL}{endpoint}', params=params, timeout=8)
    response.raise_for_status()
    return response.json()


def poster_url(path, size='w500'):
    if path:
        return f'{IMAGE_BASE}/{size}{path}'
    return None


def profile_url(path):
    if path:
        return f'{IMAGE_BASE}/w185{path}'
    return None


def genre_names(genre_ids):
    return [GENRE_MAP[gid] for gid in genre_ids if gid in GENRE_MAP]


def now_playing():
    return _get('/movie/now_playing')['results']


def popular():
    return _get('/movie/popular')['results']


def top_rated():
    return _get('/movie/top_rated')['results']


def upcoming():
    return _get('/movie/upcoming')['results']


def trending():
    return _get('/trending/movie/week')['results']


def search_movies(query):
    return _get('/search/movie', query=query)['results']


def movie_detail(tmdb_id):
    return _get(f'/movie/{tmdb_id}')


def movie_credits(tmdb_id):
    data = _get(f'/movie/{tmdb_id}/credits')
    cast = data.get('cast', [])[:8]
    director = next(
        (p['name'] for p in data.get('crew', []) if p['job'] == 'Director'),
        None
    )
    return cast, director


def similar(tmdb_id):
    return _get(f'/movie/{tmdb_id}/similar')['results'][:6]
