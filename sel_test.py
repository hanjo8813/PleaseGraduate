from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_Driver(url):
    options = webdriver.ChromeOptions()
    # 크롬창을 열지않고 백그라운드로 실행
    # options.add_argument("headless")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    '''
    # 다운로드될 경로 지정
    root = os.getcwd() + '\\app\\uploaded_media'
    options.add_experimental_option('prefs', {'download.default_directory' : root} )
    '''
    driver = webdriver.Chrome('C:/Users/NB1/Desktop/프로그램/GitWorkSpace/SejongGraduateHellper/Graduate Web/chromedriver.exe', options=options)
    driver.get(url)
    return driver

def selenium_uis(id, pw):
    url = 'https://portal.sejong.ac.kr/jsp/login/uisloginSSL.jsp?rtUrl=uis.sejong.ac.kr/app/sys.Login.servj?strCommand=SSOLOGIN'
    driver = get_Driver(url) # 크롬 드라이버 <-- 실행하는 로컬 프로젝트 내에 존재해야됨 exe 파일로 존재
    #id , pw 입력할 곳 찾기
    tag_id = driver.find_element_by_id("id") # id 입력할곳 찾기 변수는 id태그
    tag_pw = driver.find_element_by_id("password")
    tag_id.clear()
    #id , pw 보내기
    tag_id.send_keys(id)
    tag_pw.send_keys(pw)  
    #로그인버튼 클릭
    login_btn = driver.find_element_by_id('logbtn')
    login_btn.click()
    # 프레임전환
    driver.switch_to.frame(2)
    print("버튼은 찾음")
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_20SCH_SUH_STUD');")
    time.sleep(1)
    driver.find_element_by_xpath('''//*[@id="SELF_STUDSELF_SUB_20SCH_SUH_STUDSuhJudgeSelfQ"]''').click()
    
    time.sleep(10)


    '''
    # 수업/성적 메뉴선택
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_30');")
    # 성적 및 강의평가 선택
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_30SCH_SUG05_STUD');")
    time.sleep(100)

    # 기이수성적조회로 클릭 이동
    driver.find_element_by_xpath('//*[@id="SELF_STUDSELF_SUB_30SCH_SUG05_STUD"]/table/tbody/tr[1]').click()
    time.sleep(10)

    # 최상위(default) 프레임으로 이동
    driver.switch_to.default_content()
    # 프레임 경우의 수 다 찾고 이동
    driver.switch_to.frame(3)
    driver.switch_to.frame(0)
    # 다운로드 버튼 x_path 클릭
    x = driver.find_element_by_xpath('//*[@id="btnDownload_btn"])
    x.click()
    time.sleep(5)
    ''' 

    driver.quit()
    return

selenium_uis('15011187', 'z8813z')