# 파이썬 라이브러리
import os
import json
import time
import shutil
import pandas as pd
import numpy as np
import platform
import random
from surprise import SVD, accuracy
from surprise import Reader, Dataset
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
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

def r_index(request):
    return render(request, "index.html")

def r_head(request):
    return render(request, "head.html")

def f_logout(request):
    request.session.clear()
    return redirect('/head/')

def r_loading(request):
    # 사용자 id(학번)과 pw을 세션에 저장 (request의 세션부분에 저장되는것)
    request.session['id']=request.POST.get('id')
    request.session['pw']=request.POST.get('pw')
    return render(request, "loading.html")





def list_to_query(list_):
    al = AllLecture.objects.none()
    for s_num in list_:
        temp = AllLecture.objects.filter(subject_num = s_num)
        al = temp | al
    return al

def make_dic(my_list):
    my_list.sort()
    dic = defaultdict(lambda:-1)
    for s_num in my_list:
        dic[s_num]
        sg = SubjectGroup.objects.filter(subject_num = s_num)
        if sg.exists():
            dic[s_num] = sg[0].group_num
    return dic

def make_recommend_list(my_dic, dic):
    my_dic_ = my_dic.copy()
    dic_ = dic.copy()
    check = dic.copy()
    for k in check.keys():
        check[k] = 0
    # 만족한 학수번호는 딕셔너리에서 pop
    for s_num in my_dic_.keys():
        # 1차로 학수번호 검사
        # 있다면? -> 기준 딕셔너리에서 팝.
        if s_num in dic_.keys():
            check[s_num] = 1
            dic_.pop(s_num)
        # 없다면? 2차 검사
        else :
            g_num = my_dic_[s_num]
            for k, v in dic_.items():
                if v == g_num :
                    s_num = k
            if g_num != -1 and (g_num in dic_.values()):
                check[s_num] = 1
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
    return recommend, list(check.values())

def recom_machine_learning(what, file_name):
    # 해당 이수구분에 맞게 데이터 merge
    del what['선택영역']
    rec = what
    #학생, 과목, 평점 하나의 데이터 프레임으로 묶기(User가 듣지 않은 과목 뭔지 찾기)
    user = file_name
    tab = pd.crosstab(rec['이름'],rec['학수번호']) #사용자가 어떤 과목을 듣지 않았는지 확인하기 위하여 데이터프레임 shape 변경
    tab_t = tab.transpose().reset_index()
    item_ids =[] #유저가 듣지 않은 과목
    for i in range(tab_t.shape[0]):
        if tab_t[user][i] == 0:
            item_ids.append(tab_t['학수번호'][i])
    #학습준비
    reader = Reader(rating_scale=(0,2)) #이건 이제 
    data = Dataset.load_from_df(df=rec, reader=reader)
    train = data.build_full_trainset()
    test = train.build_testset()
    #모델학습
    model = SVD(n_factors=100, n_epochs=20,random_state=123)
    model.fit(train) # 모델 학습 하는 코드
    actual_rating = 0
    #학습결과 데이터프레임화
    item = [] #과목명
    score = [] #유사도점수
    for item_id in item_ids :
        a = model.predict(user, item_id, actual_rating)
        item.append(a[1])
        score.append(a[3])
    df = pd.DataFrame({'item':item,'score':score})
    result = df.sort_values(by=['score'],axis=0,ascending=False).reset_index(drop=True) #결과 데이터프레임

    item = result['item'].tolist()
    score = result['score'].tolist()
    # score 백분율화
    for i in range(len(score)):
        score[i] = round(score[i] / 2 * 100, 3)
    # 최신과목만 추출
    for i, z in enumerate(zip(item,score)):
        nl = NewLecture.objects.filter(subject_num=z[0])
        if nl.exists() == 0:
            item.pop(i)
            score.pop(i)
    zipped = zip(list_to_query(item), score)
    
    return zipped

# --------------------------------------------- (졸업요건 검사 파트) ----------------------------------------------------------------

def r_result(request):
    # 세션에 담긴 변수 추출
    file_name = request.session.get('file_name')
    info = request.session.get('info')
    # 원래 info에서 영어도 넘어와야함. -> 일단 변수로 저장
    info['eng'] = 0

    # 셀레니움으로 넘어온 변수들
    p_year = info["year"]
    p_major = info["major"]

    user_info = {
        'id' : info["id"],
        'name' : info["name"],
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

    #------------------------------------------------------------------------------
    # 입력받은 엑셀 파일 dataframe으로 변환
    root = './app/uploaded_media/' + file_name
    data = pd.read_excel(root, index_col=None)

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

    # 전필 초과시 
    remain = 0
    if standard_num['me'] < df_me['학점'].sum() :
        remain = df_me['학점'].sum() - standard_num['me']
    # 내 이수학점 수치
    my_num ={
        'ss' : data['학점'].sum(),              # sum_score
        'me' : df_me['학점'].sum() - remain,    # major_essential
        'ms' : df_ms['학점'].sum(),             # major_selection
        'ce' : df_ce['학점'].sum() ,            # core_essential   
        'cs' : df_cs['학점'].sum(),             # core_selection
        'b' : df_b['학점'].sum(),               # basic
        'remain' : remain,
    }

    # 사용자가 들은 dic 추출
    my_dic_ce = make_dic(df_ce['학수번호'].tolist())
    my_dic_cs = make_dic(df_cs['학수번호'].tolist())
    my_dic_b = make_dic(df_b['학수번호'].tolist())

    #-------------------------------------------------------------------------------------
    # 필수과목 >> 추천과목 리스트 생성 (최신과목으로)   
    recom_ce, check_ce = make_recommend_list(my_dic_ce, dic_ce)   # 중필
    recom_cs, check_cs = make_recommend_list(my_dic_cs, dic_cs)   # 중선
    recom_b, check_b = make_recommend_list(my_dic_b, dic_b)      # 기교
    standard_list = {
        'ce' : zip(list_to_query(dic_ce.keys()), check_ce),
        'cs' : zip(list_to_query(dic_cs.keys()), check_cs),
        'b' : zip(list_to_query(dic_b.keys()), check_b),
    }

    recommend_ess = {
        'ce' : list_to_query(recom_ce),
        'cs' : list_to_query(recom_cs),
        'b' : list_to_query(recom_b),
    }

    # 영역 추출
    cs_part =["사상과역사","사회와문화","융합과창업","자연과과학기술","세계와지구촌"]   # 기준 영역 5개
    my_cs_part = list(set(df_cs[df_cs['선택영역'].isin(cs_part)]['선택영역'].tolist()))
    # 영역 통과 여부
    bo = 1
    # 사용자가 안들은 영역 추출
    recom_cs_part = []
    if len(my_cs_part) < 3:
        bo = 0
        recom_cs_part = list(set(cs_part) - set(my_cs_part))
    # 사용자의 부족 영역 체크
    part_check = ['이수' for _ in range(5)]
    for i, c in enumerate(cs_part):
        if c not in my_cs_part:
            part_check[i] = '미이수'
    cs_part = {
        'check' : part_check,
        'all' : cs_part,
    }

    #------------------------------------------------------------------------------------
    # 전필/전선/중선 >> 추천과목 리스트 생성 (최신과목으로)
    path_dir = './app/uploaded_media/' #엑셀 저장 디렉토리 지정
    file_list = os.listdir(path_dir) # 디렉토리내 파일 읽어서 리스트형식으로 저장
    data = []
    for i in range(len(file_list)): # .DS_Store 쓰레기 값 제거 (디렉토리에 있는지 확인해봐야함)
        if file_list[i][0] =='.':
            del file_list[i]
            break
    for i in range(len(file_list)): # 엑셀 to 데이터프레임 변경 후 data 리스트에 저장
        data.append(pd.read_excel(path_dir+file_list[i], index_col=None))
    #데이터 전처리
    MR = [] # 전공필수
    MC = [] # 전공선택
    EC = [] # 교양선택
    for i in range(len(file_list)): 
        del data[i]['학기'] #필요없는 컬럼 삭제
        del data[i]['교과목명']
        del data[i]['교직영역']
        del data[i]['학점']
        del data[i]['평가방식']
        del data[i]['등급']
        del data[i]['개설학과코드']
        data[i] = data[i].rename({'년도':'이름'},axis='columns') #년도 컬럼 이름 컬럼으로 컬럼명 변경
        data[i]['이름'] = file_list[i] #이름 컬럼에 이름 덮어씀
        MR.append(data[i][data[i]['이수구분'].isin(['전필'])]) #전필만 모아서 저장
        MC.append(data[i][data[i]['이수구분'].isin(['전선'])]) #전선만 모아서 저장
        EC.append(data[i][data[i]['이수구분'].isin(['교선1'])]) #교선만 모아서 저장
        del MR[i]['이수구분'] #필요없는 컬럼 삭제
        del MC[i]['이수구분']
        del EC[i]['이수구분']
        MR[i]['평점'] = 1 #이수했는지 확인하는 숫자 1로 덮어씀
        MC[i]['평점'] = 1
        EC[i]['평점'] = 1

    mr_train = pd.concat(MR,ignore_index=True) 
    mc_train = pd.concat(MC,ignore_index=True) 
    ec_train = pd.concat(EC,ignore_index=True) 
    store = []
    cs_ml = []
    if recom_cs_part:
        for i in recom_cs_part:
            is_in = ec_train['선택영역'] == i
            store.append(ec_train[is_in])
        ec_train = pd.concat(store).sort_values(by=['이름'], axis=0)
        ec_train = ec_train.reset_index(drop = True)
        new_data = {'이름': file_name, '학수번호': ec_train['학수번호'][0], '선택영역':0,'평점':0}
        ec_train = ec_train.append(new_data,ignore_index=True)
        
    recommend_sel = {
        'me' : recom_machine_learning(mr_train, file_name),    # 전필 zip(학수번호, 추천지수)    
        'ms' : recom_machine_learning(mc_train, file_name),    # 전선
        'cs' : recom_machine_learning(ec_train, file_name),   # 교선
    }

    pass_me = 0
    pass_ms = 0
    pass_ce = 0
    pass_cs = 0
    pass_b = 0
    if standard_num['me'] <= my_num['me']:
        pass_me = 1
    if standard_num['ms'] <= my_num['me'] + my_num['remain']:
        pass_ms = 1
    if not recom_ce:
        pass_ce = 1
    if not recom_cs:
        pass_cs = 1
    if not recom_b:
        pass_b = 1

    pass_obj = {
        'n_me' : pass_me,
        'lack_me' : standard_num['me'] - my_num['me'],
        'lack_ms' : standard_num['ms'] - my_num['ms'] - my_num['remain'],
        'n_ms' : pass_ms,
        'l_ce' : pass_ce,       # 중필 필수과목 
        'l_cs' : pass_cs,       # 중선 필수과목
        'p_cs' : bo,            # 중선 필수영역
        'l_b' : pass_b,         # 기교 필수과목
        'eng' : info['eng'],    # 영어인증
    }

    context = {
        'user_info' : user_info,            # 사용자 정보
        'my_num' : my_num,                  # 사용자 이수학점들
        'standard_num' : standard_num,      # 기준 수치 
        'standard_list' : standard_list,    # 기준 필수과목 리스트
        'recommend_ess' : recommend_ess,    # 필수과목 추천리스트
        'recommend_sel' : recommend_sel,    # 선택과목 추천리스트
        'cs_part' : cs_part,                # 중선 영역
        'pass_obj' : pass_obj               # 패스 여부
    }

    return render(request, "result.html", context)


# --------------------------------------------- (공학인증 파트) ----------------------------------------------------------------

def r_en_result(request):
    '''
    # 테스트용
    file_name = 'test12.xls'
    info = {
        'book' : [4, 4, 4, 1, 13],
        'major' : '소프트웨어',
        'id' : '16011140',
        'year' : '18',
        'name' : '안재현',
        'eng' : 0,
    }
    '''

    # 세션에 담긴 변수 추출
    file_name = request.session.get('file_name')
    info = request.session.get('info')

    p_year = info["year"]
    p_major = info["major"]

    user_info = {
        'id' : info["id"],
        'name' : info["name"],
    }

    s_row = Standard.objects.get(user_dep = p_major, user_year=p_year)

    # df 생성
    root = './app/uploaded_media/' + file_name
    data = pd.read_excel(root, index_col=None)

    # 사용자가 들은 과목리스트 전부를 딕셔너리로.
    my_engine_admit = make_dic(data['학수번호'].tolist())

    # 1.전문 교양
    dic_pro = make_dic([int(s_num) for s_num in s_row.pro_acc_list.split(',')])
    recom_pro, check_pro = make_recommend_list(my_engine_admit, dic_pro)
    mynum_pro = data[data['학수번호'].isin(dic_pro.keys())]['학점'].sum()

    # 2. bsm 필수
    dic_bsm_ess = make_dic([int(s_num) for s_num in s_row.bsm_ess_list.split(',')])
    recom_bsm_ess, check_bsm_ess = make_recommend_list(my_engine_admit, dic_bsm_ess)
    mynum_bsm_ess = data[data['학수번호'].isin(dic_bsm_ess.keys())]['학점'].sum()

    # 3. bsm 선택 (16학번일때만 해당)
    if s_row.bsm_sel_list:
        dic_bsm_sel = make_dic([int(s_num) for s_num in s_row.bsm_sel_list.split(',')])
        mynum_bsm_ess += data[data['학수번호'].isin(dic_bsm_sel.keys())]['학점'].sum()  # bsm 선택 이수학점을 더한다.

    # 4. 전공 설계
    # 4-1. 전공 전체 학점
    dic_build = make_dic([int(s_num) for s_num in s_row.engine_major_list.split(',')])
    recom_build, check_build =make_recommend_list(my_engine_admit,dic_build)
    mynum_build = data[data['학수번호'].isin(dic_build.keys())]['학점'].sum()
 
    # int화
    df_e = data[data['학수번호'] == 9993]
    if not df_e.empty:
        num_df_e = df_e['년도'].sum()
        num_df_2 = int(df_e['학기'].sum().replace('학기', ''))
    df_e2 = data[data['학수번호'] == 9960]
    num_df_e2 = df_e2['년도'].sum()

    # 소설기부터 df 추출
    data2 = data
    n = data2.shape[0]
    flag = 0
    while (True):
        for i in range(n):
            if i == n - 1:
                flag = 1
            if not df_e.empty:
                if data2['년도'][i] < num_df_e:  # 소설기이전 학기 삭제
                    data2 = data2.drop(data2.index[i])
                    n -= 1
                    data2.reset_index(inplace=True, drop=True)
                    break
                elif data2['년도'][i] == num_df_e and data2['학기'][i] == "1학기":
                    data2 = data2.drop(data2.index[i])
                    n -= 1
                    data2.reset_index(inplace=True, drop=True)
                    break
            if not df_e2.empty:
                if data2['년도'][i] > num_df_e2:  # 캡스톤 이후 학기 삭제
                    data2 = data2.drop(data2.index[i])
                    n -= 1
                    data2.reset_index(inplace=True, drop=True)
                    break
        if flag == 1:
            break
    # 사용자가 소설기부터 들은 강의의 학수번호 리스트->딕셔너리
    my_engine_admit2 = make_dic(data2['학수번호'].tolist())

    # 4-2. 설계 필수과목 안들은 리스트
    dic_build_ess = make_dic([int(s_num) for s_num in s_row.build_ess_list.split(',')])
    recom_build_ess, check_build_ess = make_recommend_list(my_engine_admit2, dic_build_ess)

    # 4-3. 설계 선택과목 중 안들은 리스트
    dic_build_sel = make_dic([int(s_num) for s_num in s_row.build_sel_list.split(',')])
    recom_build_sel, check_build_sel = make_recommend_list(my_engine_admit2, dic_build_sel)


    standard_num ={
        'total' : s_row.sum_eng,    # 공학인증 총학점 기준 - 92
        'pro' : s_row.pro,          # 전문교양 기준 학점
        'bsm' : s_row.bsm,          # bsm 기준 학점
        'build' : s_row.build,      # 설계과목 기준학점
    }

    my_num = {
        'total' : mynum_pro+mynum_build+mynum_bsm_ess,              
        'pro' : mynum_pro,
        'bsm' : mynum_bsm_ess,        
        'build' : mynum_build,
    }

    standard_list = {
        'pro' : zip(list_to_query(dic_pro.keys()),check_pro),
        'bsm_ess' : zip(list_to_query(dic_bsm_ess.keys()), check_bsm_ess),
        'bsm_sel' : [],
        'build_ess' : zip(list_to_query(dic_build_ess.keys()),check_build_ess),
        'build_sel' : zip(list_to_query(dic_build_sel.keys()),check_build_sel),
    }

    # 전공영역 추천 과목 중 부족학점만큼 랜덤으로 골라주기
    n = standard_num['build'] - my_num['build']
    random.shuffle(recom_build)
    recom_build = recom_build[:n//3+1]

    recommend = {
        'pro' : list_to_query(recom_pro),
        'bsm_ess' : list_to_query(recom_bsm_ess), # bsm 추천시 합쳐서 추천.
        'build' : list_to_query(recom_build),
    }

    # 필수과목 패스 여부
    pass_pro = 0
    pass_bsm_ess = 0
    pass_build_ess = 0
    pass_build_sel = 0
    if not recom_pro:
        pass_pro = 1
    if not recom_bsm_ess:
        pass_bsm_ess = 1
    if not recom_build_ess:
        pass_build_ess = 1
    # 설계선택 여부
    if sum(check_build_sel) >= 3 :
        pass_build_sel = 1
    if len(recom_build_ess) == 2:  # 소설기도 안들은 경우
        pass_build_sel = -1
    
    pass_obj = {
        'pro' : pass_pro,
        'bsm_ess' : pass_bsm_ess,
        'build_ess' : pass_build_ess,
        'build_sel' : pass_build_sel,
        'n' : n,
    }

    # 16학번일 경우에 bsm 선택과목 추가.
    if s_row.bsm_sel_list:
        pass_bsm_sel = 0
        if len(recom_bsm_ess) <= 1:
            pass_bsm_sel = 1
        pass_obj['bsm_sel'] = pass_bsm_sel
        standard_list['bsm_sel'] = list_to_query(dic_bsm_sel.keys())
    
    context={
        'user_info' : user_info,
        'standard_num' : standard_num,
        'my_num' : my_num,
        'standard_list' : standard_list,
        'recommend' : recommend,
        'pass_obj' : pass_obj,
    }
   
    return render(request, "en_result.html", context)




# --------------------------------------------- (셀레니움 파트) ----------------------------------------------------------------



def get_Driver(url):
    # 윈도우일 때 -> 개발용
    if platform.system() == 'Windows':
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        root = os.getcwd() + '\\app\\uploaded_media'
        options.add_experimental_option('prefs', {'download.default_directory' : root} )
        driver = webdriver.Chrome('./chromedriver.exe', options=options)
    # ubuntu일 때 -> 배포용
    else:
        options = webdriver.ChromeOptions()
        # 크롬창을 열지않고 백그라운드로 실행
        #options.add_argument("headless")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        root = os.getcwd() + '/app/uploaded_media'
        options.add_experimental_option('prefs', {'download.default_directory' : root} )
        driver = webdriver.Chrome('/home/ubuntu/Downloads/chromedriver', options=options)
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
    time.sleep(0.5)
    # 기이수성적조회로 클릭 이동
    driver.find_element_by_xpath('''//*[@id="SELF_STUDSELF_SUB_30SCH_SUG05_STUD"]/table/tbody/tr[1]''').click()
    time.sleep(1)
    # 최상위(default) 프레임으로 이동
    driver.switch_to.default_content()
    time.sleep(0.5)
    # 프레임 경우의 수 다 찾고 이동
    driver.switch_to.frame(3)
    driver.switch_to.frame(0)
    time.sleep(0.5)
    # 다운로드 버튼 x_path 클릭
    x = driver.find_element_by_xpath('''//*[@id="btnDownload_btn"]''')
    x.click()
    time.sleep(2)

    '''
    #---------------------------------------------------------------- 영어성적 가져오기
    driver.switch_to_default_content()
    driver.switch_to.frame(2)
    driver.execute_script("javaScript:frameResize(this);")
    time.sleep(1)
    driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_20SCH_SUH_STUD');")
    time.sleep(1)  # 자바스크립트 실행시간 기다려줘야함 must need
    driver.find_element_by_xpath('//*[@id="SELF_STUDSELF_SUB_20SCH_SUH_STUDSuhJudgeSelfQ"]').click()
    # k = driver.switch_to_window()
    time.sleep(1)  # 마찬가지로 창 뜨고 기다려줘야 팝업창 볼 수 있음
    mywindow = driver.window_handles[0]  # uis 창
    popup =  driver.window_handles[1]  # 팝업 창
    driver.switch_to_window(popup)
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="ckb1_item0"]/table/tbody/tr/td/table/tbody/tr/td/input').click()

    driver.find_element_by_xpath('//*[@id="ckb2_item0"]/table/tbody/tr/td/table/tbody/tr/td/input').click()
    driver.find_element_by_id('btnClose_btn').click()
    time.sleep(2)
    # print(driver.current_window_handle)
    driver.switch_to_window(     driver.window_handles[0])  # 다시 uis 창으로 윈도우 바꿔놓기
    driver.switch_to_frame(3)  # 이 사이트에서는 프레임 0 - 3 총 4개
    soup = BeautifulSoup(driver.page_source, 'html.parser')  # 드라이버의 현재 source(html) 가져오기
    # print(soup)
    # print("이부분이 첫번째프레임")
    # 3  , 1
    driver.switch_to_frame(0)
    soup = BeautifulSoup(driver.page_source, 'html.parser')  # 드라이버의 현재 source(html) 가져오기
    k = soup.find('div', id='lbl179').select_one('div').string.strip().replace('\n','')  # 영어 합격 불합격 저장하는변수 , true false 로 변경 예정
    if k == '불합격':
        eng = 0
    elif k == '합격':
        eng = 1
    '''

    driver.quit()
    return 

def selenium_book(id, pw):
    url = 'https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=classic.sejong.ac.kr/ssoLogin.do'
    driver = get_Driver(url)  # 크롬 드라이버 <-- 실행하는 로컬 프로젝트 내에 존재해야됨 exe 파일로 존재
    checked = driver.find_element_by_xpath('//*[@id="chkNos"]').get_attribute('checked')
    if checked:
        driver.find_element_by_xpath('//*[@id="chkNos"]').click() # 체크창 클릭
        alert = driver.switch_to_alert()
        alert.dismiss()
    time.sleep(0.5)
    # id , pw 입력할 곳 찾기
    tag_id = driver.find_element_by_id("id")  # id 입력할곳 찾기 변수는 id태그
    tag_pw = driver.find_element_by_id("password")
    tag_id.clear()
    # id , pw 보내기
    tag_id.send_keys(id)
    tag_pw.send_keys(pw)
    time.sleep(0.5)
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
    # 세션에서 ID/PW 뽑아냄
    s_id = request.session.get('id')
    s_pw = request.session.get('pw')

    # 가상 디스플레이를 활용해 실행속도 단축
    if platform.system() != 'Windows':
        display = Display(visible=0, size=(1024, 768))
        display.start()

    # 셀레니움으로 서버(uploaded_media)에 엑셀 다운
    selenium_uis(s_id,s_pw)
    # 다운로드 후 이름 변경
    file_name = time.strftime('%y-%m-%d %H_%M_%S') + '.xls'
    Initial_path = './app/uploaded_media'
    filename = max([Initial_path + "/" + f for f in os.listdir(Initial_path)],key=os.path.getctime)
    shutil.move(filename,os.path.join(Initial_path,file_name))
    # 대양휴머니티 크롤링 후 학과/학번/인증권수 넘기기
    info = selenium_book(s_id, s_pw)
    # 세션에 변경 파일이름과 유저 정보를 저장
    request.session['file_name']=file_name
    request.session['info']=info

    if platform.system() != 'Windows':
        display.stop()

    return r_result(request)

#---------------------------------------------------------------------------------------------------------------



























# ----------------------------------------------- (웹 연동 테스트) --------------------------------------------------------------------


# result 페이지 테스트용.
def result_test(request):
    file_name = 'test5.xls'

    info = {
        'book' : [4, 4, 4, 1, 13],
        'major' : '디지털콘텐츠',
        'id' : '111111111',
        'year' : '15',
        'name' : '이름',
        'eng' : 0,
    }
    # 원래 info에서 영어도 넘어와야함. -> 일단 변수로 저장
    info['eng'] = 0

    # 셀레니움으로 넘어온 변수들
    p_year = info["year"]
    p_major = info["major"]

    user_info = {
        'id' : info["id"],
        'name' : info["name"],
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

    #------------------------------------------------------------------------------
    # 입력받은 엑셀 파일 dataframe으로 변환
    root = './app/uploaded_media/' + file_name
    data = pd.read_excel(root, index_col=None)

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

    # 전필 초과시 
    remain = 0
    if standard_num['me'] < df_me['학점'].sum() :
        remain = df_me['학점'].sum() - standard_num['me']
    # 내 이수학점 수치
    my_num ={
        'ss' : data['학점'].sum(),              # sum_score
        'me' : df_me['학점'].sum() - remain,    # major_essential
        'ms' : df_ms['학점'].sum(),             # major_selection
        'ce' : df_ce['학점'].sum() ,            # core_essential   
        'cs' : df_cs['학점'].sum(),             # core_selection
        'b' : df_b['학점'].sum(),               # basic
        'remain' : remain,
    }

    # 사용자가 들은 dic 추출
    my_dic_ce = make_dic(df_ce['학수번호'].tolist())
    my_dic_cs = make_dic(df_cs['학수번호'].tolist())
    my_dic_b = make_dic(df_b['학수번호'].tolist())

    #-------------------------------------------------------------------------------------
    # 필수과목 >> 추천과목 리스트 생성 (최신과목으로)   
    recom_ce, check_ce = make_recommend_list(my_dic_ce, dic_ce)   # 중필
    recom_cs, check_cs = make_recommend_list(my_dic_cs, dic_cs)   # 중선
    recom_b, check_b = make_recommend_list(my_dic_b, dic_b)      # 기교
    standard_list = {
        'ce' : zip(list_to_query(dic_ce.keys()), check_ce),
        'cs' : zip(list_to_query(dic_cs.keys()), check_cs),
        'b' : zip(list_to_query(dic_b.keys()), check_b),
    }

    recommend_ess = {
        'ce' : list_to_query(recom_ce),
        'cs' : list_to_query(recom_cs),
        'b' : list_to_query(recom_b),
    }

    # 영역 추출
    cs_part =["사상과역사","사회와문화","융합과창업","자연과과학기술","세계와지구촌"]   # 기준 영역 5개
    my_cs_part = list(set(df_cs[df_cs['선택영역'].isin(cs_part)]['선택영역'].tolist()))
    # 영역 통과 여부
    bo = 1
    # 사용자가 안들은 영역 추출
    recom_cs_part = []
    if len(my_cs_part) < 3:
        bo = 0
        recom_cs_part = list(set(cs_part) - set(my_cs_part))
    # 사용자의 부족 영역 체크
    part_check = ['이수' for _ in range(5)]
    for i, c in enumerate(cs_part):
        if c not in my_cs_part:
            part_check[i] = '미이수'
    cs_part = {
        'check' : part_check,
        'all' : cs_part,
    }

    #------------------------------------------------------------------------------------
    # 전필/전선/중선 >> 추천과목 리스트 생성 (최신과목으로)
    path_dir = './app/uploaded_media/' #엑셀 저장 디렉토리 지정
    file_list = os.listdir(path_dir) # 디렉토리내 파일 읽어서 리스트형식으로 저장
    data = []
    for i in range(len(file_list)): # .DS_Store 쓰레기 값 제거 (디렉토리에 있는지 확인해봐야함)
        if file_list[i][0] =='.':
            del file_list[i]
            break
    for i in range(len(file_list)): # 엑셀 to 데이터프레임 변경 후 data 리스트에 저장
        data.append(pd.read_excel(path_dir+file_list[i], index_col=None))
    #데이터 전처리
    MR = [] # 전공필수
    MC = [] # 전공선택
    EC = [] # 교양선택
    for i in range(len(file_list)): 
        del data[i]['학기'] #필요없는 컬럼 삭제
        del data[i]['교과목명']
        del data[i]['교직영역']
        del data[i]['학점']
        del data[i]['평가방식']
        del data[i]['등급']
        del data[i]['개설학과코드']
        data[i] = data[i].rename({'년도':'이름'},axis='columns') #년도 컬럼 이름 컬럼으로 컬럼명 변경
        data[i]['이름'] = file_list[i] #이름 컬럼에 이름 덮어씀
        MR.append(data[i][data[i]['이수구분'].isin(['전필'])]) #전필만 모아서 저장
        MC.append(data[i][data[i]['이수구분'].isin(['전선'])]) #전선만 모아서 저장
        EC.append(data[i][data[i]['이수구분'].isin(['교선1'])]) #교선만 모아서 저장
        del MR[i]['이수구분'] #필요없는 컬럼 삭제
        del MC[i]['이수구분']
        del EC[i]['이수구분']
        MR[i]['평점'] = 1 #이수했는지 확인하는 숫자 1로 덮어씀
        MC[i]['평점'] = 1
        EC[i]['평점'] = 1

    mr_train = pd.concat(MR,ignore_index=True) 
    mc_train = pd.concat(MC,ignore_index=True) 
    ec_train = pd.concat(EC,ignore_index=True) 
    store = []
    cs_ml = []
    if recom_cs_part:
        for i in recom_cs_part:
            is_in = ec_train['선택영역'] == i
            store.append(ec_train[is_in])
        ec_train = pd.concat(store).sort_values(by=['이름'], axis=0)
        ec_train = ec_train.reset_index(drop = True)
        new_data = {'이름': file_name, '학수번호': ec_train['학수번호'][0], '선택영역':0,'평점':0}
        ec_train = ec_train.append(new_data,ignore_index=True)
        
    recommend_sel = {
        'me' : recom_machine_learning(mr_train, file_name),    # 전필 zip(학수번호, 추천지수)    
        'ms' : recom_machine_learning(mc_train, file_name),    # 전선
        'cs' : recom_machine_learning(ec_train, file_name),   # 교선
    }

    pass_me = 0
    pass_ms = 0
    pass_ce = 0
    pass_cs = 0
    pass_b = 0
    if standard_num['me'] <= my_num['me']:
        pass_me = 1
    if standard_num['ms'] <= my_num['me'] + my_num['remain']:
        pass_ms = 1
    if not recom_ce:
        pass_ce = 1
    if not recom_cs:
        pass_cs = 1
    if not recom_b:
        pass_b = 1

    pass_obj = {
        'n_me' : pass_me,
        'lack_me' : standard_num['me'] - my_num['me'],
        'lack_ms' : standard_num['ms'] - my_num['ms'] - my_num['remain'],
        'n_ms' : pass_ms,
        'l_ce' : pass_ce,       # 중필 필수과목 
        'l_cs' : pass_cs,       # 중선 필수과목
        'p_cs' : bo,            # 중선 필수영역
        'l_b' : pass_b,         # 기교 필수과목
        'eng' : info['eng'],    # 영어인증
    }

    context = {
        'user_info' : user_info,            # 사용자 정보
        'my_num' : my_num,                  # 사용자 이수학점들
        'standard_num' : standard_num,      # 기준 수치 
        'standard_list' : standard_list,    # 기준 필수과목 리스트
        'recommend_ess' : recommend_ess,    # 필수과목 추천리스트
        'recommend_sel' : recommend_sel,    # 선택과목 추천리스트
        'cs_part' : cs_part,                # 중선 영역
        'pass_obj' : pass_obj               # 패스 여부
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





    #공학인증

    df_e = data[data['학수번호'] == 9993]
    if not df_e.empty:
        num_df_e = df_e['년도'].sum()
        num_df_2 = int(df_e['학기'].sum().replace('학기', ''))

    if df_e.empty:
        print("sw설계 기초 안들었다")
    else:
        print("들었다")

    df_e2 = data[data['학수번호'] == 9960]
    num_df_e2 = df_e2['년도'].sum()

    if df_e2.empty:  # 캡스톤들었는지 여부 확인
        print("안 들었다")
    else:
        print("들었다.")

    data2 = data
    n = data2.shape[0]
    flag = 0
    while (True):
        for i in range(n):
            if i == n - 1:
                flag = 1
            if not df_e.empty:
                if data2['년도'][i] < num_df_e:  # 소설기이전 학기 삭제
                    data2 = data2.drop(data2.index[i])
                    n -= 1
                    data2.reset_index(inplace=True, drop=True)
                    break
                elif data2['년도'][i] == num_df_e and data2['학기'][i] == "1학기":
                    data2 = data2.drop(data2.index[i])
                    n -= 1
                    data2.reset_index(inplace=True, drop=True)
                    break
            if not df_e2.empty:
                if data2['년도'][i] > num_df_e2:  # 캡스톤 이후 학기 삭제
                    data2 = data2.drop(data2.index[i])
                    n -= 1
                    data2.reset_index(inplace=True, drop=True)
                    break
        if flag == 1:
            break
    print(data2)


    # 공학인증

    # db에서 ind 를 가지고 공학인증 비교 기준 뽑아내기
    # 1. 이수학점 수치 기준
    num_engin_sum = s_row.sum_eng  # 공학인증 총학점
    num_pro = s_row.pro  # 전문 교양 학점
    num_bsm = s_row.bsm  # bsm 학점
    num_build = s_row.build  # 설계과목 학점

    print(num_engin_sum, num_pro, num_bsm, num_build)

    df_engin = data
    df_engin.reset_index(inplace=True, drop=True)
    my_engine_admit = make_dic(df_engin['학수번호'].tolist())

    # 1.전문 교양
    print("전문교양")
    dic_pro = make_dic([int(s_num) for s_num in s_row.pro_acc_list.split(',')])
    recom_pro = make_recommend_list(my_engine_admit, dic_pro)
    if not recom_pro:
        print('모든 전문교양 필수과목을 들었습니다!')
    else:
        print('전문교양 중 들어야하는 과목입니다.')
        for s_num in recom_pro:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)

    # 2. bsm 필수
    print("bsm필수")
    dic_bsm_ess = make_dic([int(s_num) for s_num in s_row.bsm_ess_list.split(',')])
    recom_bsm_ess = make_recommend_list(my_engine_admit, dic_bsm_ess)
    if not recom_bsm_ess:
        print('모든 bsm 필수과목을 들었습니다!')
    else:
        print('bsm필수 중 들어야하는 과목입니다.')
        for s_num in recom_bsm_ess:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)

    # 3. bsm 선택
    print("ss",s_row.bsm_sel_list)
    if  s_row.bsm_sel_list:
        dic_bsm_sel = make_dic([int(s_num) for s_num in s_row.bsm_sel_list.split(',')])
        recom_bsm_sel = make_recommend_list(my_engine_admit, dic_bsm_sel)
        print('bsm선택')
        if (len(recom_bsm_sel) <= 1):  # bsm선택중 남은과목이 한개 이상
            print("bsm 선택과목2개중", 2 - len(recom_bsm_sel), "과목 을 이수하였습니다.")
        else:
            print('bsm선택 중 들어야하는 과목입니다. 이중 하나만 수강하면 됩니다.')
            for s_num in recom_bsm_sel:
                al = AllLecture.objects.get(subject_num=s_num)
                print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)


    # 4.설계과목
    df_engin2 = data2
    df_engin2.reset_index(inplace=True, drop=True)
    my_engine_admit2 = make_dic(df_engin2['학수번호'].tolist())

    # 설계 필수과목
    print("설계과목필수")
    dic_build_ess = make_dic([int(s_num) for s_num in s_row.build_ess_list.split(',')])
    recom_build_ess = make_recommend_list(my_engine_admit2, dic_build_ess)

    if not recom_build_ess:
        print('모든 설계 필수과목을 들었습니다!')
    else:
        print('설계 필수과목 중 들어야하는 과목입니다.')
        for s_num in recom_build_ess:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)

    # 설계 선택과목
    print("설계과목선택")
    dic_build_sel = make_dic([int(s_num) for s_num in s_row.build_sel_list.split(',')])

    num_build_sel = len(dic_build_sel)
    recom_build_sel = make_recommend_list(my_engine_admit2, dic_build_sel)



    df_engine_major = data
    df_engine_major.reset_index(inplace=True, drop=True)
    my_dic_engine_major = make_dic(df_engine_major['학수번호'].tolist())

    dic_engine_major=make_dic([int(s_num) for s_num in s_row.engine_major_list.split(',')])
    num_em=0
    for s_num in dic_engine_major:
        al=AllLecture.objects.get(subject_num=s_num)
        num_em+=al.grade


    print("설계인증 전공학점 총합:",num_em)
    recom_engine_major=make_recommend_list(my_dic_engine_major,dic_engine_major)
    print("sSSS")
    temp=0
    for s_num in recom_engine_major:
        al = AllLecture.objects.get(subject_num=s_num)
        temp+=al.grade
    print("내가안들은 설계 인증 전공학점:",temp)

    my_num_em=num_em-temp
    print("전공영역 60점중 내가 이수한 학점:",my_num_em)
    if my_num_em<60:
        for s_num in recom_engine_major:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)
    print("이것중",60-my_num_em,"학점을 더 수강하여야 합니다.")

    print("내가들은학점", num_build_sel - len(recom_build_sel))

    if (num_build_sel - len(
            recom_build_sel) >= 3):  # (11은 설계 선택과목  db에 저장되어있는 갯수)=num_build_sel, recom_build_sel은 내가 듣지않은 설계선택 학수번호가 들어가있는 리스트여서 len()으로 내가 안들은 수업 갯수 를 11에서 빼면 내가들은 수업의 갯수
        print("설계 선택과목 필수학점 9점외 선택과목 3점을 만족하였습니다.")
        if (my_num_em >= num_build):
            print("설계 영역을 만족하였습니다.")
        else:
            print("공학인증 설계영역 전공학점", num_build - my_num_em, "학점이 부족합니다.")
    else:
        print("설계 선택과목 필수학점9점외에 선택과목 3점중", num_build_sel - len(recom_build_sel), "점을 수강하였습니다.",
              3 - num_build_sel + (len(recom_build_sel)), "개의 과목을 더 수강하여야합니다.")
        for s_num in recom_build_sel:
            al = AllLecture.objects.get(subject_num=s_num)
            print(" >> ", al.subject_num, al.subject_name, al.classification, al.selection, al.grade)


    return HttpResponse('테스트 완료, 터미널 확인')







# 쓰레기통 -------------------------------------------------------------------------------------------
