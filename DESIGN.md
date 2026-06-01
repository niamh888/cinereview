# CineReview — Design Plan

A reference document describing the visual design, colour palette, layout, and component styles used across the site.

---

## Design Principles

- **Clean and content-first** — movie posters and titles take centre stage; chrome is minimal
- **Light theme with dark navigation** — pale blue-grey page background, dark navy navbar and footer for contrast
- **Consistent card-based layout** — content is grouped into white rounded cards with subtle shadows
- **Indigo as the primary accent** — used for buttons, links, active states, and key stats

---

## Framework Choice — Flask vs Django

CineReview is built with **Flask**, a lightweight Python web framework. Python offers several web frameworks; the two most common are Flask and Django.

| | Flask | Django |
|---|---|---|
| **Philosophy** | "Micro" — bring your own pieces | "Batteries included" — everything built in |
| **ORM** | You choose (e.g. SQLAlchemy) | Built-in Django ORM |
| **Auth** | You add it (e.g. Flask-Login) | Built-in |
| **Admin panel** | You build it | Auto-generated |
| **Project structure** | Flexible, you decide | Opinionated, enforced |

### Why Flask was chosen for this project

- **Appropriate scale** — CineReview is a medium-small application. Flask adds only what is needed and avoids the overhead of Django's full stack for a project of this size.
- **Transparency** — Flask makes it easy to see exactly what is happening at each step (routing, template rendering, database access). This is valuable for a learning project where understanding the mechanics matters.
- **Flexibility** — the database layer (SQLAlchemy + PostgreSQL), authentication (Flask-Login), and email (Flask-Mail) were each chosen and wired up deliberately, rather than inherited from a framework's defaults.
- **REST API suitability** — CineReview consumes the TMDB external API; Flask is well suited to applications that bridge an external API and a database without needing Django's full model-admin-auth machinery.

Django would be the better choice for a larger team project where built-in conventions reduce friction, or where the auto-generated admin panel and built-in auth would save significant time. For a focused solo project with custom requirements, Flask's simplicity is the right fit.

---

## Flask Routing

Flask routing maps a URL to a Python function using the `@app.route()` decorator. When a browser requests a URL, Flask looks it up in an internal table of URL → function pairs and calls the matching function.

### URL parameters

Parts of the URL can be captured and passed as function arguments using converters:

```python
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    ...
```

`<int:movie_id>` tells Flask to extract that segment, convert it to an integer, and pass it as `movie_id`. If anything other than an integer appears there Flask returns a 400 error automatically — no extra validation needed.

### HTTP methods

By default a route only accepts GET requests. POST (and others) must be declared explicitly:

```python
@app.route('/add-review', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        ...  # handle form submission
    return render_template('add_review.html')
```

A single function handles both requests by branching on `request.method` — this is the pattern used for every form route in this project.

### `url_for()` — reverse lookup

Instead of hard-coding a URL like `/movie/123` in templates or redirects, `url_for()` generates the correct URL from the function name:

```python
url_for('movie_detail', movie_id=123)   # → '/movie/123'
```

If a route is ever renamed or restructured, only the decorator changes — every template and redirect using `url_for()` updates automatically.

### Routes in this project

This project registers 11 routes in `app.py`:

| URL | Function | Methods |
|---|---|---|
| `/` | `index` | GET |
| `/search` | `search` | GET |
| `/movie/<int:movie_id>` | `movie_detail` | GET |
| `/add-review` | `add_review` | GET, POST |
| `/toggle-watched/<int:movie_id>` | `toggle_watched` | POST |
| `/exclude-movie/<int:movie_id>` | `exclude_movie` | POST |
| `/suggestions` | `suggestions` | GET |
| `/my-movies` | `my_movies` | GET |
| `/register` | `register` | GET, POST |
| `/login` | `login` | GET, POST |
| `/logout` | `logout` | GET |
| `/forgot-password` | `forgot_password` | GET, POST |
| `/reset-password/<token>` | `reset_password` | GET, POST |
| `/about` | `about` | GET |

Routes that require a logged-in user are protected with the `@login_required` decorator, which stacks on top of `@app.route()`. Flask processes decorators from the inside out — the route is registered first, then the login check wraps it.

---

## `render_template()`

`render_template()` is the Flask function that connects a route to an HTML file. When a route is ready to send a response, it calls `render_template()` with a template filename and any data the template needs:

```python
return render_template('index.html', movies=movies, categories=CATEGORIES)
```

Flask then:
1. Finds the file in the `templates/` folder
2. Passes the keyword arguments in as Jinja2 variables
3. Processes any Jinja2 tags (`{% for %}`, `{% if %}`, `{{ }}`)
4. Returns the fully built HTML string to the browser

Without it, a route would have to return raw HTML strings from Python — messy and unmaintainable. `render_template()` is what enforces the separation between logic (Python) and presentation (HTML templates).

### Example from this project

The movie detail route passes four variables to its template:

```python
return render_template('movie_detail.html',
    movie=movie,
    cast=cast,
    reviews=reviews,
    watched=watched
)
```

The template receives `movie`, `cast`, `reviews`, and `watched` as variables and decides how to display them. The route never touches HTML; the template never touches the database.

---

## Default Flask Folders

Flask expects three specific folders by default, each with a distinct purpose.

### `templates/`
Holds all HTML files. When you call `render_template('index.html')`, Flask looks here automatically — no path needs to be specified. Jinja2 processes the files in this folder before they are sent to the browser.

### `static/`
Holds files that are served exactly as-is with no processing. This includes CSS, JavaScript, images, and fonts. In templates these are referenced using `url_for('static', filename='style.css')` rather than a hard-coded path, so Flask generates the correct URL regardless of where the app is deployed.

### `instance/`
Holds configuration or files specific to a particular deployment that should not be committed to version control — for example a local SQLite database file or a config file containing secret keys. Flask creates this automatically in some setups.

### In this project

| Folder | Contents |
|---|---|
| `templates/` | 11 HTML templates including `base.html` and all page templates |
| `static/` | `style.css` — all site styling in one file |
| `instance/` | Local SQLite DB used during development (production uses PostgreSQL on Render) |

All three sit inside `flask_app/` since that is the root directory declared in the Render configuration.

---

## Variable Segments in Routes

`<name>` in a route is a **variable segment** — it captures whatever appears at that position in the URL and passes it as an argument to the route function:

```python
@app.route('/movie/<movie_id>')
def movie_detail(movie_id):
    ...
```

A request to `/movie/550` calls `movie_detail(movie_id='550')`.

### Converters

By default the captured value is a string. A converter can be added to change the type and restrict what Flask will match:

| Syntax | Type | Rejects |
|---|---|---|
| `<name>` | string | anything containing a `/` |
| `<int:name>` | integer | non-numeric values |
| `<float:name>` | float | non-numeric values |
| `<path:name>` | string | nothing — allows `/` in the value |

If the URL doesn't match the converter type, Flask returns a 404 automatically — no extra validation is needed in the route function.

### In this project

Two routes use `<int:movie_id>`:

```python
@app.route('/movie/<int:movie_id>')
@app.route('/toggle-watched/<int:movie_id>', methods=['POST'])
```

The `int:` converter means `/movie/abc` or `/movie/3.5` will never reach the function — Flask rejects them before any code runs. It also means `movie_id` arrives already typed as an integer, ready to use in a database query or API call without any manual conversion.

---

## Colour Palette

### Backgrounds
| Name | Hex | Used for |
|------|-----|---------|
| Page background | `#f0f2f8` | Body background |
| Card / surface | `#ffffff` | All cards, forms, panels |
| Subtle surface | `#f8fafc` | Read-only fields, empty states |
| Suggestion card | `#f8faff` | Suggestion panel cards |

### Navigation & Footer
| Name | Hex | Used for |
|------|-----|---------|
| Nav/footer background | `#1e293b` | Navbar and footer |
| Nav search input | `#334155` | Search box background |
| Nav links | `#cbd5e1` | Default nav link colour |
| Nav brand / username | `#7c9ef0` | CineReview logo, logged-in username |

### Primary Accent (Indigo)
| Name | Hex | Used for |
|------|-----|---------|
| Primary | `#4f6ef7` | Buttons, links, active tabs, stat numbers |
| Primary hover | `#3b5be0` | Hover state for primary buttons |
| Tag background | `#eff3ff` | Genre tag background |
| Rating badge bg | `#eff6ff` | TMDB rating badge background |
| Rating badge text | `#2563eb` | TMDB rating badge text |

### Text
| Name | Hex | Used for |
|------|-----|---------|
| Primary text | `#0f172a` | Headings, titles |
| Body text | `#1e1e2e` | General body copy |
| Secondary text | `#475569` | Descriptions, review comments |
| Muted text | `#94a3b8` | Metadata, labels, placeholders |
| Subtle text | `#64748b` | Subtitles, form hints, footer |

### Status Colours
| Name | Hex | Used for |
|------|-----|---------|
| Success / watched green | `#166534` | Watched badge, success alerts, watched button |
| Success background | `#f0fdf4` | Success alert / watched button background |
| Success border | `#86efac` | Success alert / watched card border |
| Error red | `#991b1b` | Error alert text |
| Error background | `#fff1f2` | Error alert background |
| Error border / field | `#fca5a5` / `#f87171` | Error alert border / invalid input border |
| Star / amber | `#f59e0b` | Star rating icons |

### Special
| Name | Value | Used for |
|------|-------|---------|
| No-poster gradient | `135deg, #667eea → #764ba2` | Purple gradient shown when a film has no poster image |

---

## Typography

| Property | Value |
|----------|-------|
| Font family | `'Segoe UI', system-ui, sans-serif` |
| Page heading (h1) | `1.9rem`, weight `700`, colour `#0f172a` |
| Section heading (h2) | `1.2rem`, colour `#0f172a` |
| Body / paragraph | `0.95–0.97rem`, colour `#475569` |
| Small / meta | `0.82–0.88rem`, colour `#94a3b8` |
| Tiny / tags | `0.72rem`, uppercase, letter-spacing `0.4px` |
| Nav brand | `1.3rem`, weight `700` |

---

## Layout

### Page Shell
- Sticky navbar — `60px` tall, full width, `z-index: 100`
- Main content area — `max-width: 1200px`, centred, padding `2rem 1.5rem`
- Footer — dark, centred text, pinned to the bottom via `flex-column` on `body`

### Grids
| Grid | Rule |
|------|------|
| Movie poster grid | `repeat(auto-fill, minmax(160px, 1fr))`, gap `1.25rem` |
| Cast photo grid | `repeat(auto-fill, minmax(100px, 1fr))`, gap `0.75rem` |
| Movie detail hero | `260px 1fr` (poster + info), gap `2rem` |
| About stats | `repeat(3, 1fr)`, gap `1rem` |

---

## Components

### Navbar
- Dark navy background (`#1e293b`), sticky at the top
- Left: **CineReview** brand link in `#7c9ef0`
- Centre: search bar (dark input + indigo submit button)
- Right: nav links; shows **My Movies** + username + Log out when logged in, otherwise **Log in** + **Register** (Register styled as an indigo pill button)

### Movie Poster Card
- White card, `border-radius: 10px`, subtle shadow
- Poster image fills top (2:3 aspect ratio), scales slightly on hover
- **Watched state**: green border (`#86efac`), poster dimmed to 45% brightness, "Watched" overlay badge on the image
- Card body: title, year, genre tag, TMDB rating badge, action buttons (Details / Review)

### Movie Detail Hero
- Two-column grid: large poster on the left, film info on the right
- Info includes: title, tagline, year/runtime/genres, TMDB star rating (amber star + large number), overview, director, action buttons
- Action buttons: **Mark as Watched** (green-tinted when active), **No Thanks** (red-tinted when active, toggleable), **Write a Review**
- **No Thanks** marks the film as excluded — hidden from the home grid and filtered out of suggestions; clicking again un-excludes it
- White card with `border-radius: 14px`

### Suggestion Panel
- Indigo-tinted border (`#c7d2fe`), white background
- Shows up to 4 horizontal mini-cards (poster thumbnail + title, year, genre, rating)
- Genre filter pills (All + 18 TMDB genres) let the user narrow suggestions by category; selecting a genre resets to page 1
- "More Suggestions" button loads the next page of results from TMDB
- Already-watched and "No Thanks" films are filtered out server-side before results are returned
- Dismissible via an × button; hidden with `display: none`

### Buttons
| Class | Style |
|-------|-------|
| `.btn-primary` | Indigo `#4f6ef7`, white text |
| `.btn-secondary` | Light grey `#f1f5f9`, slate text, grey border |
| `.btn-watched` | Green-tinted `#f0fdf4`, dark green text, green border |
| All buttons | `border-radius: 6px`, slight lift on hover (`translateY(-1px)`) |

### Tabs (Category Filter)
- Pill-shaped (`border-radius: 20px`), white background with grey border
- Active tab: solid indigo fill, white text
- Hover: indigo border and text colour

### Tags & Badges
| Element | Style |
|---------|-------|
| Genre tag | Indigo text on indigo-tinted bg, uppercase, tiny font |
| TMDB rating badge | Blue text on blue-tinted bg, pill shape |
| Watched badge | Dark green text on green-tinted bg, pill shape |
| Star rating | Amber stars (`#f59e0b`), unfilled stars in `#e2e8f0` |

### Forms
- Max-width `560px`
- Labels: `0.9rem`, weight `600`, dark slate
- Inputs/selects/textareas: white background, grey border, `border-radius: 6px`
- Focus state: indigo border + soft indigo glow (`box-shadow: 0 0 0 3px rgba(79,110,247,0.12)`)
- Error state: red border (`#f87171`), red error message below the field
- Password fields include a show/hide toggle button and a live strength meter

### Flash Messages
- Success: green-tinted background, green border and text
- Error: red-tinted background, red border and text
- Displayed at the top of the content area, below the navbar

### Empty / Error States
- Dashed grey border, centred text in muted colour (`#94a3b8`)
- 404 page: oversized `6rem` grey "404" heading, short message, back-to-home button

---

## Borders & Shadows

| Use | Value |
|-----|-------|
| Standard card | `border: 1px solid #e2e8f0` |
| Watched card | `border: 2px solid #86efac` |
| Suggestion panel | `border: 2px solid #c7d2fe` |
| Card shadow | `0 1px 4px rgba(0,0,0,0.06)` |
| Card hover shadow | `0 6px 20px rgba(0,0,0,0.10)` |
| Navbar shadow | `0 2px 8px rgba(0,0,0,0.15)` |
| Detail poster shadow | `0 4px 16px rgba(0,0,0,0.15)` |
| Border radius — small | `4–6px` (tags, inputs, buttons) |
| Border radius — medium | `8–10px` (cards, review cards) |
| Border radius — large | `12–14px` (hero, about cards) |
| Border radius — pill | `20px` (tabs, badges) |

---

## CSS Selectors

### Selector Types Used

This project uses a range of CSS selector types to target elements precisely and keep styles maintainable.

| Selector type | Example from `style.css` | What it targets |
|---|---|---|
| **Element** | `body`, `a`, `*` | Every instance of that HTML tag |
| **Class** | `.navbar`, `.btn`, `.poster-card` | Any element with that class attribute |
| **Pseudo-class** | `a:hover`, `input:focus`, `.tab.active` | An element in a specific state |
| **Pseudo-element** | `*::before`, `input::placeholder`, `li::before` | A generated part of an element |
| **Compound** (two classes) | `.poster-card.is-watched`, `.star.filled`, `.tab.active` | An element that has both classes simultaneously |
| **Descendant** | `.nav-search input`, `.poster-title a`, `.about-card h2` | An element nested inside another |
| **Compound + Descendant** | `.filter-bar .btn.active`, `.form-group.has-error input` | A nested element that also carries a specific class |

---

### Why No ID Selectors Were Used

No `#id` selectors appear anywhere in `style.css`. This is a deliberate choice based on two CSS fundamentals:

**1. IDs must be unique per page.**
An HTML `id` attribute can only appear once on any given page. A CSS rule like `#poster-card` could therefore only ever style a single element. Classes have no such restriction — the same class can be applied to dozens of elements, which is exactly what `.poster-card` does across the movie grid.

**2. IDs have very high specificity.**
CSS specificity determines which rule wins when two rules target the same element. IDs carry a specificity weight of `(1, 0, 0)` — far higher than classes `(0, 1, 0)` or elements `(0, 0, 1)`. A style set via an ID selector is extremely difficult to override later without resorting to `!important` or adding even more specific selectors, which makes the stylesheet fragile and hard to maintain.

By using only class selectors, every style in this project can be:
- **Reused** — apply `.btn-primary` to any button on any page
- **Overridden cleanly** — add a second class (e.g. `.btn-sm`) to adjust without fighting specificity
- **Combined** — compound selectors like `.poster-card.is-watched` layer behaviour without duplicating rules

---

## Passing Python Data Structures to Templates

Flask's `render_template()` function accepts keyword arguments that become variables inside the Jinja2 template. Any Python object can be passed this way — lists, dictionaries, sets, booleans, or plain values — and Jinja2 accesses them by the keyword name used in the call.

```python
return render_template('index.html', movies=movies, categories=CATEGORIES, watched_ids=watched_ids)
#                                     ↑ template var  ↑ Python object
```

---

### Lists

A **list** holds an ordered sequence of items. In templates, lists are most useful when you need to loop through every item and render a repeated block of HTML.

**Example — `movies` list passed to the home page (`index` route, line 221):**

```python
# app.py
movies = tmdb.now_playing()   # returns a list of movie dictionaries from the TMDB API
return render_template('index.html', movies=movies, ...)
```

```html
<!-- index.html -->
{% for movie in movies %}
    <div class="poster-card">
        <h2>{{ movie.title }}</h2>
    </div>
{% endfor %}
```

The template has no knowledge of how many films are in the list — Jinja2 simply repeats the block once per item. Adding or removing movies in Python requires no HTML changes.

**Other lists used:**

| Variable | Route | Contents |
|---|---|---|
| `movies` | `index`, `search` | List of movie dicts from TMDB |
| `cast` | `movie_detail` | List of actor dicts from TMDB |
| `reviews` | `movie_detail` | List of `Review` database objects |
| `watched_movies` | `my_movies` | List of `MovieCache` database objects |

---

### Dictionaries

A **dictionary** maps keys to values. In templates, dictionaries are useful in two ways: looping through all key-value pairs with `.items()`, or accessing a specific value by key name.

**Example 1 — `CATEGORIES` dictionary iterated to build the category tabs (`index` route, line 221):**

```python
# app.py
CATEGORIES = {
    'now_playing': 'Now Playing',
    'popular':     'Popular',
    'top_rated':   'Top Rated',
    'upcoming':    'Upcoming',
}
return render_template('index.html', categories=CATEGORIES, ...)
```

```html
<!-- index.html -->
{% for key, label in categories.items() %}
    <a href="{{ url_for('index', category=key) }}" class="tab">{{ label }}</a>
{% endfor %}
```

Adding a new category only requires a change in `app.py` — the template updates automatically.

---

**Example 2 — `errors` and `form_data` dictionaries for form validation (`add_review` route, line 381):**

```python
# app.py
errors   = {'name': 'Your name is required.', 'comment': 'Comment too short.'}
form_data = {'name': 'Alice', 'rating': '3', 'comment': 'Gr'}
return render_template('add_review.html', errors=errors, form_data=form_data)
```

```html
<!-- add_review.html -->
<input name="name" value="{{ form_data.name }}">
{% if errors.name %}
    <span class="error-msg">{{ errors.name }}</span>
{% endif %}
```

The `errors` dictionary uses field names as keys so the template can display the right message next to the right input. The `form_data` dictionary repopulates each field with what the user typed, so they don't have to retype everything after a validation failure.

---

### Sets

A **set** holds unique values with no duplicates and supports fast membership testing with `in`. It is used here to efficiently check whether the current user has watched a given film.

**Example — `watched_ids` set passed to the home page (`index` route, line 221):**

```python
# app.py
watched_ids = {w.movie_id for w in WatchedMovie.query.filter_by(user_id=current_user.id).all()}
#              ↑ set comprehension — produces a set of integer movie IDs
return render_template('index.html', watched_ids=watched_ids, ...)
```

```html
<!-- index.html -->
<div class="poster-card {% if movie.id in watched_ids %}is-watched{% endif %}">
```

Using a set rather than a list means the `in` check runs in constant time regardless of how many films the user has watched — a list would slow down as the watched list grows.

---

### Individual values

Single values (integers, strings, booleans) are passed the same way and accessed directly in the template by name.

**Example — stats passed to the about page (`about` route, line 610):**

```python
# app.py
return render_template('about.html',
    total_reviews=Review.query.count(),    # integer
    total_users=User.query.count(),        # integer
    total_watched=WatchedMovie.query.count()  # integer
)
```

```html
<!-- about.html -->
<span class="stat-number">{{ total_reviews }}</span>
```

---

## Jinja2 — Loops and Conditionals

### Why Jinja2?

Jinja2 is Flask's built-in templating engine. It lets you embed Python-like logic directly inside HTML files, so pages can display different content depending on what data the server sends. Without it, every page would need to be written as static HTML — you couldn't show a list of movies, display a user's name, or hide a button for logged-out users without writing separate pages for every possible state.

The key principle is **separation of concerns**: Python in `app.py` handles the logic and fetches the data; Jinja2 in the templates handles how that data is displayed. Neither side needs to know the details of the other.

---

### Loops

A Jinja2 loop works like a Python `for` loop — it repeats a block of HTML for every item in a list or dictionary.

**Example 1 — Rendering the category tabs from a Python dictionary:**
```html
{% for key, label in categories.items() %}
    <a href="{{ url_for('index', category=key) }}"
       class="tab {% if category == key %}active{% endif %}">
        {{ label }}
    </a>
{% endfor %}
```
`categories` is a Python dictionary defined in `app.py`. Jinja2 loops through each key/label pair and renders a tab link for each one. Without this loop, each tab would have to be hard-coded in the HTML — adding or renaming a category would mean editing both the Python and the HTML.

---

**Example 2 — Rendering the movie poster grid:**
```html
{% for movie in movies %}
<div class="poster-card">
    <h2>{{ movie.title }}</h2>
    <span class="year">{{ movie.release_date[:4] if movie.release_date else '—' }}</span>
</div>
{% endfor %}
```
`movies` is a list returned from the TMDB API in `app.py`. Jinja2 renders one card for every film in the list. The inline conditional (`if movie.release_date else '—'`) handles the case where a film has no release date, displaying a dash instead of crashing.

---

**Example 3 — Rendering star ratings:**
```html
{% for i in range(1, 6) %}
    <span class="star {% if i <= review.rating %}filled{% endif %}">★</span>
{% endfor %}
```
This loops five times (1 through 5) and adds the `filled` CSS class (which colours the star amber) to any star whose number is less than or equal to the review's rating. A rating of 3 produces three filled stars and two empty ones.

---

### Conditionals

A Jinja2 conditional works like a Python `if` statement — it shows or hides blocks of HTML based on a condition.

**Example 1 — Showing different content to logged-in vs. logged-out users:**
```html
{% if current_user.is_authenticated %}
    <a href="{{ url_for('my_movies') }}">My Movies</a>
    <span>{{ current_user.username }}</span>
    <a href="{{ url_for('logout') }}">Log out</a>
{% else %}
    <a href="{{ url_for('login') }}">Log in</a>
    <a href="{{ url_for('register') }}">Register</a>
{% endif %}
```
The navbar changes entirely depending on whether the user is logged in. Flask-Login provides `current_user` and Jinja2 uses it to decide which links to render.

---

**Example 2 — Handling a missing movie poster:**
```html
{% if movie.poster_path %}
    <img src="{{ poster_url(movie.poster_path) }}" alt="{{ movie.title }}">
{% else %}
    <div class="no-poster">{{ movie.title }}</div>
{% endif %}
```
Not every film in TMDB has a poster image. This conditional checks whether one exists and either shows the image or falls back to a styled placeholder showing the film's title.

---

**Example 3 — Showing an empty state when there are no reviews:**
```html
{% if reviews %}
    {% for review in reviews %}
        <div class="review-card">...</div>
    {% endfor %}
{% else %}
    <div class="empty-state">
        <p>No reviews yet for this film.</p>
    </div>
{% endif %}
```
If no reviews exist for a film, instead of showing a blank space the page displays a helpful message. The `if reviews` check is true when the list has at least one item, and false when it is empty.

---

**Example 4 — Marking watched movies on the home page:**
```html
<div class="poster-card {% if movie.id in watched_ids %}is-watched{% endif %}">
```
`watched_ids` is a set of movie IDs the logged-in user has marked as watched, passed in from `app.py`. If the current movie's ID is in that set, the `is-watched` CSS class is added to the card, which applies the green border and dimmed poster styling.

---

## POST Forms and Server-Side Validation

### How POST forms work

HTML forms can send data in two ways — `GET` (data appended to the URL) or `POST` (data sent in the request body, hidden from the URL). POST is used for any action that changes data on the server: submitting a review, creating an account, or logging in.

```html
<form method="POST" action="{{ url_for('add_review') }}">
```

The `action` attribute tells the browser which URL to send the data to. Using `url_for()` rather than a hard-coded path means the URL is always correct even if routes are renamed.

---

### The route handles both GET and POST

A single Flask route handles both requests by declaring `methods=['GET', 'POST']` and branching on `request.method`:

```python
# app.py — add_review route (line 307)
@app.route('/add-review', methods=['GET', 'POST'])
def add_review():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        # read what the user submitted
        name    = request.form.get('name', '').strip()
        comment = request.form.get('comment', '').strip()

        # validate
        if not name:
            errors['name'] = 'Your name is required.'
        if not comment or len(comment) < 10:
            errors['comment'] = 'Comment must be at least 10 characters.'

        if not errors:
            # save to database and redirect
            db.session.add(Review(name=name, comment=comment, ...))
            db.session.commit()
            return redirect(url_for('movie_detail', movie_id=...))

        # validation failed — fall through to re-render the form
        form_data = {'name': name, 'comment': comment}

    return render_template('add_review.html', errors=errors, form_data=form_data)
```

- **GET request** — `errors` and `form_data` are both empty; the blank form is displayed.
- **POST request, valid** — data is saved and the user is redirected (using `redirect()` prevents the browser re-submitting on refresh).
- **POST request, invalid** — `errors` and `form_data` are passed back to the template so the form re-renders with error messages and the user's input still filled in.

---

### The template displays errors and preserves input

Jinja2 conditionals check each field's error key and add visual feedback; the `value` attribute is repopulated from `form_data` so the user doesn't have to retype everything.

```html
<!-- add_review.html -->
<div class="form-group {% if errors.name %}has-error{% endif %}">
    <label for="name">Your Name</label>
    <input type="text" id="name" name="name"
           value="{{ form_data.get('name', '') }}"
           placeholder="e.g. Jane Smith">
    {% if errors.name %}
        <span class="error-msg">{{ errors.name }}</span>
    {% endif %}
</div>
```

- `{% if errors.name %}has-error{% endif %}` adds the CSS class that turns the input border red.
- `value="{{ form_data.get('name', '') }}"` repopulates the field with what the user typed.
- `{{ errors.name }}` displays the specific message for that field.

---

### Forms using POST across the project

| Template | Route | Purpose |
|---|---|---|
| `add_review.html` | `/add-review` | Submit a star rating and written review |
| `register.html` | `/register` | Create a new user account |
| `login.html` | `/login` | Authenticate an existing user |
| `forgot_password.html` | `/forgot-password` | Request a password reset email |
| `reset_password.html` | `/reset-password/<token>` | Set a new password using a reset token |

---

## Server-Side Validation Logic

Client-side validation (JavaScript running in the browser) is a convenience — it gives the user instant feedback without a page reload. It cannot be trusted, because anyone can disable JavaScript or send a crafted HTTP request directly to the server, bypassing the browser entirely. **Server-side validation is the only kind that can be relied upon.**

This project validates all input in Python before anything is saved to the database.

---

### Type 1 — Rules validation via a helper function

Complex validation logic is extracted into a dedicated helper rather than repeated inside routes. `check_password_strength()` in `app.py` (line 123) checks the password against five rules and returns a list of any that were not met:

```python
# app.py — line 123
def check_password_strength(password):
    issues = []
    if len(password) < 8:
        issues.append('at least 8 characters')
    if not re.search(r'[A-Z]', password):
        issues.append('an uppercase letter')
    if not re.search(r'[a-z]', password):
        issues.append('a lowercase letter')
    if not re.search(r'\d', password):
        issues.append('a number')
    if not re.search(r'[!@#$%^&*]', password):
        issues.append('a special character (!@#$ etc.)')
    return issues   # empty list means the password passed all checks
```

The register route calls it and converts any issues into a single error message:

```python
# app.py — register route (line 472)
strength_issues = check_password_strength(password)
if strength_issues:
    errors['password'] = f'Password must include: {", ".join(strength_issues)}.'
```

The same function is reused identically in the `reset_password` route — the logic lives in one place and both routes stay consistent automatically.

The register page also has a live JavaScript strength meter that runs the same checks in the browser as the user types. But the Python validation always runs on submission regardless — a user who disables JavaScript still gets the same server-side check.

---

### Type 2 — Database validation

Some checks cannot be done client-side at all because the browser has no access to the database. Username and email uniqueness are validated by querying the database directly in the register route:

```python
# app.py — register route (line 459)
if User.query.filter_by(username=username).first():
    errors['username'] = 'That username is already taken.'

if User.query.filter_by(email=email).first():
    errors['email'] = 'An account with that email already exists.'
```

`User.query.filter_by(...).first()` returns a `User` object if a match is found, or `None` if not. The condition is truthy when a record exists, falsy when it does not — so the error is only added when a duplicate is detected.

This type of validation is impossible to replicate reliably in JavaScript. Even if you added an API endpoint to check availability live, the database could change between that check and the actual submission. The server-side check at submission time is the definitive one.

---

### The validation flow

All field errors are collected into the `errors` dictionary before any database write is attempted. The route only proceeds to save data when `errors` is empty:

```python
if errors:
    return render_template('register.html', errors=errors, form_data=form_data)

# only reached if all validation passed
user = User(username=username, email=email)
user.set_password(password)
db.session.add(user)
db.session.commit()
```

This pattern — collect all errors first, write nothing until all pass — prevents partial or invalid data from ever reaching the database.

---

## Code Quality

### Logical file organisation

The project separates responsibilities across files so each file has one clear purpose:

| File | Responsibility |
|---|---|
| `app.py` | Flask routes, database models, validation helpers |
| `tmdb.py` | All TMDB API calls — no route logic lives here |
| `templates/` | HTML presentation only — no business logic |
| `static/style.css` | All styling in one file, grouped by component |

This means changes to the TMDB API only ever touch `tmdb.py`; changes to how a page looks only ever touch a template or `style.css`. Neither file needs to know anything about the other.

---

### Clear route definitions

Routes are named to match their purpose and use typed URL parameters where appropriate:

```python
# app.py
@app.route('/')                                        # home
@app.route('/search')                                  # search results
@app.route('/movie/<int:movie_id>')                    # single film
@app.route('/toggle-watched/<int:movie_id>', methods=['POST'])  # watched toggle
@app.route('/exclude-movie/<int:movie_id>', methods=['POST'])   # no thanks
@app.route('/suggestions')                             # personalised suggestions (JSON)
@app.route('/my-movies')                               # personal watchlist
@app.route('/forgot-password', methods=['GET', 'POST'])
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
```

`<int:movie_id>` tells Flask to accept only integers in that segment of the URL — if anything else is passed Flask returns a 400 error automatically, with no extra validation code needed. Routes that modify data are restricted to `POST` only or declare `GET` and `POST` explicitly. Protected routes use the `@login_required` decorator rather than manual session checks inside each route.

---

### Proper indentation

All Python files use consistent **4-space indentation** throughout, following PEP 8 (the Python style standard). HTML templates use **2-space indentation** for nested elements. Formatting was applied using **Alt + Shift + F** (VS Code's Format Document command), which automatically corrects indentation, spacing, and line length across the entire file in one step — ensuring consistency that is difficult to maintain by hand.

---

### Meaningful variable names

Variable names are chosen to say what they contain, not just their type:

| Name used | What it would be if named poorly | Why the chosen name is clearer |
|---|---|---|
| `watched_ids` | `ids` or `data` | Makes clear it's a set of IDs specifically for watched films |
| `strength_issues` | `result` or `errors` | Distinguishes password rule failures from form-level `errors` |
| `captcha_question` | `q` or `question` | Clear this is the CAPTCHA string, not any other question |
| `movie_reviews` | `reviews` | Distinguishes reviews for this specific film from reviews in general |
| `watched_entries` | `rows` or `data` | Distinguishes the raw database records from the `watched_movies` list built from them |
| `_get` (tmdb.py) | `request` or `fetch` | Leading underscore signals it is an internal helper not intended to be called from outside the module |

---

### Comments explaining non-trivial logic

Every function in `app.py` and `tmdb.py` has a docstring explaining what it does and any non-obvious behaviour:

```python
# app.py — line 91
@app.context_processor
def inject_tmdb():
    """Make tmdb helper functions available in every Jinja template without passing them manually."""

# app.py — line 101
def cache_movie(tmdb_id):
    """Save basic movie info to the local database so it can be shown without calling TMDB again."""

# app.py — line 153
def verify_reset_token(token, max_age=3600):
    """Decode a reset token and return the email, or None if the token is expired or tampered with."""
```

Inline comments are used where the reason for a line of code would not be obvious from reading it:

```python
# tmdb.py — line 5
# Set TMDB_API_KEY as an environment variable in production
```

```html
<!-- register.html -->
{# Honeypot — hidden from humans, bots fill it in and get silently rejected #}
```

JavaScript functions in the templates include a single-line comment summarising what the function does and any non-obvious side effects (such as automatically hiding the suggested password after 3 seconds).

---

### Separation of logic and presentation

Business logic and presentation are kept strictly separate:

- **`tmdb.py`** wraps every TMDB API call behind a named Python function. Routes in `app.py` call `tmdb.now_playing()` or `tmdb.movie_credits()` — they never construct API URLs or parse raw JSON themselves.
- **`app.py`** handles validation, database queries, and deciding what data to send. It never builds HTML.
- **Templates** display the data they receive. They do not query the database, call APIs, or contain validation logic.

The `context_processor` (app.py, line 91) is a practical example of this separation — it makes `poster_url`, `profile_url`, and `genre_names` available in every template automatically, so routes do not need to pass them as arguments in every `render_template()` call:

```python
@app.context_processor
def inject_tmdb():
    return {
        'poster_url':   tmdb.poster_url,
        'profile_url':  tmdb.profile_url,
        'genre_names':  tmdb.genre_names,
    }
```

A template can then call `{{ poster_url(movie.poster_path) }}` directly without the route knowing or caring that the template needs it.

---

## Deployment

The application is deployed live at **[https://cinereview-jik9.onrender.com](https://cinereview-jik9.onrender.com)**.

### Platform — Render Web Service

Render was chosen as the hosting platform because it natively supports Python/Flask applications, offers a free tier suitable for a portfolio project, and connects directly to a GitHub repository so every push to `main` triggers an automatic redeploy.

This project is deployed as a **Web Service** — not a Static Site. A static site serves fixed HTML/CSS/JS files with no server logic. CineReview requires a running Python server (to handle routes, validate forms, and query the database) and a PostgreSQL database (to persist users, reviews, and watched films), so a Web Service is the correct deployment type.

### Render configuration

| Setting | Value | Why |
|---|---|---|
| Root directory | `flask_app` | The `Procfile` and `requirements.txt` live inside this subfolder, not the repo root |
| Build command | `pip install -r requirements.txt` | Installs all Python dependencies on each deploy |
| Start command | `gunicorn app:app` | Starts the app using Gunicorn, a production-grade WSGI server |

Gunicorn replaces Flask's built-in development server in production. Flask's dev server is single-threaded and not designed to handle real traffic — Gunicorn can handle multiple concurrent requests safely.

### Database

A PostgreSQL database is provisioned separately on Render and linked to the web service via the `DATABASE_URL` environment variable. The app handles the switch automatically in `app.py`:

```python
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///cinereview.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
```

- **Locally** — no `DATABASE_URL` is set, so the app falls back to a local SQLite file
- **On Render** — `DATABASE_URL` is set automatically when the PostgreSQL service is linked, switching the app to PostgreSQL with no code changes

The `postgres://` → `postgresql://` replacement is needed because Render provides the older URL prefix but SQLAlchemy requires the newer one.

### Environment variables

Sensitive values are never stored in the code — they are set as environment variables in the Render dashboard:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs session cookies and password reset tokens |
| `TMDB_API_KEY` | Authenticates requests to the TMDB API |
| `DATABASE_URL` | Set automatically by Render when the PostgreSQL database is linked |
| `MAIL_USERNAME` | Gmail address for sending password reset emails (optional) |
| `MAIL_PASSWORD` | Gmail app password (optional) |

---

## Testing the Application

### Local testing

During development, Flask runs a built-in development server on your own machine. Starting the app with:

```bash
cd flask_app
flask run
```

produces output like:

```
* Running on http://127.0.0.1:5000
```

`127.0.0.1` is the loopback address — it refers to your own machine and is not accessible to anyone else. `:5000` is Flask's default port. The same address is also reachable as `http://localhost:5000`. Opening either in a browser loads the running application.

---

### Production testing

The application is deployed on [Render](https://render.com) and accessible at:

**`https://cinereview-jik9.onrender.com`**

This runs through Gunicorn (a production-grade web server) rather than Flask's development server, and connects to a PostgreSQL database rather than the local SQLite file. Testing the live URL verifies that the deployment configuration, environment variables, and database connection all work correctly in production.

---

### Routes tested

Every route was tested in both environments to confirm correct behaviour:

| URL | What was verified |
|---|---|
| `http://localhost:5000/` | Home page loads, category tabs switch between Now Playing / Popular / Top Rated / Upcoming |
| `/search?q=inception` | Search results display correctly; empty search shows no results gracefully |
| `/movie/<id>` | Film detail page shows poster, cast, TMDB rating, and any stored reviews |
| `/add-review?movie_id=<id>` | Form displays for logged-in users; validation errors shown without losing entered data |
| `/my-movies` | Watched list shows for logged-in user; redirects to login if not authenticated |
| `/register` | Registration form validates all fields; duplicate username/email rejected; password strength meter active |
| `/login` | Correct credentials log the user in; incorrect credentials show an error without revealing which field was wrong |
| `/forgot-password` | Submitting a known email sends a reset link; unknown email shows the same success message (to avoid leaking account existence) |
| `/about` | Stats (total reviews, users, watched count) display correctly |
| `/any-invalid-url` | Custom 404 page is shown rather than Flask's default error page |

---

## Assignment Technical Requirements

Checklist of the UCD Professional Academy Flask assignment requirements and how this project meets them.

| Requirement | Status | Notes |
|-------------|--------|-------|
| Flask environment + virtual environment | ✅ | `.venv` set up, `requirements.txt` present |
| `app.py` with defined routes | ✅ | 14 clearly defined routes |
| Project structure | ✅ | Follows required layout (CSS is at `static/style.css`) |
| 5+ HTML templates | ✅ | 11 templates including `base.html` |
| Template inheritance via `base.html` | ✅ | All pages use `{% extends "base.html" %}` |
| Navigation across all pages | ✅ | Persistent navbar present on every page |
| Modern CSS styling | ✅ | Comprehensive, professional styling in `style.css` |
| Python data structures passed to templates | ✅ | Movies list, reviews, categories dict, stats |
| Jinja2 loops and conditionals | ✅ | Used throughout all templates |
| At least one POST form with validation | ✅ | Register, login, add review, password reset |
| Server-side processing and validation logic | ✅ | Full validation in multiple routes |
| Comments explaining non-trivial logic | ✅ | Docstrings on all functions in `app.py` and `tmdb.py`; single-line comments on all JavaScript functions in templates |
| Separation of logic and presentation | ✅ | Logic in `app.py`/`tmdb.py`, presentation in templates |
| Deployed on Render | ✅ | `Procfile` configured for Gunicorn |
