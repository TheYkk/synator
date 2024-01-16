FROM python:3.11-slim

RUN mkdir /src

ADD ./handlers.py /src

WORKDIR /src

RUN apt update && apt upgrade -y && \
    python -m pip install --upgrade pip && \
    pip install kopf kubernetes && \
    apt clean && apt autoremove --yes

CMD kopf run handlers.py --all-namespaces
