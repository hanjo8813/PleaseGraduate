# 파이썬 라이브러리
import os
import json
import time
import shutil
import pandas as pd
import numpy as np
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 장고 관련 참조
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
# 모델 참조
from .models import *


# DB 감지 테스트
def r_dbcheck(request):
    # model의 test_table 테이블을 변수에 저장
    tt = TestTable.objects.all()
    # 그리고 함수가 불려서 페이지를 렌더링할때 그 변수를 해당 페이지에 넘김
    return render(request, "dbcheck.html", {"t_h":tt})


# 이 함수가 호출되면 -> index.html을 렌더링한다.
def r_index(request):
    return render(request, "index.html")

def r_head(request):
    return render(request, "head.html")

def r_login(request):
    return render(request, "login.html")

def r_result(request, file_name, info):

    # 셀레니움으로 넘어온 변수들
    p_year = info["year"]
    p_major = info["major"]

    user_info = {
        'id' : info["id"],
        'name' : info["name"],
        'major' : info["major"],
        'W' : info["book"][0],
        'E' : info["book"][1],
        'EW' : info["book"][2],
        'S' : info["book"][3],
    }

    # 파이썬 변수를 가지고 ind로 매핑
    s_row = Standard.objects.get(user_dep = p_major, user_year=p_year)

    #---------------------------------------------------------
    # db에서 ind 를 가지고 모든 비교 기준 뽑아내기
    # 1. 이수학점 수치 기준
    standard_num ={
        'ss' : s_row.sum_score,          # sum_score
        'me' : s_row.major_essential,    # major_essential
        'ms' : s_row.major_selection,    # major_selection
        'ce' : s_row.core_essential,     # core_essential   
        'cs' : s_row.core_selection,     # core_selection
        'b' : s_row.basic,               # basic
    }
    
    # 2. 중필(교필) 필수과목. { 학수번호 : 그룹번호 } 딕셔너리로 매핑
    # ind로 필수과목 추출후 딕셔너리 만들기
    dic_ce = make_dic([int(s_num) for s_num in s_row.ce_list.split(',')])
    # 3. 중선(교선1) 필수과목
    dic_cs = make_dic([int(s_num) for s_num in s_row.cs_list.split(',')])
    # 4. 기교 필수과목 
    dic_b = make_dic([int(s_num) for s_num in s_row.b_list.split(',')])

    standard_list = {
        'ce' : list_to_query(dic_ce.keys()),
        'cs' : list_to_query(dic_cs.keys()),
        'b' : list_to_query(dic_b.keys()),
    }

    #------------------------------------------------------------------------------
    # 입력받은 엑셀 파일 dataframe으로 변환
    data = pd.read_excel('./app/uploaded_media/기이수성적_재현.xls', index_col=None)

    # 논패, F과목 삭제
    n = data.shape[0]
    flag = 0
    while(True):
        for i in range(n):
            if i == n-1 :
                flag = 1
            if data['등급'][i]=='NP':
                data = data.drop(data.index[i])
                n -= 1
                data.reset_index(inplace=True, drop=True)
                break
            elif data['등급'][i]=='F':
                data = data.drop(data.index[i])
                n -= 1
                data.reset_index(inplace=True, drop=True)
                break
        if flag == 1:
            break

    # 이수 구분마다 df 생성
    # 전필
    df_me = data[data['이수구분'].isin(['전필'])]
    df_me.reset_index(inplace=True,drop=True)
    # 전선
    df_ms = data[data['이수구분'].isin(['전선'])]
    df_ms.reset_index(inplace=True,drop=True)
    # 중필(교필)
    df_ce = data[data['이수구분'].isin(['교필'])]
    df_ce.reset_index(inplace=True,drop=True)
    # 중선(교선)
    df_cs = data[data['이수구분'].isin(['교선1'])]
    df_cs.reset_index(inplace=True,drop=True)
    # 기교
    df_b = data[data['이수구분'].isin(['기교'])]
    df_b.reset_index(inplace=True,drop=True)

    # 내 이수학점 수치
    my_num ={
        'ss' : data['학점'].sum(),          # sum_score
        'me' : df_me['학점'].sum(),         # major_essential
        'ms' : df_ms['학점'].sum(),         # major_selection
        'ce' : df_ce['학점'].sum() ,        # core_essential   
        'cs' : df_cs['학점'].sum(),         # core_selection
        'b' : df_b['학점'].sum(),           # basic
    }

    # 사용자가 들은 dic 추출
    my_dic_ce = make_dic(df_ce['학수번호'].tolist())
    my_dic_cs = make_dic(df_cs['학수번호'].tolist())
    my_dic_b = make_dic(df_b['학수번호'].tolist())

    #-------------------------------------------------------------------------------------
    # 추천과목 리스트 생성 (최신과목으로)
    recom_ce = make_recommend_list(my_dic_ce, dic_ce)   # 중필
    recom_cs = make_recommend_list(my_dic_cs, dic_cs)   # 중선
    recom_b = make_recommend_list(my_dic_b, dic_b)      # 기교

    recommend_ess = {
        'ce' : list_to_query(recom_ce),
        'cs' : list_to_query(recom_cs),
        'b' : list_to_query(recom_b),
    }

    # 영역 추출
    cs_part =["사상과역사","사회와문화","융합과창업","자연과과학기술","세계와지구촌"]   # 기준 영역 5개
    my_cs_part =[]
    for s_num in my_dic_cs.keys():
        al = AllLecture.objects.get(subject_num=s_num)
        my_cs_part.append(al.selection)
    # 사용자가 들은 영역
    my_cs_part = list(set(my_cs_part))
    # 사용자의 부족 영역
    recom_cs_part = list(set(cs_part) - set(my_cs_part))
    

    context = {
        'my_num' : my_num,
        'user_info' : user_info,
        'standard_num' : standard_num,
        'standard_list' : standard_list,
        'recommend_ess' : recommend_ess,
    }

    return render(request, "result.html", context)


def r_en_result(request):
    return render(request, "en_result.html")


# --------------------------------------------- (셀레니움 파트) ----------------------------------------------------------------

def get_Driver(url):
    options = webdriver.ChromeOptions()
    # 크롬창을 열지않고 백그라운드로 실행
    # options.add_argument("headless")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # 다운로드될 경로 지정
    root = os.getcwd() + '\\app\\uploaded_media'
    options.add_experimental_option('prefs', {'download.default_directory' : root} )
    driver = webdriver.Chrome('./chromedriver.exe', options=options)
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
    # 수업/성적 메뉴선택
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_30');")
    # 성적 및 강의평가 선택
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_30SCH_SUG05_STUD');")
    time.sleep(1)
    # 기이수성적조회로 클릭 이동
    driver.find_element_by_xpath('''//*[@id="SELF_STUDSELF_SUB_30SCH_SUG05_STUD"]/table/tbody/tr[1]''').click()
    time.sleep(1)
    # 최상위(default) 프레임으로 이동
    driver.switch_to.default_content()
    # 프레임 경우의 수 다 찾고 이동
    driver.switch_to.frame(3)
    driver.switch_to.frame(0)
    # 다운로드 버튼 x_path 클릭
    x = driver.find_element_by_xpath('''//*[@id="btnDownload_btn"]''')
    x.click()
    time.sleep(5)
    driver.quit()
    return

def selenium_book(id, pw):
    url = 'https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=classic.sejong.ac.kr/ssoLogin.do'
    driver = get_Driver(url)  # 크롬 드라이버 <-- 실행하는 로컬 프로젝트 내에 존재해야됨 exe 파일로 존재
    checked = driver.find_element_by_xpath('//*[@id="chkNos"]').get_attribute('checked')
    if checked:
        driver.find_element_by_xpath('//*[@id="chkNos"]').click() # 체크창 클릭
        alert = driver.switch_to_alert()
        print(alert.text)
        alert.dismiss()
    time.sleep(1)
    # id , pw 입력할 곳 찾기
    tag_id = driver.find_element_by_id("id")  # id 입력할곳 찾기 변수는 id태그
    tag_pw = driver.find_element_by_id("password")
    tag_id.clear()
    time.sleep(1)
    # id , pw 보내기
    tag_id.send_keys(id)
    tag_pw.send_keys(pw)
    time.sleep(1)
    # 로그인버튼 클릭
    login_btn = driver.find_element_by_id('loginBtn')
    login_btn.click()
    driver.switch_to.frame(0)
    driver.find_element_by_class_name("box02").click()  # 고전독서 인증현황 페이지로 감
    #------------------------------------------------------------------------------------------------- selenium part
    html = driver.page_source  # 페이지 소스 가져오기 , -> 고전독서 인증현황 페이지 html 가져오는것
    # 독서 권수 리스트에 저장
    soup = BeautifulSoup(html, 'html.parser')
    soup1 = soup.select_one("tbody > tr")  # tbody -> tr 태그 접근
    i = 0
    book = []  # 0 : 서양 , 1 : 동양 , 2: 동서양 ,3 : 과학 , 4 : 전체
    for td in soup1:
        if td.string.strip() == '' or td.string.strip()[0].isalpha():  # 공백제거 및 필요없는 문자 지우기
            continue
        book.append((int)(td.string.strip().strip().replace('권', '')))
    
    # 유저 학과 저장
    soup_major = soup.select_one("li > dl > dd")
    major = soup_major.string.strip().strip()
    for dd in soup_major:
        if dd.string.strip() == '' :  # 공백제거 및 필요없는 문자 지우기
            continue
        major = dd.string.strip().replace('학과', '')
    # 유저 이름 저장
    soup_name = soup.select("li > dl > dd")
    name = soup_name[2].string
    driver.quit()

    # 넘겨줄 변수
    info = {
        'book' : book,
        'major' : major,
        'id' : id,
        'year' : id[:2],
        'name' : name,
    }
    return info 

def f_login(request):
    # 셀레니움으로 서버(uploaded_media)에 엑셀 다운
    selenium_uis(request.POST.get('id'), request.POST.get('pw'))
    # 다운로드 후 이름 변경
    file_name = time.strftime('%y-%m-%d %H_%M_%S') + '.xls'
    Initial_path = './app/uploaded_media'
    filename = max([Initial_path + "/" + f for f in os.listdir(Initial_path)],key=os.path.getctime)
    shutil.move(filename,os.path.join(Initial_path,file_name))
    # 대양휴머니티 크롤링 후 학과/학번/인증권수 넘기기
    context = selenium_book(request.POST.get('id'), request.POST.get('pw'))
    return r_result(request, file_name, context)

#---------------------------------------------------------------------------------------------------------------












# ----------------------------------------------- (웹 연동 테스트) --------------------------------------------------------------------

def list_to_query(list_):
    al = AllLecture.objects.none()
    for s_num in list_:
        temp = AllLecture.objects.filter(subject_num = s_num)
        al = temp | al
    return al

def make_dic(my_list):
    dic = defaultdict(lambda:-1)
    for s_num in my_list:
        dic[s_num]
        sg = SubjectGroup.objects.filter(subject_num = s_num)
        if sg.exists():
            dic[s_num] = sg[0].group_num
    return dic

def make_recommend_list(my_dic_, dic_):
    # 만족한 학수번호는 딕셔너리에서 pop
    for s_num in my_dic_.keys():
        # 1차로 학수번호 검사
        # 있다면? -> 기준 딕셔너리에서 팝.
        if s_num in dic_.keys():
            dic_.pop(s_num)
        # 없다면? 2차 검사
        else :
            g_num = my_dic_[s_num]
            if g_num != -1 and (g_num in dic_.values()):
                dic_.pop(s_num)
        
    # 추천 리스트 알고리즘
    recommend = []
    for s_num in dic_.keys():
        nl = NewLecture.objects.filter(subject_num = s_num)
        # 부족 과목이 열리고 있다면
        if nl.exists():
            recommend.append(nl[0].subject_num.subject_num)
        # 더이상 열리지 않는다면 -> 그룹번호로 동일과목 찾은 후 열리는 것만 저장
        else:
            g_num = dic_[s_num]
            # 동일과목도 없고 과목이 없어졌다?
            if g_num == -1:
                recommend.append(s_num)
            # 아니면 동일과목중 열리고 있는 강의를 찾자
            else:
                sg = SubjectGroup.objects.filter(group_num = g_num)
                for s in sg:
                    nl2 = NewLecture.objects.filter(subject_num = s.subject_num)
                    if nl2.exists():
                        recommend.append(nl2[0].subject_num.subject_num)
    return recommend

# result 페이지 테스트용.
def result_test(request):
   # 셀레니움으로 넘어올 변수들
    p_name = '안재현'
    p_major = '디지털콘텐츠'
    p_id = '16011140'
    p_year = p_id[:2]

    user_info = {
        'id' : p_id,
        'name' : p_name,
        'major' : p_major,
    }

    # 파이썬 변수를 가지고 ind로 매핑
    s_row = Standard.objects.get(user_dep = p_major, user_year=p_year)

    #---------------------------------------------------------
    # db에서 ind 를 가지고 모든 비교 기준 뽑아내기
    # 1. 이수학점 수치 기준
    standard_num ={
        'ss' : s_row.sum_score,          # sum_score
        'me' : s_row.major_essential,    # major_essential
        'ms' : s_row.major_selection,    # major_selection
        'ce' : s_row.core_essential,     # core_essential   
        'cs' : s_row.core_selection,     # core_selection
        'b' : s_row.basic,               # basic
    }
    
    # 2. 중필(교필) 필수과목. { 학수번호 : 그룹번호 } 딕셔너리로 매핑
    # ind로 필수과목 추출후 딕셔너리 만들기
    dic_ce = make_dic([int(s_num) for s_num in s_row.ce_list.split(',')])
    # 3. 중선(교선1) 필수과목
    dic_cs = make_dic([int(s_num) for s_num in s_row.cs_list.split(',')])
    # 4. 기교 필수과목 
    dic_b = make_dic([int(s_num) for s_num in s_row.b_list.split(',')])

    standard_list = {
        'ce' : list_to_query(dic_ce.keys()),
        'cs' : list_to_query(dic_cs.keys()),
        'b' : list_to_query(dic_b.keys()),
    }

    #------------------------------------------------------------------------------
    # 입력받은 엑셀 파일 dataframe으로 변환
    data = pd.read_excel('./app/uploaded_media/기이수성적_재현.xls', index_col=None)

    # 논패, F과목 삭제
    n = data.shape[0]
    flag = 0
    while(True):
        for i in range(n):
            if i == n-1 :
                flag = 1
            if data['등급'][i]=='NP':
                data = data.drop(data.index[i])
                n -= 1
                data.reset_index(inplace=True, drop=True)
                break
            elif data['등급'][i]=='F':
                data = data.drop(data.index[i])
                n -= 1
                data.reset_index(inplace=True, drop=True)
                break
        if flag == 1:
            break

    # 이수 구분마다 df 생성
    # 전필
    df_me = data[data['이수구분'].isin(['전필'])]
    df_me.reset_index(inplace=True,drop=True)
    # 전선
    df_ms = data[data['이수구분'].isin(['전선'])]
    df_ms.reset_index(inplace=True,drop=True)
    # 중필(교필)
    df_ce = data[data['이수구분'].isin(['교필'])]
    df_ce.reset_index(inplace=True,drop=True)
    # 중선(교선)
    df_cs = data[data['이수구분'].isin(['교선1'])]
    df_cs.reset_index(inplace=True,drop=True)
    # 기교
    df_b = data[data['이수구분'].isin(['기교'])]
    df_b.reset_index(inplace=True,drop=True)

    # 내 이수학점 수치
    my_num ={
        'ss' : data['학점'].sum(),          # sum_score
        'me' : df_me['학점'].sum(),         # major_essential
        'ms' : df_ms['학점'].sum(),         # major_selection
        'ce' : df_ce['학점'].sum() ,        # core_essential   
        'cs' : df_cs['학점'].sum(),         # core_selection
        'b' : df_b['학점'].sum(),           # basic
    }

    # 필수과목 dic 추출
    my_dic_ce = make_dic(df_ce['학수번호'].tolist())
    my_dic_cs = make_dic(df_cs['학수번호'].tolist())
    my_dic_b = make_dic(df_b['학수번호'].tolist())

    #-------------------------------------------------------------------------------------
    # 필수과목 중 부족과목의 최신과목 학수번호 추출하기

    
    # 추천과목 리스트 생성 (최신과목으로)
    recom_ce = make_recommend_list(my_dic_ce, dic_ce)   # 중필
    recom_cs = make_recommend_list(my_dic_cs, dic_cs)   # 중선
    recom_b = make_recommend_list(my_dic_b, dic_b)      # 기교

    recommend_ess = {
        'ce' : list_to_query(recom_ce),
        'cs' : list_to_query(recom_cs),
        'b' : list_to_query(recom_b),
    }

    # 영역 추출
    cs_part =["사상과역사","사회와문화","융합과창업","자연과과학기술","세계와지구촌"]   # 기준 영역 5개
    my_cs_part =[]
    for s_num in my_dic_cs.keys():
        al = AllLecture.objects.get(subject_num=s_num)
        my_cs_part.append(al.selection)
    # 사용자가 들은 영역
    my_cs_part = list(set(my_cs_part))
    # 사용자의 부족 영역
    recom_cs_part = list(set(cs_part) - set(my_cs_part))
    


    context = {
        'my_num' : my_num,
        'user_info' : user_info,
        'standard_num' : standard_num,
        'standard_list' : standard_list,
        'recommend_ess' : recommend_ess,
    }

    return render(request, "result.html", context)






#  -------------------------------------------- (터미널 테스트) ---------------------------------------------------------


def f_test(request):
    # 셀레니움으로 넘어올 변수들
    p_major = '디지털콘텐츠'
    p_year = 16
    
    # 파이썬 변수를 가지고 ind로 매핑
    s_row = Standard.objects.get(user_dep = p_major, user_year=p_year)

    #---------------------------------------------------------
    # db에서 ind 를 가지고 모든 비교 기준 뽑아내기
    # 1. 이수학점 수치 기준
    num_ss = s_row.sum_score           # sum_score
    num_me = s_row.major_essential     # major_essential
    num_ms = s_row.major_selection     # major_selection
    num_ce = s_row.core_essential      # core_essential   
    num_cs = s_row.core_selection      # core_selection
    num_b = s_row.basic                # basic
    print(num_ss, num_me, num_ms, num_ce, num_cs, num_b)
    
    # 2. 중필(교필) 필수과목. { 학수번호 : 그룹번호 } 딕셔너리로 매핑
    # ind로 필수과목 추출후 딕셔너리 만들기
    dic_ce = make_dic([int(s_num) for s_num in s_row.ce_list.split(',')])
    print("중필")
    print(dic_ce)

    # 3. 중선(교선1) 필수과목
    dic_cs = make_dic([int(s_num) for s_num in s_row.cs_list.split(',')])
    print("중선")
    print(dic_cs)
    
    # 4. 기교 필수과목 
    dic_b = make_dic([int(s_num) for s_num in s_row.b_list.split(',')])
    print("기교")
    print(dic_b)

    list_to_query(dic_ce.keys())

    #------------------------------------------------------------------------------
    # 입력받은 엑셀 파일 dataframe으로 변환
    data = pd.read_excel('./app/uploaded_media/기이수성적_재현.xls', index_col=None)

    # 논패, F과목 삭제
    n = data.shape[0]
    flag = 0
    while(True):
        for i in range(n):
            if i == n-1 :
                flag = 1
            if data['등급'][i]=='NP':
                data = data.drop(data.index[i])
                n -= 1
                data.reset_index(inplace=True, drop=True)
                break
            elif data['등급'][i]=='F':
                data = data.drop(data.index[i])
                n -= 1
                data.reset_index(inplace=True, drop=True)
                break
        if flag == 1:
            break

    # 이수 구분마다 df 생성
    # 전필
    df_me = data[data['이수구분'].isin(['전필'])]
    df_me.reset_index(inplace=True,drop=True)
    my_num_me = df_me['학점'].sum()
    # 전선
    df_ms = data[data['이수구분'].isin(['전선'])]
    df_ms.reset_index(inplace=True,drop=True)
    my_num_ms = df_ms['학점'].sum()
    # 중필(교필)
    df_ce = data[data['이수구분'].isin(['교필'])]
    df_ce.reset_index(inplace=True,drop=True)
    my_num_ce = df_ce['학점'].sum()                         # 사용자의 중필학점 총합
    my_dic_ce = make_dic(df_ce['학수번호'].tolist())     # 사용자 학수-그룹번호 딕셔너리
    # 중선(교선)
    df_cs = data[data['이수구분'].isin(['교선1'])]
    df_cs.reset_index(inplace=True,drop=True)
    my_num_cs = df_cs['학점'].sum()
    my_dic_cs = make_dic(df_cs['학수번호'].tolist())
    # 기교
    df_b = data[data['이수구분'].isin(['기교'])]
    df_b.reset_index(inplace=True,drop=True)
    my_num_b = df_b['학점'].sum()
    my_dic_b = make_dic(df_b['학수번호'].tolist())

    # 사용자의 총 학점
    my_num_ss = data['학점'].sum()

    #-------------------------------------------------------------------------------------
    # 검사 단계
    # 1. 총 학점 비교
    print('<총 학점>')
    if num_ss <= my_num_ss :
        print('총 학점 기준을 만족했습니다.')
    else:
        print(num_ss-my_num_ss,'학점이 부족합니다.')
    print("")

    # 2. 전필 검사
    print('<전필>')
    remain = 0
    if num_me <= my_num_me :
        print('전필 학점 기준을 만족했습니다.')
        if num_me < my_num_me:
            remain = my_num_me - num_me
    else:
        print(num_me-my_num_me, '학점이 부족합니다.')
    print("")

    # 3. 전선 검사
    print('<전선>')
    if num_ms <= my_num_ms :
        print('전선 학점 기준을 만족했습니다.')
    else:
        if num_ms <= my_num_ms + remain:
            print('전선 학점이 부족했지만 전필에서 ', remain, '학점이 남아 기준을 만족했습니다.')
        else:
            print(num_ms-my_num_ms,'학점이 부족합니다.')
    print("")

    # 4. 중필 검사
    # 학점 검사는 필요없지만 일단 넣음
    print('<중필>')
    if num_ce <= my_num_ce :
        print('총 학점 기준을 만족했습니다.')
    else:
        print(num_ce-my_num_ce,'학점이 부족합니다.')

    # 추천과목 매핑 후 추출
    recom_ce = make_recommend_list(my_dic_ce, dic_ce)
    if not recom_ce:
        print('모든 필수과목을 들었습니다!')
    else:
        print('들어야하는 과목입니다.')
        for s_num in recom_ce:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)
    print("")


    # 5. 기교 검사
    print('<기교>')
    if num_b <= my_num_b :
        print('총 학점 기준을 만족했습니다.')
    else:
        print(num_b-my_num_b,'학점이 부족합니다.')
    # 추천과목 매핑 후 추출
    recom_b = make_recommend_list(my_dic_b, dic_b)
    if not recom_b:
        print('모든 필수과목을 들었습니다!')
    else:
        print('들어야하는 과목입니다.')
        for s_num in recom_b:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)
    print("")

    #-------------------------------------------------------------------------------------------
    #6. 중선
    print("<중선>")
    cs_part =["사상과역사","사회와문화","융합과창업","자연과과학기술","세계와지구촌"]

    my_cs_part =[]
    for s_num in my_dic_cs.keys():
        al = AllLecture.objects.get(subject_num=s_num)
        my_cs_part.append(al.selection)

    recom_cs_part = list(set(cs_part) - set(my_cs_part))
    my_cs_part = list(set(my_cs_part))

    if(len(my_cs_part)>=3):
        print("영역 3가지를 만족하였습니다")
        print("만족한 영역은:")
        print(my_cs_part)
    else:
        print("영역 3가지를 만족하지못했습니다")
        print("만족하지 못한 영역은:")
        print(recom_cs_part)


    # 추천과목 매핑 후 추출
    recom_cs = make_recommend_list(my_dic_cs, dic_cs)
    if not recom_cs:
        print('모든 필수과목을 들었습니다!')
    else:
        print('들어야하는 과목입니다.')
        for s_num in recom_cs:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)


    return HttpResponse('테스트 완료, 터미널 확인')







# 쓰레기통 -------------------------------------------------------------------------------------------
