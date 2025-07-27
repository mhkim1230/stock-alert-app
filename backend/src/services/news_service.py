#!/usr/bin/env python3
# type: ignore
"""
뉴스 서비스 - 야후 파이낸스 완전 제거, RSS만 사용
"""

import logging
import feedparser
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup
import aiohttp
import json

class NewsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # RSS 피드만 사용 (야후 완전 제거)
        self.rss_feeds = [
            'https://feeds.bloomberg.com/economics/news.rss',
            'https://www.marketwatch.com/rss/topstories',
        ]
        
        # 네이버 뉴스 URL만 사용
        self.news_sources = {
            'naver_finance': 'https://finance.naver.com/news/',
        }

    async def get_latest_news(self, limit: int = 10) -> List[Dict[str, str]]:
        """최신 뉴스 조회 - RSS + 네이버만"""
        try:
            articles = []
            
            # RSS 피드에서 뉴스 수집
            for feed_url in self.rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:limit//len(self.rss_feeds)]:
                        articles.append({
                            'title': str(entry.get('title', '제목 없음')),
                            'summary': str(entry.get('summary', '요약 없음'))[:200] + '...',
                            'url': str(entry.get('link', '')),
                            'published': str(entry.get('published', '')),
                            'source': {'name': str(feed.feed.get('title', 'RSS'))}
                        })
                except Exception as e:
                    self.logger.warning(f"RSS 피드 파싱 실패 {feed_url}: {e}")
                    continue
            
            # 네이버 뉴스 추가 (간단한 파싱만)
            try:
                naver_articles = await self._get_naver_finance_news()
                articles.extend(naver_articles[:5])
            except Exception as e:
                self.logger.warning(f"네이버 뉴스 파싱 실패: {e}")
            
            return articles[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ 뉴스 조회 실패: {e}")
            return []

    async def get_stock_news(self, symbol: str = None) -> List[Dict[str, str]]:
        """주식 뉴스 조회 - RSS + 네이버만"""
        try:
            articles = []
            
            # RSS 피드에서 주식 관련 뉴스 필터링
            for feed_url in self.rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:20]:
                        title = str(entry.get('title', '')).lower()
                        summary = str(entry.get('summary', '')).lower()
                        
                        # 주식/경제 관련 키워드 필터링
                        stock_keywords = ['stock', 'market', 'trading', 'investment', 'economy', 'finance']
                        if symbol:
                            stock_keywords.append(symbol.lower())
                        
                        if any(keyword in title or keyword in summary for keyword in stock_keywords):
                            articles.append({
                                'title': str(entry.get('title', '제목 없음')),
                                'summary': str(entry.get('summary', '요약 없음'))[:200] + '...',
                                'url': str(entry.get('link', '')),
                                'published': str(entry.get('published', '')),
                                'source': {'name': str(feed.feed.get('title', 'RSS'))}
                            })
                except Exception as e:
                    self.logger.warning(f"주식 뉴스 RSS 파싱 실패 {feed_url}: {e}")
                    continue
            
            return articles[:10]
            
        except Exception as e:
            self.logger.error(f"❌ 주식 뉴스 조회 실패: {e}")
            return []

    async def _get_naver_finance_news(self) -> List[Dict[str, str]]:
        """네이버 금융 뉴스 간단 파싱"""
        try:
            url = "https://finance.naver.com/news/"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = []
                
                # 네이버 뉴스 항목 찾기 (간단한 방법)
                news_items = soup.select('.newsList li')[:5]
                
                for item in news_items:
                    try:
                        title_elem = item.select_one('a')
                        if title_elem:
                            title = title_elem.get_text().strip()
                            url = title_elem.get('href', '')
                            if url and not url.startswith('http'):
                                url = f"https://finance.naver.com{url}"
                            
                            articles.append({
                                'title': str(title),
                                'summary': str(title[:100]) + '...',
                                'url': str(url),
                                'published': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                'source': {'name': '네이버 금융'}
                            })
                    except Exception as e:
                        continue
                
                return articles
            
            return []
            
        except Exception as e:
            self.logger.error(f"❌ 네이버 뉴스 파싱 실패: {e}")
            return []

    async def search_news(self, keywords: str) -> List[Dict[str, Any]]:
        """뉴스 검색"""
        # 네이버 뉴스 검색 URL
        url = f"https://search.naver.com/search.naver?where=news&query={keywords}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    raise Exception("Failed to fetch news")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                news_list = []
                articles = soup.select('.news_wrap')
                
                for article in articles[:5]:  # 상위 5개 기사만 가져오기
                    title = article.select_one('.news_tit')
                    description = article.select_one('.news_dsc')
                    press = article.select_one('.info_group a.info.press')
                    date = article.select_one('.info_group span.info')
                    
                    if title and description:
                        news_list.append({
                            'title': title.get_text(strip=True),
                            'link': title.get('href', ''),
                            'description': description.get_text(strip=True),
                            'press': press.get_text(strip=True) if press else '',
                            'date': date.get_text(strip=True) if date else ''
                        })
                
                return news_list

# 전역 인스턴스
news_service = NewsService() 