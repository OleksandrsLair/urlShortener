# URL Shortener (Django)

A minimal URL shortener service with TTL and analytics, packaged to run in Docker.

# Features
- POST /api/shorten: create a short URL for a given long URL (optional TTL). Short code is generated automatically.
- GET /r/<short_id>: redirect to the original URL (increments hit counter)
- GET /api/resolve/<short_id>: resolve a short ID to the original URL (JSON)
- GET /stats/<short_id>: return hit count, creation time, expiry, and TTL status

# Data/TTL
- If ttl is provided, the link expires expires_at = now + ttl seconds.
- If TTL is not provided, the link does not expire (infinite TTL).

# Project layout
- Project: url_shortener/
- App: shortener/
- DB: SQLite (db.sqlite3) in the project directory

# Quickstart (Local)
1) Create a virtualenv and install dependencies:
   ```
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt```

2) Apply migrations and run the server:
   ```
   python url_shortener/manage.py migrate
   python url_shortener/manage.py runserver 0.0.0.0:8000```

3) Try it out:
   # Shorten a URL
   `curl -s -X POST http://localhost:8000/api/shorten -d 'target_url=https://example.com' | jq`

   # Shorten with TTL (e.g., 1 hour)
   `curl -s -X POST http://localhost:8000/api/shorten -d 'target_url=https://example.com' -d 'ttl=3600' | jq`

   # Resolve
   `curl -s http://localhost:8000/api/resolve/<short_id> | jq`

   # Redirect
   `curl -i http://localhost:8000/r/<short_id>`

   # Stats
   `curl -s http://localhost:8000/stats/<short_id> | jq`

Request/Response examples
- POST /api/shorten
  Body (form or JSON): { "target_url": "https://example.com", "ttl": 60 }
  201 Created JSON: { "short_id": "abc1234", "short_url": "http://host/r/abc1234", "target_url": "https://example.com", "created_at": "...", "expires_at": "..."|null }

- GET /api/resolve/<short_id>
  200 OK JSON: { "url": "https://example.com", "short_id": "abc1234" }
  404 if not found; 410 if expired

- GET /r/<short_id>
  302 Found redirect to target URL
  404 if not found; 410 if expired

- GET /stats/<short_id>
  200 OK JSON: { "short_id", "target_url", "hit_count", "created_at", "expires_at"|null, "expired": bool, "ttl_seconds_remaining"|null }

# Docker
## Build image:
  `docker build -t urlshortener .`

## Run container (listens on 8000):
  `docker run --rm -p 8000:8000 urlshortener`

Stop: Ctrl+C if run in foreground, or `docker stop <container>` if detached.

## Tests (bonus)
Run the test suite:
  `python url_shortener/manage.py test shortener`

# Notes
- Default settings are for development (DEBUG=True, ALLOWED_HOSTS=['*']).
- For production, use environment-specific settings and a production server (e.g., gunicorn) behind a reverse proxy.



# Postman
- Import the collection at docs/url-shortener.postman_collection.json into Postman.
- Set the collection variable base_url if needed (defaults to http://localhost:8000).
- Run "Shorten URL" first to create a link; the collection stores short_code automatically for the other requests.
