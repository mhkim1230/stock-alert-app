# 🚀 개선된 서버 실행 가이드

## 🔧 문제점 해결

기존 서버 실행 시 발생하던 문제들을 해결했습니다:

### ❌ 기존 문제점들
- `python` 명령어 인식 불가 (macOS에서 `python3` 필요)
- 포트 충돌 시 수동 처리 필요
- 가상환경 경로 문제
- 백그라운드 실행 시 오류 처리 부족
- 모듈 임포트 경로 문제

### ✅ 개선된 해결책

## 📋 실행 방법

### 1️⃣ 통합 실행 (권장)
```bash
cd backend
source venv/bin/activate
python3 start_all.py
```

### 2️⃣ 개별 실행

**API 서버만 실행:**
```bash
cd backend
source venv/bin/activate
python3 start_server.py
```

**웹 시뮬레이터만 실행:**
```bash
cd backend/web_simulator
source venv/bin/activate
python3 start_web.py
```

## 🌐 접속 URL

- **웹 시뮬레이터**: http://localhost:8007
- **API 서버**: http://localhost:8001
- **상태 확인**: http://localhost:8001/health

## ✅ 개선 사항

### 🔄 자동 포트 관리
- 포트 충돌 시 자동으로 기존 프로세스 종료
- 안전한 포트 정리 및 재시작

### 🛡️ 강화된 오류 처리
- 모듈 임포트 오류 시 명확한 해결 방법 제시
- 가상환경 미활성화 시 안내 메시지
- 예외 상황별 맞춤형 오류 메시지

### 🎯 환경 설정 자동화
- Python 경로 자동 설정
- 작업 디렉토리 자동 변경
- 환경 변수 자동 구성

### 📊 실시간 상태 모니터링
- 서버 시작 과정 실시간 표시
- 포트 사용 상태 확인
- 서버 간 의존성 관리

## 🚨 문제 해결

### Python 명령어 오류
```bash
# ❌ 이렇게 하지 마세요
python run_server.py

# ✅ 이렇게 하세요
python3 start_server.py
```

### 가상환경 미활성화
```bash
# 가상환경 활성화 확인
source venv/bin/activate
# 터미널 프롬프트에 (venv) 표시 확인
```

### 포트 충돌 시
```bash
# 자동 해결됨! 더 이상 수동 처리 불필요
# 기존: lsof -ti:8001 | xargs kill -9
# 현재: 스크립트가 자동으로 처리
```

## 🔍 테스트 명령어

### API 서버 테스트
```bash
curl http://localhost:8001/health
curl "http://localhost:8001/naver/stocks/search/삼성전자"
```

### 웹 시뮬레이터 테스트
브라우저에서 http://localhost:8007 접속

## 💡 추가 기능

### 📝 로그 확인
- 실시간 로그 출력
- 오류 발생 시 상세 정보 제공
- 서버 상태 변화 추적

### 🔧 개발자 모드
- 자동 재시작 비활성화 (안정성 우선)
- 상세 로그 레벨 설정
- 개발 환경 최적화

---

## 🎉 결과

이제 서버 실행이 **안정적**이고 **간편**해졌습니다!

- ✅ **원클릭 실행**: `python3 start_all.py`
- ✅ **자동 문제 해결**: 포트 충돌, 환경 설정 등
- ✅ **명확한 오류 메시지**: 문제 발생 시 해결 방법 제시
- ✅ **통합 관리**: API + 웹 서버 동시 실행

**💰 비용**: ₩0 (완전 무료)  
**⚡ 성능**: 개선된 안정성  
**🔒 신뢰성**: 자동 오류 복구 