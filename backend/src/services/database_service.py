from passlib.hash import pbkdf2_sha256
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from src.models.database import (
    User, 
    StockAlert, 
    CurrencyAlert,
    Watchlist,
    database
)

class DatabaseService:
    """데이터베이스 서비스 클래스"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해싱"""
        return pbkdf2_sha256.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pbkdf2_sha256.verify(plain_password, hashed_password)
    
    @classmethod
    def create_user(cls, username: str, email: str, password: str) -> User:
        """새로운 사용자 생성"""
        database.connect()
        
        try:
            # 이메일 중복 확인
            existing_user = User.select().where(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                raise ValueError("이미 존재하는 이메일 또는 사용자명입니다.")
            
            # 사용자 생성
            user = User.create(
                username=username,
                email=email,
                password_hash=cls.hash_password(password)
            )
            
            return user
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def authenticate_user(cls, email: str, password: str) -> Optional[User]:
        """사용자 인증"""
        database.connect()
        
        try:
            user = User.select().where(User.email == email).first()
            
            if user and cls.verify_password(password, user.password_hash):
                # 마지막 로그인 시간 업데이트
                user.last_login = datetime.now()
                user.save()
                return user
            
            return None
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def create_stock_alert(
        cls, 
        user_id: uuid.UUID, 
        symbol: str, 
        condition: str, 
        target_price: float
    ) -> StockAlert:
        """주식 알림 생성"""
        database.connect()
        
        try:
            alert = StockAlert.create(
                user_id=user_id,
                symbol=symbol,
                condition=condition,
                target_price=target_price
            )
            
            return alert
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def add_stock_to_watchlist(cls, user_id: int, stock_symbol: str, name: str = None, name_kr: str = None, market: str = None) -> Watchlist:
        """주식 관심종목 추가"""
        database.connect()
        
        try:
            # 이미 존재하는지 확인
            existing = Watchlist.select().where(
                (Watchlist.user == user_id) & 
                (Watchlist.symbol == stock_symbol) & 
                (Watchlist.type == 'stock')
            ).first()
            
            if existing:
                # 이미 존재하면 활성화만 하고 정보 업데이트
                existing.is_active = True
                if name:
                    existing.name = name
                if name_kr:
                    existing.name_kr = name_kr
                if market:
                    existing.market = market
                existing.save()
                return existing
            else:
                # 새로 생성
                watchlist_item = Watchlist.create(
                    user=user_id,
                    symbol=stock_symbol,
                    name=name,
                    name_kr=name_kr,
                    type='stock',
                    market=market
                )
                return watchlist_item
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def add_currency_to_watchlist(cls, user_id: int, currency_symbol: str, name: str = None) -> Watchlist:
        """환율 관심종목 추가"""
        database.connect()
        
        try:
            # 이미 존재하는지 확인
            existing = Watchlist.select().where(
                (Watchlist.user == user_id) & 
                (Watchlist.symbol == currency_symbol) & 
                (Watchlist.type == 'currency')
            ).first()
            
            if existing:
                # 이미 존재하면 활성화만 하고 정보 업데이트
                existing.is_active = True
                if name:
                    existing.name = name
                existing.save()
                return existing
            else:
                # 새로 생성
                watchlist_item = Watchlist.create(
                    user=user_id,
                    symbol=currency_symbol,
                    name=name,
                    type='currency'
                )
                return watchlist_item
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def remove_stock_from_watchlist(cls, user_id: int, stock_symbol: str) -> bool:
        """주식 관심종목 제거"""
        database.connect()
        
        try:
            deleted_count = Watchlist.delete().where(
                (Watchlist.user == user_id) & 
                (Watchlist.symbol == stock_symbol) & 
                (Watchlist.type == 'stock')
            ).execute()
            
            return deleted_count > 0
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def remove_currency_from_watchlist(cls, user_id: int, currency_symbol: str) -> bool:
        """환율 관심종목 제거"""
        database.connect()
        
        try:
            deleted_count = Watchlist.delete().where(
                (Watchlist.user == user_id) & 
                (Watchlist.symbol == currency_symbol) & 
                (Watchlist.type == 'currency')
            ).execute()
            
            return deleted_count > 0
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def get_user_stock_watchlist(cls, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 주식 관심종목 조회"""
        database.connect()
        
        try:
            watchlist_items = Watchlist.select().where(
                (Watchlist.user == user_id) & 
                (Watchlist.type == 'stock') & 
                (Watchlist.is_active == True)
            ).order_by(Watchlist.created_at.desc())
            
            return [
                {
                    'symbol': item.symbol,
                    'name': item.name,
                    'name_kr': item.name_kr,
                    'market': item.market,
                    'created_at': item.created_at.isoformat() if item.created_at else None
                }
                for item in watchlist_items
            ]
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def get_user_currency_watchlist(cls, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 환율 관심종목 조회"""
        database.connect()
        
        try:
            watchlist_items = Watchlist.select().where(
                (Watchlist.user == user_id) & 
                (Watchlist.type == 'currency') & 
                (Watchlist.is_active == True)
            ).order_by(Watchlist.created_at.desc())
            
            return [
                {
                    'symbol': item.symbol,
                    'name': item.name,
                    'created_at': item.created_at.isoformat() if item.created_at else None
                }
                for item in watchlist_items
            ]
        
        except Exception as e:
            raise e
        finally:
            database.close()
    
    @classmethod
    def get_user_full_watchlist(cls, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """사용자의 전체 관심종목 조회 (주식 + 환율)"""
        try:
            stocks = cls.get_user_stock_watchlist(user_id)
            currencies = cls.get_user_currency_watchlist(user_id)
            
            return {
                'stocks': stocks,
                'currencies': currencies,
                'total_count': len(stocks) + len(currencies)
            }
        
        except Exception as e:
            raise e 