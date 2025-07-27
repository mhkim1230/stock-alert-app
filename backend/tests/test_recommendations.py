import sys
import os
import pytest
from fastapi.testclient import TestClient

# 프로젝트 루트 경로를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.main import app

client = TestClient(app)

def test_get_stock_recommendations():
    """주식 추천 API 테스트"""
    response = client.get("/recommendations/stocks")
    assert response.status_code == 200
    
    recommendations = response.json()
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    
    # 각 추천 주식의 필수 필드 검증
    for stock in recommendations:
        assert "symbol" in stock
        assert "name" in stock
        assert "sector" in stock
        assert "recommendation" in stock
        assert "target_price" in stock

def test_get_stock_recommendations_by_sector():
    """특정 섹터의 주식 추천 테스트"""
    response = client.get("/recommendations/stocks?sector=Technology")
    assert response.status_code == 200
    
    recommendations = response.json()
    assert isinstance(recommendations, list)
    
    # 모든 추천 주식이 Technology 섹터인지 확인
    for stock in recommendations:
        assert stock['sector'].lower() == 'technology'

def test_get_market_sentiment():
    """시장 센티먼트 API 테스트"""
    response = client.get("/recommendations/market-sentiment")
    assert response.status_code == 200
    
    sentiment = response.json()
    
    # 필수 키 검증
    assert "overall_sentiment" in sentiment
    assert "sp500_trend" in sentiment
    assert "nasdaq_trend" in sentiment
    assert "dow_trend" in sentiment
    
    # 유효한 센티먼트 값인지 확인
    valid_sentiments = ["Bullish", "Bearish", "Neutral"]
    valid_trends = ["Bullish", "Bearish", "Stable"]
    
    assert sentiment["overall_sentiment"] in valid_sentiments
    assert sentiment["sp500_trend"] in valid_trends
    assert sentiment["nasdaq_trend"] in valid_trends
    assert sentiment["dow_trend"] in valid_trends 