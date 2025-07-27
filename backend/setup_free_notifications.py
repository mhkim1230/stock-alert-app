#!/usr/bin/env python3
"""
완전 무료 알림 시스템 설정 도우미
- 환경변수 설정 가이드
- 무료 서비스 계정 생성 도움
- 테스트 및 검증
"""

import os
import sys
import subprocess
import webbrowser
from typing import Dict, Any

def print_header():
    """헤더 출력"""
    print("🎉 완전 무료 알림 시스템 설정 도우미")
    print("💰 총 비용: ₩0 (완전 무료!)")
    print("📱 지원 채널: 이메일, FCM, 텔레그램, 웹푸시")
    print("=" * 60)

def check_current_env():
    """현재 환경변수 상태 확인"""
    print("\n🔧 현재 환경변수 상태:")
    
    env_vars = {
        'EMAIL_USER': '이메일 알림 (Gmail)',
        'EMAIL_APP_PASSWORD': '이메일 앱 비밀번호',
        'FCM_SERVER_KEY': 'Firebase FCM 푸시',
        'TELEGRAM_BOT_TOKEN': '텔레그램 봇',
        'DATABASE_URL': '데이터베이스'
    }
    
    status = {}
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value and value != 'your-email@gmail.com' and value != 'your-app-password':
            print(f"✅ {var}: 설정됨 ({description})")
            status[var] = True
        else:
            print(f"❌ {var}: 설정 필요 ({description})")
            status[var] = False
    
    return status

def setup_gmail():
    """Gmail 설정 가이드"""
    print("\n📧 1. Gmail 무료 이메일 알림 설정")
    print("=" * 40)
    
    print("📋 설정 단계:")
    print("1. Gmail 계정에 로그인")
    print("2. 계정 관리 → 보안")
    print("3. 2단계 인증 활성화")
    print("4. 앱 비밀번호 생성")
    print("5. '메일' 앱 선택")
    
    if input("\n🌐 Gmail 계정 관리 페이지를 열까요? (y/n): ").lower() == 'y':
        webbrowser.open('https://myaccount.google.com/security')
    
    print("\n💡 설정 완료 후 다음 명령어를 실행하세요:")
    print("export EMAIL_USER='your-email@gmail.com'")
    print("export EMAIL_APP_PASSWORD='your-app-password'")

def setup_firebase():
    """Firebase FCM 설정 가이드"""
    print("\n🔥 2. Firebase FCM 무료 푸시 알림 설정")
    print("=" * 40)
    
    print("📋 설정 단계:")
    print("1. Firebase Console 접속")
    print("2. '프로젝트 추가' → 무료 플랜 선택")
    print("3. 프로젝트 이름: 'stock-alert-free'")
    print("4. 프로젝트 설정 → Cloud Messaging")
    print("5. '서버 키' 복사")
    
    if input("\n🌐 Firebase Console을 열까요? (y/n): ").lower() == 'y':
        webbrowser.open('https://console.firebase.google.com')
    
    print("\n💡 설정 완료 후 다음 명령어를 실행하세요:")
    print("export FCM_SERVER_KEY='your-firebase-server-key'")

def setup_telegram():
    """텔레그램 봇 설정 가이드"""
    print("\n🤖 3. 텔레그램 무료 봇 알림 설정")
    print("=" * 40)
    
    print("📋 설정 단계:")
    print("1. 텔레그램 앱에서 @BotFather 검색")
    print("2. /newbot 명령 실행")
    print("3. 봇 이름: 'Stock Alert Bot'")
    print("4. 봇 사용자명: 'your_stock_alert_bot'")
    print("5. 봇 토큰 복사")
    
    if input("\n🌐 텔레그램 웹을 열까요? (y/n): ").lower() == 'y':
        webbrowser.open('https://web.telegram.org')
    
    print("\n💡 설정 완료 후 다음 명령어를 실행하세요:")
    print("export TELEGRAM_BOT_TOKEN='your-bot-token'")

def create_env_file():
    """환경변수 파일 생성"""
    print("\n📄 4. 환경변수 파일 생성")
    print("=" * 40)
    
    env_content = """# 완전 무료 알림 시스템 환경변수
# 총 비용: ₩0 (완전 무료!)

# Gmail 무료 이메일 알림
EMAIL_USER=your-email@gmail.com
EMAIL_APP_PASSWORD=your-gmail-app-password

# Firebase FCM 무료 푸시 알림
FCM_SERVER_KEY=your-firebase-fcm-server-key

# 텔레그램 무료 봇 알림
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# 데이터베이스 (기본값 사용 가능)
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_alert_db

# 기타 설정
DEBUG=true
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env 파일이 생성되었습니다!")
        print("📝 파일을 편집하여 실제 값을 입력하세요.")
    except Exception as e:
        print(f"❌ .env 파일 생성 실패: {e}")

def test_services():
    """무료 서비스 테스트"""
    print("\n🧪 5. 무료 알림 시스템 테스트")
    print("=" * 40)
    
    if input("테스트를 실행하시겠습니까? (y/n): ").lower() == 'y':
        try:
            result = subprocess.run([
                sys.executable, 'test_free_notification_system.py'
            ], capture_output=True, text=True)
            
            print("📊 테스트 결과:")
            print(result.stdout)
            
            if result.returncode == 0:
                print("✅ 무료 알림 시스템 테스트 완료!")
            else:
                print("⚠️ 일부 테스트 실패 - 환경변수를 확인하세요.")
                
        except Exception as e:
            print(f"❌ 테스트 실행 실패: {e}")

def run_server():
    """서버 실행"""
    print("\n🚀 6. 서버 실행")
    print("=" * 40)
    
    if input("서버를 실행하시겠습니까? (y/n): ").lower() == 'y':
        print("🌐 서버 실행 중...")
        print("📚 API 문서: http://localhost:8000/docs")
        print("🔄 자동 재로드 활성화")
        print("\n종료하려면 Ctrl+C를 누르세요.")
        
        try:
            subprocess.run(['./run_server.sh'])
        except KeyboardInterrupt:
            print("\n🛑 서버가 중지되었습니다.")

def show_next_steps():
    """다음 단계 안내"""
    print("\n🎯 다음 단계")
    print("=" * 40)
    
    print("1. 📱 iOS 앱 연동:")
    print("   - Xcode에서 Firebase SDK 추가")
    print("   - FCM 토큰 등록 구현")
    print("   - API 연동 테스트")
    
    print("\n2. 🌐 웹 앱 연동:")
    print("   - 서비스 워커 등록")
    print("   - 웹 푸시 구독 구현")
    print("   - 알림 권한 요청")
    
    print("\n3. 📊 모니터링:")
    print("   - 알림 전달률 확인")
    print("   - 사용자 피드백 수집")
    print("   - 성능 최적화")

def main():
    """메인 함수"""
    print_header()
    
    # 현재 상태 확인
    status = check_current_env()
    
    # 설정되지 않은 서비스 안내
    if not all(status.values()):
        print("\n🔧 설정이 필요한 무료 서비스들:")
        
        if not status.get('EMAIL_USER'):
            setup_gmail()
        
        if not status.get('FCM_SERVER_KEY'):
            setup_firebase()
        
        if not status.get('TELEGRAM_BOT_TOKEN'):
            setup_telegram()
        
        # 환경변수 파일 생성
        create_env_file()
        
        print("\n💡 모든 설정 완료 후 다시 이 스크립트를 실행하세요!")
    else:
        print("\n🎉 모든 환경변수가 설정되었습니다!")
        
        # 테스트 실행
        test_services()
        
        # 서버 실행
        run_server()
    
    # 다음 단계 안내
    show_next_steps()
    
    print("\n🎊 완전 무료 알림 시스템 설정 완료!")
    print("💰 월 비용: ₩0 | 연간 절약: $99+")

if __name__ == "__main__":
    main() 