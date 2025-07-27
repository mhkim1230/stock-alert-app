#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.web_scraping_service import WebScrapingStockService

def test_samsung_search():
    """삼성전자 검색 테스트"""
    print("🔍 삼성전자 검색 테스트 시작...")
    
    scraping_service = WebScrapingStockService()
    
    # 1. 삼성전자 직접 검색
    print("\n1. '삼성전자' 검색:")
    result = scraping_service.get_stock_price_naver('005930')
    if result:
        print(f"✅ 성공: {result}")
    else:
        print("❌ 실패")
    
    # 2. 삼성전자 한글 검색
    print("\n2. '삼성전자' 한글 검색:")
    search_results = scraping_service.search_stocks('삼성전자')
    if search_results:
        print(f"✅ 검색 결과: {len(search_results)}개")
        for stock in search_results[:3]:
            print(f"  - {stock}")
    else:
        print("❌ 검색 결과 없음")
    
    # 3. 기타 한국 주식 검색
    print("\n3. 'SK하이닉스' 검색:")
    result = scraping_service.get_stock_price_naver('000660')
    if result:
        print(f"✅ 성공: {result}")
    else:
        print("❌ 실패")
    
    print("\n🏁 테스트 완료!")

if __name__ == "__main__":
    test_samsung_search() 