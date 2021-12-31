###!/bin/bash

DOCKER_USERNAME=$1
DOCKER_PASSWORD=$2
DOCKER_REPOSITORY=$3
DOCKER_TAG=$4

echo "================== docker login =================="
docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD

echo "================== PULL docker image =================="
docker pull $DOCKER_USERNAME/$DOCKER_REPOSITORY:$DOCKER_TAG

echo "================== UPDATE '.env' file =================="
echo -e "DOCKER_USERNAME=$DOCKER_USERNAME\nDOCKER_REPOSITORY=$DOCKER_REPOSITORY\nDOCKER_TAG=$DOCKER_TAG" > .env

echo "================== SERVER DOWN =================="
docker-compose -p pg_compose down

echo "================== SERVER UP   =================="
docker-compose -p pg_compose up -d

echo "================== DELETE unused images  =================="
docker image prune -f