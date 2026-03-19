# Deploy Now

## 1. Supabase
1. Supabase에서 새 프로젝트를 생성합니다.
2. `Project Settings -> Database -> Connection string` 에서 PostgreSQL URI를 복사합니다.
3. 비밀번호를 실제 값으로 치환한 뒤 저장합니다.

필요 값:
- `DATABASE_URL`

## 2. Render
1. GitHub에 이 저장소를 푸시합니다.
2. Render에서 `Blueprint` 또는 `New Web Service` 로 저장소를 연결합니다.
3. 루트의 [render.yaml](/Users/mhkim/AI프로젝트/render.yaml) 기준으로 배포합니다.
4. 아래 환경 변수를 입력합니다.

필수 환경 변수:
- `DATABASE_URL`
- `ADMIN_API_KEY`
- `APNS_KEY_ID`
- `APNS_TEAM_ID`
- `APNS_BUNDLE_ID`
- `APNS_PRIVATE_KEY`

선택 환경 변수:
- `ALLOWED_ORIGINS`
- `DEBUG=false`
- `APNS_USE_SANDBOX=true`

## 3. Snapshot Refresh
Render free 플랜에서는 Cron Job을 쓸 수 없으므로, GitHub Actions가 5분마다 스냅샷 갱신을 호출합니다.

GitHub 저장소 `Settings -> Secrets and variables -> Actions` 에 아래 두 값을 추가합니다.
- `RENDER_BASE_URL`
- `ADMIN_API_KEY`

예:
```text
RENDER_BASE_URL=https://stock-alert-app.onrender.com
ADMIN_API_KEY=stockalert-admin-2026-secret-key-1230
```

워크플로 파일:
- `.github/workflows/refresh-market-snapshots.yml`

실행 내용:
- `POST /internal/refresh-watchlist-quotes`
- `POST /internal/refresh-fx-quotes`

수동 실행도 가능합니다.
```bash
curl -X POST https://YOUR_RENDER_APP.onrender.com/internal/refresh-watchlist-quotes \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"

curl -X POST https://YOUR_RENDER_APP.onrender.com/internal/refresh-fx-quotes \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

## 4. iPhone App
앱의 설정 화면에서 아래 두 값을 입력합니다.
- `Server URL`
- `Admin API Key`

이제 로그인 없이 서버에 연결됩니다.

## 5. Quick Check
```bash
curl https://YOUR_RENDER_APP.onrender.com/health
curl https://YOUR_RENDER_APP.onrender.com/watchlist -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

## 6. Test Rule
- 테스트 DB도 로컬 SQLite를 쓰지 않습니다.
- `TEST_DATABASE_URL` 은 Hosted PostgreSQL이어야 합니다.
- 운영 DB URL을 테스트에 재사용하지 마세요.
