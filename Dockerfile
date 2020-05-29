FROM ubuntu:20.04

ENV TZ America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#   Install Python3.7, then create a symlink at /usr/bin/python so I can call python3.7 using python
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get install -y python3.7 && \
    apt-get install -y python3-pip && \
    apt-get install -y python3.7-dev && \
    ln -s /usr/bin/python3.7 /usr/bin/python

COPY . /usr/src/

RUN cd /usr/src/ && \
    python3.7 -m pip install -r requirements.txt && \
    chmod +x reset_project.sh && \
    ./reset_project.sh

WORKDIR /usr/src/anniversary_project 


EXPOSE 8000

ENTRYPOINT ["python3.7", "manage.py", "runserver", "0.0.0.0:8000"]