#!/bin/bash
# This shell script deploys a new version to a server.
PROJ_NAME=Gitjits
PROJ_DIR=$PROJ_NAME
VENV=$PROJ_NAME
PA_DOMAIN="$PROJ_NAME.pythonanywhere.com"
PA_USER=$PROJ_NAME

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
sshpass -p "$DEMO_PA_PWD" ssh -o "StrictHostKeyChecking no" "$PA_USER@ssh.pythonanywhere.com" /bin/bash << EOF
    cd ~/$PROJ_DIR; PA_USER=$PA_USER PROJ_DIR=~/$PROJ_DIR VENV=$VENV PA_DOMAIN=$PA_DOMAIN ./rebuild.sh

echo "Deploy complete!"
EOF

echo "SSHing to PythonAnywhere."
