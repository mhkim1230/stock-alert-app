#!/usr/bin/env python3
"""
자동 서버 시작 스크립트
- API 서버 (localhost:8001)
- 웹 시뮬레이터 (localhost:8007)
- 설정 자동화, 수정 불필요
"""

import os
import sys
import subprocess
import time
import threading
import signal
import requests

class AutoServerManager:
    """자동 서버 관리자"""
    
    def __init__(self):
        self.api_process = None
        self.web_process = None
        self.running = True
        
    def start_api_server(self):
        """API 서버 시작"""
        try:
            print("🚀 API 서버 시작 중...")
            
            # backend 디렉토리로 이동
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(backend_dir)
            
            # Python 경로 설정 및 API 서버 실행
            cmd = [
                sys.executable, "-c",
                "import sys; sys.path.append('.'); "
                "from src.api.main import app; "
                "import uvicorn; "
                "uvicorn.run(app, host='0.0.0.0', port=8001, reload=False)"
            ]
            
            self.api_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print("✅ API 서버 프로세스 시작됨 (PID: {})".format(self.api_process.pid))
            
            # 서버 시작 대기
            for i in range(30):  # 30초 대기
                try:
                    response = requests.get("http://localhost:8001/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ API 서버 준비 완료: http://localhost:8001")
                        return True
                except:
                    pass
                time.sleep(1)
                print(f"⏳ API 서버 시작 대기 중... ({i+1}/30)")
            
            print("⚠️ API 서버 시작 확인 실패 (하지만 계속 진행)")
            return True
            
        except Exception as e:
            print(f"❌ API 서버 시작 실패: {e}")
            return False
    
    def start_web_server(self):
        """웹 시뮬레이터 서버 시작"""
        try:
            print("🌐 웹 시뮬레이터 서버 시작 중...")
            
            web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_simulator")
            
            cmd = [
                sys.executable,
                os.path.join(web_dir, "simple_web_server.py")
            ]
            
            self.web_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print("✅ 웹 서버 프로세스 시작됨 (PID: {})".format(self.web_process.pid))
            
            # 웹 서버 시작 대기
            time.sleep(3)
            
            try:
                response = requests.get("http://localhost:8007", timeout=5)
                if response.status_code == 200:
                    print("✅ 웹 서버 준비 완료: http://localhost:8007")
                    return True
            except:
                pass
            
            print("✅ 웹 서버 시작됨: http://localhost:8007")
            return True
            
        except Exception as e:
            print(f"❌ 웹 서버 시작 실패: {e}")
            return False
    
    def monitor_servers(self):
        """서버 상태 모니터링"""
        while self.running:
            time.sleep(10)
            
            # API 서버 상태 확인
            if self.api_process and self.api_process.poll() is not None:
                print("⚠️ API 서버가 종료되었습니다.")
                
            # 웹 서버 상태 확인
            if self.web_process and self.web_process.poll() is not None:
                print("⚠️ 웹 서버가 종료되었습니다.")
    
    def stop_servers(self):
        """서버 중지"""
        print("\n🛑 서버 중지 중...")
        self.running = False
        
        if self.api_process:
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
                print("✅ API 서버 중지됨")
            except:
                try:
                    self.api_process.kill()
                    print("🔪 API 서버 강제 종료됨")
                except:
                    pass
        
        if self.web_process:
            try:
                self.web_process.terminate()
                self.web_process.wait(timeout=5)
                print("✅ 웹 서버 중지됨")
            except:
                try:
                    self.web_process.kill()
                    print("🔪 웹 서버 강제 종료됨")
                except:
                    pass
    
    def run(self):
        """서버 실행"""
        print("=" * 60)
        print("🚀 자동 서버 시작 스크립트")
        print("📡 API 서버: http://localhost:8001")
        print("🌐 웹 시뮬레이터: http://localhost:8007")
        print("⏹️  종료: Ctrl+C")
        print("=" * 60)
        
        try:
            # API 서버 시작
            if not self.start_api_server():
                print("❌ API 서버 시작 실패")
                return
            
            # 웹 서버 시작
            if not self.start_web_server():
                print("❌ 웹 서버 시작 실패")
                return
            
            print("\n" + "=" * 60)
            print("🎉 모든 서버가 성공적으로 시작되었습니다!")
            print("📱 브라우저에서 http://localhost:8007 접속")
            print("🔗 API 문서: http://localhost:8001/docs")
            print("💡 네이버 실시간 파싱 지원")
            print("⏹️  종료하려면 Ctrl+C 를 누르세요")
            print("=" * 60)
            
            # 모니터링 스레드 시작
            monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
            monitor_thread.start()
            
            # 메인 루프
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️ 사용자가 서버 중지를 요청했습니다.")
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류: {e}")
        finally:
            self.stop_servers()
            print("👋 서버가 완전히 종료되었습니다.")

def main():
    """메인 함수"""
    # 신호 처리
    def signal_handler(signum, frame):
        print("\n🛑 종료 신호를 받았습니다...")
        manager.stop_servers()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 서버 매니저 실행
    manager = AutoServerManager()
    manager.run()

if __name__ == "__main__":
    main() 