import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 크롬 드라이버 로드
driver = webdriver.Chrome()

# 창 최대화
driver.maximize_window()

# 로드할 URL
url = "https://blog.naver.com/dls32208/222604964339"

# URL 로드
driver.get(url)

# 웹 페이지 로드될 때까지 기다림
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

# 스크린샷 파일명
filename = "screenshot.png"

# 스크린샷 찍기
pyautogui.screenshot(filename)

# "댓글작성" 버튼 좌표 찾기
button_location = pyautogui.locateOnScreen("comment_button.png")

# 드라이버 종료
driver.quit()
