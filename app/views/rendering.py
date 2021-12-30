# 파이썬 라이브러리
import os
import json
import time
import datetime
import openpyxl
import pandas as pd
import platform
import random
import bcrypt
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display
from django_pandas.io import read_frame
# 장고 관련 참조
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
# 모델 참조
from django.db.models import Count, Sum
from ..models import *
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