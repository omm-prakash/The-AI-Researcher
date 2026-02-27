#!/bin/bash

# Exit on any error
set -e

# Configuration
APP_NAME="tar-backend"
PROJECT_DIR="$HOME/research-agent"
ENTRY_POINT="run_prod.py"
BRANCH="authentication"

echo "================================================"
echo " Starting Deployment for $APP_NAME..."
echo "================================================"

# 1. Navigate to project directory
cd $PROJECT_DIR

# 2. Pull the latest code
echo "=> [1/4] Pulling latest changes from branch '$BRANCH'..."
git pull origin $BRANCH

# 3. Handle Virtual Environment & Dependencies
echo "=> [2/4] Updating dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment (venv) not found. Please create it first."
    exit 1
fi
pip install -r requirements.txt

# 4. Handle PM2 process
echo "=> [3/4] Syncing PM2 process..."
# We run the python file directly so that your if name == "main": block (with all your uvicorn settings) is executed.
if pm2 describe $APP_NAME > /dev/null 2>&1
then
    echo "   Existing process found. Restarting..."
    pm2 restart $APP_NAME
else
    echo "   Starting $APP_NAME for the first time..."
    pm2 start "python $ENTRY_POINT" --name $APP_NAME
    pm2 save
fi

echo "=> [4/4] Deployment complete!"
echo "================================================"