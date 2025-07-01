# 🚀 Deploy to Render

## Step-by-Step Deployment Guide

### 1. **Commit and Push Changes**
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. **Create Render Account**
- Go to [render.com](https://render.com)
- Sign up with your GitHub account
- Connect your GitHub account to Render

### 3. **Deploy Using Blueprint**
- In Render dashboard, click **"New"** → **"Blueprint"**
- Connect your GitHub repository: `teren-papercutlabs/cp-intro`
- Select the `main` branch
- Render will detect the `render.yaml` file automatically
- Click **"Apply"**

### 4. **Services Created**
Render will create 3 services:
- **hyperliquid-db** (PostgreSQL database)
- **hyperliquid-api** (Backend API)
- **hyperliquid-frontend** (React frontend)

### 5. **Get Your API URL**
After deployment:
- Go to your **hyperliquid-api** service in Render
- Copy the URL (something like `https://hyperliquid-api-abc123.onrender.com`)

### 6. **Update Frontend API URL**
- Go to **hyperliquid-frontend** service
- Click **"Environment"** tab
- Update `VITE_API_URL` to: `https://your-api-url.onrender.com/api`
- Click **"Save Changes"**
- The frontend will automatically redeploy

### 7. **Initialize Database with Real Data**
Once deployed, you'll need to populate the database:

Option A: **Manual Script Execution**
- Go to your API service dashboard
- Use the "Shell" feature to run:
```bash
python scripts/init_production_db.py
python scripts/simple_db_load.py
```

Option B: **Add to Your Local Environment**
```bash
# Set production database URL locally
export DATABASE_URL="your-render-postgres-url"
python scripts/simple_db_load.py
```

### 8. **Environment Variables**
Your services will automatically have:
- **API**: `DATABASE_URL`, `FLASK_ENV=production`
- **Frontend**: `VITE_API_URL`

### 9. **Access Your App**
- **Frontend**: `https://hyperliquid-frontend-abc123.onrender.com`
- **API**: `https://hyperliquid-api-abc123.onrender.com/api/losers`

## 🔧 Troubleshooting

### Database Connection Issues
- Check that PostgreSQL service is running
- Verify `DATABASE_URL` is correctly set in API service

### Frontend Not Loading Data
- Verify `VITE_API_URL` points to your API service
- Check API service logs for errors
- Ensure CORS is enabled (already configured)

### API Service Errors
- Check logs in Render dashboard
- Verify all Python dependencies are in `requirements.txt`
- Check that database schema is initialized

## 📊 Expected Results
After successful deployment:
- **50 losing traders** from Hyperliquid with real data
- **41 counter-trade opportunities** 
- **Live terminal-style dashboard**
- **Auto-refresh every 30 seconds**

## 💰 Render Costs (Free Tier)
- PostgreSQL: Free tier (90 days, then $7/month)
- Web Services: Free tier (750 hours/month)
- Static Site: Free

Total: **Free for 90 days**, then ~$14/month for basic usage.