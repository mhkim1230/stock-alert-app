import pytest
from datetime import datetime
from src.services.news_service import NewsService

class TestNewsService:
    @pytest.fixture
    def news_service(self):
        """NewsService 인스턴스 생성"""
        return NewsService()

    def test_get_top_headlines(self, news_service):
        """
        Top Headlines 조회 테스트
        - 기본 동작 확인
        - 결과 존재 여부 검증
        """
        headlines = news_service.get_top_headlines(page_size=5)
        
        assert isinstance(headlines, list), "결과는 리스트여야 합니다"
        assert len(headlines) > 0, "최소 1개 이상의 헤드라인 필요"
        
        # 각 뉴스 항목 구조 검증
        for article in headlines:
            assert 'title' in article, "각 기사는 제목을 포함해야 합니다"
            assert 'description' in article, "각 기사는 설명을 포함해야 합니다"
            assert 'url' in article, "각 기사는 URL을 포함해야 합니다"
            assert 'publishedAt' in article, "각 기사는 발행 시간을 포함해야 합니다"
            assert 'source' in article, "각 기사는 출처 정보를 포함해야 합니다"

    def test_get_stock_related_news(self, news_service):
        """
        주식 관련 뉴스 검색 테스트
        - 다양한 주식 심볼로 검색
        - 결과 존재 여부 검증
        """
        test_symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        for symbol in test_symbols:
            stock_news = news_service.get_stock_related_news(symbol, page_size=3)
            
            assert isinstance(stock_news, list), f"{symbol} 뉴스 결과는 리스트여야 합니다"
            
            # 키워드 포함 여부 검증
            for article in stock_news:
                assert (symbol.lower() in article['title'].lower() or 
                        symbol.lower() in article['description'].lower()), \
                    f"검색 결과에 키워드 '{symbol}'가 포함되어야 합니다"

    def test_get_market_news(self, news_service):
        """
        시장 관련 뉴스 검색 테스트
        - 다양한 카테고리로 검색
        - 결과 존재 여부 검증
        """
        test_categories = ['business', 'technology', 'finance']
        
        for category in test_categories:
            market_news = news_service.get_market_news(category=category, page_size=3)
            
            assert isinstance(market_news, list), f"{category} 뉴스 결과는 리스트여야 합니다"
            
            # 키워드 포함 여부 검증
            for article in market_news:
                assert (category.lower() in article['title'].lower() or 
                        category.lower() in article['description'].lower()), \
                    f"검색 결과에 키워드 '{category}'가 포함되어야 합니다"

    def test_search_news(self, news_service):
        """
        키워드 뉴스 검색 테스트
        - 다양한 키워드로 검색
        - 결과 존재 여부 검증
        """
        test_keywords = ['technology', 'finance', 'stock', 'market']
        
        for keyword in test_keywords:
            search_results = news_service.search_news(query=keyword, page_size=3)
            
            assert isinstance(search_results, list), f"{keyword} 검색 결과는 리스트여야 합니다"
            
            # 키워드 포함 여부 검증
            for article in search_results:
                assert (keyword.lower() in article['title'].lower() or 
                        keyword.lower() in article['description'].lower()), \
                    f"검색 결과에 키워드 '{keyword}'가 포함되어야 합니다"

    def test_page_size_limit(self, news_service):
        """
        페이지 크기 제한 테스트
        - 다양한 페이지 크기 검증
        """
        test_sizes = [1, 3, 5, 10]
        
        for size in test_sizes:
            # 다양한 메서드로 테스트
            headlines = news_service.get_top_headlines(page_size=size)
            assert len(headlines) <= size, f"페이지 크기 {size} 제한 위반 (Top Headlines)"
            
            stock_news = news_service.get_stock_related_news('AAPL', page_size=size)
            assert len(stock_news) <= size, f"페이지 크기 {size} 제한 위반 (Stock News)"
            
            market_news = news_service.get_market_news(category='business', page_size=size)
            assert len(market_news) <= size, f"페이지 크기 {size} 제한 위반 (Market News)"

    def test_source_diversity(self, news_service):
        """
        뉴스 소스 다양성 테스트
        - 여러 소스에서 뉴스 가져오기
        """
        headlines = news_service.get_top_headlines(page_size=10)
        
        # 소스 다양성 검증
        sources = set(article['source']['name'] for article in headlines)
        assert len(sources) > 1, "최소 2개 이상의 뉴스 소스 필요"

    def test_error_handling(self, news_service):
        """
        오류 처리 테스트
        - 빈 키워드 검색
        - 특수 문자 포함 키워드
        """
        # 빈 키워드 테스트
        empty_results = news_service.search_news(query='', page_size=1)
        assert isinstance(empty_results, list), "빈 키워드 검색 결과는 리스트여야 합니다"
        
        # 특수 문자 포함 키워드 테스트
        special_results = news_service.search_news(query='!@#$%^', page_size=1)
        assert isinstance(special_results, list), "특수 문자 키워드 검색 결과는 리스트여야 합니다" 