#!/bin/bash
sed -i "s/HOSTNAME/$SERVER_NAME/g" /etc/nginx/conf.d/trans.conf
nginx -g "daemon off;"