#!/usr/bin/env python3
"""
통합 서버 실행 스크립트
- API 서버와 웹 시뮬레이터 동시 실행
- 포트 충돌 자동 해결
- 프로세스 관리 강화
"""

import sys
import os
import socket
import subprocess
import time
import threading
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

def run_api_server():
    """API 서버 실행"""
    try:
        # 환경 설정
        backend_dir = Path(__file__).parent
        os.chdir(backend_dir)
        sys.path.insert(0, str(backend_dir))
        os.environ['PYTHONPATH'] = str(backend_dir)
        
        from src.api.main import app
        import uvicorn
        
        print("🚀 API 서버 시작 중...")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8001, 
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ API 서버 오류: {e}")

def run_web_server():
    """웹 시뮬레이터 실행"""
    try:
        # 환경 설정
        web_dir = Path(__file__).parent / "web_simulator"
        os.chdir(web_dir)
        sys.path.insert(0, str(web_dir))
        
        from simple_web_server import StableWebHandler
        import socketserver
        
        print("🌐 웹 시뮬레이터 시작 중...")
        with socketserver.TCPServer(("", 8007), StableWebHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ 웹 서버 오류: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 통합 서버 실행!")
    print("=" * 60)
    
    # 포트 정리
    for port in [8001, 8007]:
        if check_port(port):
            print(f"⚠️ 포트 {port} 정리 중...")
            kill_port(port)
    
    print("📡 API 서버: http://localhost:8001")
    print("🌐 웹 시뮬레이터: http://localhost:8007")
    print("📋 Health Check: http://localhost:8001/health")
    print("⏹️  서버 종료: Ctrl+C")
    print("=" * 60)
    
    try:
        # 스레드로 각 서버 실행
        api_thread = threading.Thread(target=run_api_server, daemon=True)
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        
        api_thread.start()
        time.sleep(3)  # API 서버 먼저 시작
        web_thread.start()
        
        print("✅ 모든 서버가 시작되었습니다!")
        print("💡 브라우저에서 http://localhost:8007 접속하세요!")
        
        # 메인 스레드 대기
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n✅ 모든 서버가 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 실행 오류: {e}")

if __name__ == "__main__":
    main() 