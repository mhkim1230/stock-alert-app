import sys
import os
import logging
from typing import List, Dict, Any

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import db, create_tables

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_migration_history_table():
    """
    마이그레이션 히스토리 테이블 생성
    """
    try:
        db.execute_sql('''
            CREATE TABLE IF NOT EXISTS migration_history (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("마이그레이션 히스토리 테이블 생성 완료")
    except Exception as e:
        logger.error(f"마이그레이션 히스토리 테이블 생성 실패: {e}")

def check_migration_applied(migration_name: str) -> bool:
    """
    특정 마이그레이션이 이미 적용되었는지 확인
    
    :param migration_name: 마이그레이션 이름
    :return: 마이그레이션 적용 여부
    """
    try:
        result = db.execute_sql(
            'SELECT COUNT(*) FROM migration_history WHERE migration_name = %s', 
            (migration_name,)
        )
        return result.fetchone()[0] > 0
    except Exception as e:
        logger.error(f"마이그레이션 확인 중 오류: {e}")
        return False

def record_migration(migration_name: str):
    """
    마이그레이션 히스토리에 기록
    
    :param migration_name: 마이그레이션 이름
    """
    try:
        db.execute_sql(
            'INSERT INTO migration_history (migration_name) VALUES (%s)', 
            (migration_name,)
        )
        logger.info(f"마이그레이션 기록: {migration_name}")
    except Exception as e:
        logger.error(f"마이그레이션 기록 실패: {e}")

def run_migrations():
    """
    모든 데이터베이스 마이그레이션 실행
    """
    try:
        # 데이터베이스 연결
        db.connect()
        
        # 마이그레이션 히스토리 테이블 생성
        create_migration_history_table()
        
        # 마이그레이션 이름
        migration_name = 'migration_v1_initial_schema'
        
        # 이미 적용된 마이그레이션인지 확인
        if check_migration_applied(migration_name):
            logger.info(f"마이그레이션 {migration_name} 이미 적용됨")
            return
        
        # 테이블 생성
        create_tables()
        
        # 마이그레이션 히스토리에 기록
        record_migration(migration_name)
        
        logger.info("모든 마이그레이션 완료")
    
    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {e}")
    
    finally:
        # 데이터베이스 연결 종료
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    run_migrations() 