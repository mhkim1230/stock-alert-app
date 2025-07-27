#!/bin/bash

# iOS 시뮬레이터 및 웹 테스트 앱 실행 스크립트
# 완전 무료 알림 시스템 테스트용

echo "📱 iOS 시뮬레이터 및 웹 테스트 앱 실행"
echo "💰 총 비용: ₩0 (완전 무료!)"
echo "=" * 50

# 1. Xcode 및 시뮬레이터 확인
echo "🔍 Xcode 및 iOS 시뮬레이터 확인 중..."

if ! command -v xcrun &> /dev/null; then
    echo "❌ Xcode가 설치되지 않았습니다."
    echo "💡 Xcode를 App Store에서 설치하세요."
    echo "🌐 App Store에서 Xcode 검색 후 설치"
    open "https://apps.apple.com/us/app/xcode/id497799835"
    exit 1
fi

echo "✅ Xcode 발견됨"

# 2. 사용 가능한 시뮬레이터 목록 확인
echo "📱 사용 가능한 iOS 시뮬레이터 목록:"
xcrun simctl list devices available | grep -E "iPhone|iPad" | head -10

# 3. 기본 시뮬레이터 선택 (iPhone 15 Pro 또는 사용 가능한 최신 기기)
SIMULATOR_NAME="iPhone 15 Pro"
SIMULATOR_UUID=$(xcrun simctl list devices available | grep "$SIMULATOR_NAME" | head -1 | grep -o '([^)]*)'  | tr -d '()')

if [ -z "$SIMULATOR_UUID" ]; then
    # iPhone 15 Pro가 없으면 사용 가능한 첫 번째 iPhone 사용
    SIMULATOR_UUID=$(xcrun simctl list devices available | grep "iPhone" | head -1 | grep -o '([^)]*)'  | tr -d '()')
    SIMULATOR_NAME=$(xcrun simctl list devices available | grep "iPhone" | head -1 | sed 's/.*iPhone/iPhone/' | sed 's/ (.*//')
fi

if [ -z "$SIMULATOR_UUID" ]; then
    echo "❌ 사용 가능한 iOS 시뮬레이터를 찾을 수 없습니다."
    echo "💡 Xcode를 실행하여 시뮬레이터를 설치하세요."
    exit 1
fi

echo "📱 선택된 시뮬레이터: $SIMULATOR_NAME ($SIMULATOR_UUID)"

# 4. 시뮬레이터 실행
echo "🚀 iOS 시뮬레이터 실행 중..."
xcrun simctl boot "$SIMULATOR_UUID" 2>/dev/null || echo "시뮬레이터가 이미 실행 중입니다."
open -a Simulator

# 5. 시뮬레이터 부팅 대기
echo "⏳ 시뮬레이터 부팅 대기 중..."
sleep 5

# 6. 백엔드 서버 상태 확인
echo "🔍 백엔드 서버 상태 확인 중..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ 백엔드 서버 실행 중"
else
    echo "⚠️ 백엔드 서버가 실행되지 않았습니다."
    echo "🚀 백엔드 서버를 먼저 실행합니다..."
    
    # 백그라운드에서 서버 실행
    nohup ./run_server.sh > server.log 2>&1 &
    SERVER_PID=$!
    echo "📝 서버 PID: $SERVER_PID"
    
    # 서버 시작 대기
    echo "⏳ 서버 시작 대기 중..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/ > /dev/null; then
            echo "✅ 백엔드 서버 시작 완료"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
fi

# 7. 웹 테스트 앱 열기
echo "🌐 웹 테스트 앱을 시뮬레이터에서 실행 중..."

# 시뮬레이터에서 Safari 열기
xcrun simctl openurl "$SIMULATOR_UUID" "http://localhost:8000/web_simulator/"

# 데스크톱에서도 브라우저 열기 (비교용)
echo "🖥️ 데스크톱 브라우저에서도 테스트 앱 열기..."
sleep 2
open "http://localhost:8000/web_simulator/"

# 8. 테스트 가이드 출력
echo ""
echo "🎉 iOS 시뮬레이터 및 웹 테스트 앱 실행 완료!"
echo "=" * 50
echo ""
echo "📱 테스트 방법:"
echo "1. iOS 시뮬레이터에서 Safari 브라우저 확인"
echo "2. 웹 푸시 알림 권한 요청 버튼 클릭"
echo "3. 알림 권한 허용"
echo "4. 각종 알림 테스트 버튼 클릭"
echo "5. 주식/환율 알림 생성 테스트"
echo ""
echo "🖥️ 데스크톱 브라우저에서도 동일하게 테스트 가능"
echo ""
echo "📊 테스트 항목:"
echo "✅ 웹 푸시 알림 (무료)"
echo "✅ 주식 알림 생성 (무료)"
echo "✅ 환율 알림 생성 (무료)"
echo "✅ 시스템 상태 확인 (무료)"
echo ""
echo "💰 총 비용: ₩0 (완전 무료!)"
echo "🔄 서버 종료: Ctrl+C"
echo ""
echo "📚 API 문서: http://localhost:8000/docs"
echo "🧪 테스트 앱: http://localhost:8000/web_simulator/"
echo ""

# 9. 로그 모니터링 (선택사항)
read -p "📋 서버 로그를 실시간으로 보시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 서버 로그 모니터링 시작 (Ctrl+C로 종료):"
    tail -f logs/stock_alert.log 2>/dev/null || tail -f server.log 2>/dev/null || echo "로그 파일을 찾을 수 없습니다."
fi

echo "🎊 테스트 완료! 즐거운 개발 되세요!" 