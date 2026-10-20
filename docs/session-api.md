# Session access for the application

Use the existing Django users and session cookies. These endpoints do not create
users, change roles, or grant new permissions. The admin remains available.

## Browser flow

1. `GET /api/auth/session/` returns `{user, csrf_token}` and sets a CSRF cookie.
   `user` is null when signed out; otherwise it contains `id`, `username`, `name`,
   and `role`. Responses are not cacheable.
2. `POST /api/auth/login/` with JSON `{username, password}` and the
   `X-CSRFToken` header. Keep same-origin cookies enabled. A successful response
   contains the user and a fresh CSRF token: replace the previous token after login.
3. Send that token on every unsafe API request, including
   `POST /api/auth/logout/`. Logout returns the anonymous session representation.

Missing/invalid CSRF or a foreign origin returns 403. Invalid credentials (including
inactive users) return 401 with the same generic message. Malformed login payloads
return 400. GET cannot log in or out. No CSRF exemptions are introduced.

## Development integration

The frontend must use its same-origin `/api` proxy. Host and Origin must remain
consistent through the proxy; do not disable CSRF to make local login work.
The browser integration and proxy configuration are part of the frontend delivery.
Before exposing the application publicly, configure deployment-level login rate
limiting and HTTPS; this increment does not introduce a rate-limiting service.

## Verification

From `backend`, run `..\.venv\Scripts\python.exe -m pytest tests/test_session.py -q`.
Tests use Django's real session client with CSRF checks enabled and an isolated
test database, not the local demonstration data.
