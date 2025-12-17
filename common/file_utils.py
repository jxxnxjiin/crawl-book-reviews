"""
파일 처리 관련 공통 유틸리티
"""

import csv
import re
from pathlib import Path


def save_to_csv(data, filename, output_dir="./results"):
    """
    데이터를 CSV 파일로 저장

    Args:
        data: 저장할 데이터 (리스트 또는 딕셔너리 리스트)
        filename: 파일명
        output_dir: 저장 디렉토리 (기본: ./results)

    Returns:
        dict: {'status': 'success' | 'error', 'message': str, 'filepath': str}
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return {'status': 'error', 'message': 'No data to save'}

    # 출력 디렉토리 생성
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / filename

    # 딕셔너리 리스트인 경우
    if isinstance(data, list) and data and isinstance(data[0], dict):
        keys = data[0].keys()
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
    else:
        return {'status': 'error', 'message': 'Invalid data format'}

    print(f"✓ 저장 완료: {filepath}")
    return {'status': 'success', 'filepath': str(filepath), 'message': 'File saved successfully'}


def sanitize_filename(filename):
    """
    파일명에 사용할 수 없는 문자 제거

    Args:
        filename: 원본 파일명

    Returns:
        str: 정제된 파일명
    """
    # Windows/Linux에서 사용 불가능한 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 공백을 언더스코어로 변경
    filename = filename.replace(' ', '_')
    return filename
