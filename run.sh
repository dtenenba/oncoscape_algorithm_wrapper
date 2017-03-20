#!/bin/bash

if [ -z "$MONGO_URL" ]; then
    echo "Need to set MONGO_URL when calling this container! Exiting."
    exit 1
fi



gunicorn -w 4 -b "0.0.0.0:8000" flask_app:app
