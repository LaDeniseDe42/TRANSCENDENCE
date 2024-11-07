FROM python:3.10.12-alpine

COPY ./transcendence /app/transcendence

RUN pip install --upgrade pip && pip install -r /app/transcendence/requirements.txt \
    && python /app/transcendence/manage.py collectstatic --noinput \
    && apk add --no-cache bash

WORKDIR /app/transcendence

CMD ["bash", "/app/transcendence/script.sh"]