# Deployment Guide - AI CertPro Platform

## 🚀 Deployment Options

### Option 1: Local Development

1. **Clone the repository**
```bash
cd cert_platform
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application**
```bash
chmod +x start.sh
./start.sh
```

Access at: http://localhost:5000

### Option 2: Production Deployment (Linux Server)

#### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- Nginx
- PostgreSQL (recommended for production)

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx postgresql -y

# Create application user
sudo useradd -m -s /bin/bash certpro
sudo su - certpro
```

#### Step 2: Application Setup

```bash
# Clone/upload application
cd /home/certpro
# Upload your cert_platform directory here

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### Step 3: Database Setup (PostgreSQL)

```bash
# Create database
sudo -u postgres psql
postgres=# CREATE DATABASE certpro;
postgres=# CREATE USER certpro_user WITH PASSWORD 'secure_password_here';
postgres=# GRANT ALL PRIVILEGES ON DATABASE certpro TO certpro_user;
postgres=# \q

# Update db_manager.py to use PostgreSQL instead of SQLite
# Replace: sqlite3.connect(db_path)
# With: psycopg2.connect(
#         dbname='certpro',
#         user='certpro_user',
#         password='secure_password_here',
#         host='localhost'
#       )
```

#### Step 4: Gunicorn Service

Create `/etc/systemd/system/certpro.service`:

```ini
[Unit]
Description=AI CertPro Platform
After=network.target

[Service]
User=certpro
Group=certpro
WorkingDirectory=/home/certpro/cert_platform
Environment="PATH=/home/certpro/cert_platform/venv/bin"
ExecStart=/home/certpro/cert_platform/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/home/certpro/cert_platform/certpro.sock \
    --access-logfile /home/certpro/cert_platform/logs/access.log \
    --error-logfile /home/certpro/cert_platform/logs/error.log \
    backend.app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable certpro
sudo systemctl start certpro
sudo systemctl status certpro
```

#### Step 5: Nginx Configuration

Create `/etc/nginx/sites-available/certpro`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://unix:/home/certpro/cert_platform/certpro.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/certpro/cert_platform/static;
        expires 30d;
    }

    client_max_body_size 20M;
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/certpro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 6: SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Option 3: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p database logs

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "backend.app:app"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - DATABASE_PATH=/app/database/cert_platform.db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/app/static
    depends_on:
      - web
    restart: unless-stopped
```

Deploy:
```bash
docker-compose up -d
```

### Option 4: Cloud Deployment

#### AWS (Elastic Beanstalk)

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize:
```bash
eb init -p python-3.10 cert-platform
```

3. Create environment:
```bash
eb create cert-platform-prod
```

4. Deploy:
```bash
eb deploy
```

#### Heroku

1. Create `Procfile`:
```
web: gunicorn backend.app:app
```

2. Deploy:
```bash
heroku create cert-platform
git push heroku main
```

#### Google Cloud Run

1. Create `Dockerfile` (see above)

2. Build and deploy:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/cert-platform
gcloud run deploy cert-platform --image gcr.io/PROJECT_ID/cert-platform --platform managed
```

## 🔒 Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Use HTTPS (SSL/TLS)
- [ ] Set up firewall (UFW or similar)
- [ ] Enable rate limiting
- [ ] Use strong database passwords
- [ ] Regular security updates
- [ ] Implement CORS restrictions
- [ ] Set up backup system
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for secrets

## 📊 Monitoring

### Application Monitoring

Install monitoring tools:
```bash
pip install prometheus-flask-exporter
```

Add to app.py:
```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

### Log Monitoring

Set up log rotation:
```bash
sudo nano /etc/logrotate.d/certpro
```

```
/home/certpro/cert_platform/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 certpro certpro
}
```

## 🔄 Backup Strategy

### Database Backup

Create backup script `/home/certpro/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR=/home/certpro/backups
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /home/certpro/cert_platform/database/cert_platform.db \
   $BACKUP_DIR/cert_platform_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Schedule with cron:
```bash
crontab -e
# Add: 0 2 * * * /home/certpro/backup.sh
```

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (Nginx, HAProxy)
- Deploy multiple Gunicorn workers
- Use Redis for session storage
- CDN for static files

### Database Scaling
- Read replicas for PostgreSQL
- Connection pooling
- Query optimization
- Caching layer (Redis)

## 🧪 Testing Production

```bash
# Health check
curl https://your-domain.com/api/programs

# Load testing
pip install locust
locust -f tests/load_test.py --host https://your-domain.com
```

## 🆘 Troubleshooting

### Check logs
```bash
sudo journalctl -u certpro -n 100 -f
tail -f /home/certpro/cert_platform/logs/error.log
```

### Restart services
```bash
sudo systemctl restart certpro
sudo systemctl restart nginx
```

### Database issues
```bash
# Check database permissions
ls -la /home/certpro/cert_platform/database/

# Reinitialize if needed
python3 -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); db.initialize()"
```

## 📞 Support

For deployment issues:
- Email: devops@aicertpro.com
- Documentation: https://docs.aicertpro.com
- Community: https://community.aicertpro.com
