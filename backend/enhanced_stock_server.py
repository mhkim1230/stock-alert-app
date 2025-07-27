#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import http.server
import socketserver
import urllib.parse
import urllib.request
from datetime import datetime
import re

class StockSearchHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 한국 주식 데이터베이스 (실제 종목코드 포함)
        self.korean_stocks = {
            '005930': {'name': '삼성전자', 'name_en': 'Samsung Electronics'},
            '000660': {'name': 'SK하이닉스', 'name_en': 'SK Hynix'},
            '035420': {'name': 'NAVER', 'name_en': 'NAVER'},
            '051910': {'name': 'LG화학', 'name_en': 'LG Chem'},
            '006400': {'name': '삼성SDI', 'name_en': 'Samsung SDI'},
            '035720': {'name': '카카오', 'name_en': 'Kakao'},
            '068270': {'name': '셀트리온', 'name_en': 'Celltrion'},
            '207940': {'name': '삼성바이오로직스', 'name_en': 'Samsung Biologics'},
            '373220': {'name': 'LG에너지솔루션', 'name_en': 'LG Energy Solution'},
            '005380': {'name': '현대차', 'name_en': 'Hyundai Motor'},
            '000270': {'name': '기아', 'name_en': 'Kia'},
            '012330': {'name': '현대모비스', 'name_en': 'Hyundai Mobis'},
            '066570': {'name': 'LG전자', 'name_en': 'LG Electronics'},
            '003550': {'name': 'LG', 'name_en': 'LG Corp'},
            '096770': {'name': 'SK이노베이션', 'name_en': 'SK Innovation'},
            '017670': {'name': 'SK텔레콤', 'name_en': 'SK Telecom'},
            '030200': {'name': 'KT', 'name_en': 'KT'},
            '055550': {'name': '신한지주', 'name_en': 'Shinhan Financial Group'},
            '105560': {'name': 'KB금융', 'name_en': 'KB Financial Group'},
            '086790': {'name': '하나금융지주', 'name_en': 'Hana Financial Group'},
            '028260': {'name': '삼성물산', 'name_en': 'Samsung C&T'},
            '009150': {'name': '삼성전기', 'name_en': 'Samsung Electro-Mechanics'},
            '018260': {'name': '삼성에스디에스', 'name_en': 'Samsung SDS'},
            '032830': {'name': '삼성생명', 'name_en': 'Samsung Life Insurance'},
            '000810': {'name': '삼성화재', 'name_en': 'Samsung Fire & Marine Insurance'},
            '036570': {'name': '엔씨소프트', 'name_en': 'NCSOFT'},
            '251270': {'name': '넷마블', 'name_en': 'Netmarble'},
            '112040': {'name': '위메이드', 'name_en': 'Wemade'},
            '259960': {'name': '크래프톤', 'name_en': 'KRAFTON'},
            '377300': {'name': '카카오페이', 'name_en': 'Kakao Pay'},
            '323410': {'name': '카카오뱅크', 'name_en': 'Kakao Bank'},
        }
        
        # 미국 주식 데이터베이스
        self.us_stocks = {
            'AAPL': {'name': 'Apple Inc.', 'name_ko': '애플'},
            'GOOGL': {'name': 'Alphabet Inc.', 'name_ko': '구글'},
            'MSFT': {'name': 'Microsoft Corporation', 'name_ko': '마이크로소프트'},
            'TSLA': {'name': 'Tesla Inc.', 'name_ko': '테슬라'},
            'AMZN': {'name': 'Amazon.com Inc.', 'name_ko': '아마존'},
            'NVDA': {'name': 'NVIDIA Corporation', 'name_ko': '엔비디아'},
            'META': {'name': 'Meta Platforms Inc.', 'name_ko': '메타'},
            'NFLX': {'name': 'Netflix Inc.', 'name_ko': '넷플릭스'},
            'BABA': {'name': 'Alibaba Group Holding Limited', 'name_ko': '알리바바'},
            'V': {'name': 'Visa Inc.', 'name_ko': '비자'},
            'JPM': {'name': 'JPMorgan Chase & Co.', 'name_ko': 'JP모건'},
            'JNJ': {'name': 'Johnson & Johnson', 'name_ko': '존슨앤존슨'},
            'WMT': {'name': 'Walmart Inc.', 'name_ko': '월마트'},
            'PG': {'name': 'Procter & Gamble Company', 'name_ko': 'P&G'},
            'UNH': {'name': 'UnitedHealth Group Incorporated', 'name_ko': '유나이티드헬스'},
            'HD': {'name': 'Home Depot Inc.', 'name_ko': '홈디포'},
            'MA': {'name': 'Mastercard Incorporated', 'name_ko': '마스터카드'},
            'BAC': {'name': 'Bank of America Corporation', 'name_ko': '뱅크오브아메리카'},
            'DIS': {'name': 'Walt Disney Company', 'name_ko': '디즈니'},
            'ADBE': {'name': 'Adobe Inc.', 'name_ko': '어도비'},
        }
        super().__init__(*args, **kwargs)
    
    def get_stock_price_yahoo(self, symbol):
        """Yahoo Finance에서 실시간 주가 조회"""
        try:
            # 한국 주식인 경우 .KS 추가
            if symbol.isdigit() and len(symbol) == 6:
                yahoo_symbol = f'{symbol}.KS'
            else:
                yahoo_symbol = symbol
            
            # Yahoo Finance API 호출
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                if data['chart']['result'] and data['chart']['result'][0]:
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    
                    current_price = meta.get('regularMarketPrice', 0)
                    previous_close = meta.get('previousClose', 0)
                    change = current_price - previous_close if previous_close else 0
                    change_percent = (change / previous_close * 100) if previous_close else 0
                    
                    return {
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'currency': meta.get('currency', 'USD'),
                        'market_state': meta.get('marketState', 'REGULAR')
                    }
        except Exception as e:
            print(f'가격 조회 실패 ({symbol}): {e}')
        
        return None
    
    def search_stocks(self, query):
        """주식 검색 (자동완성 지원)"""
        results = []
        query_lower = query.lower()
        
        # 한국 주식 검색
        for code, info in self.korean_stocks.items():
            name = info['name']
            name_en = info['name_en']
            
            # 종목코드, 한글명, 영문명으로 검색
            if (query in code or 
                query_lower in name.lower() or 
                query_lower in name_en.lower()):
                
                # 실시간 가격 조회
                price_info = self.get_stock_price_yahoo(code)
                
                stock_data = {
                    'symbol': f'{code}.KS',
                    'code': code,
                    'name': name,
                    'name_en': name_en,
                    'market': 'KRX',
                    'type': 'korean'
                }
                
                if price_info:
                    stock_data.update(price_info)
                    stock_data['price_display'] = f"{price_info['price']:,}원"
                    if price_info['change'] >= 0:
                        stock_data['change_display'] = f"+{price_info['change']:,}원 (+{price_info['change_percent']:.2f}%)"
                        stock_data['change_class'] = 'positive'
                    else:
                        stock_data['change_display'] = f"{price_info['change']:,}원 ({price_info['change_percent']:.2f}%)"
                        stock_data['change_class'] = 'negative'
                else:
                    stock_data['price_display'] = '조회 중...'
                    stock_data['change_display'] = ''
                
                results.append(stock_data)
        
        # 미국 주식 검색
        for symbol, info in self.us_stocks.items():
            name = info['name']
            name_ko = info.get('name_ko', '')
            
            # 심볼, 영문명, 한글명으로 검색
            if (query_lower in symbol.lower() or 
                query_lower in name.lower() or 
                query_lower in name_ko.lower()):
                
                # 실시간 가격 조회
                price_info = self.get_stock_price_yahoo(symbol)
                
                stock_data = {
                    'symbol': symbol,
                    'name': name,
                    'name_ko': name_ko,
                    'market': 'NASDAQ/NYSE',
                    'type': 'us'
                }
                
                if price_info:
                    stock_data.update(price_info)
                    stock_data['price_display'] = f"${price_info['price']:.2f}"
                    if price_info['change'] >= 0:
                        stock_data['change_display'] = f"+${price_info['change']:.2f} (+{price_info['change_percent']:.2f}%)"
                        stock_data['change_class'] = 'positive'
                    else:
                        stock_data['change_display'] = f"${price_info['change']:.2f} ({price_info['change_percent']:.2f}%)"
                        stock_data['change_class'] = 'negative'
                else:
                    stock_data['price_display'] = 'Loading...'
                    stock_data['change_display'] = ''
                
                results.append(stock_data)
        
        # 검색 결과를 관련도순으로 정렬
        def relevance_score(item):
            score = 0
            if query_lower == item.get('symbol', '').lower():
                score += 100
            elif query_lower == item.get('code', '').lower():
                score += 90
            elif query_lower in item.get('name', '').lower():
                score += 50
            elif query_lower in item.get('name_ko', '').lower():
                score += 40
            elif query_lower in item.get('name_en', '').lower():
                score += 30
            return score
        
        results.sort(key=relevance_score, reverse=True)
        return results[:10]  # 상위 10개만 반환
    
    def do_GET(self):
        if self.path.startswith('/api/search/stocks'):
            # URL에서 쿼리 파라미터 추출
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            search_query = query_params.get('q', [''])[0]
            
            # 주식 검색 실행
            results = self.search_stocks(search_query) if search_query else []
            
            # JSON 응답
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps(results, ensure_ascii=False, indent=2)
            self.wfile.write(response.encode('utf-8'))
            
        elif self.path.startswith('/api/currency'):
            # 환율 더미 데이터 (기존과 동일)
            rates = {
                'USD/KRW': {'rate': 1300.50, 'change': '+0.8%'},
                'EUR/KRW': {'rate': 1420.30, 'change': '+1.2%'},
                'JPY/KRW': {'rate': 9.80, 'change': '-0.5%'},
                'CNY/KRW': {'rate': 180.20, 'change': '+0.3%'}
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps(rates, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'API endpoint not found')

if __name__ == '__main__':
    PORT = 8009
    print(f'🚀 향상된 주식 검색 API 서버 시작 - 포트 {PORT}')
    print(f'📊 주식 검색 (자동완성): http://localhost:{PORT}/api/search/stocks?q=삼성')
    print(f'📊 미국 주식 검색: http://localhost:{PORT}/api/search/stocks?q=AAPL')
    print(f'💱 환율 조회: http://localhost:{PORT}/api/currency')
    print(f'')
    print(f'✨ 새로운 기능:')
    print(f'   - 실시간 주가 조회 (Yahoo Finance)')
    print(f'   - 한글/영문 자동완성 검색')
    print(f'   - 한국/미국 주식 통합 검색')
    print(f'   - 가격 변동률 표시')

    with socketserver.TCPServer(('', PORT), StockSearchHandler) as httpd:
        httpd.serve_forever()
