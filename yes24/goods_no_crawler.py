import requests
from bs4 import BeautifulSoup
import sys

def get_goods_no(url):
    """
    예스24 검색결과 또는 카테고리 페이지에서 상품 목록 추출
    
    지원 페이지:
    - 검색 결과: https://www.yes24.com/product/search?query=...
    - 카테고리: https://www.yes24.com/product/category/display/...
    """
    goods_no_dict = {}
    req = requests.get(url)
    content = req.content
    soup = BeautifulSoup(content, 'html.parser')
    
    # data-goods-no 속성을 가진 모든 li 태그 선택 (검색/카테고리 페이지 모두 지원)
    li_list = soup.select("li[data-goods-no]")
    
    for li in li_list:
        # 책 제목
        title_tag = li.select_one("a.gd_name")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # 상품번호
        goods_no = li.get("data-goods-no")
        
        if title and goods_no:
            goods_no_dict[title] = goods_no
    
    return goods_no_dict

if __name__ == "__main__":
    url = sys.argv[1]
    goods_no_dict = get_goods_no(url)
    
    print(f"총 {len(goods_no_dict)}개 상품 발견:")
    for i, (title, goods_no) in enumerate(goods_no_dict.items(), 1):
        print(f"  {i}. {title} (상품번호: {goods_no})")  
