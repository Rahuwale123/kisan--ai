# AWS EC2 Deployment Guide for Kisan Voice Assistant

## Step 1: Launch EC2 Instance

1. Go to AWS EC2 Console
2. Launch a new EC2 instance:
   - Choose Ubuntu Server 22.04 LTS
   - Select t2.micro (free tier) or t2.small
   - Create or select a key pair for SSH access
   - Configure security group:
     ```
     HTTP (80)   : 0.0.0.0/0
     HTTPS (443) : 0.0.0.0/0
     SSH (22)    : Your IP
     Custom TCP  : 5000 (Application port)
     ```

## Step 2: Connect to EC2 Instance
```bash
# Use your .pem file
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 3: Install Dependencies
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and pip
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv nginx -y

# Install MySQL
sudo apt install mysql-server -y
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure MySQL installation
sudo mysql_secure_installation
```

## Step 4: Set Up MySQL Database
```bash
sudo mysql
```
```sql
CREATE DATABASE farmers_database;
CREATE USER 'kisan_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON farmers_database.* TO 'kisan_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Step 5: Clone and Set Up Application
```bash
# Clone repository
git clone https://github.com/Rahuwale123/kisan--ai.git
cd kisan--ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
```

Add these environment variables to .env:
```
MYSQL_HOST=localhost
MYSQL_USER=kisan_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=farmers_database
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
GEMINI_API_KEY=your_key
WEBHOOK_BASE_URL=your_domain_or_ip
```

## Step 6: Set Up Gunicorn
```bash
# Test Gunicorn
gunicorn --bind 0.0.0.0:5000 run:app

# Create systemd service
sudo nano /etc/systemd/system/kisan.service
```

Add this content:
```ini
[Unit]
Description=Kisan Voice Assistant
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/kisan--ai
Environment="PATH=/home/ubuntu/kisan--ai/venv/bin"
ExecStart=/home/ubuntu/kisan--ai/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl start kisan
sudo systemctl enable kisan
```

## Step 7: Set Up Nginx
```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/kisan
```

Add this content:
```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/kisan /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Step 8: SSL Certificate (Optional but Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your_domain
```

## Step 9: Update Twilio Webhook URLs
Update your Twilio webhook URLs to point to:
```
https://your_domain/voice
https://your_domain/voice/status
```

## Monitoring and Maintenance

### View Logs
```bash
# Application logs
sudo journalctl -u kisan.service -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart application
sudo systemctl restart kisan

# Restart Nginx
sudo systemctl restart nginx
```

### Database Backup
```bash
# Backup
mysqldump -u kisan_user -p farmers_database > backup.sql

# Restore
mysql -u kisan_user -p farmers_database < backup.sql
```

## Troubleshooting
1. Check application logs: `sudo journalctl -u kisan.service -f`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Test MySQL connection: `mysql -u kisan_user -p`
4. Check service status: `sudo systemctl status kisan`
5. Verify ports: `sudo netstat -tulpn`
