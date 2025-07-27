import cx_Oracle
import os
import sys

def create_user(username, password, system_password):
    try:
        # system 계정으로 접속
        dsn = cx_Oracle.makedsn(
            host="localhost",
            port=1521,
            service_name="XEPDB1"  # 기본 PDB 이름
        )
        connection = cx_Oracle.connect(
            user="system",
            password=system_password,
            dsn=dsn
        )
        
        cursor = connection.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute(
            "SELECT COUNT(*) FROM all_users WHERE username = :username",
            username=username.upper()
        )
        
        if cursor.fetchone()[0] > 0:
            print(f"사용자 {username}이(가) 이미 존재합니다.")
            return
        
        # 새 사용자 생성 (따옴표로 비밀번호 감싸기)
        cursor.execute(f'CREATE USER {username.upper()} IDENTIFIED BY "{password}"')
        
        # 권한 부여
        cursor.execute(f'GRANT CONNECT, RESOURCE TO {username.upper()}')
        cursor.execute(f'ALTER USER {username.upper()} QUOTA UNLIMITED ON USERS')
        
        connection.commit()
        print(f"✅ 사용자 {username.upper()} 생성 완료")
        print(f"✅ 권한 부여 완료")
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle 에러 발생: {error}")
        if "ORA-12514" in str(error):
            print("💡 힌트: service_name이 올바른지 확인하세요.")
        elif "ORA-01017" in str(error):
            print("💡 힌트: system 계정의 비밀번호가 올바른지 확인하세요.")
    except Exception as error:
        print(f"❌ 에러 발생: {error}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    username = "MHKIM"  # 대문자로 변경
    password = "rlaalghk11"
    system_password = input("system 계정의 비밀번호를 입력하세요: ")
    create_user(username, password, system_password) 