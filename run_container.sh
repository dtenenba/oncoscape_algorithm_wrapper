#!/bin/bash


docker run  --name oncoscape_plsr --rm -p 8000:8000 \
   -e "MONGO_URL=$MONGO_URL" dtenenba/oncoscape_plsr
