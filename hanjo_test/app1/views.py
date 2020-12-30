from django.shortcuts import render
from django.http import HttpResponse
from .models import TestTable

# 이 함수가 호출되면 -> index.html을 렌더링한다.
def f_index(request):
    return render(request, "index.html")

def f_dbcheck(request):
    # model의 test_table 테이블을 변수에 저장
    tt = TestTable.objects.all()
    # 그리고 함수가 불려서 페이지를 렌더링할때 그 변수를 해당 페이지에 넘김
    return render(request, "dbcheck.html", {"t_h":tt})

def f_upload(request):
    return render(request, "upload.html")