#!/usr/bin/env python3
"""CRWV 구글 검색 파싱 테스트 스크립트"""

import urllib.request
import urllib.parse
import re
import json

def test_google_search_crwv():
    """CRWV 구글 검색 테스트"""
    symbol = "CRWV"
    search_query = f"{symbol} stock price"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        print(f"🔍 구글에서 '{search_query}' 검색 중...")
        request = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        print(f"✅ HTML 다운로드 완료 ({len(html)} 바이트)")
        
        # 구글 주식 가격 패턴 찾기
        price_patterns = [
            r'data-last-price="([0-9,]+\.?[0-9]*)"',  # 구글 주식 위젯
            r'<span[^>]*class="[^"]*IsqQVc[^"]*"[^>]*>([0-9,]+\.?[0-9]*)</span>',  # 구글 검색 결과
            r'<span[^>]*>(\$?[0-9,]+\.?[0-9]*)</span>.*?USD',  # USD 가격
            r'([0-9,]+\.[0-9]{2})\s*USD',  # 숫자.숫자 USD 패턴
        ]
        
        for i, pattern in enumerate(price_patterns):
            matches = re.findall(pattern, html)
            print(f"패턴 {i+1}: {len(matches)}개 매치 - {matches[:5]}")  # 처음 5개만 출력
            
            if matches:
                for match in matches:
                    price_str = match.replace(',', '').replace('$', '')
                    try:
                        price = float(price_str)
                        if 1 <= price <= 10000:  # 합리적인 주가 범위
                            print(f"🎯 가격 발견: ${price}")
                            return price
                    except ValueError:
                        continue
        
        # HTML에서 모든 숫자 패턴 찾기
        all_numbers = re.findall(r'\b([0-9]{1,4}\.[0-9]{2})\b', html)
        print(f"🔢 전체 숫자 패턴: {len(all_numbers)}개 - {all_numbers[:10]}")
        
        for num_str in all_numbers:
            try:
                price = float(num_str)
                if 50 <= price <= 1000:  # CRWV 예상 가격 범위
                    print(f"🎯 추정 가격: ${price}")
                    return price
            except ValueError:
                continue
                
        print("❌ 가격을 찾을 수 없습니다")
        
        # HTML 일부 출력 (디버깅용)
        print("\n📄 HTML 샘플:")
        print(html[:1000] + "..." if len(html) > 1000 else html)
        
        return None
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None

def test_fallback_database():
    """백업 데이터베이스 테스트"""
    FALLBACK_STOCKS = [
        {"symbol": "CRWV", "name": "CoreWeave Inc. (코어위브)", "name_kr": "코어위브", "currency": "USD"},
        {"symbol": "COREWEAVE", "name": "CoreWeave Inc. (코어위브)", "name_kr": "코어위브", "currency": "USD"},
    ]
    
    test_queries = ["CRWV", "crwv", "코어위브", "CoreWeave", "coreweave"]
    
    for query in test_queries:
        print(f"\n🔍 '{query}' 검색 테스트:")
        query_lower = query.lower()
        found = []
        
        for stock in FALLBACK_STOCKS:
            if (query_lower in stock['symbol'].lower() or 
                query_lower in stock['name'].lower() or 
                query_lower in stock['name_kr'].lower()):
                found.append(stock)
        
        print(f"  결과: {len(found)}개 - {found}")

if __name__ == "__main__":
    print("🧪 CRWV 테스트 시작\n")
    
    print("1️⃣ 백업 데이터베이스 테스트")
    test_fallback_database()
    
    print("\n2️⃣ 구글 검색 파싱 테스트")
    price = test_google_search_crwv()
    
    if price:
        print(f"\n✅ 성공! CRWV 현재 가격: ${price}")
    else:
        print(f"\n❌ 실패! CRWV 가격을 찾을 수 없습니다") 