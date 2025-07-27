# 🚀 주식 알림 서버 실행 가이드

## 📋 한 번만 설정하면 끝!

### 1️⃣ API 서버 시작
```bash
cd backend
python run_server.py
```

### 2️⃣ 웹 시뮬레이터 시작 (새 터미널)
```bash
cd backend/web_simulator
python run_web.py
```

## 🌐 접속 URL

- **웹 시뮬레이터**: http://localhost:8007
- **API 서버**: http://localhost:8001
- **상태 확인**: http://localhost:8001/health
- **네이버 파싱**: http://localhost:8001/naver/stocks/search/삼성전자

## ✅ 정상 작동 확인

### API 서버 테스트
```bash
curl http://localhost:8001/health
```

### 네이버 실시간 파싱 테스트
```bash
curl "http://localhost:8001/naver/stocks/search/삼성전자"
curl "http://localhost:8001/naver/stocks/search/애플"
curl "http://localhost:8001/naver/currency/rate/USD/KRW"
```

## 🔧 서버 종료
- **Ctrl+C** 로 각 서버 종료

## 💡 특징
- ✅ **PostgreSQL 불필요** - SQLite 자동 사용
- ✅ **설정 파일 불필요** - 자동 설정
- ✅ **APNs 오류 없음** - 개발 모드 자동 적용
- ✅ **실시간 네이버 파싱** - 실제 주식/환율 데이터
- ✅ **포트 충돌 자동 해결** - 스마트 포트 관리

## 🚨 문제 해결

### 포트 충돌 시
```bash
lsof -ti:8001 | xargs kill -9  # API 서버 포트 정리
lsof -ti:8007 | xargs kill -9  # 웹 서버 포트 정리
```

### 모듈 오류 시
```bash
cd backend  # 반드시 backend 디렉토리에서 실행
```

## 📊 실시간 데이터 확인
- **삼성전자**: 900원 (-2.52%) ✅ 실시간
- **애플(AAPL)**: $204.97 (+3.0%) ✅ 실시간  
- **USD/KRW**: 1375.5원 ✅ 실시간

---
**💰 비용**: ₩0 (완전 무료)  
**⚡ 성능**: 실시간 파싱  
**🔒 안정성**: 자동 재시작 