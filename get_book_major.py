from selenium import webdriver
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import shutil
import json
import time
# 세종대학교 포탈 url


def main():
    mybooks = crawling_book("16011140" , "960923")
    print(mybooks.get_book())
    print(mybooks.get_major())
    
class crawling_book:
    id =""
    password = ""
    URL = 'https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=classic.sejong.ac.kr/ssoLogin.do'
    mybooks = []
    major = ""
    driver = ""
    html = ""

    def __init__(self , id , password): # 아이디 패스워드 받아서 진행시키기
        self.id = id
        self.password = password
        self.set_book()
        self.set_major()

    def get_book(self):
        return self.mybooks


    def get_major(self):
        return self.major

    def set_major(self):
        soup = BeautifulSoup(self.html , 'html.parser')
        soup_major = soup.select_one("li > dl > dd")
        self.major = soup_major.string.strip().strip()
        for dd in soup_major:
            if dd.string.strip() == '' :  # 공백제거 및 필요없는 문자 지우기
                continue
            self.major = dd.string.strip()

    def set_book(self):
        self.driver = self.get_Driver()  # 크롬 드라이버 <-- 실행하는 로컬 프로젝트 내에 존재해야됨 exe 파일로 존재
        # id , pw 입력할 곳 찾기
        time.sleep(5)
        tag_id = self.driver.find_element_by_id("id")  # id 입력할곳 찾기 변수는 id태그
        time.sleep(3)
        tag_pw = self.driver.find_element_by_id("password")
        tag_id.clear()
        tag_pw.clear()
        
        # id , pw 보내기
        tag_id.send_keys(self.id)
        time.sleep(5)
        tag_pw.send_keys(self.password)
        time.sleep(5)
        time.sleep(1)
        # 로그인버튼 클릭
        login_btn = self.driver.find_element_by_id('loginBtn')
        login_btn.click()
        self.driver.switch_to.frame(0)
        self.driver.find_element_by_class_name("box02").click()  # 고전독서 인증현황 페이지로 감

        self.html = self.driver.page_source  # 페이지 소스 가져오기 , -> 고전독서 인증현황 페이지 html 가져오는것
        soup = BeautifulSoup(self.html, 'html.parser')
        # ----------------------------------------------------------------------------------------- 학번 ,학과 가져오는부분

        # ----------------------------------------------------------------------------------------- 고전독서 가져오는 부분
        soup1 = soup.select_one("tbody > tr")  # tbody -> tr 태그 접근
        i = 0
        book = []  # 0 : 서양 , 1 : 동양 , 2: 동서양 ,3 : 과학 , 4 : 전체
        for td in soup1:
            if td.string.strip() == '' or td.string.strip()[0].isalpha():  # 공백제거 및 필요없는 문자 지우기
                continue
            book.append((int)(td.string.strip().strip().replace('권', '')))
        self.driver.quit()
        self.mybooks = book
    def get_Driver(self):
        #options = webdriver.ChromeOptions()
        #options.add_experimental_option('excludeSwitches', ['enable-logging'])
        #options.add_experimental_option('prefs', {
        #    'download.default_directory': 'C:\\Users\\NB1\\Desktop\\프로그램\\GitWorkSpace\\SejongGraduateHellper\\Graduate Web\\app\\uploaded_media'})
        # driver = webdriver.Chrome(
        #     'C:/Users/NB1/Desktop/프로그램/GitWorkSpace/SejongGraduateHellper/Graduate Web/chromedriver.exe', options=options)
        driver = webdriver.Chrome(
            'C:/Users/NB1/Desktop/프로그램/GitWorkSpace/SejongGraduateHellper/Graduate Web/chromedriver.exe') # 크롬드라이버의 절대경로
        driver.get(self.URL)
        return driver


if __name__ == '__main__':
    main()