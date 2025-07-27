# 🔧 완전 무료 알림 시스템 환경변수 설정 가이드

## 💰 총 비용: ₩0 (완전 무료!)

모든 알림 채널이 무료 서비스를 사용합니다. 유료 구독이나 결제가 전혀 필요하지 않습니다!

## 📋 필수 환경변수 설정

### 1. 🔐 환경변수 파일 생성

```bash
# backend 디렉토리에서 실행
cp env_setup_guide.md .env
# 또는
touch .env
```

### 2. ✉️ Gmail 무료 이메일 알림 설정

```bash
# .env 파일에 추가
EMAIL_USER=your-email@gmail.com
EMAIL_APP_PASSWORD=your-gmail-app-password
```

**Gmail 앱 비밀번호 생성 방법:**
1. Gmail 계정 로그인
2. 계정 관리 → 보안
3. 2단계 인증 활성화
4. 앱 비밀번호 생성
5. "메일" 앱 선택 → 비밀번호 복사

**비용**: 완전 무료 ✅

### 3. 📱 Firebase FCM 무료 푸시 알림 설정

```bash
# .env 파일에 추가
FCM_SERVER_KEY=your-firebase-fcm-server-key
```

**Firebase FCM 설정 방법:**
1. [Firebase Console](https://console.firebase.google.com) 접속
2. "프로젝트 추가" → 무료 플랜 선택
3. 프로젝트 설정 → Cloud Messaging
4. "서버 키" 복사

**비용**: 완전 무료 ✅ (월 무제한 메시지)

### 4. 🤖 텔레그램 무료 봇 알림 설정

```bash
# .env 파일에 추가
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

**텔레그램 봇 생성 방법:**
1. 텔레그램에서 [@BotFather](https://t.me/BotFather) 검색
2. `/newbot` 명령 실행
3. 봇 이름 및 사용자명 설정
4. 봇 토큰 복사

**비용**: 완전 무료 ✅

### 5. 🗄️ 데이터베이스 설정 (선택사항)

```bash
# .env 파일에 추가 (기본값 사용 가능)
DATABASE_URL=postgresql://username:password@localhost:5432/stock_alert_db
```

**무료 PostgreSQL 옵션:**
- **로컬 설치**: 완전 무료
- **ElephantSQL**: 무료 20MB
- **Supabase**: 무료 500MB
- **Heroku Postgres**: 무료 10,000 rows

## 🚀 환경변수 적용 및 서버 실행

### 1. 환경변수 로드

```bash
# 방법 1: export 명령어
export EMAIL_USER="your-email@gmail.com"
export EMAIL_APP_PASSWORD="your-app-password"
export FCM_SERVER_KEY="your-fcm-key"
export TELEGRAM_BOT_TOKEN="your-bot-token"

# 방법 2: .env 파일 사용 (추천)
source .env
```

### 2. 서버 실행

```bash
# 간편 실행 스크립트
./run_server.sh

# 또는 직접 실행
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 테스트

```bash
# 무료 알림 시스템 테스트
python test_free_notification_system.py
```

## 📊 설정 완료 확인

서버 실행 시 다음과 같이 표시되면 설정 완료:

```
🚀 완전 무료 알림 시스템 서버 시작
💰 비용: ₩0 (완전 무료)
📱 지원 채널: 이메일, FCM, 텔레그램, 웹푸시

🔧 환경변수 확인:
- EMAIL_USER: your-email@gmail.com ✅
- FCM_SERVER_KEY: AIza... ✅
- TELEGRAM_BOT_TOKEN: 1234... ✅

🌐 서버 실행 중... (http://localhost:8000)
📚 API 문서: http://localhost:8000/docs
```

## 🎯 다음 단계

1. **iOS 앱 연동**: FCM SDK 추가
2. **웹 앱 연동**: 웹 푸시 API 구현
3. **사용자 테스트**: 실제 알림 전송 테스트
4. **모니터링**: 알림 전달률 확인

## 💡 문제 해결

### 이메일 알림이 작동하지 않는 경우:
- Gmail 2단계 인증 활성화 확인
- 앱 비밀번호 정확성 확인
- 보안 수준이 낮은 앱 허용 설정

### FCM 푸시가 작동하지 않는 경우:
- Firebase 프로젝트 설정 확인
- 서버 키 유효성 확인
- 클라이언트 토큰 등록 확인

### 텔레그램 봇이 작동하지 않는 경우:
- 봇 토큰 유효성 확인
- 사용자가 봇과 대화 시작했는지 확인
- 채팅 ID 정확성 확인

---

**🎉 모든 설정이 완료되면 완전 무료로 프로페셔널한 알림 시스템을 사용할 수 있습니다!** 