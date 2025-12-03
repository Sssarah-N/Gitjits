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
# With -T, no indentation, quoted heredoc
sshpass -p "$DEMO_PA_PWD" ssh -T -o "StrictHostKeyChecking no" "$PA_USER@ssh.pythonanywhere.com" << 'EOF'
cd ~/Gitjits
./rebuild.sh
EOF