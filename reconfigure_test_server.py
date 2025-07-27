#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconfigure 오류 수정 테스트 서버
"""

import json
import time
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# UTF-8 환경 강제 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
# Python 버전 호환성을 위한 안전한 인코딩 설정
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        print("✅ reconfigure 성공!")
    elif hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        print("✅ TextIOWrapper 사용!")
    else:
        print("⚠️ 기본 stdout 사용")
except (AttributeError, OSError) as e:
    print(f"⚠️ 인코딩 설정 실패: {e}")
    # 인코딩 설정이 실패해도 계속 진행
    pass

class TestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """안전한 로그 출력"""
        try:
            message = format % args
            print(f"🔍 {self.address_string()} - {message}")
        except Exception as e:
            print(f"⚠️ 로그 오류: {e}")

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'OK',
            'message': 'reconfigure 오류 수정 테스트 완료! 🎉',
            'korean_test': '한글 테스트: 삼성전자, 애플, 코어위브',
            'encoding': 'UTF-8',
            'timestamp': int(time.time())
        }
        
        json_response = json.dumps(response, ensure_ascii=False, indent=2)
        self.wfile.write(json_response.encode('utf-8'))

def run_test():
    port = 8011
    server_address = ('', port)
    
    try:
        httpd = HTTPServer(server_address, TestHandler)
        print(f"🧪 reconfigure 테스트 서버 시작!")
        print(f"📡 URL: http://localhost:{port}")
        print(f"🔤 한글 테스트: 삼성전자, 애플, 코어위브")
        print(f"⏹️  서버 종료: Ctrl+C")
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 테스트 완료!")
        httpd.shutdown()
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    run_test() 