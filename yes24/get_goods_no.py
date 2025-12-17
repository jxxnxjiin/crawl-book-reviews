import requests
from bs4 import BeautifulSoup
import time
import re
from .utils import HEADERS

def _parse_products_from_soup(soup):
    """HTML에서 상품 목록 추출"""
    goods_dict = {}
    li_list = soup.select("li[data-goods-no]")
    
    for li in li_list:
        title_tag = li.select_one("a.gd_name")
        title = title_tag.get_text(strip=True) if title_tag else ""
        goods_no = li.get("data-goods-no")
        
        if title and goods_no:
            goods_dict[title] = goods_no
    
    return goods_dict

def get_goods_no(url, max_products=None):
    """
    예스24에서 상품 목록 추출

    query: 검색 키워드 (search) 또는 카테고리 번호 (attention/new)
    source_type: "search" (키워드 검색), "attention" (주목할 신상품), "new" (신상품)
    size: 검색 결과 수 (search에서만 사용)
    order: 정렬 방식 (search에서만 사용)
    max_products: 최대 상품 수 (None이면 전체)

    반환값: {제목: 상품번호} 딕셔너리
    """
    all_goods = {}
    page = 1

    while True:
        # 페이지 번호를 URL에 추가 또는 교체
        if 'pageNumber=' in url:
            # 기존 pageNumber를 현재 페이지로 교체
            current_url = re.sub(r'pageNumber=\d+', f'pageNumber={page}', url)
        elif '?' in url:
            current_url = f"{url}&pageNumber={page}"
        else:
            current_url = f"{url}?pageNumber={page}"

        response = requests.get(current_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        goods_dict = _parse_products_from_soup(soup)

        if not goods_dict:
            break

        # 결과 병합
        for title, goods_no in goods_dict.items():
            all_goods[title] = goods_no

            # max_products 제한 체크
            if max_products and len(all_goods) >= max_products:
                return dict(list(all_goods.items())[:max_products])

        # 다음 페이지 확인
        next_btn = soup.select_one(".yesUI_pagen .next:not(.dim)")
        if not next_btn:
            break

        page += 1
        time.sleep(0.5)  # 0.5초 대기 (차단 방지)

    return all_goods