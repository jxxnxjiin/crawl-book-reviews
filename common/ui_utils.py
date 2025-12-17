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
    검색 결과를 체크박스가 포함된 데이터 테이블로 표시하고 선택된 항목 반환
    
    Args:
        search_results: {제목: 상품번호} 딕셔너리
        session_key_prefix: 세션 키 접두사
        
    Returns:
        dict: 선택된 {제목: 상품번호} 딕셔너리
    """
    st.markdown("---")
    st.subheader(f"📋 검색 결과: '{st.session_state.get(f'{session_key_prefix}_search_keyword', '')}'")

    if not search_results:
        st.warning("표시할 검색 결과가 없습니다.")
        return {}

    # 1. 데이터프레임 생성 (기본적으로 '선택' 컬럼은 False)
    # 딕셔너리를 리스트로 변환
    data_list = [
        {"제목": title, "상품번호": str(goods_no), "선택": False} 
        for title, goods_no in search_results.items()
    ]
    df = pd.DataFrame(data_list)

    # 2. '전체 선택' 기능 추가 (옵션)
    # 전체 선택용 키 생성
    select_all_key = f"{session_key_prefix}_select_all"
    
    col_header, _ = st.columns([2, 8])
    with col_header:
        # 전체 선택 체크박스
        select_all = st.checkbox("✅ 전체 선택/해제", key=select_all_key)

    # 전체 선택이 켜져있으면 데이터의 '선택' 값을 모두 True로 설정
    if select_all:
        df["선택"] = True

    # 3. 데이터 에디터(수정 가능한 테이블) 표시
    st.markdown("### ✋ 아래 목록에서 책을 선택하세요")
    
    edited_df = st.data_editor(
        df,
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "선택",
                help="크롤링할 상품을 체크하세요",
                default=False,
                width="small"
            ),
            "제목": st.column_config.TextColumn(
                "제목",
                width="large",
                disabled=True  # 제목은 수정 불가능하게 설정
            )
        },
        hide_index=True,          # 인덱스 숨김
        use_container_width=True, # 가로폭 꽉 채우기
        height=400,               # 높이 고정 (스크롤 가능)
        key=f"{session_key_prefix}_editor" # 고유 키 설정
    )

    # 4. 선택된 행 필터링 및 반환 포맷 변환
    # '선택' 컬럼이 True인 행만 추출
    selected_rows = edited_df[edited_df["선택"] == True]

    if not selected_rows.empty:
        # 기존 로직과 호환되도록 {제목: 상품번호} 딕셔너리로 변환
        selected_goods = dict(zip(selected_rows["제목"], selected_rows["상품번호"]))
        
        st.info(f"📌 총 {len(selected_goods)}개 책이 선택되었습니다.")
        return selected_goods
    else:
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
