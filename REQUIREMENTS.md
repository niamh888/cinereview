# CineReview — Requirements & Test Traceability

A living document mapping user needs to software requirements and test cases,
following the structure of a Software Development Life Cycle (SDLC) requirements
traceability matrix.

---

## 1. User Requirements (UR)

User requirements describe what the system must do from the end-user's perspective.
They are written in plain language, free of implementation detail.

| ID | Requirement |
|----|-------------|
| UR-001 | Users shall be able to browse movies organised by category (Now Playing, Popular, Top Rated, Upcoming) |
| UR-002 | Users shall be able to search for movies by title |
| UR-003 | Users shall be able to view detailed information about a specific movie |
| UR-004 | Users shall be able to create a personal account |
| UR-005 | Users shall be able to log in to and log out of their account |
| UR-006 | Users shall be able to reset a forgotten password via email |
| UR-007 | Users shall be able to mark movies as watched and view their watched list |
| UR-008 | Users shall be able to mark movies as "No Thanks" to permanently exclude them from the grid and suggestions |
| UR-009 | Users shall be able to write and read star-rated reviews for any movie |
| UR-010 | The system shall provide personalised movie suggestions filterable by genre, decade, age rating, and language, with multi-select support |
| UR-011 | The application shall be usable on mobile devices without loss of core functionality |
| UR-012 | The system shall protect user data and restrict access to authenticated-only features |
| UR-013 | The application shall be accessible to users of assistive technologies, conforming to WCAG 2.1 Level AA |

---

## 2. Software Requirements (SR)

Software requirements are derived from user requirements and describe specific,
measurable system behaviours.

### UR-001 — Movie Browsing

| ID | Requirement |
|----|-------------|
| SR-001.1 | GET `/` shall return HTTP 200 with a rendered movie grid |
| SR-001.2 | The `category` query parameter shall accept `now_playing`, `popular`, `top_rated`, and `upcoming` and return the corresponding film set |
| SR-001.3 | Movies marked as excluded by the authenticated user shall not appear in the grid |

### UR-002 — Movie Search

| ID | Requirement |
|----|-------------|
| SR-002.1 | GET `/search?q=<query>` shall return HTTP 200 |
| SR-002.2 | A search with an empty query string shall return HTTP 200 with zero results and no error |

### UR-003 — Movie Detail

| ID | Requirement |
|----|-------------|
| SR-003.1 | GET `/movie/<valid_integer_id>` shall return HTTP 200 |
| SR-003.2 | GET `/movie/<id>` where the TMDB lookup fails shall return HTTP 404 |
| SR-003.3 | GET `/movie/<non_integer>` shall return HTTP 404 (Flask converter rejects non-integers) |

### UR-004 — Account Creation

| ID | Requirement |
|----|-------------|
| SR-004.1 | GET `/register` shall return HTTP 200 |
| SR-004.2 | POST `/register` with valid data shall create a user record, log the user in, and redirect to the home page |
| SR-004.3 | POST `/register` with a username already in the database shall return HTTP 200 with a field error |
| SR-004.4 | POST `/register` with an email already in the database shall return HTTP 200 with a field error |
| SR-004.5 | POST `/register` with a password that fails strength checks shall return HTTP 200 with a field error |
| SR-004.6 | POST `/register` with mismatched password and confirm-password shall return HTTP 200 with a field error |
| SR-004.7 | POST `/register` with an incorrect CAPTCHA answer shall return HTTP 200 with a field error |
| SR-004.8 | POST `/register` with the honeypot field filled in shall redirect without creating a user |

### UR-005 — Authentication

| ID | Requirement |
|----|-------------|
| SR-005.1 | GET `/login` shall return HTTP 200 |
| SR-005.2 | POST `/login` with valid credentials shall authenticate the user and redirect to the home page |
| SR-005.3 | POST `/login` with incorrect credentials shall return HTTP 200 with an error message |
| SR-005.4 | GET `/logout` shall log the user out and redirect to the home page |

### UR-006 — Password Reset

| ID | Requirement |
|----|-------------|
| SR-006.1 | GET `/forgot-password` shall return HTTP 200 |
| SR-006.2 | POST `/forgot-password` with a registered email shall trigger a reset email and redirect |
| SR-006.3 | POST `/forgot-password` with an unknown email shall show the same success message (to avoid account enumeration) |

### UR-007 — Watch Tracking

| ID | Requirement |
|----|-------------|
| SR-007.1 | POST `/toggle-watched/<id>` for an authenticated user shall return JSON `{"watched": true}` on first call |
| SR-007.2 | POST `/toggle-watched/<id>` for an authenticated user shall return JSON `{"watched": false}` when the movie is already watched |
| SR-007.3 | POST `/toggle-watched/<id>` for an unauthenticated user shall return a redirect to `/login` |
| SR-007.4 | GET `/my-movies` for an authenticated user shall return HTTP 200 |
| SR-007.5 | GET `/my-movies` for an unauthenticated user shall redirect to `/login` |

### UR-008 — Movie Exclusion

| ID | Requirement |
|----|-------------|
| SR-008.1 | POST `/exclude-movie/<id>` for an authenticated user shall return JSON `{"excluded": true}` on first call |
| SR-008.2 | POST `/exclude-movie/<id>` shall return JSON `{"excluded": false}` when the movie is already excluded (toggle) |
| SR-008.3 | POST `/exclude-movie/<id>` for an unauthenticated user shall redirect to `/login` |
| SR-008.4 | Excluded movies shall not appear in GET `/suggestions` results |

### UR-009 — Reviews

| ID | Requirement |
|----|-------------|
| SR-009.1 | GET `/add-review` shall return HTTP 200 |
| SR-009.2 | POST `/add-review` with valid data shall save a `Review` record and redirect to the movie detail page |
| SR-009.3 | POST `/add-review` with a missing reviewer name shall return HTTP 200 with a field error |
| SR-009.4 | POST `/add-review` with a comment shorter than 10 characters shall return HTTP 200 with a field error |
| SR-009.5 | POST `/add-review` with a rating outside 1–5 shall return HTTP 200 with a field error |

### UR-010 — Suggestions

| ID | Requirement |
|----|-------------|
| SR-010.1 | GET `/suggestions` shall return HTTP 200 with JSON containing `suggestions` (list) and `reason` (string) keys |
| SR-010.2 | Watched movies shall be excluded from `/suggestions` results for authenticated users |
| SR-010.3 | Excluded movies shall be excluded from `/suggestions` results for authenticated users |
| SR-010.4 | The `genre_ids` parameter shall accept comma-separated TMDB genre IDs and pass them to the discover endpoint using OR syntax |
| SR-010.5 | The `decades` parameter shall accept comma-separated decade keys and use the bounding date range across all selected decades |
| SR-010.6 | The `age_ratings` parameter shall apply US certification filtering; multiple selections use the most permissive rating |
| SR-010.7 | The `languages` parameter shall accept comma-separated ISO 639-1 codes and filter by original language |
| SR-010.8 | All four filter parameters may be combined in a single request |

### UR-011 — Mobile

| ID | Requirement |
|----|-------------|
| SR-011.1 | The `<meta name="viewport">` tag shall be present in `base.html` |
| SR-011.2 | `style.css` shall contain `@media` breakpoints at max-width 768px, 640px, and 480px |
| SR-011.3 | At ≤768px the movie detail hero shall stack to a single column |
| SR-011.4 | At ≤640px the navbar shall wrap the search bar to a second row |
| SR-011.5 | At ≤480px the poster grid shall render as two columns |

### UR-012 — Security

| ID | Requirement |
|----|-------------|
| SR-012.1 | Routes `/my-movies`, `/toggle-watched/<id>`, `/exclude-movie/<id>` shall redirect unauthenticated users to `/login` |
| SR-012.2 | Passwords shall be stored as hashed values; the plain-text password shall never be persisted |
| SR-012.3 | `FLASK_DEBUG` shall not be set in the production environment |

### UR-013 — Accessibility

| ID | Requirement |
|----|-------------|
| SR-013.1 | Every page shall include a skip navigation link as the first focusable element, allowing keyboard users to bypass the navbar |
| SR-013.2 | All icon-only interactive elements shall have an accessible name via `aria-label` |
| SR-013.3 | The search form shall carry `role="search"` and the input shall have a programmatic label |
| SR-013.4 | Flash messages shall use `role="alert"` so screen readers announce them immediately |
| SR-013.5 | Toggle buttons (Watched, No Thanks, filter pills) shall maintain `aria-pressed` to communicate their state to screen readers |
| SR-013.6 | Dynamic content regions (flash container, suggestions list) shall use `aria-live` so screen readers announce updates |
| SR-013.7 | All buttons shall display a visible focus ring when focused via keyboard |
| SR-013.8 | Star ratings displayed in reviews shall provide a text alternative readable by screen readers |
| SR-013.9 | Links that open in a new tab shall include `rel="noopener noreferrer"` and a screen-reader-visible warning |
| SR-013.10 | The page shall declare its language via `<html lang="en">` |
| SR-013.11 | Semantic landmark elements (`<nav>`, `<main>`, `<footer>`, `<section>`) shall be used throughout |

---

## 3. Test Cases (TC)

Each test case maps to one or more software requirements.
**[A]** = Automated (pytest) · **[M]** = Manual

### Public Routes

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-001 | Home page returns 200 | SR-001.1 | [A] | Response status == 200 |
| TC-002 | Home page contains movie title | SR-001.1 | [A] | Response body contains mock movie title |
| TC-003 | Category filter `popular` returns 200 | SR-001.2 | [A] | GET `/?category=popular` status == 200 |
| TC-004 | Search with query returns 200 | SR-002.1 | [A] | GET `/search?q=fight` status == 200 |
| TC-005 | Search with empty query returns 200 | SR-002.2 | [A] | GET `/search` status == 200 |
| TC-006 | Movie detail with valid ID returns 200 | SR-003.1 | [A] | GET `/movie/550` status == 200 |
| TC-007 | Movie detail with non-integer ID returns 404 | SR-003.3 | [A] | GET `/movie/abc` status == 404 |
| TC-008 | About page returns 200 | SR-001.1 | [A] | Response status == 200 |
| TC-009 | Unknown URL returns 404 | — | [A] | GET `/does-not-exist` status == 404 |

### Registration

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-010 | Register page returns 200 | SR-004.1 | [A] | Response status == 200 |
| TC-011 | Valid registration creates user and redirects | SR-004.2 | [A] | Status 200 after redirect; user exists in DB |
| TC-012 | Duplicate username returns error | SR-004.3 | [A] | Response contains username error message |
| TC-013 | Duplicate email returns error | SR-004.4 | [A] | Response contains email error message |
| TC-014 | Weak password returns error | SR-004.5 | [A] | Response contains password error message |
| TC-015 | Mismatched passwords returns error | SR-004.6 | [A] | Response contains confirm-password error |
| TC-016 | Wrong CAPTCHA returns error | SR-004.7 | [A] | Response contains CAPTCHA error message |
| TC-017 | Honeypot filled redirects without creating user | SR-004.8 | [A] | No new user in DB; response is a redirect |

### Authentication

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-018 | Login page returns 200 | SR-005.1 | [A] | Response status == 200 |
| TC-019 | Login with valid credentials redirects | SR-005.2 | [A] | Status 200 after redirect; welcome flash present |
| TC-020 | Login with wrong password returns error | SR-005.3 | [A] | Response contains error message |
| TC-021 | Login with unknown username returns error | SR-005.3 | [A] | Response contains error message |
| TC-022 | Logout redirects to home | SR-005.4 | [A] | Status 200 after redirect |

### Access Control

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-023 | `/my-movies` unauthenticated redirects to login | SR-007.5, SR-012.1 | [A] | Redirect to `/login` |
| TC-024 | `/toggle-watched/<id>` unauthenticated redirects | SR-007.3, SR-012.1 | [A] | Redirect to `/login` |
| TC-025 | `/exclude-movie/<id>` unauthenticated redirects | SR-008.3, SR-012.1 | [A] | Redirect to `/login` |

### Watch Tracking

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-026 | Toggle watched returns `{"watched": true}` | SR-007.1 | [A] | JSON `watched == True` |
| TC-027 | Second toggle returns `{"watched": false}` | SR-007.2 | [A] | JSON `watched == False` |
| TC-028 | `/my-movies` returns 200 when authenticated | SR-007.4 | [A] | Response status == 200 |

### Movie Exclusion

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-029 | Exclude movie returns `{"excluded": true}` | SR-008.1 | [A] | JSON `excluded == True` |
| TC-030 | Second exclude returns `{"excluded": false}` | SR-008.2 | [A] | JSON `excluded == False` |

### Reviews

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-031 | Add review page returns 200 | SR-009.1 | [A] | Response status == 200 |
| TC-032 | Valid review submission saves to DB and redirects | SR-009.2 | [A] | Review record exists in DB; redirect to movie |
| TC-033 | Missing name returns field error | SR-009.3 | [A] | Response contains name error message |
| TC-034 | Comment < 10 characters returns field error | SR-009.4 | [A] | Response contains comment error message |
| TC-035 | Rating outside 1–5 returns field error | SR-009.5 | [A] | Response contains rating error message |

### Suggestions

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-036 | Suggestions returns JSON with required keys | SR-010.1 | [A] | Response has `suggestions` list and `reason` string |
| TC-037 | Suggestions excludes watched movies | SR-010.2 | [A] | Movie ID in watched list absent from results |
| TC-038 | Suggestions excludes excluded movies | SR-010.3 | [A] | Movie ID in excluded list absent from results |
| TC-039 | genre_ids filter returns valid response | SR-010.4 | [A] | Response status 200 with valid JSON |
| TC-040 | decades filter returns valid response | SR-010.5 | [A] | Response status 200 with valid JSON |
| TC-041 | age_ratings filter returns valid response | SR-010.6 | [A] | Response status 200 with valid JSON |
| TC-042 | languages filter returns valid response | SR-010.7 | [A] | Response status 200 with valid JSON |

### Mobile & Responsive (Manual)

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-043 | Viewport meta tag present in page source | SR-011.1 | [A] | `<meta name="viewport">` in response HTML |
| TC-044 | Home page renders correctly on 375px screen | SR-011.3–5 | [M] | Poster grid shows 2 columns; no horizontal overflow |
| TC-045 | Home page renders correctly on 768px screen | SR-011.3 | [M] | Movie hero stacks; navbar still usable |
| TC-046 | Navbar search bar moves to second row on phone | SR-011.4 | [M] | Search bar visible below brand and links |
| TC-047 | Movie detail hero stacks on tablet | SR-011.3 | [M] | Poster appears above info text |

### Security (Manual)

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-048 | Password stored as hash in database | SR-012.2 | [M] | Inspect `user.password_hash`; not equal to plain text |
| TC-049 | Password reset email arrives with valid link | SR-006.2 | [M] | Email received; link opens reset form; token expires after 1 hour |
| TC-050 | Debug mode off in production | SR-012.3 | [M] | Render dashboard: `FLASK_DEBUG` not set; 500 shows generic error page |

### Browser & JavaScript (Manual)

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-051 | Suggestion panel opens and shows cards | SR-010.1 | [M] | Cards appear with poster, title, genre, rating |
| TC-052 | Multiple genre filters can be selected together | SR-010.8 | [M] | Two genre pills active simultaneously; results update |
| TC-053 | Clicking active filter deselects it | SR-010.8 | [M] | Pill returns to inactive state; results refresh |
| TC-054 | Watched toggle updates button without page reload | SR-007.1 | [M] | Button changes to green "Watched" instantly |
| TC-055 | No Thanks on movie detail excludes from future suggestions | SR-008.1, SR-008.4 | [M] | Return to home; open suggestions; movie absent |
| TC-056 | Cross-browser: Chrome, Firefox, Safari | All | [M] | Core flows work without visual breakage |

### Accessibility

| TC | Description | SR | Type | Pass Criterion |
|----|-------------|----|------|----------------|
| TC-057 | Skip navigation link present in page source | SR-013.1 | [A] | Response HTML contains `class="skip-nav"` and `href="#main-content"` |
| TC-058 | Search button has accessible name | SR-013.2 | [A] | `aria-label="Search"` present on search button |
| TC-059 | Search form has `role="search"` | SR-013.3 | [A] | `role="search"` present on nav search form |
| TC-060 | Flash messages have `role="alert"` | SR-013.4 | [A] | Flash div contains `role="alert"` |
| TC-061 | `<html>` tag declares language | SR-013.10 | [A] | `lang="en"` present on `<html>` element |
| TC-062 | `<main>` landmark present | SR-013.11 | [A] | `<main>` element present in page source |
| TC-063 | Skip link is visible and functional on keyboard focus | SR-013.1 | [M] | Tab once on any page; blue skip link appears; Enter jumps to main content |
| TC-064 | All buttons have visible focus ring | SR-013.7 | [M] | Tab through page; every button shows indigo outline when focused |
| TC-065 | Toggle button state announced by screen reader | SR-013.5 | [M] | NVDA/VoiceOver announces "not pressed" / "pressed" on Watched and No Thanks buttons |
| TC-066 | Suggestions list announced when content loads | SR-013.6 | [M] | Screen reader reads new suggestion titles after panel opens |
| TC-067 | Star rating read correctly by screen reader | SR-013.8 | [M] | Screen reader announces "Rating: 4 out of 5 stars" not individual star characters |
| TC-068 | External link warns of new tab | SR-013.9 | [M] | Screen reader announces "(opens in new tab)" on TMDB footer link |
| TC-069 | Colour contrast passes AA ratio | SR-013.11 | [M] | Run WAVE or axe on any page; no contrast errors reported |
| TC-070 | Full keyboard navigation — no trapped focus | SR-013.1 | [M] | Navigate entire site using only Tab, Shift+Tab, Enter, Space; every feature reachable |

---

## 4. Traceability Matrix

| UR | SR | TC |
|----|----|----|
| UR-001 | SR-001.1, SR-001.2, SR-001.3 | TC-001, TC-002, TC-003 |
| UR-002 | SR-002.1, SR-002.2 | TC-004, TC-005 |
| UR-003 | SR-003.1, SR-003.2, SR-003.3 | TC-006, TC-007 |
| UR-004 | SR-004.1 – SR-004.8 | TC-010 – TC-017 |
| UR-005 | SR-005.1 – SR-005.4 | TC-018 – TC-022 |
| UR-006 | SR-006.1 – SR-006.3 | TC-049 |
| UR-007 | SR-007.1 – SR-007.5 | TC-023, TC-024, TC-026 – TC-028 |
| UR-008 | SR-008.1 – SR-008.4 | TC-025, TC-029, TC-030, TC-055 |
| UR-009 | SR-009.1 – SR-009.5 | TC-031 – TC-035 |
| UR-010 | SR-010.1 – SR-010.8 | TC-036 – TC-042, TC-051 – TC-053 |
| UR-011 | SR-011.1 – SR-011.5 | TC-043 – TC-047 |
| UR-012 | SR-012.1 – SR-012.3 | TC-023 – TC-025, TC-048, TC-050 |
| UR-013 | SR-013.1 – SR-013.11 | TC-057 – TC-070 |

---

## 5. Manual Testing Guide

The following test cases cannot be executed by the automated test suite and must
be performed manually. Instructions assume the application is running locally at
`http://localhost:5000` or live at the Render URL.

---

### TC-044 / TC-045 — Responsive Layout (Mobile & Tablet)

**Tools required:** Chrome DevTools (or equivalent)

1. Open the home page in Chrome.
2. Open DevTools → Toggle device toolbar (Ctrl+Shift+M).
3. Set width to **375px** (iPhone SE):
   - Verify the poster grid shows **2 columns**.
   - Verify no content overflows horizontally (no horizontal scroll bar).
   - Verify the navbar brand and links are visible; search bar sits below them.
4. Set width to **768px** (iPad):
   - Verify the movie grid still fills the width.
   - Navigate to a movie detail page; verify the poster appears **above** the film info (single column).

---

### TC-046 — Navbar on Phone

1. With DevTools at 375px width, open the home page.
2. Verify the search bar appears on its own row below the brand and nav links.
3. Verify the "Write a Review" link is hidden (expected at this width).
4. Verify the remaining links (Movies, My Movies, About, Log out) are visible and tappable.

---

### TC-047 — Movie Detail Hero Stacks at Tablet Width

1. With DevTools at 768px, navigate to any movie detail page.
2. Verify the poster image is centred and appears above (not beside) the title and info.

---

### TC-048 — Password Stored as Hash

1. Log in as any user.
2. Open a SQLite browser (e.g. DB Browser for SQLite) and open `flask_app/cinereview.db`.
3. Open the `user` table and inspect the `password_hash` column.
4. **Pass:** the value begins with `scrypt:` or `pbkdf2:` and does not contain the plain-text password.

---

### TC-049 — Password Reset Email

**Requires:** `MAIL_USERNAME` and `MAIL_PASSWORD` set in `.env`.

1. Navigate to `/forgot-password`.
2. Enter the email address of a registered account.
3. Click **Send Reset Link**.
4. **Pass:** email arrives within 2 minutes containing a link of the form `/reset-password/<token>`.
5. Click the link and verify the reset form loads.
6. Submit a new valid password and confirm login works.
7. **Expiry check:** wait 61 minutes (or use `max_age=60` in `verify_reset_token` temporarily), revisit the link — verify it shows an "expired or invalid" message.

---

### TC-050 — Debug Mode Off in Production

1. Log in to the Render dashboard.
2. Navigate to the CineReview web service → **Environment**.
3. **Pass:** `FLASK_DEBUG` is not present in the environment variable list.
4. Trigger a deliberate error in the live app (e.g. visit `/movie/0`).
5. **Pass:** the browser shows the custom 404/500 page, not Flask's interactive debugger.

---

### TC-051 — Suggestion Panel Opens Correctly

1. Log in and go to the home page.
2. Click **★ Suggest a Movie for Me**.
3. **Pass:** the suggestions panel appears with 4 film cards, each showing a poster (or placeholder), title, genre tag, year, and star rating.
4. Verify the four filter rows (genre, decade, age, language) are visible.

---

### TC-052 — Multi-Select Filters

1. Open the suggestion panel.
2. Click **1990s** in the decade row — verify it highlights.
3. Click **2010s** — verify **both** 1990s and 2010s are highlighted simultaneously.
4. **Pass:** the suggestions refresh and the reason text reflects both decades.
5. Click **Horror** in the genre row — verify it highlights alongside the two active decade filters.
6. **Pass:** reason text reads something like *"Popular Horror films from the 1990s & 2010s"*.

---

### TC-053 — Deselecting a Filter

1. With 1990s and 2010s selected (from TC-052), click **1990s** again.
2. **Pass:** 1990s deselects; only 2010s remains active; suggestions refresh.
3. Click **All Eras** — **Pass:** all decade selections clear; "All Eras" becomes active.

---

### TC-054 — Watched Toggle (No Page Reload)

1. Navigate to any movie detail page as a logged-in user.
2. Click **Mark as Watched**.
3. **Pass:** the button changes instantly to green **✓ Watched** without the page reloading.
4. Click the button again — **Pass:** it reverts to **Mark as Watched**.

---

### TC-055 — No Thanks Excludes from Suggestions

1. As a logged-in user, navigate to the detail page for a specific film (note its title).
2. Click **No Thanks** — verify the button turns red and shows **✕ Not for Me**.
3. Return to the home page and click **★ Suggest a Movie for Me**.
4. Page through several suggestions using **↻ More Suggestions**.
5. **Pass:** the excluded film does not appear in any suggestion page.

---

### TC-056 — Cross-Browser Compatibility

Test the following flows in Chrome, Firefox, and Safari:

| Flow | Expected result |
|------|----------------|
| Home page loads with movie grid | Grid renders; posters visible |
| Search for a film | Results appear |
| Register a new account | Form validates; account created |
| Mark a film as watched | Button updates instantly |
| Open suggestion panel and apply filters | Panel updates without errors |
| View the site at 375px (DevTools) | Two-column grid; no overflow |
