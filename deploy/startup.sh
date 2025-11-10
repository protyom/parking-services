#!/bin/sh

docker compose -f /home/ubuntu/server/docker-compose.yml down && docker compose -f /home/ubuntu/server/docker-compose.yml up -d