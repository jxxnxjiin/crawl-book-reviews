"""
Kyobo Bookstore Crawler Package

교보문고 도서 크롤러 모듈
- 상품 검색 및 목록 추출
- 리뷰 수집
- 파이프라인 실행 (검색 → 리뷰 크롤링)
"""

from .utils import (
    sanitize_filename,
    select_option,
)

from .product_search import (
    build_search_url,
    get_goods_no,
    ORDER_OPTIONS,
)

from .review_scraper import (
    build_review_api_url,
    get_kyobo_reviews,
)

from .pipeline import (
    run_search_reviews,
    pipeline_search_reviews,
    main_interactive,
    main_cli,
)

__all__ = [
    # Utils
    'sanitize_filename',
    'select_option',

    # Product Search
    'build_search_url',
    'get_goods_no',
    'ORDER_OPTIONS',

    # Review Scraper
    'build_review_api_url',
    'get_kyobo_reviews',

    # Pipeline
    'run_search_reviews',
    'pipeline_search_reviews',
    'main_interactive',
    'main_cli',
]

__version__ = '1.0.0'
