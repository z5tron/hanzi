# Instructions copied from - https://hub.docker.com/_/python/
# FROM python:3-onbuild
# FROM ubuntu:bionic
FROM z5tron/texlive

RUN apt-get install nano
RUN apt-get install gcc -y
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
COPY ./requirements.txt /var/www/requirements.txt
RUN pip3 install -r /var/www/requirements.txt

RUN apt-get install -y locales
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

COPY ./chinese.py /var/www/
COPY ./static/ /var/www/static/
COPY ./templates/ /var/www/templates/
# tell the port number the container should expose
EXPOSE 5000

# run the command
CMD ["python3", "/var/www/chinese.py"]
