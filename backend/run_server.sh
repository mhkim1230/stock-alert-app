#!/bin/bash
# 완전 무료 알림 시스템 서버 실행 스크립트

echo "🚀 완전 무료 알림 시스템 서버 시작"
echo "💰 비용: ₩0 (완전 무료)"
echo "📱 지원 채널: 이메일, FCM, 텔레그램, 웹푸시"
echo "=" * 50

# 가상환경 활성화
source venv/bin/activate

# 환경변수 확인
echo "🔧 환경변수 확인:"
echo "- EMAIL_USER: ${EMAIL_USER:-'설정 필요'}"
echo "- FCM_SERVER_KEY: ${FCM_SERVER_KEY:-'설정 필요'}"
echo "- TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-'설정 필요'}"
echo ""

# 데이터베이스 마이그레이션 (필요시)
echo "🗄️ 데이터베이스 확인 중..."
python database_migration.py

# 서버 실행
echo "🌐 서버 실행 중... (http://localhost:8000)"
echo "📚 API 문서: http://localhost:8000/docs"
echo "🔄 자동 재로드 활성화"
echo ""

python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload 