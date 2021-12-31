FROM python:3.9

WORKDIR /srv/PleaseGraduate

COPY . /srv/PleaseGraduate/

RUN pip install -r requirements.txt
RUN pip install uwsgi

CMD ["uwsgi", "--ini", "uwsgi.ini"]

# local
# docker build -t django_img .
# docker run -d --name django_con -p 8000:8000 -v ${PWD}:/srv/PleaseGraduate/ django_img