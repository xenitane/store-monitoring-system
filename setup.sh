#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install project requirements
pip install -r requirements.txt

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Add folder for saving report csv
mkdir csv_data