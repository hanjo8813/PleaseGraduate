# 파이썬 라이브러리
import os
import json
import time
import datetime
import shutil
import openpyxl
import pandas as pd
import numpy as np
import platform
import random
import xlrd
import bcrypt
from collections import Counter
from surprise import SVD, accuracy
from surprise import Reader, Dataset
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
from django_pandas.io import read_frame
# 장고 관련 참조
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
# 모델 참조
from django.db import models
from django.db.models import Value, Count, Sum
from .models import *
# AJAX 통신관련 참조
from django.views.decorators.csrf import csrf_exempt


# ---------------------------------------------------- ( 렌더링 함수 ) ----------------------------------------------------------------

def r_head(request):
    # 오늘 날자의 누적 방문자수를 추출
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    today_queryset = VisitorCount.objects.get(visit_date = today_date)
    visit_today = today_queryset.visit_count
    # 모든 날짜의 방문자수 총합을 구함 (aggregate는 딕셔너리 형태로 반환)
    sum_dict = VisitorCount.objects.aggregate(Sum('visit_count'))
    visit_total = sum_dict['visit_count__sum']
    # user_info 회원수 + new_user_info 회원수 합계
    user_num = NewUserInfo.objects.count()
    context = {
        'visit_today' : visit_today,
        'visit_total' : visit_total,
        'user_num' : user_num
    }
    return render(request, "head.html", context)

@csrf_exempt
def a_statistics(request):
    # POST로 온 form 데이터 꺼내기
    selection_list = request.POST.getlist('selection[]')
    grade_list = request.POST.getlist('grade[]')
    classification = request.POST.get('classification')
    # 이수구분에 따라 쿼리 날리기
    if classification == '교선1':
        cs_queryset = UserGrade.objects.exclude(year = '커스텀').filter(classification__in = ['교선1', '중선'], selection__in=selection_list, grade__in= grade_list)
    else:
        cs_queryset = UserGrade.objects.exclude(year = '커스텀').filter(classification = classification, grade__in= grade_list)
    cs_count = cs_queryset.values_list('subject_num').annotate(count=Count('subject_num'))
    # 쿼리셋을 리스트로 변환 -> 등장횟수에 따라 내림차순 정렬 
    cs_count = sorted(list(cs_count), key = lambda x : x[1], reverse=True)
    zip_lecture_count = []
    for s_num, count in cs_count:
        if AllLecture.objects.filter(subject_num = s_num).exists():
            lec_info = list(AllLecture.objects.filter(subject_num = s_num).values())[0]
            zip_lecture_count.append([lec_info, count])
    # context 전송
    context={
        'zip_lecture_count': zip_lecture_count
    }
    return JsonResponse(context)

def r_statistics(request):
    user_num = NewUserInfo.objects.count()
    major_num = NewUserInfo.objects.values('major').distinct().count()
    context = {
        'user_num' : user_num,
        'major_num' : major_num,
    }
    response = render(request, "statistics.html", context)
    # 쿠키 추가로 설정
    if request.COOKIES.get('is_visit') is None:
        now_dt = datetime.datetime.now()
        tommorow_dt = now_dt + datetime.timedelta(days=1)
        tommorow_midnight_str = tommorow_dt.strftime('%Y-%m-%d') + ' 00:00:00'
        tommorow_midnight_time = datetime.datetime.strptime(tommorow_midnight_str, '%Y-%m-%d %H:%M:%S')
        diff_dt = (tommorow_midnight_time - now_dt).seconds
        response.set_cookie('is_visit', 'visited', diff_dt)
        today_date = now_dt.strftime('%Y-%m-%d')
        vc = VisitorCount.objects.get(visit_date=today_date)
        vc.visit_count += 1
        vc.save()
    return response

def r_login(request):
    request.session.clear()
    response = render(request, "login.html")
    # 해당 사용자의 브라우저가 첫 방문일 경우 +1
    if request.COOKIES.get('is_visit') is None:
        # 쿠키 수명은 날짜가 바뀔 때까지 설정
        now_dt = datetime.datetime.now()
        tommorow_dt = now_dt + datetime.timedelta(days=1)
        tommorow_midnight_str = tommorow_dt.strftime('%Y-%m-%d') + ' 00:00:00'
        tommorow_midnight_time = datetime.datetime.strptime(tommorow_midnight_str, '%Y-%m-%d %H:%M:%S')
        diff_dt = (tommorow_midnight_time - now_dt).seconds
        response.set_cookie('is_visit', 'visited', diff_dt)
        # 오늘 날짜의 방문자수를 +1
        today_date = now_dt.strftime('%Y-%m-%d')
        vc = VisitorCount.objects.get(visit_date=today_date)
        vc.visit_count += 1
        vc.save()
    return response

def r_agree(request):
    target_qeuryset = Standard.objects.only('user_year', 'user_dep')
    # { 학과 : [21, 20 ...] }
    dict_dep_yearlist = defaultdict(lambda:'')
    for row in target_qeuryset:
        if row.user_dep not in dict_dep_yearlist.keys():
            dict_dep_yearlist[row.user_dep] += str(row.user_year)
        else:
            dict_dep_yearlist[row.user_dep] += ', ' + str(row.user_year)
    # 지원 학과 개수
    dep_num = len(dict_dep_yearlist.keys())
    # [ 학과, '21,20....' ] => 정렬
    target_list = [[ dep, year] for dep, year in dict_dep_yearlist.items()]
    target_list = sorted(target_list, key=(lambda x: x[0]))
    context = {
        'target' : target_list,
        'dep_num' : dep_num
    }
    return render(request, "agree.html", context)

def r_register(request):
    temp_user_info = request.session.get('temp_user_info')
    if not temp_user_info :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    return render(request, "register.html")

def r_success(request):
    temp_user_info = request.session.get('temp_user_info')
    if not temp_user_info :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    request.session.clear()
    return render(request, 'success.html')

def r_changePW(request):
    temp_user_id = request.session.get('temp_user_id')
    if not temp_user_id :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    return render(request, 'changePW.html')

def r_mypage(request):
    user_id = request.session.get('id')
    if not user_id :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    # user_info DB에서 json을 꺼내 contest 딕셔너리에 저장
    context = json.loads(ui_row.mypage_json)
    return render(request, "mypage.html", context)

def r_custom(request):
    user_id = request.session.get('id')
    if not user_id :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    # 그냥 mypage json을 넘겨주고 거기서 성적표 뽑아쓰자. (DB히트 감소)
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    mypage_context = json.loads(ui_row.mypage_json)
    context = {
        'grade' : mypage_context['grade'],
        'custom_grade' : mypage_context['custom_grade'],
    }
    return render(request, "custom.html", context)

def r_success_delete(request):
    user_id = request.session.get('id')
    if not user_id :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    request.session.clear()
    return render(request, 'success_delete.html')

def r_result(request):
    user_id = request.session.get('id')
    if not user_id :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    context = json.loads(ui_row.result_json)
    return render(request, "result.html", context)

def r_multi_result(request):
    user_id = request.session.get('id')
    if not user_id :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    context = json.loads(ui_row.result_json)
    return render(request, "multi_result.html", context)

def r_en_result(request):
    user_id = request.session.get('id')
    if not user_id :
        messages.error(request, '❌ 세션 정보가 없습니다!')
        return redirect('/')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    context = json.loads(ui_row.en_result_json)
    return render(request, "en_result.html", context)


# ---------------------------------------------------- ( 로그인 관련 ) ----------------------------------------------------------------

def f_logout(request):
    request.session.clear()
    return redirect('/')

def f_login(request):
    # ID PW 넘어옴
    user_id = request.POST.get('id')
    pw = request.POST.get('pw')
    # 그 값으로 모델에서 행 추출
    ui_row = NewUserInfo.objects.filter(student_id=user_id)
    # 우선 회원가입 되지 않았다면?
    if not ui_row.exists():
        messages.error(request, '⚠️ Please Graduate에 가입되지 않은 ID입니다.')
        return redirect('/login/')
    # 회원인데 비번이 틀렸다면? 입력받은 비번을 암호화하고 DB의 비번과 비교한다.
    if not bcrypt.checkpw(pw.encode('utf-8'), ui_row[0].password.encode('utf-8')):
        messages.error(request, '⚠️ Please Graduate 비밀번호를 확인하세요.')
        return redirect('/login/')
    # !! 로그인시마다 json을 최신화시킨다 !!
    update_json(user_id)
    # 세션에 ID와 전공상태 저장
    request.session['id'] = user_id
    return redirect('/mypage/')

# 비밀번호 찾기
def f_find_pw(request):
    user_id = request.POST.get('id2')
    pw = request.POST.get('pw2')
    ui_row = NewUserInfo.objects.filter(student_id = user_id)
    # 회원인지 확인
    if not ui_row.exists() :
        messages.error(request, '⚠️ Please Graduate에 가입되지 않은 ID입니다.')
        return redirect('/login/')
    ui_row = ui_row[0]
    # 대휴칼 셀레니움 돌리기(이름, 전공, 고독현황)
    temp_user_info = selenium_DHC(user_id, pw)
    if temp_user_info == 'err_auth':
        messages.error(request, '⚠️ 세종대학교 포털 ID/PW를 다시 확인하세요! (Caps Lock 확인)')
        return redirect('/login/')
    elif temp_user_info == 'err_enter_mybook':
        messages.error(request, '⚠️ 계약학과, 편입생, 재외국민전형 입학자는 회원가입이 불가능합니다.😥 \\n\\n ❓❓ 이에 해당하지 않는다면 세종포털사이트에서의 설정을 확인하세요.\\n https://portal.sejong.ac.kr 로그인 👉 정보수정 👉 개인정보수집동의 모두 동의')
        return redirect('/login/')
    elif temp_user_info == 'err_all':
        messages.error(request, '⛔ 대양휴머니티칼리지 로그인 중 예기치 못한 오류가 발생했습니다. 학교관련 포털이 다른 창에서 로그인되어 있다면 로그아웃 후 다시 시도하세요.')
        return redirect('/login/')
    # 임시 id를 세션에 넣어줌
    request.session['temp_user_id'] = user_id
    return redirect('/changePW/')

# ---------------------------------------------------- ( mypage 관련 ) ----------------------------------------------------------------

def f_mypage(user_id):
    ui_row = NewUserInfo.objects.get(student_id=user_id)
    ug = UserGrade.objects.filter(student_id=user_id)
    # 성적표 띄울땐 커스텀과 찐 성적 구분한다
    grade = ug.exclude(year='커스텀')
    custom_grade = ug.filter(year='커스텀')
    # 공학인증 없는학과 
    user_en = Standard.objects.get(user_dep=ui_row.major, user_year=ui_row.year).sum_eng
    # 공학인증 해당학과 아니라면
    if user_en == -1:
        is_engine = 0
    # 공학인증은 있는데 기준 아직 없다면
    elif user_en == 0:
        is_engine = 1
    else:
        is_engine = 2
    # 만약 성적표 업로드 안했다면
    is_grade = 1
    if not ug.exists():
        is_grade = 0

    mypage_context ={
        'student_id' : ui_row.student_id,
        'year' : ui_row.year,
        'major' : ui_row.major,
        'major_status' : ui_row.major_status,
        'name' : ui_row.name,
        'eng' : ui_row.eng,
        'grade' : list(grade.values()),
        'custom_grade' : list(custom_grade.values()),
        'is_grade' : is_grade,
        'is_engine' : is_engine,
    }

    # 고전독서인증 변환하기
    if ui_row.book == '고특통과':
        mypage_context['special_lec'] = '고전특강이수'
    else:
        mypage_context['W'] = ui_row.book[0]
        mypage_context['E'] = ui_row.book[1]
        mypage_context['EW'] = ui_row.book[2]
        mypage_context['S'] = ui_row.book[3]

    return mypage_context

def update_json(user_id):
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    # mypage json 업데이트
    mypage_context = f_mypage(user_id)
    ui_row.mypage_json = json.dumps(mypage_context)
    # 업로드된 이수표가 있을때만 
    if UserGrade.objects.filter(student_id=user_id).exists():
        # result json 업데이트
        result_context = f_result(user_id)
        ui_row.result_json = json.dumps(result_context)
        # en_result json 업데이트
        if mypage_context['is_engine'] == 2:
            en_result_context = f_en_result(user_id)
            ui_row.en_result_json = json.dumps(en_result_context)
    # 업데이트 시간 기록
    ui_row.last_update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ui_row.save()
    return

def f_mod_info_ms(request):
    user_id = request.session.get('id')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    ui_row.major = request.POST.get('major_select')
    ui_row.save()
    update_json(user_id)
    del request.session['temp_major_select']
    messages.success(request, '업데이트성공')
    return redirect('/mypage/') 

# 1. 내정보 수정
def f_mod_info(request):
    user_id = request.session.get('id')
    pw = request.POST.get('pw')
    # 대휴칼 셀레니움 돌리기(이름, 전공, 고독현황)
    temp_user_info = selenium_DHC(user_id, pw)
    # 예외처리
    if temp_user_info == 'err_auth':
        messages.error(request, '⚠️ 세종대학교 포털 ID/PW를 다시 확인하세요! (Caps Lock 확인)')
        return redirect('/mypage/')
    elif temp_user_info == 'err_enter_mybook':
        messages.error(request, '⚠️ 계약학과, 편입생, 재외국민전형 입학자는 회원가입이 불가능합니다.😥 \\n\\n ❓❓ 이에 해당하지 않는다면 세종포털사이트에서의 설정을 확인하세요.\\n https://portal.sejong.ac.kr 로그인 👉 정보수정 👉 개인정보수집동의 모두 동의')
        return redirect('/mypage/')
    elif temp_user_info == 'err_all':
        messages.error(request, '⛔ 대양휴머니티칼리지 로그인 중 예기치 못한 오류가 발생했습니다. 학교관련 포털이 다른 창에서 로그인되어 있다면 로그아웃 후 다시 시도하세요.')
        return redirect('/mypage/')
    # 기본 정보 -> 변수에 저장
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    year = user_id[:2]
    getted_major = temp_user_info['major']

    # ***********************************************************************************
    
    # getted_major = '회화과'
    # year = 20
    # ui_row.year = year
    # ui_row.save()
    
    # ***********************************************************************************

    # 받아온거에서 전공제외 항목들 쿼리셋에 저장
    ui_row.book = temp_user_info['book']
    ui_row.name = temp_user_info['name']
    
    # 전공이 학부로 뜨는 경우(1학년에 해당)
    if getted_major[-2:] == '학부':
        # 해당 학부의 학과를 모두 불러온 후 리스트에 저장
        md = MajorDepartment.objects.filter(department = getted_major)
        major_select = [row.major for row in md]
        # 예외처리 - 바뀐 학과/전공이 기준에 해당하는지 검사
        if not Standard.objects.filter(user_year = year, user_dep__in = major_select).exists():
            messages.error(request, '😢 아직 Please Graduate에서 변경된 '+ getted_major + '-' + year + '의 검사를 지원하지 않습니다.')
            return redirect('/mypage/')
        # 통과하면 저장 후 세션에 전공선택지 넣고 메시지로 선택창 띄워준다
        ui_row.save()
        request.session['temp_major_select'] = major_select
        messages.warning(request, '전공선택 창 띄우기')
        return redirect('/mypage/')
    # 학과/전공으로 뜨는 경우
    else:
        # 예외처리 - 바뀐 학과/전공이 기준에 해당하는지 검사
        if not Standard.objects.filter(user_year = year, user_dep = getted_major).exists():
            messages.error(request, '😢 아직 Please Graduate에서 변경된 '+ getted_major + '-' + year + '의 검사를 지원하지 않습니다.')
            return redirect('/mypage/')
        # 영어인증 면제학과로 변경시, user_info의 영어정보를 면제로 바꾼다
        user_standard_row = Standard.objects.get(user_year = year, user_dep = getted_major)
        english_standard = json.loads(user_standard_row.english)
        if not english_standard:
            ui_row.eng = '영어인증면제학과'
        # 면제학과에서 이수해야하는 학과로 전과했을때
        elif ui_row.eng  == '영어인증면제학과':
            ui_row.eng = '해당없음'
        # 유저정보 테이블에 저장
        ui_row.major = getted_major
        ui_row.save()
        # json DB도 업데이트
        update_json(user_id)
        messages.success(request, '업데이트성공')
        return redirect('/mypage/') 

# 2. 전공상태 + 영어인증 수정
def f_mod_ms_eng(request):
    # 세션id, 입력받은 값 꺼내기
    user_id = request.session.get('id')
    major_status = request.POST.get('major_status')
    eng = request.POST.get('eng')
    if eng == 'OPIc':
        eng = eng + '/' + request.POST.get('opic')
    elif eng not in ['해당없음', '초과학기면제', '영어인증면제학과']:
        eng = eng + '/' + str(request.POST.get('eng_score'))
    # 사용자의 user_info row 부르기
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    # 변경시에만 다시 저장
    if ui_row.eng != eng or ui_row.major_status != major_status:
        # 수정된 DB 넣고 save
        ui_row.eng = eng
        ui_row.major_status = major_status
        ui_row.save()
        # json DB도 업데이트
        update_json(user_id)
    messages.success(request, '업데이트성공')
    return redirect('/mypage/') 

# 3. 비밀번호 수정
def f_mod_pw(request):
    # 수정은 두가지 -> 로그인전과 로그인 후
    if request.session.get('id') != None:
        user_id = request.session.get('id')
    else:
        user_id = request.POST.get('id')
    # 암호화
    password = request.POST.get('password')
    password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())    
    password = password.decode('utf-8')                                     
    # 저장
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    ui_row.password = password
    ui_row.save()
    messages.success(request, '업데이트성공')
    if request.session.get('id') != None:
        return redirect('/mypage/')
    else:
        return redirect('/login/')

# 4. 기이수과목 수정
def f_mod_grade(request):
    # 넘겨받은 파일 꺼내기
    excel = request.FILES['excel']

    # 검사1 : 엑셀파일인지 검사
    if excel.name[-4:] != 'xlsx':
        messages.error(request, '⚠️ 잘못된 파일 형식입니다. 확장자가 xlsx인 파일을 올려주세요. ')
        return redirect('/mypage/')
    try:
        # 엑셀 파일을 수정해줘야함
        wb = openpyxl.load_workbook(excel)
        ws = wb.active
        # 1~4 행에서 컬럼명 행 빼고 삭제
        ws.delete_rows(1,2)
        ws.delete_rows(2)
        # 엑셀을 df로 변환
        df = pd.DataFrame(ws.values)
        # 첫 행을 컬럼으로 지정
        df.columns = df.iloc[0, :]
        df = df.iloc[1:, :]
        df = df.drop(['순번'], axis=1)
    except:
        messages.error(request, '⚠️ 엑셀 내용이 다릅니다! 수정하지 않은 엑셀파일을 올려주세요.')
        return redirect('/mypage/')

    # 검사2 : 형식에 맞는지 검사
    if list(df.columns) != ['년도', '학기', '학수번호', '교과목명', '이수구분', '교직영역', '선택영역', '학점', '평가방식', '등급', '평점', '개설학과코드']:
        messages.error(request, '⚠️ 엑셀 내용이 다릅니다! 수정하지 않은 엑셀파일을 올려주세요.')
        return redirect('/mypage/')
    # 검사를 통과하면 df를 형식에 맞게 수정
    df.fillna('', inplace = True)

    # F 나 NP 과목은 삭제함
    for i, row in df.iterrows():
        if row['등급'] in ['F', 'FA', 'NP']:
            df.drop(i, inplace=True)
            
    df.drop(['교직영역', '평가방식','등급', '평점', '개설학과코드'], axis=1, inplace=True)
    # 추가 전 user_grade DB에 이미 데이터가 있는지 확인 후 삭제
    user_id = request.session.get('id')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    ug = UserGrade.objects.filter(student_id = user_id)
    if ug.exists() : ug.delete()
    # DF를 테이블에 추가
    for i, row in df.iterrows():
        new_ug = UserGrade()
        new_ug.student_id = user_id
        new_ug.major = ui_row.major
        new_ug.year = row['년도']
        new_ug.semester = row['학기']
        new_ug.subject_num = str(row['학수번호']).lstrip('0')
        new_ug.subject_name = row['교과목명']
        new_ug.classification = row['이수구분']
        new_ug.selection = row['선택영역']
        new_ug.grade = row['학점']
        new_ug.save()
    # json DB도 업데이트
    update_json(user_id)
    messages.success(request, '업데이트성공')
    
    return redirect('/mypage/')
    
# 회원 탈퇴
def f_delete_account(request):
    user_id = request.session.get('id')
    pw = request.POST.get('pw')
    # 해당 사용자의 DB 쿼리셋
    ui_row = NewUserInfo.objects.get(student_id=user_id)
    ug = UserGrade.objects.filter(student_id = user_id)
    # 비밀번호 일치 검사
    if not bcrypt.checkpw(pw.encode('utf-8'), ui_row.password.encode('utf-8')):
        messages.error(request, '⚠️ 비밀번호를 확인하세요.')
        return redirect('/mypage/')
    # 회원탈퇴 로그에 기록
    new_da = DeleteAccountLog()
    new_da.major = ui_row.major
    new_da.year = ui_row.year
    new_da.name = ui_row.name
    new_da.register_time = ui_row.register_time
    new_da.delete_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_da.save()
    # 데이터베이스 삭제
    ui_row.delete()
    ug.delete()
    return redirect('/success_delete/')


# ---------------------------------------------------- ( 커스텀 기능 ) ----------------------------------------------------------------

@csrf_exempt
def a_search(request):
    # AJAX 통신으로 넘어온 학수번호를 받는다
    s_num = request.POST['back_s_num']
    # 학수번호를 all_lecture 테이블에서 검색
    al = AllLecture.objects.filter(subject_num=s_num)
    # 존재한다면 
    if al.exists():
        result = al.values_list()[0]
    else:
        result = "검색실패"
    context = {
        'result' : result
    }
    return JsonResponse(context)

def f_add_custom(request):
    # 만약 삭제+추가 둘다 없다면 걍 종료
    if (not request.POST['arr_delete']) and (not request.POST['arr_year']):
        return redirect('/mypage/')
    # 아니라면 일단 정보 추출
    user_id = request.session.get('id')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    # 1. 예전 커스텀이 삭제되었을때 -> 사용자의 UG에서도 삭제해주자
    if request.POST['arr_delete']:
        del_ug = UserGrade.objects.filter(student_id=user_id, subject_num__in = request.POST['arr_delete'].split(','))
        del_ug.delete()
    # 2. 추가된게 있을 경우
    if request.POST['arr_year']:
        # POST로 싹다 받아옴
        year = request.POST['arr_year'].split(',')
        semester = request.POST['arr_semester'].split(',')
        subject_num = request.POST['arr_subject_num'].split(',')
        subject_name = request.POST['arr_subject_name'].split(',')
        classification = request.POST['arr_classification'].split(',')
        selection = request.POST['arr_selection'].split(',')
        grade = request.POST['arr_grade'].split(',')
        # 커스텀 과목을 한행씩 UserGrade 테이블에 추가
        for row in zip(year, semester, subject_num, subject_name, classification, selection, grade):
            new_ug = UserGrade()
            new_ug.student_id = user_id
            new_ug.major = ui_row.major
            new_ug.year = row[0]
            new_ug.semester = row[1]
            new_ug.subject_num = row[2]
            new_ug.subject_name = row[3]
            new_ug.classification = row[4]
            new_ug.selection = row[5]
            new_ug.grade = row[6]
            new_ug.save()
    # 3. 모든 변경 후 정보변경 + 재검사
    update_json(user_id)
    messages.success(request, '업데이트성공')
    return redirect('/mypage/')

# ---------------------------------------------------- ( 셀레니움 파트 ) ----------------------------------------------------------------

def selenium_DHC(id, pw):
    # 대양휴머니티칼리지 url
    url = 'https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=classic.sejong.ac.kr/ssoLogin.do'
    # 옵션 넣고 드라이버 생성
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # 로컬 - 개발용 -------------------------------------------------------------------------------
    if platform.system() == 'Windows':
        # 크롬 드라이버 열기
        driver = webdriver.Chrome('./chromedriver.exe', options=options)
        driver.get(url)
        # 키보드보안 해제
        driver.find_element_by_xpath('//*[@id="login_form"]/div[2]/div/div[2]/div[3]/label/span').click()
        driver.switch_to_alert().dismiss()
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

    # 서버 - 배포용 -------------------------------------------------------------------------------
    else:
        try:
            # 가상 디스플레이를 활용해 실행속도 단축
            display = Display(visible=0, size=(1024, 768))
            display.start()
            # 크롬드라이버 열기
            driver = webdriver.Chrome('/home/ubuntu/Downloads/chromedriver', options=options)
            driver.get(url)
            # 키보드보안 해제
            driver.find_element_by_xpath('//*[@id="login_form"]/div[2]/div/div[2]/div[3]/label/span').click()
            driver.switch_to_alert().dismiss()
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
        except:
            # 드라이버랑 가상디스플레이 안꺼졌으면 끄기
            if 'driver' in locals():
                driver.quit()
            if 'display' in locals():
                display.stop()
            return 'err_all'

    # 크롤링으로 받아온 값 리턴
    context = {
        'name' : name,
        'major' : major,
        'book' : book,
    }
    return context

# ---------------------------------------------------- ( 회원가입 파트 ) ----------------------------------------------------------------

def f_certify(request):
    # 입력받은 id/pw을 꺼낸다.
    id = request.POST.get('id')
    pw = request.POST.get('pw')
    year = id[:2]

    # 학번 중복 검사
    if NewUserInfo.objects.filter(student_id=id).exists():
        messages.error(request, '⚠️ 이미 가입된 학번입니다!')
        return redirect('/agree/')

    # 대휴칼 셀레니움 돌리기
    temp_user_info = selenium_DHC(id, pw)

    # 예외처리
    if temp_user_info == 'err_auth':
        messages.error(request, '⚠️ 세종대학교 포털 ID/PW를 다시 확인하세요! (Caps Lock 확인)')
        return redirect('/agree/')
    elif temp_user_info == 'err_enter_mybook':
        messages.error(request, '⚠️ 계약학과, 편입생, 재외국민전형 입학자는 회원가입이 불가능합니다.😥 \\n\\n ❓❓ 이에 해당하지 않는다면 세종포털사이트에서의 설정을 확인하세요.\\n https://portal.sejong.ac.kr 로그인 👉 정보수정 👉 개인정보수집동의 모두 동의')
        return redirect('/agree/')
    elif temp_user_info == 'err_all':
        messages.error(request, '⛔ 대양휴머니티칼리지 로그인 중 예기치 못한 오류가 발생했습니다. 학교관련 포털이 다른 창에서 로그인되어 있다면 로그아웃 후 다시 시도하세요.')
        return redirect('/agree/')

# ***********************************************************************************
    
    # temp_user_info['major'] = '호텔외식관광프랜차이즈경영학과'
    # year = 21
    
# ***********************************************************************************

    major_select = []
    # 학부로 뜨는 경우(1학년에 해당)
    if temp_user_info['major'][-2:] == '학부':
        # 해당 학부의 학과를 모두 불러온 후 리스트에 저장
        md = MajorDepartment.objects.filter(department = temp_user_info['major'])
        for m in md:
            major_select.append(m.major)
        # 예외처리 - 로그인한 사용자의 학과-학번이 기준에 있는지 검사 
        if not Standard.objects.filter(user_year = year, user_dep__in = major_select).exists():
            messages.error(request, '😢 아직 Please Graduate에서 해당 학과-학번 검사를 지원하지 않습니다.')
            return redirect('/agree/')
    # 학과 or 전공으로 뜨는 경우
    else:
        # 예외처리
        if not Standard.objects.filter(user_year = year, user_dep = temp_user_info['major']).exists():
            messages.error(request, '😢 아직 Please Graduate에서 해당 학과-학번 검사를 지원하지 않습니다.')
            return redirect('/agree/')

    # 예체능대/호경특정학과 는 영어인증 면제 / (학부소속에선 면제 없음)``
    is_exempt_english = 0
    if not major_select:
        user_standard_row = Standard.objects.get(user_year = year, user_dep = temp_user_info['major'])
        english_standard = json.loads(user_standard_row.english)
        if not english_standard:
            is_exempt_english = 1
    temp_user_info['is_exempt_english'] = is_exempt_english
    
    # 나머지 데이터도 추가해주기    
    temp_user_info['id'] = id
    temp_user_info['year'] = year
    temp_user_info['major_select'] = major_select
    # 세션에 저장
    request.session['temp_user_info'] = temp_user_info
    return redirect('/register/')

def f_register(request):
    # 1. 세션에 있는것부터 꺼내자
    temp_user_info = request.session.get('temp_user_info')
    student_id = temp_user_info['id']
    year = temp_user_info['year']
    name = temp_user_info['name']
    book = temp_user_info['book']
    
    # 2. post로 받은것 꺼내기
    major_status = request.POST.get('major_status')

    # 비밀번호를 DB에 저장하기 전 암호화
    password = request.POST.get('password')
    password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())    # 인코딩 + 솔팅 + 해싱 -> 암호화
    password = password.decode('utf-8')                                     # 저장전 디코딩
    
    # 만약 학부생일 경우 전공을 선택한것으로 저장
    if request.POST.get('major_select') : 
        major = request.POST.get('major_select')
    # 선택지가 아예없었다면 그냥 세션 전공 저장
    else : 
        major = temp_user_info['major']

    # 만약 영어 점수 썼다면 ex) 'toeic/550' <- 이런형태로 저장됨.
    eng = request.POST.get('eng')
    if eng == 'OPIc':
        eng = eng + '/' + request.POST.get('opic')
    elif eng not in ['해당없음', '초과학기면제', '영어인증면제학과']:
        eng = eng + '/' + str(request.POST.get('eng_score'))

    # 가입시간을 저장
    register_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 테스트 user_info 테이블에 데이터 입력
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

    return redirect('/success/')

# ---------------------------------------------------- ( 검사 알고리즘 함수 ) ----------------------------------------------------------------

def to_zip_list(list_1, list_2):
    zip_list = []
    for a, b in zip(list_1, list_2):
        zip_list.append([a,b])
    return zip_list

def list_to_query(list_):
    al = AllLecture.objects.filter(subject_num__in=list_)
    return list(al.values())

def make_dic(my_list):
    my_list.sort()
    dic = defaultdict(lambda:-1)
    for s_num in my_list:
        dic[s_num]
        # 필수과목의 동일과목은 sg 테이블에서 1:1로만 담겨잇어야함.
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
        # 없다면? 2차 검사 (사용자가 새 과목으로 재수강했을 경우)
        else :
            # 내 과목 리스트에서 그룹번호를 꺼냄
            g_num = my_dic_[s_num]
            # 기준 과목 리스트에서 그룹번호가 같은게 있으면 학수를 동일과목으로 바꿈
            for k, v in dic_.items():
                if v == g_num :
                    s_num = k
            # 해당 그룹번호가 기준에도 있다면 
            if g_num != -1 and (g_num in dic_.values()):
                check[s_num] = 1
                dic_.pop(s_num)
    # 추천 리스트 알고리즘
    recommend = []
    for s_num in dic_.keys():
        nl = NewLecture.objects.filter(subject_num = s_num)
        # 부족 과목이 열리고 있다면
        if nl.exists():
            recommend.append(nl[0].subject_num)
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
                        recommend.append(nl2[0].subject_num)
    return recommend, list(check.values())

def add_same_lecture(list_):
    for s_num in list_:
        sg = SubjectGroup.objects.filter(subject_num = s_num)
        for s in sg:
            rows = SubjectGroup.objects.filter(group_num = s.group_num)
            for r in rows:
                if r.subject_num not in list_:
                    list_.append(r.subject_num)
    return list_

def make_recommend_list_other(other_, user_lec_list):
    # 쿼리셋을 리스트로 변환 -> 등장횟수에 따라 내림차순 정렬 
    other_ = sorted(list(other_), key = lambda x : x[1], reverse=True)
    # 10개만 추천하기 + 내가 들었던 과목은 제외하기
    recom = []
    rank = 0
    for s_num, num in other_:
        if len(recom) >= 10:
            break
        # 뉴렉쳐에 있는 최신 학수번호 + 내가 안들은것만 담기 + 과목정보 - 등장횟수 순위 묶어서 저장
        if NewLecture.objects.filter(subject_num=s_num).exists() and (s_num not in user_lec_list):
            # AllLecture에서 이수구분이 교선일때만 리스트에 추가함
            if AllLecture.objects.filter(subject_num = s_num, classification__in = ['전필', '전선', '교선1']).exists():
                rank += 1
                row_dic = list(AllLecture.objects.filter(subject_num = s_num).values())
                recom.append( [row_dic[0], rank] )
    # 학수번호 -> 쿼리셋 -> 모든 정보 리스트로 변환 후 리턴
    return recom

def convert_to_int(num):
    if str(num)[-1] == '0':
        num = int(num)
    return num

# ---------------------------------------------------- (졸업요건 검사 파트) ----------------------------------------------------------------

def f_result(user_id):
    # userinfo 테이블에서 행 추출
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    # user_grade 테이블에서 사용자의 성적표를 DF로 변환하기
    user_qs = UserGrade.objects.filter(student_id = user_id)
    data = read_frame(user_qs, fieldnames=['subject_num', 'subject_name', 'classification', 'selection', 'grade'])
    data.rename(columns = {'subject_num' : '학수번호', 'subject_name' : '교과목명', 'classification' : '이수구분', 'selection' : '선택영역', 'grade' : '학점'}, inplace = True)
    # 사용자에게 맞는 기준 row 뽑아내기
    standard_row = Standard.objects.get(user_dep = ui_row.major, user_year = ui_row.year)

    # 아래 로직을 거치며 채워질 데이터바인딩용 context 선언
    result_context = {}     

    ####################################################
    ################### 예외처리 여부 ###################
    ####################################################
    # 교필, 교선, 기교, 복전, 영어 여부 판단
    ce_exists, cs_exists, b_exists, multi_exists, english_exists = 0, 0, 0, 0, 0
    if standard_row.core_essential:
        ce_exists = 1
    if standard_row.core_selection:
        cs_exists = 1
    if standard_row.basic:
        b_exists = 1 
    if ui_row.major_status != '해당없음':
        multi_exists = 1 
    if json.loads(standard_row.english):
        english_exists = 1
    context_exists = {
        'ce' : ce_exists,
        'cs' : cs_exists,
        'b' : b_exists,
        'english' : english_exists,
        'multi' : multi_exists,
    }
    result_context['exists'] = context_exists
        

    ###################################################
    ################### 사용자 정보 ###################
    ###################################################
    context_user_info = {
        'id' : ui_row.student_id,
        'name' : ui_row.name,
        'major' : ui_row.major,
        'year' : ui_row.year,
    }
    result_context['user_info'] = context_user_info


    ####################################################
    ################### 고전독서 영역 ###################
    ####################################################
    pass_book = 0
    if ui_row.book == '고특통과': 
        pass_book = 2
        context_book = {
            'pass' : pass_book
        }
    else:
        W, E, EW, S = int(ui_row.book[0]), int(ui_row.book[1]), int(ui_row.book[2]), int(ui_row.book[3])
        total_book = 0
        if W > 4: 
            total_book += 4
        else : 
            total_book += W
        if E > 2: 
            total_book += 2
        else : 
            total_book += E
        if EW > 3: 
            total_book += 3
        else : 
            total_book += EW
        if S > 1: 
            total_book += 1
        else : 
            total_book += S
        if total_book == 10:
            pass_book = 1
        context_book = {
            'W' : W,
            'E' : E,
            'EW' : EW,
            'S' : S,
            'total' : total_book,
            'pass' : pass_book
        }
    result_context['book'] = context_book
    
    ################################################
    ################### 전공 공통 ###################
    ################################################
    # 사용자의 성적표에서 전필, 전선 추출
    df_me = data[data['이수구분'].isin(['전필'])]
    df_me.reset_index(inplace=True,drop=True)
    df_ms = data[data['이수구분'].isin(['전선'])]
    df_ms.reset_index(inplace=True,drop=True)
    # 전필 기준에서 초과된 학점 계산
    remain = 0
    if standard_row.major_essential < df_me['학점'].sum() :
        remain = df_me['학점'].sum() - standard_row.major_essential
    # 내가들은 전필 + 전선의 동일과목 학수번호 추가한 리스트
    user_major_lec = add_same_lecture(df_ms['학수번호'].tolist() + df_me['학수번호'].tolist())

    ################################################
    ################### 전필 영역 ###################
    ################################################
    # 기준학점 & 사용자 학점 추출
    standard_num_me = standard_row.major_essential
    user_num_me = df_me['학점'].sum() - remain
    lack_me = standard_num_me - user_num_me
    # 선택추천과목 리스트 생성
    other_me = UserGrade.objects.exclude(year = '커스텀').filter(major = ui_row.major, classification = '전필').values_list('subject_num').annotate(count=Count('subject_num'))
    recom_selection_me = make_recommend_list_other(other_me, user_major_lec)
    # 패스여부 검사
    pass_me = 0
    if standard_num_me <= user_num_me:
        pass_me = 1
    # context 생성
    context_major_essential = {
        'standard_num' : standard_num_me,
        'user_num' : convert_to_int(user_num_me),
        'lack' : convert_to_int(lack_me),
        'recom_selection' : recom_selection_me,
        'pass' : pass_me,
    }
    result_context['major_essential'] = context_major_essential


    ################################################
    ################### 전선 영역 ###################
    ################################################
    # 기준학점 & 사용자학점합계 추출
    standard_num_ms = standard_row.major_selection
    user_num_ms = df_ms['학점'].sum()
    lack_ms = standard_num_ms - user_num_ms - remain
    # 선택추천과목 리스트 생성
    other_ms = UserGrade.objects.exclude(year = '커스텀').filter(major = ui_row.major, classification = '전선').values_list('subject_num').annotate(count=Count('subject_num'))
    recom_selection_ms = make_recommend_list_other(other_ms, user_major_lec)
    # 패스여부 검사
    pass_ms = 0
    if standard_num_ms <= user_num_ms + remain:
        pass_ms = 1
    # context 생성
    context_major_selection = {
        'standard_num' : standard_num_ms,
        'user_num' : convert_to_int(user_num_ms),
        'remain' : convert_to_int(remain),
        'lack' : convert_to_int(lack_ms),
        'recom_selection' : recom_selection_ms,
        'pass' : pass_ms,
    }
    result_context['major_selection'] = context_major_selection


    ################################################
    ################### 교필 영역 ###################
    ################################################
    if ce_exists :
        # 성적표에서 교필 추출
        df_ce = data[data['이수구분'].isin(['교필', '중필'])]
        df_ce.reset_index(inplace=True,drop=True)
        # 기준학점 & 사용자학점합계 추출
        standard_num_ce = standard_row.core_essential
        user_num_ce = df_ce['학점'].sum()
        # 기준필수과목 & 사용자교필과목 추출 => 동일과목 매핑 dict 생성
        dic_ce = make_dic([s_num for s_num in standard_row.ce_list.split('/')])
        user_dic_ce = make_dic(data['학수번호'].tolist())  # * 수정 : 교필, 중필 영역만 비교하지 않고 전체를 대상으로 비교
        # 기준필수과목+체크 & 추천과목 리스트 생성
        recom_essential_ce, check_ce = make_recommend_list(user_dic_ce, dic_ce)
        standard_essential_ce = to_zip_list(list_to_query(dic_ce.keys()), check_ce)
        # 패스여부 검사
        pass_ce = 0
        if not recom_essential_ce :
            pass_ce = 1
        # context 생성
        context_core_essential = {
            'standard_num' : standard_num_ce,
            'user_num' : convert_to_int(user_num_ce),
            'recom_essential' : list_to_query(recom_essential_ce),
            'standard_essential' : standard_essential_ce,
            'pass' : pass_ce,
        }
        result_context['core_essential'] = context_core_essential


    ################################################
    ################### 교선 영역 ###################
    ################################################
    if cs_exists :
        # 성적표에서 고선 추출
        df_cs = data[data['이수구분'].isin(['교선1', '중선'])]
        df_cs.reset_index(inplace=True,drop=True)
        # 기준학점 & 사용자학점합계 추출
        standard_num_cs = standard_row.core_selection
        user_num_cs = df_cs['학점'].sum()
        # 기준필수과목 & 사용자과목 추출 => 동일과목 매핑 dict 생성
        dic_cs = make_dic([s_num for s_num in standard_row.cs_list.split('/')])
        user_dic_cs = make_dic(df_cs['학수번호'].tolist())
        # 기준필수과목+체크 & 추천과목 리스트 생성
        recom_essential_cs, check_cs = make_recommend_list(user_dic_cs, dic_cs)
        standard_essential_cs = to_zip_list(list_to_query(dic_cs.keys()), check_cs)
        # 16 17의 소기코 대체과목은 컴기코로 바꿔줌
        if ui_row.year in [16, 17] and '9799' in recom_essential_cs:
            # 일단 추천리스트에서 소기코는 삭제하고
            recom_essential_cs.remove('9799')
            # 만약 컴기코를 재수강 했다면 기준 딕셔너리에서 수강 체크해준다
            if '10528' in user_dic_cs.keys():
                for i, zipped in enumerate(standard_essential_cs):
                    if zipped[0]['subject_num'] == '9799':
                        standard_essential_cs[i][1] = 1
            # 재수강 안했으면 추천리스트에 컴기코 학수번호 추가
            else:
                recom_essential_cs.append('10528')

        # 선택영역 검사
        standard_cs_part =["사상과역사","사회와문화","융합과창업","자연과과학기술","세계와지구촌"]   # 기준 영역 5개
        user_cs_part = list(set(df_cs[df_cs['선택영역'].isin(standard_cs_part)]['선택영역'].tolist()))
        # 사용자가 안들은 영역 추출
        recom_cs_part = []
        if len(user_cs_part) < 3:
            recom_cs_part = list(set(standard_cs_part) - set(user_cs_part))
        # 사용자의 부족 영역 체크
        part_check = ['이수' for _ in range(5)]
        for i, c in enumerate(standard_cs_part):
            if c not in user_cs_part:
                part_check[i] = '미이수'

        # 선택추천과목 리스트 생성
        user_cs_lec = df_cs['학수번호'].tolist() + [s_num for s_num in standard_row.cs_list.split('/')]
        if not recom_cs_part :  # 만족한경우엔 5개 다 추천
            cs_part_for_recom = standard_cs_part
        else:                   # 만족 못했으면 영역 recom 리스트 그대로
            cs_part_for_recom = recom_cs_part
        other_cs = UserGrade.objects.exclude(year = '커스텀').filter(classification__in = ['교선1', '중선'],  selection__in=cs_part_for_recom)
        other_cs = other_cs.values_list('subject_num').annotate(count=Count('subject_num'))
        recom_selection_cs = make_recommend_list_other(other_cs, user_cs_lec)
        # 패스여부 검사 (선택영역, 기준학점, 필수과목, 전체)
        pass_cs_part, pass_cs_num, pass_cs_ess, pass_cs= 0, 0, 0, 0
        if not recom_cs_part:
            pass_cs_part = 1
        if standard_num_cs <= user_num_cs:
            pass_cs_num = 1
        if not recom_essential_cs:
            pass_cs_ess = 1
        if pass_cs_part and pass_cs_num and pass_cs_ess:
            pass_cs = 1

        # context 생성
        context_core_selection = {
            'standard_num' : standard_num_cs,
            'user_num' : convert_to_int(user_num_cs),
            'recom_essential' : list_to_query(recom_essential_cs),
            'standard_essential' : standard_essential_cs,
            'recom_selection' : recom_selection_cs,
            'standard_cs_part' : standard_cs_part,
            'part_check' : part_check,
            'pass_part' : pass_cs_part,
            'pass_ess' : pass_cs_ess,
            'pass' : pass_cs,
        }
        result_context['core_selection'] = context_core_selection


    ################################################
    ################### 기교 영역 ###################
    ################################################
    if b_exists :
        # 성적표에서 기교 추출
        df_b = data[data['이수구분'].isin(['기교'])]
        df_b.reset_index(inplace=True,drop=True)
        # 기준학점 & 사용자학점합계 추출
        standard_num_b = standard_row.basic
        user_num_b = df_b['학점'].sum()
        # 기준필수과목 & 사용자교필과목 추출 => 동일과목 매핑 dict 생성
        dic_b = make_dic([s_num for s_num in standard_row.b_list.split('/')])
        user_dic_b = make_dic(data['학수번호'].tolist())     # * 수정 : 기교 영역만 비교하지 않고 전체를 대상으로 비교
        # 기준필수과목+체크 & 추천과목 리스트 생성
        recom_essential_b, check_b = make_recommend_list(user_dic_b, dic_b)
        standard_essential_b = to_zip_list(list_to_query(dic_b.keys()), check_b)
        # 패스여부 검사
        pass_b = 0
        if not recom_essential_b :
            pass_b = 1
        # context 생성
        context_basic = {
            'standard_num' : standard_num_b,
            'user_num' : convert_to_int(user_num_b),
            'recom_essential' : list_to_query(recom_essential_b),
            'standard_essential' : standard_essential_b,
            'pass' : pass_b,
        }

        # 화학과 기교에서는 조건이 추가된다.
        if ui_row.major == '화학과':
            pass_chemy_all = pass_b
            chemy_B_exists = 0
            # 기교 -> 선택과목 기준 설정
            if ui_row.year >= 19:
                data_chemy_A = ['2657', '3353']             # 일생 / 통계
                data_chemy_B = []
            elif ui_row.year >= 16:
                data_chemy_A = ['2647', '2657']             # 일물실1 / 일생
                data_chemy_B = ['2649', '2657', '3353']     # 일물실2 / 일생 / 통계
            else:
                data_chemy_A = ['4082', '2647', '2657']     # 고미적1 / 일물실1 / 일생
                data_chemy_B = ['4300', '2649']             # 고미적 2 / 일물실2

            dic_chemy_A = make_dic(data_chemy_A)
            recom_chemy_A, check_chemy_A = make_recommend_list(user_dic_b, dic_chemy_A)
            standard_chemy_A = to_zip_list(list_to_query(dic_chemy_A.keys()), check_chemy_A)
            pass_chemy_A = 0
            if 1 in check_chemy_A:
                pass_chemy_A = 1
            else:
                pass_chemy_all = 0
                context_basic['recom_chemy_A'] = list_to_query(recom_chemy_A)
            context_basic['standard_chemy_A'] = standard_chemy_A
            context_basic['pass_chemy_A'] = pass_chemy_A
                
            if data_chemy_B:
                chemy_B_exists = 1
                dic_chemy_B = make_dic(data_chemy_B)
                recom_chemy_B, check_chemy_B = make_recommend_list(user_dic_b, dic_chemy_B)
                standard_chemy_B = to_zip_list(list_to_query(dic_chemy_B.keys()), check_chemy_B)
                pass_chemy_B = 0
                if 1 in check_chemy_B:
                    pass_chemy_B = 1
                else:
                    pass_chemy_all = 0
                    context_basic['recom_chemy_B'] =list_to_query(recom_chemy_B)
                context_basic['standard_chemy_B'] = standard_chemy_B
                context_basic['pass_chemy_B'] = pass_chemy_B
            context_basic['chemy_B_exists'] = chemy_B_exists
            context_basic['pass_chemy_all'] = pass_chemy_all
        result_context['basic'] = context_basic


    ################################################
    ################### 영어 영역 ###################
    ################################################
    if english_exists:
        # 영어합격기준 (영문과만 예외처리)
        eng_standard = json.loads(standard_row.english)
        # 영어 인증 여부
        eng_pass, eng_score = 0, 0
        eng_category = ui_row.eng
        # 인텐시브 들었다면 통과
        if '6844' in data['학수번호'].tolist():
            eng_category = 'Intensive English 이수'
            eng_pass = 1
        else:
            if eng_category != '해당없음':
                if eng_category == '초과학기면제': 
                    eng_pass = 1
                # 영어 점수 기재했을 경우
                else: 
                    eng_category, eng_score = eng_category.split('/')
                    # OPIc일 경우
                    if eng_category == 'OPIc':
                        # 영어영문은 기준이 더 높다
                        if ui_row.major == '영어영문학전공':
                            opic_standard = ['AL', 'IH', 'IM']
                        else:
                            opic_standard = ['AL', 'IH', 'IM', 'IL']
                        if eng_score in opic_standard:
                            eng_pass = 1
                    elif int(eng_score) >= eng_standard[eng_category] :
                        eng_pass = 1
        context_english = {
            'standard' : eng_standard,
            'category' : eng_category,
            'score' : eng_score,
            'pass' : eng_pass,
        }
        result_context['english'] = context_english


    #####################################################
    ################### 복수/연계 전공 ###################
    #####################################################
    # 복수/연계 전공시 -> 전필,전선 : 기준 수정 + 복필(연필),복선(연선) : 기준과 내 학점계산 추가
    if multi_exists:
        result_context['user_info']['major_status'] = ui_row.major_status
        new_standard_me = 15
        new_standard_ms = 24
        standard_multi_me = 15
        standard_multi_ms = 24
        # 전공 기준 학점 수정
        result_context['major_essential']['standard_num'] = new_standard_me
        result_context['major_selection']['standard_num'] = new_standard_ms
        # 전필 -> 전선 넘기기 연산 다시하기
        remain = 0
        if new_standard_me < df_me['학점'].sum() :
            remain = df_me['학점'].sum() - new_standard_me
        result_context['major_essential']['user_num'] = convert_to_int(df_me['학점'].sum() - remain)
        result_context['major_selection']['remain'] = convert_to_int(remain)
        result_context['major_selection']['user_num'] = convert_to_int(user_num_ms)
        # 전공 패스여부 다시 검사
        pass_me, pass_ms = 0,0
        if new_standard_me <= user_num_me: 
            pass_me = 1
        if new_standard_ms <= user_num_ms + remain: 
            pass_ms = 1
        result_context['major_essential']['pass'] = pass_me
        result_context['major_selection']['pass'] = pass_ms
        # 전공 부족학점 다시 계산
        result_context['major_essential']['lack'] = convert_to_int(new_standard_me - user_num_me)
        result_context['major_selection']['lack'] = convert_to_int(new_standard_ms - user_num_ms - remain)

        # 복수/연계 전공 이수구분 설정
        if ui_row.major_status == '복수전공':
            classification_me = '복필'
            classification_ms = '복선'
        elif ui_row.major_status == '연계전공':
            classification_me = '연필'
            classification_ms = '연선'
        # 각각 X필, X선 학점 계산
        user_multi_me = data[data['이수구분'].isin([classification_me])]['학점'].sum()
        multi_remain = 0    # X필 초과시 X선으로 넘어가는 학점
        if standard_multi_me < user_multi_me :
            multi_remain = user_multi_me - standard_multi_me
        user_multi_me -= multi_remain
        user_multi_ms = data[data['이수구분'].isin([classification_ms])]['학점'].sum()
        # 복수/연계전공 pass 여부 검사
        pass_multi_me, pass_multi_ms = 0, 0
        if standard_multi_me <= user_multi_me:
            pass_multi_me = 1
        if standard_multi_ms <= user_multi_ms + multi_remain:
            pass_multi_ms = 1
        # 복수/연계 전공 context 생성
        context_multi_major_essential = {
            'standard_num' : standard_multi_me,
            'user_num' : convert_to_int(user_multi_me),
            'pass' : pass_multi_me,
        }
        context_multi_major_selection = {
            'standard_num' : standard_multi_ms,
            'user_num' : convert_to_int(user_multi_ms),
            'remain' : convert_to_int(multi_remain),
            'pass' : pass_multi_ms,
        }
        result_context['multi_major_essential'] = context_multi_major_essential
        result_context['multi_major_selection'] = context_multi_major_selection

    #############################################
    ################### Total ###################
    #############################################
    standard_num_total = standard_row.sum_score
    user_num_total = data['학점'].sum()
    # 총 기준 학점 넘기 + 모든 영역에서 pass 받으면 통과
    pass_total = 1
    if standard_num_total > user_num_total:
        pass_total = 0
    else:
        for key in result_context:
            try:
                if not result_context[key]['pass'] :
                    pass_total = 0
                    break
            except:
                pass
    # 화학과는 한번더 검사
    if ui_row.major == '화학과':
        if not result_context['basic']['pass_chemy_all']:
            pass_total = 0

    context_total = {
        'standard_num' : standard_num_total,
        'user_num' : convert_to_int(user_num_total),
        'pass' : pass_total,
    }
    result_context['total'] = context_total

    return result_context

    # @@@ result_context 구조 @@@
    # result_context = {
    #     'exists',
    #     'user_info',
    #     'book',
    #     'english',
    #     'major_essential',
    #     'major_selection',
    #     'core_essential',
    #     'core_selection',
    #     'basic',
    #     'multi_major_essential',
    #     'multi_major_selection',
    #     'total',
    # }
    

# ---------------------------------------------------- (공학인증 파트) ----------------------------------------------------------------

def f_en_result(user_id):
    # userinfo 테이블에서 행 추출
    ui_row = NewUserInfo.objects.get(student_id = user_id)

    user_info = {
        'id' : ui_row.student_id,
        'name' : ui_row.name,
    }

    # 기준 뽑아내기
    s_row = Standard.objects.get(user_dep = ui_row.major, user_year=ui_row.year)

    # df 생성
    # user_grade 테이블에서 사용자의 성적표를 DF로 변환하기
    user_qs = UserGrade.objects.filter(student_id = user_id)
    data = read_frame(user_qs, fieldnames=['year', 'semester', 'subject_num', 'grade'])
    data.rename(columns = {'year' : '년도', 'semester' : '학기', 'subject_num' : '학수번호', 'grade' : '학점'}, inplace = True)

    # 사용자가 들은 과목리스트 전부를 딕셔너리로.
    my_engine_admit = make_dic(data['학수번호'].tolist())

    # 1.전문 교양
    dic_pro = make_dic([s_num for s_num in s_row.pro_ess_list.split('/')])
    recom_pro, check_pro = make_recommend_list(my_engine_admit, dic_pro)
    mynum_pro = data[data['학수번호'].isin(dic_pro.keys())]['학점'].sum()

    # 2. bsm 필수
    dic_bsm_ess = make_dic([s_num for s_num in s_row.bsm_ess_list.split('/')])
    recom_bsm_ess, check_bsm_ess = make_recommend_list(my_engine_admit, dic_bsm_ess)
    mynum_bsm_ess = data[data['학수번호'].isin(dic_bsm_ess.keys())]['학점'].sum()

    # 3. bsm 선택 (16학번일때만 해당)
    if s_row.bsm_sel_list:
        dic_bsm_sel = make_dic([s_num for s_num in s_row.bsm_sel_list.split('/')])
        mynum_bsm_ess += data[data['학수번호'].isin(dic_bsm_sel.keys())]['학점'].sum()  # bsm 선택 이수학점을 더한다.

    # 4. 전공 영역
    # 4-1. 전공 전체 학점
    dic_eng_major = make_dic([s_num for s_num in s_row.eng_major_list.split('/')])
    recom_eng_major, check_eng_major =make_recommend_list(my_engine_admit,dic_eng_major)
    mynum_eng_major = data[data['학수번호'].isin(dic_eng_major.keys())]['학점'].sum()

    # int화
    df_e = data[data['학수번호'] == s_row.build_start ]
    if not df_e.empty:
        num_df_e = df_e['년도'].sum()
        num_df_2 = int(df_e['학기'].sum().replace('학기', ''))
    df_e2 = data[data['학수번호'] == s_row.build_end]
    num_df_e2 = df_e2['년도'].sum()

    # 기초설계 ~ 종합설계 사이의 DF 추출
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

    # 4-2. 기초설계 추천 뽑아내기
    dic_build_start = make_dic([s_row.build_start])
    recom_build_start, check_build_start = make_recommend_list(my_engine_admit2, dic_build_start)

    # 4-3. 종합설계 추천 뽑아내기
    dic_build_end = make_dic([s_row.build_end])
    recom_build_end, check_build_end = make_recommend_list(my_engine_admit2, dic_build_end)

    # 4-4. 요소설계 과목중 안들은 리스트
    dic_build_sel = make_dic([s_num for s_num in s_row.build_sel_list.split('/')])
    recom_build_sel, check_build_sel = make_recommend_list(my_engine_admit2, dic_build_sel)

    standard_num ={
        'total' : s_row.sum_eng,                # 공학인증 총학점 기준 
        'pro' : s_row.pro,                      # 전문교양 기준 학점
        'bsm' : s_row.bsm,                      # bsm 기준 학점
        'eng_major' : s_row.eng_major,          # 설계과목 기준학점
        'build_sel_num' : s_row.build_sel_num,  # 들어야되는 요소설계 과목수
    }

    # df는 int64이므로 -> int 로 변경해준다. (세션에 넣을때 int만 들어감)
    my_num = {
        'total' : int(mynum_pro+mynum_eng_major+mynum_bsm_ess),              
        'pro' : int(mynum_pro),
        'bsm' : int(mynum_bsm_ess),        
        'eng_major' : int(mynum_eng_major),
    }

    standard_list = {
        'pro' : to_zip_list(list_to_query(dic_pro.keys()),check_pro),
        'bsm_ess' : to_zip_list(list_to_query(dic_bsm_ess.keys()), check_bsm_ess),
        'bsm_sel' : [],
        'build_start' : to_zip_list(list_to_query(dic_build_start.keys()),check_build_start),
        'build_end' : to_zip_list(list_to_query(dic_build_end.keys()),check_build_end),
        'build_sel' : to_zip_list(list_to_query(dic_build_sel.keys()),check_build_sel),
    }

    # 전공영역 추천 과목 중 부족학점만큼 랜덤으로 골라주기
    n = standard_num['eng_major'] - my_num['eng_major']
    random.shuffle(recom_eng_major)
    recom_eng_major = recom_eng_major[:n//3+1]

    recommend = {
        'pro' : list_to_query(recom_pro),
        'bsm_ess' : list_to_query(recom_bsm_ess), # bsm 추천시 합쳐서 추천.
        'eng_major' : list_to_query(recom_eng_major),
    }

    # 필수과목 패스 여부
    pass_pro = 0
    pass_bsm_ess = 0
    pass_build_start = 0
    pass_build_end = 0
    pass_build_sel = 0
    if not recom_pro : pass_pro = 1                                         # 전문교양 여부
    if not recom_bsm_ess : pass_bsm_ess = 1                                 # bsm 여부
    if not recom_build_end : pass_build_end = 1                             # 종합설계 여부
    if sum(check_build_sel) >= s_row.build_sel_num : pass_build_sel = 1     # 선택설계 여부
    if not recom_build_start : pass_build_start = 1                         # 기초설계 여부
    else : pass_build_sel = -1

    pass_obj = {
        'pro' : pass_pro,
        'bsm_ess' : pass_bsm_ess,
        'build_start' : pass_build_start,
        'build_end' : pass_build_end,
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
    
    en_result_context={
        'user_info' : user_info,
        'standard_num' : standard_num,
        'my_num' : my_num,
        'standard_list' : standard_list,
        'recommend' : recommend,
        'pass_obj' : pass_obj,
    }
    return en_result_context

# ---------------------------------------------------------------------------------------------------------------------------------------















#  -------------------------------------------- (테스트 페이지 렌더링) ---------------------------------------------------------

def r_admin_test(request):
    # 로컬에서만 접근 가능하도록 하기
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')
    request.session.clear()
    uid = []
    for row in NewUserInfo.objects.all():
        uid.append([row.last_update_time, row.register_time, row.major, row.student_id, row.name])
    
    uid = sorted(uid, key= lambda x : x[1], reverse=True)

    context={
        'uid' : uid,
        'uid_num' : len(uid),
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
    password = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')   
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
    df_sem_1 = pd.read_excel(file_path + file_name, index_col=None)                             # 해당 엑셀을 DF화 시킴
    df_sem_1.drop([d for d in list(df_sem_1) if d not in need_col]  , axis=1, inplace=True)     # 필요한 컬럼만 추출
    # 2학기 엑셀 불러오기
    file_path = './app/update_lecture/2nd_semester/'
    file_name = os.listdir(file_path)[0]
    df_sem_2 = pd.read_excel(file_path + file_name, index_col=None)                             # 해당 엑셀을 DF화 시킴
    df_sem_2.drop([d for d in list(df_sem_2) if d not in need_col]  , axis=1, inplace=True)     # 필요한 컬럼만 추출

    # 두 df를 병합, 중복제거
    # ** 우선순위 학기의 df를 앞에다 두어야 함 **
    df_merge = pd.concat([df_sem_2, df_sem_1])
    df_merge.drop_duplicates(['학수번호'], inplace=True, ignore_index=True)
    # 선택영역 Nan을 바꾸기
    df_merge.fillna('', inplace = True)
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
    df_al.rename(columns = {'subject_num' : '학수번호', 'subject_name' : '교과목명', 'classification' : '이수구분', 'selection' : '선택영역', 'grade' : '학점'}, inplace = True)

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
    df_al.rename(columns = {'subject_num' : '학수번호', 'subject_name' : '교과목명', 'classification' : '이수구분', 'selection' : '선택영역', 'grade' : '학점'}, inplace = True)
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
    # 로컬에서만 접근 가능하도록 하기
    if platform.system() != 'Windows':
        return HttpResponse('관리자 페이지엔 접근할 수 없습니다!')

    # 엑셀 불러오기
    file_path = './app/update_lecture/input_standard/'
    file_name = os.listdir(file_path)[0]
    df = pd.read_excel(file_path + file_name, index_col=None)
    df.fillna(0, inplace = True)
    
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
    for major in user_major :
        if major in all_major:
            all_major.remove(major)
    print(' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 아직 가입 안한 학과 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ')
    print()
    print(all_major)
    print()

    print(' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 학과별 회원수 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ')
    print()
    for row in sorted(NewUserInfo.objects.values_list('major').annotate(count=Count('major')), key = lambda x : x[1], reverse=True):
        print(row)
    print()

    print(' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 학번별 회원수 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ')
    print()
    for row in NewUserInfo.objects.values_list('year').annotate(count=Count('year')):
        print(row)
    print()

    
    return HttpResponse('테스트 완료, 터미널 확인')

