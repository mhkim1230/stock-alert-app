import functools
import time
import traceback
from typing import Any, Callable

from src.config.logging_config import get_logger

def log_function(
    logger=None, 
    log_level='INFO', 
    log_args=False, 
    log_return=False
):
    """
    함수 로깅을 위한 데코레이터
    
    Args:
        logger: 사용할 로거 (기본값: None, 자동으로 모듈 로거 사용)
        log_level: 로깅 레벨 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_args: 함수 인자 로깅 여부
        log_return: 반환값 로깅 여부
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 로거 설정 (미제공 시 함수의 모듈 로거 사용)
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            # 로깅 레벨 매핑
            log_levels = {
                'DEBUG': logger.debug,
                'INFO': logger.info,
                'WARNING': logger.warning,
                'ERROR': logger.error,
                'CRITICAL': logger.critical
            }
            log_method = log_levels.get(log_level.upper(), logger.info)
            
            # 함수 호출 로깅
            func_name = func.__name__
            log_method(f"Calling function: {func_name}")
            
            # 인자 로깅
            if log_args:
                log_method(f"Function arguments: args={args}, kwargs={kwargs}")
            
            # 실행 시간 측정
            start_time = time.time()
            
            try:
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 실행 시간 계산
                execution_time = time.time() - start_time
                log_method(f"Function {func_name} executed in {execution_time:.4f} seconds")
                
                # 반환값 로깅
                if log_return:
                    log_method(f"Function return value: {result}")
                
                return result
            
            except Exception as e:
                # 예외 로깅
                logger.error(f"Exception in {func_name}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        
        return wrapper
    
    return decorator 