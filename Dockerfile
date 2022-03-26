FROM python:3.8-slim

RUN pip install kopf kubernetes

ADD . /src

CMD kopf run --all-namespaces /src/handlers.py
