#!/bin/bash
set -ex

# Update repository
cd /home/ubuntu/KORAIL_AX_Platform
git pull origin main

# Update Streamlit service file to bind to 8502 and add baseUrlPath
sudo sed -i 's/--server.port 8501/--server.port 8502 --server.baseUrlPath \/app/g' /etc/systemd/system/streamlit.service
sudo systemctl daemon-reload
sudo systemctl restart streamlit

# Replace Nginx defaults with landing page
sudo apt-get update
sudo apt-get install -y nginx

sudo rm -rf /var/www/html/*
sudo cp -r /home/ubuntu/KORAIL_AX_Platform/landing_page/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html

# Write Nginx configuration mapping to Streamlit
cat << 'EOF' | sudo tee /etc/nginx/sites-available/default
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html index.htm;
    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }

    location ^~ /app/ {
        proxy_pass http://localhost:8502/app/;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    location ^~ /app/_stcore/stream {
        proxy_pass http://localhost:8502/app/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

# Ensure Nginx loads the new configuration
sudo nginx -t
sudo systemctl restart nginx
