#!/bin/bash

gunicorn -w 4 flask_app:app
