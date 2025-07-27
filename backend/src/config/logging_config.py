import os
import logging

def configure_logging(log_level=logging.INFO):
    """로깅 시스템 구성 - 기본 logging만 사용"""
    # 로그 디렉토리 생성
    log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 로그 파일 경로
    log_file_path = os.path.join(log_dir, 'stock_alert.log')

    # 로거 생성
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 콘솔 핸들러 (기본)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '[%(levelname)s] [%(name)s] %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (기본)
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('peewee').setLevel(logging.WARNING)

def get_logger(name):
    """특정 이름의 로거 반환"""
    return logging.getLogger(name)

# 기본 로깅 설정 적용
configure_logging()

# 로깅 레벨 상수
class LogLevel:
    """로깅 레벨 상수 클래스"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL 