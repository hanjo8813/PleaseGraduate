# 파이썬 라이브러리
import os
import json
import time
import shutil
import pandas as pd
import numpy as np
from collections import defaultdict
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

# 이 함수가 호출되면 -> index.html을 렌더링한다.
def r_index(request):
    return render(request, "index.html")

def r_dbcheck(request):
    # model의 test_table 테이블을 변수에 저장
    tt = TestTable.objects.all()
    # 그리고 함수가 불려서 페이지를 렌더링할때 그 변수를 해당 페이지에 넘김
    return render(request, "dbcheck.html", {"t_h":tt})

def r_upload(request):
    return render(request, "upload.html")

def f_upload(request):
    # 만약 post 형식으로 제출됐는데 file이 있다면.
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        # 일단 미디어 폴더에 저장.
        fs = FileSystemStorage()
        fs.save(uploaded_file.name , uploaded_file)
        # 그 파일을 compare 렌더링하는 함수로 넘긴다.
        return r_compare(request, uploaded_file.name)
    # file이 없다면.
    else:
        return HttpResponse('업로드 실패')

def r_compare(request, file_name):
    # 메시지를 html로 넘긴다.
    messages.info(request, '업로드 성공. app/uploaded_media 폴더 확인!!')


#-------------------------------------------------------------------
    p_major = '디지털콘텐츠'
    p_year = 16

    # 파이썬 변수를 가지고 ind로 매핑
    ic_row = IndCombi.objects.get(major=p_major, year=p_year)
    p_ind = ic_row.ind  # 매핑된 ind
    print(p_ind)

    # ---------------------------------------------------------

    # 이수학점 기준 모델 불러오기
    gs = GraduateScore.objects.all()
    gs_sum = gs[p_ind-1].sum_score

    #-----------------------------------------------
    # db에서 ind 를 가지고 모든 비교 기준 뽑아내기
    # 1. 이수학점 수치 기준
    gs_row = GraduateScore.objects.get(ind=p_ind)
    num_ss = gs_row.sum_score  # sum_score
    num_me = gs_row.major_essential  # major_essential
    num_ms = gs_row.major_selection  # major_selection
    num_ce = gs_row.core_essential  # core_essential
    num_cs = gs_row.core_selection  # core_selection
    num_b = gs_row.basic  # basic




#-----------------------------------------------------------------------
    # dataframe 작업
    root = './app/uploaded_media/' + file_name
    data = pd.read_excel(root, index_col=None)
    data.to_csv('csvfile.csv', encoding='utf-8')
    data_sum = data['학점'].sum()
    # ---------------------------------------------------------------
    df_me = data[data['이수구분'].isin(['전필'])]
    df_me.reset_index(inplace=True, drop=True)
    my_num_me = df_me['학점'].sum()
    # 전선
    df_ms = data[data['이수구분'].isin(['전선'])]
    df_ms.reset_index(inplace=True, drop=True)
    my_num_ms = df_ms['학점'].sum()
    # 중필(교필)
    df_ce = data[data['이수구분'].isin(['교필'])]
    df_ce.reset_index(inplace=True, drop=True)
    my_num_ce = df_ce['학점'].sum()  # 사용자의 중필학점 총합
    my_dic_ce = df_make_dic(df_ce['학수번호'].tolist())  # 사용자 학수-그룹번호 딕셔너리
    # 중선(교선)
    df_cs = data[data['이수구분'].isin(['교선1'])]
    df_cs.reset_index(inplace=True, drop=True)
    my_num_cs = df_cs['학점'].sum()
    my_dic_cs = df_make_dic(df_cs['학수번호'].tolist())
    # 기교
    df_b = data[data['이수구분'].isin(['기교'])]
    df_b.reset_index(inplace=True, drop=True)
    my_num_b = df_b['학점'].sum()
    my_dic_b = df_make_dic(df_b['학수번호'].tolist())

    # 2. 중필(교필) 필수과목. { 학수번호 : 그룹번호 } 딕셔너리로 매핑
    # ind로 필수과목 추출후 딕셔너리 만들기
    ce_row = CoreEssential.objects.get(ind=p_ind)
    dic_ce = db_make_dic(ce_row)
    print("중필")
    print(dic_ce)

    # 3. 중선(교선1) 필수과목
    cs_row = CoreSelection.objects.get(ind=p_ind)
    dic_cs = db_make_dic(cs_row)
    print("중선")
    print(dic_cs)

    # 4. 기교 필수과목
    b_row = Basic.objects.get(ind=p_ind)
    dic_b = db_make_dic(b_row)
    print("기교")
    print(dic_b)

    #2. 전필검사
    print('<전필>')
    remain = 0
    need_me_score=0
    if num_me <= my_num_me:
        print('전필 학점 기준을 만족했습니다.')
        if num_me < my_num_me:
            remain = my_num_me - num_me
    else:
        need_me_score=num_me-my_num_me
        print(need_me_score, '학점이 부족합니다.')
    print("")

    # 3. 전선 검사
    need_ms_score=0
    final_num_my_ms=my_num_ms+remain
    print('<전선>')
    if num_ms <= my_num_ms :
        print('전선 학점 기준을 만족했습니다.')
    else:
        if num_ms <= final_num_my_ms:
            print('전선 학점이 부족했지만 전필에서 ', remain, '학점이 남아 기준을 만족했습니다.')
        else:
            need_ms_score=num_ms-my_num_ms
            print(need_ms_score,'학점이 부족합니다.')
    print("")

    # 4. 중필 검사
    # 학점 검사는 필요없지만 일단 넣음
    print('<중필>')
    recom_ce_list=[]
    if num_ce <= my_num_ce:
        print('총 학점 기준을 만족했습니다.')
    else:
        print(num_ce - my_num_ce, '학점이 부족합니다.')
    # 추천과목 매핑 후 추출
    recom_ce = make_recommend_list(my_dic_ce, dic_ce)
    if not recom_ce:
        print('모든 필수과목을 들었습니다!')
    else:
        print('들어야하는 과목입니다.')
        for s_num in recom_ce:
            al = AllLecture.objects.get(subject_num=s_num)
            recom_ce_list.append(al.subject_name);
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)
    print("")

    #-----------------------------------------------------------------------------
    return render(request, "compare.html", {"recom_ce":recom_ce,"recom_ce_list":recom_ce_list,"need_me_score":need_me_score,"need_ms_score":need_ms_score,"final_num_my_ms":final_num_my_ms,"gs_sum":gs_sum , "data_sum":data_sum , "remain":remain, "num_me":num_me,"my_num_me":my_num_me , "num_ms":num_ms,"my_num_ms":my_num_ms})

# 셀레니움 파트 -------------------------------------------------------------------------------------

def get_Driver_uis(url):
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
    driver = get_Driver_uis(url) # 크롬 드라이버 <-- 실행하는 로컬 프로젝트 내에 존재해야됨 exe 파일로 존재
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
    return

def f_login(request):
    # 셀레니움으로 서버(uploaded_media)에 엑셀 다운
    selenium_uis(request.POST.get('id'), request.POST.get('pw'))
    # 다운로드 후 이름 변경
    file_name = time.strftime('%y-%m-%d %H_%M_%S') + '.xls'
    Initial_path = './app/uploaded_media'
    filename = max([Initial_path + "/" + f for f in os.listdir(Initial_path)],key=os.path.getctime)
    shutil.move(filename,os.path.join(Initial_path,file_name))
    return r_compare(request, file_name)

#-------------------------------------------------------------------------------------

# 비교 분석 파트 -------------------------------------------------------------------------------------

def db_make_dic(row):
    dic = defaultdict(lambda:-1)
    for s_num in row.subject_num_list.split(','):
        s_num = int(s_num)
        dic[s_num]
        sg = SubjectGroup.objects.filter(subject_num = s_num)
        if sg.exists():
            dic[s_num] = sg[0].group_num
    return dic

def df_make_dic(my_list):
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


def f_test(request):
    # 셀레니움으로 넘어올 학과 - 입학년도
    p_major = '디지털콘텐츠'
    p_year = 16
    
    # 파이썬 변수를 가지고 ind로 매핑
    ic_row = IndCombi.objects.get(major = p_major, year=p_year)
    p_ind = ic_row.ind      # 매핑된 ind
    print(p_ind)

    #---------------------------------------------------------
    # db에서 ind 를 가지고 모든 비교 기준 뽑아내기
    # 1. 이수학점 수치 기준
    gs_row = GraduateScore.objects.get(ind = p_ind)
    num_ss = gs_row.sum_score           # sum_score
    num_me = gs_row.major_essential     # major_essential
    num_ms = gs_row.major_selection     # major_selection
    num_ce = gs_row.core_essential      # core_essential   
    num_cs = gs_row.core_selection      # core_selection
    num_b = gs_row.basic                # basic
    print(num_ss, num_me, num_ms, num_ce, num_cs, num_b)
    
    # 2. 중필(교필) 필수과목. { 학수번호 : 그룹번호 } 딕셔너리로 매핑
    # ind로 필수과목 추출후 딕셔너리 만들기
    ce_row = CoreEssential.objects.get(ind = p_ind)
    dic_ce = db_make_dic(ce_row)
    print("중필")
    print(dic_ce)

    # 3. 중선(교선1) 필수과목
    cs_row = CoreSelection.objects.get(ind = p_ind)
    dic_cs = db_make_dic(cs_row)
    print("중선")
    print(dic_cs)
    
    # 4. 기교 필수과목 
    b_row = Basic.objects.get(ind = p_ind)
    dic_b = db_make_dic(b_row)
    print("기교")
    print(dic_b)

    #------------------------------------------------------------------------------
    # 입력받은 엑셀 파일 dataframe으로 변환
    data = pd.read_excel('./app/uploaded_media/기이수성적_재현.xls', index_col=None)
    data.to_csv('csvfile.csv', encoding='utf-8')

    # 논패과목 삭제
    '''
    for i in data.index:
        if data.loc[i]['등급'] == 'NP':
            data = data.drop(data.index[i])
    data.reset_index(inplace=True, drop=True)
    
    for i in range(data.shape[0]):
        if data['등급'][i]=='NP':
            data = data.drop(data.index[i])
    data.reset_index(inplace=True, drop=True)
    '''
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
    my_dic_ce = df_make_dic(df_ce['학수번호'].tolist())     # 사용자 학수-그룹번호 딕셔너리
    # 중선(교선)
    df_cs = data[data['이수구분'].isin(['교선1'])]
    df_cs.reset_index(inplace=True,drop=True)
    my_num_cs = df_cs['학점'].sum()
    my_dic_cs = df_make_dic(df_cs['학수번호'].tolist())
    # 기교
    df_b = data[data['이수구분'].isin(['기교'])]
    df_b.reset_index(inplace=True,drop=True)
    my_num_b = df_b['학점'].sum()
    my_dic_b = df_make_dic(df_b['학수번호'].tolist())

    # 사용자의 총 학점
    my_num_ss = my_num_me+my_num_ms+my_num_ce+my_num_cs+my_num_b
    
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
    cs_list=["사상과역사","사회와문화","융합과창업","자연과과학기술","세계와지구촌"]
    print(my_dic_cs)
    my_cs_list=[]
    for s_num in my_dic_cs:
        al = AllLecture.objects.get(subject_num=s_num)
        my_cs_list.append(al.selection)


    my_cs_list=set(my_cs_list)
    my_cs_list = list(my_cs_list)





    if(len(my_cs_list)>=3):
        print("영역 3가지를 만족하였습니다")
        print("만족한 영역은:")
        for i in cs_list:
            if i in my_cs_list:
                print(i)

    else:
        print("영역 3가지를 만족하지못했습니다");
        print("만족하지 못한 영역은:")
        for i in cs_list:
            if i not in my_cs_list:
                print(i)



    # 추천과목 매핑 후 추출
    recom_cs = make_recommend_list(my_dic_cs, dic_cs)
    if not recom_cs:
        print('모든 필수과목을 들었습니다!')
    else:
        print('들어야하는 과목입니다.')
        for s_num in recom_cs:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)
    #-------------------------------------------------------------------------------------------
    return HttpResponse('테스트 완료, 터미널 확인')