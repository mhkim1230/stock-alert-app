import os
import sys
from dotenv import load_dotenv

def load_environment_variables(env_file_path=None):
    """
    환경 변수 로딩 유틸리티
    
    Args:
        env_file_path (str, optional): .env 파일 경로. 
                                       제공되지 않으면 기본 경로 사용.
    """
    # 기본 .env 파일 경로 설정
    if env_file_path is None:
        # 스크립트 실행 위치 기준 상대 경로
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_file_path = os.path.join(base_dir, '.env')
    
    # 환경 변수 파일 존재 여부 확인
    if not os.path.exists(env_file_path):
        print(f"경고: {env_file_path} 파일을 찾을 수 없습니다.")
        return False
    
    try:
        # python-dotenv를 사용한 환경 변수 로딩
        load_dotenv(env_file_path, override=True)
        print(f"환경 변수가 {env_file_path}에서 성공적으로 로드되었습니다.")
        return True
    
    except Exception as e:
        print(f"환경 변수 로딩 중 오류 발생: {e}")
        return False

def validate_required_env_vars():
    """
    필수 환경 변수 존재 여부 확인
    
    Returns:
        bool: 모든 필수 환경 변수가 설정되어 있으면 True
    """
    required_vars = [
        'SECRET_KEY', 
        'DATABASE_URL', 
        'APP_ENV'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("다음 필수 환경 변수가 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    
    return True

def main():
    """
    스크립트를 직접 실행할 경우의 메인 함수
    환경 변수 로딩 및 검증 수행
    """
    # 환경 변수 로딩
    load_environment_variables()
    
    # 필수 환경 변수 검증
    if validate_required_env_vars():
        print("모든 필수 환경 변수가 설정되었습니다.")
        sys.exit(0)
    else:
        print("환경 변수 설정에 문제가 있습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main() 