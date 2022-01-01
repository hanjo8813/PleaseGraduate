from .base import *

DEBUG = False

ALLOWED_HOSTS = [ 'pg.hanjo.xyz' ]  # 배포전 변경

# static file 경로 설정
# 내가 쓰고있는 스태틱 경로 (collectstatic 할때 참조)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static')
]
# 스태틱 target 폴더
STATIC_ROOT = os.path.join(BASE_DIR, 'deploy/col_static')
# 요청 받는 이름
STATIC_URL = '/static/'
