# 🚀 Deployment Guide - SkillSphere Learning Platform

## Quick Start (Local Development)

```bash
# 1. Start Backend Server (Terminal 1)
cd backend
npm run dev

# 2. Start Frontend (Terminal 2)
cd frontend
npm run dev

# 3. Open browser
open http://localhost:5173
```

---

## Production Deployment

### Option 1: Railway.app (Recommended)

**Backend:**
1. Create account at railway.app
2. Create new project → Deploy from GitHub
3. Add environment variables:
   ```
   NODE_ENV=production
   PORT=5000
   JWT_SECRET=your-random-secret-key
   FRONTEND_URL=https://your-frontend.vercel.app
   ```
4. Deploy from `backend/` folder
5. Note the backend URL

**Frontend:**
1. Update `frontend/.env.production`:
   ```
   VITE_API_URL=https://your-backend.railway.app/api
   ```
2. Build: `npm run build`
3. Deploy `dist/` folder to Vercel/Netlify

---

### Option 2: Heroku

**Backend:**
```bash
cd backend
heroku create skillsphere-api
heroku config:set NODE_ENV=production
heroku config:set JWT_SECRET=your-secret
heroku config:set FRONTEND_URL=https://skillsphere.vercel.app
git subtree push --prefix backend heroku main
```

**Frontend:**
- Deploy to Vercel or Netlify from frontend folder

---

### Option 3: DigitalOcean / VPS

**Requirements:**
- Node.js 18+
- PM2 for process management
- Nginx for reverse proxy
- SSL certificate (Let's Encrypt)

**Setup:**
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2
sudo npm install -g pm2

# Clone and setup
git clone <repo-url>
cd learning-community-platform
cd backend && npm install --production
npm run init-db

# Start with PM2
pm2 start server.js --name skillsphere-api
pm2 save
pm2 startup
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## Database Migration (SQLite → PostgreSQL)

For production, consider PostgreSQL:

1. Install PostgreSQL
2. Update `backend/config/database.js`:
   ```javascript
   import pg from 'pg';
   const { Pool } = pg;

   const pool = new Pool({
     connectionString: process.env.DATABASE_URL,
     ssl: { rejectUnauthorized: false }
   });

   export const dbRun = async (sql, params) => {
     const client = await pool.connect();
     try {
       const result = await client.query(sql, params);
       return result;
     } finally {
       client.release();
     }
   };
   ```

3. Convert SQL schema from SQLite to PostgreSQL syntax

---

## Environment Variables

### Backend (.env)
```env
NODE_ENV=production
PORT=5000
JWT_SECRET=generate-strong-random-key-here
FRONTEND_URL=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/db (if using PostgreSQL)
```

### Frontend (.env.production)
```env
VITE_API_URL=https://api.yourdomain.com
```

---

## Security Checklist

- [ ] Change JWT_SECRET to strong random value
- [ ] Enable HTTPS/SSL certificates
- [ ] Set secure CORS origins
- [ ] Enable rate limiting (already configured)
- [ ] Use environment variables for all secrets
- [ ] Enable database backups
- [ ] Set up monitoring (Sentry, LogRocket)
- [ ] Configure firewall rules
- [ ] Enable security headers (Helmet already configured)
- [ ] Run `npm audit fix` regularly

---

## Performance Optimization

### Backend
- Use Redis for session storage
- Enable database indexing
- Implement caching (Redis)
- Use CDN for static assets
- Enable gzip compression

### Frontend
- Code splitting (Vite already does this)
- Lazy load routes
- Optimize images
- Enable service worker (PWA)
- Use CDN for assets

---

## Monitoring & Analytics

**Recommended Tools:**
- **Error Tracking**: Sentry
- **Analytics**: Google Analytics, Plausible
- **Performance**: New Relic, Datadog
- **Uptime**: UptimeRobot, Pingdom

---

## Backup Strategy

```bash
# Backup database (if using SQLite)
cp backend/database.sqlite backups/database-$(date +%Y%m%d).sqlite

# Backup database (if using PostgreSQL)
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql
```

Set up automated daily backups using cron.

---

## Scaling Considerations

1. **Horizontal Scaling**: Use load balancer (Nginx, HAProxy)
2. **Database**: Migrate to PostgreSQL with read replicas
3. **Caching**: Redis for sessions and frequently accessed data
4. **CDN**: CloudFlare for static assets
5. **File Storage**: AWS S3 for user uploads
6. **WebSockets**: Use Socket.IO Redis adapter for multiple servers

---

## CI/CD Pipeline

**GitHub Actions Example:**

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Backend
        run: |
          cd backend
          # Deploy to your platform
      - name: Deploy Frontend
        run: |
          cd frontend
          npm install
          npm run build
          # Deploy dist/ folder
```

---

## Troubleshooting

**Backend won't start:**
- Check Node.js version (needs 18+)
- Verify DATABASE_URL is correct
- Check port 5000 is available
- Review logs: `pm2 logs`

**Frontend can't reach API:**
- Verify VITE_API_URL is correct
- Check CORS settings in backend
- Ensure backend is running
- Check browser console for errors

**Database errors:**
- Run `npm run init-db` to reset
- Check file permissions
- Verify SQLite installation

---

## Support & Maintenance

- Monitor error logs daily
- Update dependencies monthly
- Backup database weekly
- Review security advisories
- Monitor performance metrics
- Respond to user feedback

---

**Platform is ready for deployment! 🎉**
