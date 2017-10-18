#!/bin/bash

if [ -z "$MONGO_CONNECTION" ]; then
    echo "Need to set MONGO_CONNECTION when calling this container! Exiting."
    exit 1
fi

if [ -z "$MONGO_USERNAME" ]; then
    echo "Need to set MONGO_USERNAME when calling this container! Exiting."
    exit 1
fi

if [ -z "$MONGO_PASSWORD" ]; then
    echo "Need to set MONGO_PASSWORD when calling this container! Exiting."
    exit 1
fi

gunicorn -w 4 -b "0.0.0.0:8000" flask_app:app
