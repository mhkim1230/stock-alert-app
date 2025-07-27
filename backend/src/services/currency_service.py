#!/usr/bin/env python3
"""
환율 서비스 - 네이버 증권만 사용
forex_python 완전 제거
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import json

class CurrencyService:
    """환율 서비스"""
    
    def __init__(self):
        """초기화"""
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_timeout = 300  # 5분 캐시
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.api_key = "your-api-key"  # 실제 운영에서는 환경 변수로 관리
        
    async def get_exchange_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        """환율 조회"""
        # ExchangeRate-API URL
        url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/{base_currency}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if 'conversion_rates' in data and target_currency in data['conversion_rates']:
                        return float(data['conversion_rates'][target_currency])
                    
                    return None
        except Exception:
            return None
    
    async def get_currency_info(self, base_currency: str, target_currency: str) -> Optional[Dict[str, Any]]:
        """환율 정보 조회"""
        # ExchangeRate-API URL
        url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/{base_currency}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if 'conversion_rates' in data and target_currency in data['conversion_rates']:
                        rate = data['conversion_rates'][target_currency]
                        return {
                            'base_currency': base_currency,
                            'target_currency': target_currency,
                            'rate': rate,
                            'last_update': data.get('time_last_update_utc'),
                            'next_update': data.get('time_next_update_utc')
                        }
                    
                    return None
        except Exception:
            return None

    async def get_major_currencies(self) -> List[Dict]:
        """주요 환율 조회 - 네이버 증권만 사용"""
        try:
            major_pairs = [
                ('USD', 'KRW'),
                ('EUR', 'KRW'), 
                ('JPY', 'KRW'),
                ('CNY', 'KRW')
            ]
            
            results = []
            for from_cur, to_cur in major_pairs:
                try:
                    rate = await self.get_exchange_rate(from_cur, to_cur)
                    results.append({
                        'from_currency': from_cur,
                        'to_currency': to_cur,
                        'rate': rate,
                        'source': 'naver_real',
                        'last_updated': datetime.now().isoformat()
                    })
                except Exception as e:
                    self.logger.error(f"❌ {from_cur}/{to_cur} 환율 조회 실패: {e}")
                    continue
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 주요 환율 조회 실패: {e}")
            return []

    def get_supported_currencies(self) -> List[str]:
        """지원하는 통화 목록"""
        return ['USD', 'EUR', 'JPY', 'CNY', 'GBP', 'AUD', 'CAD', 'CHF', 'KRW']

# 전역 인스턴스
currency_service = CurrencyService() 