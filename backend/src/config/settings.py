import os
import secrets
from typing import List, Optional
from functools import lru_cache
from dotenv import load_dotenv
import logging

# 환경 변수 로드를 최상단으로 이동
load_dotenv()

# 데이터베이스 설정
DATABASE_CONFIG = {
    'database': os.getenv('DB_NAME', 'XE'),
    'user': os.getenv('DB_USER', 'MHKIM'),
    'password': os.getenv('DB_PASSWORD', 'rlaalghk11'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 1521))
}

# 환율 API 설정
CURRENCY_API_SETTINGS = {
    'provider': os.getenv('CURRENCY_API_PROVIDER', 'exchangerate-api'),
    'api_key': os.getenv('CURRENCY_API_KEY', ''),
    'base_url': os.getenv(
        'CURRENCY_API_BASE_URL', 
        'https://api.exchangerate-api.com/v4/latest/'
    ),
    'timeout': int(os.getenv('CURRENCY_API_TIMEOUT', 10))
}

# APNs 설정
APNS_SETTINGS = {
    'bundle_id': os.getenv('APNS_BUNDLE_ID', 'com.example.stockalert'),
    'key_id': os.getenv('APNS_KEY_ID', ''),
    'team_id': os.getenv('APNS_TEAM_ID', ''),
    'auth_key_path': os.getenv(
        'APNS_AUTH_KEY_PATH', 
        os.path.join(os.path.dirname(__file__), 'AuthKey.p8')
    ),
    'use_sandbox': os.getenv('APNS_USE_SANDBOX', 'true').lower() == 'true'
}

# 로깅 설정
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': os.getenv('LOG_FILE_PATH', 'logs/stock_alert.log')
}

# 보안 설정
SECURITY_CONFIG = {
    'jwt_secret_key': os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
    'jwt_algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
    'jwt_expiration_minutes': int(os.getenv('JWT_EXPIRATION_MINUTES', 30))
}

# 알림 설정
NOTIFICATION_CONFIG = {
    'max_alerts_per_user': int(os.getenv('MAX_ALERTS_PER_USER', 10)),
    'alert_cooldown_hours': int(os.getenv('ALERT_COOLDOWN_HOURS', 24))
}

# API 키 설정
API_KEYS = {}

class Settings:
    """애플리케이션 설정 (클라우드 최적화)"""
    
    def __init__(self):
        # 클라우드 환경 감지
        self.IS_CLOUD = os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU_APP_ID')
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # 데이터베이스 설정 (우선순위: Supabase → SQLite)
        if self.IS_CLOUD:
            # 클라우드 환경: Supabase PostgreSQL
            self.DATABASE_URL = os.getenv('DATABASE_URL')
            if self.DATABASE_URL and self.DATABASE_URL.startswith('postgres://'):
                # Supabase URL 형식 변환
                self.DATABASE_URL = self.DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        else:
            # 로컬 환경: SQLite 또는 기존 Oracle
            self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./stock_alert.db')
        
        # Oracle 설정 (기존 호환성)
        self.DATABASE_USER = os.getenv('DATABASE_USER', 'stock_user')
        self.DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'password')
        self.DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
        self.DATABASE_PORT = os.getenv('DATABASE_PORT', '1521')
        self.DATABASE_NAME = os.getenv('DATABASE_NAME', 'stock_db')
        
        # 서버 설정
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', '8000'))
        
        # JWT 설정
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        # APNs 설정 (iOS 푸시 알림)
        self.APNS_KEY_ID = os.getenv('APNS_KEY_ID')
        self.APNS_TEAM_ID = os.getenv('APNS_TEAM_ID') 
        self.APNS_BUNDLE_ID = os.getenv('APNS_BUNDLE_ID', 'com.example.stockalert')
        self.APNS_PRIVATE_KEY_PATH = os.getenv('APNS_PRIVATE_KEY_PATH')
        self.APNS_USE_SANDBOX = os.getenv('APNS_USE_SANDBOX', 'true').lower() == 'true'
        
        # 로깅 설정
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # 파싱 설정 (클라우드 최적화)
        self.ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        self.CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '300'))  # 5분
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))
        
        # 요청 제한 (클라우드에서 IP 차단 방지)
        self.MIN_REQUEST_DELAY = float(os.getenv('MIN_REQUEST_DELAY', '1.0'))
        self.MAX_REQUEST_DELAY = float(os.getenv('MAX_REQUEST_DELAY', '3.0'))
        
        # CORS 설정
        if self.IS_CLOUD:
            self.ALLOWED_ORIGINS = ["*"]  # 클라우드에서는 모든 도메인 허용
        else:
            self.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8007"]
        
        # 설정 로깅
        logging.getLogger(__name__).info(f"🌍 환경: {'클라우드' if self.IS_CLOUD else '로컬'}")
        logging.getLogger(__name__).info(f"📊 데이터베이스: {self.get_db_type()}")
    
    def get_db_type(self) -> str:
        """현재 사용 중인 데이터베이스 타입 반환"""
        if self.DATABASE_URL:
            if 'postgresql' in self.DATABASE_URL:
                return 'PostgreSQL (Supabase)'
            elif 'sqlite' in self.DATABASE_URL:
                return 'SQLite (로컬)'
            elif 'oracle' in self.DATABASE_URL:
                return 'Oracle'
        return '미설정'
    
    @property
    def database_url(self) -> str:
        """데이터베이스 URL 반환"""
        return self.DATABASE_URL or 'sqlite:///./stock_alert.db'

# 전역 설정 인스턴스
settings = Settings() 