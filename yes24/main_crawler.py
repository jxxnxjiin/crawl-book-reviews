"""
예스24 리뷰 크롤러 메인 스크립트
1. 검색 결과에서 상품 목록 추출
2. 각 상품별로 리뷰 크롤링 (최대 10개씩)
3. 개별 파일 또는 통합 파일로 저장
"""

from product_search import get_goods_no, ORDER_OPTIONS
from review_scraper import get_yes24_reviews, sanitize_filename
import pandas as pd
import os
import sys
import time
from datetime import datetime

# 저장 방식 옵션
SAVE_MODE_OPTIONS = {
    '1': ('individual', '개별 파일 (책마다 CSV)'),
    '2': ('merged', '통합 파일 (하나의 CSV)'),
}


def crawl_all_reviews(goods_dict, output_dir="./results", max_reviews_per_book=10, save_mode='individual'):
    """
    상품 목록에 대해 리뷰 크롤링
    
    goods_dict: {제목: 상품번호} 딕셔너리
    output_dir: 결과 저장 폴더
    max_reviews_per_book: 책당 최대 리뷰 수 (기본값: 10)
    save_mode: 'individual' (개별 파일) 또는 'merged' (통합 파일)
    """
    if not goods_dict:
        print("상품을 찾을 수 없습니다.")
        return
    
    # 출력 폴더 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 리뷰 크롤링
    print("\n" + "=" * 60)
    mode_name = "개별 파일" if save_mode == 'individual' else "통합 파일"
    print(f"📝 리뷰 크롤링 시작 (최대 {max_reviews_per_book}개씩, {mode_name})")
    print("=" * 60)
    
    results_summary = []
    all_reviews = []  # 통합 모드용
    
    for i, (title, goods_no) in enumerate(goods_dict.items(), 1):
        print(f"\n[{i}/{len(goods_dict)}] {title}")
        print("-" * 40)
        
        try:
            # 리뷰 크롤링 (최대 개수 제한)
            reviews = get_yes24_reviews(title, goods_no, max_reviews=max_reviews_per_book)
            
            if reviews:
                # 각 리뷰에 goods_no와 title 추가
                for review in reviews:
                    review['goods_no'] = goods_no
                    review['title'] = title
                
                if save_mode == 'individual':
                    # 개별 파일 저장
                    filename = sanitize_filename(title)
                    output_path = f"{output_dir}/{filename}.csv"
                    
                    df = pd.DataFrame(reviews)
                    cols = ['goods_no', 'title', 'rating', 'content', 'author', 'date']
                    df = df.reindex(columns=[c for c in cols if c in df.columns])
                    df.to_csv(output_path, index=False, encoding="utf-8-sig")
                    
                    print(f"✓ {len(reviews)}개 리뷰 저장: {output_path}")
                    results_summary.append({
                        'title': title,
                        'goods_no': goods_no,
                        'review_count': len(reviews),
                        'file': output_path
                    })
                else:
                    # 통합 모드: 리스트에 추가
                    all_reviews.extend(reviews)
                    print(f"✓ {len(reviews)}개 리뷰 수집")
                    results_summary.append({
                        'title': title,
                        'goods_no': goods_no,
                        'review_count': len(reviews)
                    })
            else:
                print(f"✗ 리뷰 없음")
                results_summary.append({
                    'title': title,
                    'goods_no': goods_no,
                    'review_count': 0,
                    'file': None if save_mode == 'individual' else None
                })
            
            # 서버 부하 방지를 위한 대기 (상품 간 2초)
            time.sleep(2)
            
        except Exception as e:
            print(f"✗ 에러 발생: {e}")
            results_summary.append({
                'title': title,
                'goods_no': goods_no,
                'review_count': -1,
                'file': None if save_mode == 'individual' else None
            })
    
    # 통합 모드: 모든 리뷰를 하나의 파일로 저장
    if save_mode == 'merged' and all_reviews:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_path = f"{output_dir}/reviews_{timestamp}.csv"
        
        df = pd.DataFrame(all_reviews)
        cols = ['goods_no', 'title', 'rating', 'content', 'author', 'date']
        df = df.reindex(columns=[c for c in cols if c in df.columns])
        df.to_csv(merged_path, index=False, encoding="utf-8-sig")
        
        print(f"\n📁 통합 파일 저장: {merged_path}")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("✅ 크롤링 완료!")
    print("=" * 60)
    
    total_reviews = sum(r['review_count'] for r in results_summary if r['review_count'] > 0)
    success_count = sum(1 for r in results_summary if r['review_count'] > 0)
    
    print(f"성공: {success_count}/{len(goods_dict)} 상품")
    print(f"총 리뷰 수: {total_reviews}개")
    
    # 요약 CSV 저장
    summary_df = pd.DataFrame(results_summary)
    summary_path = f"{output_dir}/_summary.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"📁 요약 파일: {summary_path}")
    
    return results_summary


def select_option(options, prompt):
    """사용자에게 옵션 선택 받기"""
    print(f"\n{prompt}")
    for key, (_, name) in options.items():
        print(f"  {key}. {name}")
    
    while True:
        choice = input("\n선택 (번호 입력): ").strip()
        if choice in options:
            return options[choice][0]
        print("잘못된 입력입니다. 다시 선택해주세요.")


def main_interactive():
    """인터랙티브 모드로 실행"""
    print("=" * 50)
    print("📚 예스24 리뷰 크롤러")
    print("=" * 50)
    
    # 1단계: 키워드 입력
    query = input("\n검색 키워드: ").strip()
    if not query:
        print("키워드를 입력해주세요.")
        return
    
    # 2단계: 검색 결과 수 입력
    print("\n📋 검색 결과 수:")
    size_input = input("입력 (기본값: 40): ").strip()
    size = int(size_input) if size_input.isdigit() else 40
    
    # 3단계: 정렬 방식 선택
    order = select_option(ORDER_OPTIONS, "📊 정렬 방식:")
    
    # 4단계: 검색 실행
    print(f"\n🔍 '{query}' 검색 중... (size={size}, order={order})")
    goods_dict = get_goods_no(query, size, order)
    
    if not goods_dict:
        print("상품을 찾을 수 없습니다.")
        return
    
    print(f"\n총 {len(goods_dict)}개 상품 발견:")
    for i, (title, goods_no) in enumerate(goods_dict.items(), 1):
        print(f"  {i}. {title} (상품번호: {goods_no})")
    
    # 5단계: 최대 리뷰 수 입력
    print("\n📝 책당 최대 리뷰 수:")
    max_reviews_input = input("입력 (기본값: 10): ").strip()
    max_reviews = int(max_reviews_input) if max_reviews_input.isdigit() else 10
    
    # 6단계: 저장 방식 선택
    save_mode = select_option(SAVE_MODE_OPTIONS, "💾 저장 방식:")
    
    # 7단계: 크롤링 실행
    crawl_all_reviews(goods_dict, max_reviews_per_book=max_reviews, save_mode=save_mode)


def main_cli():
    """CLI 인자로 실행 (빠른 실행용)"""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  인터랙티브: python main_crawler.py")
        print("  빠른 실행:  python main_crawler.py <키워드> [최대리뷰수] [size] [order] [save_mode]")
        print("")
        print("예시:")
        print('  python main_crawler.py "어린왕자" 10 40 RELATION individual')
        print('  python main_crawler.py "어린왕자" 10 40 RELATION merged')
        print("")
        print("size: 원하는 검색 결과 수")
        print("order: RELATION, RECENT, SINDEX_ONLY, REG_DTS, CONT_CNT, REVIE_CNT")
        print("save_mode: individual (개별파일), merged (통합파일)")
        sys.exit(1)
    
    query = sys.argv[1]
    max_reviews = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    order = sys.argv[4] if len(sys.argv) > 4 else 'RELATION'
    save_mode = sys.argv[5] if len(sys.argv) > 5 else 'individual'
    
    print("=" * 60)
    print(f"🔍 '{query}' 검색 중... (size={size}, order={order})")
    print("=" * 60)
    
    goods_dict = get_goods_no(query, size, order)
    
    if goods_dict:
        print(f"\n총 {len(goods_dict)}개 상품 발견:")
        for i, (title, goods_no) in enumerate(goods_dict.items(), 1):
            print(f"  {i}. {title} (상품번호: {goods_no})")
        
        crawl_all_reviews(goods_dict, max_reviews_per_book=max_reviews, save_mode=save_mode)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 인자 없으면 인터랙티브 모드
        main_interactive()
    else:
        # 인자 있으면 CLI 모드
        main_cli()
