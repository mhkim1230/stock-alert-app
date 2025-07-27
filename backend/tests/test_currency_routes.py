import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.models.database import User, CurrencyAlert
from src.services.auth_service import AuthService

class TestCurrencyRoutes:
    @pytest.fixture(scope="function")
    def client(self):
        """FastAPI 테스트 클라이언트 생성"""
        return TestClient(app)
    
    @pytest.fixture(scope="function")
    def auth_service(self):
        """인증 서비스 생성"""
        return AuthService()
    
    @pytest.fixture(scope="function")
    def test_user(self, auth_service):
        """테스트용 사용자 생성"""
        # 테스트 사용자 생성 및 토큰 발급
        username = "test_currency_user"
        password = "testpassword123"
        email = "currency_test@example.com"
        
        # 사용자 생성
        user = User.create(
            username=username,
            email=email,
            password_hash=auth_service.get_password_hash(password)
        )
        
        # 액세스 토큰 생성
        access_token = auth_service.create_access_token(user.id)
        
        return {
            "user": user,
            "access_token": access_token
        }
    
    def test_create_currency_alert(self, client, test_user):
        """환율 알림 생성 API 테스트"""
        # 요청 페이로드
        payload = {
            "base_currency": "USD",
            "target_currency": "KRW",
            "target_rate": 1300.0,
            "condition": "above"
        }
        
        # API 요청
        response = client.post(
            "/currency/alerts", 
            json=payload,
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # 응답 검증
        assert response.status_code == 200
        
        # 응답 데이터 검증
        data = response.json()
        assert data["base_currency"] == "USD"
        assert data["target_currency"] == "KRW"
        assert data["target_rate"] == 1300.0
        assert data["condition"] == "above"
        assert data["is_active"] is True
    
    def test_create_currency_alert_invalid_currency(self, client, test_user):
        """잘못된 통화 코드로 알림 생성 실패 테스트"""
        # 요청 페이로드
        payload = {
            "base_currency": "INVALID",
            "target_currency": "KRW",
            "target_rate": 1300.0,
            "condition": "above"
        }
        
        # API 요청
        response = client.post(
            "/currency/alerts", 
            json=payload,
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # 응답 검증
        assert response.status_code == 400
        assert "유효하지 않은 통화 코드" in response.json()["detail"]
    
    def test_get_user_currency_alerts(self, client, test_user):
        """사용자의 환율 알림 조회 API 테스트"""
        # 테스트용 알림 생성
        CurrencyAlert.create(
            user=test_user['user'],
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above"
        )
        
        CurrencyAlert.create(
            user=test_user['user'],
            base_currency="EUR",
            target_currency="USD",
            target_rate=1.1,
            condition="below"
        )
        
        # API 요청
        response = client.get(
            "/currency/alerts",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # 응답 검증
        assert response.status_code == 200
        
        # 데이터 검증
        alerts = response.json()
        assert len(alerts) == 2
        assert {alert["base_currency"] for alert in alerts} == {"USD", "EUR"}
    
    def test_update_currency_alert(self, client, test_user):
        """환율 알림 업데이트 API 테스트"""
        # 테스트용 알림 생성
        alert = CurrencyAlert.create(
            user=test_user['user'],
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above"
        )
        
        # 요청 페이로드
        payload = {
            "target_rate": 1350.0,
            "condition": "below",
            "is_active": False
        }
        
        # API 요청
        response = client.put(
            f"/currency/alerts/{alert.id}", 
            json=payload,
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # 응답 검증
        assert response.status_code == 200
        
        # 데이터 검증
        data = response.json()
        assert data["target_rate"] == 1350.0
        assert data["condition"] == "below"
        assert data["is_active"] is False
    
    def test_delete_currency_alert(self, client, test_user):
        """환율 알림 삭제 API 테스트"""
        # 테스트용 알림 생성
        alert = CurrencyAlert.create(
            user=test_user['user'],
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above"
        )
        
        # API 요청
        response = client.delete(
            f"/currency/alerts/{alert.id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # 응답 검증
        assert response.status_code == 204
        
        # 삭제 확인
        deleted_alert = CurrencyAlert.select().where(CurrencyAlert.id == alert.id).first()
        assert deleted_alert is None
    
    def test_get_exchange_rate(self, client):
        """현재 환율 조회 API 테스트"""
        # 테스트 통화 쌍
        test_cases = [
            ("USD", "KRW"),
            ("EUR", "USD"),
            ("JPY", "KRW"),
            ("BTC", "USD")
        ]
        
        for base, target in test_cases:
            # API 요청
            response = client.get(f"/currency/rate/{base}/{target}")
            
            # 응답 검증
            assert response.status_code == 200
            
            # 데이터 검증
            data = response.json()
            assert data["base_currency"] == base
            assert data["target_currency"] == target
            assert "rate" in data
            assert isinstance(data["rate"], (int, float))
            assert data["rate"] > 0 