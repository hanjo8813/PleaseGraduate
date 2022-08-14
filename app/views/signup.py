# 파이썬 라이브러리
import platform
import json
import datetime
from tkinter.tix import Tree
import bcrypt
# 장고 관련 참조
from django.shortcuts import redirect
from django.contrib import messages
# 모델 참조
from ..models import *
from .crawler import *
# AJAX 통신관련 참조
from django.views.decorators.csrf import csrf_exempt


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
    temp_user_info = get_user_info(id, pw)

    # 예외처리
    if temp_user_info == 'err_auth':
        messages.error(request, '⚠️ 세종대학교 포털 ID/PW를 다시 확인하세요! (Caps Lock 확인) \\n\\n (재외국민전형 입학자, 계약학과, 편입생은 학생인증이 불가능합니다.😥)')
        return redirect('/agree/')
    elif temp_user_info == 'err_server':
        messages.error(request, '⛔ 대양휴머니티칼리지 로그인 중 예기치 못한 오류가 발생했습니다. 대양휴머니티칼리지 사이트의 서버 문제일 수 있으니 잠시 후 시도해주세요.')
        return redirect('/agree/')

# ***********************************************************************************

    if platform.system() == 'Windows':
        temp_user_info['major'] = '소프트웨어학과'
        year = 22
    
# ***********************************************************************************

    # 검사 가능 학과 선별 로직
    input_major = temp_user_info['major']
    major_select = []

    # 세부전공
    major_qs = Major.objects.filter(sub_major = input_major)
    if major_qs.exists():
        temp_user_info['sub_major'] = input_major   # 세션에 추가해줌
        temp_user_info['major'] = major_qs[0].major
    else:
        # 전공/학과
        major_qs = Major.objects.filter(major = input_major)
        if major_qs.exists():
            pass
        else:
            # 학부
            major_qs = Major.objects.filter(department = input_major)
            if major_qs.exists():
                for q in major_qs:
                    major_select.append(q.major)
            else:
                messages.error(request, '😢 아직 Please Graduate에서 ' + input_major + '-' + str(year) + '학번의 검사를 지원하지 않습니다.')
                return redirect('/agree/') 
    
    # 예체능대학은 영어면제
    is_exempt_english = 0
    if major_qs[0].college == "예체능대학":
        is_exempt_english = 1
    temp_user_info['is_exempt_english'] = is_exempt_english

    # 예외처리
    if major_select :
        if not Standard.objects.filter(user_year = year, user_dep__in = major_select).exists():
            messages.error(request, '😢 아직 Please Graduate에서 ' + input_major + '-' + str(year) + '학번의 검사를 지원하지 않습니다.')
            return redirect('/agree/')
    else:
        if not Standard.objects.filter(user_year = year, user_dep = temp_user_info['major']).exists():
            messages.error(request, '😢 아직 Please Graduate에서 ' + input_major + '-' + str(year) + '학번의 검사를 지원하지 않습니다.')
            return redirect('/agree/')

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
    # 세부전공이 있다면 추가
    if "sub_major" in temp_user_info :
        new_ui.sub_major = temp_user_info['sub_major']
    new_ui.save()

    return redirect('/success/')