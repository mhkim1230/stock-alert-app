# 🚀 주식 알림 앱 - 무료 클라우드 배포 가이드

## 📋 개요
로컬 PC 없이도 24/7 안정적으로 운영되는 주식 알림 시스템을 무료 클라우드에 배포하는 방법입니다.

## 🏗️ 아키텍처

```
[iPhone 앱] → [Render.com API 서버] → [Supabase PostgreSQL DB]
                     ↓
              [네이버 파싱 + 캐싱]
```

## 💰 비용 (완전 무료!)

| 서비스 | 무료 한도 | 예상 사용량 | 비용 |
|--------|-----------|-------------|------|
| Render.com | 750시간/월 | 720시간/월 | ₩0 |
| Supabase | 500MB + 무제한 API | 100MB | ₩0 |
| **총합** | | | **₩0** |

## 🚀 배포 단계

### 1단계: Supabase 데이터베이스 설정

1. [Supabase](https://supabase.com) 가입
2. "New Project" 클릭
3. 프로젝트 이름: `stock-alert-db`
4. 데이터베이스 비밀번호 설정
5. 리전: `Southeast Asia (Singapore)` 선택
6. "Create new project" 클릭

**CONNECTION URL 복사:**
```
Database URL: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

### 2단계: GitHub 리포지토리 설정

1. GitHub에서 새 리포지토리 생성
2. 프로젝트 코드 업로드:
```bash
git init
git add .
git commit -m "Initial commit: 클라우드 최적화 완료"
git branch -M main
git remote add origin https://github.com/your-username/stock-alert-app.git
git push -u origin main
```

### 3단계: Render.com 배포

1. [Render.com](https://render.com) 가입
2. "New Web Service" 클릭
3. GitHub 리포지토리 연결
4. 설정:
   - **Name**: `stock-alert-api`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

### 4단계: 환경변수 설정

Render.com 대시보드에서 다음 환경변수 추가:

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
DEBUG=false
ENABLE_CACHING=true
CACHE_TIMEOUT=300
SECRET_KEY=[자동생성]
LOG_LEVEL=INFO
```

### 5단계: 배포 완료 확인

1. 배포 로그 확인
2. 서비스 URL 접속 테스트:
   - `https://your-app.onrender.com/health`
   - `https://your-app.onrender.com/naver/stocks/search/삼성전자`

## 📱 iPhone 앱 설정 변경

기존 로컬 URL을 클라우드 URL로 변경:

```swift
// 변경 전
let apiBaseURL = "http://localhost:8001"

// 변경 후  
let apiBaseURL = "https://your-app.onrender.com"
```

## 🔧 최적화 기능

### 1. 네이버 파싱 안정화
- ✅ 5개 헤더 로테이션
- ✅ 1-3초 랜덤 딜레이
- ✅ 5분 캐싱 전략
- ✅ 3회 재시도 로직

### 2. 데이터베이스 자동 전환
- ✅ 클라우드: PostgreSQL (Supabase)
- ✅ 로컬: SQLite (백업)
- ✅ 자동 마이그레이션

### 3. 성능 최적화
- ✅ 커넥션 풀링
- ✅ 백그라운드 스케줄러
- ✅ 에러 복구 로직

## 🚨 문제 해결

### 배포 실패 시
```bash
# 로그 확인
render logs

# 의존성 재설치
pip install -r requirements.txt --force-reinstall
```

### 데이터베이스 연결 오류
1. Supabase 프로젝트 상태 확인
2. DATABASE_URL 환경변수 재확인
3. 네트워크 방화벽 설정 확인

### 파싱 실패 시
- 자동 재시도 로직 작동
- 캐시된 데이터 제공
- 로그에서 상세 에러 확인

## 🎉 완료!

이제 PC를 끄고 여행을 가도 앱이 24/7 안정적으로 작동합니다!

**접속 URL:**
- API 서버: `https://your-app.onrender.com`
- 관리 대시보드: Render.com + Supabase
- 총 비용: **₩0** (완전 무료)

## 📞 지원

문제 발생 시 GitHub Issues로 문의해주세요. 