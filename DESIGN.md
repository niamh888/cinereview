# CineReview — Design Plan

A reference document describing the visual design, colour palette, layout, and component styles used across the site.

---

## Design Principles

- **Clean and content-first** — movie posters and titles take centre stage; chrome is minimal
- **Light theme with dark navigation** — pale blue-grey page background, dark navy navbar and footer for contrast
- **Consistent card-based layout** — content is grouped into white rounded cards with subtle shadows
- **Indigo as the primary accent** — used for buttons, links, active states, and key stats

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
- Card body: title, year, genre tag, TMDB rating badge, action buttons (Review / Watched toggle)

### Movie Detail Hero
- Two-column grid: large poster on the left, film info on the right
- Info includes: title, tagline, year/runtime/genres, TMDB star rating (amber star + large number), overview, director, action buttons
- White card with `border-radius: 14px`

### Suggestion Panel
- Indigo-tinted border (`#c7d2fe`), white background
- Shows up to 4 horizontal mini-cards (poster thumbnail + title, year, genre, rating)
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
