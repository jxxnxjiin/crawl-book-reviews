### Constants ###
from pathlib import Path
import json
import sys
sys.path.append(str(Path(__file__).parent.parent))

from common.http_utils import HEADERS

### URL Builders ###

def build_search_url(query, size=40, order='RELATION', page=1):
    """검색 URL 생성"""
    return f"https://www.yes24.com/product/search?domain=ALL&query={query}&page={page}&size={size}&order={order}"

def build_attention_url(category_number, page=1):
    """주목할 만한 신간도서 URL 생성"""
    return f"https://www.yes24.com/product/category/attentionnewproduct?categoryNumber={category_number}&pageNumber={page}"

def build_newly_published_url(category_number, page=1):
    """신간도서 URL 생성"""
    return f"https://www.yes24.com/product/category/newproduct?categoryNumber={category_number}&pageNumber={page}"

def build_review_url(goods_no, page=1, sort=1):
    """리뷰 URL 생성"""
    return f"https://www.yes24.com/Product/communityModules/GoodsReviewList/{goods_no}?goodsSetYn=N&Sort={sort}&PageNumber={page}&Type=ALL"

def build_book_url(goods_no):
    """상품 상세 페이지 URL 생성"""
    return f"https://www.yes24.com/product/goods/{goods_no}"

def get_categories(cache_file="./yes24_categories.json"):
    cache_path = Path(cache_file)

    if cache_file:
        with open(cache_path, 'r', encoding='utf-8') as f:
            categories = json.load(f)
            print(f"✓ 캐시 파일에서 {len(categories)}개 카테고리 로드: {cache_path}")
            return {cat_id: info["name"] for cat_id, info in categories.items()}