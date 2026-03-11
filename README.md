# Personal Bookmark Manager

> A web-based personal bookmark manager built with Python/Flask and SQLite, containerised with Docker.  
> AI (GitHub Copilot) was used throughout every SDLC phase — from requirement validation and code generation to test authoring and documentation.

---

## Features

| Feature | Description |
|---------|-------------|
| **Add Bookmark** | Save a URL with an optional title; title is auto-fetched from the page if omitted |
| **Tagging** | Assign one or more comma-separated tags to any bookmark |
| **List** | View all bookmarks, newest first |
| **Filter by Tag** | Click any tag chip to show only bookmarks with that tag |
| **Search** | Free-text search across titles and URLs |
| **Delete** | Remove any bookmark with a single click |
| **Persistence** | SQLite database stored in a Docker volume — data survives container restarts |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 · Flask 3 |
| Database | SQLite (via Python `sqlite3`) |
| Frontend | Vanilla HTML / CSS / JavaScript (no build step) |
| Server | Gunicorn |
| Container | Docker / Docker Compose |

---

## Quick Start

### Option 1 — Docker Compose (recommended)

```bash
# Clone the repository
git clone https://github.com/aivipulsharma-a1/AI-SDLC-Bookmark.git
cd AI-SDLC-Bookmark

# Build and start (first run downloads the base image)
docker compose up --build -d

# Open in your browser
open http://localhost:5000
```

Bookmarks are persisted in a named Docker volume (`bookmark_data`).  
They survive `docker compose down` / `docker compose up` cycles.

### Option 2 — Local development (no Docker)

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
python run.py
# → http://localhost:5000
```

---

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `DATABASE_PATH` | `./bookmarks.db` | Absolute path to the SQLite file |
| `SECRET_KEY` | `dev-secret-key` | Flask secret key — change in production |

---

## API Reference

All endpoints are JSON-based.

### `GET /api/bookmarks`
Returns all bookmarks (newest first).

| Query param | Description |
|-------------|-------------|
| `q` | Free-text search (title or URL) |
| `tag` | Filter by exact tag name |

### `POST /api/bookmarks`
Create a new bookmark.

```json
{
  "url":   "https://example.com",
  "title": "Example",          // optional — auto-fetched if omitted
  "tags":  ["python", "web"]   // optional — also accepts "python, web"
}
```

### `DELETE /api/bookmarks/<id>`
Delete a bookmark by its numeric id.

### `GET /api/tags`
Returns all tags with their bookmark counts.

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

All tests use a temporary SQLite database; no clean-up is required.

---

## Project Structure

```
AI-SDLC-Bookmark/
├── app/
│   ├── __init__.py        # App factory + DB init
│   ├── routes.py          # REST API endpoints
│   ├── utils.py           # Title auto-fetch helper
│   └── templates/
│       └── index.html     # Single-page UI (HTML + CSS + JS)
├── tests/
│   └── test_app.py        # Integration & unit tests
├── run.py                 # Gunicorn / dev entrypoint
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## AI in the SDLC

GitHub Copilot was used in every phase of this project:

| SDLC Phase | AI Contribution |
|------------|----------------|
| **Requirements** | Validated user stories from the PRD; identified missing acceptance criteria |
| **Design** | Suggested the Flask + SQLite + Docker architecture; proposed the REST API shape |
| **Code Generation** | Generated boilerplate for routes, DB helpers, and the single-page UI |
| **Code Review** | Reviewed each module for correctness, SQL injection safety, and style |
| **Testing** | Generated comprehensive test cases covering all PRD features; suggested edge cases (duplicate tags, missing URL, persistence) |
| **Documentation** | Produced this README including API reference and the AI impact summary |

---

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes and add/update tests as needed.
3. Run `pytest tests/ -v` and ensure all tests pass.
4. Open a pull request with a clear description.

---

## License

MIT

