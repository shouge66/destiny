# frontend-spa

Lightweight single page app built with plain HTML/CSS/JavaScript.

## Run with Django backend

1. Start backend API:

```bash
python manage.py runserver 127.0.0.1:8000
```

2. Start static frontend server from `frontend-spa` folder (example):

```bash
python -m http.server 5500
```

3. Open:

- http://127.0.0.1:5500

## Auth flow

- Login: `POST /api/auth/token/`
- Refresh: `POST /api/auth/token/refresh/`

Default API base is configured in `js/config.js`.
