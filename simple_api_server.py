#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전 무료 주식 API 서버 - 안정성 강화
모든 인코딩 오류 해결 및 Yahoo Finance 완전 제거
"""

import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import time
import random
import re
import sys
import os

# UTF-8 환경 강제 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# Python 버전 호환성을 위한 안전한 인코딩 설정
try:
    # Python 3.7+ reconfigure 방식
    if hasattr(sys.stdout, 'reconfigure') and callable(getattr(sys.stdout, 'reconfigure', None)):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure') and callable(getattr(sys.stderr, 'reconfigure', None)):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    # 대체 방식
    elif hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except (AttributeError, OSError, TypeError, ValueError):
    # 모든 인코딩 설정이 실패해도 계속 진행
    pass

class StableStockAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 검증된 주식 종목 데이터베이스 (완전 무료 데이터)
        self.VALID_STOCKS = {
            # 미국 주식
            'AAPL': {'name': 'Apple Inc.', 'exchange': 'NASDAQ', 'korean_name': '애플', 'base_price': 175.0},
            'GOOGL': {'name': 'Alphabet Inc.', 'exchange': 'NASDAQ', 'korean_name': '구글', 'base_price': 140.0},
            'MSFT': {'name': 'Microsoft Corporation', 'exchange': 'NASDAQ', 'korean_name': '마이크로소프트', 'base_price': 380.0},
            'TSLA': {'name': 'Tesla Inc.', 'exchange': 'NASDAQ', 'korean_name': '테슬라', 'base_price': 250.0},
            'AMZN': {'name': 'Amazon.com Inc.', 'exchange': 'NASDAQ', 'korean_name': '아마존', 'base_price': 155.0},
            'NVDA': {'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ', 'korean_name': '엔비디아', 'base_price': 850.0},
            'META': {'name': 'Meta Platforms Inc.', 'exchange': 'NASDAQ', 'korean_name': '메타', 'base_price': 480.0},
            'NFLX': {'name': 'Netflix Inc.', 'exchange': 'NASDAQ', 'korean_name': '넷플릭스', 'base_price': 450.0},
            'AMD': {'name': 'Advanced Micro Devices', 'exchange': 'NASDAQ', 'korean_name': 'AMD', 'base_price': 140.0},
            'INTC': {'name': 'Intel Corporation', 'exchange': 'NASDAQ', 'korean_name': '인텔', 'base_price': 35.0},
            'CORZ': {'name': 'CoreWeave Inc.', 'exchange': 'NASDAQ', 'korean_name': '코어위브', 'base_price': 25.0},
            
            # 한국 주식
            '005930': {'name': '삼성전자', 'exchange': 'KRX', 'korean_name': '삼성전자', 'base_price': 75000},
            '000660': {'name': 'SK하이닉스', 'exchange': 'KRX', 'korean_name': 'SK하이닉스', 'base_price': 130000},
            '035420': {'name': 'NAVER', 'exchange': 'KRX', 'korean_name': '네이버', 'base_price': 180000},
            '005380': {'name': '현대차', 'exchange': 'KRX', 'korean_name': '현대차', 'base_price': 240000},
            '066570': {'name': 'LG전자', 'exchange': 'KRX', 'korean_name': 'LG전자', 'base_price': 95000},
            '035720': {'name': '카카오', 'exchange': 'KRX', 'korean_name': '카카오', 'base_price': 55000},
            '051910': {'name': 'LG화학', 'exchange': 'KRX', 'korean_name': 'LG화학', 'base_price': 380000},
            '006400': {'name': '삼성SDI', 'exchange': 'KRX', 'korean_name': '삼성SDI', 'base_price': 520000},
            '207940': {'name': '삼성바이오로직스', 'exchange': 'KRX', 'korean_name': '삼성바이오로직스', 'base_price': 750000},
            '068270': {'name': '셀트리온', 'exchange': 'KRX', 'korean_name': '셀트리온', 'base_price': 160000},
        }
        
        # 검색 별칭 (한글 포함)
        self.SEARCH_ALIASES = {
            # 한국 주식
            '삼성전자': '005930', '삼성': '005930', 'samsung': '005930',
            'sk하이닉스': '000660', 'sk': '000660', 'hynix': '000660', '하이닉스': '000660',
            '네이버': '035420', 'naver': '035420',
            '현대차': '005380', '현대자동차': '005380', 'hyundai': '005380',
            'lg전자': '066570', 'lg': '066570', '엘지': '066570', '엘지전자': '066570',
            '카카오': '035720', 'kakao': '035720',
            'lg화학': '051910', '엘지화학': '051910',
            '삼성sdi': '006400', '삼성SDI': '006400',
            '삼성바이오': '207940', '삼성바이오로직스': '207940',
            '셀트리온': '068270', 'celltrion': '068270',
            
            # 미국 주식 (한글 포함)
            'apple': 'AAPL', '애플': 'AAPL',
            'google': 'GOOGL', '구글': 'GOOGL', 'alphabet': 'GOOGL',
            'microsoft': 'MSFT', '마이크로소프트': 'MSFT', '마소': 'MSFT',
            'tesla': 'TSLA', '테슬라': 'TSLA',
            'amazon': 'AMZN', '아마존': 'AMZN',
            'nvidia': 'NVDA', '엔비디아': 'NVDA',
            'meta': 'META', '메타': 'META', 'facebook': 'META', '페이스북': 'META',
            'netflix': 'NFLX', '넷플릭스': 'NFLX',
            'amd': 'AMD', '에이엠디': 'AMD',
            'intel': 'INTC', '인텔': 'INTC',
            'coreweave': 'CORZ', '코어위브': 'CORZ', 'corz': 'CORZ',
        }
        
        # 알림 저장소 (메모리 기반)
        self.stock_alerts = []
        self.currency_alerts = []
        
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """안전한 로그 메시지 출력"""
        try:
            message = format % args
            print(f"{self.address_string()} - - [{self.log_date_time_string()}] {message}")
        except Exception as e:
            print(f"Log error: {e}")
    
    def get_realistic_stock_data(self, symbol):
        """현실적인 주식 데이터 생성 (완전 무료, 안정적)"""
        if symbol not in self.VALID_STOCKS:
            return None
            
        stock_info = self.VALID_STOCKS[symbol]
        base_price = stock_info['base_price']
        
        # 시간 기반 현실적인 변동 시뮬레이션
        current_time = time.time()
        daily_cycle = (current_time % 86400) / 86400  # 0-1 사이의 하루 주기
        weekly_cycle = (current_time % 604800) / 604800  # 0-1 사이의 주간 주기
        
        # 복합적인 변동 요소
        daily_variation = 0.02 * (daily_cycle - 0.5)  # ±1% 일간 변동
        weekly_variation = 0.05 * (weekly_cycle - 0.5)  # ±2.5% 주간 변동
        random_variation = random.uniform(-0.015, 0.015)  # ±1.5% 랜덤 변동
        
        total_variation = daily_variation + weekly_variation + random_variation
        
        # 가격 계산
        current_price = base_price * (1 + total_variation)
        change = current_price - base_price
        change_percent = total_variation * 100
        
        # 거래량 시뮬레이션
        base_volume = 1000000 if stock_info['exchange'] == 'NASDAQ' else 5000000
        volume_variation = random.uniform(0.5, 2.0)  # 50% ~ 200%
        volume = int(base_volume * volume_variation)
        
        return {
            'symbol': symbol,
            'name': stock_info['name'],
            'korean_name': stock_info['korean_name'],
            'current_price': round(current_price, 2 if stock_info['exchange'] == 'NASDAQ' else 0),
            'change': round(change, 2 if stock_info['exchange'] == 'NASDAQ' else 0),
            'change_percent': round(change_percent, 2),
            'volume': volume,
            'currency': 'USD' if stock_info['exchange'] == 'NASDAQ' else 'KRW',
            'exchange': stock_info['exchange'],
            'source': 'stable_simulation',
            'last_updated': int(current_time)
        }

    def do_OPTIONS(self):
        """CORS preflight 요청 처리"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """GET 요청 처리 (완전한 한글 지원)"""
        try:
            # URL 파싱 (인코딩 안전)
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # 쿼리 파라미터 안전 파싱
            query_params = {}
            if parsed_url.query:
                try:
                    query_params = parse_qs(parsed_url.query, keep_blank_values=True)
                    # 단일 값으로 변환
                    for key, value_list in query_params.items():
                        if value_list:
                            query_params[key] = value_list[0]
                        else:
                            query_params[key] = ''
                except Exception as e:
                    print(f"쿼리 파싱 오류: {e}")
                    query_params = {}
            
            # 응답 헤더 설정
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # 라우팅
            if path == '/':
                response = self.get_api_info()
            elif path == '/api/search/stocks':
                query = query_params.get('q', '')
                response = self.search_stocks(query)
            elif path == '/api/stock/price':
                symbol = query_params.get('symbol', '')
                response = self.get_stock_price(symbol)
            elif path == '/api/currency/rate':
                from_currency = query_params.get('from', 'USD')
                to_currency = query_params.get('to', 'KRW')
                response = self.get_currency_rate(from_currency, to_currency)
            elif path == '/api/alerts/stock':
                response = {'alerts': self.stock_alerts, 'count': len(self.stock_alerts)}
            elif path == '/api/alerts/currency':
                response = {'alerts': self.currency_alerts, 'count': len(self.currency_alerts)}
            elif path == '/api/alerts/check':
                response = self.check_alerts()
            else:
                response = {'error': 'Not Found', 'path': path}
            
            # JSON 응답 전송 (UTF-8 안전)
            json_response = json.dumps(response, ensure_ascii=False, indent=2)
            self.wfile.write(json_response.encode('utf-8'))
            
        except Exception as e:
            print(f"GET 요청 처리 오류: {e}")
            self.send_error(500, f"Internal Server Error: {e}")

    def do_POST(self):
        """POST 요청 처리 (알림 추가)"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
            except:
                self.send_error(400, "Invalid JSON")
                return
            
            # 응답 헤더 설정
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            path = urlparse(self.path).path
            
            if path == '/api/alerts/stock':
                response = self.add_stock_alert(data)
            elif path == '/api/alerts/currency':
                response = self.add_currency_alert(data)
            else:
                response = {'error': 'Not Found'}
            
            json_response = json.dumps(response, ensure_ascii=False, indent=2)
            self.wfile.write(json_response.encode('utf-8'))
            
        except Exception as e:
            print(f"POST 요청 처리 오류: {e}")
            self.send_error(500, f"Internal Server Error: {e}")

    def get_api_info(self):
        """API 정보 반환"""
        return {
            'name': '안정적인 주식 API 서버',
            'version': '2.0.0',
            'status': 'running',
            'features': [
                '완전 무료 주식 데이터',
                '한글 검색 완벽 지원',
                '실시간 시뮬레이션',
                '알림 기능',
                '환율 조회'
            ],
            'endpoints': {
                'search': '/api/search/stocks?q=검색어',
                'price': '/api/stock/price?symbol=AAPL',
                'currency': '/api/currency/rate?from=USD&to=KRW',
                'alerts': '/api/alerts/stock'
            },
            'supported_stocks': len(self.VALID_STOCKS),
            'last_updated': int(time.time())
        }

    def search_stocks(self, query):
        """주식 검색 (완전한 한글 지원)"""
        if not query:
            return {'results': [], 'count': 0}
        
        query = query.lower().strip()
        results = []
        
        # 직접 매칭 확인
        if query.upper() in self.VALID_STOCKS:
            stock_data = self.get_realistic_stock_data(query.upper())
            if stock_data:
                results.append(stock_data)
        
        # 별칭 검색
        if query in self.SEARCH_ALIASES:
            symbol = self.SEARCH_ALIASES[query]
            stock_data = self.get_realistic_stock_data(symbol)
            if stock_data and stock_data not in results:
                results.append(stock_data)
        
        # 부분 매칭 검색
        for alias, symbol in self.SEARCH_ALIASES.items():
            if query in alias.lower():
                stock_data = self.get_realistic_stock_data(symbol)
                if stock_data and stock_data not in results:
                    results.append(stock_data)
        
        # 이름으로 검색
        for symbol, info in self.VALID_STOCKS.items():
            if (query in info['name'].lower() or 
                query in info['korean_name'].lower() or
                query in symbol.lower()):
                stock_data = self.get_realistic_stock_data(symbol)
                if stock_data and stock_data not in results:
                    results.append(stock_data)
        
        return {
            'results': results,
            'count': len(results),
            'query': query,
            'search_time': time.time()
        }

    def get_stock_price(self, symbol):
        """개별 주식 가격 조회"""
        if not symbol:
            return {'error': 'Symbol is required'}
        
        stock_data = self.get_realistic_stock_data(symbol.upper())
        if stock_data:
            return stock_data
        else:
            return {'error': f'Stock {symbol} not found'}

    def get_currency_rate(self, from_currency, to_currency):
        """환율 조회 (시뮬레이션)"""
        # 기본 환율 (USD/KRW 기준)
        base_rates = {
            'USD': {'KRW': 1300.0, 'JPY': 150.0, 'EUR': 0.85},
            'KRW': {'USD': 1/1300.0, 'JPY': 150.0/1300.0, 'EUR': 0.85/1300.0},
            'JPY': {'USD': 1/150.0, 'KRW': 1300.0/150.0, 'EUR': 0.85/150.0},
            'EUR': {'USD': 1/0.85, 'KRW': 1300.0/0.85, 'JPY': 150.0/0.85}
        }
        
        if from_currency not in base_rates or to_currency not in base_rates[from_currency]:
            return {'error': f'Currency pair {from_currency}/{to_currency} not supported'}
        
        base_rate = base_rates[from_currency][to_currency]
        # 실시간 변동 시뮬레이션
        variation = random.uniform(-0.02, 0.02)  # ±2% 변동
        current_rate = base_rate * (1 + variation)
        
        return {
            'from': from_currency,
            'to': to_currency,
            'rate': round(current_rate, 4),
            'change_percent': round(variation * 100, 2),
            'last_updated': int(time.time())
        }

    def add_stock_alert(self, data):
        """주식 알림 추가"""
        try:
            alert = {
                'id': len(self.stock_alerts) + 1,
                'symbol': data.get('symbol', '').upper(),
                'target_price': float(data.get('target_price', 0)),
                'condition': data.get('condition', 'above'),  # above, below
                'created_at': int(time.time())
            }
            
            if alert['symbol'] not in self.VALID_STOCKS:
                return {'error': 'Invalid stock symbol'}
            
            if alert['target_price'] <= 0:
                return {'error': 'Target price must be positive'}
            
            self.stock_alerts.append(alert)
            return {'success': True, 'alert': alert}
            
        except Exception as e:
            return {'error': f'Failed to add alert: {e}'}

    def add_currency_alert(self, data):
        """환율 알림 추가"""
        try:
            alert = {
                'id': len(self.currency_alerts) + 1,
                'from_currency': data.get('from_currency', 'USD'),
                'to_currency': data.get('to_currency', 'KRW'),
                'target_rate': float(data.get('target_rate', 0)),
                'condition': data.get('condition', 'above'),
                'created_at': int(time.time())
            }
            
            if alert['target_rate'] <= 0:
                return {'error': 'Target rate must be positive'}
            
            self.currency_alerts.append(alert)
            return {'success': True, 'alert': alert}
            
        except Exception as e:
            return {'error': f'Failed to add alert: {e}'}

    def check_alerts(self):
        """알림 체크"""
        triggered_alerts = []
        
        # 주식 알림 체크
        for alert in self.stock_alerts:
            stock_data = self.get_realistic_stock_data(alert['symbol'])
            if stock_data:
                current_price = stock_data['current_price']
                if ((alert['condition'] == 'above' and current_price >= alert['target_price']) or
                    (alert['condition'] == 'below' and current_price <= alert['target_price'])):
                    triggered_alerts.append({
                        'type': 'stock',
                        'alert': alert,
                        'current_price': current_price,
                        'triggered_at': int(time.time())
                    })
        
        # 환율 알림 체크
        for alert in self.currency_alerts:
            rate_data = self.get_currency_rate(alert['from_currency'], alert['to_currency'])
            if 'rate' in rate_data:
                current_rate = rate_data['rate']
                if ((alert['condition'] == 'above' and current_rate >= alert['target_rate']) or
                    (alert['condition'] == 'below' and current_rate <= alert['target_rate'])):
                    triggered_alerts.append({
                        'type': 'currency',
                        'alert': alert,
                        'current_rate': current_rate,
                        'triggered_at': int(time.time())
                    })
        
        return {
            'triggered_alerts': triggered_alerts,
            'count': len(triggered_alerts),
            'total_stock_alerts': len(self.stock_alerts),
            'total_currency_alerts': len(self.currency_alerts)
        }

def run_server():
    """서버 실행"""
    server_address = ('', 8008)
    
    try:
        httpd = HTTPServer(server_address, StableStockAPIHandler)
        print("🚀 안정적인 주식 API 서버 시작! (완전 무료)")
        print(f"📡 API 서버: http://localhost:8008")
        print(f"🔍 주식 검색: http://localhost:8008/api/search/stocks?q=삼성")
        print(f"💰 주식 가격: http://localhost:8008/api/stock/price?symbol=AAPL")
        print(f"💱 환율 조회: http://localhost:8008/api/currency/rate?from=USD&to=KRW")
        print(f"✅ 지원 종목: 20개 (미국 11개, 한국 9개)")
        print(f"⏹️  서버 종료: Ctrl+C")
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 서버를 종료합니다...")
        httpd.shutdown()
    except Exception as e:
        print(f"❌ 서버 오류: {e}")

if __name__ == "__main__":
    run_server() 