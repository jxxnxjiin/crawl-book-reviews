"""
Chrome 드라이버 설정 유틸리티

환경 변수로 경로 설정 가능:
- CHROME_PATH: Chrome/Chromium 바이너리 경로
- CHROMEDRIVER_PATH: chromedriver 경로

설정 안 하면 WSL/Linux 기본값 사용
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# 기본값 (WSL/Linux)
DEFAULT_CHROME_PATH = "/usr/bin/chromium-browser"
DEFAULT_CHROMEDRIVER_PATH = "/usr/bin/chromedriver"


def get_chrome_driver(headless=True):
    """
    Chrome 드라이버 생성
    
    headless: 헤드리스 모드 여부 (기본값: True)
    """
    # 환경 변수에서 경로 가져오기 (없으면 기본값)
    chrome_path = os.environ.get("CHROME_PATH", DEFAULT_CHROME_PATH)
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", DEFAULT_CHROMEDRIVER_PATH)
    
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument('--headless=new')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # 차단 방지: User-Agent 설정
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Chrome 바이너리 경로 설정
    if chrome_path and os.path.exists(chrome_path):
        options.binary_location = chrome_path
    
    # chromedriver 서비스 설정
    if chromedriver_path and os.path.exists(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service()  # 시스템 PATH에서 찾기
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver

