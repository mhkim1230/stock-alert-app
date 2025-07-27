import asyncio
from setup_env import setup_environment
from src.models.database import engine
from sqlalchemy import text

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        # 환경 변수 설정
        setup_environment()
        
        # 데이터베이스 연결 테스트
        async with engine.connect() as conn:
            # 간단한 쿼리 실행
            result = await conn.execute(text("SELECT 1 FROM DUAL"))
            value = await result.scalar()
            
            if value == 1:
                print("✅ 데이터베이스 연결 성공!")
                print(f"연결 URL: {engine.url}")
            else:
                print("❌ 데이터베이스 연결 실패: 예상치 못한 결과")
    
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {str(e)}")
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database_connection()) 