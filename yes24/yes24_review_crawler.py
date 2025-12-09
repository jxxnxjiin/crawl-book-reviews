from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time
import sys
import re
import os


def parse_reviews_from_html(soup):
    """HTML에서 리뷰 데이터 추출"""
    reviews = []
    review_items = soup.select(".reviewInfoGrp")
    
    for item in review_items:
        review_data = {}
        
        # 평점 추출 (예: "평점8점" → "8")
        rating_elem = item.select_one(".review_rating .total_rating")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            # 숫자만 추출
            rating_num = re.search(r'\d+', rating_text)
            review_data['rating'] = int(rating_num.group()) if rating_num else None
        
        # 리뷰 내용 추출 (origin에서 가져옴 - 전체 내용)
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


def get_product_title(soup):
    """상품 제목 추출"""
    # meta 태그에서 제목 추출
    title_meta = soup.select_one('meta[name="title"]')
    if title_meta and title_meta.get('content'):
        return title_meta.get('content')
    
    # og:title에서 추출 (백업)
    og_title = soup.select_one('meta[property="og:title"]')
    if og_title and og_title.get('content'):
        # "| 저자 | 출판사 - 예스24" 부분 제거
        title = og_title.get('content').split('|')[0].strip()
        return title
    
    return None


def sanitize_filename(filename):
    """파일명에 사용할 수 없는 문자 제거"""
    # 파일명에 사용 불가능한 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 공백을 언더스코어로
    filename = filename.replace(' ', '_')
    return filename


def get_yes24_reviews(goods_no, max_reviews=10):
    """
    예스24 상품 리뷰 크롤링
    goods_no: 상품 번호 (예: "143605394")
    max_reviews: 최대 수집할 리뷰 수 (기본값: 10, None이면 전체 수집)
    """
    
    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # 차단 방지: User-Agent 설정
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # WSL용: Chromium 바이너리 경로 설정
    options.binary_location = "/usr/bin/chromium-browser"
    
    # 시스템에 설치된 chromedriver 사용
    driver = webdriver.Chrome(
        service=Service("/usr/bin/chromedriver"),
        options=options
    )
    
    all_reviews = []
    product_title = None
    
    try:
        # 먼저 상품 페이지에서 제목만 가져오기
        url = f"https://www.yes24.com/Product/Goods/{goods_no}"
        driver.get(url)
        time.sleep(2)
        
        # 상품 제목 추출
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_title = get_product_title(soup)
        if product_title:
            print(f"상품명: {product_title}")
        
        # 리뷰 API 직접 호출 (첫 페이지부터)
        review_url = f"https://www.yes24.com/Product/communityModules/GoodsReviewList/{goods_no}?goodsSetYn=N&Sort=1&PageNumber=1&Type=ALL"
        driver.get(review_url)
        time.sleep(3)
        
        # 첫 페이지 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 최대 페이지 확인
        max_page = get_max_page(soup)
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
        product_title = None
        
    finally:
        driver.quit()
    
    return all_reviews, product_title


if __name__ == "__main__":
    # 사용 예시
    goods_no = sys.argv[1]
    reviews, product_title = get_yes24_reviews(goods_no)
    
    # 파일명 생성 (제목 사용, 없으면 상품번호)
    if product_title:
        filename = sanitize_filename(product_title)
    else:
        filename = goods_no
    
    # 출력 경로 생성
    output_dir = "./results"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/{filename}.csv"
    
    # 결과 출력
    for i, review in enumerate(reviews, 1): 
        print(f"=== 리뷰 {i} ===")
        print(f"평점: {review.get('rating', 'N/A')}")
        print(f"내용: {review.get('content', 'N/A')}")
        print()
    
    # DataFrame으로 저장
    if reviews:
        df = pd.DataFrame(reviews)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"{output_path} 파일로 저장되었습니다.")
