# Quick Deployment Guide for BreathIn

## ✅ Everything is Ready!

All deployment files have been created and pushed to GitHub. Now you just need to trigger the deployment.

---

## Option 1: Deploy via Fly.io Dashboard (Easiest)

1. **Go to Fly.io Dashboard**: https://fly.io/dashboard

2. **Find your app** "breathein"

3. **Click on the app** to open it

4. **Look for "Deploy" or "Settings"** tab

5. **Trigger deployment** from GitHub:
   - Click "Deploy from GitHub" or "Redeploy"
   - Select the `main` branch
   - Click "Deploy"

6. **Wait for build** (2-5 minutes)

7. **Access your app** at: `https://breathein.fly.dev`

---

## Option 2: Deploy via Fly.io CLI

### Step 1: Install Fly.io CLI (if not already)

**On your local machine** (not in this sandbox):

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Step 2: Login

```bash
flyctl auth login
```

This will open your browser to authenticate.

### Step 3: Clone and Deploy

```bash
# Clone your repository
git clone https://github.com/elshadsabziyev/BreathIn.git
cd BreathIn

# Deploy to Fly.io
flyctl deploy
```

### Step 4: Access Your App

```bash
# Open in browser
flyctl open

# Or visit directly
# https://breathein.fly.dev
```

---

## Option 3: Alternative - Railway (Even Easier!)

If Fly.io is giving you trouble, Railway is super easy:

### Steps:

1. **Go to Railway**: https://railway.app

2. **Sign in** with GitHub

3. **New Project** → **Deploy from GitHub repo**

4. **Select** `elshadsabziyev/BreathIn`

5. **Railway automatically**:
   - Detects the Dockerfile
   - Builds and deploys
   - Gives you a public URL

6. **Click "Generate Domain"** to get your permanent URL

7. **Done!** Your app is live at `breathein.up.railway.app` (or similar)

**Railway is recommended if you want zero configuration!**

---

## Checking Deployment Status

### Fly.io

```bash
# Check app status
flyctl status -a breathein

# View logs
flyctl logs -a breathein

# View in browser
flyctl open -a breathein
```

### Railway

- Go to your Railway dashboard
- Click on your project
- View logs in real-time
- Click the generated domain to access

---

## Expected URLs

After deployment, your app will be available at:

**Fly.io**: `https://breathein.fly.dev`  
**Railway**: `https://breathein.up.railway.app` (or similar)

---

## Troubleshooting

### "App not found" on Fly.io

**Solution**: The app might not be created yet. Create it:

```bash
flyctl apps create breathein
flyctl deploy
```

### Build fails

**Check**:
1. All files are committed to GitHub
2. Dockerfile is in the root directory
3. requirements.txt is complete

**View logs**:
```bash
flyctl logs -a breathein
```

### Port issues

The app is configured to listen on the `PORT` environment variable, which both Fly.io and Railway set automatically. No changes needed!

---

## What's Deployed

Your BreathIn app includes:
- ✅ Cascaded ML architecture (6 models)
- ✅ Real-time air quality predictions
- ✅ 24-hour forecasts
- ✅ Health recommendations
- ✅ Modern NiceGUI interface
- ✅ Production-ready Dockerfile
- ✅ Automatic HTTPS
- ✅ 1GB RAM, 1 vCPU (Fly.io)

---

## Cost

**Fly.io**: FREE (within $5/month credit)  
**Railway**: FREE (within $5/month credit)

Both platforms won't charge you beyond the free tier unless you explicitly upgrade.

---

## Next Steps After Deployment

1. **Test the app**: Enter a city name and verify predictions work
2. **Share the URL**: Send it to friends/colleagues
3. **Monitor**: Check logs occasionally
4. **Scale** (if needed): Add more resources via dashboard

---

## Need Help?

- **Fly.io Docs**: https://fly.io/docs
- **Railway Docs**: https://docs.railway.app
- **GitHub Issues**: https://github.com/elshadsabziyev/BreathIn/issues

---

**Your app is ready to deploy! Choose your preferred method above and you'll be live in minutes.** 🚀
