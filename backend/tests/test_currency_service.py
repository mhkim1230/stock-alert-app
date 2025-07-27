import pytest
import uuid
from datetime import datetime, timedelta
import asyncio

from src.services.currency_service import CurrencyService
from src.models.database import User, CurrencyAlert
import peewee

class TestCurrencyService:
    @pytest.fixture(scope="function")
    def db(self):
        """테스트용 데이터베이스 설정"""
        # 테스트 데이터베이스 초기화
        test_db = peewee.SqliteDatabase(':memory:')
        
        # 모델에 테스트 데이터베이스 바인딩
        User._meta.database = test_db
        CurrencyAlert._meta.database = test_db
        
        # 테이블 생성
        test_db.create_tables([User, CurrencyAlert])
        
        yield test_db
        
        # 테이블 삭제
        test_db.drop_tables([User, CurrencyAlert])
        test_db.close()
    
    @pytest.fixture(scope="function")
    def currency_service(self):
        """CurrencyService 인스턴스 생성"""
        return CurrencyService()
    
    @pytest.fixture(scope="function")
    def test_user(self, db):
        """테스트용 사용자 생성"""
        user = User.create(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password"
        )
        return user
    
    @pytest.mark.asyncio
    async def test_get_current_exchange_rate(self):
        """현재 환율 조회 테스트"""
        service = CurrencyService()
        
        # USD to KRW 환율 조회
        rate = await service.get_current_exchange_rate('USD', 'KRW')
        
        # 기본 검증
        assert rate is not None, "환율 조회 실패"
        assert isinstance(rate, float), "환율은 float 타입이어야 함"
        assert rate > 0, "환율은 양수여야 함"
        
        print(f"USD to KRW 현재 환율: {rate}")

    def test_get_historical_rates(self):
        """과거 환율 데이터 조회 테스트"""
        service = CurrencyService()
        
        # 과거 환율 데이터 조회
        historical_rates = service.get_historical_rates('USD', 'KRW', days=30)
        
        # 기본 검증
        assert len(historical_rates) == 30, "30일치 데이터가 생성되어야 함"
        
        for rate_data in historical_rates:
            assert 'date' in rate_data, "각 데이터에 날짜가 포함되어야 함"
            assert 'rate' in rate_data, "각 데이터에 환율이 포함되어야 함"
            assert isinstance(rate_data['rate'], float), "환율은 float 타입이어야 함"
            assert rate_data['rate'] > 0, "환율은 양수여야 함"
        
        print("과거 환율 데이터 생성 성공")

    def test_service_initialization(self):
        """서비스 초기화 테스트"""
        service = CurrencyService()
        
        assert service is not None, "서비스 초기화 실패"
        print("서비스 초기화 성공")

    @pytest.mark.asyncio
    async def test_create_currency_alert_success(self, test_user):
        """환율 알림 생성 성공 테스트"""
        service = CurrencyService()
        
        alert = await service.create_currency_alert(
            user_id=test_user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above"
        )
        
        assert alert is not None
        assert alert.base_currency == "USD"
        assert alert.target_currency == "KRW"
        assert alert.target_rate == 1300.0
        assert alert.condition == "above"
        assert alert.is_active is True

    @pytest.mark.asyncio
    async def test_create_currency_alert_invalid_currency(self, test_user):
        """잘못된 통화 코드로 알림 생성 실패 테스트"""
        service = CurrencyService()
        
        with pytest.raises(ValueError, match="유효하지 않은 통화 코드"):
            await service.create_currency_alert(
                user_id=test_user.id,
                base_currency="INVALID",
                target_currency="KRW",
                target_rate=1300.0,
                condition="above"
            )

    @pytest.mark.asyncio
    async def test_create_currency_alert_invalid_condition(self, test_user):
        """잘못된 조건으로 알림 생성 실패 테스트"""
        service = CurrencyService()
        
        with pytest.raises(ValueError, match="유효하지 않은 알림 조건"):
            await service.create_currency_alert(
                user_id=test_user.id,
                base_currency="USD",
                target_currency="KRW",
                target_rate=1300.0,
                condition="invalid_condition"
            )

    @pytest.mark.asyncio
    async def test_get_user_currency_alerts(self, test_user):
        """사용자의 환율 알림 조회 테스트"""
        service = CurrencyService()
        
        # 여러 알림 생성
        await service.create_currency_alert(
            user_id=test_user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above"
        )
        
        await service.create_currency_alert(
            user_id=test_user.id,
            base_currency="EUR",
            target_currency="USD",
            target_rate=1.1,
            condition="below"
        )
        
        # 알림 조회
        alerts = await service.get_user_currency_alerts(test_user.id)
        
        assert len(alerts) == 2
        assert {alert.base_currency for alert in alerts} == {"USD", "EUR"}

    @pytest.mark.asyncio
    async def test_update_currency_alert(self, test_user):
        """환율 알림 업데이트 테스트"""
        service = CurrencyService()
        
        # 알림 생성
        alert = await service.create_currency_alert(
            user_id=test_user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above"
        )
        
        # 알림 업데이트
        updated_alert = await service.update_currency_alert(
            alert_id=alert.id,
            user_id=test_user.id,
            target_rate=1350.0,
            condition="below",
            is_active=False
        )
        
        assert updated_alert.target_rate == 1350.0
        assert updated_alert.condition == "below"
        assert updated_alert.is_active is False

    @pytest.mark.asyncio
    async def test_delete_currency_alert(self, test_user):
        """환율 알림 삭제 테스트"""
        service = CurrencyService()
        
        # 알림 생성
        alert = await service.create_currency_alert(
            user_id=test_user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above"
        )
        
        # 알림 삭제
        await service.delete_currency_alert(
            alert_id=alert.id,
            user_id=test_user.id
        )
        
        # 삭제 확인
        with pytest.raises(Exception):
            CurrencyAlert.get_by_id(alert.id)

    @pytest.mark.asyncio
    async def test_check_currency_alerts(self, test_user):
        """환율 알림 조건 확인 테스트"""
        service = CurrencyService()
        
        # 현재 환율 기반 알림 생성
        current_usd_krw = await service.get_current_exchange_rate("USD", "KRW")

        alert = await service.create_currency_alert(
            user_id=test_user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=current_usd_krw * 1.1,  # 10% 높은 환율
            condition="above"
        )
        
        assert alert is not None 

    def test_get_exchange_rate(self, currency_service):
        """
        환율 조회 테스트
        - 주요 통화 쌍 검증
        """
        test_currency_pairs = [
            ('USD', 'KRW'),
            ('EUR', 'USD'),
            ('JPY', 'GBP'),
            ('AUD', 'CAD')
        ]
        
        for base, target in test_currency_pairs:
            rate = currency_service._get_exchange_rate(base, target)
            
            assert rate is not None, f"{base}->{target} 환율 조회 실패"
            assert isinstance(rate, float), f"{base}->{target} 환율은 실수여야 합니다"
            assert rate > 0, f"{base}->{target} 환율은 양수여야 합니다"

    def test_convert_currency(self, currency_service):
        """
        통화 변환 테스트
        - 다양한 금액 및 통화 쌍 검증
        """
        test_conversions = [
            (100, 'USD', 'KRW'),
            (50, 'EUR', 'USD'),
            (1000, 'JPY', 'GBP')
        ]
        
        for amount, base, target in test_conversions:
            converted = currency_service.convert_currency(amount, base, target)
            
            assert converted is not None, f"{amount} {base}->{target} 변환 실패"
            assert isinstance(converted, float), f"변환 결과는 실수여야 합니다"
            assert converted > 0, f"변환 결과는 양수여야 합니다"

    def test_supported_currencies(self, currency_service):
        """
        지원되는 통화 목록 테스트
        - 통화 목록 구조 검증
        """
        supported = currency_service.get_supported_currencies()
        
        assert isinstance(supported, dict), "통화 목록은 딕셔너리여야 합니다"
        assert len(supported) > 0, "최소 1개 이상의 통화가 지원되어야 합니다"
        
        for code, name in supported.items():
            assert isinstance(code, str), "통화 코드는 문자열이어야 합니다"
            assert isinstance(name, str), "통화 이름은 문자열이어야 합니다"
            assert len(code) == 3, "통화 코드는 3자리여야 합니다"

    def test_historical_rates(self, currency_service):
        """
        과거 환율 조회 테스트
        - 특정 날짜 환율 검증
        """
        base_currency = 'USD'
        target_currencies = ['EUR', 'JPY', 'GBP']
        test_date = datetime.now() - timedelta(days=30)
        
        historical_rates = currency_service.get_historical_rates(
            base_currency, 
            target_currencies, 
            test_date
        )
        
        assert isinstance(historical_rates, dict), "과거 환율은 딕셔너리여야 합니다"
        
        for target in target_currencies:
            assert target in historical_rates, f"{target} 환율 정보 누락"
            rate = historical_rates[target]
            
            assert isinstance(rate, float), f"{target} 환율은 실수여야 합니다"
            assert rate > 0, f"{target} 환율은 양수여야 합니다"

    def test_caching_mechanism(self, currency_service):
        """
        캐싱 메커니즘 테스트
        - 연속 조회 시 캐시 동작 검증
        """
        base, target = 'USD', 'KRW'
        
        # 첫 번째 조회
        first_rate = currency_service._get_exchange_rate(base, target)
        
        # 캐시된 두 번째 조회
        second_rate = currency_service._get_exchange_rate(base, target)
        
        assert first_rate == second_rate, "캐싱 메커니즘 작동 실패"

    def test_error_handling(self, currency_service):
        """
        오류 처리 테스트
        - 존재하지 않는 통화 코드
        """
        # 존재하지 않는 통화 코드
        invalid_conversions = [
            (100, 'XYZ', 'ABC'),
            (50, 'USD', 'ZZZ')
        ]
        
        for amount, base, target in invalid_conversions:
            converted = currency_service.convert_currency(amount, base, target)
            assert converted is None, f"잘못된 통화 코드 {base}->{target} 변환 오류" 