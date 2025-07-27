import cx_Oracle
from sqlalchemy import create_engine, text
import uuid
from datetime import datetime

# Oracle client 초기화
cx_Oracle.init_oracle_client(lib_dir="/opt/oracle/instantclient_19_8")

# 연결 정보
username = 'system'
password = 'oracle123'
hostname = 'localhost'
port = '1521'
service_name = 'XE'

# DSN 생성
dsn = cx_Oracle.makedsn(hostname, port, service_name=service_name)

# 연결 문자열 생성
connection_string = f'oracle+cx_oracle://{username}:{password}@{dsn}'

try:
    # 엔진 생성
    engine = create_engine(connection_string)
    
    # 연결 테스트
    with engine.connect() as connection:
        # 기본 연결 테스트
        result = connection.execute(text("SELECT 1 FROM dual"))
        for row in result:
            print(f"연결 성공! 테스트 쿼리 결과: {row[0]}")
        
        # STOCK_ALERT 테이블 생성
        create_table_sql = """
        CREATE TABLE STOCK_ALERT (
            id VARCHAR2(36) PRIMARY KEY,
            user_id VARCHAR2(36) NOT NULL,
            stock_symbol VARCHAR2(20) NOT NULL,
            target_price NUMBER(10,2) NOT NULL,
            condition VARCHAR2(10) NOT NULL,
            is_active NUMBER(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            triggered_at TIMESTAMP,
            last_checked TIMESTAMP
        )
        """
        
        try:
            connection.execute(text("DROP TABLE STOCK_ALERT"))
            print("\n기존 STOCK_ALERT 테이블 삭제 완료")
        except:
            pass
            
        try:
            connection.execute(text(create_table_sql))
            print("\nSTOCK_ALERT 테이블 생성 완료")
            
            # 테스트 데이터 추가
            test_data = [
                {
                    'id': str(uuid.uuid4()),
                    'user_id': str(uuid.uuid4()),
                    'stock_symbol': 'AAPL',
                    'target_price': 150.00,
                    'condition': 'ABOVE',
                    'is_active': 1,
                    'created_at': datetime.now(),
                    'triggered_at': None,
                    'last_checked': datetime.now()
                },
                {
                    'id': str(uuid.uuid4()),
                    'user_id': str(uuid.uuid4()),
                    'stock_symbol': 'GOOGL',
                    'target_price': 2500.00,
                    'condition': 'BELOW',
                    'is_active': 1,
                    'created_at': datetime.now(),
                    'triggered_at': None,
                    'last_checked': datetime.now()
                }
            ]
            
            for data in test_data:
                insert_sql = """
                INSERT INTO STOCK_ALERT (id, user_id, stock_symbol, target_price, condition, is_active, created_at, triggered_at, last_checked)
                VALUES (:id, :user_id, :stock_symbol, :target_price, :condition, :is_active, :created_at, :triggered_at, :last_checked)
                """
                connection.execute(text(insert_sql), data)
            
            print("\n테스트 데이터 추가 완료")
            
        except Exception as e:
            print(f"\nSTOCK_ALERT 테이블 생성 또는 데이터 추가 오류: {str(e)}")
            
        # STOCK_ALERT 테이블 조회
        try:
            result = connection.execute(text("""
                SELECT 
                    id,
                    user_id,
                    stock_symbol,
                    target_price,
                    condition,
                    CASE is_active 
                        WHEN 1 THEN '활성' 
                        ELSE '비활성' 
                    END as is_active,
                    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                    TO_CHAR(triggered_at, 'YYYY-MM-DD HH24:MI:SS') as triggered_at,
                    TO_CHAR(last_checked, 'YYYY-MM-DD HH24:MI:SS') as last_checked
                FROM STOCK_ALERT
                ORDER BY created_at DESC
            """))
            
            print("\nSTOCK_ALERT 테이블 데이터:")
            print("=" * 120)
            print(f"{'종목':^10} | {'목표가':^10} | {'조건':^8} | {'상태':^8} | {'생성일시':^19} | {'트리거일시':^19} | {'마지막 체크':^19}")
            print("-" * 120)
            
            for row in result:
                print(f"{row.stock_symbol:^10} | {row.target_price:^10} | {row.condition:^8} | {row.is_active:^8} | {row.created_at:^19} | {row.triggered_at or '없음':^19} | {row.last_checked:^19}")
            
            print("=" * 120)
            
        except Exception as e:
            print(f"\nSTOCK_ALERT 테이블 조회 오류: {str(e)}")

except Exception as e:
    print(f"오류 발생: {str(e)}") 