"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import platform, os, json
from django.core.exceptions import ImproperlyConfigured
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)


# 장고 비밀키 + DB 접속 정보 분리
secret_file = os.path.join(BASE_DIR, 'secret.json')

with open(secret_file) as f:
    secrets = json.loads(f.read())

def get_secret(setting, secrets=secrets):
    # json을 읽고 값을 가져온다
    try:
        return secrets[setting]
    # 오류났을 경우에 오류상황 명시
    except KeyError:
        error_msg = "Set the {} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)


# json에서 장고 키 빼오기
SECRET_KEY = get_secret("SECRET_KEY")


# 개발시엔 True로 디버그 확인, 배포시엔 False
if platform.system() == 'Windows':
    DEBUG = True
else:
    DEBUG = False


# 호스트 설정
ALLOWED_HOSTS = [
    # 개발용 호스트(모두 허용)
    '*',
    # 배포용 호스트
    #'.ap-northeast-2.compute.amazonaws.com',
]


# 세션 설정
SESSION_EXPIRE_AT_BROWSER_CLOSE = True      # 브라우저 종료시 세션 파괴
SESSION_SAVE_EVERY_REQUEST = True           # 사용자가 리퀘 날릴때마다 초기화
SESSION_COOKIE_AGE = 3*60*60                # 3시간 안건들면 세션 파괴


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_crontab',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # DB접속 정보는 json secret 파일에서 빼옴
        'NAME': get_secret("NAME"),
        'USER': get_secret("USER"),
        'PASSWORD': get_secret("PASSWORD"),
        'HOST': get_secret("HOST"),
        'PORT': get_secret("PORT"),
    }
}



# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

# Default 시간에서 서울 시간으로 변경했음
TIME_ZONE = 'Asia/Seoul'

# TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/


# static file 경로 설정

# 내가 쓰고있는 스태틱 경로 (collectstatic 할때 참조)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static')
]
# 장고가 스태틱 모아줄때 폴더명 지정
STATIC_ROOT = os.path.join(BASE_DIR, 'col_static')
# 요청 받는 이름
STATIC_URL = '/static/'


# 크론탭 설정

# 분 시 일 월 요일
CRONJOBS = [
    ('0 15 * * *', 'app.crontab.insert_today'),
]


'''
# media root 추가
#app폴더의 하위폴더로 루트 설정.
MEDIA_ROOT = os.path.join(BASE_DIR , 'app/uploaded_media')
MEDIA_URL = '/uploaded_media/'
'''
