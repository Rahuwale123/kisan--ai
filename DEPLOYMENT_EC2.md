# AWS EC2 Deployment Guide for Kisan Voice Assistant

## Step 1: Configure Security Group
1. Go to EC2 Console > Security Groups
2. Create or edit your security group with these rules:

Inbound Rules:
```
Type        Port    Source          Description
SSH         22      Your IP         SSH access
HTTP        80      0.0.0.0/0       Web access
HTTPS       443     0.0.0.0/0       SSL access
Custom TCP  5000    0.0.0.0/0       Application port
```

Outbound Rules:
```
Type        Port    Destination     Description
All traffic All     0.0.0.0/0       Allow all outbound traffic
```

Note: Make sure to apply this security group to your EC2 instance.

## Step 2: Install Dependencies
```bash
# Update system and install dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip nginx git

# Install MySQL (MariaDB)
sudo yum install -y mariadb105-server
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Secure MySQL installation
sudo mysql_secure_installation
# Answer the prompts:
# - Enter current root password (just press Enter as it's not set)
# - Set root password: Y
# - Remove anonymous users: Y
# - Disallow root login remotely: Y
# - Remove test database: Y
# - Reload privilege tables: Y
```

## Step 3: Set Up MySQL Database
```bash
# Connect to MySQL
sudo mysql -u root -p
# Enter the password you set during mysql_secure_installation

# In MySQL prompt, run:
CREATE DATABASE farmers_database;
CREATE USER 'kisan_user'@'localhost' IDENTIFIED BY 'QWer12@*';
GRANT ALL PRIVILEGES ON farmers_database.* TO 'kisan_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Step 4: Clone Repository
```bash
git clone https://github.com/Rahuwale123/kisan--ai.git
cd kisan--ai
```

## Step 5: Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install MySQL connector if not in requirements.txt
pip install mysql-connector-python
```

## Step 6: Configure Environment Variables
```bash
# Create and edit .env file
nano .env
```

Add these environment variables:
```
# Database configuration
MYSQL_HOST=localhost
MYSQL_USER=kisan_user
MYSQL_PASSWORD=QWer12@*
MYSQL_DATABASE=farmers_database

# Twilio configuration
TWILIO_ACCOUNT_SID=AC610e5206c0153bcb5833955b4a9d13b1
TWILIO_AUTH_TOKEN=9c1ff3c6501227937bf9c6cdf624db6a
TWILIO_PHONE_NUMBER=+16609003015
GEMINI_API_KEY=AIzaSyDJ6hYHy5RZpdaeT3WCGGKdk_nvoH5VoRs
DEBUG=1
BASE_URL=http://54.92.244.26
WEBHOOK_BASE_URL=http://54.92.244.26
```

## Step 7: Create Service File
```bash
sudo nano /etc/systemd/system/farming-assistant.service
```

Add this content:
```ini
[Unit]
Description=Farming Assistant Service
After=network.target mariadb.service

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/kisan--ai
Environment="PATH=/home/ec2-user/kisan--ai/venv/bin"
ExecStart=/home/ec2-user/kisan--ai/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Step 8: Configure Nginx
```bash
sudo nano /etc/nginx/conf.d/farming-assistant.conf
```

Add this content:
```nginx
server {
    listen 80;
    server_name 54.92.244.26;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Step 9: Start Services
```bash
# Make sure MySQL is running
sudo systemctl status mariadb
sudo systemctl restart mariadb

# Enable and start the application service
sudo systemctl daemon-reload
sudo systemctl enable farming-assistant
sudo systemctl start farming-assistant

# Check application status
sudo systemctl status farming-assistant

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```

## Step 10: Test the Application
```bash
# Test database connection
mysql -u kisan_user -p farmers_database -e "SELECT 1;"

# Test the application
curl -X POST "http://54.92.244.26/initiate-call" \
-H "Content-Type: application/json" \
-d '{"phone_number": "+918208594908"}'
```

## Monitoring Commands
```bash
# Check application logs
sudo journalctl -u farming-assistant -f

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Check MySQL logs
sudo tail -f /var/log/mysqld.log

# Check service status
sudo systemctl status farming-assistant
sudo systemctl status nginx
sudo systemctl status mariadb
```

## Restart Commands
```bash
# Restart application
sudo systemctl restart farming-assistant

# Restart MySQL
sudo systemctl restart mariadb

# Restart Nginx
sudo systemctl restart nginx

# Restart all services
sudo systemctl restart mariadb farming-assistant nginx
```

## Database Backup (Optional)
```bash
# Backup database
mysqldump -u kisan_user -p farmers_database > backup.sql

# Restore database if needed
mysql -u kisan_user -p farmers_database < backup.sql
``` 
