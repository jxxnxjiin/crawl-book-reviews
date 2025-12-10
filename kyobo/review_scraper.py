"""
교보문고 리뷰 크롤러 모듈
API를 통해 리뷰 데이터 수집
"""

import requests
import re


def sanitize_filename(filename):
    """파일명에 사용할 수 없는 문자 제거"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename


def build_review_api_url(goods_no, page=1, page_limit=10):
    """리뷰 API URL 생성"""
    return f"https://product.kyobobook.co.kr/api/review/list?page={page}&pageLimit={page_limit}&reviewSort=001&revwPatrCode=002&saleCmdtid={goods_no}"


def get_kyobo_reviews(title, goods_no, max_reviews=10):
    """
    교보문고 상품 리뷰 크롤링
    
    title: 상품 제목
    goods_no: 상품 번호 (S로 시작)
    max_reviews: 최대 수집할 리뷰 수 (기본값: 10, None이면 전체 수집)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    all_reviews = []
    page = 1
    page_limit = 50  # 한 번에 최대 50개씩 요청
    
    try:
        print(f"상품명: {title}")
        
        while True:
            url = build_review_api_url(goods_no, page, page_limit)
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data.get('statusCode') != 200:
                print(f"API 에러: {data.get('resultMessage')}")
                break
            
            review_list = data.get('data', {}).get('reviewList', [])
            total_count = data.get('data', {}).get('totalCount', 0)
            
            if page == 1:
                print(f"총 {total_count}개의 리뷰가 있습니다.")
            
            if not review_list:
                break
            
            # 리뷰 파싱
            for item in review_list:
                review_data = {
                    'rating': item.get('revwRvgr'),
                    'content': item.get('revwCntt'),
                    'author': item.get('mmbrId'),
                    'date': item.get('cretDttm', '')[:10],  # YYYY-MM-DD만
                }
                
                if review_data.get('content'):
                    all_reviews.append(review_data)
            
            print(f"페이지 {page}: {len(review_list)}개 리뷰 수집")
            
            # max_reviews 제한 체크
            if max_reviews and len(all_reviews) >= max_reviews:
                all_reviews = all_reviews[:max_reviews]
                print(f"\n최대 {max_reviews}개 리뷰 수집 완료.")
                break
            
            # 다음 페이지 체크
            if len(review_list) < page_limit:
                print(f"\n총 {len(all_reviews)}개의 리뷰를 수집했습니다.")
                break
            
            page += 1
    
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
    
    return all_reviews
