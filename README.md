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
python main_crawler.py                          # 인터랙티브 모드
python main_crawler.py "키워드" 10 40 RELATION  # CLI 모드
```

**정렬 옵션:** RELATION(정확도), RECENT(신상품), SINDEX_ONLY(인기도), REG_DTS(등록일), CONT_CNT(평점), REVIE_CNT(리뷰)

### 교보문고

```bash
cd kyobo
python main_crawler.py                    # 인터랙티브 모드
python main_crawler.py "키워드" 10 40 qntt  # CLI 모드
```

**정렬 옵션:** qntt(판매량), date(최신), kcont(클로버리뷰), krvgr(클로버평점), 빈문자열(인기도)

## CLI 인자

```
python main_crawler.py <키워드> [최대리뷰수] [검색결과수] [정렬] [저장방식]
```

- `최대리뷰수`: 책당 최대 리뷰 수 (기본값: 10)
- `검색결과수`: 검색할 상품 수 (기본값: 40)
- `저장방식`: individual(개별파일), merged(통합파일)

## 출력

```
results/
├── <책제목>.csv    # 개별 리뷰 파일
└── _summary.csv    # 전체 요약
```
