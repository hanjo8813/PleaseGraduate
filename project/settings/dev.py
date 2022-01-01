from .base import *

DEBUG = True

ALLOWED_HOSTS = [ '*' ]

# static file 경로 설정
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'dev/col_static')
STATIC_URL = '/static/'
