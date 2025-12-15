"""
예스24
카테고리 계층 구조를 딕셔너리 형태로 추출
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path


def get_categories(category_number="001", use_cache=True, cache_file="categories_cache.json"):
    """
    신간도서 페이지에서 카테고리 목록 추출

    category_number: 대분류 카테고리 번호 (기본값: 001 = 국내도서)
    use_cache: 캐시 파일 사용 여부 (기본값: True)
    cache_file: 캐시 파일 경로 (기본값: categories_cache.json)

    반환값:
    {
        "001": {"name": "국내도서", "depth": 1, "children": ["001001001", ...]},
        "001001001": {"name": "소설/시/희곡", "depth": 2, "children": [...]},
        ...
    }
    """
    cache_path = Path(cache_file)

    # 절대 경로가 아니면 현재 스크립트 디렉토리 기준으로 변경
    if not cache_path.is_absolute():
        cache_path = Path(__file__).parent / cache_file

    # 캐시 파일이 있으면 로드
    if use_cache and cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                categories = json.load(f)
                print(f"✓ 캐시 파일에서 {len(categories)}개 카테고리 로드: {cache_path}")
                return categories
        except Exception as e:
            print(f"⚠ 캐시 파일 로드 실패: {e}")

    # 웹에서 카테고리 정보 가져오기
    print(f"웹에서 카테고리 정보 가져오는 중...")
    url = f"https://www.yes24.com/product/category/newproduct?categoryNumber={category_number}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    categories = {}

    # 카테고리 li 태그 찾기
    cat_elements = soup.select('li[id^="category"]')

    for elem in cat_elements:
        cat_id = elem.get('id', '').replace('category', '')
        if not cat_id:
            continue

        # 카테고리 이름 추출
        name_tag = elem.select_one('em.txt')
        name = name_tag.get_text(strip=True) if name_tag else ""

        if not name:
            continue

        # 깊이 계산 (001 = 1, 001001 = 2, 001001001 = 3)
        depth = len(cat_id) // 3

        # 부모 카테고리 ID 계산
        parent_id = cat_id[:-3] if depth > 1 else None

        categories[cat_id] = {
            "name": name,
            "depth": depth,
            "parent": parent_id,
            "children": []
        }

    # 부모-자식 관계 설정
    for cat_id, info in categories.items():
        parent_id = info.get("parent")
        # parent_id가 존재하지 않으면 첫 3자리를 parent로 시도
        if parent_id:
            if parent_id in categories:
                categories[parent_id]["children"].append(cat_id)
            else:
                # 첫 3자리를 parent로 시도 (001001001 -> 001)
                root_parent = cat_id[:3]
                if root_parent in categories:
                    categories[root_parent]["children"].append(cat_id)
                    info["parent"] = root_parent

    # 캐시 파일로 저장
    if use_cache:
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(categories, f, ensure_ascii=False, indent=2)
                print(f"✓ {len(categories)}개 카테고리를 캐시 파일로 저장: {cache_file}")
        except Exception as e:
            print(f"⚠ 캐시 파일 저장 실패: {e}")

    return categories


def get_flat_categories(category_number="001"):
    """
    단순 딕셔너리 형태로 반환 {id: name}
    """
    categories = get_categories(category_number)
    return {cat_id: info["name"] for cat_id, info in categories.items()}


def print_category_tree(categories):
    """카테고리 트리 출력 (depth 기반)"""
    # depth별로 정렬
    sorted_cats = sorted(categories.items(), key=lambda x: (x[1]["depth"], x[0]))

    for cat_id, info in sorted_cats:
        indent = info["depth"] - 1
        print(f"{'  ' * indent}{cat_id}: {info['name']}")


if __name__ == "__main__":
    import sys
    
    cat_num = sys.argv[1] if len(sys.argv) > 1 else "001" #기본 국내도서
    
    print(f"=== 예스24 신간도서 카테고리 ({cat_num}) ===\n")
    
    categories = get_categories(cat_num)
    print(f"총 {len(categories)}개 카테고리 발견\n")
    
    # 트리 형태로 출력
    print_category_tree(categories)
    
    print("\n=== 단순 딕셔너리 (샘플) ===")
    flat = get_flat_categories(cat_num)
    for i, (k, v) in enumerate(list(flat.items())[:10]):
        print(f"  '{k}': '{v}'")
    print("  ...")

