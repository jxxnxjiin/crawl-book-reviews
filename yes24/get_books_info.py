import requests
from bs4 import BeautifulSoup
import re
from utils import HEADERS, build_book_url

### 세부 정보 추출 ###
def get_book_info(goods_no):
    """
    상품 상세 페이지에서 정보 추출

    반환값: {
        'goods_no': 상품번호,
        'title': 제목,
        'author': 저자,
        'publisher': 출판사,
        'pub_date': 출간일,
        'pages': 쪽수,
        'size': 크기,
        'category_path': 카테고리 경로 (대분류>중분류>소분류>...)
    }
    """
    url = build_book_url(goods_no)

    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    info = {'goods_no': goods_no}

    # 제목
    title_tag = soup.select_one('.gd_name')
    info['title'] = title_tag.get_text(strip=True) if title_tag else ""

    # 저자/출판사 정보
    pub_area = soup.select_one('.gd_pubArea')
    if pub_area:
        # 저자
        author_tag = pub_area.select_one('.gd_auth a')
        info['author'] = author_tag.get_text(strip=True) if author_tag else ""

        # 출판사
        pub_tag = pub_area.select_one('.gd_pub a')
        info['publisher'] = pub_tag.get_text(strip=True) if pub_tag else ""

        # 출간일
        date_tag = pub_area.select_one('.gd_date')
        info['pub_date'] = date_tag.get_text(strip=True) if date_tag else ""
    else:
        info['author'] = ""
        info['publisher'] = ""
        info['pub_date'] = ""

    # 품목정보에서 쪽수, 크기 추출
    spec_section = soup.select_one('#infoset_specific')
    info['pages'] = ""
    info['size'] = ""

    if spec_section:
        rows = spec_section.select('tr')
        for row in rows:
            th = row.select_one('th')
            td = row.select_one('td')
            if th and td:
                th_text = th.get_text(strip=True)
                td_text = td.get_text(strip=True)

                if '쪽수' in th_text or '무게' in th_text:
                    # "160쪽 | 215*285*20mm" 형태 파싱
                    parts = td_text.split('|')
                    if len(parts) >= 1:
                        pages_match = re.search(r'(\d+)쪽', parts[0])
                        info['pages'] = pages_match.group(1) if pages_match else ""
                    if len(parts) >= 2:
                        info['size'] = parts[-1].strip()

    # 관련분류 (카테고리 경로)
    cate_section = soup.select_one('#infoset_goodsCate')
    info['category_path'] = ""

    if cate_section:
        # 첫 번째 카테고리 경로만 추출
        links = cate_section.select('a')
        if links:
            # 중복 제거하면서 순서 유지
            seen = set()
            path_parts = []
            for link in links:
                text = link.get_text(strip=True)
                if text and text not in seen:
                    seen.add(text)
                    path_parts.append(text)
                    # 첫 번째 전체 경로만 (보통 4-5단계)
                    if len(path_parts) >= 4:
                        break
            info['category_path'] = " > ".join(path_parts)

    # 책 소개
    intro_section = soup.select_one('#infoset_introduce')
    info['description'] = ""

    if intro_section:
        # infoWrap_txtInner 또는 txtContentText에서 텍스트 추출
        txt_inner = intro_section.select_one('.infoWrap_txtInner')
        if txt_inner:
            # textarea 내용 또는 일반 텍스트
            textarea = txt_inner.select_one('textarea')
            if textarea:
                info['description'] = textarea.get_text(strip=True)
            else:
                info['description'] = txt_inner.get_text(strip=True)
        else:
            # 대체: 전체 섹션에서 추출
            info['description'] = intro_section.get_text(strip=True).replace('책소개', '', 1).strip()

    return info