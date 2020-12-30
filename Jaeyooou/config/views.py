# view -> 기능을 담당한다 (페이지 단위)

from django.http import HttpResponse
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
def test(request):
    return "<html><body>test</body></html>"

def index(request):

    html = "<html><body>안녕 창의학기제!!!!!</body></html>"
    return HttpResponse(html)
def welcome(request):

    html = "<html><body>Welcomepage</body></html>"
    return HttpResponse(html)

def template_test(request):
    return render(request , 'test.html')

def upload_test(request):
    #요청이 post 형식일때 , html 파일에 정의되어있음
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        print(uploaded_file.name)
        print(uploaded_file.size)
        fs = FileSystemStorage()
        fs.save(uploaded_file.name , uploaded_file)
        return render(request , 'test.html')
    return render(request , 'Upload.html')