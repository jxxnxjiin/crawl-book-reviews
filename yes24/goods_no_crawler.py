import requests
from bs4 import BeautifulSoup
import sys

def get_goods_no(query):
    """
    예스24에서 상품 목록 추출
    
    query: 검색 키워드 또는 전체 URL
    - 키워드: "어린왕자" → 검색 URL로 변환
    """
    # URL인지 키워드인지 자동 감지
    url = f"https://www.yes24.com/product/search?query={query}"
    
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

if __name__ == "__main__":
    query = sys.argv[1]
    goods_no_dict = get_goods_no(query)
    
    print(f"총 {len(goods_no_dict)}개 상품 발견:")
    for i, (title, goods_no) in enumerate(goods_no_dict.items(), 1):
        print(f"  {i}. {title} (상품번호: {goods_no})")  
