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
from django.contrib import admin
from django.urls import path, include
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # 첫페이지 url 설정
    path('', views.f_index),

    # 뒤에 붙일 url주소는 page2, view에서 불러오는 함수는 i_to_p2,
    # 해당 패턴의 이름은 i_to_p2로 설정
    path('dbcheck/', views.f_dbcheck, name='n_dbcheck'),
    path('upload/', views.f_upload, name='n_upload'),
    path('compare/', views.f_compare, name='n_compare'),

]
