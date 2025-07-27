import sys
import os
import pytest
from fastapi.testclient import TestClient

# 프로젝트 루트 경로를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.main import app

client = TestClient(app)

def test_user_registration():
    """사용자 등록 테스트"""
    # 새로운 사용자 등록
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "strongpassword123"
    }
    
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 200
    
    registered_user = response.json()
    assert "id" in registered_user
    assert registered_user["username"] == user_data["username"]
    assert registered_user["email"] == user_data["email"]

def test_duplicate_user_registration():
    """중복 사용자 등록 방지 테스트"""
    # 이미 등록된 이메일로 사용자 등록 시도
    user_data = {
        "username": "duplicateuser",
        "email": "testuser@example.com",  # 이전 테스트에서 사용된 이메일
        "password": "anotherpassword123"
    }
    
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 400
    assert "이미 등록된 이메일입니다." in response.json()["detail"]

def test_user_login():
    """사용자 로그인 테스트"""
    # 로그인 시도
    login_data = {
        "username": "testuser@example.com",
        "password": "strongpassword123"
    }
    
    response = client.post("/users/login", data=login_data)
    assert response.status_code == 200
    
    login_response = response.json()
    assert "access_token" in login_response
    assert login_response["token_type"] == "bearer"

def test_watchlist_management():
    """관심 종목 추가 및 제거 테스트"""
    # 먼저 로그인하여 토큰 획득
    login_data = {
        "username": "testuser@example.com",
        "password": "strongpassword123"
    }
    
    login_response = client.post("/users/login", data=login_data)
    access_token = login_response.json()["access_token"]
    
    # 주식 관심 종목 추가
    add_stock_response = client.post(
        "/users/watchlist/stocks", 
        params={"stock_symbol": "AAPL"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert add_stock_response.status_code == 200
    assert "AAPL 주식이 관심 종목에 추가되었습니다." in add_stock_response.json()["message"]
    
    # 주식 관심 종목 제거
    remove_stock_response = client.delete(
        "/users/watchlist/stocks", 
        params={"stock_symbol": "AAPL"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert remove_stock_response.status_code == 200
    assert "AAPL 주식이 관심 종목에서 제거되었습니다." in remove_stock_response.json()["message"] 