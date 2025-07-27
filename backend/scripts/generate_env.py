#!/usr/bin/env python3
import os
import secrets
import argparse
import json

def generate_secret_key():
    """안전한 랜덤 시크릿 키 생성"""
    return secrets.token_hex(32)

def create_env_file(output_path, overwrite=False):
    """환경 변수 파일 생성"""
    default_config = {
        "APP_NAME": "StockAlertApp",
        "APP_ENV": "development",
        "DEBUG": "True",
        
        "DATABASE_URL": "sqlite:///stock_alert.db",
        "DATABASE_HOST": "localhost",
        "DATABASE_PORT": "5432",
        "DATABASE_NAME": "stock_alert_db",
        "DATABASE_USER": "",
        "DATABASE_PASSWORD": "",
        
        "SECRET_KEY": generate_secret_key(),
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        
        "NEWSAPI_KEY": "",
        "YFINANCE_API_KEY": "",
        "FOREX_API_KEY": "",
        
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "json",
        
        "CORS_ALLOWED_ORIGINS": "http://localhost:8000,https://localhost:3000",
        "ALLOWED_HOSTS": "localhost,127.0.0.1",
        
        "SMTP_HOST": "",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "SMTP_USE_TLS": "True",
        
        "ENABLE_STOCK_ALERTS": "True",
        "ENABLE_CURRENCY_ALERTS": "True", 
        "ENABLE_NEWS_ALERTS": "True"
    }

    # 파일 존재 여부 확인
    if os.path.exists(output_path) and not overwrite:
        print(f"파일 {output_path}이 이미 존재합니다. 덮어쓰기를 원하면 --overwrite 옵션을 사용하세요.")
        return

    # 환경 변수 파일 생성
    with open(output_path, 'w') as f:
        for key, value in default_config.items():
            f.write(f"{key}={value}\n")

    print(f"환경 변수 파일이 {output_path}에 생성되었습니다.")
    return default_config

def create_json_config(output_path, config, overwrite=False):
    """JSON 설정 파일 생성"""
    if os.path.exists(output_path) and not overwrite:
        print(f"파일 {output_path}이 이미 존재합니다. 덮어쓰기를 원하면 --overwrite 옵션을 사용하세요.")
        return

    with open(output_path, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"JSON 설정 파일이 {output_path}에 생성되었습니다.")

def main():
    parser = argparse.ArgumentParser(description="환경 설정 파일 생성 도구")
    parser.add_argument(
        "--env-path", 
        default=os.path.join(os.path.dirname(__file__), '..', '.env'), 
        help="환경 변수 파일 경로"
    )
    parser.add_argument(
        "--json-path", 
        default=os.path.join(os.path.dirname(__file__), '..', 'config.json'), 
        help="JSON 설정 파일 경로"
    )
    parser.add_argument(
        "--overwrite", 
        action="store_true", 
        help="기존 파일 덮어쓰기"
    )

    args = parser.parse_args()

    # 환경 변수 파일 생성
    config = create_env_file(args.env_path, args.overwrite)
    
    # JSON 설정 파일 생성
    create_json_config(args.json_path, config, args.overwrite)

if __name__ == "__main__":
    main() 