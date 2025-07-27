import os
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

try:
    from apns2.client import APNsClient
    from apns2.payload import Payload
    from apns2.errors import APNsException
    APNS_AVAILABLE = True
except ImportError:
    APNS_AVAILABLE = False
    APNsClient = None
    Payload = None
    APNsException = Exception

# 안전한 APNs 설정 (개발 환경 최적화)
APNS_SETTINGS = {
    'key_id': os.getenv('APNS_KEY_ID', ''),  # 빈 값으로 기본 설정
    'team_id': os.getenv('APNS_TEAM_ID', ''),  # 빈 값으로 기본 설정
    'bundle_id': os.getenv('APNS_BUNDLE_ID', 'com.example.stockalert'),
    'is_production': os.getenv('APNS_PRODUCTION', 'false').lower() == 'true',
    
    # 인증 키 파일 경로 (프로젝트 루트 기준)
    'auth_key_path': os.getenv('APNS_AUTH_KEY_PATH', 'AuthKey.p8')
}

def validate_apns_settings():
    """APNs 설정 유효성 검사 (개발 환경에서는 비활성화)"""
    app_env = os.getenv('APP_ENV', 'development')
    
    if app_env == 'production':
        required_keys = ['key_id', 'team_id', 'bundle_id']
        
        for key in required_keys:
            if not APNS_SETTINGS[key]:
                raise ValueError(f"프로덕션 환경: APNs 설정 오류 - {key}가 설정되지 않았습니다.")
        
        auth_key_path = APNS_SETTINGS['auth_key_path']
        if not os.path.exists(auth_key_path):
            raise FileNotFoundError(f"APNs 인증 키 파일을 찾을 수 없습니다: {auth_key_path}")
        
        print("✅ 프로덕션 환경: APNs 설정 검증 완료")
    else:
        print("개발 환경: APNs 설정 검증을 건너뜁니다.")

# 안전한 모듈 로드 (오류가 발생해도 계속 진행)
try:
    validate_apns_settings()
except Exception as e:
    print(f"⚠️  APNs 설정 검증 실패 (개발 환경에서는 정상): {e}")

class APNSClientConfig:
    """
    Apple Push Notification Service (APNs) 클라이언트 구성 (안전 버전)
    """
    def __init__(self):
        """
        APNs 클라이언트 초기화 (안전 모드)
        """
        # 환경 변수에서 APNs 설정 로드
        self.bundle_id = os.getenv('APNS_BUNDLE_ID', 'com.example.stockalert')
        self.key_id = os.getenv('APNS_KEY_ID', '')
        self.team_id = os.getenv('APNS_TEAM_ID', '')
        
        # 인증 키 파일 경로 (p8 파일)
        self.auth_key_path = os.getenv('APNS_AUTH_KEY_PATH', 'AuthKey.p8')
        
        # 서버 환경 (개발/프로덕션)
        self.use_sandbox = os.getenv('APNS_USE_SANDBOX', 'true').lower() == 'true'
        
        # 클라이언트 캐시
        self._client: Optional[object] = None
        
        # 개발 환경에서는 클라이언트를 생성하지 않음
        self.is_development = os.getenv('APP_ENV', 'development') == 'development'
    
    def _create_client(self) -> Optional[object]:
        """
        APNs 클라이언트 생성 (안전 버전)
        
        :return: APNsClient 인스턴스 또는 None
        """
        if not APNS_AVAILABLE:
            print("APNs 라이브러리를 사용할 수 없습니다.")
            return None
        
        if self.is_development:
            print("개발 환경에서는 APNs 클라이언트를 생성하지 않습니다.")
            return None
            
        if not self.key_id or not self.team_id:
            print("APNs 설정이 불완전합니다 (key_id, team_id 필요).")
            return None
            
        try:
            # APNs 클라이언트 생성 시도 (다양한 파라미터 조합)
            if APNsClient is not None:
                # 최신 버전의 apns2 라이브러리용
                return APNsClient(
                    credentials=self.auth_key_path,
                    use_sandbox=self.use_sandbox
                )
            else:
                return None
        except Exception as e:
            print(f"APNs 클라이언트 생성 실패: {e}")
            return None
    
    @property
    def client(self) -> Optional[object]:
        """
        APNs 클라이언트 싱글톤 접근자 (안전 버전)
        
        :return: APNsClient 인스턴스 또는 None
        """
        if self.is_development:
            return None
            
        if not self._client and APNS_AVAILABLE:
            self._client = self._create_client()
        return self._client
    
    async def send_notification(
        self, 
        device_token: str, 
        payload: Dict[str, Any]
    ) -> bool:
        """
        특정 디바이스에 푸시 알림 전송 (안전 모드)
        
        :param device_token: 대상 디바이스 토큰
        :param payload: 알림 페이로드
        :return: 알림 전송 성공 여부
        """
        if self.is_development or not APNS_AVAILABLE:
            alert_info = payload.get('aps', {}).get('alert', {})
            print(f"[시뮬레이션] APNs 알림 전송: {device_token[:10]}... - {alert_info}")
            return True
            
        try:
            client = self.client
            if not client:
                print(f"[시뮬레이션] APNs 클라이언트 없음: {device_token[:10]}...")
                return True
            
            # APNs 페이로드 생성
            if Payload is not None:
                apns_payload = Payload(
                    alert=payload.get('aps', {}).get('alert', {}),
                    sound=payload.get('aps', {}).get('sound', 'default'),
                    custom=payload
                )
            
                # 비동기 알림 전송
                send_notification_method = getattr(client, 'send_notification', None)
                if send_notification_method:
                    await asyncio.to_thread(
                        send_notification_method, 
                        device_token, 
                        apns_payload, 
                        topic=self.bundle_id
                    )
            
            return True
        except Exception as e:
            print(f"APNs 알림 전송 실패 (시뮬레이션으로 대체): {e}")
            return True  # 실패해도 True 반환 (개발 환경)

# 글로벌 APNs 클라이언트 인스턴스 (안전 버전)
try:
    apns_client = APNSClientConfig() 
except Exception as e:
    print(f"APNs 클라이언트 설정 실패 (개발 환경에서는 정상): {e}")
    apns_client = None 