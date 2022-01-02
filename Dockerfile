FROM python:3.9

RUN apt-get update 
RUN apt-get -y install cron

WORKDIR /srv/PleaseGraduate

COPY . /srv/PleaseGraduate/

RUN pip install -r requirements.txt
RUN pip install uwsgi