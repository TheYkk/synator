FROM python:3.8-slim

ADD . /src

RUN pip install -r /src/requirements.txt

CMD kopf run --all-namespaces /src/handlers.py
