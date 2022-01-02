###!/bin/bash

# 컨테이너 내부에서 실행될 스크립트

PROFILE=$1

service cron start

if [ $PROFILE == "dev" ] then
    python manage.py crontab add --settings=project.settings.dev
    cd /srv/PleaseGraduate/dev/
    uwsgi --ini uwsgi.ini
else
    python manage.py crontab add --settings=project.settings.prod
     cd /srv/PleaseGraduate/deploy/
    uwsgi --ini uwsgi.ini
fi
