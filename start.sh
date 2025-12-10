#!/bin/bash

# Run migrations
python manage.py migrate

# Start gunicorn
gunicorn FeedProject.wsgi:application