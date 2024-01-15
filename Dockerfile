FROM python:3.11-slim

RUN apt update && apt upgrade -y && python -m pip install --upgrade pip && pip install kopf kubernetes && apt clean && apt autoremove --yes

ADD . /src

CMD kopf run /src/handlers.py --all-namespaces
