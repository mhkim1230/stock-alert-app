#!/usr/bin/env python3
"""
웹 스크래핑 주식 서비스 테스트
네이버, 구글에서 실제 주식 데이터를 가져와서 테스트
"""

import sys
import os

# 백엔드 모듈 import를 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_web_scraping():
    """웹 스크래핑 서비스 테스트"""
    print("🔍 웹 스크래핑 주식 서비스 테스트 시작")
    
    try:
        from services.web_scraping_service import WebScrapingStockService
        print("✅ 웹 스크래핑 서비스 import 성공")
        
        # 서비스 초기화
        scraper = WebScrapingStockService()
        print("✅ 웹 스크래핑 서비스 초기화 완료")
        
        # 테스트 케이스들
        test_cases = [
            ('AAPL', 'Apple 주식'),
            ('005930.KS', '삼성전자'),
            ('GOOGL', 'Google 주식'),
            ('035420.KS', '네이버'),
            ('TSLA', 'Tesla 주식')
        ]
        
        print("\n📊 주식 가격 조회 테스트:")
        print("-" * 50)
        
        for symbol, description in test_cases:
            print(f"\n🔍 {description} ({symbol}) 조회 중...")
            
            try:
                result = scraper.get_stock_price(symbol)
                
                if result:
                    print(f"✅ 성공!")
                    print(f"   가격: {result.get('price', 'N/A')}")
                    print(f"   변화: {result.get('change', 'N/A')}")
                    print(f"   변화율: {result.get('change_percent', 'N/A')}%")
                    print(f"   출처: {result.get('source', 'N/A')}")
                    print(f"   시간: {result.get('timestamp', 'N/A')}")
                else:
                    print(f"❌ 실패: 데이터 없음")
                    
            except Exception as e:
                print(f"❌ 오류: {e}")
        
        # 검색 테스트
        print("\n🔍 주식 검색 테스트:")
        print("-" * 50)
        
        search_queries = ['삼성', 'Apple', '네이버', 'Tesla']
        
        for query in search_queries:
            print(f"\n🔍 '{query}' 검색 중...")
            
            try:
                results = scraper.search_stocks(query)
                
                if results:
                    print(f"✅ {len(results)}개 결과 발견:")
                    for i, result in enumerate(results[:3], 1):
                        print(f"   {i}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
                else:
                    print(f"❌ 검색 결과 없음")
                    
            except Exception as e:
                print(f"❌ 검색 오류: {e}")
        
        # 인기 주식 테스트
        print("\n📈 인기 주식 조회 테스트:")
        print("-" * 50)
        
        try:
            trending = scraper.get_trending_stocks()
            
            if trending:
                print(f"✅ {len(trending)}개 인기 주식 발견:")
                for i, stock in enumerate(trending[:5], 1):
                    print(f"   {i}. {stock.get('symbol', 'N/A')} - {stock.get('price', 'N/A')} ({stock.get('source', 'N/A')})")
            else:
                print("❌ 인기 주식 데이터 없음")
                
        except Exception as e:
            print(f"❌ 인기 주식 조회 오류: {e}")
        
        # 시장 상태 테스트
        print("\n📊 시장 상태 조회 테스트:")
        print("-" * 50)
        
        try:
            market_status = scraper.get_market_status()
            
            if market_status:
                print("✅ 시장 상태 조회 성공:")
                print(f"   코스피: {market_status.get('kospi', 'N/A')}")
                print(f"   코스닥: {market_status.get('kosdaq', 'N/A')}")
                print(f"   시장 개장: {market_status.get('market_open', 'N/A')}")
                print(f"   출처: {market_status.get('source', 'N/A')}")
            else:
                print("❌ 시장 상태 데이터 없음")
                
        except Exception as e:
            print(f"❌ 시장 상태 조회 오류: {e}")
        
        print("\n🎉 웹 스크래핑 테스트 완료!")
        
    except ImportError as e:
        print(f"❌ import 오류: {e}")
        print("💡 backend/src/services/web_scraping_service.py 파일을 확인하세요")
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    test_web_scraping() 