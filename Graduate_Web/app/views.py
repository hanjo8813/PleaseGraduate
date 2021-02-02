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

def recom_machine_learning(what, user_id):
    # 해당 이수구분에 맞게 데이터 merge
    del what['선택영역']
    rec = what
    #학생, 과목, 평점 하나의 데이터 프레임으로 묶기(User가 듣지 않은 과목 뭔지 찾기)
    tab = pd.crosstab(rec['학번'],rec['학수번호']) #사용자가 어떤 과목을 듣지 않았는지 확인하기 위하여 데이터프레임 shape 변경
    tab_t = tab.transpose().reset_index()
    item_ids =[] #유저가 듣지 않은 과목
    for i in range(tab_t.shape[0]):
        if tab_t[user_id][i] == 0:
            item_ids.append(tab_t['학수번호'][i])
    #학습준비
    reader = Reader(rating_scale=(0,2))
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
        a = model.predict(user_id, item_id, actual_rating)
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
    zipped = zip(list_to_query(item[:7]), score[:7])    # 최대 7개까지 추천해줌.

    return zipped

# --------------------------------------------- (졸업요건 검사 파트) ----------------------------------------------------------------

def r_result(request):
    # 세션에 담긴 변수 추출
    user_id = request.session.get('id')

    # userinfo 테이블에서 행 추출
    u_row = UserInfo.objects.get(student_id = user_id)

    user_info = {
        'id' : u_row.student_id,
        'name' : u_row.name,
        'major' : u_row.major,
        'year' : u_row.year,
    }
   
    # 고전독서 정보 파싱 후 info에 추가하기
    pass_book = 0
    if u_row.book == '고특통과': 
        pass_book = 2
    else:
        W, E, EW, S = int(u_row.book[0]), int(u_row.book[1]), int(u_row.book[2]), int(u_row.book[3])
        total_book = 0
        if W > 4: total_book += 4
        else : total_book += W
        if E > 2: total_book += 2
        else : total_book += E
        if EW > 3: total_book += 3
        else : total_book += EW
        if S > 1: total_book += 1
        else : total_book += S
        if total_book == 10:
            pass_book = 1
        user_info['W'] = W
        user_info['E'] = E
        user_info['EW'] = EW
        user_info['S'] = S
        user_info['total'] = total_book

    # 파이썬 변수를 가지고 ind로 매핑
    s_row = Standard.objects.get(user_dep = u_row.major, user_year = u_row.year)

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
    # user_grade 테이블에서 사용자의 성적표를 DF로 변환하기
    data = pd.DataFrame(columns=['학수번호', '이수구분', '선택영역', '학점'])
    ug = UserGrade.objects.filter(student_id = user_id)
    for u in ug:
        data.loc[len(data)] = [u.subject_num, u.classification, u.selection, u.grade]

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
    pass_p_cs = 1
    # 사용자가 안들은 영역 추출
    recom_cs_part = []
    if len(my_cs_part) < 3:
        pass_p_cs = 0
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
    # 머신러닝 할 데이터프레임 생성
    mr_train = pd.DataFrame(columns=['학번', '학수번호', '선택영역', '평점'])
    mc_train = pd.DataFrame(columns=['학번', '학수번호', '선택영역', '평점'])
    ec_train = pd.DataFrame(columns=['학번', '학수번호', '선택영역', '평점'])
    ug_MR = UserGrade.objects.filter(classification = '전필')
    ug_MC = UserGrade.objects.filter(classification = '전선')
    ug_EC = UserGrade.objects.filter(classification = '교선1')
    for u in ug_MR:
        mr_train.loc[len(mr_train)] = [u.student_id, u.subject_num, u.selection, 1]
    for u in ug_MC:
        mc_train.loc[len(mc_train)] = [u.student_id, u.subject_num, u.selection, 1]
    for u in ug_EC:
        ec_train.loc[len(ec_train)] = [u.student_id, u.subject_num, u.selection, 1]
    
    # 만약 사용자가 전필을 아예 안들었다면?
    if user_id not in mr_train['학번'].tolist() :
        new_data = {'학번': user_id, '학수번호': 0, '선택영역':0,'평점':0}
        mr_train = mr_train.append(new_data,ignore_index=True)
    # 만약 사용자가 전선을 아예 안들었다면?
    if user_id not in mc_train['학번'].tolist():
        new_data = {'학번': user_id, '학수번호': 0, '선택영역':0,'평점':0}
        mc_train = mc_train.append(new_data,ignore_index=True)
    # 중선 안들은 영역만 추천하기
    if recom_cs_part:
        store = []
        for i in recom_cs_part:
            is_in = ec_train['선택영역'] == i
            store.append(ec_train[is_in])
        ec_train = pd.concat(store).sort_values(by=['학번'], axis=0)
        ec_train = ec_train.reset_index(drop = True)
        new_data = {'학번': user_id, '학수번호': ec_train['학수번호'][0], '선택영역':0,'평점':0}
        ec_train = ec_train.append(new_data,ignore_index=True)
        
    recommend_sel = {
        'me' : recom_machine_learning(mr_train, user_id),    # 전필 zip(학수번호, 추천지수)    
        'ms' : recom_machine_learning(mc_train, user_id),    # 전선
        'cs' : recom_machine_learning(ec_train, user_id),   # 교선
    }

    # 과목 통과 여부 
    pass_me, pass_ms, pass_ce, pass_l_cs, pass_n_cs, pass_cs_tot, pass_b, pass_total = 0,0,0,0,0,0,0,0
    if standard_num['me'] <= my_num['me']: pass_me = 1
    if standard_num['ms'] <= my_num['ms'] + my_num['remain']: pass_ms = 1
    if not recom_ce: pass_ce = 1
    if not recom_cs: pass_l_cs = 1
    if standard_num['cs'] <= my_num['cs'] : pass_n_cs = 1     
    if pass_n_cs==1 and pass_p_cs==1: pass_cs_tot = 1
    if not recom_b: pass_b = 1
    if pass_me!=0 and pass_ms!=0 and pass_ce!=0 and  pass_cs_tot!=0 and pass_b!=0 and pass_book!=0 and u_row.eng!=0:
        pass_total = 1
        
    pass_obj = {
        'total' : pass_total,
        'n_me' : pass_me,
        'lack_me' : standard_num['me'] - my_num['me'],
        'lack_ms' : standard_num['ms'] - my_num['ms'] - my_num['remain'],
        'n_ms' : pass_ms,
        'l_ce' : pass_ce,       # 중필 필수과목 통과여부
        't_cs' : pass_cs_tot,   # 중선 기준 학점+필수영역 통과여부
        'n_cs' : pass_n_cs,     # 중선 기준 학점 통과여부
        'l_cs' : pass_l_cs,     # 중선 필수과목 통과여부
        'p_cs' : pass_p_cs,     # 중선 필수영역 통과여부
        'l_b' : pass_b,         # 기교 필수과목 통과여부
        'book' : pass_book,     # 고전독서 인증여부
        'eng' : u_row.eng,      # 영어인증여부
    } 

    # 공학인증 기준이 있는지 검사.
    en_exist = 0
    if s_row.sum_eng != 0:  # 존재한다면
        en_exist = 1

    context = {
        'user_info' : user_info,            # 사용자 정보
        'my_num' : my_num,                  # 사용자 이수학점들
        'standard_num' : standard_num,      # 기준 수치 
        'standard_list' : standard_list,    # 기준 필수과목 리스트
        'recommend_ess' : recommend_ess,    # 필수과목 추천리스트
        'recommend_sel' : recommend_sel,    # 선택과목 추천리스트
        'cs_part' : cs_part,                # 중선 영역
        'pass_obj' : pass_obj,              # 패스 여부
        'en_exist' : en_exist,              # 공학인증 기준 존재여부
    }
    
    return render(request, "result.html", context)


# --------------------------------------------- (공학인증 파트) ----------------------------------------------------------------

def r_en_result(request):
    user_id = request.session.get('id')
    # user_id = '16011140'

    # userinfo 테이블에서 행 추출
    u_row = UserInfo.objects.get(student_id = user_id)

    user_info = {
        'id' : u_row.student_id,
        'name' : u_row.name,
    }

    # 기준 뽑아내기
    s_row = Standard.objects.get(user_dep = u_row.major, user_year=u_row.year)

    # df 생성
    # user_grade 테이블에서 사용자의 성적표를 DF로 변환하기
    data = pd.DataFrame(columns=['년도', '학기', '학수번호', '학점'])
    ug = UserGrade.objects.filter(student_id = user_id)
    for u in ug:
        data.loc[len(data)] = [u.year, u.semester, u.subject_num, u.grade]

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
        root = '/srv/SGH_for_AWS/Graduate_Web/app/uploaded_media'
        options.add_experimental_option('prefs', {'download.default_directory' : root} )
        driver = webdriver.Chrome('/home/ubuntu/Downloads/chromedriver', options=options)
    driver.get(url)
    return driver

def f_login(request):
    # r_loading에서 받은 세션 꺼내기
    id = request.session.get('id')
    pw = request.session.get('pw')
    year = id[:2]

    if platform.system() == 'Windows':
        # 1. 고전독서인증센터 크롤링 ----------------------------------------------------------------------------
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
        # ID/PW 틀렸을 때 예외처리 ***
        try:
            driver.switch_to.frame(0)
        except:
            driver.quit()
            messages.error(request, 'ID/PW를 다시 확인하세요! (Caps Lock 확인)')
            request.session.clear()
            return redirect('/head/')
        driver.find_element_by_class_name("box02").click()  # 고전독서 인증현황 페이지로 감
        #------------------------------------------------------------------------------------------------- selenium part
        html = driver.page_source  # 페이지 소스 가져오기 , -> 고전독서 인증현황 페이지 html 가져오는것
        # 독서 권수 리스트에 저장
        soup = BeautifulSoup(html, 'html.parser')
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

        # 학과-학번이 기준에 있는지 검사 - 예외처리
        st = Standard.objects.filter(user_year = year, user_dep = major)
        # 존재하지 않으면
        if not st.exists():
            messages.error(request, '아직 PleaseGraduate에 해당 학과-학번의 수강편람 기준이 없어 검사가 불가합니다.')
            request.session.clear()
            return redirect('/head/')

        # 2. uis 크롤링 ----------------------------------------------------------------------------
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
        time.sleep(1.5)
        # 영어인증 test
        driver.switch_to_default_content()
        driver.switch_to.frame(2)
        driver.execute_script("javaScript:frameResize(this);")
        time.sleep(0.5)
        driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_20SCH_SUH_STUD');")
        time.sleep(0.5)  # 자바스크립트 실행시간 기다려줘야함 must need
        driver.find_element_by_xpath('//*[@id="SELF_STUDSELF_SUB_20SCH_SUH_STUDSuhJudgeSelfQ"]').click()
        time.sleep(1.5)  # 마찬가지로 창 뜨고 기다려줘야 팝업창 볼 수 있음
        popup = driver.window_handles[1]  # 팝업 창
        driver.switch_to_window(popup)
        driver.find_element_by_xpath('//*[@id="ckb1_item0"]/table/tbody/tr/td/table/tbody/tr/td/input').click()
        eng = 0
        driver.quit()

        # 기존 회원인지 검사
        ui = UserInfo.objects.filter(student_id = id)
        if not ui.exists():
            # user_info 테이블에 정보 추가
            new_ui = UserInfo()
            new_ui.student_id = id
            new_ui.year = int(id[:2])
            new_ui.major = major
            new_ui.name = name
            new_ui.book = book
            new_ui.eng = eng
            new_ui.save()
        else:
            # user_info 테이블에 정보 수정
            for u in ui:
                u.book = book
                u.eng = eng
                u.save()
            # user_grade 테이블의 해당 회원 성적표 삭제하기
            ug = UserGrade.objects.filter(student_id = id)
            ug.delete()

        # 파일명 변경
        file_path = './app/uploaded_media/'
        new_file_name = time.strftime('%y-%m-%d %H_%M_%S') + '.xls'
        file_name = max([file_path + f for f in os.listdir(file_path)],key=os.path.getctime)
        shutil.move(file_name,os.path.join(file_path,new_file_name))
        time.sleep(1)
        df = pd.read_excel(file_path + new_file_name, index_col=None) # 해당 엑셀을 DF화 시킴
        os.remove(file_path + new_file_name)    # 해당 엑셀파일 삭제
        # DF에서 불필요 칼럼 삭제
        df.drop(['교직영역', '평가방식', '평점', '개설학과코드'], axis=1, inplace=True)
        # 논패, F과목 삭제
        n = df.shape[0]
        flag = 0    
        while(True):
            for i in range(n):
                if i == n-1 :
                    flag = 1
                if df['등급'][i]=='NP' or df['등급'][i]=='F' or df['등급'][i]=='FA':
                    df = df.drop(df.index[i])
                    n -= 1
                    df.reset_index(inplace=True, drop=True)
                    break
            if flag == 1:
                break
        # DF를 테이블에 추가
        for i, row in df.iterrows():
            new_ug = UserGrade()
            new_ug.student_id = id
            new_ug.year = row['년도']
            new_ug.semester = row['학기']
            new_ug.subject_num = row['학수번호']
            new_ug.subject_name = row['교과목명']
            new_ug.classification = row['이수구분']
            new_ug.selection = row['선택영역']
            new_ug.grade = row['학점']
            new_ug.grade_credit = row['등급']
            new_ug.save()

    else:
        # 가상 디스플레이를 활용해 실행속도 단축
        display = Display(visible=0, size=(1024, 768))
        display.start()

                # 1. 고전독서인증센터 크롤링 ----------------------------------------------------------------------------
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
        # ID/PW 틀렸을 때 예외처리 ***
        try:
            driver.switch_to.frame(0)
        except:
            driver.quit()
            display.stop()
            messages.error(request, 'ID/PW를 다시 확인하세요! (Caps Lock 확인)')
            request.session.clear()
            return redirect('/head/')
        driver.find_element_by_class_name("box02").click()  # 고전독서 인증현황 페이지로 감
        #------------------------------------------------------------------------------------------------- selenium part
        html = driver.page_source  # 페이지 소스 가져오기 , -> 고전독서 인증현황 페이지 html 가져오는것
        # 독서 권수 리스트에 저장
        soup = BeautifulSoup(html, 'html.parser')
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

        # 학과-학번이 기준에 있는지 검사 - 예외처리
        st = Standard.objects.filter(user_year = year, user_dep = major)
        # 존재하지 않으면
        if not st.exists():
            display.stop()
            messages.error(request, '아직 PleaseGraduate에 해당 학과-학번의 수강편람 기준이 없어 검사가 불가합니다.')
            request.session.clear()
            return redirect('/head/')

        # 2. uis 크롤링 ----------------------------------------------------------------------------
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
        time.sleep(1.5)
        #---------------------------------------------------------------- 영어성적 가져오기
        driver.switch_to_default_content()
        driver.switch_to.frame(2)
        driver.execute_script("javaScript:frameResize(this);")
        time.sleep(0.5)
        driver.execute_script("javascript:onMenu('SELF_STUDSELF_SUB_20SCH_SUH_STUD');")
        time.sleep(0.5)  # 자바스크립트 실행시간 기다려줘야함 must need
        driver.find_element_by_xpath('//*[@id="SELF_STUDSELF_SUB_20SCH_SUH_STUDSuhJudgeSelfQ"]').click()
        time.sleep(1.5)  # 마찬가지로 창 뜨고 기다려줘야 팝업창 볼 수 있음
        popup = driver.window_handles[1]  # 팝업 창
        driver.switch_to_window(popup)
        time.sleep(0.5)
        driver.find_element_by_xpath('//*[@id="ckb1_item0"]/table/tbody/tr/td/table/tbody/tr/td/input').click()
        driver.find_element_by_xpath('//*[@id="ckb2_item0"]/table/tbody/tr/td/table/tbody/tr/td/input').click()
        driver.find_element_by_id('btnClose_btn').click()
        time.sleep(0.5)
        driver.switch_to_window(     driver.window_handles[0])  # 다시 uis 창으로 윈도우 바꿔놓기
        driver.switch_to_frame(3)  # 이 사이트에서는 프레임 0 - 3 총 4개
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # 드라이버의 현재 source(html) 가져오기
        driver.switch_to_frame(0)
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # 드라이버의 현재 source(html) 가져오기
        k = soup.find('div', id='lbl179').select_one('div').string.strip().replace('\n','')  # 영어 합격 불합격 저장하는변수 , true false 로 변경 예정
        if k == '불합격':
            eng = 0
        elif k == '합격':
            eng = 1
        driver.quit()
        display.stop()

        # 기존 회원인지 검사
        ui = UserInfo.objects.filter(student_id = id)
        if not ui.exists():
            # user_info 테이블에 정보 추가
            new_ui = UserInfo()
            new_ui.student_id = id
            new_ui.year = int(id[:2])
            new_ui.major = major
            new_ui.name = name
            new_ui.book = book
            new_ui.eng = eng
            new_ui.save()
        else:
            # user_info 테이블에 정보 수정
            for u in ui:
                u.book = book
                u.eng = eng
                u.save()
            # user_grade 테이블의 해당 회원 성적표 삭제하기
            ug = UserGrade.objects.filter(student_id = id)
            ug.delete()

        # 파일명 변경
        file_path = '/srv/SGH_for_AWS/Graduate_Web/app/uploaded_media/'
        new_file_name = time.strftime('%y-%m-%d %H_%M_%S') + '.xls'
        file_name = max([file_path + f for f in os.listdir(file_path)],key=os.path.getctime)
        shutil.move(file_name,os.path.join(file_path,new_file_name))
        time.sleep(1)
        df = pd.read_excel(file_path + new_file_name, index_col=None) # 해당 엑셀을 DF화 시킴
        os.remove(file_path + new_file_name)    # 해당 엑셀파일 삭제
        # DF에서 불필요 칼럼 삭제
        df.drop(['교직영역', '평가방식', '평점', '개설학과코드'], axis=1, inplace=True)
        # 논패, F과목 삭제
        n = df.shape[0]
        flag = 0    
        while(True):
            for i in range(n):
                if i == n-1 :
                    flag = 1
                if df['등급'][i]=='NP' or df['등급'][i]=='F' or df['등급'][i]=='FA':
                    df = df.drop(df.index[i])
                    n -= 1
                    df.reset_index(inplace=True, drop=True)
                    break
            if flag == 1:
                break
        # DF를 테이블에 추가
        for i, row in df.iterrows():
            new_ug = UserGrade()
            new_ug.student_id = id
            new_ug.year = row['년도']
            new_ug.semester = row['학기']
            new_ug.subject_num = row['학수번호']
            new_ug.subject_name = row['교과목명']
            new_ug.classification = row['이수구분']
            new_ug.selection = row['선택영역']
            new_ug.grade = row['학점']
            new_ug.grade_credit = row['등급']
            new_ug.save()

    return r_result(request)
        
     

#---------------------------------------------------------------------------------------------------------------



























# ----------------------------------------------- (웹 연동 테스트) --------------------------------------------------------------------


# result 페이지 테스트용.
def result_test(request):
    # 세션에 담긴 변수 추출
    user_id = '15011187'

    # userinfo 테이블에서 행 추출
    u_row = UserInfo.objects.get(student_id = user_id)

    user_info = {
        'id' : u_row.student_id,
        'name' : u_row.name,
        'major' : u_row.major,
        'year' : u_row.year,
    }
   
    # 고전독서 정보 파싱 후 info에 추가하기
    pass_book = 0
    if u_row.book == '고특통과': 
        pass_book = 2
    else:
        W, E, EW, S = int(u_row.book[0]), int(u_row.book[1]), int(u_row.book[2]), int(u_row.book[3])
        total_book = 0
        if W > 4: total_book += 4
        else : total_book += W
        if E > 2: total_book += 2
        else : total_book += E
        if EW > 3: total_book += 3
        else : total_book += EW
        if S > 1: total_book += 1
        else : total_book += S
        if total_book == 10:
            pass_book = 1
        user_info['W'] = W
        user_info['E'] = E
        user_info['EW'] = EW
        user_info['S'] = S
        user_info['total'] = total_book

    # 파이썬 변수를 가지고 ind로 매핑
    s_row = Standard.objects.get(user_dep = u_row.major, user_year = u_row.year)

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
    # user_grade 테이블에서 사용자의 성적표를 DF로 변환하기
    data = pd.DataFrame(columns=['학수번호', '이수구분', '선택영역', '학점'])
    ug = UserGrade.objects.filter(student_id = user_id)
    for u in ug:
        data.loc[len(data)] = [u.subject_num, u.classification, u.selection, u.grade]

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
    pass_p_cs = 1
    # 사용자가 안들은 영역 추출
    recom_cs_part = []
    if len(my_cs_part) < 3:
        pass_p_cs = 0
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
    # 머신러닝 할 데이터프레임 생성
    mr_train = pd.DataFrame(columns=['학번', '학수번호', '선택영역', '평점'])
    mc_train = pd.DataFrame(columns=['학번', '학수번호', '선택영역', '평점'])
    ec_train = pd.DataFrame(columns=['학번', '학수번호', '선택영역', '평점'])
    ug_MR = UserGrade.objects.filter(classification = '전필')
    ug_MC = UserGrade.objects.filter(classification = '전선')
    ug_EC = UserGrade.objects.filter(classification = '교선1')
    for u in ug_MR:
        mr_train.loc[len(mr_train)] = [u.student_id, u.subject_num, u.selection, 1]
    for u in ug_MC:
        mc_train.loc[len(mc_train)] = [u.student_id, u.subject_num, u.selection, 1]
    for u in ug_EC:
        ec_train.loc[len(ec_train)] = [u.student_id, u.subject_num, u.selection, 1]
    
    # 만약 사용자가 전필을 아예 안들었다면?
    if user_id not in mr_train['학번'].tolist() :
        new_data = {'학번': user_id, '학수번호': 0, '선택영역':0,'평점':0}
        mr_train = mr_train.append(new_data,ignore_index=True)
    # 만약 사용자가 전선을 아예 안들었다면?
    if user_id not in mc_train['학번'].tolist():
        new_data = {'학번': user_id, '학수번호': 0, '선택영역':0,'평점':0}
        mc_train = mc_train.append(new_data,ignore_index=True)
    # 중선 안들은 영역만 추천하기
    if recom_cs_part:
        store = []
        for i in recom_cs_part:
            is_in = ec_train['선택영역'] == i
            store.append(ec_train[is_in])
        ec_train = pd.concat(store).sort_values(by=['학번'], axis=0)
        ec_train = ec_train.reset_index(drop = True)
        new_data = {'학번': user_id, '학수번호': ec_train['학수번호'][0], '선택영역':0,'평점':0}
        ec_train = ec_train.append(new_data,ignore_index=True)
        
    recommend_sel = {
        'me' : recom_machine_learning(mr_train, user_id),    # 전필 zip(학수번호, 추천지수)    
        'ms' : recom_machine_learning(mc_train, user_id),    # 전선
        'cs' : recom_machine_learning(ec_train, user_id),   # 교선
    }

    # 과목 통과 여부 
    pass_me, pass_ms, pass_ce, pass_l_cs, pass_n_cs, pass_cs_tot, pass_b, pass_total = 0,0,0,0,0,0,0,0
    if standard_num['me'] <= my_num['me']: pass_me = 1
    if standard_num['ms'] <= my_num['ms'] + my_num['remain']: pass_ms = 1
    if not recom_ce: pass_ce = 1
    if not recom_cs: pass_l_cs = 1
    if standard_num['cs'] <= my_num['cs'] : pass_n_cs = 1     
    if pass_n_cs==1 and pass_p_cs==1: pass_cs_tot = 1
    if not recom_b: pass_b = 1
    if pass_me!=0 and pass_ms!=0 and pass_ce!=0 and  pass_cs_tot!=0 and pass_b!=0 and pass_book!=0 and u_row.eng!=0:
        pass_total = 1
        
    pass_obj = {
        'total' : pass_total,
        'n_me' : pass_me,
        'lack_me' : standard_num['me'] - my_num['me'],
        'lack_ms' : standard_num['ms'] - my_num['ms'] - my_num['remain'],
        'n_ms' : pass_ms,
        'l_ce' : pass_ce,       # 중필 필수과목 통과여부
        't_cs' : pass_cs_tot,   # 중선 기준 학점+필수영역 통과여부
        'n_cs' : pass_n_cs,     # 중선 기준 학점 통과여부
        'l_cs' : pass_l_cs,     # 중선 필수과목 통과여부
        'p_cs' : pass_p_cs,     # 중선 필수영역 통과여부
        'l_b' : pass_b,         # 기교 필수과목 통과여부
        'book' : pass_book,     # 고전독서 인증여부
        'eng' : u_row.eng,      # 영어인증여부
    } 

    # 공학인증 기준이 있는지 검사.
    en_exist = 0
    if s_row.sum_eng != 0:  # 존재한다면
        en_exist = 1

    context = {
        'user_info' : user_info,            # 사용자 정보
        'my_num' : my_num,                  # 사용자 이수학점들
        'standard_num' : standard_num,      # 기준 수치 
        'standard_list' : standard_list,    # 기준 필수과목 리스트
        'recommend_ess' : recommend_ess,    # 필수과목 추천리스트
        'recommend_sel' : recommend_sel,    # 선택과목 추천리스트
        'cs_part' : cs_part,                # 중선 영역
        'pass_obj' : pass_obj,              # 패스 여부
        'en_exist' : en_exist,              # 공학인증 기준 존재여부
    }
    
    return render(request, "result.html", context)








#  -------------------------------------------- (터미널 테스트) ---------------------------------------------------------



def f_test(request):
   
    return HttpResponse('테스트 완료, 터미널 확인')

