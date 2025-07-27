#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
"""

import sys
import os
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import DATABASE_CONFIG
from src.models.database import initialize_database, close_database
from src.config.logging_config import get_logger

logger = get_logger(__name__)

def create_database_if_not_exists():
    """데이터베이스가 존재하지 않으면 생성"""
    try:
        # 기본 postgres 데이터베이스에 연결
        conn = psycopg2.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database='postgres'  # 기본 데이터베이스
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 데이터베이스 존재 확인
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (DATABASE_CONFIG['database'],)
        )
        
        if not cursor.fetchone():
            # 데이터베이스 생성
            cursor.execute(f"CREATE DATABASE {DATABASE_CONFIG['database']}")
            print(f"✅ 데이터베이스 '{DATABASE_CONFIG['database']}' 생성 완료")
        else:
            print(f"ℹ️  데이터베이스 '{DATABASE_CONFIG['database']}' 이미 존재")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 생성 중 오류: {e}")
        return False
    
    return True

def create_user_if_not_exists():
    """데이터베이스 사용자가 존재하지 않으면 생성"""
    try:
        # postgres 사용자로 연결
        conn = psycopg2.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            user='postgres',  # 기본 관리자 사용자
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 사용자 존재 확인
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_user WHERE usename = %s",
            (DATABASE_CONFIG['user'],)
        )
        
        if not cursor.fetchone():
            # 사용자 생성
            cursor.execute(f"""
                CREATE USER {DATABASE_CONFIG['user']} 
                WITH PASSWORD '{DATABASE_CONFIG['password']}'
            """)
            
            # 데이터베이스 권한 부여
            cursor.execute(f"""
                GRANT ALL PRIVILEGES ON DATABASE {DATABASE_CONFIG['database']} 
                TO {DATABASE_CONFIG['user']}
            """)
            
            print(f"✅ 사용자 '{DATABASE_CONFIG['user']}' 생성 및 권한 부여 완료")
        else:
            print(f"ℹ️  사용자 '{DATABASE_CONFIG['user']}' 이미 존재")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️  사용자 생성 건너뜀 (권한 없음 또는 이미 존재): {e}")
        return True  # 사용자 생성 실패해도 계속 진행

def backup_existing_data():
    """기존 데이터 백업"""
    try:
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path = os.path.join(os.path.dirname(__file__), 'backups', backup_filename)
        
        # 백업 디렉토리 생성
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # pg_dump 명령 실행
        dump_command = f"""
        pg_dump -h {DATABASE_CONFIG['host']} -p {DATABASE_CONFIG['port']} \
        -U {DATABASE_CONFIG['user']} -d {DATABASE_CONFIG['database']} \
        -f {backup_path}
        """
        
        result = os.system(dump_command)
        
        if result == 0:
            print(f"✅ 데이터 백업 완료: {backup_path}")
            return backup_path
        else:
            print("⚠️  데이터 백업 실패 (계속 진행)")
            return None
            
    except Exception as e:
        print(f"⚠️  백업 중 오류 (계속 진행): {e}")
        return None

def run_migration():
    """데이터베이스 마이그레이션 실행"""
    print("🚀 데이터베이스 마이그레이션 시작\n")
    
    # 1. 데이터베이스 생성
    print("1. 데이터베이스 설정 확인...")
    if not create_database_if_not_exists():
        print("❌ 데이터베이스 생성 실패")
        return False
    
    # 2. 사용자 생성
    print("\n2. 데이터베이스 사용자 설정...")
    create_user_if_not_exists()
    
    # 3. 기존 데이터 백업
    print("\n3. 기존 데이터 백업...")
    backup_path = backup_existing_data()
    
    # 4. 테이블 생성/업데이트
    print("\n4. 테이블 구조 업데이트...")
    try:
        initialize_database()
        print("✅ 테이블 구조 업데이트 완료")
    except Exception as e:
        print(f"❌ 테이블 업데이트 실패: {e}")
        return False
    
    # 5. 마이그레이션 완료
    print("\n=== 마이그레이션 완료 ===")
    print("✅ 모든 데이터베이스 설정이 완료되었습니다!")
    
    if backup_path:
        print(f"📁 백업 파일: {backup_path}")
    
    # 6. 연결 테스트
    print("\n6. 데이터베이스 연결 테스트...")
    try:
        from src.models.database import User
        user_count = User.select().count()
        print(f"✅ 연결 성공! 현재 사용자 수: {user_count}명")
        
        close_database()
        return True
        
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

def show_database_info():
    """데이터베이스 정보 출력"""
    print("\n📊 데이터베이스 설정 정보:")
    print(f"   호스트: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
    print(f"   데이터베이스: {DATABASE_CONFIG['database']}")
    print(f"   사용자: {DATABASE_CONFIG['user']}")
    print(f"   연결 문자열: postgresql://{DATABASE_CONFIG['user']}:***@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("          Stock Alert 데이터베이스 마이그레이션")
    print("=" * 60)
    
    show_database_info()
    
    # 사용자 확인
    response = input("\n데이터베이스 마이그레이션을 시작하시겠습니까? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("마이그레이션이 취소되었습니다.")
        return
    
    # 마이그레이션 실행
    success = run_migration()
    
    if success:
        print("\n🎉 데이터베이스 마이그레이션이 성공적으로 완료되었습니다!")
        print("\n다음 단계:")
        print("1. FastAPI 서버 시작: python -m uvicorn src.api.main:app --reload")
        print("2. API 문서 확인: http://localhost:8000/docs")
        print("3. 헬스 체크: http://localhost:8000/health")
    else:
        print("\n❌ 마이그레이션 중 오류가 발생했습니다.")
        print("로그를 확인하고 문제를 해결한 후 다시 시도해주세요.")

if __name__ == "__main__":
    main() 