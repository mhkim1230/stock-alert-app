import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.sql import text
from src.config.settings import Settings

@pytest.mark.asyncio
async def test_database_connection():
    """비동기 데이터베이스 연결 테스트"""
    
    # 데이터베이스 연결 설정
    settings = Settings()
    DATABASE_URL = f"oracle+oracledb://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.connect() as conn:
        try:
            # 간단한 쿼리 실행
            result = await conn.execute(text("SELECT 1 FROM DUAL"))
            row = result.scalar()
            assert row == 1
            print("✅ Database connection test successful!")
            
        except Exception as e:
            print(f"❌ Database connection test failed: {str(e)}")
            raise
        finally:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(test_database_connection()) 