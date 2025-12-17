"""
Streamlit UI 관련 공통 유틸리티
"""

import streamlit as st
import pandas as pd
from datetime import datetime


# ==============================================================================
# 정렬 옵션 상수
# ==============================================================================

YES24_ORDER_OPTIONS = [
    ("RELATION", "정확도순"),
    ("RECENT", "신상품순"),
    ("SINDEX_ONLY", "인기도순"),
    ("REG_DTS", "등록일순"),
    ("CONT_CNT", "평점순"),
    ("REVIE_CNT", "리뷰순")
]

KYOBO_ORDER_OPTIONS = [
    ("qntt", "판매량순"),
    ("date", "최신순"),
    ("", "인기도순"),
    ("kcont", "클로버리뷰순"),
    ("krvgr", "클로버평점순"),
]


# ==============================================================================
# 진행 상황 관련
# ==============================================================================

def create_progress_callback():
    """
    진행 상황을 표시하는 콜백 함수 생성

    Returns:
        tuple: (progress_bar, status_text, progress_callback)
    """
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(current, total, message):
        status_text.text(f"[{current}/{total}] {message}")
        progress_bar.progress(current / total)

    return progress_bar, status_text, progress_callback


def cleanup_progress_ui(progress_bar, status_text):
    """진행 상황 UI 정리"""
    status_text.empty()
    progress_bar.empty()


# ==============================================================================
# 결과 처리
# ==============================================================================

def render_pipeline_result(result, filename_prefix, keyword=""):
    """
    파이프라인 실행 결과를 표시하고 CSV 다운로드 제공

    Args:
        result: {'status': ..., 'message': ..., 'data': ..., 'count': ...} 형태의 결과
        filename_prefix: 파일명 접두사 (예: 'yes24_reviews', 'kyobo_reviews')
        keyword: 검색 키워드 (파일명에 포함될 경우)
    """
    if result['status'] == 'error':
        st.error(f"❌ {result['message']}")
    elif result['count'] == 0:
        st.warning("⚠️ 수집된 데이터가 없습니다.")
    else:
        st.success(f"📊 {result['message']}")

        # 데이터프레임 표시
        df = pd.DataFrame(result['data'])
        st.dataframe(df, use_container_width=True)

        # CSV 다운로드
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv = df.to_csv(index=False, encoding='utf-8-sig')

        if keyword:
            filename = f"{filename_prefix}_{keyword}_{timestamp}.csv"
        else:
            filename = f"{filename_prefix}_{timestamp}.csv"

        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )


# ==============================================================================
# 검색 결과 선택
# ==============================================================================

def render_search_results_selection(search_results, session_key_prefix):
    """
    검색 결과를 표시하고 사용자 선택을 받는 UI

    Args:
        search_results: {제목: 상품번호} 딕셔너리
        session_key_prefix: 세션 키 접두사 (예: 'yes24', 'kyobo')

    Returns:
        dict: 선택된 {제목: 상품번호} 딕셔너리
    """
    st.markdown("---")
    st.subheader(f"📋 검색 결과: '{st.session_state[f'{session_key_prefix}_search_keyword']}'")

    # 검색 결과를 데이터프레임으로 표시
    df_results = pd.DataFrame([
        {
            "번호": idx,
            "제목": title,
            "상품번호": goods_no
        }
        for idx, (title, goods_no) in enumerate(search_results.items(), 1)
    ])

    st.dataframe(df_results, use_container_width=True, height=400)

    # 선택 UI
    st.markdown("### ✋ 크롤링할 책 선택")

    selected_titles = st.multiselect(
        "크롤링할 책 선택 (여러 개 선택 가능)",
        options=list(search_results.keys()),
        format_func=lambda x: x[:80] + "..." if len(x) > 80 else x,
        key=f"{session_key_prefix}_multiselect"
    )

    if selected_titles:
        selected_goods = {
            title: search_results[title]
            for title in selected_titles
        }
        st.info(f"📌 {len(selected_goods)}개 책 선택됨")
        return selected_goods

    return {}


def crawl_selected_reviews(selected_goods_dict, max_reviews, review_crawler_func):
    """
    선택된 상품들의 리뷰만 크롤링

    Args:
        selected_goods_dict: {제목: 상품번호} 딕셔너리
        max_reviews: 상품당 최대 리뷰 수
        review_crawler_func: 리뷰 크롤링 함수 (title, goods_no, max_reviews 인자를 받음)

    Returns:
        list: 수집된 리뷰 리스트
    """
    all_reviews = []
    total = len(selected_goods_dict)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, (title, goods_no) in enumerate(selected_goods_dict.items(), 1):
        status_text.text(f"[{idx}/{total}] {title[:50]}... 리뷰 수집 중")

        try:
            reviews = review_crawler_func(title, goods_no, max_reviews)

            for review in reviews:
                review['title'] = title
                review['goods_no'] = goods_no

            all_reviews.extend(reviews)
        except Exception as e:
            st.warning(f"⚠️ '{title[:30]}...' 리뷰 수집 실패: {str(e)}")

        progress_bar.progress(idx / total)

    status_text.empty()
    progress_bar.empty()

    return all_reviews


def render_crawl_results(all_reviews, filename_prefix):
    """
    크롤링 결과를 표시하고 CSV 다운로드 버튼 제공

    Args:
        all_reviews: 리뷰 리스트
        filename_prefix: 파일명 접두사 (예: 'yes24_reviews', 'kyobo_reviews')
    """
    if all_reviews:
        st.success(f"📊 총 {len(all_reviews)}개의 리뷰를 수집했습니다!")

        # 데이터프레임 표시
        df = pd.DataFrame(all_reviews)
        st.dataframe(df, use_container_width=True)

        # CSV 다운로드
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"{filename_prefix}_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("⚠️ 수집된 리뷰가 없습니다.")
