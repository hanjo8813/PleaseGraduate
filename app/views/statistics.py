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
    grade_list = request.POST.getlist('grade[]')
    selection_list = request.POST.getlist('selection[]')

    # 선택영역 추가 수정
    if "기타" in selection_list:
        selection_list += ["인성과도덕", "사회와제도", "예술과생활", "생명과자연", "생명과 과학", "역사와문화", "인성과창의력"]
    if "자기계발과진로" in selection_list:
        selection_list += ["융합과창업"]
    
    # 사용자 과목정보에서 교선 긁어옴
    cs_queryset = UserGrade.objects.exclude(year = '커스텀').filter(
        classification__in = ['교선', '교선1', '교선2'], 
        selection__in=selection_list, 
        grade__in= grade_list
    )
    cs_count = cs_queryset.values_list('subject_num').annotate(count=Count('subject_num'))
    # 쿼리셋을 리스트로 변환 -> 등장횟수에 따라 내림차순 정렬 
    cs_count = sorted(list(cs_count), key = lambda x : x[1], reverse=True)
    zip_lecture_count = []
    for s_num, count in cs_count:
        if count < 10:
            continue
        al_queryset = AllLecture.objects.filter(
            subject_num = s_num, 
            classification__in = ['교선', '교선1', '교선2'], 
            selection__in=selection_list,
            # grade__in=grade_list
        )
        if al_queryset.exists():
            lec_info = list(al_queryset.values())[0]
            zip_lecture_count.append([lec_info, count])
    # context 전송
    context={
        'zip_lecture_count': zip_lecture_count
    }
    return JsonResponse(context)