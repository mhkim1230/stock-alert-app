#!/usr/bin/env python3
"""
간단한 웹 스크래핑 테스트
네이버, 구글에서 주식 데이터를 직접 가져와서 테스트
"""

import requests
import re
from bs4 import BeautifulSoup
import time
import urllib.parse

def test_naver_stock_scraping():
    """네이버 금융에서 주식 데이터 스크래핑 테스트"""
    print("🔍 네이버 금융 스크래핑 테스트")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 삼성전자 테스트
    try:
        url = "https://finance.naver.com/item/main.nhn?code=005930"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 현재가 파싱
            price_elem = soup.select_one('.no_today .blind')
            if price_elem:
                price = price_elem.text.replace(',', '')
                print(f"✅ 삼성전자 현재가: {price}원")
            else:
                print("❌ 삼성전자 가격 파싱 실패")
        else:
            print(f"❌ 네이버 접속 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 네이버 스크래핑 오류: {e}")

def test_google_stock_scraping():
    """구글 파이낸스에서 주식 데이터 스크래핑 테스트"""
    print("\n🔍 구글 파이낸스 스크래핑 테스트")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Apple 주식 테스트
    try:
        url = "https://www.google.com/finance/quote/AAPL:NASDAQ"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 가격 파싱 (여러 선택자 시도)
            price_selectors = [
                '.YMlKec.fxKbKc',
                '.YMlKec',
                '[data-last-price]'
            ]
            
            price_found = False
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                    try:
                        price = float(price_text)
                        print(f"✅ Apple 주식 가격: ${price}")
                        price_found = True
                        break
                    except:
                        continue
            
            if not price_found:
                print("❌ Apple 주식 가격 파싱 실패")
                # 디버깅을 위해 HTML 일부 출력
                print("HTML 내용 샘플:")
                print(response.text[:500])
        else:
            print(f"❌ 구글 접속 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 구글 스크래핑 오류: {e}")

def test_yahoo_stock_scraping():
    """야후 파이낸스에서 주식 데이터 스크래핑 테스트"""
    print("\n🔍 야후 파이낸스 스크래핑 테스트")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Tesla 주식 테스트
    try:
        url = "https://finance.yahoo.com/quote/TSLA"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 가격 파싱
            price_selectors = [
                'fin-streamer[data-field="regularMarketPrice"]',
                '[data-field="regularMarketPrice"]',
                '.Fw\\(b\\).Fz\\(36px\\)'
            ]
            
            price_found = False
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.text.strip().replace(',', '')
                    try:
                        price = float(price_text)
                        print(f"✅ Tesla 주식 가격: ${price}")
                        price_found = True
                        break
                    except:
                        continue
            
            if not price_found:
                print("❌ Tesla 주식 가격 파싱 실패")
        else:
            print(f"❌ 야후 접속 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 야후 스크래핑 오류: {e}")

def test_naver_search():
    """네이버 주식 검색 테스트"""
    print("\n🔍 네이버 주식 검색 테스트")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 네이버 주식 검색 API 시도
        url = "https://finance.naver.com/api/search/searchListJson.nhn"
        params = {
            'query': '삼성',
            'target': 'stock',
            'start': 1,
            'count': 5
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'items' in data:
                    print(f"✅ 검색 결과 {len(data['items'])}개 발견:")
                    for item in data['items'][:3]:
                        print(f"   - {item.get('code', 'N/A')}: {item.get('name', 'N/A')}")
                else:
                    print("❌ 검색 결과 형식 오류")
            except:
                print("❌ JSON 파싱 실패")
        else:
            print(f"❌ 네이버 검색 API 접속 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 네이버 검색 오류: {e}")

def main():
    """메인 테스트 함수"""
    print("🚀 웹 스크래핑 주식 데이터 테스트 시작")
    print("=" * 60)
    
    # 각 테스트 실행 (서버 부하 방지를 위해 간격 두기)
    test_naver_stock_scraping()
    time.sleep(2)
    
    test_google_stock_scraping()
    time.sleep(2)
    
    test_yahoo_stock_scraping()
    time.sleep(2)
    
    test_naver_search()
    
    print("\n🎉 모든 테스트 완료!")
    print("\n💡 결과 분석:")
    print("- ✅ 표시된 항목: 성공적으로 데이터 스크래핑")
    print("- ❌ 표시된 항목: 스크래핑 실패 (사이트 구조 변경 또는 차단)")
    print("- 실제 서비스에서는 여러 소스를 조합하여 안정성 확보")

if __name__ == "__main__":
    main() 