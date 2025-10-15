# Build and Push Docker Image

## Prerequisites
- Docker Desktop installed and running
- Logged into Docker Hub: `docker login`

## Steps to Build and Push

### 1. Open PowerShell or Command Prompt

Navigate to the project directory:
```powershell
cd C:\Users\dmitrijs.odinokijs\python_projects\runpod_interaction
```

### 2. Build the Docker Image

```powershell
docker build -t dmitryodinoky/telegram-bot-flux:latest .
```

This will:
- Use the updated Dockerfile with healthcheck.sh
- Install all dependencies
- Copy telegram_bot.py and flux_workflow_simple.json
- Set up the health check script

**Expected output:** You should see build steps completing, ending with:
```
Successfully tagged dmitryodinoky/telegram-bot-flux:latest
```

### 3. (Optional) Test the Image Locally

Before pushing, you can test the image:

```powershell
docker-compose up -d
```

Wait 40-60 seconds, then check health:
```powershell
docker-compose ps
```

You should see both services as "healthy".

To stop:
```powershell
docker-compose down
```

### 4. Push to Docker Hub

```powershell
docker push dmitryodinoky/telegram-bot-flux:latest
```

**Expected output:**
```
The push refers to repository [docker.io/dmitryodinoky/telegram-bot-flux]
latest: digest: sha256:xxxxx size: xxxx
```

### 5. Verify on Docker Hub

Visit: https://hub.docker.com/r/dmitryodinoky/telegram-bot-flux/tags

You should see the `latest` tag with a recent timestamp.

## After Pushing

### Deploy to Coolify

1. Go to your Coolify dashboard
2. Navigate to your service
3. Click "Redeploy" or "Deploy"
4. Coolify will pull the new image with the health check
5. Wait for both services to become healthy:
   - MinIO: ~30-40 seconds
   - Telegram Bot: ~40-60 seconds

### Monitor Deployment

In Coolify, check the logs:
- MinIO should show: "MinIO Object Storage Server"
- Bot should show: "Starting Telegram bot..."

### Verify Health Checks

After deployment, the services should show as "healthy" in Coolify.

If the bot is unhealthy, check logs for errors:
- Missing environment variables
- RunPod API connection issues
- Telegram token issues

## Troubleshooting

### Build Fails

**Error: COPY failed**
- Make sure `healthcheck.sh` exists in the project directory
- Check that all files are present: `telegram_bot.py`, `flux_workflow_simple.json`

**Error: Cannot connect to Docker daemon**
- Start Docker Desktop
- Wait for Docker to fully start
- Try the build command again

### Push Fails

**Error: denied: requested access to the resource is denied**
- Login to Docker Hub: `docker login`
- Enter username: `dmitryodinoky`
- Enter password/access token
- Retry push

**Error: unauthorized**
- Make sure you own the `dmitryodinoky` Docker Hub account
- Or use your own Docker Hub username and update the image name

### Image Size Concerns

The image should be approximately:
- Base Python 3.11-slim: ~130 MB
- With dependencies: ~200-250 MB

If much larger, check for unnecessary files being copied.

## Alternative: Build on Different Machine

If Docker Desktop isn't available, you can:

1. **Use GitHub Actions** - Set up CI/CD to build and push automatically
2. **Use a cloud build service** - Google Cloud Build, AWS CodeBuild
3. **Build on the Coolify server** - SSH and build directly on the deployment server

## Quick Reference

```powershell
# One-liner to build and push
docker build -t dmitryodinoky/telegram-bot-flux:latest . && docker push dmitryodinoky/telegram-bot-flux:latest
```

After pushing, redeploy in Coolify to use the updated image.
