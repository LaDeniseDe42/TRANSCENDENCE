FROM    nginx:1.25.5-alpine

ARG    DOMAIN_NAME
ENV   DOMAIN_NAME=${DOMAIN_NAME}

RUN     apk add openssl && \
        mkdir -p /etc/nginx/ssl && \
        openssl req -x509 -nodes -out /etc/nginx/ssl/trans.crt -keyout /etc/nginx/ssl/trans.key -subj "/C=FR/ST=GES/L=Mulhouse/O=42/OU=42/CN=${DOMAIN_NAME}" && \
        apk add --no-cache bash

COPY    ./nginx.conf    /etc/nginx/conf.d/trans.conf
COPY    ./launch.sh     /tmp/launch.sh

CMD     ["bash", "/tmp/launch.sh"]