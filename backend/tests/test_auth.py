import sys
import os
import pytest
import uuid
from datetime import timedelta, datetime

# 프로젝트 루트 경로를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.services.auth_service import AuthService
from src.models.database import User, initialize_database

def test_password_hashing():
    """비밀번호 해싱 및 검증 테스트"""
    password = "test_password_123"
    
    # 비밀번호 해싱
    hashed_password = AuthService.hash_password(password)
    
    # 해시된 비밀번호 검증
    assert AuthService.verify_password(password, hashed_password) is True
    
    # 잘못된 비밀번호 검증
    assert AuthService.verify_password("wrong_password", hashed_password) is False

def test_jwt_token_creation():
    """JWT 토큰 생성 및 검증 테스트"""
    # 테스트용 사용자 데이터
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    
    # 토큰 생성
    tokens = AuthService.create_user_token(user_id, email)
    
    # 토큰 존재 여부 확인
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    
    # 액세스 토큰 검증
    access_payload = AuthService.validate_token(tokens["access_token"])
    assert access_payload is not None
    assert access_payload.get("sub") == user_id
    assert access_payload.get("email") == email
    
    # 리프레시 토큰 검증
    refresh_payload = AuthService.validate_token(tokens["refresh_token"])
    assert refresh_payload is not None
    assert refresh_payload.get("sub") == user_id
    assert refresh_payload.get("type") == "refresh"

def test_token_expiration():
    """토큰 만료 테스트"""
    # 매우 짧은 만료 시간으로 토큰 생성
    short_lived_token = AuthService.create_access_token(
        data={"sub": "test_user"},
        expires_delta=timedelta(seconds=1)
    )
    
    # 1초 대기
    import time
    time.sleep(2)
    
    # 만료된 토큰 검증
    expired_payload = AuthService.validate_token(short_lived_token)
    assert expired_payload is None

def test_token_invalid_signature():
    """잘못된 서명 토큰 검증 테스트"""
    # 유효하지 않은 토큰 생성 (잘못된 키 사용)
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.invalid_signature"
    
    # 토큰 검증
    invalid_payload = AuthService.validate_token(invalid_token)
    assert invalid_payload is None 