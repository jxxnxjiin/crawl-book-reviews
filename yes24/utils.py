### Constants ###

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

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