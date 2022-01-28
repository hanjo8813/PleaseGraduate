from .base import *

DEBUG = False

ALLOWED_HOSTS = [ 'please-graduate.com' ]  # 배포전 변경

# static file 경로 설정
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'deploy/col_static')
STATIC_URL = '/static/'

# cron 설정
CRONJOBS = [
    ('0 15 * * *', 'app.crontab.insert_today'),
    ('1 15 * * *', 'app.crontab.daily_statistics'),
]
CRONTAB_DJANGO_SETTINGS_MODULE = 'project.settings.prod'