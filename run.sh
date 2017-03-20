#!/bin/bash

if [ -z "$MONGO_URL" ]; then
    echo "Need to set MONGO_URL when calling this container! Exiting."
    exit 1
fi



gunicorn -w 4 flask_app:app
