# 파이썬 라이브러리
import os
import json
import time
import datetime
import pandas as pd
import platform
import bcrypt
from django_pandas.io import read_frame
# 장고 관련 참조
from django.shortcuts import render, redirect
from django.http import HttpResponse
# 모델 참조
from django.db.models import Count
from ..models import *


#  -------------------------------------------- (테스트 페이지 렌더링) ---------------------------------------------------------

def r_admin_test(request):
    # 로컬에서만 접근 가능하도록 하기
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')
    request.session.clear()
    uid = []
    for row in NewUserInfo.objects.all():
        uid.append([row.last_update_time, row.register_time,
                   row.major, row.student_id, row.name])

    uid = sorted(uid, key=lambda x: x[1], reverse=True)

    context = {
        'uid': uid,
        'uid_num': len(uid),
    }
    return render(request, "admin_test.html", context)

#  -------------------------------------------- (사용자 테스트) ---------------------------------------------------------


def f_user_test(request):
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')

    user_id = request.POST['user_id']
    request.session['id'] = user_id

    #update_json(user_id)

    return redirect('/mypage/')

#  -------------------------------------------- (사용자 테스트) ---------------------------------------------------------


def f_insert_user(request):
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')

    # admin 페이지 입력데이터 검증
    student_id = request.POST.get('student_id')
    major = request.POST.get('major')
    name = request.POST.get('name')
    if '' in [student_id, major, name]:
        return HttpResponse('❌❌❌ 세가지 데이터를 모두 입력해야 함 ❌❌❌')

    register_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    password = bcrypt.hashpw('1234'.encode(
        'utf-8'), bcrypt.gensalt()).decode('utf-8')
    year = student_id[:2]
    major_status = '해당없음'
    book = '고특통과'
    eng = '해당없음'

    new_ui = NewUserInfo()
    new_ui.register_time = register_time
    new_ui.student_id = student_id
    new_ui.password = password
    new_ui.year = year
    new_ui.major = major
    new_ui.major_status = major_status
    new_ui.name = name
    new_ui.book = book
    new_ui.eng = eng
    new_ui.save()

    return HttpResponse('삽입 완료, new_user_info 테이블 확인')

#  -------------------------------------------- (강의정보 테이블 업데이트) ---------------------------------------------------------


def make_merge_df():
    # 사용법
    # 1. upadate_lecture 폴더안에 1학기 폴더(1st_semester)와 2학기 폴더(2nd_semester) 구분되어 있음
    # 2. 두 학기의 최신 강의목록 엑셀 파일을 각 폴더에 넣는다.
    # 3. 각 폴더에는 엑셀파일이 하나씩만 존재해야한다.
    # 4. 엑셀의 확장자는 .xlsx 가 아닌 .xls 이어야하므로 로컬에서 변경해준다.
    # 5. 엑셀파일에서 칼럼명이 살짝 이상할때가 있으므로 (한칸띄우기 등등) 검토가 필요함.
    # 6. DB 변경하는 시간이 1분정도 걸림

    need_col = ['학수번호', '교과목명', '이수구분', '선택영역', '학점']
    # 1학기 엑셀 불러오기
    file_path = './app/update_lecture/1st_semester/'
    file_name = os.listdir(file_path)[0]
    # 해당 엑셀을 DF화 시킴
    df_sem_1 = pd.read_excel(file_path + file_name, index_col=None)
    df_sem_1.drop([d for d in list(df_sem_1) if d not in need_col],
                  axis=1, inplace=True)     # 필요한 컬럼만 추출
    # 2학기 엑셀 불러오기
    file_path = './app/update_lecture/2nd_semester/'
    file_name = os.listdir(file_path)[0]
    # 해당 엑셀을 DF화 시킴
    df_sem_2 = pd.read_excel(file_path + file_name, index_col=None)
    df_sem_2.drop([d for d in list(df_sem_2) if d not in need_col],
                  axis=1, inplace=True)     # 필요한 컬럼만 추출

    # 두 df를 병합, 중복제거
    # ** 우선순위 학기의 df를 앞에다 두어야 함 **
    df_merge = pd.concat([df_sem_2, df_sem_1])
    df_merge.drop_duplicates(['학수번호'], inplace=True, ignore_index=True)
    # 선택영역 Nan을 바꾸기
    df_merge.fillna('', inplace=True)
    # 최신강의 학수번호 리스트
    s_num_list = df_merge['학수번호'].tolist()
    return df_merge, s_num_list


def f_test_update(request):
    # 로컬에서만 접근 가능하도록 하기
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')

    df_merge, s_num_list = make_merge_df()
    # 1. test_new_lecture 업데이트
    # 우선 text_new_lecture 테이블의 데이터를 모두 삭제해준다
    TestNewLecture.objects.all().delete()
    time.sleep(10)   # 삭제하는 시간 기다리기

    # 테이블에 최신 학수번호를 삽입
    for s_num in s_num_list:
        new_nl = TestNewLecture()
        new_nl.subject_num = s_num
        new_nl.save()

    # 2. test_all_lecture 업데이트
    # test_all_lecture 쿼리셋을 df로 변환
    df_al = read_frame(TestAllLecture.objects.all())
    # df 칼럼명 바꾸기
    df_al.rename(columns={'subject_num': '학수번호', 'subject_name': '교과목명',
                 'classification': '이수구분', 'selection': '선택영역', 'grade': '학점'}, inplace=True)

    copy_df_al = df_al.copy()

    # 기존 테이블 df에서 학수번호 겹치는 것을 삭제 (과목정보 최신화)
    for i, row in df_al.iterrows():
        if int(row['학수번호']) in s_num_list:
            copy_df_al.drop(i, inplace=True)
    # 삭제한 df에 최신 강의 df를 병합
    df_new_al = pd.concat([copy_df_al, df_merge])
    # test_all_lecture 테이블 안 데이터 모두 삭제
    TestAllLecture.objects.all().delete()
    time.sleep(20)

    # 삭제 후에 최신 강의 DF를 한 행씩 테이블에 추가
    for i, row in df_new_al.iterrows():
        new_al = TestAllLecture()
        new_al.subject_num = row['학수번호']
        new_al.subject_name = row['교과목명']
        new_al.classification = row['이수구분']
        new_al.selection = row['선택영역']
        new_al.grade = row['학점']
        new_al.save()

    return HttpResponse('업데이트 완료, MySQL test_all_lecture / test_new_lecture 테이블 확인')


def f_update(request):
    # 로컬에서만 접근 가능하도록 하기
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')

    df_merge, s_num_list = make_merge_df()

    # 1. new_lecture 업데이트
    NewLecture.objects.all().delete()
    time.sleep(10)
    for s_num in s_num_list:
        new_nl = NewLecture()
        new_nl.subject_num = s_num
        new_nl.save()

    # 2. all_lecture 업데이트
    df_al = read_frame(AllLecture.objects.all())
    df_al.rename(columns={'subject_num': '학수번호', 'subject_name': '교과목명',
                 'classification': '이수구분', 'selection': '선택영역', 'grade': '학점'}, inplace=True)
    for i, row in df_al.iterrows():
        if int(row['학수번호']) in s_num_list:
            df_al.drop(i, inplace=True)
    df_new_al = pd.concat([df_al, df_merge])
    AllLecture.objects.all().delete()
    time.sleep(10)
    for i, row in df_new_al.iterrows():
        new_al = AllLecture()
        new_al.subject_num = row['학수번호']
        new_al.subject_name = row['교과목명']
        new_al.classification = row['이수구분']
        new_al.selection = row['선택영역']
        new_al.grade = row['학점']
        new_al.save()

    return HttpResponse('업데이트 완료, MySQL all_lecture / new_lecture 테이블 확인')

#  -------------------------------------------- (학과-학번 기준 엑셀 DB에 넣기) ---------------------------------------------------------


def f_input_st(request):
    # 사용법
    # 1. 해당 폴더에 들어있는 엑셀(xls) 첫 행 아래로 새로운 데이터를 추가한다.
    # 2. 아니면 관리용 엑셀파일을 복사 -> xls로 변경 -> 첫 행 삭제

    # 로컬에서만 접근 가능하도록 하기
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')

    # 엑셀 불러오기
    file_path = './app/update_lecture/input_standard/'
    file_name = os.listdir(file_path)[0]
    df = pd.read_excel(file_path + file_name, index_col=None)
    df.fillna(0, inplace=True)

    # 테이블 데이터 삭제
    Standard.objects.all().delete()
    time.sleep(5)   # 삭제하는 시간 기다리기

    for i, row in df.iterrows():
        new_st = Standard()
        new_st.index = i
        new_st.user_year = row['user_year']
        new_st.user_dep = row['user_dep']
        new_st.sum_score = int(row['sum_score'])
        new_st.major_essential = int(row['major_essential'])
        new_st.major_selection = int(row['major_selection'])
        new_st.core_essential = int(row['core_essential'])
        new_st.core_selection = int(row['core_selection'])
        new_st.basic = int(row['basic'])
        new_st.ce_list = str(row['ce_list'])
        new_st.cs_list = str(row['cs_list'])
        new_st.b_list = str(row['b_list'])
        new_st.english = json.dumps(eval(row['english']))
        new_st.sum_eng = int(row['sum_eng'])
        new_st.pro = int(row['pro'])
        new_st.bsm = int(row['bsm'])
        new_st.eng_major = int(row['eng_major'])
        new_st.build_sel_num = int(row['build_sel_num'])
        new_st.pro_ess_list = str(row['pro_ess_list'])
        new_st.bsm_ess_list = str(row['bsm_ess_list'])
        new_st.bsm_sel_list = str(row['bsm_sel_list'])
        new_st.build_start = str(int(row['build_start']))
        new_st.build_sel_list = str(row['build_sel_list'])
        new_st.build_end = str(int(row['build_end']))
        new_st.eng_major_list = str(row['eng_major_list'])
        new_st.save()

    return HttpResponse('삽입완료 standard 테이블 확인')


#  -------------------------------------------- (터미널 테스트) ---------------------------------------------------------


def f_test(request):
    # 로컬에서만 접근 가능하도록 하기
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')

    user_major = list(NewUserInfo.objects.values_list('major').distinct())
    all_major = list(Standard.objects.values_list('user_dep').distinct())
    for major in user_major:
        if major in all_major:
            all_major.remove(major)
    print(' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 아직 가입 안한 학과 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ')
    print()
    print(all_major)
    print()

    print(' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 학과별 회원수 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ')
    print()
    for row in sorted(NewUserInfo.objects.values_list('major').annotate(count=Count('major')), key=lambda x: x[1], reverse=True):
        print(row)
    print()

    print(' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 학번별 회원수 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ')
    print()
    for row in NewUserInfo.objects.values_list('year').annotate(count=Count('year')):
        print(row)
    print()

    return HttpResponse('테스트 완료, 터미널 확인')
