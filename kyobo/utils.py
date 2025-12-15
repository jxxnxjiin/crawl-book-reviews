"""
교보문고 크롤러 유틸리티 함수
"""

import re


def sanitize_filename(filename):
    """파일명에 사용할 수 없는 문자 제거"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename


def select_option(options, prompt):
    """사용자에게 옵션 선택 받기"""
    print(f"\n{prompt}")
    for key, (_, name) in options.items():
        print(f"  {key}. {name}")
    
    while True:
        choice = input("\n선택 (번호 입력): ").strip()
        if choice in options:
            return options[choice][0]
        print("잘못된 입력입니다. 다시 선택해주세요.")

