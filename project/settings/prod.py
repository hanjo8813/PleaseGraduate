from .base import *

DEBUG = True

ALLOWED_HOSTS = [ 'pg.hanjo.xyz' ]  # 배포전 변경

# static file 경로 설정
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'deploy/col_static')
STATIC_URL = '/static/'

# cron 설정
CRONJOBS = [
    ('0 15 * * *', 'app.crontab.insert_today'),
    ('* * * * *', 'app.crontab.test'),
]
CRONTAB_DJANGO_SETTINGS_MODULE = 'project.settings.prod'