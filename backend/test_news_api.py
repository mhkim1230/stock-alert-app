import os
import requests

def test_news_api():
    # API 키 확인
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        print("API 키가 설정되지 않았습니다.")
        return False

    # 테스트 URL
    url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'country': 'us',
        'category': 'business',
        'apiKey': api_key
    }

    try:
        # API 요청
        response = requests.get(url, params=params)
        
        # 응답 상태 확인
        if response.status_code == 200:
            data = response.json()
            print("API 연결 성공!")
            print(f"총 기사 수: {len(data.get('articles', []))}")
            
            # 첫 번째 기사 제목 출력
            if data.get('articles'):
                print("첫 번째 기사 제목:", data['articles'][0].get('title', '제목 없음'))
            return True
        else:
            print(f"API 연결 실패. 상태 코드: {response.status_code}")
            print("응답 내용:", response.text)
            return False

    except Exception as e:
        print(f"오류 발생: {e}")
        return False

if __name__ == '__main__':
    test_news_api() 