from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import shutil
import json
import time
URL = 'https://portal.sejong.ac.kr/jsp/login/uisloginSSL.jsp?rtUrl=uis.sejong.ac.kr/app/sys.Login.servj?strCommand=SSOLOGIN'
id = '15011187' # uis 아이디
password = 'z8813z' # uis 비밀번호 #<---- 웹에서 받아서 id pw 넣기
#세종대학교 포탈 url

def main():
    driver = get_Driver() # 크롬 드라이버 <-- 실행하는 로컬 프로젝트 내에 존재해야됨 exe 파일로 존재
    #id , pw 입력할 곳 찾기
    tag_id = driver.find_element_by_id("id") # id 입력할곳 찾기 변수는 id태그
    tag_pw = driver.find_element_by_id("password")
    tag_id.clear()
    #id , pw 보내기
    tag_id.send_keys(id)
    tag_pw.send_keys(password)  
    #로그인버튼 클릭
    login_btn = driver.find_element_by_id('logbtn')
    login_btn.click()
    
    # 프레임전환
    driver.switch_to.frame(2)
    # 수업/성적 메뉴선택
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_30');")
    # 성적 및 강의평가 선택
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_30SCH_SUG05_STUD');")
    time.sleep(1)
    # 기이수성적조회 클릭
    driver.find_element_by_xpath('''//*[@id="SELF_STUDSELF_SUB_30SCH_SUG05_STUD"]/table/tbody/tr[1]''').click()
    time.sleep(1)
    # 최상위(default) 프레임으로 이동
    driver.switch_to.default_content()
    # 프레임 경우의 수 다 찾았음
    driver.switch_to.frame(3)
    driver.switch_to.frame(0)
    # 다운로드 버튼 x_path
    x = driver.find_element_by_xpath('''//*[@id="btnDownload_btn"]''')
    x.click()
    time.sleep(1)

    file_name = time.strftime('%y-%m-%d %H_%M_%S') + '.xls'

    Initial_path = 'C:\\Users\\NB1\\Desktop\\프로그램\\GitWorkSpace\\SejongGraduateHellper\\Graduate Web\\app\\uploaded_media'
    filename = max([Initial_path + "\\" + f for f in os.listdir(Initial_path)],key=os.path.getctime)
    shutil.move(filename,os.path.join(Initial_path,file_name))
    time.sleep(1)
    
    time.sleep(100000)


def get_Driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('prefs', {'download.default_directory' : 'C:\\Users\\NB1\\Desktop\\프로그램\\GitWorkSpace\\SejongGraduateHellper\\Graduate Web\\app\\uploaded_media'})
    driver = webdriver.Chrome('C:/Users/NB1/Desktop/프로그램/GitWorkSpace/SejongGraduateHellper/Graduate Web/chromedriver.exe', options=options)
    driver.get(URL)
    return driver

if __name__ == '__main__':
    main()