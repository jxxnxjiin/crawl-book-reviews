"""
교보문고 상품 검색 모듈
"""

import requests
from bs4 import BeautifulSoup
import re

# 정렬 옵션 상수
ORDER_OPTIONS = {
    '1': ('qntt', '판매량순'),
    '2': ('date', '최신순'),
    '3': ('', '인기도순'),
    '4': ('kcont', '클로버리뷰순'),
    '5': ('krvgr', '클로버평점순'),
}


def build_search_url(query, size=40, order='', page=1):
    """검색 URL 생성"""
    return f"https://search.kyobobook.co.kr/search?keyword={query}&page={page}&ra={order}&len={size}"


def get_goods_no(query, size=40, order='', page=1):
    """
    교보문고에서 키워드 기반으로 상품 목록 추출
    
    query: 검색 키워드
    size: 검색 결과 수 (자연수)
    order: 정렬 방식 (qntt/date/kcont/krvgr 또는 빈 문자열)
    """
    url = build_search_url(query, size, order, page)
    
    goods_no_dict = {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    
    # a.prod_info 태그에서 상품 정보 추출
    prod_links = soup.select("a.prod_info")
    
    for link in prod_links:
        # href에서 상품 ID 추출 (예: /detail/S000201100675)
        href = link.get("href", "")
        match = re.search(r'/detail/(S\d+)', href)
        
        if match:
            goods_no = match.group(1)
            
            # 제목 추출 (span[id^="cmdtName_"])
            title_tag = link.select_one(f'span[id="cmdtName_{goods_no}"]')
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            if title and goods_no:
                goods_no_dict[title] = goods_no
    
    return goods_no_dict