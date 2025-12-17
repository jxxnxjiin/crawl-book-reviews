"""
Kyobo Crawler Main Script

교보문고 크롤러 메인 실행 스크립트
파이프라인: 키워드 검색 → 리뷰 크롤링
"""

import time
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from common.file_utils import save_to_csv
from .product_search import get_goods_no, ORDER_OPTIONS
from .review_scraper import get_kyobo_reviews
from .utils import select_option


# =============================================================================
# 핵심 로직 함수 (UI-agnostic) - app.py와 공유
# =============================================================================

def run_search_reviews(keyword, max_products=10, max_reviews_per_book=10, order='', progress_callback=None):
    """
    키워드 검색 → 리뷰 크롤링 (핵심 로직)

    Args:
        keyword: 검색 키워드
        max_products: 최대 상품 수
        max_reviews_per_book: 상품당 최대 리뷰 수
        order: 정렬 방식 ('qntt', 'date', 'kcont', 'krvgr', '' 등)
        progress_callback: 진행상황 콜백 함수 (optional)
                         callback(current, total, message) 형식

    Returns:
        dict: {
            'status': 'success' | 'error',
            'message': str,
            'data': list,  # 리뷰 리스트
            'count': int,
            'summary': list  # 상품별 요약 정보
        }
    """
    try:
        # 상품 검색
        goods_dict = get_goods_no(keyword, size=max_products, order=order)

        if not goods_dict:
            return {
                'status': 'error',
                'message': '검색 결과가 없습니다.',
                'data': [],
                'count': 0,
                'summary': []
            }

        # 각 상품의 리뷰 수집
        all_reviews = []
        results_summary = []
        total_items = len(goods_dict)

        for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
            if progress_callback:
                progress_callback(idx, total_items, f"{title[:50]}... 리뷰 수집 중")

            try:
                reviews = get_kyobo_reviews(title, goods_no, max_reviews=max_reviews_per_book)

                if reviews:
                    # 각 리뷰에 goods_no와 title 추가
                    for review in reviews:
                        review['goods_no'] = goods_no
                        review['title'] = title

                    all_reviews.extend(reviews)
                    results_summary.append({
                        'title': title,
                        'goods_no': goods_no,
                        'review_count': len(reviews)
                    })
                else:
                    results_summary.append({
                        'title': title,
                        'goods_no': goods_no,
                        'review_count': 0
                    })

            except Exception as e:
                # 개별 상품 실패는 무시하고 계속 진행
                if progress_callback:
                    progress_callback(idx, total_items, f"실패: {title[:30]}... - {str(e)[:50]}")

                results_summary.append({
                    'title': title,
                    'goods_no': goods_no,
                    'review_count': -1
                })

            time.sleep(2)  # 서버 부하 방지

        return {
            'status': 'success',
            'message': f'{len(all_reviews)}개의 리뷰를 수집했습니다.',
            'data': all_reviews,
            'count': len(all_reviews),
            'summary': results_summary
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'오류 발생: {str(e)}',
            'data': [],
            'count': 0,
            'summary': []
        }


# =============================================================================
# CLI 전용 함수
# =============================================================================

def pipeline_search_reviews():
    """파이프라인: 키워드 검색 → 리뷰 크롤링 (CLI용)"""
    print("\n" + "="*60)
    print("교보문고 리뷰 크롤러")
    print("="*60)

    # 키워드 입력
    keyword = input("\n검색 키워드: ").strip()
    if not keyword:
        print("❌ 키워드를 입력해야 합니다.")
        return {'status': 'error', 'message': 'No keyword provided'}

    # 검색 결과 수 입력
    size_input = input("검색 결과 수 (기본 40): ").strip()
    size = int(size_input) if size_input.isdigit() else 40

    # 정렬 방식 선택
    order = select_option(ORDER_OPTIONS, "정렬 방식:")

    # 최대 리뷰 수 입력
    max_reviews_input = input("책당 최대 리뷰 수 (기본 10): ").strip()
    max_reviews = int(max_reviews_input) if max_reviews_input.isdigit() else 10

    print(f"\n🔍 '{keyword}' 검색 중...")

    # 진행상황 콜백
    def progress_callback(current, total, message):
        print(f"[{current}/{total}] {message}")

    # 핵심 로직 실행
    result = run_search_reviews(
        keyword=keyword,
        max_products=size,
        max_reviews_per_book=max_reviews,
        order=order,
        progress_callback=progress_callback
    )

    if result['status'] == 'error':
        print(f"❌ {result['message']}")
        return result

    print(f"\n📊 {result['message']}")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kyobo_reviews_{keyword}_{timestamp}.csv"
    save_result = save_to_csv(result['data'], filename)

    # 요약 저장
    if result['summary']:
        summary_filename = f"kyobo_summary_{keyword}_{timestamp}.csv"
        save_to_csv(result['summary'], summary_filename)

    return save_result


def main_interactive():
    """인터랙티브 모드로 실행 (하위 호환성)"""
    return pipeline_search_reviews()


def main_cli():
    """CLI 인자로 실행 (빠른 실행용)"""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  인터랙티브: python pipeline.py")
        print("  빠른 실행:  python pipeline.py <키워드> [최대리뷰수] [size] [order]")
        print("")
        print("예시:")
        print('  python pipeline.py "토익" 10 40 qntt')
        print('  python pipeline.py "토익" 10 40 date')
        print("")
        print("size: 원하는 검색 결과 수")
        print("order: qntt(판매량), date(최신), kcont(클로버리뷰), krvgr(클로버평점), 빈문자열(인기도)")
        sys.exit(1)

    keyword = sys.argv[1]
    max_reviews = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    order = sys.argv[4] if len(sys.argv) > 4 else ''

    print("=" * 60)
    print(f"🔍 '{keyword}' 검색 중... (size={size}, order={order})")
    print("=" * 60)

    # 진행상황 콜백
    def progress_callback(current, total, message):
        print(f"[{current}/{total}] {message}")

    # 핵심 로직 실행
    result = run_search_reviews(
        keyword=keyword,
        max_products=size,
        max_reviews_per_book=max_reviews,
        order=order,
        progress_callback=progress_callback
    )

    if result['status'] == 'error':
        print(f"❌ {result['message']}")
        return result

    print(f"\n📊 {result['message']}")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kyobo_reviews_{keyword}_{timestamp}.csv"
    save_result = save_to_csv(result['data'], filename)

    # 요약 저장
    if result['summary']:
        summary_filename = f"kyobo_summary_{keyword}_{timestamp}.csv"
        save_to_csv(result['summary'], summary_filename)

    return save_result


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 인자 없으면 인터랙티브 모드
        main_interactive()
    else:
        # 인자 있으면 CLI 모드
        main_cli()
