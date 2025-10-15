# Deployment Notes - Fixed for Coolify

## Changes Made

### 1. Added Health Check Script
Created `healthcheck.sh` to verify the bot process is running:
```bash
#!/bin/sh
ps aux | grep -v grep | grep -q "python telegram_bot.py"
exit $?
```

### 2. Updated Dockerfile
- Added `healthcheck.sh` to the image
- Made it executable with `chmod +x`

### 3. Updated docker-compose.coolify.yml
Added health check configuration:
```yaml
healthcheck:
  test: ["CMD-SHELL", "/app/healthcheck.sh"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 4. Updated docker-compose.yml
Added the same health check for consistency in local deployments.

## Required Environment Variables

Create a `.env` file in Coolify with these variables:

```env
# Required
TELEGRAM_BOT_TOKEN=<your_bot_token_from_@BotFather>
RUNPOD_API_KEY=<your_runpod_api_key>
RUNPOD_ENDPOINT_ID=dkjet0qyll05jx
GEMINI_API_KEY=<your_gemini_api_key>

# Optional (defaults provided)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=flux-images
HUGGING_FACE_TOKEN=
```

## RunPod Endpoint Configuration

Your RunPod endpoint: `dkjet0qyll05jx`

The bot uses the synchronous endpoint:
```
https://api.runpod.ai/v2/dkjet0qyll05jx/runsync
```

Make sure your endpoint:
1. Has the FLUX.1-dev-fp8 model loaded
2. Has ComfyUI installed and configured
3. Supports the `/runsync` endpoint (synchronous execution)

## Deployment Steps for Coolify

1. **Push the updated Docker image:**
   ```bash
   docker build -t dmitryodinoky/telegram-bot-flux:latest .
   docker push dmitryodinoky/telegram-bot-flux:latest
   ```

2. **In Coolify:**
   - Create a new service from `docker-compose.coolify.yml`
   - Set environment variables in Coolify's UI
   - Deploy the stack

3. **Verify deployment:**
   - MinIO should be healthy first (30s start period + health checks)
   - Bot should start after MinIO is healthy
   - Bot health check starts after 40s (start_period)
   - Check logs: `docker logs <container_name>`

## Health Check Behavior

- **MinIO**: Checks `http://localhost:9000/minio/health/live` every 10s
- **Bot**: Checks if Python process is running every 30s
- **Start Period**: Bot has 40s grace period before health checks begin
- **Retries**: Bot gets 3 failed health checks before marked unhealthy

## Troubleshooting

### Bot marked as unhealthy
```bash
# Check if bot process is running
docker exec <container_name> ps aux

# Check bot logs for errors
docker logs <container_name>

# Verify environment variables
docker exec <container_name> env | grep -E "TELEGRAM|RUNPOD|GEMINI"
```

### MinIO connection issues
```bash
# Check MinIO logs
docker logs <minio_container_name>

# Verify MinIO is accessible from bot container
docker exec <bot_container_name> curl -f http://minio:9000/minio/health/live
```

### RunPod API errors
1. Verify `RUNPOD_ENDPOINT_ID=dkjet0qyll05jx` in .env
2. Check RunPod API key is valid
3. Ensure endpoint is running and not paused
4. Check RunPod dashboard for endpoint status

## Testing Locally

```bash
# Build the image
docker-compose build

# Start services
docker-compose up -d

# Check health status
docker-compose ps

# View logs
docker-compose logs -f telegram_bot
```

## Post-Deployment Verification

Send a test message to your bot:
1. Start a chat with your bot on Telegram
2. Send `/start` to verify bot is responsive
3. Send a text prompt like "a red apple"
4. Wait 30-60 seconds for image generation
5. Check MinIO console at `http://<host>:9001` (credentials: minioadmin/minioadmin)

## Notes

- The bot takes ~30-60 seconds per image generation
- Images are saved to MinIO with 7-day expiration URLs
- Local debug copies saved to `/app/outputs/` inside container
- Health check grace period (40s) allows bot to fully initialize before checks begin
