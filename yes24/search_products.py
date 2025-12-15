"""
예스24 키워드 검색 상품 목록 추출
"""

import requests
from bs4 import BeautifulSoup
import time


# 정렬 옵션
ORDER_OPTIONS = {
    '1': ('RELATION', '정확도순'),
    '2': ('RECENT', '신상품순'),
    '3': ('SINDEX_ONLY', '인기도순'),
    '4': ('REG_DTS', '등록일순'),
    '5': ('CONT_CNT', '평점순'),
    '6': ('REVIE_CNT', '리뷰순'),
}


def _get_session():
    """세션 생성 및 초기화"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    # 쿠키 획득을 위해 메인 페이지 먼저 방문
    session.get('https://www.yes24.com')
    return session


def build_search_url(query, page=1, size=24, order='RELATION'):
    """검색 URL 생성"""
    return f"https://www.yes24.com/product/search?domain=ALL&query={query}&page={page}&size={size}&order={order}"


def _parse_products_from_soup(soup):
    """HTML에서 상품 목록 추출"""
    goods_dict = {}
    
    # data-goods-no 속성을 가진 모든 li 요소 찾기
    li_list = soup.find_all('li', attrs={'data-goods-no': True})
    
    for li in li_list:
        title_tag = li.find('a', class_='gd_name')
        title = title_tag.get_text(strip=True) if title_tag else ""
        goods_no = li.get("data-goods-no")
        
        if title and goods_no:
            goods_dict[title] = goods_no
    
    return goods_dict


def search_products(query, size=24, order='RELATION', max_products=None):
    """
    예스24 키워드 검색으로 상품 목록 추출
    
    query: 검색 키워드
    size: 페이지당 결과 수 (24/40/80/120)
    order: 정렬 방식 (RELATION/RECENT/SINDEX_ONLY/REG_DTS/CONT_CNT/REVIE_CNT)
    max_products: 최대 상품 수 (None이면 전체)
    
    반환값: {제목: 상품번호} 딕셔너리
    """
    session = _get_session()
    all_goods = {}
    page = 1
    
    while True:
        url = build_search_url(query, page=page, size=size, order=order)
        response = session.get(url)
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


if __name__ == "__main__":
    import sys
    
    query = sys.argv[1] if len(sys.argv) > 1 else "파이썬"
    max_count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"=== '{query}' 검색 결과 (최대 {max_count}개) ===\n")
    
    products = search_products(query, max_products=max_count)
    
    print(f"총 {len(products)}개 상품:\n")
    for i, (title, goods_no) in enumerate(products.items(), 1):
        print(f"  {i}. [{goods_no}] {title[:50]}...")

