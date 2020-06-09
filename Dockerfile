FROM debian:buster 

ENV PYTHON_VERSION "3.7"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    nano \
    sudo \
    openssh-server \
    git \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get install -y python${PYTHON_VERSION} \
    python3-pip \
    python${PYTHON_VERSION}-dev \
    && ln -s /usr/bin/python${PYTHON_VERSION} /usr/bin/python \
    && python -m pip install --upgrade --force pip

COPY . /pyarchive

RUN pip install -r /pyarchive/requirements.txt

EXPOSE 8000

WORKDIR /pyarchive/anniversary_project

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
