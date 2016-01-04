FROM debian
MAINTAINER "MuzHack" <contact@muzhack.com>

RUN apt-get update && apt-get install -y cron python3 python3-pip lsb-release wget
RUN echo "deb http://download.rethinkdb.com/apt `lsb_release -cs` main" | tee /etc/apt/sources.list.d/rethinkdb.list
RUN wget -qO- https://download.rethinkdb.com/apt/pubkey.gpg | apt-key add -
RUN apt-get update && apt-get install -y rethinkdb
RUN apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app
COPY ./crontab /etc/cron.d/
COPY ./requirements.txt /app/
RUN mkdir -p /app/rethinkdb
COPY ./rethinkdb/backup.py /app/rethinkdb/

RUN pip3 install -r requirements.txt
RUN rm -rf requirements.txt

CMD python3 cron.py
