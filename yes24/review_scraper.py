from bs4 import BeautifulSoup
from utils import get_chrome_driver
import time
import re


def parse_reviews_from_html(soup):
    """HTML에서 리뷰 데이터 추출"""
    reviews = []
    review_items = soup.select(".reviewInfoGrp")
    
    for item in review_items:
        review_data = {}
        
        # 평점 추출
        rating_elem = item.select_one(".review_rating .total_rating")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            # 숫자만 추출 (예: "평점8점" → "8")
            rating_num = re.search(r'\d+', rating_text)
            review_data['rating'] = int(rating_num.group()) if rating_num else None
        
        # 리뷰 내용 추출
        content_elem = item.select_one(".reviewInfoBot.origin .review_cont")
        if content_elem:
            content = content_elem.get_text(strip=True)
            review_data['content'] = content
        
        # 작성자 추출
        author_elem = item.select_one(".txt_id .lnk_id")
        if author_elem:
            review_data['author'] = author_elem.get_text(strip=True)
        
        # 날짜 추출
        date_elem = item.select_one(".txt_date")
        if date_elem:
            review_data['date'] = date_elem.get_text(strip=True)
        
        # 유효한 리뷰만 추가
        if review_data.get('content'):
            reviews.append(review_data)
    
    return reviews


def get_max_page(soup):
    """최대 페이지 번호 추출"""
    page_nums = soup.select(".yesUI_pagenS .num")
    if page_nums:
        max_page = 1
        for num in page_nums:
            text = num.get_text(strip=True)
            if text.isdigit():
                max_page = max(max_page, int(text))
        return max_page
    return 1


def sanitize_filename(filename):
    """파일명에 사용할 수 없는 문자 제거"""
    # 파일명에 사용 불가능한 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 공백을 언더스코어로
    filename = filename.replace(' ', '_')
    return filename


def get_yes24_reviews(title, goods_no, max_reviews=10):
    """
    예스24 상품 리뷰 크롤링
    title: 상품 제목
    goods_no: 상품 번호
    max_reviews: 최대 수집할 리뷰 수 (기본값: 10, None이면 전체 수집)
    """
    driver = get_chrome_driver()
    
    all_reviews = []

    try:
        # 리뷰 API 직접 호출 (첫 페이지)
        review_url = f"https://www.yes24.com/Product/communityModules/GoodsReviewList/{goods_no}?goodsSetYn=N&Sort=1&PageNumber=1&Type=ALL"
        driver.get(review_url)
        time.sleep(3)
        
        # 첫 페이지 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 최대 페이지 확인
        max_page = get_max_page(soup)
        print(f"상품명: {title}")
        print(f"총 {max_page} 페이지의 리뷰가 있습니다.")
        
        # 첫 페이지 리뷰 수집
        reviews = parse_reviews_from_html(soup)
        all_reviews.extend(reviews)
        print(f"페이지 1: {len(reviews)}개 리뷰 수집")
        
        # max_reviews 제한 체크
        if max_reviews and len(all_reviews) >= max_reviews:
            all_reviews = all_reviews[:max_reviews]
            print(f"\n최대 {max_reviews}개 리뷰 수집 완료.")
        else:
            # 2페이지부터 순회 (max_reviews에 도달할 때까지)
            for page in range(2, max_page + 1):
                # 리뷰 API 직접 호출
                review_url = f"https://www.yes24.com/Product/communityModules/GoodsReviewList/{goods_no}?goodsSetYn=N&Sort=1&PageNumber={page}&Type=ALL"
                driver.get(review_url)
                time.sleep(3)  # 차단 방지를 위해 3초 대기
                
                # 파싱
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                reviews = parse_reviews_from_html(soup)
                all_reviews.extend(reviews)
                print(f"페이지 {page}: {len(reviews)}개 리뷰 수집")
                
                # max_reviews 제한 체크
                if max_reviews and len(all_reviews) >= max_reviews:
                    all_reviews = all_reviews[:max_reviews]
                    print(f"\n최대 {max_reviews}개 리뷰 수집 완료.")
                    break
            else:
                print(f"\n총 {len(all_reviews)}개의 리뷰를 수집했습니다.")
        
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
                
    finally:
        driver.quit()
    
    return all_reviews