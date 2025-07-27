#!/usr/bin/env python3
"""
간단한 테스트 서버 - 웹 시뮬레이터 연결 테스트용
완전 무료 알림 시스템
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import threading
import time

class StockAlertHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 웹 시뮬레이터 페이지 서빙
        if path == '/web_simulator/' or path == '/web_simulator/index.html':
            self.serve_web_simulator()
        elif path == '/':
            self.serve_api_status()
        elif path == '/health':
            self.serve_health_check()
        elif path == '/web_simulator/status':
            self.serve_simulator_status()
        else:
            self.send_error(404, "페이지를 찾을 수 없습니다")
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/web_simulator/test':
            self.handle_test_request()
        else:
            self.send_error(404, "API 엔드포인트를 찾을 수 없습니다")
    
    def serve_web_simulator(self):
        """웹 시뮬레이터 HTML 서빙"""
        html_file = 'web_simulator/index.html'
        
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            self.serve_fallback_simulator()
    
    def serve_fallback_simulator(self):
        """웹 시뮬레이터 대체 페이지"""
        html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Stock Alert - 완전 무료 알림 테스트</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .cost-info {
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #333;
            padding: 15px;
            text-align: center;
            font-weight: bold;
        }
        .content {
            padding: 30px 20px;
        }
        .test-button {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 15px 25px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
        }
        .status {
            background: #e8f5e8;
            border: 1px solid #4CAF50;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
        }
        #log {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Stock Alert</h1>
            <p>완전 무료 알림 시스템 테스트</p>
        </div>
        
        <div class="cost-info">
            💰 총 비용: ₩0 (완전 무료!)
        </div>
        
        <div class="content">
            <div class="status">
                <h3>📊 시스템 상태</h3>
                <div id="systemStatus">✅ 서버 연결 성공!</div>
            </div>
            
            <button class="test-button" onclick="testNotification()">
                📱 웹 푸시 알림 테스트
            </button>
            
            <button class="test-button" onclick="testStockAlert()">
                📈 주식 알림 테스트
            </button>
            
            <button class="test-button" onclick="testCurrencyAlert()">
                💱 환율 알림 테스트
            </button>
            
            <div style="margin-top: 20px;">
                <h4>📋 로그</h4>
                <div id="log"></div>
            </div>
        </div>
    </div>

    <script>
        function log(message) {
            const logElement = document.getElementById('log');
            const timestamp = new Date().toLocaleTimeString();
            logElement.innerHTML += `[${timestamp}] ${message}\\n`;
            logElement.scrollTop = logElement.scrollHeight;
        }
        
        function testNotification() {
            if ('Notification' in window) {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        new Notification('📱 Stock Alert 테스트', {
                            body: '완전 무료 웹 푸시 알림이 작동합니다! 💰 비용: ₩0',
                            icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">📱</text></svg>'
                        });
                        log('✅ 웹 푸시 알림 전송 성공');
                    } else {
                        log('❌ 알림 권한이 거부되었습니다');
                    }
                });
            } else {
                log('❌ 이 브라우저는 웹 푸시를 지원하지 않습니다');
            }
        }
        
        function testStockAlert() {
            log('📈 주식 알림 테스트: AAPL > $200');
            setTimeout(() => {
                log('✅ 주식 알림 생성 성공 (시뮬레이션)');
                alert('주식 알림이 생성되었습니다!\\nAAPL > $200');
            }, 1000);
        }
        
        function testCurrencyAlert() {
            log('💱 환율 알림 테스트: USD/KRW > 1400');
            setTimeout(() => {
                log('✅ 환율 알림 생성 성공 (시뮬레이션)');
                alert('환율 알림이 생성되었습니다!\\nUSD/KRW > 1400');
            }, 1000);
        }
        
        // 페이지 로드 시 초기화
        window.onload = function() {
            log('🚀 완전 무료 알림 시스템 테스트 시작');
            log('💰 총 비용: ₩0 | 연간 절약: $99+');
            log('📱 지원 채널: 이메일, FCM, 텔레그램, 웹푸시');
        };
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_api_status(self):
        """API 상태 응답"""
        response = {
            "status": "success",
            "message": "완전 무료 알림 시스템이 정상 작동 중입니다!",
            "cost": "₩0",
            "features": ["이메일", "FCM", "텔레그램", "웹푸시"],
            "annual_savings": "$99+"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def serve_health_check(self):
        """헬스 체크 응답"""
        response = {
            "status": "healthy",
            "message": "완전 무료 알림 시스템 서버가 정상 작동 중입니다.",
            "timestamp": time.time()
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def serve_simulator_status(self):
        """시뮬레이터 상태 응답"""
        response = {
            "system": "완전 무료 알림 시스템",
            "status": "정상 작동",
            "cost": "₩0",
            "annual_savings": "$99+",
            "notification_channels": 4,
            "platform_support": ["iOS", "Android", "Web", "Desktop"]
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_test_request(self):
        """테스트 요청 처리"""
        response = {
            "status": "success",
            "message": "테스트 요청이 성공적으로 처리되었습니다!",
            "cost": "₩0 (완전 무료!)"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

def run_server(port=8080):
    """서버 실행"""
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, StockAlertHandler)
    
    print(f"🎉 완전 무료 알림 시스템 테스트 서버 시작!")
    print(f"💰 총 비용: ₩0 (완전 무료!)")
    print(f"🌐 서버 주소: http://localhost:{port}")
    print(f"🧪 웹 시뮬레이터: http://localhost:{port}/web_simulator/")
    print(f"📚 API 상태: http://localhost:{port}/")
    print(f"❤️ 헬스 체크: http://localhost:{port}/health")
    print("=" * 60)
    print("🔄 서버 종료: Ctrl+C")
    print("📱 브라우저에서 웹 시뮬레이터를 테스트하세요!")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다.")
        httpd.server_close()

if __name__ == "__main__":
    run_server() 