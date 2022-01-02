FROM python:3.9

# 크론탭 설치
RUN apt-get update 
RUN apt-get -y install cron

# chrome 설치
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt-get update 
RUN apt-get -y install google-chrome-stable

# chrome driver 설치
RUN apt-get install -yqq unzip curl
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /srv/

WORKDIR /srv/PleaseGraduate

COPY . /srv/PleaseGraduate/

RUN pip install -r requirements.txt
RUN pip install uwsgi