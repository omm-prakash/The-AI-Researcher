#!/bin/bash

# Configuration - Updated for your specific domain
DOMAIN="the-ai-researcher.duckdns.org"
PORT=8000

echo "================================================"
echo " Setting up Nginx Reverse Proxy for $DOMAIN"
echo "================================================"

if [ "$EUID" -ne 0 ]; then
  echo "Error: Run as root (sudo ./setup_nginx.sh)"
  exit 1
fi

# 1. Install Nginx
if ! command -v nginx &> /dev/null; then
    apt-get update && apt-get install -y nginx
fi

# 2. Safety Check: Don't overwrite if SSL is already configured
if grep -q "443 ssl" /etc/nginx/sites-available/tar-backend 2>/dev/null; then
    echo "!!! WARNING: SSL is already configured in /etc/nginx/sites-available/tar-backend."
    echo "!!! Running this script will overwrite your HTTPS settings."
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 3. Create Configuration
cat > /etc/nginx/sites-available/tar-backend <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Performance
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # AI Specific Timeouts (5 Minutes)
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF

ln -sf /etc/nginx/sites-available/tar-backend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx

echo "================================================"
echo " Setup complete! Next step: run Certbot for SSL."
echo "================================================"