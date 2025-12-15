"""
Yes24 Crawler Main Script

예스24 크롤러 메인 실행 스크립트
세 개의 파이프라인 제공:
1. 키워드 검색 → 리뷰 크롤링
2. 키워드 검색 → 세부정보 크롤링
3. 카테고리 신간 → 세부정보 추출
"""

import csv
from datetime import datetime
from pathlib import Path

from utils import build_attention_url
from get_goods_no import get_goods_no
from get_reviews import get_reviews
from get_books_info import get_book_info
from get_category_info import get_flat_categories
from search_products import search_products  # 키워드 검색용 (세션 지원)


def save_to_csv(data, filename):
    """데이터를 CSV 파일로 저장"""
    if not data:
        print("저장할 데이터가 없습니다.")
        return {'status': 'error', 'message': 'No data to save'}

    # results 디렉토리 생성
    Path("results").mkdir(exist_ok=True)
    filepath = Path("results") / filename

    # 딕셔너리 리스트인 경우
    if isinstance(data, list) and data and isinstance(data[0], dict):
        keys = data[0].keys()
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
    else:
        return {'status': 'error', 'message': 'Invalid data format'}

    print(f"✓ 저장 완료: {filepath}")
    return {'status': 'success', 'filepath': str(filepath)}


def pipeline_search_reviews():
    """파이프라인 1: 키워드 검색 → 리뷰 크롤링"""
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

    # 상품 검색 (세션 기반)
    goods_dict = search_products(keyword, size=40, order='RELATION', max_products=max_products)

    if not goods_dict:
        print("❌ 검색 결과가 없습니다.")
        return {'status': 'error', 'message': 'No products found'}

    print(f"✓ {len(goods_dict)}개의 상품을 찾았습니다.\n")

    # 각 상품의 리뷰 수집
    all_reviews = []
    for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
        print(f"[{idx}/{len(goods_dict)}] {title} (상품번호: {goods_no})")
        print(f"  리뷰 수집 중...")

        reviews = get_reviews(
            title=title,
            goods_no=goods_no,
            max_reviews=max_reviews
        )

        # 상품 정보 추가
        for review in reviews:
            review['product_title'] = title
            review['goods_no'] = goods_no
            all_reviews.append(review)

        print(f"  ✓ {len(reviews)}개의 리뷰 수집 완료\n")

    print(f"\n📊 총 {len(all_reviews)}개의 리뷰를 수집했습니다.")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_reviews_{keyword}_{timestamp}.csv"
    result = save_to_csv(all_reviews, filename)

    return result


def pipeline_search_bookinfo():
    """파이프라인 2: 키워드 검색 → 세부정보 크롤링"""
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

    # 상품 검색 (세션 기반)
    goods_dict = search_products(keyword, size=40, order='RELATION', max_products=max_products)

    if not goods_dict:
        print("❌ 검색 결과가 없습니다.")
        return {'status': 'error', 'message': 'No products found'}

    print(f"✓ {len(goods_dict)}개의 상품을 찾았습니다.\n")

    # 각 상품의 세부정보 추출
    all_books_info = []
    for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
        print(f"[{idx}/{len(goods_dict)}] {title} (상품번호: {goods_no})")
        print(f"  세부정보 추출 중...")

        info = get_book_info(goods_no)
        all_books_info.append(info)

        print(f"  ✓ 추출 완료\n")

    print(f"\n📊 총 {len(all_books_info)}개의 도서 정보를 추출했습니다.")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_books_{keyword}_{timestamp}.csv"
    result = save_to_csv(all_books_info, filename)

    return result


def pipeline_category_bookinfo():
    """파이프라인 3: 카테고리 신간 → 세부정보 추출"""
    print("\n" + "="*60)
    print("파이프라인 3: 카테고리 신간 → 세부정보 추출")
    print("="*60)

    # 카테고리 목록 가져오기
    print("\n📚 카테고리 목록을 가져오는 중...")
    categories = get_flat_categories("001")  # 국내도서 카테고리

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

    # 신간도서 가져오기
    url = build_attention_url(selected_cat_id)
    goods_dict = get_goods_no(url, max_products=max_products)

    if not goods_dict:
        print("❌ 신간도서를 찾을 수 없습니다.")
        return {'status': 'error', 'message': 'No products found'}

    print(f"✓ {len(goods_dict)}개의 신간도서를 찾았습니다.\n")

    # 각 도서의 세부정보 추출
    all_books_info = []
    for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
        print(f"[{idx}/{len(goods_dict)}] {title} (상품번호: {goods_no})")
        print(f"  세부정보 추출 중...")

        info = get_book_info(goods_no)
        info['category_id'] = selected_cat_id
        info['category_name'] = selected_cat_name
        all_books_info.append(info)

        print(f"  ✓ 추출 완료\n")

    print(f"\n📊 총 {len(all_books_info)}개의 도서 정보를 추출했습니다.")

    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"category_books_{selected_cat_id}_{timestamp}.csv"
    result = save_to_csv(all_books_info, filename)

    return result


def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("예스24 크롤러")
    print("="*60)

    while True:
        print("\n원하는 작업을 선택하세요:")
        print("1. 키워드 검색 → 리뷰 크롤링")
        print("2. 키워드 검색 → 세부정보 크롤링")
        print("3. 카테고리 신간 → 세부정보 추출")
        print("4. 종료")

        choice = input("\n선택 (1-4): ").strip()

        if choice == '1':
            result = pipeline_search_reviews()
        elif choice == '2':
            result = pipeline_search_bookinfo()
        elif choice == '3':
            result = pipeline_category_bookinfo()
        elif choice == '4':
            print("\n👋 프로그램을 종료합니다.")
            return {'status': 'success'}
        else:
            print("❌ 잘못된 선택입니다. 1-4 중에서 선택해주세요.")
            continue

        # 결과 확인
        if result.get('status') == 'error':
            print(f"\n❌ 오류: {result.get('message', 'Unknown error')}")

        # 계속할지 물어보기
        cont = input("\n다른 작업을 계속하시겠습니까? (y/n): ").strip().lower()
        if cont != 'y':
            print("\n👋 프로그램을 종료합니다.")
            return {'status': 'success'}

    return {'status': 'success'}


if __name__ == "__main__":
    try:
        result = main()
        exit(0 if result.get('status') == 'success' else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
