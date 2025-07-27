#!/usr/bin/env python3
"""
Python 환경 설정 스크립트
- PYTHONPATH 자동 설정
- 모듈 import 경로 문제 해결
"""

import os
import sys
from pathlib import Path

def setup_python_path():
    """Python 경로를 설정합니다."""
    # 현재 디렉토리 (backend)
    backend_dir = Path(__file__).parent.absolute()
    
    # src 디렉토리
    src_dir = backend_dir / "src"
    
    # 경로들을 sys.path에 추가
    paths_to_add = [
        str(backend_dir),
        str(src_dir),
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # 환경 변수도 설정
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    new_paths = [p for p in paths_to_add if p not in current_pythonpath]
    
    if new_paths:
        if current_pythonpath:
            os.environ['PYTHONPATH'] = ':'.join(new_paths) + ':' + current_pythonpath
        else:
            os.environ['PYTHONPATH'] = ':'.join(new_paths)
    
    print("✅ Python 경로 설정 완료:")
    for path in paths_to_add:
        print(f"   - {path}")

def verify_imports():
    """주요 모듈들이 import 가능한지 확인합니다."""
    test_imports = [
        'fastapi',
        'pydantic',
        'uvicorn',
        'peewee',
        'src.api.main',
        'src.models.database',
        'src.services.currency_service'
    ]
    
    print("\n🔍 모듈 import 테스트:")
    success_count = 0
    
    for module_name in test_imports:
        try:
            __import__(module_name)
            print(f"   ✅ {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"   ❌ {module_name}: {e}")
        except Exception as e:
            print(f"   ⚠️ {module_name}: {e}")
    
    print(f"\n📊 결과: {success_count}/{len(test_imports)} 성공")
    return success_count == len(test_imports)

def setup_environment():
    """환경 변수 설정"""
    # 데이터베이스 설정
    os.environ['DB_HOST'] = '1d66f6b8c035'
    os.environ['DB_PORT'] = '1521'
    os.environ['DB_NAME'] = 'XE'
    os.environ['DB_USER'] = 'MHKIM'
    os.environ['DB_PASSWORD'] = 'rlaalghk11'
    
    # 데이터베이스 URL
    os.environ['DATABASE_URL'] = 'oracle+oracledb://MHKIM:rlaalghk11@1d66f6b8c035:1521/?service_name=XE'
    
    # 애플리케이션 설정
    os.environ['APP_ENV'] = 'development'
    os.environ['DEBUG'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'

if __name__ == "__main__":
    print("🔧 Python 환경 설정 중...")
    setup_python_path()
    
    print("\n" + "="*50)
    success = verify_imports()
    
    if success:
        print("\n🎉 모든 모듈이 정상적으로 import됩니다!")
        print("💡 이제 에디터에서도 import 오류가 해결될 것입니다.")
    else:
        print("\n⚠️ 일부 모듈에서 import 오류가 발생했습니다.")
        print("💡 가상환경이 활성화되어 있는지 확인하세요: source venv/bin/activate")

    setup_environment()
    print("환경 변수가 설정되었습니다.")
    print(f"데이터베이스 호스트: {os.environ.get('DB_HOST')}")
    print(f"데이터베이스 포트: {os.environ.get('DB_PORT')}")
    print(f"데이터베이스 URL: {os.environ.get('DATABASE_URL')}") 