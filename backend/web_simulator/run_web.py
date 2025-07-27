#!/usr/bin/env python3
"""
웹 시뮬레이터 실행 스크립트
사용법: python run_web.py [포트번호]
"""

import sys
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
import signal
import threading
import socketserver
import time
import argparse
from typing import Optional

# 포트 설정
PORT = 8008
API_PORT = 8000

# 현재 디렉토리 경로
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_web_server():
    try:
        server_address = ('', PORT)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        
        print("🌐 웹 시뮬레이터 서버 시작!")
        print(f"📡 URL: http://localhost:{PORT}")
        print(f"🔗 API 연결: http://localhost:{API_PORT}")
        print("⏹️  서버 종료: Ctrl+C")
        print("-" * 50)
        
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 포트 {PORT}가 이미 사용 중입니다.")
            print("💡 다른 프로세스를 종료하고 다시 시도하세요.")
            sys.exit(1)
        else:
            print(f"❌ 서버 오류: {str(e)}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ 서버를 종료합니다...")
        httpd.server_close()
        sys.exit(0)

def parse_args():
    """커맨드 라인 인자 파싱"""
    parser = argparse.ArgumentParser(description="웹 시뮬레이터 서버")
    parser.add_argument("--port", type=int, default=8000, help="시작 포트 번호 (기본값: 8000)")
    return parser.parse_args()

if __name__ == "__main__":
    run_web_server() 