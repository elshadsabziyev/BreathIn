# BreathIn Deployment Guide

## Fly.io Deployment (Recommended)

### Prerequisites
- Fly.io account (sign up at https://fly.io)
- Fly.io CLI installed
- GitHub repository connected to Fly.io

### Automatic Deployment via GitHub

Since you've already created the app "breathein" on Fly.io and linked it to your GitHub repository, deployment is automatic:

1. **Push to GitHub** (already done):
   ```bash
   git push origin main
   ```

2. **Fly.io will automatically**:
   - Detect the Dockerfile
   - Build the Docker image
   - Deploy to your app
   - Assign a public URL

3. **Check deployment status**:
   ```bash
   flyctl status -a breathein
   ```

4. **View logs**:
   ```bash
   flyctl logs -a breathein
   ```

5. **Access your app**:
   ```
   https://breathein.fly.dev
   ```

### Manual Deployment (if needed)

If automatic deployment doesn't work, you can deploy manually:

```bash
# 1. Install Fly.io CLI (if not already installed)
curl -L https://fly.io/install.sh | sh

# 2. Add to PATH
export FLYCTL_INSTALL="/home/ubuntu/.fly"
export PATH="$FLYCTL_INSTALL/bin:$PATH"

# 3. Login to Fly.io
flyctl auth login

# 4. Navigate to project directory
cd BreathIn

# 5. Deploy
flyctl deploy
```

### Configuration Details

The `fly.toml` file configures:
- **App name**: breathein
- **Region**: iad (Washington D.C., US East)
- **Memory**: 1GB
- **CPU**: 1 shared vCPU
- **Port**: 8080
- **HTTPS**: Forced
- **Auto-scaling**: Minimum 1 machine always running

### Monitoring

**Check app status**:
```bash
flyctl status -a breathein
```

**View real-time logs**:
```bash
flyctl logs -a breathein
```

**SSH into the machine**:
```bash
flyctl ssh console -a breathein
```

**Check resource usage**:
```bash
flyctl vm status -a breathein
```

### Scaling

**Scale memory**:
```bash
flyctl scale memory 2048 -a breathein
```

**Scale CPU**:
```bash
flyctl scale vm shared-cpu-2x -a breathein
```

**Scale instances**:
```bash
flyctl scale count 2 -a breathein
```

### Custom Domain (Optional)

1. **Add your domain**:
   ```bash
   flyctl certs create yourdomain.com -a breathein
   ```

2. **Get DNS records**:
   ```bash
   flyctl certs show yourdomain.com -a breathein
   ```

3. **Add DNS records** to your domain registrar:
   - Type: A
   - Name: @
   - Value: (IP from Fly.io)
   
   - Type: AAAA
   - Name: @
   - Value: (IPv6 from Fly.io)

4. **Verify**:
   ```bash
   flyctl certs check yourdomain.com -a breathein
   ```

### Troubleshooting

**App won't start**:
```bash
# Check logs
flyctl logs -a breathein

# SSH into machine
flyctl ssh console -a breathein

# Check if port is correct
# Ensure app listens on PORT environment variable
```

**Out of memory**:
```bash
# Scale up memory
flyctl scale memory 2048 -a breathein
```

**Slow performance**:
```bash
# Add more machines
flyctl scale count 2 -a breathein

# Or upgrade CPU
flyctl scale vm shared-cpu-2x -a breathein
```

**Build fails**:
- Check Dockerfile syntax
- Ensure all dependencies in requirements.txt
- Check build logs: `flyctl logs -a breathein`

---

## Alternative: Railway Deployment

If Fly.io doesn't work, Railway is another excellent option:

### Steps

1. **Sign up at Railway**: https://railway.app

2. **New Project** → **Deploy from GitHub**

3. **Select** the BreathIn repository

4. **Configure**:
   - Build Command: (auto-detected from Dockerfile)
   - Start Command: `python app.py --host 0.0.0.0 --port $PORT`

5. **Environment Variables**:
   - PORT: (auto-set by Railway)

6. **Deploy**: Railway will automatically build and deploy

7. **Get URL**: Railway provides a public URL

### Railway Configuration

Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## Alternative: Render Deployment

### Steps

1. **Sign up at Render**: https://render.com

2. **New** → **Web Service**

3. **Connect GitHub** repository

4. **Configure**:
   - Name: breathein
   - Region: Oregon (or closest to users)
   - Branch: main
   - Build Command: (auto-detected)
   - Start Command: `python app.py --host 0.0.0.0 --port $PORT`

5. **Environment Variables**:
   - PORT: (auto-set by Render)

6. **Create Web Service**

**Note**: Render free tier spins down after inactivity (50+ second cold starts)

---

## Local Development

### Run locally

```bash
# Clone repository
git clone https://github.com/elshadsabziyev/BreathIn.git
cd BreathIn

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Or with custom host/port
python app.py --host 0.0.0.0 --port 8080
```

Access at: http://localhost:8080

### Docker (local)

```bash
# Build image
docker build -t breathein .

# Run container
docker run -p 8080:8080 breathein
```

Access at: http://localhost:8080

---

## Production Checklist

- [x] Dockerfile created
- [x] fly.toml configured
- [x] .dockerignore added
- [x] App accepts PORT environment variable
- [x] App binds to 0.0.0.0 (not localhost)
- [x] Dependencies in requirements.txt
- [x] GitHub repository connected
- [ ] Domain configured (optional)
- [ ] Monitoring set up
- [ ] Backup strategy (if storing data)

---

## Cost Estimation

### Fly.io (Current Configuration)
- **Free tier**: $5/month credit
- **1GB RAM + 1 vCPU**: ~$5/month
- **Bandwidth**: 100GB included
- **Total**: **FREE** (within credit limit)

### Railway
- **Free tier**: $5/month credit
- **300MB RAM + 0.1 vCPU**: ~$2-3/month
- **Total**: **FREE** (within credit limit)

### Render
- **Free tier**: $0/month
- **Limitation**: Spins down after inactivity
- **Total**: **FREE** (with cold starts)

---

## Support

For deployment issues:
- **Fly.io Docs**: https://fly.io/docs
- **Fly.io Community**: https://community.fly.io
- **GitHub Issues**: https://github.com/elshadsabziyev/BreathIn/issues

---

**Deployment Status**: Ready for production ✅
