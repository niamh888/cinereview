# CineReview — Accessibility Audit

This document records the accessibility assessment of CineReview, the issues
identified, the fixes applied, and what still requires manual verification.
The audit is conducted against **WCAG 2.1 Level AA** — the international
standard for web accessibility required by most public-sector and many
commercial applications.

WCAG 2.1 is organised around four principles, known as **POUR**:

| Principle | Meaning |
|---|---|
| **Perceivable** | Information and UI components must be presentable to all users |
| **Operable** | UI components and navigation must be operable by all users |
| **Understandable** | Information and UI operation must be understandable |
| **Robust** | Content must be robust enough to be interpreted by assistive technologies |

---

## Audit Findings

### What was already in place

| Feature | Detail | WCAG criterion |
|---|---|---|
| Language declaration | `<html lang="en">` present on every page | 3.1.1 |
| Viewport meta tag | `<meta name="viewport">` present | — |
| Semantic landmarks | `<nav>`, `<main>`, `<footer>`, `<section>` used throughout | 1.3.1 |
| Heading hierarchy | `<h1>` per page, `<h2>` for sections — no levels skipped | 1.3.1 |
| Descriptive page titles | Each page has a unique `<title>` (e.g. `Fight Club — CineReview`) | 2.4.2 |
| Image alt text | Movie posters use `alt="{{ movie.title }}"`, actor photos use `alt="{{ actor.name }}"` | 1.1.1 |
| Form input focus ring | Indigo glow on focused form fields | 1.4.11, 2.4.7 |
| Form labels | All form fields have associated `<label>` elements | 1.3.1 |
| Colour contrast (body text) | `#0f172a` / `#475569` on white backgrounds meets AA ratio | 1.4.3 |

---

### Issues found and fixed

| Issue | WCAG criterion | Fix applied |
|---|---|---|
| No skip navigation link — keyboard users tabbed through the entire navbar on every page | 2.4.1 | `<a href="#main-content" class="skip-nav">` added before the navbar; visible on keyboard focus |
| Search button was icon-only (🔍) with no accessible name | 4.1.2 | `aria-label="Search"` added to the button |
| Search input had only a placeholder, no programmatic label | 1.3.1 | `aria-label="Search movies"` added to the input |
| Search form had no landmark role | 2.4.1 | `role="search"` added to the `<form>` |
| Flash messages had no `role="alert"` — screen readers would not announce them | 4.1.3 | `role="alert"` added to each flash `<div>`; container has `aria-live="polite"` |
| Navbar had no `aria-label` to identify it | 4.1.2 | `aria-label="Site navigation"` added to `<nav>` |
| Dismiss suggestions button was icon-only (×) with no accessible name | 4.1.2 | `aria-label="Close suggestions"` added |
| Suggestions list had no `aria-live` — screen readers did not announce when content loaded | 4.1.3 | `aria-live="polite"` added to `#suggestions-list` |
| Watched and No Thanks buttons had no `aria-pressed` — toggle state was invisible to screen readers | 4.1.2 | `aria-pressed="true/false"` added in HTML; JS updated to maintain it on toggle |
| Filter pill buttons (genre, decade, age, language) had no `aria-pressed` | 4.1.2 | `aria-pressed` added and maintained in `toggleFilterBtn()` helper |
| Buttons had no focus ring — keyboard users could not see which button was focused | 2.4.7 | `.btn:focus-visible { outline: 3px solid #4f6ef7 }` added to `style.css` |
| Star rating display rendered five ★ characters — a screen reader would say "star star star star star" with no context | 1.3.1 | `<span class="sr-only">Rating: X out of 5 stars</span>` added; visual stars wrapped in `aria-hidden="true"` |
| External TMDB link opened in a new tab with no warning | 3.2.2 | `rel="noopener noreferrer"` added; `<span class="sr-only">(opens in new tab)</span>` added inside the link |

---

### Items requiring manual verification

The following cannot be verified by automated tests and must be checked manually.

| Check | How to test | Pass criterion |
|---|---|---|
| Skip link is visible on keyboard focus | Tab once from address bar on any page | A blue "Skip to main content" link appears at the top-left; pressing Enter jumps past the navbar |
| Keyboard navigation through the entire site | Tab through all interactive elements | Every link, button, and form field receives a visible focus ring; no elements are unreachable |
| Screen reader announces page changes | Use NVDA (Windows) or VoiceOver (Mac) | Page title is announced on navigation; flash messages are read aloud; suggestions list announces new content |
| Screen reader announces toggle state | Tab to Watched or No Thanks button, press Space | Screen reader announces "Mark as Watched, toggle button, not pressed" / "Watched, toggle button, pressed" |
| Colour contrast — muted/secondary text | Run page through WebAIM Contrast Checker | `#94a3b8` (muted text) on `#ffffff` background — **check this ratio specifically** |
| Mobile accessibility — touch targets | Test on a phone at 375px | All buttons and links are at least 44×44px tappable area |
| Form error messages are announced | Submit a form with invalid data using a screen reader | Error messages are read aloud when the page re-renders |

---

## Tools for further testing

| Tool | Purpose | URL |
|---|---|---|
| **axe DevTools** | Browser extension — automated WCAG scan | [deque.com/axe](https://www.deque.com/axe/) |
| **WAVE** | Visual overlay of accessibility issues | [wave.webaim.org](https://wave.webaim.org/) |
| **WebAIM Contrast Checker** | Check colour contrast ratios | [webaim.org/resources/contrastchecker](https://webaim.org/resources/contrastchecker/) |
| **NVDA** | Free screen reader for Windows | [nvaccess.org](https://www.nvaccess.org/) |
| **VoiceOver** | Built-in screen reader on Mac/iPhone | System Preferences → Accessibility |
| **Lighthouse** | Built into Chrome DevTools — includes accessibility score | DevTools → Lighthouse tab |

---

## Standard referenced

**WCAG 2.1 Level AA** — Web Content Accessibility Guidelines, W3C Recommendation,
5 June 2018. [https://www.w3.org/TR/WCAG21/](https://www.w3.org/TR/WCAG21/)
