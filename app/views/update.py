# 파이썬 라이브러리
import json
import openpyxl
import pandas as pd
import bcrypt
# 장고 관련 참조
from django.shortcuts import redirect
from django.contrib import messages
# 모델 참조
from ..models import *
from .auth import *


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
    temp_user_info = get_user_info(user_id, pw)
    # 예외처리
    if temp_user_info == 'err_auth':
        messages.error(request, '⚠️ 세종대학교 포털 ID/PW를 다시 확인하세요! (Caps Lock 확인) \\n\\n (재외국민전형 입학자는 업데이트가 불가능합니다.)')
        return redirect('/mypage/')
    elif temp_user_info == 'err_server':
        messages.error(request, '⛔ 대양휴머니티칼리지 로그인 중 예기치 못한 오류가 발생했습니다. 대양휴머니티칼리지 사이트의 서버 문제일 수 있으니 잠시 후 시도해주세요.')
        return redirect('/mypage/')
    # 기본 정보 -> 변수에 저장
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    year = user_id[:2]
    
    # 받아온거에서 전공제외 항목들 쿼리셋에 저장
    ui_row.book = temp_user_info['book']
    ui_row.name = temp_user_info['name']

    # ***********************************************************************************
    
    # temp_user_info['major'] = ""
    # year = 
    # ui_row.year = 
    # ui_row.save()
    
    # ***********************************************************************************

    # 검사 가능 학과 선별 로직
    input_major = temp_user_info['major']
    major_select = []

    # 세부전공
    major_qs = Major.objects.filter(sub_major = input_major)
    if major_qs.exists():
        ui_row.sub_major = input_major
        ui_row.major = major_qs[0].major
    else:
        # 전공/학과
        major_qs = Major.objects.filter(major = input_major)
        if major_qs.exists():
            ui_row.sub_major = None
            ui_row.major = major_qs[0].major
        else:
            # 학부
            major_qs = Major.objects.filter(department = input_major)
            if major_qs.exists():
                ui_row.sub_major = None
                for q in major_qs:
                    major_select.append(q.major)
            else:
                messages.error(request, '😢 아직 Please Graduate에서 ' + input_major + '-' + str(year) + '학번의 검사를 지원하지 않습니다.')
                return redirect('/mypage/') 

    # 예체능대학은 영어면제
    if major_qs[0].college == "예체능대학":
        ui_row.eng = '영어인증면제학과'
    else:
        ui_row.eng = '해당없음'

    # 예외처리
    if major_select :
        if not Standard.objects.filter(user_year = year, user_dep__in = major_select).exists():
            messages.error(request, '😢 아직 Please Graduate에서 ' + input_major + '-' + str(year) + '학번의 검사를 지원하지 않습니다.')
        else:
            # 통과하면 저장 후 세션에 전공선택지 넣고 메시지로 선택창 띄워준다
            ui_row.save()
            request.session['temp_major_select'] = major_select
            messages.warning(request, '전공선택 창 띄우기')
    else:
        if not Standard.objects.filter(user_year = year, user_dep = ui_row.major).exists():
            messages.error(request, '😢 아직 Please Graduate에서 ' + input_major + '-' + str(year) + '학번의 검사를 지원하지 않습니다.')
        else:
            # 유저정보 테이블에 저장 후 json DB도 업데이트
            ui_row.save()
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
    # 불필요 컬럼 삭제
    df.drop(['교직영역', '평가방식','등급', '평점', '개설학과코드'], axis=1, inplace=True)

    # 추가 전 user_grade DB에 이미 데이터가 있는지 확인 후 삭제
    user_id = request.session.get('id')
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    ug = UserGrade.objects.filter(student_id = user_id)
    if ug.exists() : ug.delete()

    # DF를 테이블에 추가
    for i, row in df.iterrows():
        # 저장
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