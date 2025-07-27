#!/usr/bin/env python3
"""
네이버 주식 서비스 (클라우드 최적화 버전)
- 동적 파싱 + 헤더 로테이션
- 캐싱 전략으로 성능 향상
- IP 차단 방지 최적화
- 클라우드 환경 지원
"""

import asyncio
import requests
import re
import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
from urllib.parse import quote
from functools import lru_cache
from ..config.stock_urls_config import url_config, price_config
from ..config.settings import settings

class NaverStockService:
    """네이버 기반 주식 정보 서비스 (클라우드 최적화 버전)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 캐시 저장소
        self.cache = {}
        self.cache_timeout = timedelta(seconds=settings.CACHE_TIMEOUT)
        
        # 헤더 풀 (로테이션용)
        self.headers_pool = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://finance.naver.com/'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.google.com/'
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': 'https://finance.yahoo.com/'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://finance.naver.com/'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.naver.com/'
            }
        ]
        
        self.logger.info(f"📊 네이버 주식 서비스 초기화 완료 (클라우드 최적화 + 캐싱 + 헤더 로테이션)")

    def _get_random_headers(self) -> Dict[str, str]:
        """랜덤 헤더 반환 (IP 차단 방지)"""
        return random.choice(self.headers_pool).copy()

    def _create_fresh_session(self):
        """새로운 Session 생성 + 랜덤 헤더 적용"""
        session = requests.Session()
        headers = self._get_random_headers()
        session.headers.update(headers)
        return session

    def _add_random_delay(self):
        """랜덤 딜레이 추가 (요청 제한)"""
        delay = random.uniform(settings.MIN_REQUEST_DELAY, settings.MAX_REQUEST_DELAY)
        time.sleep(delay)

    def _get_cache_key(self, query: str, query_type: str = "stock") -> str:
        """캐시 키 생성"""
        return f"{query_type}:{query.lower()}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 검사"""
        if not settings.ENABLE_CACHING:
            return False
        
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key].get('timestamp')
        if not cache_time:
            return False
        
        return datetime.now() - cache_time < self.cache_timeout

    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """캐시에서 데이터 조회"""
        if self._is_cache_valid(cache_key):
            self.logger.info(f"💾 캐시 히트: {cache_key}")
            return self.cache[cache_key]['data']
        return None

    def _save_to_cache(self, cache_key: str, data: List[Dict]):
        """캐시에 데이터 저장"""
        if settings.ENABLE_CACHING:
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            self.logger.debug(f"💾 캐시 저장: {cache_key}")

    async def search_stock(self, query: str) -> List[Dict]:
        """메인 검색 함수 - 한국 우선 → 해외 fallback"""
        try:
            self.logger.info(f"🔍 통합 주식 검색 시작: {query}")
            
            # 요청 간 지연 추가 (403 에러 방지)
            self._add_random_delay()
            
            # 캐시 키 생성
            cache_key = self._get_cache_key(query)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 1단계: 한국 주식 우선 시도
            results = await self._search_from_naver_search(query)
            
            # 한국 주식에서 결과를 찾았으면 반환
            if results:
                self.logger.info(f"✅ 한국 주식 검색 성공: {len(results)}개")
                self._save_to_cache(cache_key, results)
                return results
            
            # 2단계: 해외 주식 시도
            self.logger.info(f"🌍 한국 주식 검색 실패, 해외 주식 시도: {query}")
            world_result = await self._try_world_stock_only(query)
            
            if world_result:
                self.logger.info(f"✅ 해외 주식 검색 성공")
                self._save_to_cache(cache_key, [world_result])
                return [world_result]
            
            # 모든 시도 실패
            self.logger.warning(f"❌ 모든 검색 방법 실패: {query}")
            self._save_to_cache(cache_key, [])
            return []
            
        except Exception as e:
            self.logger.error(f"❌ 통합 검색 오류: {e}")
            return []

    async def _search_from_naver_search(self, query: str) -> List[Dict]:
        """네이버 검색에서 한국/해외 주식 모두 찾기"""
        try:
            self.logger.info(f"🔍 통합 주식 검색 시작: {query}")
            
            # 1. 유저 입력: "삼성전자"
            search_query = f"{query} 주가"  # "삼성전자 주가"
            encoded_query = quote(search_query)
            url = f"{url_config.NAVER_SEARCH_BASE_URL}?query={encoded_query}"
            
            self.logger.info(f"📝 네이버 통합 검색: {search_query}")
            
            # 매번 새로운 Session 사용
            session = self._create_fresh_session()
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            html_content = response.text
            results = []
            
            # 2. 네이버 검색 결과에서 종목코드 동적 추출
            korean_codes = re.findall(r'finance\.naver\.com/item/main\.naver\?code=(\d{6})', html_content)
            if korean_codes:
                unique_code = korean_codes[0]  # "005930" 자동 추출!
                
                # 3. 추출된 종목코드로 실시간 정보 조회
                korean_result = await self._get_korean_stock_by_code(unique_code)
                if korean_result:
                    results.append(korean_result)
                    return results  # 한국 주식 찾으면 바로 반환
            
            # 2. 해외 주식 검색 - 검색 결과 페이지에서 바로 파싱 (NEW!)
            world_result = self._parse_world_stock_from_search_page(html_content, query)
            if world_result:
                results.append(world_result)
            
            return results
                
        except Exception as e:
            self.logger.error(f"❌ 네이버 검색 오류: {e}")
            return []

    def _parse_world_stock_from_search_page(self, html_content: str, query: str) -> Optional[Dict]:
        """네이버 검색 결과 페이지에서 해외 주식 정보 직접 파싱"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 주가 정보가 포함된 패턴들 찾기
            # 예: "엔비디아 $157.75 전일대비 상승 $2.66 (+1.72%)" 같은 패턴
            
            # 해외 주식 가격 파싱 (개선된 방식)
            current_price = None
            change_percent = None
            stock_name = query  # 기본값은 검색어
            
            # 1단계: HTML 구조 기반 구체적인 패턴 (우선순위 높음)
            html_price_patterns = [
                r'<strong>(\d+\.\d+)</strong>',  # 주가 전용 strong 태그
                r'spt_con[^>]*>.*?<strong>(\d+\.\d+)</strong>',  # 주식 정보 컨테이너 내 strong 태그
                r'class="price[^"]*"[^>]*>(\d+\.\d+)',  # price 클래스
            ]
            
            # HTML 패턴으로 먼저 시도
            for pattern in html_price_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        price = float(match)
                        if price_config.WORLD_STOCK_MIN_PRICE <= price <= price_config.WORLD_STOCK_MAX_PRICE:
                            current_price = price
                            self.logger.info(f"✅ HTML 패턴에서 해외 주식 가격 발견: ${current_price:.2f} (패턴: {pattern})")
                            break
                    except (ValueError, TypeError):
                        continue
                if current_price:
                    break
            
            # 2단계: HTML 패턴으로 찾지 못한 경우 컨텍스트 기반 패턴 시도
            if not current_price:
                context_patterns = [
                    r'주가[^0-9]*(\d{1,4}\.\d{1,2})',  # '주가' 키워드 후 숫자
                    r'현재가[^0-9]*(\d{1,4}\.\d{1,2})',  # '현재가' 키워드 후 숫자
                    r'종가[^0-9]*(\d{1,4}\.\d{1,2})',  # '종가' 키워드 후 숫자
                ]
                
                for pattern in context_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        try:
                            price = float(match)
                            if price_config.WORLD_STOCK_MIN_PRICE <= price <= price_config.WORLD_STOCK_MAX_PRICE:
                                current_price = price
                                self.logger.info(f"✅ 컨텍스트 패턴에서 해외 주식 가격 발견: ${current_price:.2f} (패턴: {pattern})")
                                break
                        except (ValueError, TypeError):
                            continue
                    if current_price:
                        break
            
            # 3단계: 마지막 fallback으로 기존 일반 패턴 사용
            if not current_price:
                fallback_patterns = [
                    r'\$(\d{1,4}\.\d{1,2})',
                    r'(\d{1,4}\.\d{1,2})\s*달러',
                    r'(\d{1,4}\.\d{1,2})\s*USD',
                ]
                
                for pattern in fallback_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        try:
                            price = float(match)
                            if price_config.WORLD_STOCK_MIN_PRICE <= price <= price_config.WORLD_STOCK_MAX_PRICE:
                                current_price = price
                                self.logger.info(f"✅ Fallback 패턴에서 해외 주식 가격 발견: ${current_price:.2f} (패턴: {pattern})")
                                break
                        except (ValueError, TypeError):
                            continue
                    if current_price:
                        break
            
            # 변동률 파싱 (개선된 방식)
            if change_percent is None:
                # 1단계: HTML 구조 기반 구체적인 패턴 (우선순위 높음)
                html_change_patterns = [
                    r'<em>\(([+-]?\d+\.\d{1,2})%\)</em>',  # 네이버 HTML 구조의 변동률
                    r'n_ch[^>]*>.*?<em>\(([+-]?\d+\.\d{1,2})%\)</em>',  # 변동 정보 컨테이너 내
                    r'전일대비.*?<em>\(([+-]?\d+\.\d{1,2})%\)</em>',  # 전일대비 컨텍스트
                    r'상승.*?<em>\(([+-]?\d+\.\d{1,2})%\)</em>',  # 상승 컨텍스트
                    r'하락.*?<em>\(([+-]?\d+\.\d{1,2})%\)</em>',  # 하락 컨텍스트
                ]
                
                # HTML 패턴으로 먼저 시도
                for pattern in html_change_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        try:
                            change = float(match)
                            if -20 <= change <= 20:  # 합리적인 일일 변동률 범위
                                change_percent = change
                                self.logger.info(f"✅ HTML 패턴에서 해외 주식 변동률 발견: {change_percent}% (패턴: {pattern})")
                                break
                        except (ValueError, TypeError):
                            continue
                    if change_percent is not None:
                        break
                
                # 2단계: HTML 패턴으로 찾지 못한 경우 컨텍스트 기반 패턴 시도
                if change_percent is None:
                    context_change_patterns = [
                        r'변동률[^0-9]*([+-]?\d+\.\d{1,2})%',  # '변동률' 키워드 후
                        r'등락률[^0-9]*([+-]?\d+\.\d{1,2})%',  # '등락률' 키워드 후
                        r'전일대비[^0-9]*([+-]?\d+\.\d{1,2})%',  # '전일대비' 키워드 후
                    ]
                    
                    for pattern in context_change_patterns:
                        matches = re.findall(pattern, html_content, re.IGNORECASE)
                        for match in matches:
                            try:
                                change = float(match)
                                if -20 <= change <= 20:
                                    change_percent = change
                                    self.logger.info(f"✅ 컨텍스트 패턴에서 해외 주식 변동률 발견: {change_percent}% (패턴: {pattern})")
                                    break
                            except (ValueError, TypeError):
                                continue
                        if change_percent is not None:
                            break
                
                # 3단계: 마지막 fallback으로 일반 패턴 사용
                if change_percent is None:
                    fallback_change_patterns = [
                        r'\(([+-]?\d+\.\d{1,2})%\)',  # 괄호 안의 변동률
                        r'([+-]?\d+\.\d{1,2})%',      # 일반적인 퍼센트
                    ]
                    
                    for pattern in fallback_change_patterns:
                        matches = re.findall(pattern, html_content, re.IGNORECASE)
                        for match in matches:
                            try:
                                change = float(match)
                                if -20 <= change <= 20:
                                    change_percent = change
                                    self.logger.info(f"✅ Fallback 패턴에서 해외 주식 변동률 발견: {change_percent}% (패턴: {pattern})")
                                    break
                            except (ValueError, TypeError):
                                continue
                        if change_percent is not None:
                            break
            
            # 해외 주식 심볼 추출 (기존 로직)
            world_symbols = re.findall(r'worldstock/stock/([A-Z\.]+)', html_content)
            symbol = world_symbols[0].split('.')[0] if world_symbols else query.upper()
            
            if current_price:
                result = {
                    'symbol': symbol,
                    'name': stock_name,
                    'name_kr': stock_name,
                    'market': self._determine_world_market(symbol),
                    'current_price': current_price,
                    'change_percent': change_percent if change_percent is not None else 0.0,
                    'timestamp': None,
                    'source': 'naver_search_direct_parsing'
                }
                
                self.logger.info(f"✅ 네이버 검색 결과에서 해외 주식 파싱 성공: {stock_name} ({symbol}) - ${current_price:.2f} ({change_percent}%)")
                return result
            
            self.logger.warning(f"⚠️ 네이버 검색 결과에서 해외 주식 정보를 찾을 수 없음: {query}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 네이버 검색 결과 파싱 오류: {e}")
            return None

    async def _get_world_stock_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        해외 주식 정보 조회 (동적 파싱)
        
        Args:
            symbol: 해외 주식 심볼 (예: "NVDA", "AAPL")
            
        Returns:
            주식 정보 딕셔너리 또는 None
        """
        try:
            # 네이버 해외 주식 다중 URL 시도 (설정 파일 사용)
            urls_to_try = [
                pattern.format(base_url=url_config.NAVER_WORLD_STOCK_BASE_URL, symbol=symbol)
                for pattern in url_config.WORLD_STOCK_URL_PATTERNS
            ]
            
            soup = None
            for url in urls_to_try:
                try:
                    self.logger.info(f"🌍 해외 주식 조회 시도: {url}")
                    response = self._create_fresh_session().get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        self.logger.info(f"✅ 성공: {url}")
                        break
                    else:
                        self.logger.warning(f"❌ 응답 코드 {response.status_code}: {url}")
                        
                except Exception as e:
                    self.logger.warning(f"❌ 오류 ({url}): {e}")
                    continue
            
            if not soup:
                self.logger.error(f"❌ 모든 해외 주식 URL 시도 실패: {symbol}")
                return None
            
            # 종목명 동적 추출
            stock_name = self._extract_world_stock_name(soup, symbol)
            if not stock_name:
                self.logger.warning(f"❌ 해외 종목명을 찾을 수 없음: {symbol}")
                return None
            
            # 현재가 추출
            current_price = self._extract_world_stock_price_improved(soup)
            if not current_price:
                self.logger.warning(f"❌ 해외 주식 현재가를 찾을 수 없음: {symbol}")
                return None
            
            # 변동률 추출
            change_percent = self._extract_world_stock_change(soup)
            
            # 시장 구분 판단
            market = self._determine_world_market(symbol)
            
            result = {
                'symbol': symbol,
                'name': stock_name,
                'name_kr': stock_name,
                'market': market,
                'current_price': current_price,
                'change_percent': change_percent if change_percent is not None else 0.0,
                'timestamp': None,
                'source': 'naver_world_dynamic_parsing'
            }
            
            self.logger.info(f"✅ 해외 주식 동적 파싱 성공: {stock_name} ({symbol}) - ${current_price:,.2f} ({change_percent}%)")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 해외 주식 조회 실패 ({symbol}): {e}")
            return None

    def _extract_world_stock_name(self, soup: BeautifulSoup, symbol: str) -> Optional[str]:
        """해외 주식 종목명 추출"""
        try:
            # 방법 1: title 태그에서 추출
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # "NVIDIA Corporation (NVDA) : 네이버 금융" 형태에서 종목명 추출
                if '(' in title_text and ')' in title_text:
                    # 괄호 앞의 이름 추출
                    stock_name = title_text.split('(')[0].strip()
                    if stock_name and len(stock_name) < 50:
                        self.logger.info(f"✅ 해외 title에서 종목명 추출: '{stock_name}'")
                        return stock_name
            
            # 방법 2: 종목명 영역에서 추출
            name_selectors = [
                '.h_company h2',
                '.wrap_company h2',
                '.company_info .name',
                '.stock_name',
                '.nm'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name_text = name_elem.get_text(strip=True)
                    if name_text and len(name_text) < 50:
                        self.logger.info(f"✅ 해외 {selector}에서 종목명 추출: '{name_text}'")
                        return name_text
            
            # 방법 3: 백업 - 심볼을 종목명으로 사용
            self.logger.warning(f"⚠️ 해외 종목명 추출 실패, 심볼 사용: {symbol}")
            return symbol
            
        except Exception as e:
            self.logger.error(f"❌ 해외 종목명 추출 오류: {e}")
            return symbol

    def _extract_world_stock_price_improved(self, soup: BeautifulSoup) -> Optional[float]:
        """개선된 해외주식 현재가 추출"""
        try:
            self.logger.info("🔍 해외주식 현재가 추출 시작")
            
            # 방법 1: 특정 선택자들로 가격 찾기
            price_selectors = [
                '.rate_info .num',
                '.rate_info strong',
                '.spt_con strong',
                '.today_price',
                '.no_today',
                '.today',
                'span[class*="price"]',
                'div[class*="price"]',
                'strong[class*="price"]'
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                self.logger.debug(f"선택자 {selector}: {len(elements)}개 요소 발견")
                
                for elem in elements:
                    price_text = elem.get_text(strip=True)
                    self.logger.debug(f"가격 후보 텍스트: '{price_text}'")
                    
                    # 숫자와 소수점만 추출
                    price_clean = re.sub(r'[^\d.]', '', price_text)
                    
                    if price_clean and '.' in price_clean:
                        try:
                            price = float(price_clean)
                            if price_config.WORLD_STOCK_MIN_PRICE <= price <= price_config.WORLD_STOCK_MAX_PRICE:
                                self.logger.info(f"✅ 선택자에서 해외주식 현재가 발견: ${price:,.2f}")
                                return price
                        except ValueError:
                            continue
            
            # 방법 2: 전체 텍스트에서 달러 가격 패턴 찾기
            html_text = soup.get_text()
            self.logger.debug(f"HTML 텍스트 길이: {len(html_text)}")
            
            # 더 정확한 달러 가격 패턴들
            price_patterns = [
                r'\$(\d{1,4}(?:,\d{3})*\.\d{2})',     # $157.75, $1,234.56
                r'\$(\d{1,4}\.\d{2})',                # $157.75
                r'(\d{1,4}(?:,\d{3})*\.\d{2})\s*달러', # 157.75 달러
                r'(\d{1,4}\.\d{2})\s*달러',            # 157.75 달러
                r'(\d{1,4}(?:,\d{3})*\.\d{2})\s*USD', # 157.75 USD
                r'(\d{1,4}\.\d{2})\s*USD'             # 157.75 USD
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, html_text)
                self.logger.debug(f"패턴 '{pattern}': {len(matches)}개 매치")
                
                for match in matches:
                    try:
                        price_str = match.replace(',', '').strip()
                        price = float(price_str)
                        
                        # 합리적인 해외주식 가격 범위
                        if price_config.WORLD_STOCK_MIN_PRICE <= price <= price_config.WORLD_STOCK_MAX_PRICE:
                            self.logger.info(f"✅ 패턴에서 해외주식 현재가 발견: ${price:,.2f}")
                            return price
                    except (ValueError, AttributeError):
                        continue
            
            # 방법 3: 모든 숫자 패턴 중에서 가격 범위에 맞는 것 찾기
            all_numbers = re.findall(r'\d{1,4}\.\d{2}', html_text)
            self.logger.debug(f"모든 소수점 숫자 패턴: {len(all_numbers)}개")
            
            for num_str in all_numbers:
                try:
                    price = float(num_str)
                    if price_config.HIGH_VALUE_STOCK_MIN_PRICE <= price <= price_config.HIGH_VALUE_STOCK_MAX_PRICE:
                        self.logger.info(f"✅ 숫자 패턴에서 해외주식 현재가 발견: ${price:,.2f}")
                        return price
                except ValueError:
                    continue
            
            self.logger.warning("❌ 해외주식 현재가를 찾을 수 없음")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 해외주식 현재가 추출 오류: {e}")
            return None

    def _extract_world_stock_change(self, soup: BeautifulSoup) -> Optional[float]:
        """해외 주식 변동률 추출"""
        try:
            # 해외 주식 변동률 패턴 검색
            html_content = soup.get_text()
            
            # % 패턴 찾기
            percent_patterns = [
                r'([+-]?\d+\.\d+)%',
                r'([+-]?\d+)%'
            ]
            
            for pattern in percent_patterns:
                matches = re.findall(pattern, html_content)
                
                for match in matches:
                    try:
                        value = float(match)
                        # 합리적인 변동률 범위 (-50% ~ +50%)
                        if price_config.MIN_CHANGE_PERCENT <= value <= price_config.MAX_CHANGE_PERCENT:
                            self.logger.info(f"✅ 해외 변동률 추출: {value}%")
                            return value
                    except ValueError:
                        continue
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ 해외 변동률 추출 오류: {e}")
            return 0.0

    def _determine_world_market(self, symbol: str) -> str:
        """해외 주식 시장 구분 판단"""
        try:
            # 일반적인 패턴으로 시장 추정 (정확하지 않을 수 있음)
            if len(symbol) <= 4 and symbol.isalpha():
                return 'NASDAQ'  # 대부분의 미국 주식
            else:
                return 'NYSE'  # 기타
        
        except Exception:
            return 'NASDAQ'  # 기본값

    async def _get_korean_stock_by_code(self, code: str) -> Optional[Dict]:
        """
        종목코드로 한국 주식 정보 조회 (동적 파싱)
        
        Args:
            code: 6자리 종목코드
            
        Returns:
            주식 정보 딕셔너리 또는 None
        """
        try:
            url = f"{url_config.NAVER_FINANCE_BASE_URL}?code={code}"
            self.logger.info(f"📡 네이버 금융 접근: {url}")
            
            response = self._create_fresh_session().get(url, timeout=url_config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 종목명 동적 추출
            stock_name = self._extract_stock_name(soup, code)
            if not stock_name:
                self.logger.warning(f"❌ 종목명을 찾을 수 없음: {code}")
                return None
            
            # 현재가 추출
            current_price = self._extract_current_price(soup)
            if not current_price:
                self.logger.warning(f"❌ 현재가를 찾을 수 없음: {code}")
                return None
            
            # 변동률 추출
            change_percent = self._extract_change_percent(soup)
            
            # 시장 구분 (코스피/코스닥 판단 - 간단한 로직)
            market = self._determine_market(soup, code)
            
            result = {
                'symbol': code,
                'name': stock_name,
                'name_kr': stock_name,
                'market': market,
                'current_price': current_price,
                'change_percent': change_percent if change_percent is not None else 0.0,
                'timestamp': None,
                'source': 'naver_dynamic_parsing'
            }
            
            self.logger.info(f"✅ 동적 파싱 성공: {stock_name} ({code}) - {current_price:,.0f}원 ({change_percent}%)")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 종목코드 조회 실패 ({code}): {e}")
            return None

    def _extract_stock_name(self, soup: BeautifulSoup, code: str) -> Optional[str]:
        """HTML에서 정확한 종목명 추출"""
        try:
            # 방법 1: title 태그에서 추출
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # "삼성전자 : 네이버페이 증권" 형태에서 종목명만 추출
                if ':' in title_text:
                    stock_name = title_text.split(':')[0].strip()
                    if stock_name and len(stock_name) < 20:  # 너무 긴 제목 제외
                        self.logger.info(f"✅ title에서 종목명 추출: '{stock_name}'")
                        return stock_name
            
            # 방법 2: 종목명 영역에서 추출
            name_selectors = [
                '.wrap_company h2',
                '.h_company h2', 
                '.company_info .name',
                '.info_company .name'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name_text = name_elem.get_text(strip=True)
                    if name_text and len(name_text) < 20:
                        self.logger.info(f"✅ {selector}에서 종목명 추출: '{name_text}'")
                        return name_text
            
            # 방법 3: 메타 태그에서 추출 (try-except로 안전하게 처리)
            try:
                meta_title = soup.find('meta', {'property': 'og:title'})
                content = getattr(meta_title, 'attrs', {}).get('content', '') if meta_title else ''
                if content and '-' in content:
                    stock_name = content.split('-')[0].strip()
                    if stock_name and len(stock_name) < 20:
                        self.logger.info(f"✅ meta 태그에서 종목명 추출: '{stock_name}'")
                        return stock_name
            except (AttributeError, TypeError):
                pass
            
            # 방법 4: 백업 - 종목코드를 종목명으로 사용
            self.logger.warning(f"⚠️ 종목명 추출 실패, 종목코드 사용: {code}")
            return code
            
        except Exception as e:
            self.logger.error(f"❌ 종목명 추출 오류: {e}")
            return code

    def _extract_current_price(self, soup: BeautifulSoup) -> Optional[float]:
        """현재가 추출 (기존 로직 유지)"""
        try:
            price_selectors = [
                '.no_today .blind',
                '.today .blind',
                '.no_today',
                '.rate_info .num',
                '.spt_con strong',
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                self.logger.debug(f"가격 선택자 {selector}: {len(elements)}개")
                
                for elem in elements:
                    price_text = elem.get_text(strip=True)
                    
                    try:
                        price_str = price_text.replace('원', '').replace(',', '').strip()
                        
                        if price_str.replace('.', '').isdigit() and len(price_str) >= 3:
                            price = float(price_str)
                            
                            # 합리적인 주식 가격 범위 (100원 ~ 100만원)
                            if 100 <= price <= 1000000:
                                self.logger.info(f"✅ 현재가 추출: {price:,.0f}원")
                                return price
                    except (ValueError, AttributeError):
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 현재가 추출 오류: {e}")
            return None

    def _extract_change_percent(self, soup: BeautifulSoup) -> Optional[float]:
        """변동률 추출 (기존 개선된 로직 유지)"""
        try:
            # .no_exday 영역에서 변동률 추출
            exday_container = soup.select_one('.no_exday')
            if exday_container:
                exday_text = exday_container.get_text(strip=True)
                
                # 상승/하락 판단
                is_rise = '상승' in exday_text
                is_decline = '하락' in exday_text
                
                # blind 요소들에서 변동률 후보 찾기
                blind_elements = exday_container.select('.blind')
                
                for elem in blind_elements:
                    text = elem.get_text(strip=True)
                    
                    # 소수점이 있는 숫자만 변동률 후보로 간주
                    if re.match(r'^\d+\.\d+$', text):
                        try:
                            value = float(text)
                            # 합리적인 변동률 범위
                            if price_config.MIN_CHANGE_PERCENT <= value <= price_config.MAX_CHANGE_PERCENT:
                                change_percent = -value if is_decline else value
                                self.logger.info(f"✅ 변동률 추출: {change_percent}%")
                                return change_percent
                        except ValueError:
                            continue
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ 변동률 추출 오류: {e}")
            return 0.0

    def _determine_market(self, soup: BeautifulSoup, code: str) -> str:
        """시장 구분 판단 (코스피/코스닥)"""
        try:
            # HTML에서 시장 정보 추출 시도
            market_keywords = soup.get_text().lower()
            
            if 'kosdaq' in market_keywords or '코스닥' in market_keywords:
                return 'KOSDAQ'
            elif 'kospi' in market_keywords or '코스피' in market_keywords:
                return 'KOSPI'
            
            # 종목코드 패턴으로 간단 판단 (완벽하지 않음)
            if code.startswith('0'):
                return 'KOSPI'
            else:
                return 'KOSDAQ'
                
        except Exception:
            return 'KOSPI'  # 기본값

    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """환율 정보 조회 (화폐별 정확한 패턴 적용 버전)"""
        try:
            url = f"{url_config.EXCHANGE_RATE_BASE_URL}?query={from_currency}+{to_currency}+환율"
            self.logger.info(f"💱 환율 조회 시도: {from_currency}→{to_currency}")
            
            response = self._create_fresh_session().get(url, timeout=10)
            html_text = response.text
            
            # 화폐별 특정 환율 범위 설정
            currency_ranges = {
                'USD': (1100, 1400),   # USD/KRW: 1100~1400원
                'EUR': (1400, 1700),   # EUR/KRW: 1400~1700원  
                'JPY': (8, 12),        # JPY/KRW: 8~12원 (100엔당)
                'CNY': (160, 200),     # CNY/KRW: 160~200원
                'GBP': (1500, 1800),   # GBP/KRW: 1500~1800원
            }
            
            min_rate, max_rate = currency_ranges.get(from_currency, (500, 2500))
            
            # 정확한 환율 패턴 (화폐별 맞춤)
            if from_currency == 'JPY':
                # 일본 엔화: 100엔당 가격
                rate_patterns = [
                    rf'({from_currency}[/\\s]*{to_currency}[\\s:]*)(\\d+[,.]?\\d*)',
                    rf'(100[\\s]*엔[\\s:]*)(\\d+[,.]?\\d*)',
                    rf'(\\d+[,.]?\\d*)\\s*원\\s*(?:.*?엔|.*?JPY)',
                ]
            else:
                # 기타 화폐 - 더 정확한 패턴 사용 (4자리 우선)
                rate_patterns = [
                    rf'(\\d{{4}}[.,]\\d{{2}})',  # 4자리.2자리 형태 (1599.19) - 우선순위 1
                    rf'<strong>(\\d{{4}}[.,]\\d{{2}})</strong>',  # HTML 태그 내 4자리 - 우선순위 2
                    rf'(\\d{{4}}[,.]?\\d{{2,3}}[,.]?\\d{{0,2}})',  # 4자리 전체 패턴 - 우선순위 3
                    rf'({from_currency}[/\\s]*{to_currency}[\\s:]*)(\\d{{4}}[,.]?\\d{{2,3}})',  # 화폐명+4자리
                    rf'(\\d{{1,4}}[,.]?\\d{{2,3}}[,.]?\\d{{0,2}})\\s*원',  # 일반 패턴 (마지막)
                    rf'<strong>(\\d{{1,4}}[,.]?\\d{{2,3}}[,.]?\\d{{0,2}})</strong>',  # HTML 태그 내
                    rf'(\\d{{1,4}}[,.]?\\d{{2,3}}[,.]?\\d{{0,2}})\\s*KRW',
                ]
            
            # 패턴별로 검색하고 범위 내 값 찾기
            for pattern in rate_patterns:
                matches = re.findall(pattern, html_text)
                for match in matches:
                    try:
                        # 튜플인 경우 마지막 그룹(숫자 부분) 추출, 아니면 match 자체 사용
                        if isinstance(match, tuple) and len(match) > 1:
                            rate_str = match[-1]  # 마지막 그룹이 숫자 부분
                        else:
                            rate_str = match
                            
                        rate_str = rate_str.replace(',', '') if isinstance(rate_str, str) else str(rate_str).replace(',', '')
                        rate = float(rate_str)
                        
                        # 화폐별 범위 체크
                        if min_rate <= rate <= max_rate:
                            self.logger.info(f"✅ {from_currency}→{to_currency} 환율 발견: {rate} (패턴: {pattern[:30]})")
                            return rate
                    except (ValueError, TypeError, IndexError):
                        continue
            
            # 범위 체크 없이 재시도 (더 관대한 검색) - 4자리 우선
            general_patterns = [
                r'(\d{4}[.,]\d{2})',                   # 정확히 4자리.2자리 (1599.19) - 최우선
                r'(\d{4}[,.]?\d{2,3}[,.]?\d{0,2})',   # 4자리 패턴 - 우선순위 2
                r'(\d{3,4}[.,]\d{1,3})',              # 3-4자리.소수 형태 (1599.19 or 599.19)
                r'(\d{1,4}[.,]\d{1,3})',              # 일반적인 소수점 형태 - 마지막
            ]
            
            for pattern in general_patterns:
                matches = re.findall(pattern, html_text)
                for match in matches:
                    try:
                        rate_str = match.replace(',', '') if isinstance(match, str) else str(match).replace(',', '')
                        rate = float(rate_str)
                        
                        # 매우 넓은 범위로 재검증
                        if 500 <= rate <= 2500:
                            self.logger.info(f"✅ {from_currency}→{to_currency} 일반 환율 발견: {rate}")
                            return rate
                    except (ValueError, TypeError):
                        continue
            
            self.logger.warning(f"⚠️ 환율을 찾을 수 없음: {from_currency}→{to_currency}")
            return 1.0
                
        except Exception as e:
            self.logger.error(f"❌ 환율 조회 오류: {e}")
            return 1.0

    async def _try_world_stock_only(self, query: str) -> Optional[Dict]:
        """해외주식 전용 파싱 - 네이버 해외주식 직접 접근"""
        try:
            self.logger.info(f"🌍 해외주식 전용 파싱 시작: {query}")
            
            # 검색어를 그대로 사용 (네이버가 알아서 변환함)
            symbol = query.upper()  # 기본적으로 대문자로만 변환
            
            # 네이버 해외주식 URL들 시도 (설정 파일 사용)
            urls_to_try = [
                pattern.format(base_url=url_config.NAVER_WORLD_STOCK_BASE_URL, symbol=symbol)
                for pattern in url_config.WORLD_STOCK_URL_PATTERNS
            ]
            
            for url in urls_to_try:
                try:
                    self.logger.info(f"🔗 해외주식 URL 시도: {url}")
                    response = self._create_fresh_session().get(url, timeout=10)
                    
                    if response.status_code == 200 and len(response.text) > 1000:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 해외주식 정보 파싱 시도
                        result = self._parse_world_stock_direct(soup, symbol, query)
                        if result:
                            self.logger.info(f"✅ 해외주식 파싱 성공: {url}")
                            return result
                    else:
                        self.logger.warning(f"❌ 응답 실패 ({response.status_code}): {url}")
                        
                except Exception as e:
                    self.logger.warning(f"❌ URL 접근 오류 ({url}): {e}")
                    continue
            
            self.logger.error(f"❌ 모든 해외주식 URL 시도 실패: {query}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 해외주식 파싱 오류: {e}")
            return None

    def _parse_world_stock_direct(self, soup: BeautifulSoup, symbol: str, original_query: str) -> Optional[Dict]:
        """네이버 해외주식 페이지 직접 파싱"""
        try:
            # 종목명 추출
            stock_name = self._extract_world_stock_name_improved(soup, symbol, original_query)
            
            # 현재가 추출
            current_price = self._extract_world_stock_price_improved(soup)
            if not current_price:
                return None
            
            # 변동률 추출
            change_percent = self._extract_world_stock_change_improved(soup)
            
            # 시장 구분 (기본값)
            market = 'NASDAQ'  # 대부분의 해외주식이 나스닥
            
            result = {
                'symbol': symbol,
                'name': stock_name,
                'name_kr': stock_name,
                'market': market,
                'current_price': current_price,
                'change_percent': change_percent if change_percent is not None else 0.0,
                'timestamp': None,
                'source': 'naver_world_direct_parsing'
            }
            
            self.logger.info(f"✅ 해외주식 직접 파싱 성공: {stock_name} ({symbol}) - ${current_price:,.2f} ({change_percent}%)")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 해외주식 직접 파싱 오류: {e}")
            return None

    def _extract_world_stock_name_improved(self, soup: BeautifulSoup, symbol: str, original_query: str) -> str:
        """개선된 해외주식 종목명 추출"""
        try:
            # 방법 1: title 태그에서 추출
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if symbol in title_text:
                    # "NVIDIA Corporation (NVDA)" 형태에서 종목명 추출
                    parts = title_text.split('(')
                    if len(parts) > 0:
                        name = parts[0].strip()
                        if name and len(name) < 50:
                            return name
            
            # 방법 2: 메타 태그에서 추출
            meta_title = soup.find('meta', {'property': 'og:title'})
            content = getattr(meta_title, 'attrs', {}).get('content', '') if meta_title else ''
            if content and symbol in content:
                return content.split('(')[0].strip()
            
            # 방법 3: 원본 검색어를 종목명으로 사용
            
            # 방법 4: 원본 검색어 사용
            return original_query.upper()
            
        except Exception as e:
            self.logger.error(f"❌ 해외 종목명 추출 오류: {e}")
            return original_query.upper()

    def _extract_world_stock_change_improved(self, soup: BeautifulSoup) -> Optional[float]:
        """개선된 해외주식 변동률 추출"""
        try:
            html_text = soup.get_text()
            
            # 변동률 패턴들
            change_patterns = [
                r'([+-]?\d+\.\d+)%',  # +1.72%, -2.34%
                r'([+-]?\d+)%'        # +2%, -3%
            ]
            
            for pattern in change_patterns:
                matches = re.findall(pattern, html_text)
                for match in matches:
                    try:
                        value = float(match)
                        # 합리적인 변동률 범위
                        if price_config.MIN_CHANGE_PERCENT <= value <= price_config.MAX_CHANGE_PERCENT:
                            self.logger.info(f"✅ 해외주식 변동률 발견: {value}%")
                            return value
                    except ValueError:
                        continue
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ 해외주식 변동률 추출 오류: {e}")
            return 0.0

    async def get_stock_price(self, symbol: str) -> Optional[float]:
        """주식의 현재 가격을 조회합니다."""
        try:
            # 주식 정보 검색
            results = await self.search_stock(symbol)
            
            if not results:
                self.logger.warning(f"❌ 주식 정보를 찾을 수 없음: {symbol}")
                return None
            
            # 첫 번째 결과의 현재가 반환
            stock_info = results[0]
            current_price = stock_info.get('current_price')
            
            if current_price is None:
                self.logger.warning(f"❌ 현재가 정보 없음: {symbol}")
                return None
            
            # 숫자만 추출 (원화 표시 제거)
            if isinstance(current_price, str):
                current_price = float(current_price.replace('원', '').replace(',', ''))
            
            return current_price
            
        except Exception as e:
            self.logger.error(f"❌ 주가 조회 오류: {e}")
            return None

# 전역 인스턴스
naver_stock_service = NaverStockService() 