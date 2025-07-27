#!/usr/bin/env python3
"""
삼성전자 변동률 파싱 디버깅 스크립트 (개선된 버전)
522.52% 문제 분석 및 해결
"""

import requests
import re
from bs4 import BeautifulSoup

def debug_samsung_change():
    """삼성전자 변동률 파싱 문제 분석 (개선된 버전)"""
    
    print("🔍 삼성전자 변동률 파싱 디버깅 (개선된 버전)")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    # 네이버 금융 직접 URL
    url = "https://finance.naver.com/item/main.naver?code=005930"
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"📄 HTML 길이: {len(response.text):,} 문자")
        
        # 현재가 파싱 테스트
        print("\n💰 현재가 파싱 테스트:")
        print("-" * 30)
        
        price_selectors = [
            '.no_today .blind',
            '.today .blind', 
            '.no_today',
            '.rate_info .num',
        ]
        
        current_price = None
        for selector in price_selectors:
            elements = soup.select(selector)
            print(f"\n선택자: {selector}")
            print(f"매치된 요소 수: {len(elements)}")
            
            for i, elem in enumerate(elements[:3]):
                text = elem.get_text(strip=True)
                print(f"  [{i}] '{text}'")
                
                # 가격 검증
                try:
                    price_str = text.replace('원', '').replace(',', '').strip()
                    if price_str.replace('.', '').isdigit() and len(price_str) >= 3:
                        price_val = float(price_str)
                        if 50000 <= price_val <= 100000:  # 삼성전자 예상 범위
                            current_price = price_val
                            print(f"    ✅ 유효한 가격: {price_val:,.0f}원")
                        else:
                            print(f"    ❌ 범위 외 가격: {price_val:,.0f}원")
                except (ValueError, AttributeError):
                    print(f"    ❌ 파싱 실패")
            
            if current_price:
                break
        
        print(f"\n💰 최종 현재가: {current_price:,.0f}원" if current_price else "\n❌ 현재가를 찾을 수 없음")
        
        # 변동률 파싱 테스트 (개선된 방법)
        print("\n📈 변동률 파싱 테스트 (개선된 방법):")
        print("-" * 40)
        
        # .no_exday 컨테이너 분석
        exday_container = soup.select_one('.no_exday')
        if exday_container:
            exday_text = exday_container.get_text(strip=True)
            print(f"전일대비 전체 텍스트: '{exday_text}'")
            
            # 상승/하락 판단
            is_rise = '상승' in exday_text
            is_decline = '하락' in exday_text
            print(f"방향: {'상승' if is_rise else '하락' if is_decline else '보합'}")
            
            # blind 요소들 개별 분석
            blind_elements = exday_container.select('.blind')
            print(f"\nblind 요소 {len(blind_elements)}개:")
            
            potential_changes = []
            for i, elem in enumerate(blind_elements):
                text = elem.get_text(strip=True)
                print(f"  [{i}] '{text}'")
                
                # 소수점이 있는 숫자만 변동률 후보로 간주
                if re.match(r'^\d+\.\d+$', text):
                    try:
                        value = float(text)
                        if 0.01 <= value <= 20.0:  # 합리적인 변동률 범위
                            potential_changes.append(value)
                            print(f"      → 변동률 후보: {value}%")
                    except ValueError:
                        pass
            
            # 최종 변동률 결정
            change_percent = None
            if potential_changes:
                change_value = min(potential_changes)  # 가장 작은 값 선택
                
                if is_decline:
                    change_percent = -change_value
                elif is_rise:
                    change_percent = change_value
                else:
                    change_percent = change_value
                
                print(f"\n✅ 변동률 확정: {change_percent}%")
            else:
                print(f"\n❌ 변동률을 찾을 수 없음")
        
        # 문제가 되었던 기존 패턴들 확인
        print("\n🔍 기존 문제 패턴 확인:")
        print("-" * 30)
        
        html_content = response.text
        
        # 522.52 같은 큰 숫자 검색
        large_numbers = re.findall(r'(\d{3,}\.\d+)', html_content)
        print(f"큰 숫자들 (100 이상): {large_numbers[:10]}")  # 첫 10개만
        
        # 정상적인 변동률 패턴 검색
        normal_patterns = re.findall(r'([+-]?\d{1,2}\.\d+)%', html_content)
        print(f"정상 변동률 패턴: {normal_patterns[:10]}")  # 첫 10개만
        
        # 최종 결과 요약
        print("\n" + "=" * 60)
        print("📊 최종 결과:")
        print(f"  현재가: {current_price:,.0f}원" if current_price else "  현재가: 파싱 실패")
        print(f"  변동률: {change_percent}%" if change_percent is not None else "  변동률: 파싱 실패")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_samsung_change() 