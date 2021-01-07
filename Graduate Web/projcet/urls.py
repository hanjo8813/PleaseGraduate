"""projcet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.conf import settings
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # 첫페이지 url 설정
    path('', views.r_index),

    # 정현이 head
    path('head/', views.r_head),

    # 페이지 렌더링
    path('dbcheck/', views.r_dbcheck),
    path('login/', views.r_login),
    path('en_result/', views.r_en_result),

    # 다른 함수사용 url 패턴
    path('f_test/', views.f_test),
    path('f_login/', views.f_login),

    # 테스트용
    path('result_test/', views.result_test),

]

# 미디어 루트 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL , document_root = settings.MEDIA_ROOT)
