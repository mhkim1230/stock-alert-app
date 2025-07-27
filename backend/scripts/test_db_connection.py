import sys
import os
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import db, User
from src.config.settings import DATABASE_CONFIG

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """
    데이터베이스 연결 및 기본 작업 테스트
    """
    try:
        # 데이터베이스 연결
        db.connect()
        logger.info("데이터베이스 연결 성공")
        
        # 사용자 테이블 존재 여부 확인
        if not db.table_exists(User):
            logger.warning("사용자 테이블이 존재하지 않습니다.")
            return False
        
        # 테스트 사용자 생성
        test_user = User.create(
            username=f'test_user_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            email=f'test_{datetime.now().strftime("%Y%m%d%H%M%S")}@example.com',
            password_hash='test_password_hash',
            is_active=True,
            last_login=datetime.now()
        )
        
        logger.info(f"테스트 사용자 생성: {test_user.username}")
        
        # 사용자 조회
        retrieved_user = User.get_by_id(test_user.id)
        logger.info(f"사용자 조회 성공: {retrieved_user.username}")
        
        # 테스트 사용자 삭제
        test_user.delete_instance()
        logger.info("테스트 사용자 삭제 완료")
        
        return True
    
    except Exception as e:
        logger.error(f"데이터베이스 테스트 중 오류 발생: {e}")
        return False
    
    finally:
        # 데이터베이스 연결 종료
        if not db.is_closed():
            db.close()
            logger.info("데이터베이스 연결 종료")

def print_database_config():
    """
    데이터베이스 구성 정보 출력
    """
    logger.info("데이터베이스 구성 정보:")
    for key, value in DATABASE_CONFIG.items():
        # 비밀번호는 마스킹
        display_value = '****' if key == 'password' else value
        logger.info(f"{key}: {display_value}")

def main():
    """
    메인 실행 함수
    """
    print_database_config()
    
    connection_result = test_database_connection()
    
    if connection_result:
        logger.info("데이터베이스 연결 및 기본 작업 테스트 성공")
        sys.exit(0)
    else:
        logger.error("데이터베이스 연결 또는 작업 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main() 