# 파이썬 라이브러리
import datetime
import bcrypt
# 장고 관련 참조
from django.shortcuts import redirect
from django.contrib import messages
# 모델 참조
from ..models import *
from .calculate import *
from .crawler import *

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
    temp_user_info = get_user_info(user_id, pw)
    # 예외처리
    if temp_user_info == 'err_auth':
        messages.error(request, '⚠️ 세종대학교 포털 ID/PW를 다시 확인하세요! (Caps Lock 확인) \\n\\n (재외국민전형 입학자는 메일로 문의해주세요.)')
        return redirect('/login/')
    elif temp_user_info == 'err_server':
        messages.error(request, '⛔ 대양휴머니티칼리지 로그인 중 예기치 못한 오류가 발생했습니다. 대양휴머니티칼리지 사이트의 서버 문제일 수 있으니 잠시 후 시도해주세요.')
        return redirect('/login/')
    # 임시 id를 세션에 넣어줌
    request.session['temp_user_id'] = user_id
    return redirect('/changePW/')

def f_mypage(user_id):
    ui_row = NewUserInfo.objects.get(student_id=user_id)
    ug = UserGrade.objects.filter(student_id=user_id)
    # 성적표 띄울땐 커스텀과 찐 성적 구분한다
    grade = list(ug.exclude(year='커스텀').values())
    custom_grade = list(ug.filter(year='커스텀').values())
    # 성적표 리스트에서 이수구분 변경여부 검사
    for i, g in enumerate(grade):
        is_changed_classification = 0
        # 변경내역 있는 과목 조회
        cc_qs = ChangedClassification.objects.filter(year = ui_row.year, subject_num = g["subject_num"])
        if cc_qs.exists():
            changed_classifiaction = cc_qs[0].classification
            # 학번 기준과 맞지않으면 변경
            if g["classification"] != changed_classifiaction:
                grade[i]["classification"] += "→" + changed_classifiaction
                is_changed_classification = 1
        # 해당 과목에 이수구분 변경여부 추가 마킹
        grade[i]["is_changed_classification"] = is_changed_classification
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
        'sub_major' : ui_row.sub_major,
        'major_status' : ui_row.major_status,
        'name' : ui_row.name,
        'eng' : ui_row.eng,
        'grade' : grade,
        'custom_grade' : custom_grade,
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