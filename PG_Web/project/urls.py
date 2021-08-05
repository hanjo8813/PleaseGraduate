"""project URL Configuration

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

    # 페이지 렌더링
    path('', views.r_head),
    path('statistics/', views.r_statistics),
    path('login/', views.r_login),
    path('changePW/', views.r_changePW),
    path('mypage/', views.r_mypage),
    path('agree/', views.r_agree),
    path('custom/', views.r_custom),
    path('register/', views.r_register),
    path('success/', views.r_success),
    path('success_delete/', views.r_success_delete),
    path('result/', views.r_result),
    path('en_result/', views.r_en_result),

    # 다른 함수사용 url 패턴
    path('f_login/', views.f_login),
    path('f_logout/', views.f_logout),
    path('f_certify/', views.f_certify),
    path('f_register/', views.f_register),
    path('f_mod_info/', views.f_mod_info),
    path('f_mod_info_ms/', views.f_mod_info_ms),
    path('f_mod_ms_eng/', views.f_mod_ms_eng),
    path('f_mod_pw/', views.f_mod_pw),
    path('f_mod_grade/', views.f_mod_grade),
    path('f_find_pw/', views.f_find_pw),
    path('f_add_custom/', views.f_add_custom),
    path('f_delete_account/', views.f_delete_account),

    # AJAX 통신
    path('a_statistics/', views.a_statistics),
    path('a_search/', views.a_search),
    

    # 테스트용
    path('admin_test/', views.r_admin_test),
    path('f_user_test/', views.f_user_test),
    path('f_insert_user/', views.f_insert_user),
    path('f_test/', views.f_test),
    path('f_update/', views.f_update),
    path('f_test_update/', views.f_test_update),
    path('f_input_st/', views.f_input_st),
]

urlpatterns += static(settings.MEDIA_URL , document_root = settings.MEDIA_ROOT)


# 미디어 루트 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL , document_root = settings.MEDIA_ROOT)
