import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from jose.exceptions import JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
import bcrypt
from sqlalchemy.sql import text
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import User, DeviceToken
from src.config.logging_config import get_logger
from src.utils.logging_decorator import log_function

logger = get_logger(__name__)

# JWT 토큰 설정
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class TokenData(BaseModel):
    username: Optional[str] = None

class AuthService:
    """인증 서비스"""
    
    SECRET_KEY = SECRET_KEY
    ALGORITHM = ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def __init__(self):
        """초기화"""
        pass
    
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def register(self, db: AsyncSession, username: str, email: str, password: str) -> User:
        """사용자 등록"""
        # 중복 확인
        if await self.get_user_by_username(db, username):
            raise ValueError("Username already exists")
        if await self.get_user_by_email(db, email):
            raise ValueError("Email already exists")
        
        # 비밀번호 해시
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # 사용자 생성
        user = User(
            username=username,
            email=email,
            password_hash=password_hash.decode()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> str:
        """사용자 인증 및 토큰 생성"""
        user = await self.get_user_by_username(db, username)
        if not user:
            raise ValueError("Invalid username or password")
        
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise ValueError("Invalid username or password")
        
        # JWT 토큰 생성
        access_token = await self._create_access_token(
            data={"sub": user.username},
            db=db,
            expires_delta=timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return access_token
    
    async def _create_access_token(self, data: Dict[str, Any], db: AsyncSession, expires_delta: Optional[timedelta] = None) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        
        # 만료 시간 설정
        if expires_delta:
            expire = await db.execute(
                text("SELECT SYSTIMESTAMP + :interval FROM DUAL"),
                {"interval": f"INTERVAL '{expires_delta.total_seconds()}' SECOND"}
            )
            expire = expire.scalar()
        else:
            expire = await db.execute(text("SELECT SYSTIMESTAMP + INTERVAL '30' MINUTE FROM DUAL"))
            expire = expire.scalar()
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt.decode('utf-8') if isinstance(encoded_jwt, bytes) else encoded_jwt
    
    async def verify_token(self, db: AsyncSession, token: str) -> User:
        """토큰 검증 및 사용자 반환"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                raise ValueError("Invalid token")
            
            user = await self.get_user_by_username(db, username)
            if user is None:
                raise ValueError("User not found")
            
            return user
            
        except JWTError:
            raise ValueError("Invalid token")
    
    async def register_device_token(self, db: AsyncSession, token: str, device_type: Optional[str] = None) -> DeviceToken:
        """디바이스 토큰 등록"""
        device_token = DeviceToken(
            token=token,
            device_type=device_type
        )
        db.add(device_token)
        await db.commit()
        await db.refresh(device_token)
        
        return device_token

    def _hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, username: str, email: str, password: str) -> User:
        """사용자 생성"""
        # 중복 사용자 확인
        existing_user = User.select().where(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            raise ValueError("이미 존재하는 사용자명 또는 이메일입니다.")

        # 비밀번호 해싱
        hashed_password = self._hash_password(password)

        # 사용자 생성
        new_user = User.create(
            username=username,
            email=email,
            password_hash=hashed_password,
            is_active=True
        )

        return new_user

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """현재 사용자 정보 조회"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: Optional[str] = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="토큰에서 사용자를 식별할 수 없습니다.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            user = User.select().where(User.id == uuid.UUID(user_id)).first()
            
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="사용자를 찾을 수 없습니다.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return user
        
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 유효하지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    async def refresh_token(self, db: AsyncSession, token: str) -> str:
        """토큰 갱신"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: Optional[str] = payload.get("sub")
            
            if user_id is None:
                raise ValueError("유효하지 않은 토큰입니다.")
            
            # 새 토큰 생성
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            new_token = await self._create_access_token(
                data={"sub": user_id}, 
                db=db,
                expires_delta=access_token_expires
            )
            
            return new_token
        
        except JWTError:
            raise ValueError("토큰 갱신에 실패했습니다.")

    async def update_user_profile(
        self, 
        user_id: uuid.UUID, 
        username: Optional[str] = None, 
        email: Optional[str] = None
    ) -> User:
        """사용자 프로필 업데이트"""
        user = User.select().where(User.id == user_id).first()
        
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 사용자명 중복 확인
        if username:
            existing_username = User.select().where(
                (User.username == username) & (User.id != user_id)
            ).first()
            
            if existing_username:
                raise ValueError("이미 존재하는 사용자명입니다.")
            
            user.username = username
        
        # 이메일 중복 확인
        if email:
            existing_email = User.select().where(
                (User.email == email) & (User.id != user_id)
            ).first()
            
            if existing_email:
                raise ValueError("이미 존재하는 이메일입니다.")
            
            user.email = email
        
        # 업데이트 및 저장
        user.save()
        
        return user

    @log_function(log_args=True)
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        평문 비밀번호와 해시된 비밀번호 검증
        
        Args:
            plain_password (str): 입력된 평문 비밀번호
            hashed_password (str): 저장된 해시된 비밀번호
        
        Returns:
            bool: 비밀번호 일치 여부
        """
        try:
            is_valid = pwd_context.verify(plain_password, hashed_password)
            logger.info(f"Password verification result: {is_valid}")
            return is_valid
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @log_function(log_args=True)
    def get_password_hash(self, password: str) -> str:
        """
        비밀번호 해싱
        
        Args:
            password (str): 해시할 평문 비밀번호
        
        Returns:
            str: 해시된 비밀번호
        """
        try:
            hashed_password = pwd_context.hash(password)
            logger.info("Password hashed successfully")
            return hashed_password
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise

    @log_function(log_args=True, log_return=True)
    async def create_access_token(self, data: Dict[str, Any], db: AsyncSession, expires_delta: Optional[timedelta] = None) -> str:
        """
        JWT 액세스 토큰 생성
        
        Args:
            data (Dict[str, Any]): 토큰에 포함될 데이터
            db (AsyncSession): 데이터베이스 세션
            expires_delta (Optional[timedelta], optional): 토큰 만료 시간. 기본값은 30분
        
        Returns:
            str: 생성된 JWT 토큰
        """
        try:
            to_encode = data.copy()
            
            # 만료 시간 설정
            if expires_delta:
                result = await db.execute(
                    text("SELECT SYSTIMESTAMP + :interval FROM DUAL"),
                    {"interval": f"INTERVAL '{expires_delta.total_seconds()}' SECOND"}
                )
                expire = result.scalar()
            else:
                result = await db.execute(text("SELECT SYSTIMESTAMP + INTERVAL '30' MINUTE FROM DUAL"))
                expire = result.scalar()
            
            to_encode.update({"exp": expire})
            
            # 토큰 생성
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            
            logger.info(f"Access token created for user: {data.get('sub', 'Unknown')}")
            return encoded_jwt.decode('utf-8') if isinstance(encoded_jwt, bytes) else encoded_jwt
        
        except Exception as e:
            logger.error(f"Access token creation error: {e}")
            raise

    @log_function(log_args=True, log_return=True)
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        JWT 토큰 디코딩 및 검증
        
        Args:
            token (str): 디코딩할 JWT 토큰
        
        Returns:
            Dict[str, Any]: 디코딩된 토큰 페이로드
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            username: Optional[str] = payload.get("sub")
            if username is None:
                logger.warning("Token does not contain subject (username)")
                raise ValueError("Could not validate credentials")
            
            token_data = TokenData(username=username)
            
            logger.info(f"Token decoded successfully for user: {token_data.username}")
            return payload
        
        except JWTError as e:
            logger.error(f"Token decoding error: {e}")
            raise ValueError("Could not validate credentials")
        except Exception as e:
            logger.error(f"Unexpected error during token decoding: {e}")
            raise
    
    @classmethod
    async def create_user_token(cls, db: AsyncSession, user_id: str, email: str) -> Dict[str, str]:
        """사용자 인증 토큰 생성"""
        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await cls.create_access_token(
            data={
                "sub": str(user_id),
                "email": email
            }, 
            db=db,
            expires_delta=access_token_expires
        )
        
        # 리프레시 토큰 생성 (선택적)
        refresh_token_expires = timedelta(days=7)
        refresh_token = await cls.create_access_token(
            data={
                "sub": str(user_id),
                "type": "refresh"
            }, 
            db=db,
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @classmethod
    def validate_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """토큰 유효성 검사"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            # 토큰 만료 또는 검증 실패
            return None 

# 전역 AuthService 인스턴스
auth_service = AuthService()

# get_current_user를 모듈 레벨에서 사용할 수 있도록 export
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """현재 사용자 정보 조회 (모듈 레벨 함수)"""
    return await auth_service.get_current_user(token) 