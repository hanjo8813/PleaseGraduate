# 파이썬 라이브러리
import time
import platform
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
# 모델 참조
from ..models import *

def selenium_DHC(id, pw):
    # 대양휴머니티칼리지 url
    url = 'https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=classic.sejong.ac.kr/ssoLogin.do'

    # 옵션 넣고 드라이버 생성
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])


    # 가상 디스플레이를 활용해 실행속도 단축
    display = Display(visible=0, size=(1024, 768))
    display.start()
    # 옵션 추가
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # 크롬드라이버 열기
    driver = webdriver.Chrome('/srv/chromedriver', options=options)
    driver.get(url)
    time.sleep(1)
    # 키보드 보안 해제
    driver.find_element_by_xpath('//*[@id="login_form"]/div[2]/div/div[2]/div[3]/label/span').click()
    driver.switch_to_alert().dismiss()
    # id , pw 입력할 곳 찾기
    tag_id = driver.find_element_by_id("id")  # id 입력할곳 찾기 변수는 id태그
    tag_pw = driver.find_element_by_id("password")
    # id , pw 보내기
    tag_id.send_keys(id)
    tag_pw.send_keys(pw)
    time.sleep(0.5)
    # 로그인버튼 클릭
    login_btn = driver.find_element_by_id('loginBtn')
    login_btn.click()
    # ID/PW 틀렸을 때 예외처리 ***
    try:
        driver.switch_to.frame(0)
    except:
        driver.quit()
        display.stop()
        return 'err_auth'
    # 팝업창 있을 경우 모두 닫아준다
    while 1:
        try:
            driver.find_element_by_class_name("close").click()
        except:
            break
    # 고전독서 인증현황 페이지로 감, 실패시 재외국민/편입생/계약학과임
    try:
        driver.find_element_by_class_name("box02").click()  
    except:
        driver.quit()
        display.stop()
        return 'err_enter_mybook'
    html = driver.page_source  # 페이지 소스 가져오기 , -> 고전독서 인증현황 페이지 html 가져오는것
    # 독서 권수 리스트에 저장
    soup = BeautifulSoup(html, 'html.parser')
    # 유저 학과/학부 저장
    soup_major = soup.select_one("li > dl > dd")
    major = soup_major.string
    # 유저 이름 저장
    soup_name = soup.select("li > dl > dd")
    name = soup_name[2].string
    # 인증 여부
    soup_cert = soup.select("li > dl > dd")
    cert = soup_cert[7].string.strip().replace('\n','').replace('\t','')
    # 고특으로 대체이수 하지 않았을 때
    if cert[-4:] == '대체이수':
        book = '고특통과'
    else :
        book=[]
        soup1 = soup.select_one("tbody > tr")  # tbody -> tr 태그 접근
          # 0 : 서양 , 1 : 동양 , 2: 동서양 ,3 : 과학 , 4 : 전체
        for td in soup1:
            if td.string.strip() == '' or td.string.strip()[0].isalpha():  # 공백제거 및 필요없는 문자 지우기
                continue
            book.append(td.string.strip().strip().replace('권', ''))
        book = ''.join(book[:4]).replace(' ','')
    driver.quit()
    display.stop()

    


    # # 로컬 개발용
    # if platform.system() == 'Windows':
    #     # 크롬 드라이버 실행
    #     driver = webdriver.Chrome('./dev/chromedriver.exe', options=options)
    #     driver.get(url)
    #     time.sleep(4)
    #     # 키보드 보안 해제
    #     driver.find_element_by_xpath('//*[@id="login_form"]/div[2]/div/div[2]/div[3]/label/span').click()
    #     driver.switch_to_alert().dismiss()
    #     # id , pw 입력할 곳 찾기
    #     tag_id = driver.find_element_by_id("id")  # id 입력할곳 찾기 변수는 id태그
    #     tag_pw = driver.find_element_by_id("password")
    #     # id , pw 보내기
    #     tag_id.send_keys(id)
    #     tag_pw.send_keys(pw)
    #     time.sleep(0.5)
    #     # 로그인버튼 클릭
    #     login_btn = driver.find_element_by_id('loginBtn')
    #     login_btn.click()
    #     # ID/PW 틀렸을 때 예외처리 ***
    #     try:
    #         driver.switch_to.frame(0)
    #     except:
    #         driver.quit()
    #         return 'err_auth'
    #     # 팝업창 있을 경우 모두 닫아준다
    #     while 1:
    #         try:
    #             driver.find_element_by_class_name("close").click()
    #         except:
    #             break
    #     # 고전독서 인증현황 페이지로 감, 실패시 재외국민/편입생/계약학과임
    #     try:
    #         driver.find_element_by_class_name("box02").click()  
    #     except:
    #         driver.quit()
    #         return 'err_enter_mybook'
    #     html = driver.page_source  # 페이지 소스 가져오기 , -> 고전독서 인증현황 페이지 html 가져오는것
    #     # 독서 권수 리스트에 저장
    #     soup = BeautifulSoup(html, 'html.parser')
    #     # 유저 학과/학부 저장
    #     soup_major = soup.select_one("li > dl > dd")
    #     major = soup_major.string
    #     # 유저 이름 저장
    #     soup_name = soup.select("li > dl > dd")
    #     name = soup_name[2].string
    #     # 인증 여부
    #     soup_cert = soup.select("li > dl > dd")
    #     cert = soup_cert[7].string.strip().replace('\n','').replace('\t','')
    #     # 고특으로 대체이수 하지 않았을 때
    #     if cert[-4:] == '대체이수':
    #         book = '고특통과'
    #     else :
    #         book=[]
    #         soup1 = soup.select_one("tbody > tr")  # tbody -> tr 태그 접근
    #           # 0 : 서양 , 1 : 동양 , 2: 동서양 ,3 : 과학 , 4 : 전체
    #         for td in soup1:
    #             if td.string.strip() == '' or td.string.strip()[0].isalpha():  # 공백제거 및 필요없는 문자 지우기
    #                 continue
    #             book.append(td.string.strip().strip().replace('권', ''))
    #         book = ''.join(book[:4]).replace(' ','')
    #     driver.quit()

    # else:
    #     try:
    #         options.add_argument('headless')
    #         options.add_argument('--no-sandbox')
    #         options.add_argument('--disable-dev-shm-usage')
    #         # 가상 디스플레이를 활용해 실행속도 단축
    #         display = Display(visible=0, size=(1024, 768))
    #         display.start()
    #         # 크롬드라이버 열기
    #         driver = webdriver.Chrome('/srv/chromedriver', options=options)
    #         driver.get(url)
    #         time.sleep(0.5)
    #         # 키보드 보안 해제
    #         driver.find_element_by_xpath('//*[@id="login_form"]/div[2]/div/div[2]/div[3]/label/span').click()
    #         driver.switch_to_alert().dismiss()
    #         # id , pw 입력할 곳 찾기
    #         tag_id = driver.find_element_by_id("id")  # id 입력할곳 찾기 변수는 id태그
    #         tag_pw = driver.find_element_by_id("password")
    #         # id , pw 보내기
    #         tag_id.send_keys(id)
    #         tag_pw.send_keys(pw)
    #         time.sleep(0.5)
    #         # 로그인버튼 클릭
    #         login_btn = driver.find_element_by_id('loginBtn')
    #         login_btn.click()
    #         # ID/PW 틀렸을 때 예외처리 ***
    #         try:
    #             driver.switch_to.frame(0)
    #         except:
    #             driver.quit()
    #             display.stop()
    #             return 'err_auth'
    #         # 팝업창 있을 경우 모두 닫아준다
    #         while 1:
    #             try:
    #                 driver.find_element_by_class_name("close").click()
    #             except:
    #                 break
    #         # 고전독서 인증현황 페이지로 감, 실패시 재외국민/편입생/계약학과임
    #         try:
    #             driver.find_element_by_class_name("box02").click()  
    #         except:
    #             driver.quit()
    #             display.stop()
    #             return 'err_enter_mybook'
    #         html = driver.page_source  # 페이지 소스 가져오기 , -> 고전독서 인증현황 페이지 html 가져오는것
    #         # 독서 권수 리스트에 저장
    #         soup = BeautifulSoup(html, 'html.parser')
    #         # 유저 학과/학부 저장
    #         soup_major = soup.select_one("li > dl > dd")
    #         major = soup_major.string
    #         # 유저 이름 저장
    #         soup_name = soup.select("li > dl > dd")
    #         name = soup_name[2].string
    #         # 인증 여부
    #         soup_cert = soup.select("li > dl > dd")
    #         cert = soup_cert[7].string.strip().replace('\n','').replace('\t','')
    #         # 고특으로 대체이수 하지 않았을 때
    #         if cert[-4:] == '대체이수':
    #             book = '고특통과'
    #         else :
    #             book=[]
    #             soup1 = soup.select_one("tbody > tr")  # tbody -> tr 태그 접근
    #               # 0 : 서양 , 1 : 동양 , 2: 동서양 ,3 : 과학 , 4 : 전체
    #             for td in soup1:
    #                 if td.string.strip() == '' or td.string.strip()[0].isalpha():  # 공백제거 및 필요없는 문자 지우기
    #                     continue
    #                 book.append(td.string.strip().strip().replace('권', ''))
    #             book = ''.join(book[:4]).replace(' ','')
    #         driver.quit()
    #         display.stop()
    #     except:
    #         # 드라이버 종료
    #         if 'driver' in locals():
    #             driver.quit()
    #         if 'display' in locals():
    #             display.stop()
    #         return 'err_all'

    # 크롤링으로 받아온 값 리턴
    context = {
        'name' : name,
        'major' : major,
        'book' : book,
    }
    return context