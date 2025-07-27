#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
안정적인 웹 시뮬레이터 서버
- 고정 포트 8000
- 자동 API 서버 연결 (localhost:8001)
- 설정 불필요
"""

import http.server
import socketserver
import os
import sys
import json
from urllib.parse import urlparse, parse_qs, quote
import requests
import threading
import time

# UTF-8 환경 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

class StableWebHandler(http.server.SimpleHTTPRequestHandler):
    """안정적인 웹 핸들러"""
    
    def __init__(self, *args, **kwargs):
        # API 서버 URL 고정
        self.api_base_url = "http://localhost:8000"
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET 요청 처리"""
        if self.path == '/':
            self.path = '/index.html'
        
        # API 상태 확인 엔드포인트
        if self.path == '/api-status':
            self.send_api_status()
            return
            
        # 기본 파일 서빙
        return super().do_GET()
    
    def do_POST(self):
        """POST 요청 처리"""
        if self.path == '/test-api':
            self.handle_api_test()
        elif self.path == '/search-stock':
            self.handle_stock_search()
        elif self.path == '/get-currency':
            self.handle_currency_request()
        else:
            self.send_error(404, "Not Found")
    
    def send_api_status(self):
        """API 서버 상태 확인"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=3)
            if response.status_code == 200:
                status = {
                    "status": "connected",
                    "message": "API 서버 연결됨",
                    "api_url": self.api_base_url,
                    "api_data": response.json()
                }
            else:
                status = {
                    "status": "error",
                    "message": f"API 서버 오류: {response.status_code}",
                    "api_url": self.api_base_url
                }
        except Exception as e:
            status = {
                "status": "disconnected",
                "message": f"API 서버 연결 실패: {str(e)}",
                "api_url": self.api_base_url,
                "fallback": "시뮬레이션 모드"
            }
        
        self.send_json_response(status)

    def handle_api_test(self):
        """API 테스트 처리"""
        try:
            # 실제 API 서버 테스트
            response = requests.get(f"{self.api_base_url}/health", timeout=3)
            if response.status_code == 200:
                result = {
                    "success": True,
                    "message": "✅ API 서버 연결 성공!",
                    "api_url": self.api_base_url,
                    "server_info": response.json()
                }
            else:
                result = {
                    "success": False,
                    "message": f"❌ API 서버 오류: {response.status_code}",
                    "api_url": self.api_base_url
                }
        except Exception as e:
            result = {
                "success": False,
                "message": f"❌ API 서버 연결 실패: {str(e)}",
                "api_url": self.api_base_url,
                "suggestion": "backend 디렉토리에서 'python -c \"import sys; sys.path.append('.'); from src.api.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8001)\" 실행"
            }
        
        self.send_json_response(result)
    
    def handle_stock_search(self):
        """주식 검색 처리"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            query = data.get('query', '')
            
            # URL 인코딩 처리
            encoded_query = quote(query, safe='')
            
            # 네이버 실시간 파싱 API 호출
            try:
                api_url = f"{self.api_base_url}/naver/stocks/search/{encoded_query}"
                print(f"🔍 API 호출: {api_url}")  # 디버그 로그
                
                headers = {'Content-Type': 'application/json; charset=utf-8'}
                response = requests.get(api_url, headers=headers, timeout=5)
                print(f"📡 응답 상태: {response.status_code}")  # 디버그 로그
                
                if response.status_code == 200:
                    api_data = response.json()
                    print(f"📊 응답 데이터: {api_data}")  # 디버그 로그
                    if api_data and len(api_data.get('results', [])) > 0:
                        stock_info = api_data['results'][0]
                        
                        # 가격 형식 통일 (문자열 제거 및 숫자로 변환)
                        price = stock_info.get("current_price", 0)
                        if isinstance(price, str):
                            price = float(price.replace('원', '').replace(',', '').replace('$', '').strip())
                        
                        result = {
                            "success": True,
                            "data": {
                                "symbol": stock_info.get("symbol", query),
                                "name": stock_info.get("name_kr", query),
                                "price": price,
                                "change_percent": stock_info.get("change_percent", 0),
                                "source": "naver_real_parsing",
                                "market": stock_info.get("market", "UNKNOWN")
                            },
                            "message": f"✅ {query} 실시간 데이터 조회 성공"
                        }
                    else:
                        print("❌ API 응답 데이터 없음")  # 디버그 로그
                        raise Exception("데이터 없음")
                else:
                    print(f"❌ API 응답 오류: {response.status_code}")  # 디버그 로그
                    raise Exception(f"API 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 네이버 파싱 실패: {str(e)}")  # 디버그 로그
                result = {
                    "success": False,
                    "message": f"❌ {query} 실시간 데이터 조회 실패: {str(e)}",
                    "error": "네이버 파싱 서버 연결 실패"
                }
                
        except Exception as e:
            result = {
                "success": False,
                "message": f"주식 검색 오류: {str(e)}"
            }
        
        self.send_json_response(result)
    
    def handle_currency_request(self):
        """환율 조회 처리"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            from_currency = data.get('from', 'USD')
            to_currency = data.get('to', 'KRW')
            
            # 네이버 실시간 환율 파싱 API 호출
            try:
                api_url = f"{self.api_base_url}/naver/currency/rate/{from_currency}/{to_currency}"
                print(f"🔍 환율 API 호출: {api_url}")  # 디버그 로그
                response = requests.get(api_url, timeout=5)
                print(f"📡 환율 응답 상태: {response.status_code}")  # 디버그 로그
                
                if response.status_code == 200:
                    api_data = response.json()
                    print(f"📊 환율 응답 데이터: {api_data}")  # 디버그 로그
                    result = {
                        "success": True,
                        "data": {
                            "from": from_currency,
                            "to": to_currency,
                            "rate": api_data.get("rate", 0),
                            "source": "naver_real_parsing"
                        },
                        "message": f"✅ {from_currency}→{to_currency} 실시간 환율 조회 성공"
                    }
                else:
                    print(f"❌ 환율 API 응답 오류: {response.status_code}")  # 디버그 로그
                    raise Exception(f"API 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 네이버 환율 파싱 실패: {str(e)}")  # 디버그 로그
                result = {
                    "success": False,
                    "message": f"❌ {from_currency}→{to_currency} 실시간 환율 조회 실패: {str(e)}",
                    "error": "네이버 환율 파싱 서버 연결 실패"
                }
                
        except Exception as e:
            result = {
                "success": False,
                "message": f"환율 조회 오류: {str(e)}"
            }
        
        self.send_json_response(result)
    

    
    def send_json_response(self, data):
        """JSON 응답 전송"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """로그 메시지 (간소화)"""
        pass

def check_api_server():
    """API 서버 상태 주기적 확인"""
    api_url = "http://localhost:8000"
    while True:
        try:
            response = requests.get(f"{api_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ API 서버 연결됨: {api_url}")
            else:
                print(f"⚠️ API 서버 응답 이상: {response.status_code}")
        except:
            print(f"❌ API 서버 연결 실패: {api_url}")
        
        time.sleep(30)  # 30초마다 확인

def main():
    """메인 서버 실행"""
    PORT = 8000
    API_PORT = 8001
    
    # 현재 디렉토리를 웹 루트로 설정
    web_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_directory)
    
    print("🌐 안정적인 웹 시뮬레이터 서버 시작!")
    print(f"📡 URL: http://localhost:{PORT}")
    print(f"🔗 API 서버: http://localhost:{API_PORT}")
    print(f"📁 디렉토리: {web_directory}")
            
    # 웹 파일 확인
    web_files = [f for f in os.listdir('.') if f.endswith('.html')]
    print(f"📄 웹 파일: {web_files}")
    print("⏹️  서버 종료: Ctrl+C")
    print("-" * 50)
    
    # API 서버 상태 확인 스레드 시작
    api_check_thread = threading.Thread(target=check_api_server, daemon=True)
    api_check_thread.start()
    
    # 웹 서버 시작
    try:
        socketserver.TCPServer.allow_reuse_address = True  # 소켓 재사용 옵션 활성화
        with socketserver.TCPServer(("", PORT), StableWebHandler) as httpd:
            print(f"✅ 웹 서버가 포트 {PORT}에서 시작되었습니다.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 서버가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")

if __name__ == "__main__":
    main() 