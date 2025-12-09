"""
예스24 리뷰 크롤러 메인 스크립트
1. 검색 결과에서 상품 목록 추출
2. 각 상품별로 리뷰 크롤링 (최대 10개씩)
3. 책 한 권당 CSV 파일 하나씩 저장
"""

from goods_no_crawler import get_goods_no
from yes24_review_crawler import get_yes24_reviews, sanitize_filename
import pandas as pd
import os
import sys
import time


def crawl_all_reviews(query, output_dir="./results", max_reviews_per_book=10):
    """
    검색 결과의 모든 상품에 대해 리뷰 크롤링
    
    query: 검색 키워드 또는 URL
    output_dir: 결과 저장 폴더
    max_reviews_per_book: 책당 최대 리뷰 수 (기본값: 10)
    """
    
    # 1. 검색 결과에서 상품 목록 가져오기
    print("=" * 60)
    print("1단계: 검색 결과에서 상품 목록 추출")
    print("=" * 60)
    
    goods_dict = get_goods_no(query)
    
    if not goods_dict:
        print("상품을 찾을 수 없습니다.")
        return
    
    print(f"총 {len(goods_dict)}개 상품 발견:\n")
    for i, (title, goods_no) in enumerate(goods_dict.items(), 1):
        print(f"  {i}. {title} (상품번호: {goods_no})")
    
    # 출력 폴더 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. 각 상품별로 리뷰 크롤링
    print("\n" + "=" * 60)
    print(f"2단계: 각 상품별 리뷰 크롤링 (최대 {max_reviews_per_book}개씩)")
    print("=" * 60)
    
    results_summary = []
    
    for i, (title, goods_no) in enumerate(goods_dict.items(), 1):
        print(f"\n[{i}/{len(goods_dict)}] {title}")
        print("-" * 40)
        
        try:
            # 리뷰 크롤링 (최대 개수 제한)
            reviews, _ = get_yes24_reviews(goods_no, max_reviews=max_reviews_per_book)
            
            # 파일명 생성
            filename = sanitize_filename(title)
            output_path = f"{output_dir}/{filename}.csv"
            
            # 저장
            if reviews:
                # 각 리뷰에 goods_no와 title 추가
                for review in reviews:
                    review['goods_no'] = goods_no
                    review['title'] = title
                
                df = pd.DataFrame(reviews)
                # 컬럼 순서 정리
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
                print(f"✗ 리뷰 없음")
                results_summary.append({
                    'title': title,
                    'goods_no': goods_no,
                    'review_count': 0,
                    'file': None
                })
            
            # 서버 부하 방지를 위한 대기 (상품 간 5초)
            time.sleep(5)
            
        except Exception as e:
            print(f"✗ 에러 발생: {e}")
            results_summary.append({
                'title': title,
                'goods_no': goods_no,
                'review_count': -1,
                'file': None
            })
    
    # 3. 결과 요약
    print("\n" + "=" * 60)
    print("크롤링 완료!")
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python main_crawler.py <키워드|URL> [최대리뷰수]")
        print('예시: python main_crawler.py "어린왕자자" 10')
        print('예시: python main_crawler.py "https://www.yes24.com/product/category/display/001001050003" 20')
        sys.exit(1)
    
    query = sys.argv[1]
    max_reviews = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    crawl_all_reviews(query, max_reviews_per_book=max_reviews)
