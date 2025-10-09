# Telegram Bot for FLUX Image Generation (Dockerized)

Dockerized Telegram bot that generates images using FLUX.1-dev-fp8 via RunPod, with MinIO for persistent image storage.

## Features

- 🤖 Telegram bot interface for easy image generation
- 🎨 FLUX.1-dev-fp8 model via RunPod serverless
- 📦 MinIO object storage for generated images
- 🐳 Fully containerized with Docker Compose
- 🔒 Secure credential management
- 📊 Persistent storage with 7-day image links

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- RunPod account with endpoint configured
- Telegram bot token from @BotFather

### 2. Get Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow prompts to create your bot
4. Copy the bot token provided

### 3. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# RunPod
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT_ID=your_endpoint_id

# MinIO (optional, defaults work)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=flux-images
```

### 4. Start Services

```bash
docker-compose up -d
```

This will start:
- **MinIO** (object storage) on ports 9000 (API) and 9001 (Console)
- **Telegram Bot** (connected to RunPod and MinIO)

### 5. Use the Bot

1. Find your bot on Telegram (using the username you created)
2. Send `/start` to begin
3. Send any text prompt to generate an image
4. Wait 30-60 seconds for generation
5. Receive your image + permanent storage link

## Usage

### Basic Commands

- `/start` - Welcome message and introduction
- `/help` - Detailed help and examples
- `/settings` - View current bot settings

### Generate Images

Just send a text prompt:
```
a beautiful sunset over mountains, professional photography, 8k
```

The bot will:
1. Acknowledge your request
2. Send it to RunPod for processing
3. Return the generated image
4. Provide a MinIO link (valid for 7 days)

### Quality Tips

For best results, include quality keywords:
```
"cyberpunk city, highly detailed, sharp focus, 8k, professional"
"portrait of a cat, professional photography, detailed fur"
"fantasy landscape, concept art, intricate details, vibrant colors"
```

## Architecture

```
┌─────────────┐
│  Telegram   │
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Telegram Bot    │
│  (Container)    │
└────┬────────┬───┘
     │        │
     │        └──────────┐
     ▼                   ▼
┌──────────┐      ┌────────────┐
│  RunPod  │      │   MinIO    │
│   API    │      │ (Container)│
└──────────┘      └────────────┘
     │
     ▼
┌──────────────┐
│ FLUX.1-dev   │
│  Generation  │
└──────────────┘
```

## Docker Services

### Telegram Bot

- **Container**: `flux_telegram_bot`
- **Image**: Built from Dockerfile
- **Restart**: unless-stopped
- **Logs**: `/var/lib/docker/containers/.../json.log`

### MinIO

- **Container**: `flux_minio`
- **Image**: `minio/minio:latest`
- **API Port**: 9000
- **Console Port**: 9001 (Web UI)
- **Data**: Persisted in `minio_data` volume
- **Default Credentials**: minioadmin/minioadmin

## Management

### View Logs

```bash
# Bot logs
docker-compose logs -f telegram_bot

# MinIO logs
docker-compose logs -f minio

# All logs
docker-compose logs -f
```

### Restart Services

```bash
# Restart bot only
docker-compose restart telegram_bot

# Restart all
docker-compose restart

# Stop all
docker-compose stop

# Start all
docker-compose start
```

### Rebuild After Changes

```bash
# Rebuild and restart
docker-compose up -d --build
```

### Stop and Remove

```bash
# Stop services
docker-compose down

# Stop and remove volumes (deletes stored images!)
docker-compose down -v
```

## MinIO Web Console

Access MinIO web interface at: `http://localhost:9001`

Default credentials:
- **Username**: minioadmin
- **Password**: minioadmin

Here you can:
- Browse generated images
- Manage buckets
- View statistics
- Configure access policies

## Default Settings

```python
Steps: 25
CFG Scale: 4.0
Width: 1024
Height: 1024
Model: FLUX.1-dev-fp8
Negative Prompt: "blurry, low quality, distorted, ugly, bad anatomy, low res, poorly drawn"
```

## Troubleshooting

### Bot not responding

```bash
# Check if containers are running
docker-compose ps

# Check bot logs
docker-compose logs telegram_bot

# Restart bot
docker-compose restart telegram_bot
```

### MinIO connection issues

```bash
# Check MinIO health
docker-compose ps minio

# Access MinIO console
# http://localhost:9001

# Check network
docker network inspect runpod_interaction_flux_network
```

### Image generation fails

Check:
1. RunPod API key is correct
2. RunPod endpoint is active
3. Bot logs for error messages:
   ```bash
   docker-compose logs -f telegram_bot
   ```

### Out of disk space

MinIO stores all generated images. To clean up:

```bash
# Access MinIO console at http://localhost:9001
# Or use MinIO client (mc) to delete old files

# Nuclear option - delete all volumes
docker-compose down -v
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` |
| `RUNPOD_API_KEY` | RunPod API key | `rpa_...` |
| `RUNPOD_ENDPOINT_ID` | RunPod endpoint ID | `dkjet0...` |

### Optional (MinIO)

| Variable | Description | Default |
|----------|-------------|---------|
| `MINIO_ACCESS_KEY` | MinIO username | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO password | `minioadmin` |
| `MINIO_BUCKET` | Storage bucket name | `flux-images` |

## Security Notes

1. **Never commit `.env` file** - It contains secrets!
2. **Change MinIO credentials** in production
3. **Use strong passwords** for MinIO
4. **Restrict bot access** - Use Telegram's privacy settings
5. **Monitor usage** - Check RunPod costs regularly

## Production Deployment

For production use:

1. Change MinIO credentials:
   ```bash
   MINIO_ACCESS_KEY=your_secure_username
   MINIO_SECRET_KEY=your_very_long_secure_password
   ```

2. Enable HTTPS for MinIO (use reverse proxy)

3. Add Telegram user whitelist (modify `telegram_bot.py`)

4. Set up monitoring and alerts

5. Configure backup for MinIO data

## Development

### Local Testing

```bash
# Run without Docker
python telegram_bot.py

# With local MinIO
docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

### Code Changes

After modifying `telegram_bot.py`:

```bash
docker-compose up -d --build telegram_bot
```

## Example Prompts

**Landscapes:**
```
a serene mountain landscape at golden hour, professional photography, 8k, highly detailed
```

**Portraits:**
```
portrait of a woman with flowing hair, professional photo, sharp focus, detailed, bokeh background
```

**Fantasy:**
```
epic fantasy dragon, detailed scales, dramatic lighting, concept art, highly detailed
```

**Sci-fi:**
```
futuristic cyberpunk city, neon lights, rain, cinematic, highly detailed, blade runner style
```

## File Structure

```
runpod_interaction/
├── telegram_bot.py          # Main bot script
├── Dockerfile               # Bot container definition
├── docker-compose.yml       # Services orchestration
├── requirements.txt         # Python dependencies
├── .env                     # Your secrets (gitignored)
├── .env.example            # Template for .env
└── README_DOCKER.md        # This file
```

## Support

- Bot issues: Check logs with `docker-compose logs`
- RunPod API: https://docs.runpod.io
- MinIO docs: https://min.io/docs
- Telegram Bot API: https://core.telegram.org/bots/api

## License

MIT License - Free to use and modify

## Credits

- **FLUX.1** by Black Forest Labs
- **RunPod** for serverless GPU infrastructure
- **MinIO** for object storage
- **python-telegram-bot** library
