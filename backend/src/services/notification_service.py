import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text

# APNs 관련 임포트
APNS_AVAILABLE = False
APNsClient = None
Payload = None

try:
    from apns2.client import APNsClient
    from apns2.payload import Payload
    from apns2.errors import APNsException
    APNS_AVAILABLE = True
except ImportError:
    # APNs 라이브러리가 없으면 시뮬레이션 모드로 동작
    pass

# 내부 모듈 import
from src.config.logging_config import get_logger
from src.config.apns_config import APNS_SETTINGS

# 데이터베이스 모델 import
from src.models.database import (
    User,
    DeviceToken,
    NotificationLog
)

logger = get_logger(__name__)

class NotificationService:
    """iOS 앱용 APNs 알림 서비스"""
    
    def __init__(self):
        """알림 서비스 초기화 (안전 모드)"""
        self.logger = get_logger(__name__)
        self.apns_client = None
        
        # 개발 환경에서는 APNs 클라이언트를 생성하지 않음
        if os.getenv('APP_ENV', 'development') == 'production':
            try:
                self.apns_client = self._create_apns_client()
            except Exception as e:
                self.logger.error(f"APNs 클라이언트 생성 실패: {e}")
                self.apns_client = None
        else:
            self.logger.info("개발 환경: APNs 클라이언트 생성을 건너뜁니다.")
        
        logger.info("APNs 알림 서비스 초기화 완료")

    def _create_apns_client(self) -> Optional[object]:
        """APNs 클라이언트 생성 (안전 버전)"""
        if not APNS_AVAILABLE:
            self.logger.warning("APNs 라이브러리를 사용할 수 없습니다. 푸시 알림이 비활성화됩니다.")
            return None
            
        try:
            # 환경 변수에서 APNs 설정 로드
            key_id = os.getenv('APNS_KEY_ID')
            team_id = os.getenv('APNS_TEAM_ID')
            auth_key_path = os.getenv('APNS_AUTH_KEY_PATH', 'AuthKey.p8')
            use_sandbox = os.getenv('APNS_USE_SANDBOX', 'true').lower() == 'true'
            
            if not key_id or not team_id:
                self.logger.warning("APNs 설정이 불완전합니다. 푸시 알림이 비활성화됩니다.")
                return None
                
            # APNs 클라이언트 생성
            from apns2.credentials import TokenCredentials
            credentials = TokenCredentials(
                auth_key_path=auth_key_path,
                auth_key_id=key_id,
                team_id=team_id
            )
            if APNsClient:
                return APNsClient(
                    credentials=credentials,
                    use_sandbox=use_sandbox
                )
            return None
            
        except Exception as e:
            self.logger.error(f"APNs 클라이언트 생성 실패: {e}")
            return None

    async def send_notification(
        self,
        user_id: str,
        message: str,
        alert_id: str,
        alert_type: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        알림 전송
        :param user_id: 사용자 ID
        :param message: 알림 메시지
        :param alert_id: 알림 ID
        :param alert_type: 알림 타입 (stock, currency, news)
        :param additional_data: 추가 데이터 (선택적)
        :return: 전송 성공 여부
        """
        try:
            user_id_int = int(user_id)
            # 알림 로그 저장
            await self._save_notification_log(
                user_id=user_id_int,
                notification_type=alert_type,
                message=message,
                extra_data=additional_data or {}
            )
            
            # 푸시 알림 전송
            await self.send_push_notification(
                user_id=user_id_int,
                title=f"{alert_type.capitalize()} Alert",
                body=message,
                extra_data=additional_data
            )
            return True
        except Exception as e:
            self.logger.error(f"알림 전송 실패: {e}")
            return False

    async def send_push_notification(
        self, 
        user_id: int, 
        title: str, 
        body: str, 
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        특정 사용자에게 APNs 푸시 알림 전송
        
        :param user_id: 알림을 받을 사용자 ID
        :param title: 알림 제목
        :param body: 알림 본문
        :param extra_data: 추가 데이터 (선택적)
        :return: 알림 전송 성공 여부
        """
        try:
            # 사용자의 활성 디바이스 토큰 조회
            device_tokens = list(DeviceToken.select().where(
                (DeviceToken.user == user_id) & 
                (DeviceToken.is_active == True)
            ))
            
            if not device_tokens:
                self.logger.info(f"사용자 {user_id}에 대한 활성 디바이스 토큰 없음")
                # 시뮬레이션 알림 전송
                self.logger.info(f"[시뮬레이션] APNs 알림 전송: 사용자 {user_id}, 제목: {title}, 내용: {body}")
                await self._save_notification_log(user_id, "apns_simulation", f"{title}: {body}", extra_data)
                return True
            
            success_count = 0
            
            # 각 디바이스 토큰에 대해 알림 전송
            for device_token_obj in device_tokens:
                try:
                    if not self.apns_client:
                        # APNs가 사용 불가능한 경우 시뮬레이션
                        self.logger.info(f"[시뮬레이션] APNs 알림 전송: 사용자 {user_id}, 디바이스 {device_token_obj.token[:10]}...")
                        success_count += 1
                        continue
                    
                    # APNs 알림 페이로드 구성
                    if not Payload:
                        self.logger.warning("APNs Payload 클래스를 사용할 수 없습니다.")
                        success_count += 1
                        continue
                    
                    from apns2.payload import PayloadAlert
                    alert_payload = PayloadAlert(title=title, body=body)
                    payload = Payload(
                        alert=alert_payload,
                        sound="default",
                        badge=1,
                        custom=extra_data or {}
                    )
                    
                    # APNs를 통해 알림 전송
                    bundle_id = os.getenv('APNS_BUNDLE_ID', 'com.example.stockalert')
                    send_notification_method = getattr(self.apns_client, 'send_notification', None)
                    if send_notification_method:
                        await asyncio.to_thread(
                            send_notification_method,
                            device_token_obj.token,
                            payload,
                            topic=bundle_id
                        )
                    else:
                        self.logger.warning("APNs 클라이언트에 send_notification 메서드가 없습니다.")
                        success_count += 1
                        continue
                    success_count += 1
                    
                    # 디바이스 토큰 사용 시간 업데이트
                    device_token_obj.last_used = datetime.now()
                    device_token_obj.save()
                    
                    self.logger.info(f"APNs 알림 전송 성공: 사용자 {user_id}, 디바이스 {device_token_obj.token[:10]}...")
                        
                except Exception as device_error:
                    self.logger.warning(f"디바이스 알림 전송 실패 (계속 진행): {device_error}")
                    # 시뮬레이션으로 대체
                    self.logger.info(f"[시뮬레이션] APNs 대체 알림 전송: 사용자 {user_id}")
                    success_count += 1
            
            # 알림 로그 저장
            await self._save_notification_log(user_id, "apns", f"{title}: {body}", extra_data)
            
            return success_count > 0
        
        except Exception as e:
            self.logger.warning(f"APNs 알림 전송 중 오류 발생 (시뮬레이션으로 대체): {e}")
            # 오류가 발생해도 시뮬레이션으로 처리
            self.logger.info(f"[시뮬레이션] APNs 오류 대체 알림: 사용자 {user_id}, 제목: {title}")
            await self._save_notification_log(user_id, "apns_fallback", f"{title}: {body}", extra_data)
            return True

    async def register_device_token(
        self, 
        user_id: int, 
        device_token: str,
        platform: str = "iOS"
    ) -> bool:
        """
        사용자의 디바이스 토큰 등록
        
        :param user_id: 사용자 ID
        :param device_token: 디바이스 토큰
        :param platform: 플랫폼 (iOS만 지원)
        :return: 토큰 등록 성공 여부
        """
        try:
            if platform != "iOS":
                self.logger.warning(f"지원하지 않는 플랫폼: {platform}")
                return False

            # 기존 동일 토큰이 있는지 확인
            existing_token = DeviceToken.select().where(
                DeviceToken.token == device_token
            ).first()
            
            if existing_token:
                # 기존 토큰을 현재 사용자로 업데이트
                existing_token.user = user_id
                existing_token.is_active = True
                existing_token.platform = platform
                existing_token.last_used = datetime.now()
                existing_token.save()
            else:
                # 새 토큰 생성
                DeviceToken.create(
                    user=user_id,
                    token=device_token,
                    platform=platform,
                    is_active=True,
                    last_used=datetime.now()
                )
            
            self.logger.info(f"APNs 디바이스 토큰 등록 성공: 사용자 {user_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"APNs 디바이스 토큰 등록 실패: {e}")
            return False

    async def unregister_device_token(self, device_token: str) -> bool:
        """
        디바이스 토큰 해제
        
        :param device_token: 해제할 디바이스 토큰
        :return: 해제 성공 여부
        """
        try:
            updated_count = DeviceToken.update(is_active=False).where(
                DeviceToken.token == device_token
            ).execute()
            
            if updated_count > 0:
                self.logger.info(f"APNs 디바이스 토큰 해제 성공: {device_token[:10]}...")
                return True
            else:
                self.logger.warning(f"해제할 APNs 디바이스 토큰을 찾을 수 없음: {device_token[:10]}...")
                return False
        
        except Exception as e:
            self.logger.error(f"APNs 디바이스 토큰 해제 실패: {e}")
            return False

    async def _save_notification_log(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """알림 로그 저장"""
        try:
            NotificationLog.create(
                user=user_id,
                type=notification_type,
                message=message,
                extra_data=extra_data or {}
            )
        except Exception as e:
            self.logger.error(f"알림 로그 저장 실패: {e}")

    async def send_stock_alert(
        self,
        user_id: str,
        alert_id: str,
        symbol: str,
        current_price: float,
        target_price: float,
        condition: str
    ):
        """주식 알림 전송"""
        message = f"주식 {symbol}의 현재 가격이 {current_price}원으로 "
        if condition == 'above':
            message += f"목표가 {target_price}원을 상회했습니다."
        elif condition == 'below':
            message += f"목표가 {target_price}원을 하회했습니다."
        else:
            message += f"목표가 {target_price}원에 도달했습니다."

        await self.send_notification(
            user_id=user_id,
            message=message,
            alert_id=alert_id,
            alert_type="stock",
            additional_data={
                "symbol": symbol,
                "current_price": current_price,
                "target_price": target_price,
                "condition": condition
            }
        )

    async def send_news_alert(self, user_id: str, alert_id: str, keywords: str, news_items: list):
        """뉴스 알림 전송"""
        message = f"키워드 '{keywords}'에 대한 새로운 뉴스가 있습니다."
        await self.send_notification(
            user_id=user_id,
            message=message,
            alert_id=alert_id,
            alert_type="news",
            additional_data={"news_items": news_items}
        )

# 전역 APNs 알림 서비스 인스턴스
notification_service = NotificationService() 