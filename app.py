"""
통합 도서 크롤러 Streamlit Web App

Yes24, 교보문고 크롤러 통합 웹 애플리케이션
"""

import streamlit as st
import json
import sys
from pathlib import Path

# 상위 경로를 sys.path에 추가
sys.path.append(str(Path(__file__).parent))

# Yes24 크롤러 import
from yes24.pipeline import run_search_reviews as yes24_search_reviews
from yes24.pipeline import run_search_bookinfo as yes24_search_bookinfo
from yes24.pipeline import run_category_bookinfo as yes24_category_bookinfo
from yes24.get_reviews import get_reviews as yes24_get_reviews
from yes24.get_books_info import get_book_info as yes24_get_book_info
from yes24.search_products import search_products as yes24_search_products
from yes24.utils import build_newly_published_url
from yes24.get_goods_no import get_goods_no as yes24_get_goods_no

# 교보문고 크롤러 import
from kyobo.pipeline import run_search_reviews as kyobo_search_reviews
from kyobo.product_search import get_goods_no as kyobo_get_goods_no
from kyobo.review_scraper import get_kyobo_reviews

# 공통 UI 유틸리티 import
from common.ui_utils import (
    YES24_ORDER_OPTIONS,
    KYOBO_ORDER_OPTIONS,
    create_progress_callback,
    cleanup_progress_ui,
    render_pipeline_result,
    render_search_results_selection,
    crawl_selected_reviews,
    render_crawl_results,
)

# 페이지 설정
st.set_page_config(
    page_title="도서 크롤러",
    page_icon="📚",
    layout="wide"
)


# ==============================================================================
# 메인 UI
# ==============================================================================

# 타이틀
st.title("📚 도서 정보 크롤러")
st.markdown("---")

# 사이드바 - 크롤러 선택
crawler = st.pills(
    "메뉴 선택",
    ["🏠 홈", "Yes24", "교보문고"],
    selection_mode="single",
    default="🏠 홈",
    label_visibility="collapsed"
)

st.markdown("---")


# ==============================================================================
# Yes24 크롤러
# ==============================================================================
if crawler == "Yes24":
    pipeline = st.segmented_control(
    "파이프라인 선택",
    options=[
            "📕 키워드 검색 → 리뷰 크롤링",
            "📗 키워드 검색 → 세부정보 크롤링",
            "📙 카테고리 신간 → 세부정보 추출"
        ],
    selection_mode="single",
    default="📕 키워드 검색 → 리뷰 크롤링",
    )

    # 크롤링 모드 선택 (모든 파이프라인 공통)
    crawl_mode = st.segmented_control(
        "크롤링 모드",
        options=["🤖 자동 크롤링 (상위 N개)", "✋ 직접 선택"],
        selection_mode="single"
    )
    st.markdown("---")

    # ===========================================================================
    # 파이프라인 1: 키워드 검색 → 리뷰 크롤링
    # ===========================================================================
    if pipeline.startswith("📕"):
        st.header("🔍 Yes24 키워드 검색 → 리뷰 크롤링")

        # ========== 자동 크롤링 모드 ==========
        if crawl_mode == "🤖 자동 크롤링 (상위 N개)":
            col1, col2 = st.columns(2)

            with col1:
                keyword = st.text_input("검색 키워드", placeholder="예: 파이썬", key="yes24_review_auto_keyword")

            with col2:
                order_option = st.selectbox(
                    "정렬 방식",
                    YES24_ORDER_OPTIONS,
                    format_func=lambda x: x[1],
                    key="yes24_review_auto_order"
                )

            col3, col4 = st.columns(2)

            with col3:
                max_products = st.number_input("최대 상품 수", min_value=1, max_value=100, value=10, key="yes24_review_auto_products")

            with col4:
                max_reviews = st.number_input("상품당 최대 리뷰 수", min_value=1, max_value=100, value=10, key="yes24_review_auto_reviews")

            if st.button("🚀 크롤링 시작", type="primary", key="yes24_review_auto_start"):
                if not keyword:
                    st.error("❌ 검색 키워드를 입력해주세요!")
                else:
                    progress_bar, status_text, progress_callback = create_progress_callback()
                    result = yes24_search_reviews(
                        keyword=keyword,
                        max_products=max_products,
                        max_reviews=max_reviews,
                        order=order_option[0],
                        progress_callback=progress_callback
                    )
                    cleanup_progress_ui(progress_bar, status_text)
                    render_pipeline_result(result, "yes24_reviews", keyword)

        # ========== 직접 선택 모드 ==========
        else:
            col1, col2 = st.columns(2)

            with col1:
                keyword = st.text_input("검색 키워드", placeholder="예: 미적분", key="yes24_review_manual_keyword")

            with col2:
                search_size = st.number_input("검색 결과 수", min_value=10, max_value=120, value=40, step=10, key="yes24_review_manual_size")

            if st.button("🔍 검색하기", type="primary", key="yes24_review_manual_search"):
                if not keyword:
                    st.error("❌ 검색 키워드를 입력해주세요!")
                else:
                    with st.spinner("검색 중..."):
                        try:
                            goods_dict = yes24_search_products(keyword, max_products=search_size)
                            if goods_dict:
                                st.session_state.yes24_review_search_results = goods_dict
                                st.session_state.yes24_review_search_keyword = keyword
                                st.success(f"✅ {len(goods_dict)}개 상품 검색 완료!")
                            else:
                                st.warning("⚠️ 검색 결과가 없습니다.")
                        except Exception as e:
                            st.error(f"❌ 검색 실패: {str(e)}")

            if 'yes24_review_search_results' in st.session_state:
                selected_goods = render_search_results_selection(
                    st.session_state.yes24_review_search_results,
                    'yes24_review'
                )

                if selected_goods:
                    max_reviews = st.number_input("상품당 최대 리뷰 수", min_value=1, max_value=100, value=10, key="yes24_review_manual_max")

                    if st.button("🚀 선택한 책 크롤링 시작", type="primary", key="yes24_review_manual_start"):
                        st.markdown("---")
                        def yes24_review_wrapper(title, goods_no, max_rev):
                            return yes24_get_reviews(title, goods_no, max_rev, verbose=False)

                        all_reviews = crawl_selected_reviews(selected_goods, max_reviews, yes24_review_wrapper)
                        render_crawl_results(all_reviews, "yes24_reviews_selected")

    # ===========================================================================
    # 파이프라인 2: 키워드 검색 → 세부정보 크롤링
    # ===========================================================================
    elif pipeline.startswith("📗"):
        st.header("🔍 Yes24 키워드 검색 → 세부정보 크롤링")

        # ========== 자동 크롤링 모드 ==========
        if crawl_mode == "🤖 자동 크롤링 (상위 N개)":
            col1, col2 = st.columns(2)

            with col1:
                keyword = st.text_input("검색 키워드", placeholder="예: 파이썬", key="yes24_bookinfo_auto_keyword")

            with col2:
                order_option = st.selectbox(
                    "정렬 방식",
                    YES24_ORDER_OPTIONS,
                    format_func=lambda x: x[1],
                    key="yes24_bookinfo_auto_order"
                )

            max_products = st.number_input("최대 상품 수", min_value=1, max_value=100, value=10, key="yes24_bookinfo_auto_products")

            if st.button("🚀 크롤링 시작", type="primary", key="yes24_bookinfo_auto_start"):
                if not keyword:
                    st.error("❌ 검색 키워드를 입력해주세요!")
                else:
                    progress_bar, status_text, progress_callback = create_progress_callback()
                    result = yes24_search_bookinfo(
                        keyword=keyword,
                        max_products=max_products,
                        order=order_option[0],
                        progress_callback=progress_callback
                    )
                    cleanup_progress_ui(progress_bar, status_text)
                    render_pipeline_result(result, "yes24_books", keyword)

        # ========== 직접 선택 모드 ==========
        else:
            col1, col2 = st.columns(2)

            with col1:
                keyword = st.text_input("검색 키워드", placeholder="예: 기하와 벡터", key="yes24_bookinfo_manual_keyword")

            with col2:
                search_size = st.number_input("검색 결과 수", min_value=10, max_value=120, value=40, step=10, key="yes24_bookinfo_manual_size")

            if st.button("🔍 검색하기", type="primary", key="yes24_bookinfo_manual_search"):
                if not keyword:
                    st.error("❌ 검색 키워드를 입력해주세요!")
                else:
                    with st.spinner("검색 중..."):
                        try:
                            goods_dict = yes24_search_products(keyword, max_products=search_size)
                            if goods_dict:
                                st.session_state.yes24_bookinfo_search_results = goods_dict
                                st.session_state.yes24_bookinfo_search_keyword = keyword
                                st.success(f"✅ {len(goods_dict)}개 상품 검색 완료!")
                            else:
                                st.warning("⚠️ 검색 결과가 없습니다.")
                        except Exception as e:
                            st.error(f"❌ 검색 실패: {str(e)}")

            if 'yes24_bookinfo_search_results' in st.session_state:
                selected_goods = render_search_results_selection(
                    st.session_state.yes24_bookinfo_search_results,
                    'yes24_bookinfo'
                )

                if selected_goods:
                    if st.button("🚀 선택한 책 크롤링 시작", type="primary", key="yes24_bookinfo_manual_start"):
                        st.markdown("---")

                        # 세부정보 크롤링
                        all_books = []
                        total = len(selected_goods)
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for idx, (title, goods_no) in enumerate(selected_goods.items(), 1):
                            status_text.text(f"[{idx}/{total}] {title[:50]}... 세부정보 수집 중")
                            try:
                                book_info = yes24_get_book_info(goods_no)
                                all_books.append(book_info)
                            except Exception as e:
                                st.warning(f"⚠️ '{title[:30]}...' 정보 수집 실패: {str(e)}")
                            progress_bar.progress(idx / total)

                        status_text.empty()
                        progress_bar.empty()

                        render_crawl_results(all_books, "yes24_books_selected")

    # ===========================================================================
    # 파이프라인 3: 카테고리 신간 → 세부정보 추출
    # ===========================================================================
    elif pipeline.startswith("📙"):
        st.header("📚 Yes24 카테고리 신간 → 세부정보 추출")

        # 카테고리 로드
        cache_file = Path(__file__).parent / "yes24" / "yes24_categories.json"
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                categories = json.load(f)
        except Exception as e:
            st.error(f"❌ 카테고리 파일 읽기 실패: {e}")
            categories = {}

        if not categories:
            st.error("❌ 카테고리를 가져올 수 없습니다.")
        else:
            major_categories = {cat_id: info for cat_id, info in categories.items() if info['depth'] == 1}
            major_options = [(cat_id, info['name']) for cat_id, info in sorted(major_categories.items())]

            if not major_options:
                st.error("❌ 대분류를 찾을 수 없습니다.")
            else:
                col1, col2 = st.columns(2)

                with col1:
                    selected_major = st.radio(
                        "대분류 선택",
                        major_options,
                        format_func=lambda x: f"{x[1]}",
                        index=0,
                        key="yes24_category_major"
                    )
                    selected_major_id = selected_major[0]

                with col2:
                    minor_cat_ids = categories[selected_major_id]['children']
                    minor_categories = {cat_id: categories[cat_id] for cat_id in minor_cat_ids}

                    if minor_categories:
                        minor_options = [(cat_id, info['name']) for cat_id, info in sorted(minor_categories.items())]
                        selected_minor = st.selectbox(
                            f"중분류 선택 (총 {len(minor_categories)}개)",
                            minor_options,
                            format_func=lambda x: x[1],
                            key="yes24_category_minor"
                        )
                        selected_cat_id = selected_minor[0]
                        selected_cat_name = selected_minor[1]
                    else:
                        selected_cat_id = selected_major_id
                        selected_cat_name = selected_major[1]
                        st.info("중분류가 없어 대분류를 사용합니다.")

                # ========== 자동 크롤링 모드 ==========
                if crawl_mode == "🤖 자동 크롤링 (상위 N개)":
                    max_products = st.number_input("최대 상품 수", min_value=1, max_value=100, value=10, key="yes24_category_auto_products")

                    if st.button("🚀 크롤링 시작", type="primary", key="yes24_category_auto_start"):
                        progress_bar, status_text, progress_callback = create_progress_callback()
                        result = yes24_category_bookinfo(
                            category_id=selected_cat_id,
                            category_name=selected_cat_name,
                            max_products=max_products,
                            progress_callback=progress_callback
                        )
                        cleanup_progress_ui(progress_bar, status_text)
                        render_pipeline_result(result, f"yes24_category_{selected_cat_id}")

                # ========== 직접 선택 모드 ==========
                else:
                    search_size = st.number_input("검색 결과 수", min_value=10, max_value=100, value=40, step=10, key="yes24_category_manual_size")

                    if st.button("🔍 카테고리 신간 검색하기", type="primary", key="yes24_category_manual_search"):
                        with st.spinner("검색 중..."):
                            try:
                                # 신간 목록 가져오기
                                url = build_newly_published_url(selected_cat_id, page=1)
                                goods_dict = yes24_get_goods_no(url, max_products=search_size)

                                if goods_dict:
                                    st.session_state.yes24_category_search_results = goods_dict
                                    st.session_state.yes24_category_search_keyword = selected_cat_name
                                    st.success(f"✅ {len(goods_dict)}개 상품 검색 완료!")
                                else:
                                    st.warning("⚠️ 검색 결과가 없습니다.")
                            except Exception as e:
                                st.error(f"❌ 검색 실패: {str(e)}")

                    if 'yes24_category_search_results' in st.session_state:
                        selected_goods = render_search_results_selection(
                            st.session_state.yes24_category_search_results,
                            'yes24_category'
                        )

                        if selected_goods:
                            if st.button("🚀 선택한 책 크롤링 시작", type="primary", key="yes24_category_manual_start"):
                                st.markdown("---")

                                # 세부정보 크롤링
                                all_books = []
                                total = len(selected_goods)
                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                for idx, (title, goods_no) in enumerate(selected_goods.items(), 1):
                                    status_text.text(f"[{idx}/{total}] {title[:50]}... 세부정보 수집 중")
                                    try:
                                        book_info = yes24_get_book_info(goods_no)
                                        all_books.append(book_info)
                                    except Exception as e:
                                        st.warning(f"⚠️ '{title[:30]}...' 정보 수집 실패: {str(e)}")
                                    progress_bar.progress(idx / total)

                                status_text.empty()
                                progress_bar.empty()

                                render_crawl_results(all_books, f"yes24_category_{selected_cat_id}_selected")


# ==============================================================================
# 교보문고 크롤러
# ==============================================================================
elif crawler == "교보문고":
    st.header("🔍 교보문고 키워드 검색 → 리뷰 크롤링")

    # 크롤링 모드 선택
    crawl_mode = st.segmented_control(
        "크롤링 모드",
        options =["🤖 자동 크롤링 (상위 N개)", "✋ 직접 선택"],
        selection_mode="single"
    )
    st.markdown("---")

    # ========== 자동 크롤링 모드 ==========
    if crawl_mode == "🤖 자동 크롤링 (상위 N개)":
        col1, col2 = st.columns(2)

        with col1:
            keyword = st.text_input("검색 키워드", placeholder="예: 기하와 벡터", key="kyobo_auto_keyword")

        with col2:
            order_option = st.selectbox(
                "정렬 방식",
                KYOBO_ORDER_OPTIONS,
                format_func=lambda x: x[1],
                key="kyobo_auto_order"
            )

        col3, col4 = st.columns(2)

        with col3:
            max_products = st.number_input("최대 상품 수", min_value=1, max_value=100, value=10, key="kyobo_auto_products")

        with col4:
            max_reviews = st.number_input("상품당 최대 리뷰 수", min_value=1, max_value=100, value=10, key="kyobo_auto_reviews")

        if st.button("🚀 크롤링 시작", type="primary", key="kyobo_auto_start"):
            if not keyword:
                st.error("❌ 검색 키워드를 입력해주세요!")
            else:
                progress_bar, status_text, progress_callback = create_progress_callback()
                result = kyobo_search_reviews(
                    keyword=keyword,
                    max_products=max_products,
                    max_reviews_per_book=max_reviews,
                    order=order_option[0],
                    progress_callback=progress_callback
                )
                cleanup_progress_ui(progress_bar, status_text)
                render_pipeline_result(result, "kyobo_reviews", keyword)

    # ========== 직접 선택 모드 ==========
    else:
        col1, col2 = st.columns(2)

        with col1:
            keyword = st.text_input("검색 키워드", placeholder="예: 확률과 통계", key="kyobo_manual_keyword")

        with col2:
            search_size = st.number_input("검색 결과 수", min_value=10, max_value=100, value=40, step=10, key="kyobo_manual_size")

        if st.button("🔍 검색하기", type="primary", key="kyobo_manual_search"):
            if not keyword:
                st.error("❌ 검색 키워드를 입력해주세요!")
            else:
                with st.spinner("검색 중..."):
                    try:
                        goods_dict = kyobo_get_goods_no(keyword, size=search_size)
                        if goods_dict:
                            st.session_state.kyobo_search_results = goods_dict
                            st.session_state.kyobo_search_keyword = keyword
                            st.success(f"✅ {len(goods_dict)}개 상품 검색 완료!")
                        else:
                            st.warning("⚠️ 검색 결과가 없습니다.")
                    except Exception as e:
                        st.error(f"❌ 검색 실패: {str(e)}")

        if 'kyobo_search_results' in st.session_state:
            selected_goods = render_search_results_selection(
                st.session_state.kyobo_search_results,
                'kyobo'
            )

            if selected_goods:
                max_reviews = st.number_input("상품당 최대 리뷰 수", min_value=1, max_value=100, value=10, key="kyobo_manual_max")

                if st.button("🚀 선택한 책 크롤링 시작", type="primary", key="kyobo_manual_start"):
                    st.markdown("---")
                    all_reviews = crawl_selected_reviews(selected_goods, max_reviews, get_kyobo_reviews)
                    render_crawl_results(all_reviews, "kyobo_reviews_selected")

else:
    st.container(border=True).markdown("""
    ### 시작하려면 서점을 선택하세요
    
    **Yes24** 또는 **교보문고**를 선택하면 크롤링 옵션이 나타납니다.
    """)
# Footer
st.markdown("---")
st.caption("📚 도서 크롤러 v1.0 - Yes24 & 교보문고")
