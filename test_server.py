#!/usr/bin/env python3
"""
완전 무료 웹 스크래핑 기반 주식 테스트 서버
- 네이버 금융, 구글 파이낸스, 다음 금융에서 실시간 주식 데이터 스크래핑
- 유료 API 완전 제거
- 브라우저 푸시 알림 지원
"""

import http.server
import socketserver
import json
import urllib.parse
import sys
import os
from datetime import datetime

# 백엔드 모듈 import를 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

try:
    from services.web_scraping_service import WebScrapingStockService
    SCRAPING_AVAILABLE = True
    print("✅ 웹 스크래핑 서비스 로드 성공")
except ImportError as e:
    print(f"⚠️ 웹 스크래핑 서비스 로드 실패: {e}")
    SCRAPING_AVAILABLE = False

# 포트 설정
PORT = 8003
while True:
    try:
        with socketserver.TCPServer(("", PORT), None) as test_server:
            break
    except OSError:
        PORT += 1
        if PORT > 8010:
            print("❌ 사용 가능한 포트를 찾을 수 없습니다.")
            sys.exit(1)

class StockTestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        if SCRAPING_AVAILABLE:
            self.stock_scraper = WebScrapingStockService()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET 요청 처리"""
        if self.path == '/':
            self.send_main_page()
        elif self.path == '/web_simulator/':
            self.send_web_simulator()
        elif self.path.startswith('/api/search/stocks'):
            self.handle_stock_search()
        elif self.path.startswith('/api/trending'):
            self.handle_trending_stocks()
        else:
            super().do_GET()
    
    def send_main_page(self):
        """메인 페이지"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>📈 무료 웹 스크래핑 주식 서비스</title>
            <meta charset="utf-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .card { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .btn { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📈 완전 무료 웹 스크래핑 주식 서비스</h1>
                
                <div class="card">
                    <h2>🌐 데이터 소스</h2>
                    <ul>
                        <li><strong>네이버 금융</strong> - 한국 주식 우선</li>
                        <li><strong>구글 파이낸스</strong> - 해외 주식 우선</li>
                        <li><strong>다음 금융</strong> - 백업 소스</li>
                        <li><strong>야후 파이낸스</strong> - 백업 소스</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h2>🚀 테스트 링크</h2>
                    <p><a href="/web_simulator/" class="btn">📱 웹 시뮬레이터 열기</a></p>
                    <p><a href="/api/search/stocks?q=삼성전자" class="btn">🔍 삼성전자 검색</a></p>
                    <p><a href="/api/search/stocks?q=AAPL" class="btn">🍎 Apple 검색</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_web_simulator(self):
        """웹 시뮬레이터 페이지"""
        html = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📈 무료 주식 알림 앱</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .phone { 
                    max-width: 375px; 
                    margin: 0 auto; 
                    background: #000; 
                    border-radius: 25px; 
                    padding: 10px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                }
                .screen { 
                    background: #fff; 
                    border-radius: 20px; 
                    height: 700px; 
                    overflow: hidden;
                }
                .header { 
                    background: linear-gradient(135deg, #007AFF, #5856D6);
                    color: white; 
                    padding: 40px 20px 20px; 
                    text-align: center;
                }
                .content { 
                    padding: 20px; 
                    height: calc(100% - 120px); 
                    overflow-y: auto;
                }
                .search-box { 
                    width: 100%; 
                    padding: 12px 16px; 
                    border: 2px solid #e9ecef; 
                    border-radius: 25px; 
                    font-size: 16px;
                    margin-bottom: 20px;
                }
                .search-box:focus { 
                    outline: none; 
                    border-color: #007AFF; 
                }
                .search-results { 
                    margin-top: 20px; 
                }
                .stock-item { 
                    background: white; 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin-bottom: 10px; 
                    border: 1px solid #e9ecef;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .stock-item:hover { 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
                    transform: translateY(-2px);
                }
                .stock-symbol { 
                    font-weight: bold; 
                    color: #007AFF; 
                    font-size: 18px;
                }
                .stock-name { 
                    color: #6c757d; 
                    font-size: 14px;
                    margin-top: 2px;
                }
                .stock-price { 
                    font-size: 16px; 
                    font-weight: 600; 
                    margin-top: 5px;
                }
                .loading { 
                    text-align: center; 
                    padding: 20px; 
                    color: #6c757d;
                }
            </style>
        </head>
        <body>
            <div class="phone">
                <div class="screen">
                    <div class="header">
                        <h1>📈 주식 검색</h1>
                        <p>무료 실시간 주식 데이터</p>
                    </div>
                    
                    <div class="content">
                        <input type="text" id="stock-search" class="search-box" 
                               placeholder="주식 검색 (예: 삼성전자, AAPL, 네이버)" 
                               oninput="searchStocks()">
                        
                        <div id="stock-search-results" class="search-results"></div>
                    </div>
                </div>
            </div>
            
            <script>
                let searchTimeout;
                
                function searchStocks() {
                    const query = document.getElementById('stock-search').value.trim();
                    if (!query) {
                        document.getElementById('stock-search-results').innerHTML = '';
                        return;
                    }
                    
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        document.getElementById('stock-search-results').innerHTML = '<div class="loading">검색 중...</div>';
                        
                        fetch(`/api/search/stocks?q=${encodeURIComponent(query)}`)
                            .then(response => response.json())
                            .then(data => {
                                displaySearchResults(data);
                            })
                            .catch(error => {
                                console.error('검색 오류:', error);
                                document.getElementById('stock-search-results').innerHTML = '<div class="loading">검색 실패</div>';
                            });
                    }, 500);
                }
                
                function displaySearchResults(results) {
                    const container = document.getElementById('stock-search-results');
                    
                    if (!results || results.length === 0) {
                        container.innerHTML = '<div class="loading">검색 결과가 없습니다</div>';
                        return;
                    }
                    
                    container.innerHTML = results.map(stock => {
                        const priceDisplay = stock.price ? 
                            `<div class="stock-price">${formatPrice(stock.price)}</div>` : 
                            '<div class="stock-price">가격 조회 중...</div>';
                        
                        return `
                            <div class="stock-item">
                                <div class="stock-symbol">${stock.symbol}</div>
                                <div class="stock-name">${stock.name || stock.symbol}</div>
                                ${priceDisplay}
                                <div style="font-size: 12px; color: #6c757d; margin-top: 5px;">
                                    출처: ${stock.source || 'unknown'}
                                </div>
                            </div>
                        `;
                    }).join('');
                }
                
                function formatPrice(price) {
                    return new Intl.NumberFormat('ko-KR').format(price);
                }
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_stock_search(self):
        """주식 검색 API"""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            query = query_params.get('q', [''])[0]
            
            if not query:
                self.send_json_response([])
                return
            
            print(f"🔍 주식 검색: {query}")
            
            if SCRAPING_AVAILABLE:
                # 웹 스크래핑으로 검색
                results = self.stock_scraper.search_stocks(query)
                
                # 각 결과에 현재 가격 정보 추가
                enriched_results = []
                for result in results[:3]:  # 최대 3개만 처리 (속도 향상)
                    symbol = result.get('symbol', '')
                    if symbol:
                        print(f"📊 가격 조회: {symbol}")
                        price_info = self.stock_scraper.get_stock_price(symbol)
                        if price_info:
                            enriched_result = {**result, **price_info}
                            enriched_results.append(enriched_result)
                        else:
                            enriched_results.append(result)
                
                self.send_json_response(enriched_results)
            else:
                # 더미 데이터
                dummy_results = self.get_dummy_stock_results(query)
                self.send_json_response(dummy_results)
                
        except Exception as e:
            print(f"❌ 주식 검색 오류: {e}")
            self.send_json_response([])
    
    def handle_trending_stocks(self):
        """인기 주식 API"""
        try:
            if SCRAPING_AVAILABLE:
                trending = self.stock_scraper.get_trending_stocks()
                self.send_json_response(trending)
            else:
                dummy_trending = [
                    {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 175.50},
                    {'symbol': '005930.KS', 'name': '삼성전자', 'price': 71000}
                ]
                self.send_json_response(dummy_trending)
                
        except Exception as e:
            print(f"❌ 인기 주식 조회 오류: {e}")
            self.send_json_response([])
    
    def get_dummy_stock_results(self, query):
        """더미 주식 검색 결과"""
        stock_db = {
            '삼성': [{'symbol': '005930.KS', 'name': '삼성전자', 'price': 71000}],
            'AAPL': [{'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 175.50}],
            '네이버': [{'symbol': '035420.KS', 'name': '네이버', 'price': 185000}]
        }
        
        for key, results in stock_db.items():
            if query.lower() in key.lower():
                return results
        
        return []
    
    def send_json_response(self, data):
        """JSON 응답 전송"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """로그 메시지 (간소화)"""
        pass

if __name__ == "__main__":
    print("📈 Stock Alert 테스트 서버 시작 (웹 스크래핑 기반)")
    print(f"💡 브라우저에서 http://localhost:{PORT}/web_simulator/ 접속하세요")
    print(f"🔍 주식 검색 API: http://localhost:{PORT}/api/search/stocks?q=AAPL")
    
    if SCRAPING_AVAILABLE:
        print("✅ 웹 스크래핑 서비스 활성화 - 실제 데이터 제공")
    else:
        print("⚠️ 웹 스크래핑 서비스 비활성화 - 더미 데이터 제공")
    
    try:
        with socketserver.TCPServer(("", PORT), StockTestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 서버 종료")
    except Exception as e:
        print(f"❌ 서버 오류: {e}") 