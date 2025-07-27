from typing import Dict, Any, Optional
import aiohttp
import json

class StockService:
    """주식 서비스"""
    
    def __init__(self):
        """초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def get_stock_price(self, symbol: str) -> Optional[float]:
        """주식 가격 조회"""
        # Yahoo Finance API URL
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    # 현재가 추출
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            return float(result['meta']['regularMarketPrice'])
                    
                    return None
        except Exception:
            return None
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """주식 정보 조회"""
        # Yahoo Finance API URL
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        meta = result.get('meta', {})
                        
                        return {
                            'symbol': symbol,
                            'price': meta.get('regularMarketPrice'),
                            'change': meta.get('regularMarketChange'),
                            'change_percent': meta.get('regularMarketChangePercent'),
                            'volume': meta.get('regularMarketVolume'),
                            'market_cap': meta.get('marketCap'),
                            'currency': meta.get('currency')
                        }
                    
                    return None
        except Exception:
            return None 