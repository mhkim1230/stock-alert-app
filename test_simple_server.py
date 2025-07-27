#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 서버 - 기본 기능 확인용
"""

import json
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class TestAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.stocks = {
            'AAPL': {'name': 'Apple Inc.', 'korean_name': '애플', 'base_price': 175.0},
            'GOOGL': {'name': 'Alphabet Inc.', 'korean_name': '구글', 'base_price': 140.0},
            'MSFT': {'name': 'Microsoft Corporation', 'korean_name': '마이크로소프트', 'base_price': 380.0},
            '005930': {'name': '삼성전자', 'korean_name': '삼성전자', 'base_price': 75000},
            '000660': {'name': 'SK하이닉스', 'korean_name': 'SK하이닉스', 'base_price': 130000},
            '035420': {'name': 'NAVER', 'korean_name': '네이버', 'base_price': 180000},
        }
        
        self.aliases = {
            'apple': 'AAPL', '애플': 'AAPL',
            'google': 'GOOGL', '구글': 'GOOGL',
            'microsoft': 'MSFT', '마이크로소프트': 'MSFT',
            '삼성전자': '005930', '삼성': '005930', 'samsung': '005930',
            'sk하이닉스': '000660', 'sk': '000660',
            '네이버': '035420', 'naver': '035420',
        }
        
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # 쿼리 파라미터를 단일 값으로 변환
            for key, value_list in query_params.items():
                if value_list:
                    query_params[key] = value_list[0]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if path == '/':
                response = {'status': 'OK', 'message': '테스트 API 서버 정상 작동'}
            elif path == '/api/search/stocks':
                query = query_params.get('q', '')
                response = self.search_stocks(query)
            elif path == '/api/stock/price':
                symbol = query_params.get('symbol', '')
                response = self.get_stock_price(symbol)
            else:
                response = {'error': 'Not Found'}
            
            json_response = json.dumps(response, ensure_ascii=False, indent=2)
            self.wfile.write(json_response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def search_stocks(self, query):
        if not query:
            return {'results': [], 'count': 0}
        
        query = query.lower().strip()
        results = []
        
        # 직접 매칭
        if query.upper() in self.stocks:
            results.append(self.get_stock_data(query.upper()))
        
        # 별칭 검색
        if query in self.aliases:
            symbol = self.aliases[query]
            stock_data = self.get_stock_data(symbol)
            if stock_data not in results:
                results.append(stock_data)
        
        # 부분 매칭
        for alias, symbol in self.aliases.items():
            if query in alias:
                stock_data = self.get_stock_data(symbol)
                if stock_data not in results:
                    results.append(stock_data)
        
        return {'results': results, 'count': len(results), 'query': query}
    
    def get_stock_price(self, symbol):
        if not symbol:
            return {'error': 'Symbol required'}
        
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return {'error': f'Stock {symbol} not found'}
        
        return self.get_stock_data(symbol)
    
    def get_stock_data(self, symbol):
        if symbol not in self.stocks:
            return None
        
        stock = self.stocks[symbol]
        base_price = stock['base_price']
        
        # 간단한 변동 시뮬레이션
        variation = random.uniform(-0.03, 0.03)  # ±3%
        current_price = base_price * (1 + variation)
        change = current_price - base_price
        change_percent = variation * 100
        
        return {
            'symbol': symbol,
            'name': stock['name'],
            'korean_name': stock['korean_name'],
            'current_price': round(current_price, 2 if symbol.isalpha() else 0),
            'change': round(change, 2 if symbol.isalpha() else 0),
            'change_percent': round(change_percent, 2),
            'currency': 'USD' if symbol.isalpha() else 'KRW',
            'last_updated': int(time.time())
        }

def run_test_server():
    server_address = ('', 8009)
    
    try:
        httpd = HTTPServer(server_address, TestAPIHandler)
        print("🧪 테스트 API 서버 시작!")
        print("📡 서버: http://localhost:8009")
        print("🔍 검색 테스트: http://localhost:8009/api/search/stocks?q=삼성")
        print("💰 가격 테스트: http://localhost:8009/api/stock/price?symbol=AAPL")
        print("⏹️  서버 종료: Ctrl+C")
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 테스트 서버를 종료합니다...")
        httpd.shutdown()
    except Exception as e:
        print(f"❌ 테스트 서버 오류: {e}")

if __name__ == "__main__":
    run_test_server() 