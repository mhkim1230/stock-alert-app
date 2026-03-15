# Stock Alert Backend

Single-user FastAPI backend and hosted PWA for stock, currency, and news alerts.

## Runtime Model
- Root path `/` serves the mobile-friendly PWA
- Web access uses one admin password and an HttpOnly session cookie
- Internal automation still uses `ADMIN_API_KEY`
- Hosted PostgreSQL is the production database
- APNs is optional but supported
- Alert checks run through `POST /internal/run-alert-checks`

## Local Run
```bash
cd backend
python3 -m pip install -r requirements.txt

export DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
export ADMIN_API_KEY=dev-admin-key
export ADMIN_PASSWORD=dev-password
export SESSION_SECRET=dev-session-secret
export AUTO_CREATE_TABLES=true

python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

## Main APIs
- `GET /`
- `POST /session/login`
- `POST /session/logout`
- `GET /session/me`
- `GET /health`
- `GET/POST/DELETE /watchlist`
- `GET/POST/DELETE /alerts/stocks`
- `GET/POST/DELETE /alerts/currencies`
- `GET/POST/DELETE /alerts/news`
- `GET /notifications`
- `PATCH /notifications/{notification_id}/read`
- `POST /device-tokens`
- `GET /stocks/search`
- `GET /stocks/{symbol}`
- `GET /currency/rate`
- `GET /news`
- `POST /internal/run-alert-checks`

Session-based web access:
```http
POST /session/login
```

Internal or direct API access:
```http
X-Admin-Key: YOUR_ADMIN_API_KEY
```

## Test
```bash
cd backend
export TEST_DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
export TEST_ADMIN_API_KEY=test-admin-key
export TEST_ADMIN_PASSWORD=test-password
python3 -m pytest -q
```

## Hosted DB Check
```bash
cd backend
export DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
python3 scripts/check_hosted_db.py
```

## Deploy
- App server: Render
- Database: Supabase PostgreSQL
- Env example: [env.example](/Users/mhkim/AI프로젝트/backend/env.example)
- Blueprint: [render.yaml](/Users/mhkim/AI프로젝트/render.yaml)
