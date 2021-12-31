###!/bin/bash

# GitHub에 등록한 환경변수 받아오기
DOCKER_USERNAME=$1
DOCKER_REPOSITORY=$2
DOCKER_TAG=$3

echo "================== UPDATE '.env' file =================="
echo -e "DOCKER_USERNAME=$DOCKER_USERNAME\nDOCKER_REPOSITORY=$DOCKER_REPOSITORY\nDOCKER_TAG=$DOCKER_TAG" > .env

echo "================== PULL docker image =================="
docker pull $DOCKER_USERNAME/$DOCKER_REPOSITORY:$DOCKER_TAG

echo "================== SERVER DOWN =================="
docker-compose -p pg_compose down

echo "================== SERVER UP   =================="
docker-compose -p pg_compose up -d

echo "================== DELETE unused images  =================="
docker image prune -f