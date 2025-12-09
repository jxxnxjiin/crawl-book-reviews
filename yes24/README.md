# 📒 예스24 리뷰 크롤러

예스24 검색 결과 또는 카테고리 페이지에서 상품 리뷰를 수집합니다.

## 사용법

```bash
python main_crawler.py <URL> [최대리뷰수]
```

### 예시

```bash
# 검색 결과에서 크롤링 (기본 책당 10개 리뷰)
python main_crawler.py "https://www.yes24.com/product/search?query=블랙라벨"

# 책당 최대 20개 리뷰 수집
python main_crawler.py "https://www.yes24.com/product/search?query=블랙라벨" 20

# 카테고리 페이지에서 크롤링
python main_crawler.py "https://www.yes24.com/product/category/display/001001050003" 15
```

## 출력

- `results/<책제목>.csv` - 책별 리뷰 파일
- `results/_summary.csv` - 전체 요약

