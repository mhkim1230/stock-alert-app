#!/usr/bin/env python3
"""
간단한 서버 실행 스크립트
사용법: python run_server.py
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append('.')

# 환경 설정
os.environ['PYTHONPATH'] = '.'
os.environ['APP_ENV'] = 'production'
os.environ['DATABASE_HOST'] = 'localhost'
os.environ['DATABASE_PORT'] = '1521'
os.environ['DATABASE_NAME'] = 'XE'
os.environ['DATABASE_USER'] = 'MHKIM'
os.environ['DATABASE_PASSWORD'] = 'rlaalghk11'

# FastAPI 앱 실행
from src.api.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 주식 알림 API 서버 시작!")
    print("📡 URL: http://localhost:8001")
    print("📋 Health Check: http://localhost:8001/health")
    print("📊 네이버 파싱: http://localhost:8001/naver/stocks/search/삼성전자")
    print("⏹️  서버 종료: Ctrl+C")
    print("-" * 50)
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8001, 
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n✅ 서버가 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 오류: {e}") 