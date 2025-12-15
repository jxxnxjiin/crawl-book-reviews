"""
Yes24 Crawler Streamlit Web App

예스24 크롤러 웹 애플리케이션
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from pathlib import Path

from search_products import search_products
from get_goods_no import get_goods_no
from get_reviews import get_reviews
from get_books_info import get_book_info
from utils import build_newly_published_url


# 페이지 설정
st.set_page_config(
    page_title="Yes24 크롤러",
    page_icon="📚",
    layout="wide"
)

# 타이틀
st.title("📚 Yes24 크롤러")
st.markdown("---")

# 사이드바 - 파이프라인 선택
st.sidebar.title("크롤링 옵션")
pipeline = st.sidebar.radio(
    "파이프라인 선택",
    [
        "📕 키워드 검색 → 리뷰 크롤링",
        "📗 키워드 검색 → 세부정보 크롤링",
        "📙 카테고리 신간 → 세부정보 추출"
    ]
)
 
st.sidebar.markdown("---")


# 파이프라인 1: 키워드 검색 → 리뷰 크롤링
if pipeline.startswith("📕"):
    st.header("🔍 키워드 검색 → 리뷰 크롤링")

    col1, col2 = st.columns(2)

    with col1:
        keyword = st.text_input("검색 키워드", placeholder="예: 파이썬")

    with col2:
        order_option = st.selectbox(
            "정렬 방식",
            [
                ("RELATION", "정확도순"),
                ("RECENT", "신상품순"),
                ("SINDEX_ONLY", "인기도순"),
                ("REG_DTS", "등록일순"),
                ("CONT_CNT", "평점순"),
                ("REVIE_CNT", "리뷰순")
            ],
            format_func=lambda x: x[1]
        )

    col3, col4 = st.columns(2)

    with col3:
        max_products = st.number_input("최대 상품 수", min_value=1, max_value=100, value=10)

    with col4:
        max_reviews = st.number_input("상품당 최대 리뷰 수", min_value=1, max_value=100, value=10)

    if st.button("🚀 크롤링 시작", type="primary", use_container_width=True):
        if not keyword:
            st.error("❌ 검색 키워드를 입력해주세요!")
        else:
            with st.spinner(f"'{keyword}' 검색 중..."):
                # 상품 검색
                goods_dict = search_products(keyword, size=40, order=order_option[0], max_products=max_products)

                if not goods_dict:
                    st.error("❌ 검색 결과가 없습니다.")
                else:
                    st.success(f"✓ {len(goods_dict)}개의 상품을 찾았습니다!")

                    # 진행 상황 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    all_reviews = []
                    total_items = len(goods_dict)

                    for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
                        status_text.text(f"[{idx}/{total_items}] {title[:50]}... 리뷰 수집 중")

                        reviews = get_reviews(
                            title=title,
                            goods_no=goods_no,
                            max_reviews=max_reviews,
                            verbose=False
                        )

                        # 상품 정보 추가
                        for review in reviews:
                            review['product_title'] = title
                            review['goods_no'] = goods_no
                            all_reviews.append(review)

                        progress_bar.progress(idx / total_items)
                        time.sleep(0.3)  # 각 상품 처리 후 대기 (차단 방지)

                    status_text.empty()
                    progress_bar.empty()

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
                            file_name=f"search_reviews_{keyword}_{timestamp}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ 수집된 리뷰가 없습니다.")


# 파이프라인 2: 키워드 검색 → 세부정보 크롤링
elif pipeline.startswith("📗"):
    st.header("🔍 키워드 검색 → 세부정보 크롤링")

    col1, col2 = st.columns(2)

    with col1:
        keyword = st.text_input("검색 키워드", placeholder="예: 파이썬")

    with col2:
        order_option = st.selectbox(
            "정렬 방식",
            [
                ("RELATION", "정확도순"),
                ("RECENT", "신상품순"),
                ("SINDEX_ONLY", "인기도순"),
                ("REG_DTS", "등록일순"),
                ("CONT_CNT", "평점순"),
                ("REVIE_CNT", "리뷰순")
            ],
            format_func=lambda x: x[1]
        )

    col3, col4 = st.columns(2)

    with col3:
        max_products = st.number_input("최대 상품 수", min_value=1, max_value=100, value=10)

    with col4:
        st.write("")  # 레이아웃 균형을 위한 빈 공간

    if st.button("🚀 크롤링 시작", type="primary", use_container_width=True):
        if not keyword:
            st.error("❌ 검색 키워드를 입력해주세요!")
        else:
            with st.spinner(f"'{keyword}' 검색 중..."):
                # 상품 검색
                goods_dict = search_products(keyword, size=40, order=order_option[0], max_products=max_products)

                if not goods_dict:
                    st.error("❌ 검색 결과가 없습니다.")
                else:
                    st.success(f"✓ {len(goods_dict)}개의 상품을 찾았습니다!")

                    # 진행 상황 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    all_books_info = []
                    total_items = len(goods_dict)

                    for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
                        status_text.text(f"[{idx}/{total_items}] {title[:50]}... 세부정보 추출 중")

                        info = get_book_info(goods_no)
                        all_books_info.append(info)

                        progress_bar.progress(idx / total_items)
                        time.sleep(0.3)  # 각 상품 처리 후 대기 (차단 방지)

                    status_text.empty()
                    progress_bar.empty()

                    if all_books_info:
                        st.success(f"📊 총 {len(all_books_info)}개의 도서 정보를 추출했습니다!")

                        # 데이터프레임 표시
                        df = pd.DataFrame(all_books_info)
                        st.dataframe(df, use_container_width=True)

                        # CSV 다운로드
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        csv = df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 CSV 다운로드",
                            data=csv,
                            file_name=f"search_books_{keyword}_{timestamp}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ 수집된 도서 정보가 없습니다.")


# 파이프라인 3: 카테고리 신간 → 세부정보 추출
elif pipeline.startswith("📙"):
    st.header("📚 카테고리 신간 → 세부정보 추출")

    # 카테고리 로드 (JSON 파일 직접 읽기)
    cache_file = Path(__file__).parent / "categories_cache.json"
    st.warning(f"🔍 DEBUG: 파일 경로 = {cache_file}")
    st.warning(f"🔍 DEBUG: 파일 존재? = {cache_file.exists()}")

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            categories = json.load(f)
        st.warning(f"🔍 DEBUG: 로드된 카테고리 수 = {len(categories)}")
        depth1 = {k: v for k, v in categories.items() if v['depth'] == 1}
        st.warning(f"🔍 DEBUG: 대분류 = {list(depth1.keys())}")
    except Exception as e:
        st.error(f"❌ 카테고리 파일 읽기 실패: {e}")
        categories = {}

    if not categories:
        st.error("❌ 카테고리를 가져올 수 없습니다.")
    else:
        # 대분류 (depth=1) 추출
        major_categories = {cat_id: info for cat_id, info in categories.items() if info['depth'] == 1}

        # 대분류 선택
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
                    index=0
                )
                selected_major_id = selected_major[0]

            with col2:
                # 중분류 (선택한 대분류의 직계 자식) 추출
                minor_cat_ids = categories[selected_major_id]['children']
                minor_categories = {cat_id: categories[cat_id] for cat_id in minor_cat_ids}

                if minor_categories:
                    minor_options = [(cat_id, info['name']) for cat_id, info in sorted(minor_categories.items())]
                    selected_minor = st.selectbox(
                        f"중분류 선택 (총 {len(minor_categories)}개)",
                        minor_options,
                        format_func=lambda x: x[1]
                    )

                    # 선택한 카테고리 ID와 이름 추출
                    selected_cat_id = selected_minor[0]
                    selected_cat_name = selected_minor[1]
                else:
                    # 중분류가 없으면 대분류 사용
                    selected_cat_id = selected_major_id
                    selected_cat_name = selected_major[1]
                    st.info("중분류가 없어 대분류를 사용합니다.")

            # 크롤링 옵션
            max_products = st.number_input("최대 상품 수", min_value=1, max_value=100, value=10)

            if st.button("🚀 크롤링 시작", type="primary", use_container_width=True):
                with st.spinner(f"'{selected_cat_name}' 신간도서 검색 중..."):
                    # 신간도서 가져오기
                    url = build_newly_published_url(selected_cat_id)
                    goods_dict = get_goods_no(url, max_products=max_products)

                    if not goods_dict:
                        st.error("❌ 신간도서를 찾을 수 없습니다.")
                    else:
                        st.success(f"✓ {len(goods_dict)}개의 신간도서를 찾았습니다!")

                        # 진행 상황 표시
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        all_books_info = []
                        total_items = len(goods_dict)

                        for idx, (title, goods_no) in enumerate(goods_dict.items(), 1):
                            status_text.text(f"[{idx}/{total_items}] {title[:50]}... 세부정보 추출 중")

                            info = get_book_info(goods_no)
                            info['category_id'] = selected_cat_id
                            info['category_name'] = selected_cat_name
                            all_books_info.append(info)

                            progress_bar.progress(idx / total_items)
                            time.sleep(0.3)  # 각 상품 처리 후 대기 (차단 방지)

                        status_text.empty()
                        progress_bar.empty()

                        if all_books_info:
                            st.success(f"📊 총 {len(all_books_info)}개의 도서 정보를 추출했습니다!")

                            # 데이터프레임 표시
                            df = pd.DataFrame(all_books_info)
                            st.dataframe(df, use_container_width=True)

                            # CSV 다운로드
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            csv = df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📥 CSV 다운로드",
                                data=csv,
                                file_name=f"category_books_{selected_cat_id}_{timestamp}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        else:
                            st.warning("⚠️ 수집된 도서 정보가 없습니다.")


# Footer
st.markdown("---")