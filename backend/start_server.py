#!/usr/bin/env python3
"""
개선된 서버 실행 스크립트
- 포트 충돌 자동 해결
- 가상환경 자동 감지
- 오류 처리 강화
"""

import sys
import os
import socket
import subprocess
import time
from pathlib import Path

def check_port(port):
    """포트 사용 여부 확인"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('localhost', port))
        return result == 0

def kill_port(port):
    """포트 사용 중인 프로세스 종료"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(['kill', '-9', pid], check=False)
            time.sleep(2)
            print(f"✅ 포트 {port} 정리 완료")
    except Exception as e:
        print(f"⚠️ 포트 정리 중 오류: {e}")

def setup_environment():
    """환경 설정"""
    # 현재 디렉토리를 Python 경로에 추가
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # 환경 변수 설정
    os.environ['PYTHONPATH'] = str(current_dir)
    os.chdir(current_dir)

def main():
    """메인 실행 함수"""
    print("🚀 개선된 주식 알림 API 서버 시작!")
    print("=" * 50)
    
    # 환경 설정
    setup_environment()
    
    # 포트 체크 및 정리
    api_port = 8001
    if check_port(api_port):
        print(f"⚠️ 포트 {api_port}이 사용 중입니다. 정리 중...")
        kill_port(api_port)
    
    # 서버 실행
    try:
        from src.api.main import app
        import uvicorn
        
        print(f"📡 API 서버: http://localhost:{api_port}")
        print("📋 Health Check: http://localhost:8001/health")
        print("📊 네이버 파싱: http://localhost:8001/naver/stocks/search/삼성전자")
        print("⏹️  서버 종료: Ctrl+C")
        print("-" * 50)
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=api_port, 
            reload=False,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n✅ 서버가 정상적으로 종료되었습니다.")
    except ImportError as e:
        print(f"\n❌ 모듈 임포트 오류: {e}")
        print("💡 해결 방법: 가상환경 활성화 후 다시 시도")
        print("   source venv/bin/activate")
    except Exception as e:
        print(f"\n❌ 서버 오류: {e}")
        print("💡 로그를 확인하여 문제를 해결하세요.")

if __name__ == "__main__":
    main() 