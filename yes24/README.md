# 📒 예스24 리뷰 크롤러

예스24 도서에서 키워드 기반으로 상품 리뷰를 수집합니다.

## 파일 구조

```
yes24/
├── main_crawler.py      # 메인 실행
├── product_search.py    # 상품 검색
├── review_scraper.py    # 리뷰 스크래핑
└── utils/
    └── driver.py        # Chrome 드라이버 설정
```

## 설치

> Chrome/Chromium과 chromedriver가 설치되어 있어야 합니다.

```bash
pip install selenium beautifulsoup4 pandas requests
```

## 사용법

```bash
python main_crawler.py <키워드> [최대리뷰수]
```

### 예시

```bash
# 키워드로 검색 (기본 책당 10개 리뷰)
python main_crawler.py "어린왕자"

# 책당 최대 20개 리뷰 수집
python main_crawler.py "어린왕자" 20
```

## 출력

- `results/<책제목>.csv` - 책별 리뷰 파일
- `results/_summary.csv` - 전체 요약

