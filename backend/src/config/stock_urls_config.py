"""
주식 관련 URL 설정
하드코딩 제거를 위한 설정 파일
"""
import os

class StockUrlConfig:
    """주식 API URL 설정"""
    
    # 네이버 관련 URL
    NAVER_SEARCH_BASE_URL = os.getenv(
        'NAVER_SEARCH_BASE_URL', 
        'https://search.naver.com/search.naver'
    )
    
    NAVER_FINANCE_BASE_URL = os.getenv(
        'NAVER_FINANCE_BASE_URL',
        'https://finance.naver.com/item/main.naver'
    )
    
    NAVER_WORLD_STOCK_BASE_URL = os.getenv(
        'NAVER_WORLD_STOCK_BASE_URL',
        'https://m.stock.naver.com/worldstock/stock'
    )
    
    # 환율 API URL
    EXCHANGE_RATE_BASE_URL = os.getenv(
        'EXCHANGE_RATE_BASE_URL',
        'https://search.naver.com/search.naver'
    )
    
    # 요청 타임아웃
    REQUEST_TIMEOUT = int(os.getenv('STOCK_REQUEST_TIMEOUT', 10))
    
    # 해외주식 URL 패턴
    WORLD_STOCK_URL_PATTERNS = [
        '{base_url}/{symbol}.O/total',  # NASDAQ
        '{base_url}/{symbol}.N/total',  # NYSE  
        '{base_url}/{symbol}/total'     # 접미사 없음
    ]

class StockPriceConfig:
    """주식 가격 관련 설정"""
    
    # 해외주식 가격 범위 (USD)
    WORLD_STOCK_MIN_PRICE = float(os.getenv('WORLD_STOCK_MIN_PRICE', 1.0))
    WORLD_STOCK_MAX_PRICE = float(os.getenv('WORLD_STOCK_MAX_PRICE', 10000.0))
    
    # 엔비디아 같은 고가 주식의 일반적 범위
    HIGH_VALUE_STOCK_MIN_PRICE = float(os.getenv('HIGH_VALUE_STOCK_MIN_PRICE', 50.0))
    HIGH_VALUE_STOCK_MAX_PRICE = float(os.getenv('HIGH_VALUE_STOCK_MAX_PRICE', 1000.0))
    
    # 변동률 범위 (%)
    MIN_CHANGE_PERCENT = float(os.getenv('MIN_CHANGE_PERCENT', -50.0))
    MAX_CHANGE_PERCENT = float(os.getenv('MAX_CHANGE_PERCENT', 50.0))
    
    # 한국주식 가격 범위 (KRW)
    KOREAN_STOCK_MIN_PRICE = float(os.getenv('KOREAN_STOCK_MIN_PRICE', 100.0))
    KOREAN_STOCK_MAX_PRICE = float(os.getenv('KOREAN_STOCK_MAX_PRICE', 1000000.0))

# 전역 설정 인스턴스들
url_config = StockUrlConfig()
price_config = StockPriceConfig() 