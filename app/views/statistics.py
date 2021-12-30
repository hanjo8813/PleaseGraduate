# 장고 관련 참조
from django.http import JsonResponse
# 모델 참조
from django.db.models import Count
from ..models import *
# AJAX 통신관련 참조
from django.views.decorators.csrf import csrf_exempt


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