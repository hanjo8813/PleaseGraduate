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
    temp_user_info = selenium_DHC(user_id, pw)
    # 예외처리
    if temp_user_info == 'err_auth':
        messages.error(request, '⚠️ 세종대학교 포털 ID/PW를 다시 확인하세요! (Caps Lock 확인)')
        return redirect('/mypage/')
    elif temp_user_info == 'err_enter_mybook':
        messages.error(request, '⚠️ 계약학과, 편입생, 재외국민전형 입학자는 회원가입이 불가능합니다.😥 \\n\\n ❓❓ 이에 해당하지 않는다면 세종포털사이트에서의 설정을 확인하세요.\\n https://portal.sejong.ac.kr 로그인 👉 정보수정 👉 개인정보수집동의 모두 동의')
        return redirect('/mypage/')
    elif temp_user_info == 'err_all':
        messages.error(request, '⛔ 대양휴머니티칼리지 로그인 중 예기치 못한 오류가 발생했습니다. 다시 시도해주세요 😥')
        return redirect('/mypage/')
    # 기본 정보 -> 변수에 저장
    ui_row = NewUserInfo.objects.get(student_id = user_id)
    year = user_id[:2]
    getted_major = temp_user_info['major']

    # ***********************************************************************************
    
    # getted_major = 
    # year = 
    # ui_row.year = 
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