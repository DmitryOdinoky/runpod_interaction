# FLUX Image Generator Telegram Bot

A production-ready Telegram bot for generating high-quality images using FLUX.1-dev-fp8 model via RunPod serverless ComfyUI endpoints. Features Docker containerization, MinIO object storage, and optimized FLUX parameters.

## 🎨 Features

- **Telegram Bot Interface**: Simple text-to-image generation through Telegram
- **FLUX.1-dev-fp8 Model**: High-quality image generation with optimized parameters (CFG=1.0)
- **Docker Deployment**: Production-ready containerized setup
- **MinIO Storage**: Automatic image backup to S3-compatible storage
- **Image Preview**: Direct image display in Telegram (not as file attachment)
- **Error Handling**: Robust error handling with user-friendly messages
- **Debug Logging**: Local image saving for quality verification

## 📋 Prerequisites

- Docker and Docker Compose
- RunPod account with ComfyUI endpoint ([runpod/worker-comfyui:flux1-dev](https://console.runpod.io/hub/runpod-workers/worker-comfyui))
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- RunPod API Key and Endpoint ID

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone git@github.com:DmitryOdinoky/runpod_interaction.git
cd runpod_interaction
```

### 2. Configure Environment

Create `.env` file:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# RunPod
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT_ID=your_endpoint_id

# MinIO (optional, uses defaults if not specified)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=flux-images
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Test the Bot

1. Open Telegram and find your bot
2. Send `/start`
3. Send a prompt: `a fluffy white dragon floating in soft pastel clouds`
4. Wait 30-60 seconds for your image!

## 🏗️ Architecture

```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│  Telegram Bot   │─────▶│  RunPod API  │─────▶│  ComfyUI    │
│   (Docker)      │      │              │      │  FLUX.1-dev │
└────────┬────────┘      └──────────────┘      └─────────────┘
         │
         ▼
┌─────────────────┐
│  MinIO Storage  │
│   (Docker)      │
└─────────────────┘
```

## 🐳 Docker Deployment

### Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f telegram_bot

# Restart after code changes
docker-compose up -d --build telegram_bot

# Stop services
docker-compose down
```

### Production Deployment

#### Option 1: VPS/Cloud Server

1. **Setup Server** (Ubuntu/Debian):
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

2. **Deploy Application**:
```bash
# Clone repository
git clone git@github.com:DmitryOdinoky/runpod_interaction.git
cd runpod_interaction

# Configure environment
nano .env  # Add your credentials

# Start services
docker-compose up -d

# Enable auto-restart
docker-compose restart telegram_bot
```

3. **Configure Firewall** (optional, MinIO console access):
```bash
sudo ufw allow 9001/tcp  # MinIO console
```

4. **Monitor Logs**:
```bash
# Follow bot logs
docker-compose logs -f telegram_bot

# Check container status
docker-compose ps

# View resource usage
docker stats
```

#### Option 2: Cloud Container Services

**AWS ECS / Google Cloud Run / Azure Container Instances:**

1. Build and push image:
```bash
# Build image
docker build -t flux-telegram-bot .

# Tag for registry
docker tag flux-telegram-bot:latest your-registry/flux-telegram-bot:latest

# Push to registry
docker push your-registry/flux-telegram-bot:latest
```

2. Deploy with environment variables:
```
TELEGRAM_BOT_TOKEN=...
RUNPOD_API_KEY=...
RUNPOD_ENDPOINT_ID=...
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

#### Option 3: Docker Swarm / Kubernetes

See `docker-compose.yml` for service configuration. Key points:
- Bot container depends on MinIO health check
- MinIO uses persistent volume for data
- Logs limited to 10MB × 3 files
- Auto-restart policy: `unless-stopped`

## ⚙️ Configuration

### Bot Settings

Edit `telegram_bot.py` constants:

```python
# Default generation settings (optimized for FLUX)
DEFAULT_STEPS = 20          # 15-30 recommended
DEFAULT_CFG = 1.0           # FLUX works best with 1.0!
DEFAULT_WIDTH = 1024        # 512-2048
DEFAULT_HEIGHT = 1024       # 512-2048
DEFAULT_NEGATIVE = ""       # FLUX doesn't need negative prompts
```

### MinIO Settings

Access MinIO console at `http://localhost:9001` (or `http://your-server-ip:9001`):
- **Username**: `minioadmin`
- **Password**: `minioadmin`

Browse uploaded images in the `flux-images` bucket.

## 🤖 Bot Commands

- `/start` - Welcome message and instructions
- `/help` - Detailed usage guide
- `/settings` - View current generation settings
- **Any text** - Generate image from prompt

## 📝 Example Prompts

```
a beautiful sunset over mountains, professional photography, 8k
cyberpunk city at night, neon lights, highly detailed
portrait of a cat, professional photography, sharp focus
fantasy dragon, detailed scales, epic, concept art
fluffy white kitten floating in soft pastel clouds, dreamy atmosphere
```

## 🔧 Troubleshooting

### Bot Not Responding

```bash
# Check bot status
docker-compose ps

# View recent logs
docker-compose logs --tail=50 telegram_bot

# Restart bot
docker-compose restart telegram_bot
```

### MinIO Connection Issues

```bash
# Check MinIO status
docker-compose ps minio

# Check MinIO health
docker-compose logs minio

# Restart MinIO
docker-compose restart minio
```

### Image Generation Errors

1. **Timeout**: RunPod endpoint might be cold-starting (first request takes longer)
2. **Blurry Images**: Verify CFG=1.0 (FLUX-specific requirement)
3. **API Errors**: Check RunPod API key and endpoint ID in `.env`

### Debug Mode

Check saved images in the container:
```bash
docker exec flux_telegram_bot ls -la /app/outputs/
docker cp flux_telegram_bot:/app/outputs/. ./debug_outputs/
```

## 📊 Performance

- **Generation Time**: 30-60 seconds per image
- **Image Quality**: 1024×1024 at CFG=1.0 (optimal for FLUX)
- **Storage**: Images backed up to MinIO automatically
- **Concurrency**: Sequential processing (one user at a time)

## 🔒 Security Best Practices

1. **Change MinIO Credentials**:
```bash
# In .env file
MINIO_ACCESS_KEY=your_secure_access_key
MINIO_SECRET_KEY=your_secure_secret_key_min_8_chars
```

2. **Protect .env File**:
```bash
chmod 600 .env
```

3. **Use Secrets in Production**:
- AWS: AWS Secrets Manager
- Google Cloud: Secret Manager
- Kubernetes: Secrets

4. **Restrict MinIO Access**:
- Don't expose port 9001 publicly
- Use firewall rules
- Set up SSL/TLS for production

## 📂 Project Structure

```
runpod_interaction/
├── telegram_bot.py           # Main bot application
├── generate.py               # CLI image generator
├── runpod_test.py           # Test script
├── requirements.txt          # Python dependencies
├── Dockerfile               # Bot container definition
├── docker-compose.yml       # Multi-container orchestration
├── .env                     # Environment variables (create this)
├── QUICKSTART.md           # Quick start guide
└── outputs/                # Local debug images
```

## 🛠️ Development

### Local Testing (Without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN=...
export RUNPOD_API_KEY=...
export RUNPOD_ENDPOINT_ID=...

# Run bot
python telegram_bot.py
```

### CLI Image Generation

```bash
# Simple generation
python generate.py "your prompt here"

# With custom parameters
python generate.py "your prompt" --steps 25 --cfg 1.0 --width 1280 --height 720
```

## 🔄 Updates and Maintenance

### Update Bot Code

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

### Backup MinIO Data

```bash
# Backup MinIO volume
docker run --rm -v runpod_interaction_minio_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/minio-backup.tar.gz /data
```

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs telegram_bot
```

## 🎯 FLUX Model Tips

**Critical**: FLUX.1-dev works differently from Stable Diffusion:
- ✅ Use **CFG=1.0** (not 3.5-4.0)
- ✅ Use **steps=20** (not 25-30)
- ✅ **No negative prompts** needed
- ✅ Use `EmptySD3LatentImage` node

These settings are already configured in the bot for optimal results.

## 📄 License

This project is provided as-is for use with RunPod services.

## 🤝 Support

- **Bot Issues**: Open an issue in this repository
- **RunPod API**: [RunPod Support](https://docs.runpod.io/)
- **Telegram Bot API**: [Official Docs](https://core.telegram.org/bots/api)

## 🙏 Credits

- **FLUX.1**: Advanced image generation model by Black Forest Labs
- **RunPod**: Serverless GPU infrastructure
- **ComfyUI**: Node-based UI for Stable Diffusion
- **MinIO**: High-performance S3-compatible object storage
