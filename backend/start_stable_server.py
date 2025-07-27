#!/usr/bin/env python3
"""
안정적인 서버 관리 스크립트
- API 서버와 웹 시뮬레이터를 자동으로 시작
- 포트 충돌 자동 해결
- 프로세스 모니터링 및 자동 재시작
"""

import os
import sys
import time
import signal
import socket
import subprocess
import threading
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StableServerManager:
    def __init__(self):
        self.api_process = None
        self.web_process = None
        self.api_port = 8001
        self.web_port = 8007
        self.running = False
        
    def is_port_available(self, port):
        """포트 사용 가능 여부 확인"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    def kill_process_on_port(self, port):
        """특정 포트를 사용하는 프로세스 종료"""
        try:
            # lsof 명령으로 포트 사용 프로세스 찾기
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        try:
                            subprocess.run(['kill', '-9', pid.strip()], timeout=5)
                            logger.info(f"포트 {port}의 프로세스 {pid} 종료됨")
                        except Exception as e:
                            logger.warning(f"프로세스 {pid} 종료 실패: {e}")
                
                # 잠시 대기
                time.sleep(1)
                
        except Exception as e:
            logger.warning(f"포트 {port} 정리 중 오류: {e}")
    
    def ensure_port_available(self, port, service_name):
        """포트가 사용 가능하도록 보장"""
        if not self.is_port_available(port):
            logger.warning(f"{service_name} 포트 {port}이 사용 중입니다. 기존 프로세스를 종료합니다.")
            self.kill_process_on_port(port)
            
            # 다시 확인
            if not self.is_port_available(port):
                logger.error(f"포트 {port} 정리 실패")
                return False
        
        logger.info(f"{service_name} 포트 {port} 사용 가능")
        return True
    
    def start_api_server(self):
        """API 서버 시작"""
        try:
            if not self.ensure_port_available(self.api_port, "API 서버"):
                return False
            
            # 백엔드 디렉토리로 이동
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            
            # API 서버 시작 명령
            cmd = [
                sys.executable, '-c',
                """
import sys
sys.path.append('.')
from src.api.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8001, log_level='info')
"""
            ]
            
            logger.info("🚀 API 서버 시작 중...")
            self.api_process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info("✅ API 서버 시작됨 (localhost:8001)")
            return True
            
        except Exception as e:
            logger.error(f"API 서버 시작 실패: {e}")
            return False
    
    def start_web_server(self):
        """웹 시뮬레이터 시작"""
        try:
            if not self.ensure_port_available(self.web_port, "웹 시뮬레이터"):
                return False
            
            # 웹 시뮬레이터 디렉토리
            web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_simulator')
            
            # 웹 서버 시작 명령
            cmd = [sys.executable, 'simple_web_server.py']
            
            logger.info("🌐 웹 시뮬레이터 시작 중...")
            self.web_process = subprocess.Popen(
                cmd,
                cwd=web_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info("✅ 웹 시뮬레이터 시작됨 (localhost:8007)")
            return True
            
        except Exception as e:
            logger.error(f"웹 시뮬레이터 시작 실패: {e}")
            return False
    
    def monitor_process(self, process, name, restart_func):
        """프로세스 모니터링 및 자동 재시작"""
        while self.running:
            if process and process.poll() is not None:
                logger.error(f"{name}가 중지되었습니다. 재시작 중...")
                time.sleep(2)  # 잠시 대기
                if restart_func():
                    if name == "API 서버":
                        process = self.api_process
                    else:
                        process = self.web_process
                else:
                    logger.error(f"{name} 재시작 실패")
                    break
            
            time.sleep(5)  # 5초마다 확인
    
    def log_output(self, process, name):
        """프로세스 출력 로깅"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[{name}] {line.strip()}")
        except Exception as e:
            logger.warning(f"{name} 출력 로깅 오류: {e}")
    
    def start_servers(self):
        """두 서버 모두 시작"""
        logger.info("🚀 안정적인 서버 시스템 시작")
        
        # 기존 프로세스 정리
        self.ensure_port_available(self.api_port, "API 서버")
        self.ensure_port_available(self.web_port, "웹 시뮬레이터")
        
        self.running = True
        
        # API 서버 시작
        if not self.start_api_server():
            logger.error("API 서버 시작 실패")
            return False
        
        # 웹 서버 시작
        if not self.start_web_server():
            logger.error("웹 시뮬레이터 시작 실패")
            self.stop_servers()
            return False
        
        # 출력 로깅 스레드 시작
        if self.api_process:
            threading.Thread(
                target=self.log_output,
                args=(self.api_process, "API"),
                daemon=True
            ).start()
        
        if self.web_process:
            threading.Thread(
                target=self.log_output,
                args=(self.web_process, "WEB"),
                daemon=True
            ).start()
        
        # 모니터링 스레드 시작
        threading.Thread(
            target=self.monitor_process,
            args=(self.api_process, "API 서버", self.start_api_server),
            daemon=True
        ).start()
        
        threading.Thread(
            target=self.monitor_process,
            args=(self.web_process, "웹 시뮬레이터", self.start_web_server),
            daemon=True
        ).start()
        
        logger.info("=" * 60)
        logger.info("🎉 서버 시스템이 성공적으로 시작되었습니다!")
        logger.info("📡 API 서버: http://localhost:8001")
        logger.info("🌐 웹 시뮬레이터: http://localhost:8007")
        logger.info("📋 Health Check: http://localhost:8001/health")
        logger.info("📊 네이버 파싱: http://localhost:8001/naver/stocks/search/삼성전자")
        logger.info("⏹️  서버 종료: Ctrl+C")
        logger.info("=" * 60)
        
        return True
    
    def stop_servers(self):
        """서버 중지"""
        logger.info("🛑 서버 시스템 중지 중...")
        self.running = False
        
        if self.api_process:
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
                logger.info("✅ API 서버 중지됨")
            except Exception as e:
                logger.warning(f"API 서버 강제 종료: {e}")
                try:
                    self.api_process.kill()
                except:
                    pass
        
        if self.web_process:
            try:
                self.web_process.terminate()
                self.web_process.wait(timeout=5)
                logger.info("✅ 웹 시뮬레이터 중지됨")
            except Exception as e:
                logger.warning(f"웹 시뮬레이터 강제 종료: {e}")
                try:
                    self.web_process.kill()
                except:
                    pass
        
        # 포트 정리
        self.kill_process_on_port(self.api_port)
        self.kill_process_on_port(self.web_port)
        
        logger.info("🏁 서버 시스템 완전 중지됨")
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"시그널 {signum} 수신됨. 서버 중지 중...")
        self.stop_servers()
        sys.exit(0)

def main():
    """메인 함수"""
    manager = StableServerManager()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        if manager.start_servers():
            # 서버 실행 상태 유지
            while manager.running:
                time.sleep(1)
        else:
            logger.error("서버 시작 실패")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("사용자 중단 요청")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
    finally:
        manager.stop_servers()

if __name__ == "__main__":
    main() 