"""
예스24 상품 검색 모듈
"""

import requests
from bs4 import BeautifulSoup

# 정렬 옵션 상수
ORDER_OPTIONS = {
    '1': ('RELATION', '정확도순'),
    '2': ('RECENT', '신상품순'),
    '3': ('SINDEX_ONLY', '인기도순'),
    '4': ('REG_DTS', '등록일순'),
    '5': ('CONT_CNT', '평점순'),
    '6': ('REVIE_CNT', '리뷰순'),
}


def build_search_url(query, size=40, order='RELATION', page=1):
    """검색 URL 생성"""
    return f"https://www.yes24.com/product/search?domain=ALL&query={query}&page={page}&size={size}&order={order}"


def get_goods_no(query, size=40, order='RELATION'):
    """
    예스24에서 키워드 기반으로 상품 목록 추출
    
    query: 검색 키워드
    size: 검색 결과 수 (자연수)
    order: 정렬 방식 (RELATION/RECENT/SINDEX_ONLY/REG_DTS/CONT_CNT/REVIE_CNT)
    """
    url = build_search_url(query, size, order)
    
    goods_no_dict = {}
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    
    # data-goods-no 속성을 가진 모든 li 태그 선택
    li_list = soup.select("li[data-goods-no]")
    
    for li in li_list:
        title_tag = li.select_one("a.gd_name")
        title = title_tag.get_text(strip=True) if title_tag else ""
        goods_no = li.get("data-goods-no")
        
        if title and goods_no:
            goods_no_dict[title] = goods_no
    
    return goods_no_dict
