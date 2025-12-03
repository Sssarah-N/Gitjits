#!/bin/bash
# This shell script deploys a new version to a server.

PROJ_DIR=Gitjits
VENV=Gitjits
PA_DOMAIN="Gitjits.pythonanywhere.com"
PA_USER='Gitjits'
echo "Project dir = $PROJ_DIR"
echo "PA domain = $PA_DOMAIN"
echo "Virtual env = $VENV"

if [ -z "$DEMO_PA_PWD" ]
then
    echo "The PythonAnywhere password var (DEMO_PA_PWD) must be set in the env."
    exit 1
fi

echo "PA user = $PA_USER"
echo "PA password = $DEMO_PA_PWD"

echo "SSHing to PythonAnywhere."
echo "Installing sshpass check: $(which sshpass)"

# Run deploy command
sshpass -p "$DEMO_PA_PWD" ssh -T -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null" "$PA_USER@ssh.pythonanywhere.com" "cd ~/Gitjits && git pull origin master && source ~/.virtualenvs/Gitjits/bin/activate && pip install -r requirements.txt && pa_reload_webapp.py Gitjits.pythonanywhere.com"

echo "Deploy complete!"