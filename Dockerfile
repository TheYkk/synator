FROM python:3.8-slim

RUN python -m pip install --upgrade pip

RUN pip install kopf kubernetes

ADD . /src

CMD kopf run /src/handlers.py
