"""
Yes24 Crawler Main Script

예스24 크롤러 메인 실행 스크립트
세 개의 파이프라인 제공:
1. 키워드 검색 → 리뷰 크롤링
2. 키워드 검색 → 세부정보 크롤링
3. 카테고리 신간 → 세부정보 추출
"""

import time
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from common.file_utils import save_to_csv
from .utils import build_attention_url, build_newly_published_url, get_categories
from .get_goods_no import get_goods_no
from .get_reviews import get_reviews
from .get_books_info import get_book_info
from .search_products import search_products  # 키워드 검색용 (세션 지원)


# =============================================================================
# 핵심 로직 함수 (UI-agnostic) - app.py와 공유
# =============================================================================

def run_search_reviews(keyword, max_products=10, max_reviews=10, order='RELATION', progress_callback=None):
    """
    키워드 검색 → 리뷰 크롤링 (핵심 로직)

    Args:
        keyword: 검색 키워드
        max_products: 최대 상품 수
        max_reviews: 상품당 최대 리뷰 수
        order: 정렬 방식
        progress_callback: 진행상황 콜백 함수 (optional)
                         callback(current, total, message) 형식

    Returns:
        dict: {
            'status': 'success' | 'error',
            'message': str,
            'data': list,  # 리뷰 리스트
            'count': int
        }
    """
    try:
        # 상품 검색
        goods_dict = search_products(keyword, size=40, order=order, max_products=max_products)

        if not goods_dict:
            return {
                'status': 'error',
                'message': '검색 결과가 없습니다.',
                'data': [],
                'count': 0
            }

        # 각 상품의 리뷰 수집
        all_reviews = []
        total_items = len(goods_dict)

        for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
            if progress_callback:
                progress_callback(idx, total_items, f"{title[:50]}... 리뷰 수집 중")

            try:
                reviews = get_reviews(
                    title=title,
                    goods_no=goods_no,
                    max_reviews=max_reviews,
                    verbose=False
                )

                # 상품 정보 추가
                for review in reviews:
                    review['product_title'] = title
                    review['goods_no'] = goods_no
                    all_reviews.append(review)
            except Exception as e:
                # 개별 상품 실패는 무시하고 계속 진행
                if progress_callback:
                    progress_callback(idx, total_items, f"실패: {title[:30]}... - {str(e)[:50]}")

            time.sleep(0.3)  # 차단 방지

        return {
            'status': 'success',
            'message': f'{len(all_reviews)}개의 리뷰를 수집했습니다.',
            'data': all_reviews,
            'count': len(all_reviews)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'오류 발생: {str(e)}',
            'data': [],
            'count': 0
        }


def run_search_bookinfo(keyword, max_products=10, order='RELATION', progress_callback=None):
    """
    키워드 검색 → 세부정보 크롤링 (핵심 로직)

    Args:
        keyword: 검색 키워드
        max_products: 최대 상품 수
        order: 정렬 방식
        progress_callback: 진행상황 콜백 함수 (optional)

    Returns:
        dict: {
            'status': 'success' | 'error',
            'message': str,
            'data': list,  # 도서 정보 리스트
            'count': int
        }
    """
    try:
        # 상품 검색
        goods_dict = search_products(keyword, size=40, order=order, max_products=max_products)

        if not goods_dict:
            return {
                'status': 'error',
                'message': '검색 결과가 없습니다.',
                'data': [],
                'count': 0
            }

        # 각 상품의 세부정보 추출
        all_books_info = []
        total_items = len(goods_dict)

        for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
            if progress_callback:
                progress_callback(idx, total_items, f"{title[:50]}... 세부정보 추출 중")

            try:
                info = get_book_info(goods_no)
                all_books_info.append(info)
            except Exception as e:
                if progress_callback:
                    progress_callback(idx, total_items, f"실패: {title[:30]}... - {str(e)[:50]}")

            time.sleep(0.3)  # 차단 방지

        return {
            'status': 'success',
            'message': f'{len(all_books_info)}개의 도서 정보를 추출했습니다.',
            'data': all_books_info,
            'count': len(all_books_info)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'오류 발생: {str(e)}',
            'data': [],
            'count': 0
        }


def run_category_bookinfo(category_id, category_name, max_products=10, progress_callback=None):
    """
    카테고리 신간 → 세부정보 추출 (핵심 로직)

    Args:
        category_id: 카테고리 ID
        category_name: 카테고리 이름
        max_products: 최대 상품 수
        progress_callback: 진행상황 콜백 함수 (optional)

    Returns:
        dict: {
            'status': 'success' | 'error',
            'message': str,
            'data': list,  # 도서 정보 리스트
            'count': int
        }
    """
    try:
        # 신간도서 가져오기
        url = build_newly_published_url(category_id)
        goods_dict = get_goods_no(url, max_products=max_products)

        if not goods_dict:
            return {
                'status': 'error',
                'message': '신간도서를 찾을 수 없습니다.',
                'data': [],
                'count': 0
            }

        # 각 도서의 세부정보 추출
        all_books_info = []
        total_items = len(goods_dict)

        for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
            if progress_callback:
                progress_callback(idx, total_items, f"{title[:50]}... 세부정보 추출 중")

            try:
                info = get_book_info(goods_no)
                info['category_id'] = category_id
                info['category_name'] = category_name
                all_books_info.append(info)
            except Exception as e:
                if progress_callback:
                    progress_callback(idx, total_items, f"실패: {title[:30]}... - {str(e)[:50]}")

            time.sleep(0.3)  # 차단 방지

        return {
            'status': 'success',
            'message': f'{len(all_books_info)}개의 도서 정보를 추출했습니다.',
            'data': all_books_info,
            'count': len(all_books_info)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'오류 발생: {str(e)}',
            'data': [],
            'count': 0
        }


# =============================================================================
# CLI 전용 함수
# =============================================================================


def pipeline_search_reviews():
    """파이프라인 1: 키워드 검색 → 리뷰 크롤링 (CLI용)"""
    print("\n" + "="*60)
    print("파이프라인 1: 키워드 검색 → 리뷰 크롤링")
    print("="*60)

    # 키워드 입력
    keyword = input("\n검색 키워드를 입력하세요: ").strip()
    if not keyword:
        print("❌ 키워드를 입력해야 합니다.")
        return {'status': 'error', 'message': 'No keyword provided'}

    # 최대 상품 수 입력
    try:
        max_products = int(input("최대 상품 수 (기본 10): ").strip() or "10")
    except ValueError:
        max_products = 10

    # 상품당 최대 리뷰 수 입력
    try:
        max_reviews = int(input("상품당 최대 리뷰 수 (기본 10): ").strip() or "10")
    except ValueError:
        max_reviews = 10

    print(f"\n🔍 '{keyword}' 검색 중...")

    # 진행상황 콜백
    def progress_callback(current, total, message):
        print(f"[{current}/{total}] {message}")

    # 핵심 로직 실행
    result = run_search_reviews(
        keyword=keyword,
        max_products=max_products,
        max_reviews=max_reviews,
        order='RELATION',
        progress_callback=progress_callback
    )

    if result['status'] == 'error':
        print(f"❌ {result['message']}")
        return result

    print(f"\n📊 {result['message']}")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_reviews_{keyword}_{timestamp}.csv"
    save_result = save_to_csv(result['data'], filename)

    return save_result


def pipeline_search_bookinfo():
    """파이프라인 2: 키워드 검색 → 세부정보 크롤링 (CLI용)"""
    print("\n" + "="*60)
    print("파이프라인 2: 키워드 검색 → 세부정보 크롤링")
    print("="*60)

    # 키워드 입력
    keyword = input("\n검색 키워드를 입력하세요: ").strip()
    if not keyword:
        print("❌ 키워드를 입력해야 합니다.")
        return {'status': 'error', 'message': 'No keyword provided'}

    # 최대 상품 수 입력
    try:
        max_products = int(input("최대 상품 수 (기본 10): ").strip() or "10")
    except ValueError:
        max_products = 10

    print(f"\n🔍 '{keyword}' 검색 중...")

    # 진행상황 콜백
    def progress_callback(current, total, message):
        print(f"[{current}/{total}] {message}")

    # 핵심 로직 실행
    result = run_search_bookinfo(
        keyword=keyword,
        max_products=max_products,
        order='RELATION',
        progress_callback=progress_callback
    )

    if result['status'] == 'error':
        print(f"❌ {result['message']}")
        return result

    print(f"\n📊 {result['message']}")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_books_{keyword}_{timestamp}.csv"
    save_result = save_to_csv(result['data'], filename)

    return save_result


def pipeline_category_bookinfo():
    """파이프라인 3: 카테고리 신간 → 세부정보 추출 (CLI용)"""
    print("\n" + "="*60)
    print("파이프라인 3: 카테고리 신간 → 세부정보 추출")
    print("="*60)

    # 카테고리 목록 가져오기
    print("\n📚 카테고리 목록을 가져오는 중...")
    categories = get_categories()

    if not categories:
        print("❌ 카테고리를 가져올 수 없습니다.")
        return {'status': 'error', 'message': 'Failed to fetch categories'}

    # 카테고리 표시
    print(f"\n총 {len(categories)}개의 카테고리:")
    print("-" * 60)

    cat_list = list(categories.items())
    for idx, (cat_id, cat_name) in enumerate(cat_list, 1):
        print(f"{idx:3d}. [{cat_id}] {cat_name}")

    print("-" * 60)

    # 카테고리 선택
    try:
        choice = int(input(f"\n카테고리 번호를 선택하세요 (1-{len(cat_list)}): ").strip())
        if not (1 <= choice <= len(cat_list)):
            print("❌ 잘못된 번호입니다.")
            return {'status': 'error', 'message': 'Invalid choice'}

        selected_cat_id, selected_cat_name = cat_list[choice - 1]
    except ValueError:
        print("❌ 숫자를 입력해야 합니다.")
        return {'status': 'error', 'message': 'Invalid input'}

    print(f"\n✓ 선택한 카테고리: [{selected_cat_id}] {selected_cat_name}")

    # 최대 상품 수 입력
    try:
        max_products = int(input("최대 상품 수 (기본 10): ").strip() or "10")
    except ValueError:
        max_products = 10

    print(f"\n🔍 신간도서 검색 중...")

    # 진행상황 콜백
    def progress_callback(current, total, message):
        print(f"[{current}/{total}] {message}")

    # 핵심 로직 실행
    result = run_category_bookinfo(
        category_id=selected_cat_id,
        category_name=selected_cat_name,
        max_products=max_products,
        progress_callback=progress_callback
    )

    if result['status'] == 'error':
        print(f"❌ {result['message']}")
        return result

    print(f"\n📊 {result['message']}")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"category_books_{selected_cat_id}_{timestamp}.csv"
    save_result = save_to_csv(result['data'], filename)

    return save_result