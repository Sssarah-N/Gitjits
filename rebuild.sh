#!/bin/bash
# This runs on PythonAnywhere servers: fetches new code,
# installs needed packages, and restarts the server.


echo "Rebuilding $PA_DOMAIN"

echo "Pulling latest code..."
git pull origin main || git pull origin master

echo "Activating virtualenv..."
source /home/$PA_USER/.virtualenvs/$VENV/bin/activate

echo "Installing packages..."
pip install --upgrade -r requirements.txt

echo "Reloading web app..."
pa_reload_webapp $PA_DOMAIN

echo "Finished rebuild."
