"""
CLI 관련 공통 유틸리티
"""


def select_option(options, prompt):
    """
    사용자에게 옵션 선택 받기 (CLI 인터랙티브 모드용)

    Args:
        options: {키: (값, 설명)} 형태의 딕셔너리
        prompt: 사용자에게 표시할 프롬프트 메시지

    Returns:
        선택된 옵션의 값
    """
    print(f"\n{prompt}")
    for key, (_, name) in options.items():
        print(f"  {key}. {name}")

    while True:
        choice = input("\n선택 (번호 입력): ").strip()
        if choice in options:
            return options[choice][0]
        print("잘못된 입력입니다. 다시 선택해주세요.")
