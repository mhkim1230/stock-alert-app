#!/usr/bin/env python3
"""
네이버 파싱 전용 API 서버
실제 네이버에서 주식/환율 데이터를 파싱해서 제공
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup, Tag
import re
import uvicorn
import json
from urllib.parse import quote

app = FastAPI(title="네이버 금융 파싱 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 네이버 검색 헤더 (실제 브라우저처럼 보이게)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

@app.get("/")
async def root():
    return {"message": "🔥 네이버 금융 실시간 파싱 API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "naver_parsing"}

@app.get("/naver/stocks/search/{query}")
async def search_stocks(query: str):
    """실제 네이버 검색 페이지에서 주식 정보 파싱"""
    print(f"🔍 주식 검색: {query}")
    
    try:
        stocks = []
        
        # 방법 1: 네이버 일반 검색
        search_url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={quote(query)}"
        print(f"📡 일반 검색 URL: {search_url}")
        
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        print(f"📡 일반 검색 응답: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 주식 관련 링크 찾기
            links = soup.find_all('a', href=re.compile(r'finance\.naver\.com'))
            print(f"🔗 발견된 금융 링크 수: {len(links)}")
            
            for link in links[:3]:  # 최대 3개만
                try:
                    href = link.get('href') or ''  # None 대신 빈 문자열 사용
                    if 'item/main.naver' in href:
                        # 종목 정보 추출
                        code_match = re.search(r'code=(\d+)', href)
                        if code_match:
                            symbol = code_match.group(1)
                            name = link.get_text().strip()
                            
                            # 실제 종목 페이지에서 가격 정보 가져오기
                            stock_info = await get_stock_detail(symbol, name)
                            if stock_info:
                                stocks.append(stock_info)
                except Exception as e:
                    print(f"⚠️ 링크 처리 오류: {e}")
                    continue
        
        # 방법 2: 네이버 금융 직접 검색
        if len(stocks) == 0:
            print("🔍 네이버 금융 직접 검색 시도")
            finance_search_url = f"https://finance.naver.com/search/searchList.naver?query={quote(query)}"
            print(f"📡 금융 검색 URL: {finance_search_url}")
            
            try:
                finance_response = requests.get(finance_search_url, headers=HEADERS, timeout=10)
                print(f"📡 금융 검색 응답: {finance_response.status_code}")
                
                if finance_response.status_code == 200:
                    finance_soup = BeautifulSoup(finance_response.text, 'html.parser')
                    
                    # 검색 결과 테이블에서 종목 찾기
                    result_rows = finance_soup.find_all('tr')
                    for row in result_rows[:5]:  # 상위 5개
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            # 종목명과 코드 추출 시도
                            for cell in cells:
                                link = cell.find('a', href=re.compile(r'code=\d+'))
                                if link:
                                    href = link.get('href')
                                    code_match = re.search(r'code=(\d+)', href)
                                    if code_match:
                                        symbol = code_match.group(1)
                                        name = link.get_text().strip()
                                        
                                        print(f"🎯 금융 검색에서 발견: {name} ({symbol})")
                                        
                                        # 중복 체크
                                        if not any(s['symbol'] == symbol for s in stocks):
                                            stock_info = await get_stock_detail(symbol, name)
                                            if stock_info:
                                                stocks.append(stock_info)
                                        break
            except Exception as e:
                print(f"⚠️ 네이버 금융 검색 오류: {e}")
        
        # 방법 3: 해외 주식 검색 (네이버 모바일)
        if len(stocks) == 0:
            print("🔍 해외 주식 검색 시도")
            try:
                # 네이버 모바일 해외 주식 검색
                world_search_url = f"https://m.stock.naver.com/api/search/stock?query={quote(query)}"
                print(f"📡 해외 주식 API URL: {world_search_url}")
                
                world_response = requests.get(world_search_url, headers=HEADERS, timeout=10)
                print(f"📡 해외 주식 API 응답: {world_response.status_code}")
                
                if world_response.status_code == 200:
                    try:
                        world_data = world_response.json()
                        print(f"🔍 해외 주식 API 데이터: {world_data}")
                        
                        # API 응답에서 해외 주식 찾기
                        if 'result' in world_data and 'items' in world_data['result']:
                            for item in world_data['result']['items'][:3]:
                                if item.get('market') in ['NASDAQ', 'NYSE', 'AMEX']:
                                    symbol = item.get('code', '')
                                    name = item.get('name', '')
                                    
                                    if symbol and name:
                                        print(f"🎯 해외 주식 발견: {name} ({symbol})")
                                        
                                        # 해외 주식 상세 정보 가져오기
                                        world_stock = await get_world_stock_detail(symbol, name)
                                        if world_stock:
                                            stocks.append(world_stock)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 해외 주식 JSON 파싱 오류: {e}")
                        
                        # API가 JSON이 아닐 때 HTML 파싱 시도
                        world_soup = BeautifulSoup(world_response.text, 'html.parser')
                        
                        # 검색 결과에서 해외 주식 링크 찾기
                        world_links = world_soup.find_all('a', href=re.compile(r'worldstock/stock/[A-Z\.]+'))
                        print(f"🔗 해외 주식 링크 수: {len(world_links)}")
                        
                        for link in world_links[:3]:
                            if isinstance(link, Tag):  # Tag 객체만 처리
                                try:
                                    href = link.get('href')
                                    symbol_match = re.search(r'worldstock/stock/([A-Z\.]+)', href)
                                    if symbol_match:
                                        symbol = symbol_match.group(1)
                                        name = link.get_text().strip()
                                        
                                        print(f"🎯 해외 주식 링크에서 발견: {name} ({symbol})")
                                        
                                        world_stock = await get_world_stock_detail(symbol, name)
                                        if world_stock:
                                            stocks.append(world_stock)
                                except Exception as e:
                                    print(f"⚠️ 해외 주식 링크 처리 오류: {e}")
                                continue
                                
            except Exception as e:
                print(f"⚠️ 해외 주식 검색 오류: {e}")
        
        # 방법 4: 네이버 주식 전용 검색 (해외 주식 포함)
        if len(stocks) == 0:
            print("🔍 네이버 주식 전용 검색 시도")
            try:
                stock_search_url = f"https://search.naver.com/search.naver?where=stock&query={quote(query)}"
                print(f"📡 주식 전용 검색 URL: {stock_search_url}")
                
                stock_response = requests.get(stock_search_url, headers=HEADERS, timeout=10)
                print(f"📡 주식 전용 검색 응답: {stock_response.status_code}")
                
                if stock_response.status_code == 200:
                    # JavaScript 변수에서 실시간 주식 데이터 추출
                    stock_data = await extract_stock_data_from_js(stock_response.text, query)
                    if stock_data:
                        stocks.append(stock_data)
                        print(f"🎯 주식 전용 검색에서 발견: {stock_data['name']} (${stock_data['current_price']})")
                        
            except Exception as e:
                print(f"⚠️ 주식 전용 검색 오류: {e}")
        
        # 하드코딩 금지 - 실제 검색만 사용
        print("🔍 하드코딩 없이 실제 검색만 사용")
        
        # 하드코딩 매칭 제거 - 실제 검색만 사용
        
        print(f"✅ 최종 검색 완료: {len(stocks)}개 종목 발견")
        return {"results": stocks, "query": query}
        
    except Exception as e:
        print(f"❌ 주식 검색 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"주식 검색 실패: {str(e)}")

async def get_stock_detail(symbol: str, name: str):
    """종목 상세 정보 가져오기 (실제 네이버 파싱)"""
    print(f"🔍 종목 상세 조회: {symbol} ({name})")
    
    try:
        detail_url = f"https://finance.naver.com/item/main.naver?code={symbol}"
        print(f"📡 URL: {detail_url}")
        
        response = requests.get(detail_url, headers=HEADERS, timeout=10)
        print(f"📡 응답 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP 응답 오류: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 디버깅: HTML 샘플 출력 (더 많이)
        print("🔍 HTML 샘플:")
        print(response.text[:2000])
        print("=" * 50)
        
        # 가격 파싱 - 다양한 방법 시도
        current_price = 0
        
        # 방법 1: 모든 숫자가 포함된 요소 찾기
        print("🔍 방법1: 모든 span.blind 요소 확인")
        blind_elements = soup.find_all('span', class_='blind')
        print(f"🔍 총 {len(blind_elements)}개의 blind 요소 발견")
        
        for i, elem in enumerate(blind_elements):
            text = elem.get_text().strip().replace(',', '')
            print(f"🔍 blind[{i}]: '{elem.get_text().strip()}'")
            
            # 숫자인지 확인하고 합리적인 주가 범위인지 체크
            try:
                if text.replace(',', '').replace('.', '').isdigit():
                    price_val = float(text)
                    if 100 <= price_val <= 500000:  # 합리적인 주가 범위
                        print(f"✅ 가격 후보 발견: {price_val} (blind[{i}])")
                        if current_price == 0:  # 첫 번째 합리적인 가격 사용
                            current_price = price_val
            except:
                continue
                
        # 방법 2: 다른 CSS 선택자들 시도
        print("🔍 방법2: 다른 CSS 선택자 시도")
        
        # 일반적인 주가 표시 선택자들
        price_selectors = [
            'span.code',
            'span.num',
            'td.num',
            'span.tah.p11',
            'em.num',
            'strong.num',
            '.today .blind',
            '.no_today .blind'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            print(f"🔍 {selector}: {len(elements)}개 발견")
            for elem in elements:
                text = elem.get_text().strip()
                print(f"  - '{text}'")
                try:
                    clean_text = text.replace(',', '').replace('원', '')
                    if clean_text.replace('.', '').isdigit():
                        price_val = float(clean_text)
                        if 100 <= price_val <= 500000 and current_price == 0:
                            current_price = price_val
                            print(f"✅ 가격 발견 ({selector}): {price_val}")
                except:
                    continue
        
        # 방법 3: 테이블에서 찾기
        print("🔍 방법3: 테이블 데이터 확인")
        tables = soup.find_all('table')
        print(f"🔍 {len(tables)}개 테이블 발견")
        
        for table_idx, table in enumerate(tables):
            if hasattr(table, 'find_all'):  # find_all 메서드가 있는지 확인
                try:
                    rows = table.find_all('tr')
                    for row_idx, row in enumerate(rows):
                        if hasattr(row, 'find_all'):  # find_all 메서드가 있는지 확인
                            try:
                                cells = row.find_all(['td', 'th'])
                                for cell_idx, cell in enumerate(cells):
                                    text = cell.get_text().strip()
                                    if ',' in text and text.replace(',', '').replace('원', '').isdigit():
                                        try:
                                            price_val = float(text.replace(',', '').replace('원', ''))
                                            if 100 <= price_val <= 500000:
                                                print(f"🔍 테이블[{table_idx}][{row_idx}][{cell_idx}]: {text} -> {price_val}")
                                                if current_price == 0:
                                                    current_price = price_val
                                            break
                                        except:
                                            continue
                            except:
                                continue
                except:
                    continue
        
        print(f"🔍 최종 파싱된 가격: {current_price}")
        
        # 변동률 파싱
        change_percent = 0
        
        print("🔍 변동률 파싱 시도")
        
        # 방법 1: % 포함된 텍스트 찾기
        percent_texts = soup.find_all(string=re.compile(r'\d+\.\d+%'))
        print(f"🔍 % 텍스트 {len(percent_texts)}개 발견:")
        for text in percent_texts:
            print(f"  - '{text.strip()}'")
            try:
                percent_match = re.search(r'(\d+\.\d+)%', text)
                if percent_match:
                    change_percent = float(percent_match.group(1))
                    print(f"✅ 변동률 발견: {change_percent}%")
                    break
            except:
                continue
        
        # 결과 리턴
        result = {
            'symbol': symbol,
            'name': name,
            'name_kr': name,
            'current_price': current_price,
            'change_percent': change_percent,
            'market': 'KOSPI',
            'source': 'naver_real_parsing'
        }
        
        print(f"✅ 최종 결과: {result}")
        return result
        
    except Exception as e:
        print(f"❌ 종목 상세 조회 오류: {str(e)}")
        return None

@app.get("/naver/currency/rate/{from_currency}/{to_currency}")
async def get_currency_rate(from_currency: str, to_currency: str):
    """네이버에서 환율 정보 파싱"""
    print(f"💱 환율 조회: {from_currency}/{to_currency}")
    
    try:
        # 네이버 환율 페이지 URL
        currency_url = f"https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_{from_currency}{to_currency}"
        print(f"📡 환율 URL: {currency_url}")
        
        response = requests.get(currency_url, headers=HEADERS, timeout=10)
        print(f"📡 환율 응답: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 환율 HTTP 오류: {response.status_code}")
            return {"error": f"환율 조회 실패: {response.status_code}"}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 디버깅: HTML 샘플 출력
        print("🔍 환율 HTML 샘플:")
        print(response.text[:1500])
        print("=" * 50)
        
        # 환율 파싱 - 다양한 방법 시도
        rate = 0
        
        # 방법 1: span.blind에서 찾기
        blind_elements = soup.find_all('span', class_='blind')
        print(f"🔍 환율 span.blind 요소 {len(blind_elements)}개:")
        for i, elem in enumerate(blind_elements):
            text = elem.get_text().strip()
            print(f"  [{i}] '{text}'")
            try:
                # 숫자와 점만 있는 형태 (환율 형태)
                if re.match(r'^\d{1,4}\.\d+$', text.replace(',', '')):
                    rate_val = float(text.replace(',', ''))
                    if 1000 <= rate_val <= 2000:  # USD/KRW 합리적 범위
                        print(f"✅ 환율 발견: {rate_val}")
                        rate = rate_val
                        break
            except:
                continue
        
        # 방법 2: 테이블에서 찾기
        if rate == 0:
            print("🔍 환율 테이블 방법:")
            tables = soup.find_all('table')
            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')
                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    for cell_idx, cell in enumerate(cells):
                        text = cell.get_text().strip()
                        # 환율 형태 숫자 찾기
                        if re.match(r'^\d{1,4}\.\d+$', text.replace(',', '')):
                            try:
                                rate_val = float(text.replace(',', ''))
                                if 1000 <= rate_val <= 2000:
                                    print(f"🔍 환율 테이블[{table_idx}][{row_idx}][{cell_idx}]: {text} -> {rate_val}")
                                    rate = rate_val
                                    break
                            except:
                                continue
        
        print(f"✅ 최종 환율: {from_currency}/{to_currency} = {rate}")
        
        if rate > 0:
            return {
                "pair": f"{from_currency}/{to_currency}",
                "rate": rate,
                "source": "naver_real_parsing"
            }
        else:
            return {"error": "환율 파싱 실패"}
            
    except Exception as e:
        print(f"❌ 환율 조회 오류: {str(e)}")
        return {"error": f"환율 조회 실패: {str(e)}"}

@app.get("/naver/worldstock/{symbol}")
async def get_world_stock_direct(symbol: str):
    """해외 주식 직접 조회 (테스트용)"""
    print(f"🌍 해외 주식 직접 조회: {symbol}")
    
    try:
        result = await get_world_stock_detail(symbol, symbol)
        if result:
            return {"result": result}
        else:
            return {"error": f"해외 주식 {symbol} 조회 실패"}
    except Exception as e:
        print(f"❌ 해외 주식 직접 조회 오류: {str(e)}")
        return {"error": f"해외 주식 조회 실패: {str(e)}"}

async def get_world_stock_detail(symbol: str, name: str):
    """해외 주식 상세 정보 가져오기 (네이버 모바일)"""
    print(f"🌍 해외 주식 상세 조회: {symbol} ({name})")
    
    try:
        # 사용자 제공 정확한 URL 패턴들을 순서대로 시도
        urls_to_try = [
            f"https://m.stock.naver.com/worldstock/stock/{symbol}.O/total",  # NASDAQ (엔비디아용)
            f"https://m.stock.naver.com/worldstock/stock/{symbol}.N/total",  # NYSE  
            f"https://m.stock.naver.com/worldstock/stock/{symbol}/total",    # 접미사 없음 (기존 방식)
            f"https://m.stock.naver.com/worldstock/stock/{symbol}.Q/total",  # NASDAQ Global Select
        ]
        
        soup = None
        successful_url = None
        
        for attempt, detail_url in enumerate(urls_to_try, 1):
            print(f"📡 해외 주식 URL 시도 {attempt}/{len(urls_to_try)}: {detail_url}")
            
            response = requests.get(detail_url, headers=HEADERS, timeout=10)
            print(f"📡 해외 주식 응답 {attempt}: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ 성공한 URL: {detail_url}")
                temp_soup = BeautifulSoup(response.text, 'html.parser')
                
                # 실제 주식 데이터가 있는지 확인
                if _validate_world_stock_page(temp_soup):
                    print(f"✅ 유효한 해외주식 페이지 발견!")
                    soup = temp_soup
                    successful_url = detail_url
                    break
                else:
                    print(f"⚠️ 페이지는 열렸지만 주식 데이터 없음")
                    continue
            else:
                print(f"❌ 해외 주식 HTTP 오류 {attempt}: {response.status_code}")
                continue
        else:
            # 모든 URL 시도 실패
            print(f"❌ 모든 해외 주식 URL 시도 실패: {symbol}")
            return None
        
        # 실제 주식 데이터 파싱
        current_price = 0
        change_percent = 0
        
        # 가격 파싱
        print("🔍 해외 주식 가격 파싱 시작")
        
        # 방법 1: 가격 CSS 선택자들
        price_selectors = [
            'span.price', 'span.num', '.price_area .num', '.today_price', 
            '.current_price', 'em.num', 'strong.num', '[class*="price"]'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                try:
                    clean_text = re.sub(r'[^\d.,]', '', text)
                    if clean_text and '.' in clean_text:
                        price_val = float(clean_text.replace(',', ''))
                        if 0.01 <= price_val <= 10000:
                            print(f"✅ 해외 가격 발견 ({selector}): ${price_val}")
                            if current_price == 0:
                                current_price = price_val
                except:
                    continue
        
        # 방법 2: 텍스트에서 달러 가격 찾기
        if current_price == 0:
            dollar_texts = soup.find_all(string=re.compile(r'\$\d+\.\d+'))
            for text in dollar_texts:
                try:
                    price_match = re.search(r'\$(\d+\.\d+)', text)
                    if price_match:
                        price_val = float(price_match.group(1))
                        if 0.01 <= price_val <= 10000:
                            print(f"✅ 달러 텍스트에서 가격 발견: ${price_val}")
                            current_price = price_val
                            break
                except:
                    continue
        
        # 변동률 파싱
        percent_texts = soup.find_all(string=re.compile(r'[+-]?\d+\.\d+%'))
        for text in percent_texts:
            try:
                percent_match = re.search(r'([+-]?\d+\.\d+)%', text)
                if percent_match:
                    change_percent = float(percent_match.group(1))
                    print(f"✅ 해외 변동률 발견: {change_percent}%")
                    break
            except:
                continue
        
        # 결과 반환
        if current_price > 0:
            result = {
                'symbol': symbol,
                'name': name,
                'name_kr': name,
                'current_price': current_price,
                'change_percent': change_percent,
                'market': 'NASDAQ' if '.O' in successful_url else 'NYSE',
                'source': 'naver_world_parsing_fixed',
                'url_used': successful_url
            }
            
            print(f"✅ 해외 주식 최종 결과: {result}")
            return result
        else:
            print(f"❌ 해외 주식 가격 파싱 실패")
            return None
            
    except Exception as e:
        print(f"❌ 해외 주식 상세 조회 오류: {str(e)}")
        return None

def _validate_world_stock_page(soup: BeautifulSoup) -> bool:
    """해외주식 페이지가 유효한 데이터를 포함하는지 확인"""
    try:
        # 가격 정보가 있는지 확인
        price_indicators = [
            soup.find('span', class_='price'),
            soup.find('span', class_='num'),
            soup.select('.price_area .num'),
            soup.find_all(string=re.compile(r'\$\d+\.\d+')),
            soup.find_all(string=re.compile(r'\d+\.\d+'))
        ]
        
        for indicator in price_indicators:
            if indicator:
                return True
        
        # 404 페이지나 오류 페이지 체크
        error_texts = ['404', 'not found', '페이지를 찾을 수 없습니다', 'error']
        page_text = soup.get_text().lower()
        
        for error_text in error_texts:
            if error_text in page_text:
                return False
        
        return True
        
    except Exception as e:
        print(f"⚠️ 페이지 검증 오류: {e}")
        return False

async def extract_stock_data_from_js(html_content: str, query: str):
    """JavaScript 변수에서 실시간 주식 데이터 추출"""
    print(f"🔍 JavaScript에서 주식 데이터 추출: {query}")
    
    try:
        # 1. 현재 가격 데이터 찾기
        current_price = 0
        
        # closePrice 패턴 찾기 (가장 최신 가격)
        close_price_matches = re.findall(r'"closePrice":\s*([0-9.]+)', html_content)
        if close_price_matches:
            try:
                current_price = float(close_price_matches[-1])  # 마지막(최신) 가격 사용
                print(f"✅ closePrice에서 발견: ${current_price}")
            except:
                pass
        
        # currentPrice 패턴 찾기 (실시간 가격)
        if current_price == 0:
            current_price_matches = re.findall(r'"currentPrice":\s*([0-9.]+)', html_content)
            if current_price_matches:
                try:
                    current_price = float(current_price_matches[-1])  # 마지막(최신) 가격 사용
                    print(f"✅ currentPrice에서 발견: ${current_price}")
                except:
                    pass
        
        # 2. 주식명과 심볼 찾기
        stock_name = query
        stock_symbol = query
        
        # 메타 태그에서 주식명 찾기
        meta_title_match = re.search(r'<meta property="og:title" content="([^"]*)', html_content)
        if meta_title_match:
            title = meta_title_match.group(1)
            if ' - 네이버페이 증권' in title:
                stock_name = title.replace(' - 네이버페이 증권', '').strip()
                print(f"✅ 메타 태그에서 주식명 발견: {stock_name}")
        
        # JavaScript 변수에서 심볼 찾기
        symbol_matches = re.findall(r'"stockExchangeType"\s*:\s*"([^"]+)"', html_content)
        market = 'NASDAQ'
        if symbol_matches:
            market = symbol_matches[0]
            print(f"✅ 거래소 정보 발견: {market}")
        
        # 3. 변동률 계산 (가능하면)
        change_percent = 0
        
        # 가격 배열에서 전일 대비 계산
        price_matches = re.findall(r'"closePrice":\s*([0-9.]+)', html_content)
        if len(price_matches) >= 2:
            try:
                current = float(price_matches[-1])
                previous = float(price_matches[-2])
                if previous > 0:
                    change_percent = ((current - previous) / previous) * 100
                    print(f"✅ 변동률 계산: {change_percent:.2f}%")
            except:
                pass
        
        # 4. 결과 반환
        if current_price > 0:
            result = {
                'symbol': stock_symbol,
                'name': stock_name,
                'name_kr': stock_name,
                'current_price': current_price,
                'change_percent': change_percent,
                'market': market,
                'source': 'naver_stock_search_js'
            }
            
            print(f"✅ JavaScript 파싱 최종 결과: {result}")
            return result
        else:
            print(f"❌ JavaScript에서 가격 데이터 파싱 실패")
            return None
            
    except Exception as e:
        print(f"❌ JavaScript 파싱 오류: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 네이버 실시간 파싱 서버 시작...")
    print("📈 주식 검색: http://localhost:8001/naver/stocks/search/삼성전자")
    print("💱 환율 조회: http://localhost:8001/naver/currency/rate/USD/KRW")
    uvicorn.run(app, host="0.0.0.0", port=8001) 