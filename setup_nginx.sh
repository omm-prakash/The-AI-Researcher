#!/bin/bash

# Configuration
DOMAIN="api.yourdomain.com" # <-- CHANGE THIS to your actual domain or IP address
PORT=8000                   # Should match the port Uvicorn is running on

echo "================================================"
echo " Setting up Nginx Reverse Proxy..."
echo "================================================"

# Check for root privileges (required to edit /etc/nginx)
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root. Try: sudo ./setup_nginx.sh"
  exit 1
fi

# 1. Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "=> Installing Nginx..."
    apt-get update
    apt-get install -y nginx
fi

# 2. Create the Nginx configuration file
echo "=> Creating Nginx configuration for $DOMAIN..."
cat > /etc/nginx/sites-available/tar-backend <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Gzip settings for performance
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Main API Routing
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        
        # Websocket support (useful if you add LangGraph streaming later)
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Header forwarding
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts (Crucial for AI Researcher: allows up to 5 minutes for generation)
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF

# 3. Enable the site
echo "=> Enabling the site..."
ln -sf /etc/nginx/sites-available/tar-backend /etc/nginx/sites-enabled/

# 4. Remove default Nginx site if it exists to prevent conflicts
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# 5. Check configuration and restart
echo "=> Testing Nginx configuration..."
nginx -t

echo "=> Restarting Nginx..."
systemctl restart nginx

echo "================================================"
echo " Nginx setup complete!"
echo " Important: Make sure to point your DNS A-record for $DOMAIN to this server's IP."
echo ""
echo " Highly Recommended: Secure it with free HTTPS by running:"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d $DOMAIN"
echo "================================================"
