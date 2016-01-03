FROM debian
MAINTAINER "MuzHack" <contact@muzhack.com>

RUN apt-get update && apt-get install -y cron python3 rethinkdb \
  && pip3 install virtualenv
RUN apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app
COPY ./crontab /etc/cron.d/
COPY ./requirements.txt /app
COPY ./rethinkdb/backup.py /app/rethinkdb/

RUN virtualenv /env && /env/bin/pip3 install -r requirements.txt
RUN rm -rf requirements.txt

CMD /env/bin/python3 cron.py
