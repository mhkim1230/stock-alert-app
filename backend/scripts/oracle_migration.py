import sqlite3
import oracledb
import os
from datetime import datetime

def convert_datetime(dt):
    """SQLite datetime을 Oracle datetime으로 변환"""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                return None
    return dt

def table_exists(cursor, table_name):
    """테이블 존재 여부 확인"""
    cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def migrate_to_oracle():
    """SQLite에서 Oracle XE로 데이터 마이그레이션"""
    
    # Oracle 연결 설정
    oracle_connection = oracledb.connect(
        user="system",
        password="stockalert123",
        dsn="localhost:1521/XE"
    )
    oracle_cursor = oracle_connection.cursor()
    
    # SQLite 연결
    sqlite_connection = sqlite3.connect('stock_alert.db')
    sqlite_cursor = sqlite_connection.cursor()
    
    try:
        # 테이블 생성
        create_tables(oracle_cursor)
        
        # 데이터 마이그레이션
        if table_exists(sqlite_cursor, 'user'):
            migrate_users(sqlite_cursor, oracle_cursor)
        
        if table_exists(sqlite_cursor, 'device_token'):
            migrate_device_tokens(sqlite_cursor, oracle_cursor)
        
        if table_exists(sqlite_cursor, 'watchlist'):
            migrate_watchlist(sqlite_cursor, oracle_cursor)
        
        # 알림 테이블 마이그레이션
        migrate_alerts(sqlite_cursor, oracle_cursor)
        
        # 변경사항 저장
        oracle_connection.commit()
        print("✅ 마이그레이션 완료!")
        
    except Exception as e:
        print(f"❌ 마이그레이션 오류: {e}")
        oracle_connection.rollback()
    finally:
        oracle_cursor.close()
        oracle_connection.close()
        sqlite_cursor.close()
        sqlite_connection.close()

def create_tables(cursor):
    """Oracle 테이블 생성"""
    
    # 기존 테이블이 있다면 삭제 (외래 키 제약조건 고려한 순서)
    tables = ["NEWS_ALERT", "CURRENCY_ALERT", "STOCK_ALERT", "WATCHLIST", "DEVICE_TOKEN", '"USER"']
    for table in tables:
        try:
            cursor.execute(f"""
            BEGIN
               EXECUTE IMMEDIATE 'DROP TABLE {table} CASCADE CONSTRAINTS';
            EXCEPTION
               WHEN OTHERS THEN
                  IF SQLCODE != -942 THEN
                     RAISE;
                  END IF;
            END;
            """)
        except Exception as e:
            if "ORA-00942" not in str(e):  # 테이블이 없는 경우는 무시
                print(f"Warning: {e}")
    
    # User 테이블
    cursor.execute("""
    CREATE TABLE "USER" (
        id VARCHAR2(36) PRIMARY KEY,
        username VARCHAR2(50) UNIQUE NOT NULL,
        email VARCHAR2(100) UNIQUE NOT NULL,
        password_hash VARCHAR2(100) NOT NULL,
        is_active NUMBER(1) DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # DeviceToken 테이블
    cursor.execute("""
    CREATE TABLE DEVICE_TOKEN (
        id VARCHAR2(36) PRIMARY KEY,
        user_id VARCHAR2(36) NOT NULL,
        token VARCHAR2(200) NOT NULL,
        device_type VARCHAR2(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES "USER"(id)
    )
    """)
    
    # Watchlist 테이블
    cursor.execute("""
    CREATE TABLE WATCHLIST (
        id VARCHAR2(36) PRIMARY KEY,
        user_id VARCHAR2(36) NOT NULL,
        symbol VARCHAR2(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES "USER"(id)
    )
    """)
    
    # StockAlert 테이블
    cursor.execute("""
    CREATE TABLE STOCK_ALERT (
        id VARCHAR2(36) PRIMARY KEY,
        user_id VARCHAR2(36) NOT NULL,
        stock_symbol VARCHAR2(20) NOT NULL,
        target_price NUMBER NOT NULL,
        condition VARCHAR2(10) NOT NULL,
        is_active NUMBER(1) DEFAULT 1,
        triggered_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES "USER"(id)
    )
    """)
    
    # CurrencyAlert 테이블
    cursor.execute("""
    CREATE TABLE CURRENCY_ALERT (
        id VARCHAR2(36) PRIMARY KEY,
        user_id VARCHAR2(36) NOT NULL,
        base_currency VARCHAR2(3) NOT NULL,
        target_currency VARCHAR2(3) NOT NULL,
        target_rate NUMBER NOT NULL,
        condition VARCHAR2(10) NOT NULL,
        is_active NUMBER(1) DEFAULT 1,
        triggered_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES "USER"(id)
    )
    """)
    
    # NewsAlert 테이블
    cursor.execute("""
    CREATE TABLE NEWS_ALERT (
        id VARCHAR2(36) PRIMARY KEY,
        user_id VARCHAR2(36) NOT NULL,
        keywords VARCHAR2(200) NOT NULL,
        is_active NUMBER(1) DEFAULT 1,
        last_checked TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES "USER"(id)
    )
    """)
    
    print("✅ 테이블 생성 완료")

def migrate_users(sqlite_cursor, oracle_cursor):
    """사용자 데이터 마이그레이션"""
    sqlite_cursor.execute("""
    SELECT id, username, email, password_hash, is_active, created_at 
    FROM user
    """)
    users = sqlite_cursor.fetchall()
    
    for user in users:
        # datetime 변환
        user = list(user)
        user[5] = convert_datetime(user[5])
        
        oracle_cursor.execute("""
        INSERT INTO "USER" (id, username, email, password_hash, is_active, created_at)
        VALUES (:1, :2, :3, :4, :5, :6)
        """, user)
    
    print(f"✅ {len(users)}명의 사용자 마이그레이션 완료")

def migrate_device_tokens(sqlite_cursor, oracle_cursor):
    """디바이스 토큰 마이그레이션"""
    sqlite_cursor.execute("""
    SELECT id, user_id, token, device_type, created_at 
    FROM device_token
    """)
    tokens = sqlite_cursor.fetchall()
    
    for token in tokens:
        # datetime 변환
        token = list(token)
        token[4] = convert_datetime(token[4])
        
        oracle_cursor.execute("""
        INSERT INTO DEVICE_TOKEN (id, user_id, token, device_type, created_at)
        VALUES (:1, :2, :3, :4, :5)
        """, token)
    
    print(f"✅ {len(tokens)}개의 디바이스 토큰 마이그레이션 완료")

def migrate_watchlist(sqlite_cursor, oracle_cursor):
    """관심 종목 마이그레이션"""
    sqlite_cursor.execute("""
    SELECT id, user_id, symbol, created_at 
    FROM watchlist
    """)
    items = sqlite_cursor.fetchall()
    
    for item in items:
        # datetime 변환
        item = list(item)
        item[3] = convert_datetime(item[3])
        
        oracle_cursor.execute("""
        INSERT INTO WATCHLIST (id, user_id, symbol, created_at)
        VALUES (:1, :2, :3, :4)
        """, item)
    
    print(f"✅ {len(items)}개의 관심 종목 마이그레이션 완료")

def migrate_alerts(sqlite_cursor, oracle_cursor):
    """알림 설정 마이그레이션"""
    # 주식 알림
    if table_exists(sqlite_cursor, 'stock_alert'):
        sqlite_cursor.execute("""
        SELECT id, user_id, stock_symbol, target_price, condition, 
               is_active, triggered_at, created_at 
        FROM stock_alert
        """)
        stock_alerts = sqlite_cursor.fetchall()
        
        for alert in stock_alerts:
            # datetime 변환
            alert = list(alert)
            alert[6] = convert_datetime(alert[6])
            alert[7] = convert_datetime(alert[7])
            
            oracle_cursor.execute("""
            INSERT INTO STOCK_ALERT (id, user_id, stock_symbol, target_price, condition, 
                                   is_active, triggered_at, created_at)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
            """, alert)
        print(f"✅ {len(stock_alerts)}개의 주식 알림 마이그레이션 완료")
    
    # 환율 알림
    if table_exists(sqlite_cursor, 'currency_alert'):
        sqlite_cursor.execute("""
        SELECT id, user_id, base_currency, target_currency, target_rate, 
               condition, is_active, triggered_at, created_at 
        FROM currency_alert
        """)
        currency_alerts = sqlite_cursor.fetchall()
        
        for alert in currency_alerts:
            # datetime 변환
            alert = list(alert)
            alert[7] = convert_datetime(alert[7])
            alert[8] = convert_datetime(alert[8])
            
            oracle_cursor.execute("""
            INSERT INTO CURRENCY_ALERT (id, user_id, base_currency, target_currency, 
                                      target_rate, condition, is_active, triggered_at, created_at)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
            """, alert)
        print(f"✅ {len(currency_alerts)}개의 환율 알림 마이그레이션 완료")
    
    # 뉴스 알림
    if table_exists(sqlite_cursor, 'news_alert'):
        sqlite_cursor.execute("""
        SELECT id, user_id, keywords, is_active, last_checked, created_at 
        FROM news_alert
        """)
        news_alerts = sqlite_cursor.fetchall()
        
        for alert in news_alerts:
            # datetime 변환
            alert = list(alert)
            alert[4] = convert_datetime(alert[4])
            alert[5] = convert_datetime(alert[5])
            
            oracle_cursor.execute("""
            INSERT INTO NEWS_ALERT (id, user_id, keywords, is_active, last_checked, created_at)
            VALUES (:1, :2, :3, :4, :5, :6)
            """, alert)
        print(f"✅ {len(news_alerts)}개의 뉴스 알림 마이그레이션 완료")

if __name__ == "__main__":
    migrate_to_oracle() 