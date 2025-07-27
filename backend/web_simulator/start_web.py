#!/usr/bin/env python3
"""
개선된 웹 시뮬레이터 실행 스크립트
- 포트 충돌 자동 해결
- 안정적인 서버 실행
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
    current_dir = Path(__file__).parent
    os.chdir(current_dir)
    sys.path.insert(0, str(current_dir))

def main():
    """메인 실행 함수"""
    print("🌐 개선된 웹 시뮬레이터 서버 시작!")
    print("=" * 50)
    
    # 환경 설정
    setup_environment()
    
    # 포트 체크 및 정리
    web_port = 8000
    if check_port(web_port):
        print(f"⚠️ 포트 {web_port}이 사용 중입니다. 정리 중...")
        kill_port(web_port)
    
    try:
        from simple_web_server import StableWebHandler
        import socketserver
        
        print(f"📡 웹 시뮬레이터: http://localhost:{web_port}")
        print("🔗 API 연결: http://localhost:8001")
        print("⏹️  서버 종료: Ctrl+C")
        print("-" * 50)
        
        with socketserver.TCPServer(("", web_port), StableWebHandler) as httpd:
            print(f"✅ 서버 시작됨: http://localhost:{web_port}")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n✅ 웹 서버가 정상적으로 종료되었습니다.")
    except ImportError as e:
        print(f"\n❌ 모듈 임포트 오류: {e}")
        print("💡 simple_web_server.py 파일을 확인하세요.")
    except Exception as e:
        print(f"\n❌ 웹 서버 오류: {e}")

if __name__ == "__main__":
    main() 