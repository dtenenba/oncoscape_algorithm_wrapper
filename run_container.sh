#!/bin/bash


docker run  --name oncoscape_algorithm_wrapper --rm -p 8000:8000 \
   -e "MONGO_CONNECTION=$MONGO_CONNECTION MONGO_USERNAME=$MONGO_USERNAME MONGO_PASSWORD=$MONGO_PASSWORD" oncoscape/oncoscape_algorithm_wrapper
