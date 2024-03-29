from .base import *

DEBUG = True

ALLOWED_HOSTS = [ '*' ]

# static file 경로 설정 
# 내가 쓰고있는 스태틱 경로 (collectstatic 할때 참조)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static')
]
# 스태틱 target 폴더
STATIC_ROOT = os.path.join(BASE_DIR, 'dev/col_static')
# 요청 받는 이름
STATIC_URL = '/static/'

# cron 설정
# CRONJOBS = [
#     ('* * * * *', 'app.crontab.test'),
#     ('* * * * *', 'app.crontab.daily_statistics'),
# ]
# CRONTAB_DJANGO_SETTINGS_MODULE = 'project.settings.dev'