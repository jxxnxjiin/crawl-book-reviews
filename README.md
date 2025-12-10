# 📚 도서 리뷰 크롤러

예스24, 교보문고에서 키워드 기반으로 도서 리뷰를 수집합니다.

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 예스24

```bash
cd yes24
python main_crawler.py                         # 인터랙티브 모드
python main_crawler.py "키워드" 10 40 RELATION  # CLI 모드
```

**정렬 옵션:** 정확도(`RELATION`), 신상품(`RECENT`), 인기도(`SINDEX_ONLY`), 등록일(`REG_DTS`), 평점(`CONT_CNT`), 리뷰(`REVIE_CNT`)

### 교보문고

```bash
cd kyobo
python main_crawler.py                     # 인터랙티브 모드
python main_crawler.py "키워드" 10 40 qntt  # CLI 모드
```

**정렬 옵션:** 인기도, 판매량(`qntt`), 최신순(`date`), 클로버리뷰(`kcont`), 클로버평점(`krvgr`)

## CLI 인자

```
python main_crawler.py <키워드> [최대리뷰수] [검색결과수] [정렬] [저장방식]
```

- `최대리뷰수`: 책당 최대 리뷰 수 (기본값: 10)
- `검색결과수`: 검색할 상품 수 (기본값: 40)
- `저장방식`: individual(개별파일), merged(통합파일)