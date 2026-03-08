#!/bin/sh
# Custom nginx entrypoint that skips chown operations
set -e

# Create cache directories if they don't exist
mkdir -p /var/cache/nginx/client_temp \
    /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp \
    /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp \
    /var/run/nginx

# Start nginx directly (skip all the chown operations)
exec nginx -g "daemon off;"

