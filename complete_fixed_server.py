#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
import time
import random
import math
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 완전 안전한 UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

class CompleteStockAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 주식 데이터
        self.STOCKS = {
            'AAPL': {'name': 'Apple Inc.', 'name_kr': '애플', 'price': 175.0, 'market': 'NASDAQ'},
            'GOOGL': {'name': 'Alphabet Inc.', 'name_kr': '구글', 'price': 140.0, 'market': 'NASDAQ'},
            'MSFT': {'name': 'Microsoft Corporation', 'name_kr': '마이크로소프트', 'price': 380.0, 'market': 'NASDAQ'},
            '005930': {'name': 'Samsung Electronics', 'name_kr': '삼성전자', 'price': 75000, 'market': 'KOSPI'},
            '000660': {'name': 'SK Hynix', 'name_kr': 'SK하이닉스', 'price': 130000, 'market': 'KOSPI'},
            '035420': {'name': 'NAVER Corporation', 'name_kr': '네이버', 'price': 180000, 'market': 'KOSPI'},
        }
        
        # 검색 별칭
        self.SEARCH_MAP = {
            '삼성': '005930', '삼성전자': '005930', 'samsung': '005930',
            'sk': '000660', 'sk하이닉스': '000660', '하이닉스': '000660',
            '네이버': '035420', 'naver': '035420',
            '애플': 'AAPL', 'apple': 'AAPL',
            '구글': 'GOOGL', 'google': 'GOOGL',
            '마이크로소프트': 'MSFT', 'microsoft': 'MSFT',
        }
        
        # 환율 데이터
        self.CURRENCIES = {
            'USD': {'name_kr': '미국 달러', 'rate': 1.0},
            'KRW': {'name_kr': '한국 원', 'rate': 1300.0},
            'JPY': {'name_kr': '일본 엔', 'rate': 110.0},
            'EUR': {'name_kr': '유로', 'rate': 0.85},
        }
        
        # 알림 저장소
        self.stock_alerts = []
        self.currency_alerts = []
        
        super().__init__(*args, **kwargs)
    
    def log_message(self, format_str, *args):
        try:
            print(f"[LOG] {format_str % args}")
        except:
            print("[LOG] Error")
    
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
            
            query_params = {}
            if parsed_url.query:
                try:
                    raw_params = parse_qs(parsed_url.query)
                    for key, values in raw_params.items():
                        query_params[key] = values[0] if values else ''
                except:
                    pass
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if path == '/':
                self.handle_root()
            elif path == '/api/search/stocks':
                self.handle_search_stocks(query_params)
            elif path == '/api/stock/price':
                self.handle_stock_price(query_params)
            elif path == '/api/currency/rate':
                self.handle_currency_rate(query_params)
            elif path == '/api/alerts/stock':
                self.handle_get_stock_alerts()
            elif path == '/api/alerts/currency':
                self.handle_get_currency_alerts()
            elif path == '/api/alerts/check':
                self.handle_check_alerts()
            else:
                self.send_json({'error': '경로를 찾을 수 없습니다'}, 404)
                
        except Exception as e:
            self.send_json({'error': f'서버 오류: {str(e)}'}, 500)
    
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
            except:
                self.send_json({'error': '잘못된 JSON 데이터'}, 400)
                return
            
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path == '/api/alerts/stock':
                self.handle_create_stock_alert(data)
            elif path == '/api/alerts/currency':
                self.handle_create_currency_alert(data)
            else:
                self.send_json({'error': '경로를 찾을 수 없습니다'}, 404)
                
        except Exception as e:
            self.send_json({'error': f'서버 오류: {str(e)}'}, 500)
    
    def handle_root(self):
        info = {
            'service': '완전 수정된 주식 API 서버',
            'version': '1.0.0',
            'supported_stocks': list(self.STOCKS.keys()),
            'timestamp': datetime.now().isoformat()
        }
        self.send_json(info)
    
    def handle_search_stocks(self, params):
        query = params.get('q', '').strip()
        
        if not query:
            self.send_json([])
            return
        
        results = []
        query_lower = query.lower()
        matched_symbols = set()
        
        # 별칭으로 검색
        for alias, symbol in self.SEARCH_MAP.items():
            if query_lower in alias.lower():
                matched_symbols.add(symbol)
        
        # 직접 검색
        for symbol, data in self.STOCKS.items():
            if (query_lower in symbol.lower() or 
                query_lower in data['name'].lower() or 
                query_lower in data['name_kr'].lower()):
                matched_symbols.add(symbol)
        
        # 결과 생성
        for symbol in matched_symbols:
            if symbol in self.STOCKS:
                stock = self.STOCKS[symbol]
                price_data = self.get_simulated_price(stock['price'])
                
                results.append({
                    'symbol': symbol,
                    'name': stock['name'],
                    'name_kr': stock['name_kr'],
                    'current_price': price_data['price'],
                    'change_percent': price_data['change_percent'],
                    'market': stock['market'],
                    'timestamp': datetime.now().isoformat()
                })
        
        self.send_json(results[:10])
    
    def handle_stock_price(self, params):
        symbol = params.get('symbol', '').upper()
        
        if symbol not in self.STOCKS:
            self.send_json({'error': '주식을 찾을 수 없습니다'}, 404)
            return
        
        stock = self.STOCKS[symbol]
        price_data = self.get_simulated_price(stock['price'])
        
        result = {
            'symbol': symbol,
            'name': stock['name'],
            'name_kr': stock['name_kr'],
            'current_price': price_data['price'],
            'change_percent': price_data['change_percent'],
            'high': price_data['price'] * 1.05,
            'low': price_data['price'] * 0.95,
            'volume': random.randint(1000000, 10000000),
            'market': stock['market'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_json(result)
    
    def handle_currency_rate(self, params):
        from_curr = params.get('from', 'USD').upper()
        to_curr = params.get('to', 'KRW').upper()
        
        if from_curr not in self.CURRENCIES or to_curr not in self.CURRENCIES:
            self.send_json({'error': '지원하지 않는 통화입니다'}, 400)
            return
        
        from_rate = self.CURRENCIES[from_curr]['rate']
        to_rate = self.CURRENCIES[to_curr]['rate']
        
        base_rate = to_rate / from_rate
        current_rate = base_rate * (1 + random.uniform(-0.02, 0.02))
        
        result = {
            'from': from_curr,
            'to': to_curr,
            'rate': round(current_rate, 4),
            'from_name': self.CURRENCIES[from_curr]['name_kr'],
            'to_name': self.CURRENCIES[to_curr]['name_kr'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_json(result)
    
    def handle_create_stock_alert(self, data):
        required = ['symbol', 'target_price', 'condition']
        
        for field in required:
            if field not in data:
                self.send_json({'error': f'필수 필드 누락: {field}'}, 400)
                return
        
        symbol = data['symbol'].upper()
        if symbol not in self.STOCKS:
            self.send_json({'error': '지원하지 않는 주식입니다'}, 400)
            return
        
        alert = {
            'id': len(self.stock_alerts) + 1,
            'symbol': symbol,
            'target_price': float(data['target_price']),
            'condition': data['condition'],
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        self.stock_alerts.append(alert)
        self.send_json({'message': '알림이 생성되었습니다', 'alert': alert})
    
    def handle_create_currency_alert(self, data):
        required = ['from_currency', 'to_currency', 'target_rate', 'condition']
        
        for field in required:
            if field not in data:
                self.send_json({'error': f'필수 필드 누락: {field}'}, 400)
                return
        
        alert = {
            'id': len(self.currency_alerts) + 1,
            'from_currency': data['from_currency'].upper(),
            'to_currency': data['to_currency'].upper(),
            'target_rate': float(data['target_rate']),
            'condition': data['condition'],
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        self.currency_alerts.append(alert)
        self.send_json({'message': '환율 알림이 생성되었습니다', 'alert': alert})
    
    def handle_get_stock_alerts(self):
        active_alerts = [alert for alert in self.stock_alerts if alert['active']]
        self.send_json(active_alerts)
    
    def handle_get_currency_alerts(self):
        active_alerts = [alert for alert in self.currency_alerts if alert['active']]
        self.send_json(active_alerts)
    
    def handle_check_alerts(self):
        triggered = []
        
        # 주식 알림 확인
        for alert in self.stock_alerts:
            if not alert['active']:
                continue
            
            symbol = alert['symbol']
            if symbol in self.STOCKS:
                current_price = self.get_simulated_price(self.STOCKS[symbol]['price'])['price']
                
                should_trigger = False
                if alert['condition'] == 'above' and current_price > alert['target_price']:
                    should_trigger = True
                elif alert['condition'] == 'below' and current_price < alert['target_price']:
                    should_trigger = True
                
                if should_trigger:
                    triggered.append({
                        'type': 'stock',
                        'alert': alert,
                        'current_price': current_price,
                        'message': f"{symbol} 주식이 {alert['target_price']}을 {alert['condition']}했습니다"
                    })
        
        result = {
            'triggered_count': len(triggered),
            'triggered_alerts': triggered,
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_json(result)
    
    def get_simulated_price(self, base_price):
        now = datetime.now()
        
        time_factor = math.sin(now.hour * 0.1 + now.minute * 0.01) * 0.02
        random_factor = random.uniform(-0.05, 0.05)
        
        total_variation = time_factor + random_factor
        current_price = base_price * (1 + total_variation)
        change_percent = total_variation * 100
        
        return {
            'price': round(current_price, 2 if base_price < 1000 else 0),
            'change_percent': round(change_percent, 2)
        }
    
    def send_json(self, data, status_code=200):
        try:
            if status_code != 200:
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            error_data = json.dumps({'error': '응답 처리 오류'}, ensure_ascii=False)
            self.wfile.write(error_data.encode('utf-8'))

def run_server():
    PORT = 8010
    server_address = ('', PORT)
    
    try:
        httpd = HTTPServer(server_address, CompleteStockAPIHandler)
        
        print("🚀 완전 수정된 주식 API 서버 시작!")
        print(f"📡 API 서버: http://localhost:{PORT}")
        print(f"🔍 주식 검색: http://localhost:{PORT}/api/search/stocks?q=삼성")
        print(f"💰 주식 가격: http://localhost:{PORT}/api/stock/price?symbol=AAPL")
        print(f"💱 환율 조회: http://localhost:{PORT}/api/currency/rate?from=USD&to=KRW")
        print(f"📊 알림 확인: http://localhost:{PORT}/api/alerts/check")
        print(f"🌐 웹 시뮬레이터: http://localhost:8007")
        print(f"✅ 모든 인코딩 오류 해결됨")
        print(f"⏹️  서버 종료: Ctrl+C")
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n✅ 서버를 정상 종료합니다...")
        httpd.server_close()
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")

if __name__ == "__main__":
    run_server()
