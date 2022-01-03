# 장고 관련 참조
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
# 모델 참조
from ..models import *
from .auth import *
# AJAX 통신관련 참조
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def a_search(request):
    # AJAX 통신으로 넘어온 학수번호를 받아서 파싱
    s_num = request.POST['back_s_num']
    if not s_num.isdigit():
        return JsonResponse({'result' : '검색실패'})
    s_num = int(s_num)
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